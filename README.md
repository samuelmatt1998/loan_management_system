# OTP Verification Microservice

## 📌 Overview

This is a **Django + Node.js microservice** for OTP-based email verification. The backend uses Django REST Framework (DRF) for handling user registration and OTP verification, while Node.js + Nodemailer sends OTP emails.

## 🚀 Features

- **User Registration** with OTP verification.
- **JWT Authentication** using Django SimpleJWT.
- **Secure OTP Storage** in a Django model.
- **Automatic OTP Expiry** (5 minutes).
- **Email Sending via Node.js & Nodemailer**.

---

## 📁 Project Structure

```
/loan_management
│── /loans
│   ├── models.py   # Django models (User, OTP, Loan, etc.)
│   ├── views.py    # API endpoints
│   ├── serializers.py # Serializers for Django REST Framework
│── /otp_service (Node.js server)
│   ├── server.js   # Nodemailer logic for OTP email
│── manage.py       # Django management script
│── requirements.txt # Python dependencies
│── package.json    # Node.js dependencies
│── README.md       # Documentation
```

---

## 🔧 Setup Instructions

### 1️⃣ **Backend (Django)**

#### **Prerequisites:**

- Python < 3.13 (ensure compatibility with psycopg2)
- PostgreSQL

#### **Installation:**

```sh
# Clone the repository
git clone https://github.com/samuelmatt1998/loan_management_system.git && cd loan_management

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Run the Django server
python manage.py runserver
```

### 2️⃣ **Frontend (Node.js OTP Service)**

#### **Installation:**

```sh
cd loan_management_system
npm install  # Install dependencies
```

#### **Run the server:**

```sh
npm run dev  # Start Node.js server in development mode
```

#### **Environment Variables (**``**)**

Create a `.env` file in both Django and Node.js directories:

```ini
# Django Backend
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=your_database_url

# Node.js OTP Service
EMAIL_USER=your-email@example.com
EMAIL_PASS=your-email-password
```

---

## 📌 API Endpoints

### **1️ Register User & Send OTP**

```http
POST /api/email-register/
```

#### **Request Body:**

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### **Response:**

```json
{
  "message": "OTP sent successfully"
}
```

### **2️ Verify OTP**

```http
POST /api/verify-otp/
```

#### **Request Body:**

```json
{
  "email": "john@example.com",
  "otp": "123456"
}
```

#### **Response:**

```json
{
  "message": "OTP Verified. User Registered."
}
```

### **3️ Login**

```http
POST /api/login/
```

#### **Request Body:**

```json
{
  "email": "john@example.com",
  "password": "securepassword"
}
```

#### **Response:**

```json
{
  "message": "Login Success",
  "token": {
    "refresh": "refresh_token_here",
    "access": "access_token_here"
  }
}
```

### **4 Add Loan**

```http
POST /api/add-loan/
```

#### **Request Body:**

```json
{ 
    "amount": 15000, "interest_rate": 10, 
    "duration_months": 12
}
```

#### **Response:**

```json
{
    "status": "success",
    "data": {
        "loan_id": "loan_aa9ede94_usr1",
        "amount": 15000.0,
        "tenure": 12,
        "total_amount": 15824.86,
        "amount_remaining": 15824.86,
        "monthly_installment": 1318.74,
        "status": "ACTIVE",
        "created_at": "2025-03-02T09:55:02.545615+00:00"
    }
}
```
### **5 Make Loan Payment**

```http
POST /api/make-payment/
```

#### **Request Body:**

```json
{ 
    "loan_id":"loan_aa9ede94_usr1" 
}
```

#### **Response:**

```json
{
    "status": "success",
    "data": {
        "loan_id": "loan_aa9ede94_usr1",
        "monthly_emi": 1318.74,
        "amount_remaining": 14506.12,
        "status": "ACTIVE"
    }
}
```
### **6 View User Loan**

```http
GET /api/view-loan/
```

#### **Request Body:**

```json
{ 
    
}
```

#### **Response:**

