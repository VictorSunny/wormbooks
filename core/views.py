from django.shortcuts import render, get_object_or_404, redirect
from . import serializers
from . models import BookDB, Category, Comment, Notifications
from django.core.paginator import Paginator
from django.views.generic import View
from http import HTTPStatus
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin

User = get_user_model()

#home view with all books posted listed
class BooksView(View):
    queryset = BookDB.objects.all()
    serializer_class = serializers.BookDBSerializer
    def get(self, request):

        books = BookDB.objects.all()

        #setting url queries
        category_name = request.GET.get('category')
        year_published = request.GET.get('year')
        search = request.GET.get('search')

        #page number indicator
        page = request.GET.get('page')
        
        #handling url queries
        if category_name:
            books = BookDB.objects.filter(category= get_object_or_404(Category, slug= category_name))
        if year_published:
            books = BookDB.objects.filter(year= year_published)
        if search:
            books = BookDB.objects.filter(Q(name__icontains= search) | Q(year = search) | Q(author__icontains = search) )
        
        serializer = self.serializer_class(instance= books, many= True)

        paginator = Paginator(serializer.data, 10)
        pages_num = paginator.num_pages
        page_object = paginator.get_page(page)
        return render(request, "index.html", {"data": page_object, "total": pages_num})

# function that deleted existing notifications to avoid duplication, putting the latest of such notification first
# mitigates notifications getting spammed with actions such as repeated liking and unliking, following and unfollowing, etc.
def notification_cleanser(request, header):
    try:
        original = request.user.notifications.get(header= header)
        original.delete()
        return header
    except:
        return header

#view allowing users to see all books with incomplete information
class ContributeView(LoginRequiredMixin, View):
    queryset = BookDB.objects.all()
    serializer_class = serializers.BookDBSerializer
    def get(self, request):
        
        #filter to retrieve books with non-exisiting fields
        books = BookDB.objects.filter(Q(year= 'none') | Q(author = 'None'))

        #get page number
        page = request.GET.get('page')
        
        serializer = self.serializer_class(instance= books, many= True)
        pages_num = Paginator(serializer.data, 6).num_pages
        page_object = Paginator(serializer.data, 6).get_page(page)
        return render(request, "contribute.html", {"data": page_object, "total": pages_num})
        
# view for viewing information on a particular book. handles comments in post actions
class SingleBookView(View):
    serializer_class = serializers.SingleBookSerializer
    
    def get(self, request, book_id):
        
        #retieve book
        book = get_object_or_404(BookDB, id = book_id)

        serializer = self.serializer_class(instance= book)

        return render(request, "book_info.html", {"book": book}, status= HTTPStatus.OK)
    
    #for comment posting
    def post(self, request, book_id):
        book = get_object_or_404(BookDB, id= book_id)
        book_page = request.META.get('HTTP_REFERER', '/')
        
        if request.user.is_authenticated:
            comment_body = request.POST.get('comment')
            comment = Comment.objects.create(
                body = comment_body,
                author = request.user,
                book = book,
            )
            comment.save()

            #send notication to book creator if comment is not by book creator and notifications are allowed for book
            if book.alerts:
                if request.user != book.created_by:
                    if book.alerts:
                        unparsed_header= f"{request.user.username} commented on your book {book.name}"

                        header = notification_cleanser(request, unparsed_header)
                        alert = Notifications.objects.create(
                            owner= book.created_by,
                            book= book,
                            label= f'new comment',
                            header= header,
                        )
                        alert.save()
                
        return redirect(book_page)


#view for creating new book recommendations
class BookCreateView(View):
    serializer_class = serializers.BookDBSerializer
    
    def get(self, request):
        
        return render(request, "create_book.html", status= HTTPStatus.OK)
    
    #replace empty input fields with 'none'
    def post(self, request):
        print('posting book...')
        data = request.POST.dict()
        for key in data:
            print(key)
            if data[key] == "":
                data[key] = "none"

        #check if category entered by user exists. if not, create new category based on user input
        try:
            data['category_id'] = get_object_or_404(Category, name= data['category_id'].title() ).id
        except:
            new_category = Category.objects.create(name= data['category_id'])
            new_category.save()
            data['category_id'] = get_object_or_404(Category, name= data['category_id']).id
        
        serializer = self.serializer_class(data= data)
    
        if serializer.is_valid():
            serializer.save(created_by= request.user)
            print(serializer.data)
        
            book_id = serializer.data['id']
        else:
            print(serializer.errors)

        return redirect("core:books", book_id= book_id)

