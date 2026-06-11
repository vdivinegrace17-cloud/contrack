# ConTrack — Booth & Table Reservation System

A Python/Django web application for managing booth and table reservations
at festivals, conventions, faires, bazaars, and other public events.

## Tech Stack
- **Backend:** Python 3.10+, Django 4.2
- **Database:** SQLite (dev) → PostgreSQL (production)
- **Maps:** Leaflet.js (free, no API key needed)
- **Frontend:** Bootstrap 5 (CDN), Vanilla JS

---

## Quick Start (Development)

### 1. Clone and set up virtual environment
```bash
git clone <repo-url>
cd contrack
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Open .env and set SECRET_KEY — generate one with:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Run migrations and create superuser (Admin)
```bash
python manage.py migrate
python manage.py createsuperuser
# When prompted, this creates the platform Admin account.
# In the shell or admin panel, set: user.role = 'ADMIN'
```

### 5. Run the development server
```bash
python manage.py runserver
# Open http://127.0.0.1:8000
```

---

## Database Options

| Option       | Setup       | Cost  | Recommended for         |
|--------------|-------------|-------|-------------------------|
| **SQLite**   | Zero config | Free  | Development & student use |
| **PostgreSQL (local)** | Install Postgres | Free | Local production testing |
| **Supabase** | Sign up online | Free tier | Cloud deployment        |
| **Neon**     | Sign up online | Free tier | Cloud deployment        |

To switch to PostgreSQL, set in `.env`:
```
DATABASE_URL=postgres://user:password@localhost:5432/contrack_db
```

---

## Project Structure

```
contrack/
├── contrack/           # Django project settings & root URLs
├── apps/
│   ├── accounts/       # User model, login, dashboards, role-based access
│   ├── organizations/  # Organizer org registration & Admin approval
│   ├── events/         # Event creation and public directory
│   ├── booths/         # Floor plans, booth tagging (Leaflet), booth model
│   ├── reservations/   # Merchant applications, status tracking
│   ├── payments/       # Proof of payment submission & verification
│   └── notifications/  # In-system alerts and organizer↔merchant messaging
├── templates/          # HTML templates (extends base.html)
├── static/
│   └── js/
│       └── floorplan.js  # Leaflet floor plan viewer & tagger
└── media/              # Uploaded files (floor plans, logos, payment proofs)
```

## User Roles

| Role          | What they can do                                              |
|---------------|---------------------------------------------------------------|
| **Admin**     | Approve/reject organizer org registrations, platform oversight |
| **Organizer** | Manage events, upload floor plans, tag booths, review applications, verify payments |
| **Merchant**  | Browse events, view floor plans, apply for booths, submit payment proof |

## Floor Plan / Leaflet Architecture

- Organizer uploads a venue image (JPG/PNG)
- `booth_tagger.html` loads `floorplan.js` in **tagger mode**:
  - Click anywhere on the image to place a booth marker
  - Drag markers to reposition
  - Coordinates saved as x%/y% (resolution-independent) via AJAX
- `floor_plan.html` loads `floorplan.js` in **viewer mode**:
  - Color-coded markers: 🟢 Available · 🟠 Pending · 🔴 Reserved · ⚫ Unavailable
  - Click a green marker → opens reservation application form
