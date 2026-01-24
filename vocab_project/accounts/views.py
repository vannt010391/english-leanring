from rest_framework import status, generics, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.http import JsonResponse

from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    UserListSerializer, UserManagementSerializer
)
from .permissions import IsAdmin

User = get_user_model()


class UserPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.get(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Check if user is already logged in
        if request.user and request.user.is_authenticated:
            return Response({
                'message': 'Already logged in',
                'redirect': '/dashboard/',
                'user': UserSerializer(request.user).data
            }, status=status.HTTP_200_OK)

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )

        if user:
            # Create Django session (for @login_required views)
            login(request, user)
            
            # Create or get token (for API authentication)
            token, _ = Token.objects.get_or_create(user=user)
            
            response = Response({
                'user': UserSerializer(user).data,
                'token': token.key,
                'redirect': '/dashboard/'
            })
            
            # Also set token in a secure cookie so it persists across redirects
            response.set_cookie(
                'auth_token',
                token.key,
                max_age=1209600,  # 2 weeks
                httponly=True,
                samesite='Lax',
                path='/'
            )
            
            return response
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Delete token
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        
        # Clear Django session
        logout(request)
        
        response = Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        
        # Clear auth token cookie
        response.delete_cookie('auth_token', path='/')
        
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for admin to manage users (CRUD operations)"""
    queryset = User.objects.all()
    serializer_class = UserManagementSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    pagination_class = UserPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserManagementSerializer

    @action(detail=False, methods=['get'])
    def active_users(self, request):
        """Get list of active users only"""
        users = User.objects.filter(is_active=True)
        page = self.paginate_queryset(users)
        if page is not None:
            serializer = UserListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign role to a user"""
        user = self.get_object()
        role = request.data.get('role')
        
        if role not in ['admin', 'learner']:
            return Response(
                {'error': 'Invalid role. Must be "admin" or "learner".'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.role = role
        user.save()
        
        return Response({
            'message': f'User role updated to {role}',
            'user': UserListSerializer(user).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a user"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({
            'message': 'User deactivated',
            'user': UserListSerializer(user).data
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a user"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({
            'message': 'User activated',
            'user': UserListSerializer(user).data
        }, status=status.HTTP_200_OK)
