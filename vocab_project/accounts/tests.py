from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from rest_framework import status

User = get_user_model()


class AuthenticationTests(APITestCase):
    """Test suite for authentication functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.login_url = reverse('login')
        self.api_login_url = '/api/auth/login/'
        self.dashboard_url = reverse('dashboard')
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )
        
        self.learner_user = User.objects.create_user(
            username='learner',
            email='learner@test.com',
            password='learner123',
            role='learner'
        )
    
    def test_api_login_creates_token(self):
        """Test that API login creates authentication token"""
        response = self.client.post(
            self.api_login_url,
            {'username': 'admin', 'password': 'admin123'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.json())
        self.assertIn('user', response.json())
        self.assertIn('redirect', response.json())
        
        # Verify token was created
        token = Token.objects.get(user=self.admin_user)
        self.assertEqual(response.json()['token'], token.key)
    
    def test_api_login_creates_session(self):
        """Test that API login creates Django session"""
        response = self.client.post(
            self.api_login_url,
            {'username': 'admin', 'password': 'admin123'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that session was created
        self.assertIn('sessionid', response.cookies)
    
    def test_api_login_invalid_credentials(self):
        """Test API login with invalid credentials"""
        response = self.client.post(
            self.api_login_url,
            {'username': 'admin', 'password': 'wrongpassword'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.json())
    
    def test_dashboard_requires_login(self):
        """Test that dashboard redirects to login when not authenticated"""
        response = self.client.get(self.dashboard_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_dashboard_accessible_after_login(self):
        """Test that dashboard is accessible after successful login"""
        # Login via API
        login_response = self.client.post(
            self.api_login_url,
            {'username': 'admin', 'password': 'admin123'},
            content_type='application/json'
        )
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Now try to access dashboard
        dashboard_response = self.client.get(self.dashboard_url)
        
        # Should be successful (200) not redirect
        self.assertEqual(dashboard_response.status_code, 200)
    
    def test_login_view_renders_template(self):
        """Test that login view renders the correct template"""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
    
    def test_logout_clears_session(self):
        """Test that logout clears session"""
        # Login first
        self.client.post(
            self.api_login_url,
            {'username': 'admin', 'password': 'admin123'},
            content_type='application/json'
        )
        
        # Logout
        logout_response = self.client.post('/api/auth/logout/')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Session should be cleared - dashboard should redirect to login
        dashboard_response = self.client.get(self.dashboard_url)
        self.assertEqual(dashboard_response.status_code, 302)


class UserManagementTests(APITestCase):
    """Test suite for user management functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )
        
        self.learner_user = User.objects.create_user(
            username='learner',
            email='learner@test.com',
            password='learner123',
            role='learner'
        )
        
        # Get admin token
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.learner_token = Token.objects.create(user=self.learner_user)
    
    def test_admin_can_list_users(self):
        """Test that admin can list all users"""
        response = self.client.get(
            '/api/auth/users/',
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.json())
    
    def test_learner_cannot_list_users(self):
        """Test that learner cannot access user management"""
        response = self.client.get(
            '/api/auth/users/',
            HTTP_AUTHORIZATION=f'Token {self.learner_token.key}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_admin_can_assign_role(self):
        """Test that admin can assign roles to users"""
        response = self.client.post(
            f'/api/auth/users/{self.learner_user.id}/assign_role/',
            {'role': 'admin'},
            format='json',
            HTTP_AUTHORIZATION=f'Token {self.admin_token.key}'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify role was changed
        self.learner_user.refresh_from_db()
        self.assertEqual(self.learner_user.role, 'admin')


class UserRoleTests(TestCase):
    """Test suite for user role functionality"""
    
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='admin123',
            role='admin'
        )
        
        self.learner_user = User.objects.create_user(
            username='learner',
            email='learner@test.com',
            password='learner123',
            role='learner'
        )
    
    def test_is_admin_method(self):
        """Test User.is_admin() method"""
        self.assertTrue(self.admin_user.is_admin())
        self.assertFalse(self.learner_user.is_admin())
    
    def test_is_learner_method(self):
        """Test User.is_learner() method"""
        self.assertFalse(self.admin_user.is_learner())
        self.assertTrue(self.learner_user.is_learner())
    
    def test_default_role_is_learner(self):
        """Test that default role for new users is learner"""
        user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='test123'
        )
        
        self.assertEqual(user.role, 'learner')
