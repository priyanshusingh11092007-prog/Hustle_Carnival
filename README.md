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

## Deployment

### Render (recommended)

The repository includes a `render.yaml` Blueprint. In Render, create a new
Blueprint from this repository and provide `ADMIN_USERNAME` and
`ADMIN_PASSWORD` when prompted. Use an admin password of at least 12
characters. The Blueprint installs dependencies, initializes the database,
creates the demo services and admin account, and runs the app with Gunicorn.

The Blueprint provisions a managed PostgreSQL database and wires its
connection string into the web service, so queue data persists across deploys
and restarts.

### Vercel

The repository includes a Vercel function and rewrite configuration. Before
deploying, connect a PostgreSQL database (for example, through Vercel
Marketplace) and configure these environment variables for the Vercel
environments you will deploy:

- `DATABASE_URL` or `POSTGRES_URL`: the PostgreSQL connection string.
- `SECRET_KEY`: a long, random secret.
- `ADMIN_USERNAME` and `ADMIN_PASSWORD`: the initial administrator
  credentials. Use a password of at least 12 characters.

Deploy the repository from Vercel. The function initializes the database
schema on startup. To create the demo services and administrator account,
install the Vercel CLI, link the local repository to the Vercel project, and
run these commands from the repository root:

    vercel env pull .env.vercel --environment=production
    python -c "from dotenv import load_dotenv; load_dotenv('.env.vercel', override=True); from scripts.seed_demo import seed; seed()"

The `.env.vercel` file contains secrets; do not commit it. Vercel's local
filesystem is ephemeral, so SQLite is not suitable for deployed queue data.
Use PostgreSQL by setting one of the connection-string variables above.

### Other WSGI hosts

Install `requirements.txt`, set `SECRET_KEY`, and set either `DATABASE_URL`
or `POSTGRES_URL` to a PostgreSQL connection string. Set `ADMIN_USERNAME` and
`ADMIN_PASSWORD` as well. Then initialize and seed the database once:

    flask --app run init-db
    python scripts/seed_demo.py

Start the production server with:

    gunicorn --bind 0.0.0.0:$PORT run:app

Set `PORT` to the port supplied by your hosting platform. SQLite remains
available for local development; use PostgreSQL for durable hosted data.

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
