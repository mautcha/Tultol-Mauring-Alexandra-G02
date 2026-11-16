# Tultol — Indoor Mall Navigation System

**CSIT327 – Information Management 2 (Project Development 2)**  
**Student:** Alexandra Louie C. Mauring (G02)  
**Repository:** [Tultol-Mauring-Alexandra-G02](https://github.com/mautcha/Tultol-Mauring-Alexandra-G02)

## Overview
Tultol is a Django-based indoor mall navigation web application for Metro Cebu malls (such as SM Seaside City Cebu, Ayala Center Cebu, and SM City Cebu). It helps shoppers locate stores, check floor levels and landmark directions, and save favorite stores with personal visit notes, while allowing Mall Admins to manage mall, floor, and store records.

## Core Feature (Project Development 2)
**Mall Store & Floor Directory + Shopper Saved Stores (Vertical Slice)**
- **Mall Admins (`admin` role):** Full CRUD for `Mall`, `Floor`, and `Store` records (including unit codes, categories, operating hours, open/closed status, and indoor landmark directions).
- **Shoppers (`shopper` role):** Search and filter stores by keyword, mall, and category; browse malls and floor levels; view detailed landmark directions; and bookmark stores to **My Saved Stores** (`SavedStore`) with personal visit notes (Create, Read, Update note, Delete — strictly scoped to `request.user`).
- **Standard Features (PD1):** Shopper registration, login/logout (username or email, POST logout), role-based dashboards (`shopper` and `admin`), user profile view/edit with photo upload, change password, and password reset.

## Tech Stack
- **Backend:** Python 3.15, Django 6.1.3
- **Database:** PostgreSQL (Supabase Session Pooler)
- **Media/Images:** Pillow 13.0.0

## Setup Steps

1. **Clone the repository and create a virtual environment:**
   ```bash
   git clone https://github.com/mautcha/Tultol-Mauring-Alexandra-G02.git
   cd Tultol-Mauring-Alexandra-G02
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your `SECRET_KEY` and Supabase PostgreSQL connection details (`DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`):
   ```bash
   cp .env.example .env
   ```

4. **Apply database migrations to Supabase:**
   ```bash
   python manage.py migrate
   ```

5. **Create a default Mall Admin account:**
   ```bash
   python manage.py create_default_admin --password YourTestAdminPassword123!
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/`.

7. **Run automated tests (uses in-memory SQLite):**
   ```bash
   python manage.py test
   ```
