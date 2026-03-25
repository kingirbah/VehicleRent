# 🏍️ VehicleRent

A motorcycle rental management web app built with Flask. Supports vehicle listings, booking management, image uploads, and admin reporting.

---

## Preview

> Add a screenshot here.

---

## Tech Stack

| | |
|---|---|
| Backend | Flask 3.0 + Python |
| Database | SQLite / PostgreSQL |
| Frontend | Tailwind CSS + Alpine.js |
| Image Processing | Pillow (PIL) |

---

## Features

- Vehicle management with photo & license plate
- Booking system with auto-generated booking numbers (`JS-YYYYMMDD-XXXX`)
- Customer nationality tracking
- Admin dashboard with filters & statistics
- Print-ready booking reports
- Auto image compression (< 1MB)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/kingirbah/VehicleRent.git
cd VehicleRent
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS / Linux
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the App

```bash
python app.py
```

### 5. Open in Browser

```
http://localhost:5000/login
```

Default admin password: `admin123` ⚠️ Change this before deploying.

---

## Project Structure

```
VehicleRent/
├── app.py                  # Main application
├── requirements.txt
├── .env.example            # Environment variable template
├── templates/              # HTML templates
└── static/
    └── uploads/            # Uploaded vehicle images
```

---

## License

Personal project — for learning purposes.