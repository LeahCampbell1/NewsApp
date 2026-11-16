# Views functions are largely developed and adapted from the
# previous eCommerce project.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.db import transaction

import smtplib
import logging

from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.urls import reverse_lazy

from .models import Article, Newsletter, CustomUser, Publisher
from .forms import (
    ArticleForm,
    NewsletterForm,
    ReaderRegistrationForm,
    JournalistRegistrationForm,
    EditorRegistrationForm,
    CustomLoginForm
)

# Functions for API use
from .serializers import (PublisherSerializer,
                          ArticleSerializer,
                          NewsletterSerializer)
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import authentication_classes
# from .functions.jsonplaceholder import get_jsonplaceholder_posts
from rest_framework.exceptions import PermissionDenied, ValidationError


logger = logging.getLogger(__name__)

User = get_user_model()


# Role checks
'''
The following functions provide role checks for later functions
'''


def is_reader(user):
    return user.is_authenticated and user.role == CustomUser.Role.READER


def is_journalist(user):
    return user.is_authenticated and user.role == CustomUser.Role.JOURNALIST


def is_editor(user):
    return user.is_authenticated and user.role == CustomUser.Role.EDITOR


# Registration
'''
    Functions register users according to role and return sucess messages.
    These functions require no authentication or login as they are
    public facing
'''


# Reader register
def register_reader(request):
    ''' Function handles reader registration'''
    if request.method == 'POST':
        form = ReaderRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(request,
                             'Your reader account has been created.'
                             'Please login')
            return redirect('welcome')

    else:
        form = ReaderRegistrationForm()

    return render(
        request,
        'good_to_know/register.html',
        {'form': form, 'role': 'Reader'}
    )


# Register journalist
def register_journalist(request):
    ''' Function handles journalist registration'''
    if request.method == 'POST':
        form = JournalistRegistrationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)

            messages.success(
                request,
                'Your journalist account has been created. Please login'
            )

            return redirect('welcome')

    else:
        form = JournalistRegistrationForm()

    return render(
        request,
        'good_to_know/register.html',
        {'form': form, 'role': 'Journalist'}
    )


# Editor registration
def register_editor(request):
    ''' Function handles editor registration'''

    if request.method == 'POST':
        form = EditorRegistrationForm(request.POST)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Editor account successfully created. Please login'
            )

            return redirect('login')

    else:
        form = EditorRegistrationForm()

    return render(
        request,
        'good_to_know/register.html',
        {'form': form, 'role': 'Editor'}
    )


# Welcome, login, logout and home pages
'''
    The welcome page served as the public facing initial
    landing page for the app.
    The login functions utilise the custom user settings.
    The same login can therefore be used for all roles.
    Users are redirected to home where the latest news is
    presented.
'''


# Welcome page
def welcome(request):
    ''' Directs program to display welcome page'''
    return render(request, 'good_to_know/welcome.html')


# Login
class RoleBasedLoginView(LoginView):
    ''' Login view is displayed for al users'''

    template_name = 'good_to_know/login.html'
    authentication_form = CustomLoginForm

    def get_success_url(self):

        user = self.request.user

        if user.role == CustomUser.Role.READER:
            return reverse_lazy('home')

        elif user.role == CustomUser.Role.JOURNALIST:
            return reverse_lazy('journalist_dashboard')

        elif user.role == CustomUser.Role.EDITOR:
            return reverse_lazy('editor_dashboard')

        return reverse_lazy('home')


# Logout
@login_required
def logout_user(request):
    ''' Logout function returns user to welcome page'''
    logout(request)
    return redirect('welcome')


# Home page
def home(request):
    ''' The home view directes users to home page, which displays
        publications.
    '''

    articles = Article.objects.filter(
        approved=True
    ).select_related(
        'author', 'publisher'
    ).order_by('-created_at')

    newsletters = Newsletter.objects.filter(
        approved=True
    ).distinct().prefetch_related(
        'articles'
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/home.html',
        {
            'articles': articles,
            'newsletters': newsletters,
        }
    )


# Publication details
'''
    The following programs form the skeleton requirements for the details
    for each publication.
    Both are frequently linked accross the application.
    Newsletters are structured to contain multiple items.
'''

# Article detail


@login_required
def article_detail(request, article_id):
    ''' Function handles the display of article details for all
        logged in users
    '''

    article = get_object_or_404(
        Article.objects.select_related(
            'author', 'publisher'
        ),
        id=article_id
    )

    if not article.approved:

        journalist_owner = (
            request.user.is_authenticated
            and request.user == article.author
        )

        editor_owner = (
            is_editor(request.user)
            and article.publisher_id is not None
            and request.user.editor_publishers.filter(
                pk=article.publisher_id
            ).exists()
        )

        if not (journalist_owner or editor_owner):
            raise PermissionDenied

    return render(
        request,
        'good_to_know/article_detail.html',
        {'article': article}
    )


