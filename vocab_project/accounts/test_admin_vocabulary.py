from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class AdminVocabularyManagementTestCase(TestCase):
    """Test admin vocabulary management page"""

    def setUp(self):
        self.client = Client()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='testpass123',
            role='admin'
        )
        
        # Create learner user
        self.learner_user = User.objects.create_user(
            username='learner_test',
            email='learner@test.com',
            password='testpass123',
            role='learner'
        )

    def test_admin_can_access_vocabulary_management(self):
        """Test that admin can access vocabulary management page"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(reverse('admin_vocabulary_management'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vocabulary Management')
        self.assertTemplateUsed(response, 'admin/vocabulary_management.html')

    def test_learner_cannot_access_vocabulary_management(self):
        """Test that learner is redirected from vocabulary management"""
        self.client.login(username='learner_test', password='testpass123')
        
        response = self.client.get(reverse('admin_vocabulary_management'))
        self.assertEqual(response.status_code, 302)  # Redirect
        self.assertRedirects(response, reverse('dashboard'))

    def test_unauthenticated_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login"""
        response = self.client.get(reverse('admin_vocabulary_management'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/login/'))

    def test_admin_vocabulary_has_same_ui_as_vocabulary(self):
        """Test that admin vocabulary page has the same UI elements as regular vocabulary"""
        self.client.login(username='admin_test', password='testpass123')
        
        response = self.client.get(reverse('admin_vocabulary_management'))
        
        # Check for key UI elements from vocabulary page
        self.assertContains(response, 'id="sidebar"')
        self.assertContains(response, 'Search vocabulary')
        self.assertContains(response, 'All Vocabulary')
        self.assertContains(response, 'Published (System)')
        self.assertContains(response, 'My Vocabulary')
        self.assertContains(response, 'id="gridViewBtn"')
        self.assertContains(response, 'id="listViewBtn"')

    def test_sidebar_links_to_admin_vocabulary(self):
        """Test that sidebar in all pages links to admin_vocabulary_management"""
        self.client.login(username='admin_test', password='testpass123')
        
        pages = ['dashboard', 'vocabulary_list', 'topics_list']
        
        for page in pages:
            response = self.client.get(reverse(page))
            admin_vocab_url = reverse('admin_vocabulary_management')
            self.assertContains(
                response, 
                f'href="{admin_vocab_url}"',
                msg_prefix=f"Page {page} should link to admin vocabulary management"
            )
