from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify

# Create your models here.

User = get_user_model()


class Category(models.Model):

    name = models.CharField(max_length=25, unique= True, blank= False)
    slug = models.SlugField(max_length=25, blank= True)

    class Meta:
        ordering = ['name',]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BookDB(models.Model):

    name = models.CharField(max_length=255, blank= False)
    author = models.CharField(max_length=255, default= "none")
    year = models.CharField(blank= True, default= "none", max_length= 4)
    category = models.ForeignKey(Category, default= 1, on_delete=models.CASCADE, related_name= 'books', blank= False)
    created_on = models.DateTimeField(auto_now_add= True, null= True)
    modified_on = models.DateTimeField(auto_now= True, null= True)
    created_by = models.ForeignKey(User, default= 17, on_delete= models.SET_DEFAULT, related_name= 'books')
    description = models.CharField(max_length= 500, default= "none")
    likes = models.ManyToManyField(User, blank=True, related_name= 'likes')
    contributors = models.ManyToManyField(User, blank= True, related_name= "contributions")
    alerts = models.BooleanField(default= True)

    class Meta:
        ordering = ['-created_on',]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.name = self.name.title()
        self.author = self.author.title()
        super().save(*args, **kwargs)

class Comment(models.Model):
    author = models.ForeignKey(User, default= 17, on_delete= models.SET_DEFAULT, related_name= 'comments')
    date_created = models.DateTimeField(auto_now_add= True)
    body = models.TextField(max_length= 255, blank= False, help_text= "Enter Comment")
    book = models.ForeignKey(BookDB, on_delete= models.CASCADE, related_name='comments')

    class Meta:
        ordering = ['-date_created',]

class Notifications(models.Model):
    owner = models.ForeignKey(User, on_delete= models.CASCADE, related_name= 'notifications')
    book = models.ForeignKey(BookDB, null= True, related_name= 'notifications', on_delete= models.CASCADE)
    label = models.CharField(max_length= 50)
    account = models.ForeignKey(User, on_delete= models.CASCADE, blank= True, null= True, related_name= 'necessary_for_diversification')
    header = models.CharField(max_length= 150)
    viewed_status = models.IntegerField(default= 2)
    created_on = models.DateTimeField(auto_now_add= True, null= True)

    class Meta:
        ordering = ['-created_on',]

            
