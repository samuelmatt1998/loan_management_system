from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.contrib.auth.hashers import check_password
from django.utils.timezone import now
from decimal import Decimal
from django.contrib.auth import get_user_model
from .models import User, Loan, LoanTransaction, OTP
from .serializers import UserSerializer, RegisterSerializer, LoanSerializer
from .logics import calculate_emi, calculate_foreclosure_amount
from datetime import timedelta
import random
import requests


# Create your views here.
@api_view(["POST"])
@permission_classes([AllowAny])
def user_email_registration(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Generate OTP
        otp_code = str(random.randint(100000, 999999))
        OTP.objects.create(user=user, otp_code=otp_code)

        # Call Node.js server to send email
        email_payload = {"email": user.email, "otp": otp_code}
        response = requests.post("http://localhost:5001/send-email", json=email_payload)

        if response.status_code != 200:  # OTP sending failed
            user.delete()  # Remove user if OTP email fails
            return Response(
                {"error": "Failed to send OTP, try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"message": "OTP sent to email."}, status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get("email")
    otp = request.data.get("otp")

    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "User not found."}, status=status.HTTP_400_BAD_REQUEST)

    otp_record = OTP.objects.filter(user=user).order_by("-created_at").first()

    if not otp_record or otp_record.otp_code != otp or not otp_record.is_valid():
        user.delete()  # Delete user if OTP is invalid or expired
        return Response({"error": "Invalid or expired OTP. Registration failed."}, status=status.HTTP_400_BAD_REQUEST)

    otp_record.delete()  # Remove OTP after successful verification

    # Generate JWT tokens
    token = RefreshToken.for_user(user)
    return Response(
        {
            "Message": "Registration Successfull",
            "name": user.name,
            "email": user.email,
            "tokens": {
                "refresh": str(token),
                "access": str(token.access_token),
            },
        },
        status=status.HTTP_200_OK,
    )


'''@api_view(["POST"])
@permission_classes([AllowAny])
def user_registration(request):
""" User registeration without otp verfification use this for testing purposes and to get tokens"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = RefreshToken.for_user(user)
        # pseudo-code if otp_send_isverfied() then
        response_data = {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "tokens": {
                "refresh": str(token),
                "access": str(token.access_token),
            },
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    # if otp_send_isverfied() is false
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)'''


@api_view(["POST"])
@permission_classes([AllowAny])
def user_login(request):
    try:
        email = request.data.get("email")
        password = request.data.get("password")

        if not email:
            return Response({"Error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"Error": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"Error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if check_password(password, user.password):
            token = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "Login Success",
                    "user": {"username": user.email, "name": user.name},
                    "token": {"refresh": str(token), "access": str(token.access_token)},
                }
            )

        return Response({"Error": "Incorrect password"}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        return Response(
            {"Error": "Something went wrong", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_loan(request):
    """Create a new loan for the authenticated user."""
    try:
        serializer = LoanSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            amount = serializer.validated_data["amount"]
            interest_rate = serializer.validated_data["interest_rate"]
            duration_months = serializer.validated_data["duration_months"]

            emi_data = calculate_emi(amount, interest_rate, duration_months)
            total_amount = Decimal(emi_data["total_amount"])
            monthly_emi = emi_data["monthly_installment"]

            print(f"BEFORE CREATING LOAN: total_amount={total_amount}", flush=True)

            loan = Loan.objects.create(
                user=user,
                amount=amount,
                amount_remaining=total_amount,
                interest_rate=interest_rate,
                duration_months=duration_months,
                total_amount=total_amount,
                monthly_emi=monthly_emi,
                created_at=now(),
            )

            return Response(
                {
                    "status": "success",
                    "data": {
                        "loan_id": loan.loan_id,
                        "amount": float(loan.amount),
                        "tenure": loan.duration_months,
                        "total_amount": round(loan.total_amount, 2),
                        "amount_remaining": round(loan.amount_remaining, 2),
                        "monthly_installment": emi_data["monthly_installment"],
                        "status": loan.status,
                        "created_at": loan.created_at.isoformat(),
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {"status": "error", "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    except Exception as e:
        print(f"Exception occurred: {e}", flush=True)
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def make_payment(request):
    user = request.user
    loan_id = request.data.get("loan_id")

    try:
        loan = Loan.objects.get(loan_id=loan_id, user=user)

        if loan.amount_remaining <= 0:
            return Response(
                {"status": "error", "message": "Loan is already paid off"}, status=400
            )

        monthly_emi = loan.monthly_emi  

        if monthly_emi > loan.amount_remaining:
            return Response(
                {"status": "error", "message": "Overpayment is not allowed"}, status=400
            )

        # Deduct EMI from amount_remaining
        loan.amount_remaining -= monthly_emi
        if loan.amount_remaining == 0:
            loan.status = "CLOSED"
        loan.save()

        # Create a transaction record
        LoanTransaction.objects.create(
            loan=loan, amount_paid=monthly_emi, payment_date=now()
        )

        return Response(
            {
                "status": "success",
                "data": {
                    "loan_id": loan.loan_id,
                    "monthly_emi": float(monthly_emi),
                    "amount_remaining": float(loan.amount_remaining),
                    "status": loan.status,
                },
            },
            status=200,
        )

    except Loan.DoesNotExist:
        return Response({"status": "error", "message": "Loan not found"}, status=404)
    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def view_loan(request):
    """Retrieve all loans and installments for the authenticated user."""
    try:
        user = request.user
        if user.is_superuser:
            return Response(
                {
                    "status": "error",
                    "message": "For admin, please use the view-user-loan endpoint.",
                },
                status=401,
            )

        loans = Loan.objects.filter(user=user)

        loan_data = []
        for loan in loans:
            amount_paid = (
                loan.total_amount - loan.amount_remaining
            )  # Directly fetched from DB

            last_transaction = loan.transactions.order_by("-payment_date").first()
            next_due_date = (
                last_transaction.payment_date if last_transaction else loan.created_at
            ) + timedelta(days=30)

            loan_data.append(
                {
                    "loan_id": loan.loan_id,
                    "amount": float(loan.amount),
                    "tenure": loan.duration_months,
                    "rate": f"{loan.interest_rate}% per year",
                    "total_amount": round(
                        loan.total_amount, 2
                    ),  # Directly fetched from DB
                    "amount_paid": round(amount_paid, 2),
                    "amount_remaining": round(loan.amount_remaining, 2),
                    "next_due_date": next_due_date.strftime("%Y-%m-%d"),
                    "status": loan.status,
                    "created_at": loan.created_at.isoformat(),
                }
            )

        return Response({"status": "success", "data": {"loans": loan_data}})

    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def foreclose_loan(request, loan_id):
    user = request.user
    loan_id = request.data.get("loan_id")

    try:
        # Fetch the loan
        loan = Loan.objects.get(loan_id=loan_id)
        print(f"##########{user}")

        # Admins are not allowed to foreclose
        if user.is_superuser:
            return Response(
                {"status": "error", "message": "Admins cannot foreclose loans."},
                status=401,
            )

        # If the loan is already closed
        if loan.status == "CLOSED":
            return Response(
                {"status": "error", "message": "Loan is already closed."}, status=400
            )

        # Calculate months left

        # Apply foreclosure discount (assuming ₹500)
        foreclosure_discount = 500
        amount_paid = loan.total_amount - loan.amount_remaining
        amount_remaining = loan.amount - amount_paid

        # Calculate foreclosure amount using principal
        foreclosure_amount = calculate_foreclosure_amount(
            principal_remaining=amount_remaining,
            annual_interest_rate=loan.interest_rate,
            discount=foreclosure_discount,
        )

        # Mark loan as closed
        loan.amount_remaining = 0
        loan.status = "CLOSED"
        loan.save()

        return Response(
            {
                "status": "success",
                "message": "Loan foreclosed successfully.",
                "foreclosure_amount": round(foreclosure_amount, 2),
                "discount_applied": foreclosure_discount,
                "amount_paid": foreclosure_amount - foreclosure_discount,
            },
            status=200,
        )

    except Loan.DoesNotExist:
        return Response({"status": "error", "message": "Loan not found."}, status=404)
    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )




@api_view(["GET"])
@permission_classes([IsAdminUser])
def view_all_loan(request):
    """Retrieve all loans in the database (Admin only)."""
    try:
        loans = Loan.objects.all()

        loan_data = []
        for loan in loans:
            amount_paid = loan.total_amount - loan.amount_remaining

            loan_data.append(
                {
                    "loan_id": loan.loan_id,
                    "user_id": loan.user.id,
                    "amount": float(loan.amount),
                    "tenure": loan.duration_months,
                    "rate": f"{loan.interest_rate}% per year",
                    "total_amount": float(loan.total_amount),
                    "amount_paid": round(amount_paid, 2),
                    "amount_remaining": round(loan.amount_remaining, 2),
                    "monthly_emi": float(loan.monthly_emi),
                    "status": loan.status,
                    "created_at": loan.created_at.isoformat(),
                }
            )

        return Response({"status": "success", "data": {"loans": loan_data}}, status=200)

    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )


@api_view(["GET"])
@permission_classes([IsAdminUser])
def view_user_loan(request):
    try:
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"status": "error", "message": "User ID is required"}, status=400
            )

        loans = Loan.objects.filter(user_id=user_id)

        if not loans.exists():
            return Response(
                {"status": "error", "message": "No loans found for this user"},
                status=404,
            )

        loan_data = []
        for loan in loans:
            amount_paid = loan.total_amount - loan.amount_remaining

            last_transaction = loan.transactions.order_by("-payment_date").first()
            next_due_date = (
                last_transaction.payment_date if last_transaction else loan.created_at
            ) + timedelta(days=30)

            loan_data.append(
                {
                    "loan_id": loan.loan_id,
                    "amount": float(loan.amount),
                    "tenure": loan.duration_months,
                    "total_amount": loan.total_amount,
                    "amount_paid": round(amount_paid, 2),
                    "amount_remaining": round(loan.amount_remaining, 2),
                    "next_due_date": next_due_date.strftime("%Y-%m-%d"),
                    "status": loan.status,
                    "created_at": loan.created_at.isoformat(),
                }
            )

        return Response({"status": "success", "data": {"loans": loan_data}})

    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )


@api_view(["DELETE"])
@permission_classes([IsAdminUser])
def delete_loan(request):
    """Delete a loan based on loan_id (Admin only)."""
    loan_id = request.data.get("loan_id")  # Get loan_id from request body

    if not loan_id:
        return Response(
            {"status": "error", "message": "Loan ID is required"}, status=400
        )

    try:
        loan = Loan.objects.get(loan_id=loan_id)
        loan.delete()

        return Response(
            {"status": "success", "message": f"Loan {loan_id} has been deleted"},
            status=200,
        )

    except Loan.DoesNotExist:
        return Response({"status": "error", "message": "Loan not found"}, status=404)

    except Exception as e:
        return Response(
            {"status": "error", "message": f"Something went wrong: {str(e)}"},
            status=500,
        )
