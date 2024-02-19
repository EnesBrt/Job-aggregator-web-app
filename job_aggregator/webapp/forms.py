from django import forms
from django.contrib.auth.models import User
import re
from django.core.exceptions import ValidationError
from .models import EmailVerification, SendResetPasswordEmail
from django.contrib.auth import authenticate


# Signin form
class SigninForm(forms.ModelForm):
    username = forms.CharField(max_length=200)
    email = forms.EmailField(max_length=200)
    password = forms.CharField(max_length=500, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=500, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password"]

    # Custom validation for username, email, password and confirm_password
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email existe déjà")
        return email

    def clean_password(self):
        password = self.cleaned_data.get("password")
        if len(password) < 8:
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères"
            )
        # Regex for uppercase, number and special character
        if not re.search(r"[A-Z]", password):
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins une lettre majuscule"
            )
        if not re.search(r"[0-9]", password):
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins un chiffre"
            )
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise forms.ValidationError(
                "Le mot de passe doit contenir au moins un caractère spécial"
            )

        return password

    def clean_confirm_password(self):
        password = self.cleaned_data.get("password")
        confirm_password = self.cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise ValidationError("Les mots de passes ne correspondent pas")
        return confirm_password

    # Save the user
    def save(self, commit=True):
        user = super(SigninForm, self).save(commit=False)
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password"])
        user.is_active = False

        if commit:
            user.save()
            # Create an email verification token
            EmailVerification.objects.create(user=user)
        return user


# Login form
class LoginForm(forms.Form):
    username = forms.CharField(max_length=900)
    password = forms.CharField(max_length=900, widget=forms.PasswordInput)


class EmailForgottenPasswordForm(forms.Form):
    email = forms.EmailField(max_length=500)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email n'existe pas")

        return email