# Newsletter detail
@login_required
def newsletter_detail(request, newsletter_id):
    ''' Function handles the display of newsletters'''

    newsletter = get_object_or_404(
        Newsletter.objects.select_related(
            'author'
        ).prefetch_related('articles'),
        id=newsletter_id
    )

    journalist_owner = (
        request.user == newsletter.author
    )

    editor_owner = (
        is_editor(request.user)
        and newsletter.publisher_id is not None
        and request.user.editor_publishers.filter(
            pk=newsletter.publisher_id
        ).exists()
    )

    if not newsletter.approved:
        if not (journalist_owner or editor_owner):
            raise PermissionDenied

    articles = newsletter.articles.filter(
        approved=True
    )

    return render(
        request,
        'good_to_know/newsletter_detail.html',
        {
            'newsletter': newsletter,
            'articles': articles,
        }
    )


# Dashboards
'''
    Dashboards are formulated for: readers, journalists and editors.
    Reader dashboards with display their subscriptions.
    Journalist dashboards will contain their publications, both approved
    and pending approval.
    Editor dashboards show publications awaiting approval, as well as
    publications belonging to their publisher.
'''


@login_required
@user_passes_test(is_reader)
def reader_dashboard(request):
    ''' Reader dashboard displays subscribed journalists and publishers. '''

    publishers = request.user.subscribed_publishers.all()

    journalists = request.user.subscribed_journalists.all()

    return render(
        request,
        'good_to_know/reader_dashboard.html',
        {
            'publishers': publishers,
            'journalists': journalists,
        }
    )


# Journalist dashboard
@login_required
@user_passes_test(is_journalist)
def journalist_dashboard(request):
    ''' Journalist dashboard displays journalists own work. '''

    articles = Article.objects.filter(
        author=request.user
    ).order_by('-created_at')

    newsletters = Newsletter.objects.filter(
        author=request.user
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/journalist_dashboard.html',
        {
            'articles': articles,
            'newsletters': newsletters,
        }
    )


# Editor dashboard
@login_required
@user_passes_test(is_editor)
def editor_dashboard(request):
    ''' Editor dashboard displays work submitted for approval and
        approved publications. Editors are able to manage publishers
    '''

    articles = editor_articles(
        request.user
    ).order_by('-created_at')

    newsletters = editor_newsletters(
        request.user
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/editor_dashboard.html',
        {
            'articles': articles,
            'newsletters': newsletters,
            'pending_articles': articles.filter(approved=False),
            'approved_articles': articles.filter(approved=True),
            'pending_newsletters': newsletters.filter(approved=False),
            'approved_newsletters': newsletters.filter(approved=True),
            'publishers': request.user.editor_publishers.all(),
        }
    )


# Create publisher
@login_required
@user_passes_test(is_editor)
def create_publisher(request):
    ''' Editors create publishers. '''

    if request.method == 'POST':

        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(
                request,
                'Please enter a publisher name.'
            )

        elif Publisher.objects.filter(name__iexact=name).exists():
            messages.error(
                request,
                'This publisher already exists.'
            )

        else:
            try:
                with transaction.atomic():

                    publisher = Publisher.objects.create(
                        name=name,
                        description=description
                    )

                    request.user.editor_publishers.add(publisher)

                messages.success(
                    request,
                    f'{publisher.name} created successfully.'
                )

                return redirect('editor_dashboard')

            except Exception as error:
                logger.error(
                    'Publisher creation failed: %s',
                    error
                )

                messages.error(
                    request,
                    'There was a problem creating the publisher.'
                )

    return render(
        request,
        'good_to_know/publisher_form.html',
        {
            'page_title': 'Create Publisher',
        }
    )


# Journalist Article and newsletter management
'''
    Journalist article abilities are restricted to creating, editing and
    deleting. However independant journalists are able to self approve as
    they aren't affiliated with publishers. This is made explicit in the
    readers view.

    Functions to edit and delete publications are different for journalists
    and editors. This is to simplify permission allocation for later
    programs including API's.
'''


@login_required
@user_passes_test(is_journalist)
def create_article(request):
    ''' Journalists create articles which can be affiliated with a publisher
        or independant. Articles with selected publishers will require approval
    '''

    if request.method == 'POST':

        form = ArticleForm(
            request.POST or None,
            request.FILES or None,
            user=request.user
        )

        if form.is_valid():

            article = form.save(commit=False)

            article.author = request.user
            if article.publisher:
                article.approved = False
            else:
                article.approved = True

            article.save()

            messages.success(
                request,
                'Article created successfully.'
            )

            return redirect('journalist_dashboard')

    else:

        form = ArticleForm(user=request.user)

    return render(
        request,
        'good_to_know/article_form.html',
        {
            'form': form,
            'page_title': 'Create Article',
        }
    )


# Journalist edit article
@login_required
@user_passes_test(is_journalist)
def edit_article(request, article_id):
    ''' Function handles article editing. If affiliated with a publisher
        an edited article will require approval again. Approved articles
        can't be edited but can be deleted
    '''

    article = get_object_or_404(
        Article,
        id=article_id,
        author=request.user
    )

    form = ArticleForm(
        request.POST or None,
        request.FILES or None,
        instance=article
    )
    form.fields['publisher'].queryset = request.user.publishers.all()

    if request.method == 'POST':

        if form.is_valid():

            article = form.save(commit=False)

            # Changes require fresh approval.
            if article.publisher:
                article.approved = False
            else:
                article.approved = True

            article.save()

            messages.success(
                request,
                'Article updated successfully.'
            )

            return redirect('journalist_dashboard')

    return render(
        request,
        'good_to_know/article_form.html',
        {
            'form': form,
            'page_title': 'Edit Article',
        }
    )


