from rest_framework import serializers
from . models import BookDB, Category, Comment, Notifications

from django.contrib.auth import get_user_model

from authapp.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username',]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['name', 'slug']

class BookDBSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, required= False)
    author = serializers.CharField(max_length=150, required= False, allow_blank= True, default= 'none')
    year = serializers.CharField(required= False, max_length= 4, allow_blank= True, default= 'none')
    description = serializers.CharField(max_length= 500, required= False)
    category = CategorySerializer(read_only= True)
    category_id = serializers.IntegerField(write_only= True, required= False)
    created_by = UserSerializer(read_only= True)
    created_on = serializers.DateTimeField(format= "%d %B, %Y", required= False)

    class Meta:
        model = BookDB
        fields = ['id', 'name', 'author', 'year', 'category', 'category_id', 'likes', 'description', 'created_by', 'created_on']

class SingleBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookDB
        fields = ['name', 'author', 'year', 'category', 'created_on', 'modified_on']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['body']

# class NotificationsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notifications
#         fields = 


