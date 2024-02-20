from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from .forms import SigninForm, LoginForm, EmailForgottenPasswordForm
from .models import EmailVerification, ResetForgottenPassword
from django.core.mail import send_mail, EmailMessage
from django.utils import timezone
import uuid
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db import transaction
import logging


# Home view
def home(request):
    return render(request, "home.html")


# Signin view
def signin(request):
    if request.method == "POST":
        form = SigninForm(request.POST)
        if form.is_valid():
            user = form.save()

            # retrieve the email verification token and user
            email_verification = EmailVerification.objects.get(user=user)
            # generate a token
            token = email_verification.token

            # activation url
            activation_url = request.build_absolute_uri(
                reverse("account_activation", kwargs={"token": token})
            )

            # send the email
            email_subject = "Activation de votre compte"
            email_body = f"Bonjour {user.username},\n\nCliquez sur le lien suivant pour activer votre compte:\n\n{activation_url}"
            email = EmailMessage(email_subject, email_body, to=[user.email])
            email.send()

            return redirect("confirmation_sent")
    else:
        form = SigninForm()

    return render(request, "signin.html", {"form": form})


# activation confirmation
logger = logging.getLogger(__name__)


def account_activation(request, token):
    try:
        email_verification = EmailVerification.objects.get(token=token)

        # Check if the token is expired
        if email_verification.token_expired:
            logger.error(f"Token for user {email_verification.user.id} is expired.")
            return redirect("activation_failed", user_id=email_verification.user.id)

        # Check if account is already verified, if not, activate the user account
        if not email_verification.verified:
            user = email_verification.user
            user.is_active = True
            user.save()

            # Update the email verification token
            email_verification.verified = True
            email_verification.save()

            # Delete the email verification token
            EmailVerification.objects.filter(user=user).exclude(token=token).delete()

            return redirect("account_activated")
        else:
            logger.error(
                f"Account for user {email_verification.user.id} is already verified."
            )
            return redirect("login")

    except EmailVerification.DoesNotExist:
        logger.error(f"No email verification object found for token {token}.")
        return redirect("activation_failed_no_id")


# resend activation email
def resend_activation_email(request, user_id):
    try:
        # retrieve the user and the email verification token
        user = User.objects.get(id=user_id)
        email_verification = EmailVerification.objects.get(user=user)

        # Generate a new token
        token = uuid.uuid4()

        # Update the token in the EmailVerification object and save it to the database
        with transaction.atomic():
            email_verification.token = token
            email_verification.created_at = timezone.now()
            email_verification.save()
            print(f"Saved new token {token} for user {user_id}")

        request.session["user_id"] = user_id

        # build the activation url
        activation_url = request.build_absolute_uri(
            reverse(
                "account_activation",
                kwargs={"token": email_verification.token},
            )
        )

        # send the email
        email_subject = "Activation de votre compte"
        email_body = f"Bonjour {user.username},\n\nCliquez sur le lien suivant pour activer votre compte:\n\n{activation_url}"
        email = EmailMessage(email_subject, email_body, to=[user.email])
        email.send()

    except User.DoesNotExist:
        return redirect("activation_failed")

    return redirect("confirmation_sent")


def login_view(request):
    if request.method == "POST":
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            username = login_form.cleaned_data["username"]
            password = login_form.cleaned_data["password"]
            user = authenticate(username=username, password=password)

            # Check if username and password are correct
            if user is not None:
                auth_login(request, user)
                return redirect("job_board")
            else:
                return render(request, "login.html", {"error": "Authentication failed"})
    else:
        login_form = LoginForm()

    return render(request, "login.html", {"form": login_form})


def confirmation_sent(request):
    return render(request, "confirmation_sent.html")


def account_activated(request):
    return render(request, "account_activated.html")


def activation_failed(request, user_id=None):
    if user_id is None:
        # If no user_id is passed as a parameter, try to get it from the session
        user_id = request.session.get("user_id")

    context = {"user_id": user_id}
    return render(request, "activation_failed.html", context)


def job_board(request):
    return render(request, "job_board.html")


def send_forgotten_passord_email(request):
    if request.method == "POST":
        email_form = EmailForgottenPasswordForm(request.POST)

        if email_form.is_valid():
            # retrieve the user
            email = email_form.cleaned_data["email"]

            try:
                user = User.objects.get(email=email)

                # create a reset password token
                reset_password_email, created = (
                    SendResetPasswordEmail.objects.get_or_create(email=email)
                )

            except User.DoesNotExist:
                return redirect("email_not_found")

            # generate a token
            token = reset_password_email.token

            # Create activation url
            reset_password_url = request.build_absolute_uri(
                reverse("reset_password", kwargs={"token": token})
            )

            # send the email
            email_subject = "Réinitialisation de votre mot de passe"
            email_body = f"Bonjour {user.username},\n\nCliquez sur le lien suivant pour réinitialiser votre mot de passe:\n\n{reset_password_url}"
            email = EmailMessage(email_subject, email_body, to=[user.email])
            email.send()

            return redirect("forgott_password")

    else:
        email_form = EmailForgottenPasswordForm()

    return render(request, "send_email_forgot_password.html", {"form": email_form})


def reset_forgotten_password(request, token):
    # retrieve the reset password token
    try:
        reset_password_email = ResetForgottenPassword.objects.get(token=token)

        # Check if the token is expired
        if reset_password_email.token_expired:
            return redirect("send_reset_password")

    except ResetForgottenPassword.DoesNotExist:
        return redirect("send_reset_password")

    if request.method == "POST":
        reset_password_form = ResetForgottenPasswordForm(request.POST)

        # If the form data is valid, verify the token, delete any other tokens associated with the user,
        # update the user's password, and redirect to the "login" page.
        if reset_password_form.is_valid():

            # Check if the token is verified
            if not reset_password_email.verified:
                reset_password_email.verified = True
                reset_password_email.save()

            # Delete the reset password token
            ResetForgottenPassword.objects.filter(
                user=reset_password_email.user
            ).exclude(token=token).delete()

            # retrieve the user
            user = reset_password_email.user

            # update the user password
            user.set_password(reset_password_form.cleaned_data["new_password"])
            user.save()

            return redirect("login")

        else:
            return render(request, "reset_password.html", {"form": reset_password_form})

    else:
        reset_password_form = ResetForgottenPasswordForm()

    return render(request, "reset_password.html", {"form": reset_password_form})
