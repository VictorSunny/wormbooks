from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('home/', views.BooksView.as_view(), name= 'home'),
    path('books/contribute/', views.ContributeView.as_view(), name= 'contribute'),
    path('books/<int:book_id>/', views.SingleBookView.as_view(), name= 'books'),
    path('books/<int:book_id>/likes/', views.book_likes_view, name= 'likes'),
    path('books/categories/', views.CategoryView.as_view(), name= 'categories'),
    path('books/categories/<str:slug>/', views.CategoryBooksView.as_view(), name= 'category-books'),
    path('user/notifications/', views.notification_view, name= 'notifications'),
    path('user/<str:username>/', views.userview, name= 'profile'),
    path('follow/user/<str:username>/', views.follow_action_view, name= 'follow'),
    path('like/book/<int:book_id>/', views.like_action_view, name= 'like'),
    path('alerts/book/<int:book_id>/', views.book_alert_view, name= 'book_alert'),
    path('books/create/', views.BookCreateView.as_view(), name= 'create_book'),
    path('books/<str:submission_type>/<int:book_id>/', views.BookUpdateView.as_view(), name= 'update_book'),
    path('delte/book/<int:book_id>/', views.delete_book_view, name= 'delete_book'),
    path('delte/comment/<int:comment_id>/', views.delete_comment_view, name= 'delete_comment'),
    path('for-you/', views.for_you_page, name= 'fyp'),
    path('user/<str:username>/<str:network_type>/', views.network_view, name= 'network'),
]