from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError


# Custom user model
class CustomUser(AbstractUser):
    """
    Custom user model with Reader, Editor and Journalist roles.

    Satisfies specification:
    - Users must have an assigned role.
    - Users must belong to a group based on their role.
    """

    class Role(models.TextChoices):
        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER
    )

    # An editor can belong to ONE publisher.
    # A journalist can belong to MULTIPLE publishers.
    # Readers do not need a publisher.
    publishers = models.ManyToManyField(
        "Publisher",
        related_name="journalists",
        blank=True
    )

    editor_publishers = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="editors"
    )
    # Using session feature of django to keep subscriptions in variables
    subscribed_publishers = models.ManyToManyField(
        "Publisher",
        related_name="subscribers",
        blank=True
    )
    subscribed_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name='journalist_subscribers',
        limit_choices_to={"role": "JOURNALIST"},
        blank=True
    )

    def save(self, *args, **kwargs):
        with transaction.atomic():

            super().save(*args, **kwargs)

            group_name = self.get_role_display()

            group, created = Group.objects.get_or_create(
                name=group_name
            )

            role_groups = Group.objects.filter(
                name__in=["Reader", "Editor", "Journalist"]
            )

            self.groups.remove(*role_groups)

            self.groups.add(group)

    def clean(self):
        super().clean()

        if not self.pk:
            return

        if self.role == self.Role.EDITOR:
            if self.publishers.exists():
                raise ValidationError(
                    "Editors should use editor_publishers, not publishers."
                )

        elif self.role == self.Role.JOURNALIST:
            if self.editor_publishers.exists():
                raise ValidationError(
                    "Journalists should use publishers, not editor_publishers."
                )

        elif self.role == self.Role.READER:
            if (
                self.editor_publishers.exists()
                or self.publishers.exists()
            ):
                raise ValidationError(
                    "Readers cannot be assigned to publishers."
                )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# Publisher model
class Publisher(models.Model):
    """
    Represents a news publisher.

    Satisfies specification:
    - A publisher can have multiple editors.
    - A publisher can have multiple journalists.
    """

    name = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# Article model
class Article(models.Model):
    """
    Represents a news article.

    Satisfies specification:
    - Articles have a title, content, author, created_at,
      approved status and publisher.
    - Articles have a journalist author.
    - Articles can optionally belong to a publisher.
    """

    title = models.CharField(max_length=255)

    content = models.TextField()

    # Allows an image to be uploaded with an article.
    image = models.ImageField(
        upload_to="articles/",
        blank=True,
        null=True
    )

    # Every article has a journalist author.
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name="articles"
    )

    # Optional publisher association.
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="articles"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    # Editors can approve articles.
    approved = models.BooleanField(default=False)

    def clean(self):
        if self.author and self.author.role != CustomUser.Role.JOURNALIST:
            raise ValidationError(
                "Only journalists can author articles."
            )

        if self.author and self.publisher:
            if not self.author.publishers.filter(
                pk=self.publisher_id
            ).exists():
                raise ValidationError(
                    "The journalist must belong to the article's publisher."
                )

    def __str__(self):
        return self.title


# Newsletter
class Newsletter(models.Model):
    """
    Represents a curated collection of articles.

    Satisfies specification:
    - Newsletters have a title, description, created_at
      and journalist author.
    - Newsletters can contain multiple articles.
    """

    title = models.CharField(max_length=255)

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    # Newsletters are created by journalists.
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )

    # Many-to-many relationship:
    # Newsletter can have many articles.
    # Article be in many newsletters.

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletters'
    )

    articles = models.ManyToManyField(
        Article,
        related_name="newsletters",
        blank=True
    )
    approved = models.BooleanField(default=False)

    def clean(self):
        super().clean()

        if self.author_id and self.author.role not in [
            CustomUser.Role.JOURNALIST,
            CustomUser.Role.EDITOR
        ]:
            raise ValidationError(
                "Only journalists and editors can create newsletters."
            )
