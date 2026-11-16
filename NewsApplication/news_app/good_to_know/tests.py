# Structure for test function adapted from previous
# unit tests project submission
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model

from good_to_know import views

from good_to_know.models import (
    CustomUser,
    Publisher,
    Article,
    Newsletter
)


# Test setup

class BaseAPITestCase(APITestCase):
    def setUp(self):
        """create users, publishers, articles and subscriptions for testing."""

        # Create publishers
        self.publisher1 = Publisher.objects.create(
            name="Publisher One"
        )

        self.publisher2 = Publisher.objects.create(
            name="Publisher Two"
        )

        # Create reader
        self.reader = CustomUser.objects.create_user(
            username="reader",
            password="password123",
            role=CustomUser.Role.READER
        )

        # Create journalist
        self.journalist = CustomUser.objects.create_user(
            username="journalist",
            password="password123",
            role=CustomUser.Role.JOURNALIST
        )

        # Create editor
        self.editor = CustomUser.objects.create_user(
            username="editor",
            password="password123",
            role=CustomUser.Role.EDITOR
        )
        # Assign journalist to publisher
        self.journalist.publishers.add(
            self.publisher1
        )
        self.editor.editor_publishers.add(
            self.publisher1
        )

        # Create approved articles
        self.article1 = Article.objects.create(
            title="Article One",
            content="Content One",
            author=self.journalist,
            publisher=self.publisher1,
            approved=True
        )

        self.article2 = Article.objects.create(
            title="Article Two",
            content="Content Two",
            author=self.journalist,
            publisher=self.publisher2,
            approved=True
        )

        # Create pending article
        self.pending_article = Article.objects.create(
            title="Pending Article",
            content="Not approved",
            author=self.journalist,
            publisher=self.publisher1,
            approved=False
        )

        # Create approved newsletter
        self.newsletter = Newsletter.objects.create(
            title="Newsletter One",
            description="Newsletter description",
            author=self.journalist,
            publisher=self.publisher1,
            approved=True
        )

        self.newsletter.articles.add(
            self.article1
        )

        # Subscribe reader to publisher and journalist
        self.reader.subscribed_publishers.add(
            self.publisher1
        )

        self.reader.subscribed_journalists.add(
            self.journalist
        )


# Authentication and role tests

