from django.urls import path
from .views import (
    #user_registration,
    user_login,
    add_loan,
    make_payment,
    view_loan,
    view_all_loan,
    view_user_loan,
    delete_loan,
    foreclose_loan,
    user_email_registration,
    verify_otp
)

urlpatterns = [
    #path("register/", user_registration, name="user-registration"),
    path("login/", user_login, name="user-login"),
    path("add-loan/", add_loan, name="add-loan"),
    path("make-payment/", make_payment, name="make-payment"),
    path("view-loan/", view_loan, name="view-loan"),
    path("view-all-loan/", view_all_loan, name="view-all-loan"),
    path("view-user-loan/", view_user_loan, name="view-user-loan"),
    path("delete-loan/",delete_loan,name="delete-loan"),
    path("<str:loan_id>/foreclose/",foreclose_loan,name="foreclose-loan"),
    path("email-register/",user_email_registration,name="email-register"),
    path("verify-otp/",verify_otp,name="verify-otp"),
]
