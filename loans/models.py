from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    Group,
    Permission
)
import uuid
from datetime import datetime,timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):  
    name = models.CharField(max_length=100)
    email = models.CharField(max_length=75, unique=True)
    password = models.CharField(max_length=250)  # Managed by AbstractBaseUser
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    groups = models.ManyToManyField(Group, related_name="custom_user_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="custom_user_permissions", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"  # Use email for authentication

    def __str__(self):
        return self.email


class Loan(models.Model):
    loan_id = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="loans"
    )  # One-to-Many
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_remaining = models.DecimalField(max_digits=12, decimal_places=2,default=0)  
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    duration_months = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    monthly_emi = models.DecimalField(max_digits=12, decimal_places=2,default=0)
    status = models.CharField(
        max_length=10,
        choices=[
            ("ACTIVE", "Active"),
            ("CLOSED", "Closed"),
        ],
        default="ACTIVE",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.loan_id:
            self.loan_id = f"loan_{str(uuid.uuid4())[:8]}_usr{self.user.id}"#creates unique loan id for the user  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan_id} - {self.status}"
    


class LoanTransaction(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="transactions")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return f"Payment of {self.amount_paid} for Loan {self.loan.loan_id} on {self.payment_date}"

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        """OTP expires in 5 minutes"""
        return (datetime.now(timezone.utc) - self.created_at).total_seconds() < 300   # 5 mins
