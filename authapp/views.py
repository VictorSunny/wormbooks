from django.shortcuts import render, redirect
from core.models import BookDB
from .forms import UserCreation, LoginForm, UserUpdate, PasswordForm, EmailChange, OTPForm, EmailForm, PasswordRecoveryForm
from django.contrib.auth import logout, login, get_user_model
from core.models import Notifications
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.paginator import Paginator
from core.serializers import BookDBSerializer
from django.shortcuts import get_object_or_404
from django.views import View
from core import serializers
from core.models import Category
import secrets
from .models import OTPVerification
from django.core.mail import send_mail
from django.urls import reverse
from decouple import config
from datetime import timedelta
from django.utils import timezone

# Create your views here.

User = get_user_model()

#user singup view
def signupview(request):
    if request.method == 'POST':
        form = UserCreation(request.POST)
        if form.is_valid():
            user_data= form.cleaned_data

            #create session data with account details for account creation after otp verification
            request.session['data'] = dict(user_data)

            #redirect to otp verification page with signup data
            return redirect('authapp:otp_verify', 'signup')
    else:
        form = UserCreation()
    return render(request, "signup.html", {"form": form})

#user login view
def loginview(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            try:
                if request.session['new']:

                    #if user is new, delete use signifier of new user
                    del request.session['new']
                    return redirect('authapp:welcome')
            except:
                return redirect('core:home')

    else:
        form = LoginForm()
    return render(request, "login.html", {"form": form})

#otp verification view for signup and account security updates
def otp_verification_view(request, action):

    #retrieve session data with user information for otp verification against matching user account
    user_data = request.session.get('data')
    if action == 'signup':

        #extract verified password from signup page to set user password
        user_data['password'] = user_data['password1']

        #delete unsupported fields from signup json of session data to allow usage for user model object creation
        del user_data['password1']
        del user_data['password2']
        mail_subject = 'A WORM WELCOME'

    elif action == 'update_password':

        #set session data for new password to be used for user object update
        new_password = user_data['new_password2']
        user_data['email'] = request.user.email
        mail_subject = 'WORM PASSWORD CHANGE'

    elif action == 'update_email':

        #set session data for new email to be used for user email update
        new_email = user_data['email']  
        mail_subject = 'WORM EMAIL CHANGE'

    elif action == 'password_recovery':
        mail_subject = 'ACCOUNT RECOVERY'

    try:

        #retrieve otp object if exists
        verification_object = OTPVerification.objects.get(email= user_data['email'])

        #delete otp object if expired
        if timezone.now() > verification_object.created_at + timedelta(minutes=3):
            verification_object.delete()
            print('expired otp deleted')
            raise FileNotFoundError
        else:
            otp = verification_object.code
            print('retrieved locally')
    except:

        #create otp object if expired & deleted or does not exist
        otp = secrets.token_hex(5)

        #send otp to user email
        verification_email = send_mail(
            subject= mail_subject,
            message= f'Your signup OTP code: {otp}',
            recipient_list= [user_data['email'],],
            from_email= config('DEFAULT_FROM_EMAIL'),
        )

        #save otp as an object to be retrieved and reused within allowed window
        OTPVerification.objects.create(
            email= user_data['email'],
            code= otp,
        )

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['verification_code'] == otp:

                if action == 'signup':
                    new_user = User.objects.create_user(**user_data)
                    for field in user_data:
                        if field != 'email':
                            new_user.field = user_data[field]
                    new_user.save()

                    #create signifier that account is new. new account gets redirected to welcome page upon login
                    request.session['new'] = ['new']

                elif action == 'update_password':
                    user = User.objects.get(id= request.user.id)
                    password = user.set_password(new_password)
                    user.save()

                elif action == 'update_email':
                    user = User.objects.get(id= request.user.id)
                    user.email = new_email
                    user.save()

                if action == 'password_recovery':

                    #create session email data to allow otp view to access the email for otp verification
                    request.session['email'] = request.session['data']['email']
                    return redirect('authapp:recovery_password')
                
                #delete session data
                del request.session['data']
                return redirect('authapp:login')
            else:
                form.add_error(field= 'verification_code', error= 'Invalid code. Please try again')
    else:
        form = OTPForm()
    return render(request, 'otp_verify.html', {'form': form})
    


#logout view
login_required()    
def logoutview(request):
    logout(request)
    return redirect('/home')

#account settings view
@login_required()
def settings_view(request):
    return render(request, 'settings.html')

#view for editing basic user profile details
@login_required()
def edit_profile(request):
    form = UserUpdate(
            instance= request.user
        )
    if request.method == 'POST':
        form = UserUpdate(data= request.POST, instance= request.user)
        if form.is_valid():
            user = form.save()
            user.save()
            profile_url = reverse('core:profile', kwargs={"username": user.username})
            return redirect(profile_url)
        
    return render(request, "edit_profile.html", {"form": form})

def privacy_view(request):
    return render(request, 'privacy_settings.html')

#view for editing user password
@login_required()
def edit_password(request):
    if request.method == 'POST':
        form = PasswordForm(request.user, request.POST)
        if form.is_valid():
            request.session['data'] = dict(form.cleaned_data)
            return redirect('authapp:otp_verify', 'update_password')
    else:
        form = PasswordForm(request.user)
        
    return render(request, "edit_password.html", {"form": form})

#view for editing user email
@login_required()
def edit_email(request):
    user_object = User.objects.get(id= request.user.id)
    if request.method == 'POST':
        form = EmailChange(data= request.POST, instance= request.user)
        if form.is_valid():

            #extract password entered into form to check against current user password 
            password_entered = form.cleaned_data['confirm_password']
            if user_object.check_password(password_entered):

                #alter session data to contain new user email entered 
                request.session['data'] = dict(form.cleaned_data)

                return redirect('authapp:otp_verify', 'update_email')
            
            else:

                #if form is password entered is incorrect, raise an error
                form.add_error('confirm_password', 'Incorrect password. Please try again.')

    else:
        form = EmailChange(
            instance= request.user
        )
        
    return render(request, "edit_email.html", {"form": form})


#view for all books posted by user, allowing easier access to delete and edit operations
def user_books_view(request):

    books = request.user.books.all()
    serialixer_data = BookDBSerializer(instance= books, many= True).data
    page = request.GET.get('page')

    paginator_class = Paginator(serialixer_data, 10)
    total = paginator_class.num_pages

    data = paginator_class.get_page(page)


    return render(request, 'user_books.html', {"data": data, "total": total})

#custom account view for editing user's books and redirecting back to account settings page with other books
class BookUpdateView(View):
    serializer_class = serializers.BookDBSerializer
    
    def get(self, request, book_id):
        book = get_object_or_404(BookDB, id = book_id)

        return render(request, 'update_book.html', {"data": book})
    
    def post(self, request, book_id):
        book = get_object_or_404(BookDB, id = book_id)
        data = request.POST.dict()

        #fill all empty fields with 'none'
        for key in data:
            print(key)
            if data[key] == "":
                data[key] = "none"     
        
        #check if category entered exists in database. if not, create a new category based on user input and save to database
        try:
            data['category_id'] = get_object_or_404(Category, name= data['category_id'].title() ).id
        except:
            new_category = Category.objects.create(name= data['category_id'])
            new_category.save()
            data['category_id'] = get_object_or_404(Category, name= data['category_id']).id
        
        #pass data tpo serializer
        serializer = self.serializer_class(instance= book, data= data)

        if serializer.is_valid():
            serializer.save()
            return redirect('authapp:user_books')

#custom account view for deleting books and redirecting back to account settings page with other books
def delete_book_view(request, book_id):
    previous_page = request.META.get('HTTP_REFERER', '/')
    print(previous_page)

    book = get_object_or_404(BookDB, id = book_id)

    book.delete()

    return redirect(previous_page)     

#account recovery view for taking and verifying user email inputs for otp verification
def recovery_email_view(request):
    user_emails = User.objects.all().values('email')
    emails = []
    #create dictionary of existing email addresses in database
    for email in user_emails:
        emails.append(email['email'])
    
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email_entered = form.cleaned_data['email']

            #check if email entered by user is connected to any existing account for recovery
            if email_entered in emails:

                #set session data with user information to be used for user validation in otp verification page
                request.session['data'] = dict(form.cleaned_data)

                return redirect('authapp:otp_verify', 'password_recovery')
            
            else:
                form.add_error('email', 'Rejected. This email is not connected to any account.')

    else:
        form = EmailForm()
        
    return render(request, "recovery_email.html", {"form": form})

#account recovery view for setting new user password upon successful otp verification using account email
def recovery_password_view(request):
    
    if request.method == 'POST':
        form = PasswordRecoveryForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['new_password2'] == form.cleaned_data['new_password1']:
                recovered_user = User.objects.get(email= request.session['email'])
                recovered_user.set_password(form.cleaned_data['new_password1'])
                recovered_user.save()

                #after confirming password, delete session data containing user email
                del request.session['email']
                #redirect to login page upon successful account update
                return redirect('authapp:login')
            else:
                 form.add_error(field= 'new_password2', error= 'Passwords do not match')
    
    else:
        form = PasswordRecoveryForm()

    return render(request, 'recovery_password.html', {'form': form})

#welcome view for new users       
def welcome_view(request):
    return render(request, 'etiquette.html')