#view for editing book
class BookUpdateView(View):
    serializer_class = serializers.BookDBSerializer
    
    def get(self, request, submission_type, book_id):
        book = get_object_or_404(BookDB, id = book_id)

        #html template for rendering based on update type
        if submission_type == "update":
            html = "update_book.html"
        elif submission_type == "contribute":
            html= "contribute_update_book.html"


        return render(request, html, {"data": book}, status= HTTPStatus.OK)
    
    def post(self, request, submission_type, book_id):
        book = get_object_or_404(BookDB, id = book_id)

        #retrieve a dictionary of form data
        data = request.POST.dict()
        for key in data:
            print(key)
            if data[key] == "":
                data[key] = "none"  

        #if submission type is 'update' (accessible only by book creator and supports genre changing), check if category exists
        #if category exists, alter form data to access category, else, create new category and alter form data to access new category
        if submission_type == "update":
            if request.user == book.created_by: 
                try:
                    data['category_id'] = get_object_or_404(Category, name= data['category_id'].title() ).id
                except:
                    new_category = Category.objects.create(name= data['category_id'])
                    new_category.save()
                    data['category_id'] = get_object_or_404(Category, name= data['category_id']).id
            else:
                #if user is not the creator of the book, raise permission error 403
                raise PermissionDenied("You do not own this book")
        
        serializer = self.serializer_class(instance= book, data= data)

        #if user is logged in
        if request.user.is_authenticated:
            if serializer.is_valid():
                serializer.save()

                #send notification to book creator, regardless of whether book notifications are on or off
                if request.user != book.created_by:
                    book.contributors.add(request.user)
                    if book.alerts:
                        unparsed_header = f"{request.user.username}- edited data on your book- {book.name}"
                        header = notification_cleanser(request, unparsed_header)

                        alert = Notifications.objects.create(
                            owner= book.created_by,
                            label= "book edited",
                            book= book,
                            header= header,
                        )
                        alert.save()
            else:
                print(serializer.errors)
        
        book_id = serializer.data['id']
        return redirect(f"/books/{book_id}")
    
#view for viewing all available book genres that have been added to the database
class CategoryView(View):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer

    def get(self, request):

        all_categories = Category.objects.all()

        return render(request, "categories.html", {"category_content": all_categories}, status= HTTPStatus.OK)

 #view for seeing all available books under a particular genre   
class CategoryBooksView(View):
    serializer_class = serializers.BookDBSerializer

    def get(self, request, slug):

        category_id = get_object_or_404(Category, slug= slug)
        data = BookDB.objects.filter(category= category_id)
        serializer = self.serializer_class(instance= data, many= True)

        page = request.GET.get('page')

        pages_num = Paginator(serializer.data, 6).num_pages
        page_object = Paginator(serializer.data, 6).get_page(page)

        return render(request, "category_books.html", {"data": page_object, "total": pages_num, "category": category_id}, status= HTTPStatus.OK)
    

#view for seeing books from all the people you follow. sorted by date, latest first
@login_required()
def for_you_page(request):

    following = request.user.following.all()

    
    page = request.GET.get('page')

    
    books = BookDB.objects.filter(Q(created_by__in= following))
    books_serializer = serializers.BookDBSerializer(instance=books, many= True)
    books_paginator = Paginator(books_serializer.data[:36], 6)

    data = books_paginator.get_page(page)

    return render(request, 'fyp.html', {'data': data, 'total': books_paginator.num_pages}, status= HTTPStatus.OK)


#view for seeing user followers and following
@login_required()
def network_view(request, username, network_type):
    page_owner = User.objects.get(username= username)
    page = request.GET.get('page')
    print(network_type)

    followers = page_owner.followers.all()
    following = page_owner.following.all()
    print(following)
    
    network = {"following": following, "followers": followers}

    #access 'network' dictionary based on 'network_type' entered
    paginator = Paginator(network[network_type], 10)
    data = paginator.get_page(page)

    return render(request, 'network.html', {
        'data': data,
        'total': paginator.num_pages,
        'network_type': network_type,
        'page_owner': page_owner.username
        })

