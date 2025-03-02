from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Loan
from datetime import timedelta
from decimal import Decimal

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email"]
        extra_kwargs = {
            "password": {"write_only": True}
        }  # Ensure password is never exposed

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class RegisterSerializer(UserSerializer):  
    password = serializers.CharField(write_only=True)

    class Meta(UserSerializer.Meta):
        model=User  
        fields = ["id","name","email","password"]  

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True
    )  

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "user",
            "amount",
            "interest_rate",
            "duration_months",
            "status",
            "created_at",
        ]

class LoanSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    amount_paid = serializers.SerializerMethodField()
    amount_remaining = serializers.SerializerMethodField()
    next_due_date = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "loan_id",
            "user",
            "amount",
            "interest_rate",
            "duration_months",
            "status",
            "created_at",
            "amount_paid",
            "amount_remaining",
            "next_due_date",
        ]

    def get_amount_paid(self, obj):
        return sum(t.amount_paid for t in obj.transactions.filter(is_successful=True))

    def get_amount_remaining(self, obj):
        return obj.amount - self.get_amount_paid(obj)

    def get_next_due_date(self, obj):
        transactions = obj.transactions.filter(is_successful=True).order_by('-payment_date')
        if transactions.exists():
            last_payment = transactions.first().payment_date
            return (last_payment + timedelta(days=30)).strftime("%Y-%m-%d")
        return (obj.created_at + timedelta(days=30)).strftime("%Y-%m-%d")
    
    def validate_amount(self, value):
        """Ensure amount is between ₹1,000 and ₹100,000."""
        if value is None:
            raise serializers.ValidationError("Amount is required.")
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("Amount must be a number.")
        if value < 1000 or value > 100000:
            raise serializers.ValidationError("Amount must be between ₹1,000 and ₹100,000.")
        return value

    def validate_duration_months(self, value):
        """Ensure duration is a whole number between 3 and 24 months."""
        if value is None:
            raise serializers.ValidationError("Interest rate is required.")
        if not isinstance(value, int):
            raise serializers.ValidationError("Duration must be a whole number.")
        if value < 3 or value > 24:
            raise serializers.ValidationError("Duration must be between 3 and 24 months.")
        return value
    
    def validate_interest_rate(self, value):
        """Ensure interest rate is provided and is a positive number."""
        if value is None:
            raise serializers.ValidationError("Interest rate is required.")
        if not isinstance(value, (int, float, Decimal)):
            raise serializers.ValidationError("Interest rate must be a number.")
        if value <= 0:
            raise serializers.ValidationError("Interest rate must be greater than 0.")
        return value
