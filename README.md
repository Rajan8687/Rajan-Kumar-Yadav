# Rajan Kumar Yadav — Personal Blog

Flask + Tailwind blog with a yellow-accented professional layout, dark mode toggle, contact form, admin post creator, and your logo photo wired into the site.

Quick start

1. Copy the env file and set secrets:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Run the app:

```bash
python3 app.py
```

The logo image is at `static/img/logo.jpg`.
The admin page is `/admin` and uses `ADMIN_PASSWORD` from `.env`.
Contact form submissions are saved in SQLite and emailed to `profile.email` when the SMTP settings are configured in `.env`.
For Gmail, use an app password instead of your regular password.