# Delete article

@login_required
@user_passes_test(is_journalist)
@require_POST
def delete_article(request, article_id):
    ''' Function handles rticle deletion'''

    article = get_object_or_404(
        Article,
        id=article_id,
        author=request.user
    )

    article.delete()

    messages.success(
        request,
        'Article deleted successfully.'
    )

    return redirect('journalist_dashboard')


# Journalist create newsletter

@login_required
@user_passes_test(is_journalist)
def create_newsletter(request):
    ''' Function handles newsletter creation. Independant journalists
        can also create newsletters, using their own articles.'''

    if request.method == 'POST':

        form = NewsletterForm(
            request.POST,
            user=request.user
        )
        if form.is_valid():
            try:
                with transaction.atomic():
                    newsletter = form.save(commit=False)
                    newsletter.author = request.user

                    newsletter.publisher = form.cleaned_data['publisher']

                    if newsletter.publisher:
                        newsletter.approved = False
                    else:
                        newsletter.approved = True

                    newsletter.save()
                    form.save_m2m()

                    messages.success(
                        request,
                        'Newsletter created successfully.'
                    )

                    return redirect('newsletter_detail',
                                    newsletter_id=newsletter.id)
            except Exception as e:
                messages.error(request,
                               f'Problem creating this newsletter: {e}'
                               'Please try again.')
    else:
        form = NewsletterForm(user=request.user)

    return render(
        request,
        'good_to_know/newsletter_form.html',
        {
            'form': form,
            'page_title': 'Create Newsletter',
        }
    )


# Journalist edit newsletter
@login_required
@user_passes_test(is_journalist)
def edit_newsletter(request, newsletter_id):
    ''' Newsletters can be edited before approval if newsletter
        is affiliated with a publisher'''

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        author=request.user
    )

    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        user=request.user
    )

    if request.method == 'POST':

        if form.is_valid():

            newsletter = form.save(commit=False)

            if newsletter.publisher:
                newsletter.approved = False
            else:
                newsletter.approved = True

            newsletter.save()
            form.save_m2m()

            messages.success(
                request,
                'Newsletter updated successfully.'
            )

            return redirect('journalist_dashboard')

    return render(
        request,
        'good_to_know/newsletter_form.html',
        {
            'form': form,
            'page_title': 'Edit Newsletter',
        }
    )


# Journalist delete newsletter
@login_required
@user_passes_test(is_journalist)
@require_POST
def delete_newsletter(request, newsletter_id):
    ''' Function handles newsletter deletion. '''

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        author=request.user
    )

    newsletter.delete()

    messages.success(
        request,
        'Newsletter deleted successfully.'
    )

    return redirect('home')


# Editor article management
'''
    Article and newsletter affilitaion with the editor's publisher is
    defined to make further checking efficient.
    Editor's can edit, approve and delete publications. As according
    to the specification, creation is done by journalists.
    Upon approval of publications, they're issued to subscribers via email.
    For the purpose of this task, emails also appear in console.
'''


# Content filter
def editor_articles(user):
    ''' Function handles filtering of editors articles for dashboard view. '''

    publishers = user.editor_publishers.all()

    if not publishers.exists():
        raise PermissionDenied(
            'Your editor account has no assigned publisher.'
        )

    return Article.objects.filter(
        publisher__in=publishers
    )


def editor_newsletters(user):
    ''' Function handles filtering editor newsletters for viewing'''

    publishers = user.editor_publishers.all()

    if not publishers.exists():
        raise PermissionDenied(
            'Your editor account has no assigned publisher.'
        )

    # Only newsletters containing articles from this publisher.
    # Exclude newsletters containing articles from other publishers.
    return Newsletter.objects.filter(
        publisher__in=publishers
    )


# Editor edit article
@login_required
@user_passes_test(is_editor)
def editor_edit_article(request, article_id):
    ''' Function handles editor role when editing article '''

    article = get_object_or_404(
        editor_articles(request.user),
        id=article_id
    )

    form = ArticleForm(
        request.POST or None,
        request.FILES or None,
        instance=article,
        user=request.user
    )
    form.fields['publisher'].queryset = (
        request.user.editor_publishers.all()
    )

    if request.method == 'POST':

        if form.is_valid():
            article = form.save(commit=False)
            article.approved = False
            article.save()

            messages.success(
                request,
                'Article updated successfully.'
            )

            return redirect('editor_dashboard')

    return render(
        request,
        'good_to_know/article_form.html',
        {
            'form': form,
            'page_title': 'Edit Article',
        }
    )


# Delete article editor
@login_required
@user_passes_test(is_editor)
@require_POST
def editor_delete_article(request, article_id):
    ''' Function handles deletion of article by editor'''

    article = get_object_or_404(
        editor_articles(request.user),
        id=article_id
    )

    article.delete()

    messages.success(
        request,
        'Article deleted successfully.'
    )

    return redirect('editor_dashboard')


