# QueueSathi

A Smart Digital Queue and Waiting-Time Management System.

## Overview

QueueSathi is a Flask-based web application for managing campus
service queues.

Students can generate digital tokens and monitor their queue status.

Staff can manage tokens through a protected dashboard.

Administrators can manage services and review statistics.

## Technology

- Python
- Flask
- SQLite
- HTML
- CSS
- JavaScript

## Features

- Unique digital tokens
- Queue status tracking
- Estimated waiting time
- Staff dashboard
- Walk-in registration
- Hold, cancel and no-show
- Service management
- Basic reports
- Persistent SQLite database

## Installation

Create a virtual environment:

    python -m venv .venv

Activate it:

Windows:

    .venv\Scripts\activate

Linux/macOS:

    source .venv/bin/activate

Install dependencies:

    pip install -r requirements.txt

Copy .env.example to .env.

Generate a strong SECRET_KEY:

    python -c "import secrets; print(secrets.token_hex(32))"

Set a strong ADMIN_PASSWORD in .env.

Initialize the database:

    flask --app run init-db

Create demo services and an admin account:

    python scripts/seed_demo.py

Start the application:

    python run.py

Open:

    http://127.0.0.1:5000

## Staff Login

Visit:

    http://127.0.0.1:5000/login

Use the credentials configured in .env.

## Testing

Run:

    python -m pytest tests -v

## Demo

1. Open the customer homepage.
2. Generate several tokens.
3. Open the staff dashboard.
4. Call the next token.
5. Start serving.
6. Complete the token.
7. Observe updated queue positions.
8. Open the reports page.

## Limitations

This application is a demonstration prototype.

It assumes one active service counter per service.

It does not implement SMS, AI, multi-counter routing or
institutional authentication.

Live deployment requires security review, operational policies,
load testing and institutional approval.
