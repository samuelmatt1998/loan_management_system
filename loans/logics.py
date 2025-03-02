# Created for user implemented logics

from datetime import datetime, timedelta
import math


def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate EMI, total interest, and generate a payment schedule."""
    monthly_rate = (annual_rate / 100) / 12  # Convert yearly rate to monthly
    tenure = tenure_months

    # EMI Formula
    emi = (principal * monthly_rate * (1 + monthly_rate) ** tenure) / (
        (1 + monthly_rate) ** tenure - 1
    )
    total_interest = (emi * tenure) - principal
    total_amount = principal + total_interest

    # Generate Payment Schedule
    schedule = []
    start_date = datetime.today()

    for i in range(1, tenure + 1):
        due_date = start_date + timedelta(days=30 * i)  # Approximate next due date
        schedule.append(
            {
                "installment_no": i,
                "due_date": due_date.strftime("%Y-%m-%d"),
                "amount": round(emi, 2),
            }
        )

    return {
        "monthly_installment": round(emi, 2),
        "total_interest": round(total_interest, 2),
        "total_amount": total_amount,
        "payment_schedule": schedule,
    }


def calculate_foreclosure_amount(principal_remaining, annual_interest_rate, discount=0):
    """
    Calculate the foreclosure amount based on compound interest.

    :param principal_remaining: Remaining loan principal
    :param annual_interest_rate: Interest rate (in %)
    :param months_left: Remaining months of the loan
    :param discount: Foreclosure discount amount
    :return: Foreclosure amount to be paid
    """
    monthly_interest_rate = (annual_interest_rate / 12) / 100
    interest_for_remaining_months = principal_remaining * monthly_interest_rate

    foreclosure_amount = principal_remaining + interest_for_remaining_months - discount
    return max(foreclosure_amount, 0)  # Ensure it's never negative