class AuthenticationTests(BaseAPITestCase):

    def test_reader_can_access_publishers(self):
        """check that an authenticated reader can access publishers."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse('api_publishers')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_journalist_cannot_access_reader_endpoint(self):
        """check that journalists cannot access reader-only endpoints."""

        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.get(
            reverse(
                'view_journalist_articles',
                kwargs={
                    'journalist_id': self.journalist.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_editor_can_access_publisher_subscribers(self):
        """check that editors can access their publisher subscribers."""

        self.client.force_authenticate(
            user=self.editor
        )

        response = self.client.get(
            reverse('view_publisher_subscribers')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

    def test_unauthenticated_user_cannot_access_api(self):
        """check that unauthenticated users cannot access the api."""

        response = self.client.get(
            reverse('api_publishers')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


# Reader subscription tests

class SubscriptionAPITests(BaseAPITestCase):

    def test_reader_can_view_subscribed_publisher_articles(self):
        """check that readers can view articles from subscribed publishers."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse(
                'view_publisher_articles',
                kwargs={
                    'publisher_id': self.publisher1.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data),
            1
        )

        self.assertEqual(
            response.data[0]['title'],
            "Article One"
        )

    def test_reader_cannot_view_unsubscribed_publisher_articles(self):
        """check that readers cannot view articles from
            unsubscribed publishers.
        """

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse(
                'view_publisher_articles',
                kwargs={
                    'publisher_id': self.publisher2.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_reader_can_view_subscribed_journalist_articles(self):
        """check that readers can view articles from subscribed journalists."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse(
                'view_journalist_articles',
                kwargs={
                    'journalist_id': self.journalist.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data),
            2
        )

        self.assertEqual(
            response.data[0]['title'],
            "Article Two"
        )

    def test_reader_cannot_view_unsubscribed_journalist_articles(self):
        """check that readers cannot view articles from unsubscribed
            journalists."""

        self.client.force_authenticate(
            user=self.reader
        )

        other_journalist = CustomUser.objects.create_user(
            username="journalist2",
            password="password123",
            role=CustomUser.Role.JOURNALIST
        )

        response = self.client.get(
            reverse(
                'view_journalist_articles',
                kwargs={
                    'journalist_id': other_journalist.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_unauthenticated_user_cannot_access_articles(self):
        """check that unauthenticated users cannot access articles."""

        response = self.client.get(
            reverse(
                'view_publisher_articles',
                kwargs={
                    'publisher_id': self.publisher1.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_journalist_cannot_access_reader_subscription_endpoint(self):
        """check that journalists cannot access reader
            subscription endpoints."""

        self.client.force_authenticate(
            user=self.journalist
        )

        response = self.client.get(
            reverse(
                'view_publisher_articles',
                kwargs={
                    'publisher_id': self.publisher1.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )


# Newsletter tests

class NewsletterAPITests(BaseAPITestCase):

    def test_reader_can_view_subscribed_publisher_newsletters(self):
        """check that readers can view newsletters from subscribed
            publishers."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse(
                'view_publisher_newsletters',
                kwargs={
                    'publisher_id': self.publisher1.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            len(response.data),
            1
        )

    def test_reader_cannot_view_unsubscribed_publisher_newsletters(self):
        """check that readers cannot view newsletters from unsubscribed
            publishers."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse(
                'view_publisher_newsletters',
                kwargs={
                    'publisher_id': self.publisher2.id
                }
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )


class JournalistArticleTests(BaseAPITestCase):

    def test_journalist_can_create_publisher_article(self):
        """check that journalists can create articles for
            affiliated publishers."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse('create_article'),
            {
                'title': 'New Publisher Article',
                'content': 'Article content',
                'publisher': self.publisher1.id,
            }
        )

        self.assertEqual(response.status_code, 302)

        article = Article.objects.get(
            title='New Publisher Article'
        )

        self.assertEqual(article.author, self.journalist)
        self.assertEqual(article.publisher, self.publisher1)
        self.assertFalse(article.approved)

    def test_journalist_can_create_independent_article(self):
        """check that journalists can create articles without a publisher."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse('create_article'),
            {
                'title': 'Independent Article',
                'content': 'Independent content',
                'publisher': '',
            }
        )

        self.assertEqual(response.status_code, 302)

        article = Article.objects.get(
            title='Independent Article'
        )

        self.assertIsNone(article.publisher)
        self.assertTrue(article.approved)

    def test_journalist_cannot_select_unaffiliated_publisher(self):
        """check that journalists cannot select publishers they are not
            affiliated with."""

        self.client.force_login(self.journalist)

        response = self.client.post(
            reverse('create_article'),
            {
                'title': 'Invalid Publisher Article',
                'content': 'Article content',
                'publisher': self.publisher2.id,
            },
            follow=True
        )

        self.assertFalse(
            Article.objects.filter(
                title='Invalid Publisher Article'
            ).exists()
        )

    def test_reader_cannot_create_article(self):
        """check that readers do not have permission to create articles."""

        self.client.force_login(self.reader)

        response = self.client.post(
            reverse('create_article'),
            {
                'title': 'Reader Article',
                'content': 'Article content',
                'publisher': '',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Article.objects.filter(
                title='Reader Article'
            ).exists()
        )

    def test_unauthenticated_user_cannot_create_article(self):
        """check that users must be logged in to create articles."""

        response = self.client.post(
            reverse('create_article'),
            {
                'title': 'Unauthorised Article',
                'content': 'Article content',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Article.objects.filter(
                title='Unauthorised Article'
            ).exists()
        )


class EditorArticleTests(BaseAPITestCase):

    def test_editor_can_approve_article(self):
        """check that editors can approve pending articles from
            their publisher."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'approve_article',
                kwargs={
                    'article_id': self.pending_article.id
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.pending_article.refresh_from_db()

        self.assertTrue(self.pending_article.approved)

    def test_editor_cannot_approve_another_publishers_article(self):
        """check that editors cannot approve articles belonging to other
            publishers."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'approve_article',
                kwargs={
                    'article_id': self.article2.id
                }
            )
        )

        self.assertEqual(response.status_code, 404)

        self.article2.refresh_from_db()

        self.assertTrue(self.article2.approved)

    def test_editor_can_delete_own_publisher_article(self):
        """check that editors can delete articles belonging to
            their publisher."""

        self.client.force_login(self.editor)

        article_id = self.pending_article.id

        response = self.client.post(
            reverse(
                'editor_delete_article',
                kwargs={
                    'article_id': article_id
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Article.objects.filter(
                id=article_id
            ).exists()
        )

    def test_editor_cannot_delete_another_publishers_article(self):
        """check that editors cannot delete articles belonging to other
            publishers."""

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'editor_delete_article',
                kwargs={
                    'article_id': self.article2.id
                }
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Article.objects.filter(
                id=self.article2.id
            ).exists()
        )

    def test_reader_cannot_approve_article(self):
        """check that readers cannot approve pending articles."""

        self.client.force_login(self.reader)

        response = self.client.post(
            reverse(
                'approve_article',
                kwargs={
                    'article_id': self.pending_article.id
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.pending_article.refresh_from_db()

        self.assertFalse(self.pending_article.approved)

    def test_editor_cannot_delete_using_get_request(self):
        """check that article deletion cannot be performed using
            a get request."""

        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'editor_delete_article',
                kwargs={
                    'article_id': self.pending_article.id
                }
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertTrue(
            Article.objects.filter(
                id=self.pending_article.id
            ).exists()
        )


class ArticleApprovalEmailTests(BaseAPITestCase):

    @patch('good_to_know.views.EmailMessage.send')
    @patch('good_to_know.views.render_to_string')
    def test_article_approval_sends_email(
        self,
        mock_render,
        mock_send
    ):
        """check that approving an article triggers an email notification."""

        mock_render.return_value = '<html>Article</html>'
        mock_send.return_value = 1

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'approve_article',
                kwargs={
                    'article_id': self.pending_article.id
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.pending_article.refresh_from_db()

        self.assertTrue(self.pending_article.approved)

        mock_render.assert_called_once()

        mock_send.assert_called_once()

    @patch('good_to_know.views.EmailMessage.send')
    @patch('good_to_know.views.render_to_string')
    def test_article_remains_approved_if_email_fails(
        self,
        mock_render,
        mock_send
    ):
        """check that an email failure does not reverse
            article approval."""

        mock_render.return_value = '<html>Article</html>'

        mock_send.side_effect = OSError(
            'Email server unavailable'
        )

        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'approve_article',
                kwargs={
                    'article_id': self.pending_article.id
                }
            )
        )

        self.assertEqual(response.status_code, 302)

        self.pending_article.refresh_from_db()

        # Approval should remain successful.
        self.assertTrue(self.pending_article.approved)

        mock_send.assert_called_once()


class ApprovedArticlesAPITests(BaseAPITestCase):

    def test_api_returns_only_approved_articles(self):
        """check that pending articles are excluded from the api response."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse('view_all_articles')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        titles = [
            article['title']
            for article in response.data
        ]

        self.assertIn('Article One', titles)
        self.assertNotIn('Pending Article', titles)

    def test_api_excludes_pending_articles(self):
        """check that pending articles are excluded from the api response."""

        self.client.force_authenticate(
            user=self.reader
        )

        response = self.client.get(
            reverse('view_all_articles')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertFalse(
            any(
                article['id'] == self.pending_article.id
                for article in response.data
            )
        )

    def test_unauthenticated_user_cannot_access_approved_articles(self):
        """check that authentication is required to access approved
            articles."""

        response = self.client.get(
            reverse('view_all_articles')
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )
