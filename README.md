# SalesOps AI CRM

SalesOps AI CRM is a Django-based sales management application for tracking
leads, categories, order-bringing agents, activity history, revenue, and
AI-assisted forecasting.

## Features

- Lead, category, and agent management
- Sales status tracking
- Revenue capture and Excel export
- Lead detail timeline
- Activity tracking
- Gemini-powered sales forecasting
- Authentication and password reset
- Responsive dashboard UI
- Dark mode support
- Django admin customization
- Unit and functional test setup

## Forecasting Inputs

The forecasting page uses the current CRM data already stored in the project:

- Lead status
- Lead revenue
- Lead category
- Lead agent
- Lead age
- Lead created and updated timestamps
- Activity type
- Activity completion state
- Activity created and updated timestamps

## Setup

Create and activate a virtual environment:

```bash
py -3 -m venv .venv
.venv\scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
npm install
```

Run migrations:

```bash
py manage.py migrate
```

Build static CSS:

```bash
npm run build
```

Start the development server:

```bash
py manage.py runserver
```

Open the app:

```text
http://127.0.0.1:8000/
```

## Gemini Forecasting

Add your Google AI Studio key in:

```text
config/gemini_config.py
```

Then open:

```text
http://127.0.0.1:8000/dashboard/forecasting/
```

## Tests

Run the test suite:

```bash
pytest
```
