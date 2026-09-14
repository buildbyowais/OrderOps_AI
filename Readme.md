# 🤖 OrderOps AI

**OrderOps AI** is an AI-powered order processing and fulfillment system built with **FastAPI, MySQL, SQLAlchemy, LangGraph, and Google Gemini**.

It automates the order lifecycle from **customer risk checking and stock validation** to **alternative product offers, customer approval, and fulfillment**.

## ✨ Features

* 👤 Customer risk assessment
* 📦 Automatic stock availability checking
* 🔄 Alternative product detection
* 🤖 AI-powered customer offers using Google Gemini
* 💰 Automatic discount and final price calculation
* 📧 Customer email notifications
* 🙋 Human-in-the-loop customer approval
* ✅ Automatic order fulfillment
* 📊 Inventory/stock deduction
* 🛡️ Gemini fallback handling when the AI service is unavailable
* 🌐 REST API with Swagger documentation

## 🔄 Workflow

```text
Order
  ↓
Risk Check
  ↓
Stock Check
  ↓
 ┌──────────────────┐
 │ Product Available│
 └────────┬─────────┘
          │
          ↓
     Fulfillment

If Out of Stock
       ↓
Find Alternative
       ↓
Create AI Offer
       ↓
Send Email
       ↓
Customer Approval
       ↓
   ┌───────┴───────┐
   ↓               ↓
ACCEPT           REJECT
   ↓               ↓
Fulfillment      End
```

## 🛠️ Tech Stack

* **Python**
* **FastAPI**
* **MySQL**
* **SQLAlchemy**
* **LangGraph**
* **Google Gemini API**
* **SMTP / Email**
* **Uvicorn**
* **HTML / CSS / JavaScript**

## 📁 Project Structure

```text
OrderOps_AI/
│
├── app/
│   ├── frontend/
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   │
│   ├── services/
│   │   ├── offer_service.py
│   │   └── ...
│   │
│   ├── workflow/
│   │   └── order_workflow.py
│   │
│   ├── utils/
│   │   └── database.py
│   │
│   ├── models.py
│   └── main.py
│
├── order_env/
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd OrderOps_AI
```

### 2. Create Virtual Environment

```bash
python -m venv order_env
```

Activate it on Windows:

```bash
order_env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file and add your database, Gemini API, and email credentials:

```env
DATABASE_URL=your_database_url
GEMINI_API_KEY=your_gemini_api_key
EMAIL_HOST=your_smtp_host
EMAIL_PORT=your_smtp_port
EMAIL_USERNAME=your_email
EMAIL_PASSWORD=your_email_password
```

> ⚠️ Never commit `.env` or API keys/passwords to GitHub.

## ▶️ Run the Application

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 📚 API Documentation

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## 🔌 Main API

### Process an Order

```http
POST /orders/{order_id}/process
```

Example:

```text
POST /orders/13/process
```

This starts the complete order-processing workflow.

## 🤖 AI Offer System

When a product is unavailable, OrderOps AI:

1. Finds a suitable alternative product.
2. Retrieves the approved discount from the database.
3. Calculates the final offered price.
4. Uses Google Gemini to generate a customer-friendly message.
5. Sends the offer to the customer through email.
6. Waits for customer approval.

If Gemini is temporarily unavailable, the system uses a **fallback offer message** so the order workflow can continue without failing.

## 🙋 Human-in-the-Loop

Customer approval is required when an alternative product is offered.

```text
Alternative Found
       ↓
Offer Created
       ↓
Email Sent
       ↓
Customer Response
       ↓
 ┌─────┴─────┐
 ↓           ↓
ACCEPT      REJECT
 ↓           ↓
Fulfill     End
```

## 🗄️ Database

The application uses MySQL with SQLAlchemy.

Main database entities:

* **Customers**
* **Products**
* **Orders**
* **Alternatives**
* **Refunds**

The `Alternatives` table connects unavailable products with suitable replacement products and their approved discounts.

## 📧 Email Notifications

The system automatically sends customers an email containing:

* Alternative product
* Discount
* Final offered price
* Order information
* Customer-friendly offer message

## 👨‍💻 Author

**Muhammad Owais**