# Editor approve article
@login_required
@user_passes_test(is_editor)
@require_POST
def approve_article(request, article_id):
    ''' Function handles approval of article by editor'''

    article = get_object_or_404(
        editor_articles(request.user),
        id=article_id
    )

    article.approved = True
    article.save(update_fields=['approved'])

    messages.success(
        request,
        'Article approved successfully.'
    )
    subscribers = article.publisher.subscribers.all()
    recipient_emails = [
        subscriber.email
        for subscriber in subscribers
        if subscriber.email
    ]

    try:
        subscriber_html = render_to_string(
            'good_to_know/article_subscriber.html',
            {
                'article': article,
            }
        )

        email = EmailMessage(
            subject=f'When we know, you know.'
                    f'New realease from: {article.author}',
            body='Thank you for subsribing with Good To Know. '
                 'Your article is attached.',
            from_email=None,
            to=recipient_emails
        )

        email.attach(
            f'article_subscriber_{article.author.username.strip()}.html',
            subscriber_html,
            'text/html'
        )

        email.send(fail_silently=False)

        messages.success(
            request,
            'Article distributed to subscriebrs.'
        )

    except (smtplib.SMTPException, OSError) as error:
        logger.error('Email failed: %s', error)
        messages.warning(
            request,
            'Approval was successful, but we could not send the article. '
        )

    return redirect('editor_dashboard')


# Editor approve newsletter
@login_required
@user_passes_test(is_editor)
@require_POST
def approve_newsletter(request, newsletter_id):
    ''' Function handles approval of newsletter by editor'''

    newsletter = get_object_or_404(
        editor_newsletters(request.user),
        id=newsletter_id
    )

    newsletter.approved = True
    newsletter.save(update_fields=['approved'])

    messages.success(
        request,
        'Newsletter approved successfully.'
    )
    subscribers = newsletter.publisher.subscribers.all()

    recipient_emails = [
        subscriber.email
        for subscriber in subscribers
        if subscriber.email
    ]
    try:
        subscriber_html = render_to_string(
            'good_to_know/article_subscriber.html',
            {
                'newsletter': newsletter,
            }
        )

        email = EmailMessage(
            subject=f'When we know, you know.'
                    f'New realease from: {newsletter.author}',
            body='Thank you for subsribing with Good To Know. '
                 'Your newsletter is attached.',
            from_email=None,
            to=recipient_emails
        )

        email.attach(
            f'newsletetr_subscriber_{newsletter.author.username.strip()}.html',
            subscriber_html,
            'text/html'
        )

        email.send(fail_silently=False)

        messages.success(
            request,
            'Article distributed to subscriebrs.'
        )

    except (smtplib.SMTPException, OSError) as error:
        logger.error('Email failed: %s', error)
        messages.warning(
            request,
            'Approval was successful, but we could not send the article. '
        )

    return redirect('editor_dashboard')


# Edit newsletter update
@login_required
@user_passes_test(is_editor)
def editor_edit_newsletter(request, newsletter_id):
    ''' Function handles editor, editing newsletter'''

    newsletter = get_object_or_404(
        editor_newsletters(request.user),
        id=newsletter_id
    )

    form = NewsletterForm(
        request.POST or None,
        instance=newsletter,
        user=request.user
    )
    form.fields['articles'].queryset = (Article.objects.filter(
        publisher=newsletter.publisher)
    )

    if request.method == 'POST':

        if form.is_valid():

            newsletter = form.save(commit=False)
            newsletter.approved = False
            newsletter.save()
            form.save_m2m()

            messages.success(
                request,
                'Newsletter updated successfully.'
            )

            return redirect('editor_dashboard')

    return render(
        request,
        'good_to_know/newsletter_form.html',
        {
            'form': form,
            'page_title': 'Edit Newsletter',
        }
    )


# Editor delete newsletter
@login_required
@user_passes_test(is_editor)
@require_POST
def editor_delete_newsletter(request, newsletter_id):
    ''' Function handles editor deleting newsletter'''

    newsletter = get_object_or_404(
        editor_newsletters(request.user),
        id=newsletter_id
    )

    newsletter.delete()

    messages.success(
        request,
        'Newsletter deleted successfully.'
    )

    return redirect('editor_dashboard')


# Subscription
'''
    Readers will utilise the session management capability to retain their
    subscribtion data. The subscribe function will displayed in the
    browse pages for readers. Journalist and editor accounts are restricted
    from this capability.
'''


@login_required
@user_passes_test(is_reader)
@require_POST
def subscribe_publisher(request, publisher_id):
    ''' Function handles reader account subscription for publishers'''

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    request.user.subscribed_publishers.add(publisher)

    messages.success(
        request,
        f"You have subscribed to {publisher.name}."
    )

    return redirect("home")


@login_required
@user_passes_test(is_reader)
@require_POST
def unsubscribe_publisher(request, publisher_id):
    ''' Function handles reader account un-subscription for publishers'''

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    request.user.subscribed_publishers.remove(publisher)

    messages.success(
        request,
        f"You have unsubscribed from {publisher.name}."
    )

    return redirect("reader_dashboard")


