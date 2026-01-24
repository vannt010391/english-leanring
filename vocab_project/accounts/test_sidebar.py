from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


class SidebarStructureTestCase(TestCase):
    """Test sidebar structure based on user roles according to Phase 3 requirements"""

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

    def test_admin_sidebar_structure(self):
        """Test that admin sees correct sidebar structure"""
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Get dashboard page
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check Admin Panel section exists
        self.assertContains(response, 'id="adminPanelSection"')
        self.assertContains(response, 'Admin Panel')
        
        # Check Admin Panel links exist
        self.assertContains(response, 'id="adminDashboardLink"')
        self.assertContains(response, 'id="adminUsersLink"')
        self.assertContains(response, 'id="adminNotificationsLink"')
        
        # Check Vocabulary admin links exist
        self.assertContains(response, 'id="adminVocabAnalyticsLink"')
        self.assertContains(response, 'id="adminVocabManagementLink"')
        self.assertContains(response, 'id="adminLearningPlansLink"')
        self.assertContains(response, 'id="adminPracticeMonitorLink"')
        
        # Check Grammar admin links exist
        self.assertContains(response, 'id="adminGrammarManagementLink"')
        self.assertContains(response, 'id="adminGrammarMonitorLink"')
        
        # Check Writing admin links exist
        self.assertContains(response, 'id="adminWritingManagementLink"')
        self.assertContains(response, 'id="adminWritingMonitorLink"')
        
        # Check Listening admin links exist
        self.assertContains(response, 'id="adminListeningManagementLink"')
        self.assertContains(response, 'id="adminListeningMonitorLink"')
        
        # Check learner Dashboard section exists (but should be hidden)
        self.assertContains(response, 'id="learnerDashboardSection"')
        
        # Check learner Analytics link exists (but should be hidden)
        self.assertContains(response, 'id="learnerAnalyticsLink"')
        
        # Verify NO learnerDashboardLink exists
        self.assertNotContains(response, 'id="learnerDashboardLink"')

    def test_learner_sidebar_structure(self):
        """Test that learner sees correct sidebar structure"""
        # Login as learner
        self.client.login(username='learner_test', password='testpass123')
        
        # Get dashboard page
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check Admin Panel section exists (but should be hidden)
        self.assertContains(response, 'id="adminPanelSection"')
        
        # Check Learner Dashboard section exists
        self.assertContains(response, 'id="learnerDashboardSection"')
        self.assertContains(response, 'Dashboard')
        
        # Check learner Analytics link exists
        self.assertContains(response, 'id="learnerAnalyticsLink"')
        self.assertContains(response, 'Analytics')
        
        # Verify NO learnerDashboardLink
        self.assertNotContains(response, 'id="learnerDashboardLink"')
        
        # Check learner Vocabulary links exist
        self.assertContains(response, 'id="learnerVocabularyLink"')
        self.assertContains(response, 'id="learnerLearningPlanLink"')
        self.assertContains(response, 'id="learnerPracticeVocabLink"')
        
        # Check learner Grammar links exist
        self.assertContains(response, 'id="learnerGrammarResourceLink"')
        self.assertContains(response, 'id="learnerGrammarPracticeLink"')
        
        # Check learner Writing links exist
        self.assertContains(response, 'id="learnerWritingResourceLink"')
        self.assertContains(response, 'id="learnerWritingPracticeLink"')
        
        # Check learner Listening links exist
        self.assertContains(response, 'id="learnerListeningResourceLink"')
        self.assertContains(response, 'id="learnerListeningPracticeLink"')

    def test_sidebar_vocabulary_management_link(self):
        """Test that Vocabulary Management points to admin_vocabulary_management page"""
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Get dashboard page
        response = self.client.get(reverse('dashboard'))
        
        # Check that adminVocabManagementLink points to admin_vocabulary_management URL
        admin_vocab_url = reverse('admin_vocabulary_management')
        self.assertContains(response, f'href="{admin_vocab_url}"')
        self.assertContains(response, 'Vocabulary Management')

    def test_sidebar_sections_count(self):
        """Test that correct number of sections exist"""
        # Login as admin
        self.client.login(username='admin_test', password='testpass123')
        
        # Get dashboard page
        response = self.client.get(reverse('dashboard'))
        content = response.content.decode()
        
        # Count sections
        # Should have: Admin Panel, Dashboard (learner), Vocabulary, Grammar, Writing, Listening = 6 sections
        section_count = content.count('nav-section-title')
        self.assertEqual(section_count, 6, f"Expected 6 sections, found {section_count}")
        
        # Verify section titles
        self.assertContains(response, '>Admin Panel<')
        self.assertContains(response, '>Dashboard<')
        self.assertContains(response, '>Vocabulary<')
        self.assertContains(response, '>Grammar<')
        self.assertContains(response, '>Writing<')
        self.assertContains(response, '>Listening<')

    def test_all_pages_have_sidebar(self):
        """Test that all main pages have the sidebar structure"""
        # Login as learner
        self.client.login(username='learner_test', password='testpass123')
        
        pages = [
            ('dashboard', 'Dashboard'),
            ('vocabulary_list', 'Vocabulary'),
            ('topics_list', 'Topics'),
            ('learning_plans', 'Learning Plans'),
            ('practice', 'Practice'),
            ('analytics', 'Analytics'),
        ]
        
        for url_name, page_name in pages:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 200, f"{page_name} page should be accessible")
            
            # Check sidebar exists
            self.assertContains(response, 'id="sidebar"', msg_prefix=f"{page_name} should have sidebar")
            
            # Check learner sections exist
            self.assertContains(response, 'id="learnerDashboardSection"', msg_prefix=f"{page_name} should have learner dashboard section")
            self.assertContains(response, 'id="learnerAnalyticsLink"', msg_prefix=f"{page_name} should have learner analytics link")
            
            # Verify NO learnerDashboardLink
            self.assertNotContains(response, 'id="learnerDashboardLink"', msg_prefix=f"{page_name} should NOT have learner dashboard link")
