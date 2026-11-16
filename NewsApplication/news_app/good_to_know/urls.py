
from django.urls import path
from . import views
from .views import RoleBasedLoginView


urlpatterns = [

    # Public homepage
    path('', views.welcome, name='welcome'),

    # Registration
    path('register/reader/', views.register_reader, name='register_reader'),
    path('register/journalist/',
         views.register_journalist, name='register_journalist'),
    path('register/editor/', views.register_editor, name='register_editor'),

    path('login/', RoleBasedLoginView.as_view(), name='login'),
    # Authentication
    path('logout/', views.logout_user, name='logout'),

    # User login page
    path('home/', views.home, name='home'),

    # Publication details
    path(
        'article/<int:article_id>/',
        views.article_detail,
        name='article_detail'
    ),

    path(
        'newsletter/<int:newsletter_id>/',
        views.newsletter_detail,
        name='newsletter_detail'
    ),

    # User dashboards
    path(
        'reader-dashboard/',
        views.reader_dashboard,
        name='reader_dashboard'
    ),

    path(
        'journalist/dashboard/',
        views.journalist_dashboard,
        name='journalist_dashboard'
    ),

    # Editor
    path(
        'editor/dashboard/',
        views.editor_dashboard,
        name='editor_dashboard'
    ),
    path(
        'publisher/create/',
        views.create_publisher,
        name='create_publisher'
    ),
    # Journalist article create, update delete urls
    path(
        'journalist/article/create/',
        views.create_article,
        name='create_article'
    ),

    path(
        'journalist/article/<int:article_id>/edit/',
        views.edit_article,
        name='edit_article'
    ),

    path(
        'journalist/article/<int:article_id>/delete/',
        views.delete_article,
        name='delete_article'
    ),

    # Editor article edit and delete, approve functions
    path(
        'editor/article/<int:article_id>/edit/',
        views.editor_edit_article,
        name='editor_edit_article'
    ),

    path(
        'editor/article/<int:article_id>/delete/',
        views.editor_delete_article,
        name='editor_delete_article'
    ),

    path(
        'editor/article/<int:article_id>/approve/',
        views.approve_article,
        name='approve_article'
    ),

    # Editor newsletter edit and delete, approve functions
    path(
        'editor/newsletter/<int:newsletter_id>/edit/',
        views.editor_edit_newsletter,
        name='editor_edit_newsletter'
    ),

    path(
        'editor/newsletter/<int:newsletter_id>/approve/',
        views.approve_newsletter,
        name='approve_newsletter'
    ),

    path(
        'editor/newsletter/<int:newsletter_id>/delete/',
        views.editor_delete_newsletter,
        name='editor_delete_newsletter'
    ),

    # Journalist newsletter create, edit delete functions
    path(
        'journalist/newsletter/create/',
        views.create_newsletter,
        name='create_newsletter'
    ),
    path(
        'journalist/newsletter/<int:newsletter_id>/edit/',
        views.edit_newsletter,
        name='edit_newsletter'
    ),
    path(
        'journalist/newsletter/<int:newsletter_id>/delete/',
        views.delete_newsletter,
        name='delete_newsletter'
    ),

    # Browse links
    path(
        'publishers/',
        views.browse_publishers,
        name='browse_publishers'
        ),

    path(
        'journalists/',
        views.browse_journalists,
        name='browse_journalists'
    ),

    path(
        'newsletters/',
        views.browse_newsletters,
        name='browse_newsletters'
    ),

    path(
        'articles/',
        views.browse_articles,
        name='browse_articles'
    ),

    # Collection links
    path(
        'publisher/<int:publisher_id>/collection/',
        views.publisher_collection,
        name='publisher_collection'
    ),

    path(
        'journalist/<int:journalist_id>/collection/',
        views.journalist_collection,
        name='journalist_collection'
    ),

    # Subscribtions
    path(
        'reader/<int:publisher_id>/subscribe/',
        views.subscribe_publisher,
        name='subscribe_publisher'
    ),

    path(
        'unsubscribe-publisher/<int:publisher_id>/',
        views.unsubscribe_publisher,
        name='unsubscribe_publisher'
    ),

    path(
        'subscribe-journalist/<int:journalist_id>/',
        views.subscribe_journalist,
        name='subscribe_journalist'
    ),

    path(
        'unsubscribe-journalist/<int:journalist_id>/',
        views.unsubscribe_journalist,
        name='unsubscribe_journalist'
    ),
    path(
        'api/articles/',
        views.view_all_articles,
        name='view_all_articles'
    ),

    path(
        'api/newsletters/',
        views.view_all_newsletters,
        name='view_all_newsletters'
    ),

    # API URL patterns

    # Publishers
    path(
        'api/publishers/',
        views.view_publishers,
        name='api_publishers'
    ),

    path(
        'api/publishers/<int:publisher_id>/journalists/',
        views.view_publisher_journalists,
        name='view_publisher_journalists'
    ),

    path(
        'api/publishers/<int:publisher_id>/articles/',
        views.view_publisher_articles,
        name='view_publisher_articles'
    ),

    path(
        'api/publishers/<int:publisher_id>/newsletters/',
        views.view_publisher_newsletters,
        name='view_publisher_newsletters'
    ),

    # Journalist content
    path(
        'api/journalists/<int:journalist_id>/articles/',
        views.view_journalist_articles,
        name='view_journalist_articles'
    ),

    path(
        'api/journalists/<int:journalist_id>/newsletters/',
        views.view_journalist_newsletters,
        name='view_journalist_newsletters'
    ),

    # Subscribers
    path(
        'api/journalist/subscribers/',
        views.view_journalist_subscribers,
        name='view_journalist_subscribers'
    ),

    path(
        'api/publisher/subscribers/',
        views.view_publisher_subscribers,
        name='view_publisher_subscribers'
    ),

    # Journalist article management
    path(
        'api/journalist/articles/create/',
        views.journalist_create_article,
        name='journalist_create_article'
    ),

    path(
        'api/journalist/articles/<int:article_id>/edit/',
        views.journalist_edit_article,
        name='journalist_edit_article'
    ),

    path(
        'api/journalist/articles/<int:article_id>/delete/',
        views.journalist_delete_article,
        name='journalist_delete_article'
    ),

    # Publisher article management
    path(
        'api/publisher/articles/<int:article_id>/edit/',
        views.publisher_edit_article,
        name='publisher_edit_article'
    ),

    path(
        'api/publisher/articles/<int:article_id>/delete/',
        views.publisher_delete_article,
        name='publisher_delete_article'
    ),

    # Journalist newsletter management
    path(
        'api/journalist/newsletters/create/',
        views.journalist_create_newsletter,
        name='journalist_create_newsletter'
    ),

    path(
        'api/journalist/newsletters/<int:newsletter_id>/edit/',
        views.journalist_edit_newsletter,
        name='journalist_edit_newsletter'
    ),

    path(
        'api/journalist/newsletters/<int:newsletter_id>/delete/',
        views.journalist_delete_newsletter,
        name='journalist_delete_newsletter'
    ),

    # Publisher newsletter management
    path(
        'api/publisher/newsletters/create/',
        views.publisher_create_newsletter,
        name='publisher_create_newsletter'
    ),

    path(
        'api/publisher/newsletters/<int:newsletter_id>/edit/',
        views.publisher_edit_newsletter,
        name='publisher_edit_newsletter'
    ),

    path(
        'api/publisher/newsletters/<int:newsletter_id>/delete/',
        views.publisher_delete_newsletter,
        name='publisher_delete_newsletter'
    ),
]