@login_required
@user_passes_test(is_reader)
@require_POST
def subscribe_journalist(request, journalist_id):
    ''' Function handles reader account subscription for journalists '''

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role=CustomUser.Role.JOURNALIST
    )

    request.user.subscribed_journalists.add(journalist)

    messages.success(
        request,
        f"You have subscribed to {journalist.username}."
    )

    return redirect("home")


@login_required
@user_passes_test(is_reader)
@require_POST
def unsubscribe_journalist(request, journalist_id):
    ''' Function handles reader account un-subscription for journalists '''

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role=CustomUser.Role.JOURNALIST
    )

    request.user.subscribed_journalists.remove(journalist)

    messages.success(
        request,
        f"You have unsubscribed from {journalist.username}."
    )

    return redirect("reader_dashboard")


# Browse functions
'''
    The following functions enable the user to browse: articles,
    journalists, publishers and newsletters. As previously stated,
    this enables the users to view publications accross the database.
    As their own dashboards are restricted to their affiliated
    publications.
'''


# Browse publishers
def browse_publishers(request):
    ''' Functions handles collation of all publishers'''

    publishers = Publisher.objects.all().order_by('name')
    subscribed_publisher_ids = []

    if request.user.is_authenticated and is_reader(request.user):
        subscribed_publisher_ids = list(
            request.user.subscribed_publishers.values_list(
                'id',
                flat=True
            )
        )

    return render(
        request,
        'good_to_know/browse_publishers.html',
        {
            'publishers': publishers,
            'subscribed_publisher_ids': subscribed_publisher_ids,
        }
    )


# Browse journalists
def browse_journalists(request):
    '''  Functions handles collation of all journalists '''

    journalists = User.objects.filter(
        role=CustomUser.Role.JOURNALIST
    ).order_by('username')

    subscribed_journalist_ids = []

    if request.user.is_authenticated and is_reader(request.user):
        subscribed_journalist_ids = list(
            request.user.subscribed_journalists.values_list(
                'id',
                flat=True
            )
        )
    return render(
        request,
        'good_to_know/browse_journalists.html',
        {
            'journalists': journalists,
            'subscribed_ids': subscribed_journalist_ids,
        }
    )


# Collections
'''
    Collections collate the publications for publishers and journalists.
    This facilitates the ability to contain a readers subscribed materials.
    Whilst also forming a core element to the browse functions. Working
    together, the browse function allows the partitioning of publications
    accross journalists and publishers and select collections to view the
    entirety of their work.
'''


def publisher_collection(request, publisher_id):
    ''' Function handles display of a publishers collection '''

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    articles = Article.objects.filter(
        publisher=publisher,
        approved=True
    ).select_related(
        'author'
    ).order_by('-created_at')

    newsletters = Newsletter.objects.filter(
        publisher=publisher,
        approved=True
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    journalists = CustomUser.objects.filter(
        role=CustomUser.Role.JOURNALIST,
        publishers=publisher
    ).order_by('username')

    return render(
        request,
        'good_to_know/publisher_collection.html',
        {
            'publisher': publisher,
            'articles': articles,
            'newsletters': newsletters,
            'journalists': journalists,
        }
    )


def journalist_collection(request, journalist_id):
    '''  Function handles display of a journalists collection  '''

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role=CustomUser.Role.JOURNALIST
    )

    articles = Article.objects.filter(
        author=journalist,
        approved=True
    ).order_by('-created_at')

    newsletters = Newsletter.objects.filter(
        author=journalist,
        approved=True
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/journalist_collection.html',
        {
            'journalist': journalist,
            'articles': articles,
            'newsletters': newsletters,
        }
    )


# Browse newsletters
def browse_newsletters(request):
    '''  Function handles display of all newsletters. '''

    newsletters = Newsletter.objects.filter(
        approved=True
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/browse_newsletters.html',
        {
            'newsletters': newsletters,
        }
    )


# Browse articles
def browse_articles(request):
    ''' Function handles display of all articles'''

    articles = Article.objects.filter(
        approved=True
    ).order_by('-created_at')

    return render(
        request,
        'good_to_know/browse_articles.html',
        {
            'articles': articles,
        }
    )


# API Functions
def api_get_reader(user):
    """
    Check that the authenticated user is a reader.
    """
    if user.role != CustomUser.Role.READER:
        raise PermissionDenied(
            "Only readers can access this endpoint."
        )

    return user


def api_get_journalist(user):
    """Check that the authenticated user is a journalist."""

    if user.role != CustomUser.Role.JOURNALIST:
        raise PermissionDenied(
            "Only journalists can access this endpoint."
        )

    return user


def api_get_editor_publisher(user):
    """Get the publisher assigned to the authenticated editor."""

    if user.role != CustomUser.Role.EDITOR:
        raise PermissionDenied(
            "Only editors can access this endpoint."
        )
    publishers = user.editor_publishers.all()

    if not publishers.exists():
        raise PermissionDenied(
            "Your editor account has no assigned publisher."
        )

    return publishers


def api_validate_model(instance):
    """Run Django model validation and return errors as API errors."""

    from django.core.exceptions import ValidationError as DjangoValidationError

    try:
        instance.full_clean()
    except DjangoValidationError as error:
        raise ValidationError(
            getattr(error, 'message_dict', error.messages)
        )


