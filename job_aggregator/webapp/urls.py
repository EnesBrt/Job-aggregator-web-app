from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signin/", views.signin, name="signin"),
    path("login/", views.login_view, name="login"),
    path("confirmation_sent/", views.confirmation_sent, name="confirmation_sent"),
    path("account_activated/", views.account_activated, name="account_activated"),
    path("activation_failed/", views.activation_failed, name="activation_failed_no_id"),
    path(
        "activation_failed/<int:user_id>/",
        views.activation_failed,
        name="activation_failed",
    ),
    path("job_board/", views.job_board, name="job_board"),
    path(
        "activate/<uuid:token>/", views.account_activation, name="account_activation"
    ),  # <uuid:token> is the token that will be passed to the view function as an argument
    path(
        "resend_activation_email/<int:user_id>/",
        views.resend_activation_email,
        name="resend_activation_email",
    ),
    path(
        "send_email_forgot_password/",
        views.send_forgotten_passord_email,
        name="send_email_forgot_password",
    ),
    path(
        "forgot_password/<str:token>//",
        views.reset_forgotten_password,
        name="forgot_password",
    ),  # <str:token> is the token that will be passed to the view function as an argument
    path("forgot_password/", views.reset_forgotten_password, name="forgot_password"),
    path("profile/", views.profile, name="profile"),
    path("settings/", views.settings, name="settings"),
    path("logout_page/", views.logout_page, name="logout_page"),
]
