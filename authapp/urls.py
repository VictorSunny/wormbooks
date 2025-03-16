from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import LoginForm

app_name = 'authapp'

urlpatterns = [
    path('signup/', views.signupview, name= 'signup'),
    path('signup/<str:action>/otp-verify/', views.otp_verification_view, name= 'otp_verify'),
    path('welcome/', views.welcome_view, name= 'welcome'),
    path('login/', views.loginview, name= 'login'),
    path('login/recover/', views.recovery_email_view, name= 'recovery_email'),
    path('login/recover/password/', views.recovery_password_view, name= 'recovery_password'),
    path('logout/', views.logoutview, name= 'logout'),
    path('account/settings/', views.settings_view, name= 'settings'),
    path('account/books/', views.user_books_view, name= 'user_books'),
    path('account/books/<int:book_id>/', views.BookUpdateView.as_view(), name= 'user_book_update'),
    path('account/books/<int:book_id>/delete/', views.delete_book_view, name= 'user_book_delete'),
    path('account/settings/general/', views.edit_profile, name= 'general_settings'),
    path('account/settings/login/', views.privacy_view, name= 'privacy_settings'),
    path('account/settings/login/password/', views.edit_password, name= 'password_settings'),
    path('account/settings/login/email/', views.edit_email, name= 'email_settings'),

]