def api_get_articles(request, **filters):
    """Retrieve and validate article IDs submitted to a newsletter."""

    article_ids = request.data.get('articles', [])

    if not isinstance(article_ids, list):
        raise ValidationError(
            "Articles must be supplied as a list of IDs."
        )

    if len(article_ids) != len(set(article_ids)):
        raise ValidationError(
            "Duplicate article IDs are not allowed."
        )

    articles = Article.objects.filter(
        id__in=article_ids,
        **filters
    )

    if articles.count() != len(article_ids):
        raise ValidationError(
            "One or more selected articles are unavailable."
        )

    return articles


# View publishers
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_publishers(request):
    ''' Retrieve publishers'''
    publishers = Publisher.objects.all().order_by('name')

    serializer = PublisherSerializer(
        publishers,
        many=True
    )

    return Response(serializer.data)


# View publisher journalists
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_publisher_journalists(request, publisher_id):
    ''' Retrieve journalists affiliated with the publisher'''

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    journalists = CustomUser.objects.filter(
        role=CustomUser.Role.JOURNALIST,
        publishers=publisher
    ).order_by('username')

    data = [
        {
            'id': journalist.id,
            'username': journalist.username,
        }
        for journalist in journalists
    ]

    return Response(data)


# View approved articles
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_all_articles(request):
    ''' Retrieve only approved articles'''

    articles = Article.objects.filter(
        approved=True
    ).select_related(
        'author',
        'publisher'
    ).order_by('-created_at')

    serializer = ArticleSerializer(
        articles,
        many=True
    )

    return Response(serializer.data)


# View approved newsletters
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_all_newsletters(request):
    ''' Retrieve only approved newsletters'''

    newsletters = Newsletter.objects.filter(
        approved=True
    ).select_related(
        'author',
        'publisher'
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    serializer = NewsletterSerializer(
        newsletters,
        many=True
    )

    return Response(serializer.data)


# View Journalist articles - subscribed only
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_journalist_articles(request, journalist_id):
    ''' Retrieve articles of journalists to which user is subscribed. '''

    reader = api_get_reader(request.user)

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role=CustomUser.Role.JOURNALIST
    )

    # Check journalist subscription.
    if not reader.subscribed_journalists.filter(
        id=journalist.id
    ).exists():
        raise PermissionDenied(
            "You must subscribe to this journalist to view their articles."
        )

    articles = Article.objects.filter(
        author=journalist,
        approved=True
    ).order_by('-created_at')

    serializer = ArticleSerializer(
        articles,
        many=True
    )

    return Response(serializer.data)


# Subscribed only, view publisher articles
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_publisher_articles(request, publisher_id):
    ''' Retrieve articles of publisher to which user is subscribed'''

    reader = api_get_reader(request.user)

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    # Check publisher subscription.
    if not reader.subscribed_publishers.filter(
        id=publisher.id
    ).exists():
        raise PermissionDenied(
            "You must subscribe to this publisher to view its articles."
        )

    articles = Article.objects.filter(
        publisher=publisher,
        approved=True
    ).select_related(
        'author'
    ).order_by('-created_at')

    serializer = ArticleSerializer(
        articles,
        many=True
    )

    return Response(serializer.data)


