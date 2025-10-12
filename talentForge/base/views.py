from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CustomPasswordResetForm, CustomSetPasswordForm
import random
import string
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

# Stockage temporaire pour les codes de vérification
verification_codes = {}

def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

@login_required
def home(request):
    return render(request, 'base/home.html')

def authView(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Sauvegarder l'utilisateur mais ne pas le connecter tout de suite
            user = form.save(commit=False)
            user.is_active = False  # Désactiver le compte jusqu'à vérification
            user.save()
            
            # Générer le code de vérification
            verification_code = generate_verification_code()
            verification_codes[user.email] = {
                'code': verification_code,
                'user_id': user.id,
                'created_at': timezone.now()
            }
            
            # Envoyer l'email de vérification
            try:
                send_verification_email(user.email, verification_code)
                messages.info(request, 'A verification code has been sent to your email address.')
                return redirect('base:verify_email', email=user.email)
            except Exception as e:
                # Si l'envoi d'email échoue, supprimer l'utilisateur et afficher un message
                user.delete()
                messages.error(request, 'Failed to send verification email. Please try again.')
                print(f"Email error: {e}")  # Pour le débogage
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/signup.html', {"form": form})

def verify_email(request, email):
    if request.method == 'POST':
        entered_code = request.POST.get('verification_code')
        stored_data = verification_codes.get(email)
        
        if not stored_data:
            messages.error(request, 'No verification code found. Please sign up again.')
            return redirect('base:signup')
        
        if entered_code == stored_data['code']:
            # Vérifier si le code n'a pas expiré (15 minutes)
            if timezone.now() - stored_data['created_at'] < timedelta(minutes=15):
                # Activer l'utilisateur
                try:
                    user = User.objects.get(id=stored_data['user_id'])
                    user.is_active = True
                    user.save()
                    
                    # ✅ CORRECTION : Ré-authentifier l'utilisateur proprement
                    auth_user = authenticate(
                        request, 
                        username=user.username,
                        password=None
                    )
                    
                    if auth_user is not None:
                        login(request, auth_user)
                        # Nettoyer le code de vérification
                        del verification_codes[email]
                        messages.success(request, '🎉 Email verified successfully! Your account is now active.')
                        return redirect('base:home')
                    else:
                        # Si l'authentification échoue, rediriger vers login
                        messages.success(request, '✅ Email verified! Please log in with your credentials.')
                        return redirect('base:login')
                        
                except User.DoesNotExist:
                    messages.error(request, 'User not found. Please sign up again.')
                    return redirect('base:signup')
            else:
                messages.error(request, 'Verification code has expired. Please sign up again.')
                # Nettoyer le code expiré
                del verification_codes[email]
                return redirect('base:signup')
        else:
            messages.error(request, 'Invalid verification code. Please try again.')
    
    return render(request, 'registration/verify_email.html', {'email': email})

def custom_login(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                    return redirect('base:home')
                else:
                    messages.error(request, 'Your account is not active. Please verify your email.')
            else:
                messages.error(request, 'Invalid email/username or password.')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def send_verification_email(email, code):
    subject = 'Verify Your TalentForge Account'
    message = f'''
    Welcome to TalentForge!
    
    Your verification code is: {code}
    
    This code will expire in 15 minutes.
    
    If you didn't create an account, please ignore this email.
    
    Best regards,
    The TalentForge Team
    '''
    
    try:
        # ✅ CORRECTION : ENVOI RÉEL PAR EMAIL ACTIVÉ
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Utilise l'email configuré dans settings.py
            [email],
            fail_silently=False,
        )
        print(f"✅ Email sent to {email} with code: {code}")
    except Exception as e:
        print(f"❌ Failed to send email to {email}: {e}")
        # En cas d'erreur, on affiche dans la console
        print(f"DEVELOPMENT MODE - Code for {email}: {code}")

# Vues pour la réinitialisation du mot de passe
class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    template_name = 'registration/password_reset.html'
    email_template_name = 'registration/password_reset_email.html'
    success_url = '/password-reset/done/'

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    template_name = 'registration/password_reset_confirm.html'
    success_url = '/password-reset/complete/'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'