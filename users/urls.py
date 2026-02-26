from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserRegistrationView, UserProfileView, user_me

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('me/', user_me, name='user-me'),
]
