# Functions in this forms.py dictate how user input is handled

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser, Publisher, Article, Newsletter
from django.db import transaction
from django.db.models import Q


# Reader registration
class ReaderRegistrationForm(UserCreationForm):
    '''
    Registration for reader accounts. Requires username, email and password
    '''
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = CustomUser.Role.READER

        if commit:
            user.save()

        return user


# Journalist registration
class JournalistRegistrationForm(UserCreationForm):
    '''
    Journalist registration takes username, email and passwords.
    Journalists affiliated with publishers will link their account to
    publihsers here. Journalists can select multiple publishers or none.

    '''

    journalist_publisher = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        label="Select your publishers",
        widget=forms.CheckboxSelectMultiple(),
        help_text=(
            "You can select multiple publishers or leave this blank "
            "if you are an independent journalist."
        )
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    @transaction.atomic
    def save(self, commit=True):

        user = super().save(commit=False)
        user.role = CustomUser.Role.JOURNALIST

        if commit:
            user.save()
            user.publishers.set(
                self.cleaned_data['journalist_publisher']
            )

        return user


# Editor registration
class EditorRegistrationForm(UserCreationForm):

    '''
    Editor accounts regitser with username, email and passwords.
    Editors can register their publishers here. Duplicate publishers
    won't be allowed. Editors can select multiple publihsers.
    '''
    editor_publishers = forms.ModelMultipleChoiceField(
        queryset=Publisher.objects.all(),
        required=False,
        label="Select your publishers",
        widget=forms.CheckboxSelectMultiple(),
        help_text=(
            "Select multiple publishers or create a new publisher."
        )
    )

    publisher_name = forms.CharField(
        max_length=255,
        required=False,
        label="Or enter a new publisher name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter publisher name'
        })
    )

    publisher_description = forms.CharField(
        required=False,
        label="Publisher description",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe your publisher'
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

    def clean(self):
        cleaned_data = super().clean()

        existing = cleaned_data.get('editor_publishers')
        new_name = cleaned_data.get('publisher_name')

        if existing and new_name:
            raise forms.ValidationError(
                "Select an existing publisher OR enter a new one, not both."
            )

        if not existing and not new_name:
            raise forms.ValidationError(
                "Please select a publisher or enter a new publisher."
            )

        if new_name:
            new_name = new_name.strip()

            if not new_name:
                self.add_error(
                    'publisher_name',
                    "Publisher name cannot be blank."
                )

            elif Publisher.objects.filter(
                name__iexact=new_name
            ).exists():
                self.add_error(
                    'publisher_name',
                    "This publisher already exists. Please select it instead."
                )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):

        user = super().save(commit=False)
        user.role = CustomUser.Role.EDITOR

        if not commit:
            return user

        publishers = self.cleaned_data['editor_publishers']

        if not publishers:
            publisher = Publisher.objects.create(
                name=self.cleaned_data['publisher_name'].strip(),
                description=self.cleaned_data['publisher_description']
            )
            publishers = [publisher]

        user.save()
        user.editor_publishers.set(publishers)

        return user


# Login form
class CustomLoginForm(AuthenticationForm):
    '''
    Login form serves all user roles
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })


# Article form
class ArticleForm(forms.ModelForm):
    '''
    The article form allows journalists to create articles.
    Editors will also use the article form when editing. The user
    can input: title, content, image and optionally select a publisher.
    '''
    class Meta:
        model = Article

        fields = [
            'title',
            'content',
            'image',
            'publisher',
        ]

        labels = {
            'title': 'Article Title',
            'content': 'Article Content',
            'image': 'Upload an Image',
            'publisher': 'Publisher',
        }

        help_texts = {
            'publisher': (
                'Select a publisher you are affiliated with. '
                'Leave blank if you are an independent journalist.'
            ),
            'image': 'Optional: Upload an image to accompany your article.',
        }

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter article title',
            }),

            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Write your article here...',
            }),

            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),

            'publisher': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == CustomUser.Role.JOURNALIST:

            self.fields['publisher'].queryset = (
                user.publishers.all()
            )
            self.fields['publisher'].required = False
            self.fields['publisher'].empty_label = (
                "Publish independently (no publisher)"
            )
        elif user and user.role == CustomUser.Role.EDITOR:

            self.fields['publisher'].queryset = (
                user.editor_publishers.all()
            )
            self.fields['publisher'].required = True


# Newsletter form
class NewsletterForm(forms.ModelForm):
    '''
    The newsletter form will allow creation by both journalists and 
    editors. Articles can be added to the newsletters, when available by
    the selected publisher, if the journalist is not independant.
    Otherwise independant journalists can select any of their articles.
    '''

    publisher = forms.ModelChoiceField(
        queryset=Publisher.objects.none(),
        required=False,
        label="Select publisher",
        empty_label="Choose a publisher (optional)",
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )

    class Meta:
        model = Newsletter

        fields = [
            'title',
            'description',
            'publisher',
            'articles',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter newsletter title'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your newsletter'
            }),

            'articles': forms.CheckboxSelectMultiple(
                    attrs={
                        'class': 'form-check-input',
                    }
            ),
        }

    def __init__(self, *args, **kwargs):

        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.role == CustomUser.Role.JOURNALIST:

            self.fields['publisher'].queryset = (
                user.publishers.all()
            )
            self.fields['publisher'].required = False

            self.fields['articles'].queryset = (
                Article.objects.filter(
                    Q(author=user) |
                    Q(publisher__in=user.publishers.all()),
                    approved=True
                ).distinct().order_by('-created_at')
            )
        elif user and user.role == CustomUser.Role.EDITOR:

            self.fields['publisher'].queryset = (
                user.editor_publishers.all()
            )

            self.fields['publisher'].required = True

            self.fields['articles'].queryset = (
                Article.objects.filter(
                    publisher__in=user.editor_publishers.all(),
                    approved=True
                ).order_by('-created_at')
            )

    def clean(self):

        cleaned_data = super().clean()

        publisher = cleaned_data.get('publisher')
        articles = cleaned_data.get('articles')

        if publisher and articles:
            if articles.exclude(publisher=publisher).exists():
                self.add_error(
                    'articles',
                    'Selected articles must belong to the selected publisher.'
                )

        return cleaned_data