#view for seeing all users that liked a book. socially useful for finding people with similar taste and growing your network
@login_required()
def book_likes_view(request, book_id):
    book = BookDB.objects.get(id= book_id)
    page = request.GET.get('page')
    
    network = book.likes.all()

    paginator = Paginator(network, 10)
    data = paginator.get_page(page)

    return render(request, 'likes.html', {'data': data, 'book_name': book.name})


#view for accessing user profile
def userview(request, username):
    profile_owner = get_object_or_404(User, username= username)
    books = BookDB.objects.filter(created_by= profile_owner)

    page = request.GET.get('page')

    serializer = serializers.BookDBSerializer(instance= books, many= True)

    paginator = Paginator(serializer.data, 6)
    data = paginator.get_page(page)

    return render(request, "profile.html", {"data": data, "profile_owner": profile_owner, 'total': paginator.num_pages}, status= HTTPStatus.OK)

#view for retrieving all notifications from database based on visitor, and rendering
@login_required()
def notification_view(request):
   
    try:
        notifications = request.user.notifications.all() 
        for alert in notifications:
            print(alert)
            if alert.viewed_status > 0:
                alert.viewed_status -= 1
                alert.save()
                print(alert.viewed_status)
    except:
        notifications = None
    
    

    return render(request, "notifications.html", {"notifications": notifications,})

    

######################### ACTION VIEWS #########################

#view for deleting books with book id as accessing key
def delete_book_view(request, book_id):
    book = get_object_or_404(BookDB, id = book_id)

    book.delete()

    return redirect("core:profile", username= request.user.username)

#view for following user
@login_required()
def follow_action_view(request, username):
    prev_page = request.META.get('HTTP_REFERER', '/')

    visitor = request.user
    profile_owner = get_object_or_404(User, username= username)

    if profile_owner in visitor.following.all():
        print('unfollowed')
        visitor.following.remove(profile_owner)
        profile_owner.followers.remove(visitor)
    else:
        print('followed')
        if visitor != profile_owner:
            visitor.following.add(profile_owner)
            profile_owner.followers.add(visitor)
            
            unparsed_header= f"{visitor.username} just followed you. keep posting! ;)"
            header = notification_cleanser(request, unparsed_header)

            #send notification to followed user
            alert = Notifications.objects.create(
                owner= profile_owner,
                label= f"new follower",
                header= header,
                account= visitor
            )
            alert.save()

    return redirect(prev_page)

#view for liking books with book id as accessing key
@login_required()
def like_action_view(request, book_id):
    profile_page = request.META.get('HTTP_REFERER', '/')

    visitor = request.user
    book = get_object_or_404(BookDB, id= book_id)
    if visitor in book.likes.all():
        book.likes.remove(visitor)
    else:
        book.likes.add(visitor)

        unparsed_header= f"{visitor.username} likes your book {book.name}"
        header = notification_cleanser(request, unparsed_header)

        #send notication to book creator if like is not from book creator and notifications are allowed for book
        if visitor != book.created_by:
            if book.alerts:
                alert = Notifications.objects.create(
                    owner= book.created_by,
                    book= book,
                    label= 'new like',
                    header= header,
                )
                alert.save()

    return redirect(profile_page)

#view for turning book notifications on or off
@login_required()
def book_alert_view(request, book_id):
    book = BookDB.objects.get(id= book_id)
    prev_page = request.META.get('HTTP_REFERER', '/')
    print(f'before: {book.alerts}')

    #reset state of notifications to opposite of it's current state if book is owned by user
    if request.user == book.created_by:
        if book.alerts:
            book.alerts = False
            book.save()
        else:
            book.alerts = True
            book.save()

    return redirect(prev_page)

#view for deleting comments with comment id as accessing key
@login_required()
def delete_comment_view(request, comment_id):
    prev_page = request.META.get('HTTP_REFERER', '/')
    comment = get_object_or_404(Comment, id = comment_id)

    comment.delete()

    return redirect(prev_page)