```json
{
    "status": "success",
    "data": {
        "loans": [
            {
                "loan_id": "loan_a3f4eca4_usr1",
                "amount": 10000.0,
                "tenure": 12,
                "rate": "10.00% per year",
                "total_amount": 0.0,
                "amount_paid": 0.0,
                "amount_remaining": 0.0,
                "next_due_date": "2025-04-01",
                "status": "CLOSED",
                "created_at": "2025-02-28T11:52:30.373002+00:00"
            },
           
            
            {
                "loan_id": "loan_aa9ede94_usr1",
                "amount": 15000.0,
                "tenure": 12,
                "rate": "10.00% per year",
                "total_amount": 15824.86,
                "amount_paid": 1318.74,
                "amount_remaining": 14506.12,
                "next_due_date": "2025-04-01",
                "status": "ACTIVE",
                "created_at": "2025-03-02T09:55:02.545615+00:00"
            }
        ]
    }
}
```

### **7 View User Loan**

```http
GET /api/foreclose/
```

#### **Request Body:**

```json
{ 
    "loan_id":"loan_aa9ede94_usr1"
}
```

#### **Response:**

```json
{
    "status": "success",
    "message": "Loan foreclosed successfully.",
    "foreclosure_amount": 13295.27,
    "discount_applied": 500,
    "amount_paid": 12795.2705
}
```

### **8 View All Loan - Admin Only**

```http
GET /api/view-all-loan/
```

#### **Request Body:**

```json
{

}
```

#### **Response:**

```json
{
    "status": "success",
    "data": 
    {
        "loans": [
            {
                "loan_id": "loan_b92bad99_usr1",
                "user_id": 1,
                "amount": 10000.0,
                "tenure": 12,
                "rate": "10.00% per year",
                "total_amount": 0.0,
                "amount_paid": -10000.0,
                "amount_remaining": 10000.0,
                "monthly_emi": 0.0,
                "status": "ACTIVE",
                "created_at": "2025-03-02T01:44:37.074657+00:00"
            },"......other loans"
        ]
    }
}
```

### **9 View All Loan - Admin Only**

```http
GET /api/view-all-loan/
```

#### **Request Body:**

```json
{
    
}
```

#### **Response:**

```json
{
    "status": "success",
    "data": 
    {
        "loans": [
            {
                "loan_id": "loan_b92bad99_usr1",
                "user_id": 1,
                "amount": 10000.0,
                "tenure": 12,
                "rate": "10.00% per year",
                "total_amount": 0.0,
                "amount_paid": 0.0,
                "amount_remaining": 10000.0,
                "monthly_emi": 0.0,
                "status": "ACTIVE",
                "created_at": "2025-03-02T01:44:37.074657+00:00"
            },"......other loans"
        ]
    }
}
```
### **10 View a particular user's Loan - Admin Only**

```http
GET /api/view-user-loan/
```

#### **Request Body:**

```json
{
    "user_id":1
}
```

#### **Response:**

```json
{
    "status": "success",
    "data": 
    {
        "loans": [
            {
                "loan_id": "loan_b92bad99_usr1",
                "amount": 10000.0,
                "tenure": 12,
                "rate": "10.00% per year",
                "total_amount": 0.0,
                "amount_paid": 0.0,
                "amount_remaining": 10000.0,
                "monthly_emi": 0.0,
                "status": "ACTIVE",
                "created_at": "2025-03-02T01:44:37.074657+00:00"
            },"......other loans"
        ]
    }
}
```

### **11 Delete user's Loan - Admin Only**

```http
DELETE /api/delete-loan/
```

#### **Request Body:**

```json
{
    "loan_id":"loan_e6ad9b7d_usr1"
}
```

#### **Response:**

```json
{
    "status": "success",
    "message": "Loan loan_e6ad9b7d_usr1 has been deleted"
}
```


---



---



## 🛠 Tech Stack

- **Backend:** Django, DRF, PostgreSQL
- **Auth:** JWT (SimpleJWT)
- **Email Service:** Node.js, Nodemailer
- **Deployment:** Render (Free Tier)

---

## 📌 Notes

- OTP expires in **5 minutes**.
- Emails are sent via **Node.js (Nodemailer)**.
- Passwords are **hashed** before storage.

---

## 📄 License

This project is open-source under the MIT License.

---

## 💡 Future Improvements

- Rate limiting to prevent OTP spam.
- Multi-factor authentication.
- Use Redis for OTP verification


---



