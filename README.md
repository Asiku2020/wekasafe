# WekaSafe Backend - Quick Start Guide

## Features
- Secure admin authentication with JWT
- Automatic email notifications for quotes and incidents
- Beautiful admin dashboard with statistics
- Role-based access control (Admin & Viewer)
- File upload security
- Export data to CSV
- Search and filter functionality

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Email Settings

Edit `.env` file:

**For Gmail (Recommended):**
```env
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password-here
MAIL_FROM=info@wekasafe.com
ADMIN_EMAIL=your-email@gmail.com
```

**How to get Gmail App Password:**
1. Go to Google Account Settings
2. Security → 2-Step Verification (enable if not already)
3. Visit: https://myaccount.google.com/apppasswords
4. Generate app password for "Mail"
5. Copy the 16-character password (ignore spaces)
6. Paste in `.env` as `MAIL_PASSWORD`

**Generate Secure Keys:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Use output for `JWT_SECRET` and `SESSION_SECRET` in `.env`

### 3. Test Email Configuration
```bash
python test_email.py
```

### 4. Start the Server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Create Admin Account

**Option A - Using Browser:**
Visit: `http://localhost:8000/admin/setup`

**Option B - Using curl:**
```bash
curl -X POST http://localhost:8000/admin/setup \
  -F "email=admin@wekasafe.com" \
  -F "password=YourSecurePassword123"
```

### 6. Login to Dashboard

Visit: `http://localhost:8000/admin/login`

Login with your admin credentials.

## Dashboard Features

### Statistics Overview
- Total Quotes
- Total Incidents
- Pending Incidents
- Resolved Incidents

### Quote Management
- View all quote requests
- Search quotes
- Export to CSV
- Reference numbers (QT-######)

### Incident Management
- View all incident reports
- Filter by status (Pending/Resolved)
- Filter by severity (Critical/High/Medium/Low)
- View attachments
- Mark as resolved
- Export to CSV

## API Endpoints

### Public Endpoints
- `POST /api/submit-quote` - Submit quote request
- `POST /api/incident-report` - Submit incident report

### Admin Endpoints
- `GET /admin/login` - Login page
- `POST /admin/login` - Login action
- `GET /admin/logout` - Logout
- `GET /admin/dashboard` - Main dashboard
- `GET /admin/quotes` - View all quotes
- `GET /admin/incidents` - View all incidents
- `GET /admin/incident/{id}` - View incident details
- `POST /api/admin/incidents/{id}/resolve` - Mark incident as resolved
- `GET /admin/export/quotes` - Export quotes to CSV
- `GET /admin/export/incidents` - Export incidents to CSV

## Email Notifications

### When Quote is Submitted:
1. **Customer receives** confirmation email with reference number
2. **Admin receives** notification with quote details

### When Incident is Reported:
1. **Reporter receives** confirmation with reference number
2. **Admin receives** alert with incident details and severity

## Security Features

- JWT-based authentication
- httpOnly cookies
- Bcrypt password hashing
- XSS prevention (input sanitization)
- File upload validation (type & size)
- SQL injection prevention (SQLAlchemy ORM)
- Role-based access control
- Password reset limit (3 times)

## File Upload Security

- Allowed file types: `.jpg`, `.jpeg`, `.png`, `.pdf`, `.doc`, `.docx`, `.txt`
- Maximum file size: 10MB per file
- Secure filename generation
- Isolated upload directory

## User Roles

### Admin
- Full access to all features
- Can resolve incidents
- Can export data
- Can manage system

### Viewer
- Read-only access
- View quotes and incidents
- Cannot resolve incidents
- Cannot export data

## Troubleshooting

### Email Not Sending
1. Verify Gmail App Password (not regular password)
2. Check `.env` configuration
3. Run `python test_email.py`
4. Check if port 587 is open
5. Review server logs

### Login Issues
1. Verify admin account created successfully
2. Check `JWT_SECRET` in `.env`
3. Clear browser cookies
4. Check server terminal for errors

### Database Issues
1. Delete `wekasafe.db` file
2. Restart server (tables auto-create)
3. Run `python verify_setup.py`

## Production Deployment

### Before deploying:
1. Change all default secrets in `.env`
2. Set strong admin password
3. Enable HTTPS
4. Configure proper CORS origins
5. Use production database (PostgreSQL)
6. Set up regular backups
7. Enable rate limiting
8. Configure monitoring

### Production command:
```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Support

- Check server logs in terminal
- Review `.env` configuration
- Test email separately
- Check SETUP.md for detailed guide
- Review SECURITY.md for security best practices

## File Structure

```
wekasafe-backend/
├── main.py                 # Main application
├── auth.py                 # Authentication logic
├── models.py               # Database models
├── schemas.py              # Pydantic schemas
├── utils.py                # Utility functions
├── database.py             # Database configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── test_email.py           # Email testing script
├── verify_setup.py         # Setup verification
├── templates/              # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── quotes.html
│   ├── incidents.html
│   └── incident_detail.html
├── static/                 # Static files
└── uploads/                # Uploaded files
```

## License
© 2024 WekaSafe Solutions. All rights reserved.