# View journalist newsletters
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_journalist_newsletters(request, journalist_id):
    ''' Retrieve newsletters of journalist to which user is subscribed. '''

    reader = api_get_reader(request.user)

    journalist = get_object_or_404(
        CustomUser,
        id=journalist_id,
        role=CustomUser.Role.JOURNALIST
    )

    # Check journalist subscription.
    if not reader.subscribed_journalists.filter(
        id=journalist.id
    ).exists():
        raise PermissionDenied(
            "You must subscribe to this journalist to view their newsletters."
        )

    newsletters = Newsletter.objects.filter(
        author=journalist,
        approved=True
    ).select_related(
        'publisher'
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    serializer = NewsletterSerializer(
        newsletters,
        many=True
    )

    return Response(serializer.data)


# View publisher details
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_publisher_newsletters(request, publisher_id):
    ''' Retrieve newsletters of publisher to which user is subscribed'''

    reader = api_get_reader(request.user)

    publisher = get_object_or_404(
        Publisher,
        id=publisher_id
    )

    # Check publisher subscription.
    if not reader.subscribed_publishers.filter(
        id=publisher.id
    ).exists():
        raise PermissionDenied(
            "You must subscribe to this publisher to view its newsletters."
        )

    newsletters = Newsletter.objects.filter(
        publisher=publisher,
        approved=True
    ).select_related(
        'author'
    ).prefetch_related(
        'articles'
    ).order_by('-created_at')

    serializer = NewsletterSerializer(
        newsletters,
        many=True
    )

    return Response(serializer.data)


# Journalists can view their subscibers
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_journalist_subscribers(request):
    ''' View username of subscribers for journalist'''

    journalist = api_get_journalist(request.user)

    subscribers = journalist.journalist_subscribers.filter(
        role=CustomUser.Role.READER
    ).order_by('username')

    data = [
        {
            'id': subscriber.id,
            'username': subscriber.username
        }
        for subscriber in subscribers
    ]

    return Response(data)


# Publishers view their subscribers
@api_view(['GET'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def view_publisher_subscribers(request):
    ''' View usernames of subscribers of publisher'''

    publishers = api_get_editor_publisher(request.user)

    subscribers = CustomUser.objects.filter(
        role=CustomUser.Role.READER,
        subscribed_publishers__in=publishers
    ).distinct().order_by('username')

    data = [
        {
            'id': subscriber.id,
            'username': subscriber.username
        }
        for subscriber in subscribers
    ]

    return Response(data)


# Journalists create articles
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_create_article(request):
    ''' Create article if journalist'''

    journalist = api_get_journalist(request.user)

    serializer = ArticleSerializer(data=request.data)

    if serializer.is_valid():

        values = dict(serializer.validated_data)

        # Never allow the client to choose the author or approval.
        values.pop('author', None)
        values.pop('approved', None)

        publisher = values.get('publisher')

        if publisher and not journalist.publishers.filter(
            id=publisher.id
        ).exists():
            raise PermissionDenied(
                "You do not belong to this publisher."
            )

        article = Article(
            author=journalist,
            approved=False if publisher else True,
            **values
        )

        api_validate_model(article)
        with transaction.atomic():
            article.save()

        return Response(
            ArticleSerializer(article).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Journalists create newsletters
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_create_newsletter(request):
    ''' Create newsletter'''

    journalist = api_get_journalist(request.user)

    publisher_id = request.data.get('publisher')
    article_ids = request.data.get('articles', [])

    publisher = None

    if publisher_id:
        publisher = get_object_or_404(
            Publisher,
            id=publisher_id
        )

        if not journalist.publishers.filter(
            id=publisher.id
        ).exists():
            raise PermissionDenied(
                "You do not belong to this publisher."
            )

    # Validate article IDs
    if not isinstance(article_ids, list):
        raise ValidationError({
            "articles": "Must be an array of article IDs."
        })

    articles = api_get_articles(
        request,
        author=journalist
    )

    # Ensure all submitted IDs belong to journalist
    if articles.count() != len(set(article_ids)):
        raise ValidationError(
            "One or more articles are invalid or do not belong to you."
        )

    # Validate publisher ownership
    if publisher:
        if articles.exclude(publisher=publisher).exists():
            raise ValidationError(
                "All newsletter articles must belong to its publisher."
            )

    serializer = NewsletterSerializer(
        data=request.data
    )

    if serializer.is_valid():

        values = dict(serializer.validated_data)
        values.pop('publisher', None)
        values.pop('author', None)
        values.pop('approved', None)

        # Remove articles to avoid duplicate assignment
        values.pop('articles', None)

        newsletter = Newsletter(
            author=journalist,
            publisher=publisher,
            approved=False if publisher else True,
            **values
        )

        api_validate_model(newsletter)
        with transaction.atomic():
            newsletter.save()

            newsletter.articles.set(articles)

        return Response(
            NewsletterSerializer(newsletter).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Editor create newsletters
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def publisher_create_newsletter(request):
    ''' View for editor account to create newsletter under publisher'''

    publishers = api_get_editor_publisher(request.user)
    publisher_id = request.data.get('publisher')
    publisher = get_object_or_404(
        publishers,
        id=publisher_id
    )

    articles = api_get_articles(
        request,
        publisher=publisher
    )

    serializer = NewsletterSerializer(
        data=request.data
    )

    if serializer.is_valid():
        values = dict(serializer.validated_data)
        values.pop('articles', None)
        values.pop('publisher', None)

        newsletter = Newsletter(
            author=request.user,
            publisher=publisher,
            approved=False,
            **values
        )

        api_validate_model(newsletter)
        with transaction.atomic():
            newsletter.save()

            newsletter.articles.set(articles)

        return Response(
            NewsletterSerializer(newsletter).data,
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Journalists edit articles
@api_view(['PUT', 'PATCH'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_edit_article(request, article_id):
    ''' Journalist edit article'''

    journalist = api_get_journalist(request.user)

    article = get_object_or_404(
        Article,
        id=article_id,
        author=journalist
    )

    serializer = ArticleSerializer(
        article,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():

        values = dict(serializer.validated_data)

        # Preserve ownership and approval control.
        values.pop('author', None)
        values.pop('approved', None)

        publisher = values.get(
            'publisher',
            article.publisher
        )

        if publisher and not journalist.publishers.filter(
            id=publisher.id
        ).exists():
            raise PermissionDenied(
                "You do not belong to this publisher."
            )

        for field, value in values.items():
            setattr(article, field, value)

        article.author = journalist
        article.approved = bool(article.publisher is None)

        api_validate_model(article)
        with transaction.atomic():
            article.save()

        return Response(
            ArticleSerializer(article).data,
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Editor edit publisher articles
@api_view(['PUT', 'PATCH'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def publisher_edit_article(request, article_id):
    ''' Editor function edits article'''

    publishers = api_get_editor_publisher(request.user)

    article = get_object_or_404(
        Article,
        id=article_id,
        publisher__in=publishers
    )

    publisher = article.publisher

    serializer = ArticleSerializer(
        article,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():

        values = dict(serializer.validated_data)

        author = values.pop(
            'author',
            article.author
        )

        # Prevent the editor from changing publisher ownership.
        values.pop('publisher', None)
        values.pop('approved', None)

        if not author or not publisher.journalists.filter(
            id=author.id
        ).exists():
            raise ValidationError(
                "The journalist must belong to your publisher."
            )

        for field, value in values.items():
            setattr(article, field, value)

        article.author = author
        article.publisher = publisher
        article.approved = False

        api_validate_model(article)
        with transaction.atomic():
            article.save()

        return Response(
            ArticleSerializer(article).data,
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Journalist edit newsletters
@api_view(['PUT', 'PATCH'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_edit_newsletter(request, newsletter_id):
    ''' Journalist edits newsletter'''

    journalist = api_get_journalist(request.user)

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        author=journalist
    )

    # Retain the existing publisher unless one is supplied.
    publisher = newsletter.publisher

    if 'publisher' in request.data:

        publisher_id = request.data.get('publisher')

        if publisher_id:
            publisher = get_object_or_404(
                Publisher,
                id=publisher_id
            )

            if not journalist.publishers.filter(
                id=publisher.id
            ).exists():
                raise PermissionDenied(
                    "You do not belong to this publisher."
                )
        else:
            publisher = None

    # Only validate article IDs if the request includes them.
    articles = None

    if 'articles' in request.data:

        articles = api_get_articles(
            request,
            author=journalist
        )

        if publisher and articles.exclude(
            publisher=publisher
        ).exists():
            raise ValidationError(
                "Selected articles must belong to the newsletter's publisher."
            )

    serializer = NewsletterSerializer(
        newsletter,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():

        values = dict(serializer.validated_data)

        values.pop('articles', None)
        values.pop('publisher', None)
        values.pop('author', None)
        values.pop('approved', None)

        for field, value in values.items():
            setattr(newsletter, field, value)

        newsletter.author = journalist
        newsletter.publisher = publisher
        newsletter.approved = False if publisher else True

        api_validate_model(newsletter)
        with transaction.atomic():
            newsletter.save()

        if articles is not None:
            newsletter.articles.set(articles)

        return Response(
            NewsletterSerializer(newsletter).data,
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Editor edit newsletters
@api_view(['PUT', 'PATCH'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def publisher_edit_newsletter(request, newsletter_id):
    ''' Editor edits newsletter under publisher'''

    publishers = api_get_editor_publisher(request.user)

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        publisher__in=publishers
    )

    publisher = newsletter.publisher

    articles = None

    if 'articles' in request.data:

        articles = api_get_articles(
            request,
            publisher=publisher
        )

    serializer = NewsletterSerializer(
        newsletter,
        data=request.data,
        partial=request.method == 'PATCH'
    )

    if serializer.is_valid():

        values = dict(serializer.validated_data)
        values.pop('articles', None)
        values.pop('publisher', None)

        for field, value in values.items():
            setattr(newsletter, field, value)

        # Preserve the publisher and assign the editor.
        newsletter.publisher = publisher
        newsletter.approved = False

        api_validate_model(newsletter)
        with transaction.atomic():
            newsletter.save()

        if articles is not None:
            newsletter.articles.set(articles)

        return Response(
            NewsletterSerializer(newsletter).data,
            status=status.HTTP_200_OK
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# Journalist delete article
@api_view(['DELETE'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_delete_article(request, article_id):
    ''' Journalist deletes article'''

    journalist = api_get_journalist(request.user)

    article = get_object_or_404(
        Article,
        id=article_id,
        author=journalist
    )

    article.delete()

    return Response(
        {'message': 'Article deleted successfully.'},
        status=status.HTTP_200_OK
    )


# Editor delete publisher article
@api_view(['DELETE'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def publisher_delete_article(request, article_id):
    ''' Deletes article for publishers'''

    publishers = api_get_editor_publisher(request.user)

    article = get_object_or_404(
        Article,
        id=article_id,
        publisher__in=publishers
    )

    article.delete()

    return Response(
        {'message': 'Article deleted successfully.'},
        status=status.HTTP_200_OK
    )


# Journalist delete newsletter
@api_view(['DELETE'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def journalist_delete_newsletter(request, newsletter_id):
    ''' Delete newsletter for journalist'''

    journalist = api_get_journalist(request.user)

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        author=journalist
    )

    newsletter.delete()

    return Response(
        {'message': 'Newsletter deleted successfully.'},
        status=status.HTTP_200_OK
    )


# Eedit publisher newsletter
@api_view(['DELETE'])
@authentication_classes([BasicAuthentication])
@permission_classes([IsAuthenticated])
def publisher_delete_newsletter(request, newsletter_id):
    ''' Deletes newsletter for publisher '''

    publishers = api_get_editor_publisher(request.user)

    newsletter = get_object_or_404(
        Newsletter,
        id=newsletter_id,
        publisher__in=publishers
    )

    newsletter.delete()

    return Response(
        {'message': 'Newsletter deleted successfully.'},
        status=status.HTTP_200_OK
    )
