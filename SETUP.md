# WekaSafe Backend - Complete Setup Guide

## 📋 Overview

This is a complete, production-ready admin backend system for WekaSafe with:

- ✅ **Secure Authentication** - JWT-based with httpOnly cookies
- ✅ **Email Notifications** - Automatic replies to users & admin alerts
- ✅ **Admin Dashboard** - View all quotes and incident reports
- ✅ **Role-Based Access** - Admin and Viewer roles
- ✅ **File Upload Security** - Type validation & size limits
- ✅ **XSS Prevention** - Input sanitization
- ✅ **Export Functionality** - CSV export for quotes & incidents
- ✅ **Search & Filter** - Easy data management

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Email (IMPORTANT!)

Edit the `.env` file with your email settings:

**For Gmail (Recommended for testing):**
```env
MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_FROM=info@wekasafe.com
ADMIN_EMAIL=your-email@gmail.com
```

**How to get Gmail App Password:**
1. Go to your Google Account: https://myaccount.google.com
2. Navigate to Security
3. Enable 2-Step Verification (if not already enabled)
4. Go to App Passwords: https://myaccount.google.com/apppasswords
5. Select "Mail" and generate a password
6. Copy the 16-character password (no spaces)
7. Paste it in the `.env` file as `MAIL_PASSWORD`

### 3. Generate Secure Keys

Replace the JWT and Session secrets in `.env`:

```bash
# Generate secure random keys
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Use the output for both `JWT_SECRET` and `SESSION_SECRET`.

### 4. Test Email Configuration

```bash
python test_email.py
```

If successful, you'll receive a test email. If it fails, check your email credentials.

### 5. Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Create First Admin Account

Visit: `http://localhost:8000/admin/setup`

Or use curl:
```bash
curl -X POST http://localhost:8000/admin/setup \
  -F "email=admin@wekasafe.com" \
  -F "password=YourSecurePassword123"
```

**Important:** After creating the first admin, this endpoint is automatically disabled.

---

## 🔐 Security Features Implemented

### 1. Authentication & Authorization
- JWT tokens with httpOnly cookies
- Role-based access control (Admin, Viewer)
- Secure password hashing with bcrypt
- Session management with secure cookies

### 2. Input Validation
- XSS prevention through input sanitization
- Email validation
- Phone number validation
- SQL injection prevention (SQLAlchemy ORM)

### 3. File Upload Security
- File type whitelist (`.jpg`, `.jpeg`, `.png`, `.pdf`, `.doc`, `.docx`, `.txt`)
- File size limit (10MB per file)
- Secure filename generation
- Isolated upload directory

### 4. Rate Limiting (Basic)
- Password reset limited to 3 attempts per account
- Login attempt tracking (can be enhanced with Redis)

### 5. HTTPS Ready
- Configurable secure cookies
- CORS settings for production

---

## 📧 Email Notifications

### Automatic Emails Sent

**When a Quote is Submitted:**
1. **Customer receives:**
   - Confirmation of quote receipt
   - Reference number (QT-######)
   - Expected response time (24 hours)
   - Contact information

2. **Admin receives:**
   - Alert notification
   - All quote details
   - Direct link to admin dashboard

**When an Incident is Reported:**
1. **Reporter receives:**
   - Incident reference number (INC-##########)
   - Confirmation of report receipt
   - Safety team contact info
   - Privacy assurance

2. **Admin receives:**
   - Severity-based alert (🚨 Critical, ⚠️ High, etc.)
   - Full incident details
   - Attachment count and list
   - Direct link to incident details

---

## 🎨 Admin Dashboard Features

### Dashboard Overview
- **Statistics Cards:**
  - Total Quotes
  - Total Incidents
  - Pending Incidents
  - Resolved Incidents
  
- **Recent Activity:**
  - Latest 5 quote requests
  - Latest 8 incident reports
  
- **Severity Breakdown:**
  - Visual breakdown by incident severity

### Quotes Management
- View all quote requests
- Search functionality
- Export to CSV
- Reference numbers (QT-######)

### Incidents Management
- View all incident reports
- Filter by:
  - Status (Pending/Resolved)
  - Severity (Critical/High/Medium/Low)
- Search functionality
- Export to CSV
- View attachments
- Mark as resolved (Admin only)

### Detailed Incident View
- Complete incident information
- Timeline view
- Attachment downloads
- One-click resolution

---

## 🔧 API Endpoints

### Public Endpoints (No Auth Required)

```
POST /api/submit-quote
POST /api/incident-report
POST /admin/setup (one-time only)
```

### Admin Endpoints (Auth Required)

```
GET  /admin/login
POST /admin/login
GET  /admin/logout
GET  /admin/dashboard
GET  /admin/quotes
GET  /admin/incidents
GET  /admin/incident/{id}

GET  /api/admin/quotes
GET  /api/admin/incidents
GET  /api/admin/incidents/{id}
POST /api/admin/incidents/{id}/resolve
GET  /api/admin/stats

GET  /admin/export/quotes (Admin only)
GET  /admin/export/incidents (Admin only)
```

---

## 👥 User Roles

### Admin
- Full access to all features
- Can resolve incidents
- Can export data
- Can manage users (via database)

### Viewer
- Read-only access
- View quotes and incidents
- Cannot resolve incidents
- Cannot export data

---

## 📊 Database Schema

### Users Table
```sql
- id (Primary Key)
- email (Unique)
- hashed_password
- role (admin/viewer)
- reset_count (max 3)
- created_at
```

### Quotes Table
```sql
- id (Primary Key)
- name
- email
- phone
- service
- message
- timestamp
```

### Incidents Table
```sql
- id (Primary Key)
- reference (Unique, INC-##########)
- reporter_name
- contact
- datetime
- location
- incident_type
- severity
- description
- attachments
- resolved (Boolean)
- resolved_at
- timestamp
```

---

## 🔄 Password Reset

Admins can reset their password up to 3 times:

```bash
curl -X POST http://localhost:8000/admin/reset \
  -F "email=admin@wekasafe.com" \
  -F "password=NewPassword123"
```

After 3 resets, the account is locked and requires database intervention.

---

## 📱 Frontend Integration

### Quote Form Integration

```javascript
// Example: Submit quote from your index.html
const submitQuote = async (formData) => {
  const response = await fetch('http://localhost:8000/api/submit-quote', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      name: formData.name,
      email: formData.email,
      phone: formData.phone,
      service: formData.service,
      message: formData.message
    })
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Quote submitted! Reference:', result.reference);
  }
};
```

### Incident Report Integration

```javascript
// Example: Submit incident report with files
const submitIncident = async (formData) => {
  const form = new FormData();
  form.append('reporter_name', formData.name);
  form.append('contact', formData.email);
  form.append('datetime_field', formData.datetime);
  form.append('location', formData.location);
  form.append('incident_type', formData.type);
  form.append('severity', formData.severity);
  form.append('description', formData.description);
  
  // Add files
  for (let file of formData.files) {
    form.append('files', file);
  }
  
  const response = await fetch('http://localhost:8000/api/incident-report', {
    method: 'POST',
    body: form
  });
  
  const result = await response.json();
  if (result.success) {
    console.log('Incident reported! Reference:', result.reference);
  }
};
```

---

## 🚀 Deployment

### Production Checklist

1. **Security:**
   - [ ] Change all default secrets in `.env`
   - [ ] Set strong passwords
   - [ ] Enable HTTPS
   - [ ] Set `SECURE_COOKIES=true`
   - [ ] Configure proper CORS origins
   - [ ] Implement rate limiting with Redis

2. **Email:**
   - [ ] Use production email service (SendGrid, AWS SES, etc.)
   - [ ] Verify domain for SPF/DKIM
   - [ ] Test email delivery

3. **Database:**
   - [ ] Migrate from SQLite to PostgreSQL/MySQL
   - [ ] Set up database backups
   - [ ] Configure connection pooling

4. **Server:**
   - [ ] Use production WSGI server (Gunicorn)
   - [ ] Set up reverse proxy (Nginx)
   - [ ] Configure SSL certificates
   - [ ] Enable firewall

5. **Monitoring:**
   - [ ] Set up error logging
   - [ ] Configure monitoring alerts
   - [ ] Track uptime

### Production Command

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🐛 Troubleshooting

### Email Not Sending

1. Check `.env` configuration
2. Verify Gmail App Password (not regular password)
3. Check firewall/port 587 is open
4. Run `python test_email.py`
5. Check server logs for errors

### Login Not Working

1. Verify admin account was created successfully
2. Check JWT_SECRET in `.env`
3. Clear browser cookies
4. Check server logs

### Files Not Uploading

1. Check `UPLOAD_DIR` exists and is writable
2. Verify file size (10MB limit)
3. Check file extension is allowed
4. Review server logs

### Database Errors

1. Delete `wekasafe.db` and restart server
2. Check SQLAlchemy models match database
3. Run `python verify_setup.py`

---

## 📞 Support

For issues or questions:
- Check the logs in terminal
- Review error messages carefully
- Verify all `.env` settings
- Test email configuration separately

---

## 📄 License

© 2024 WekaSafe Solutions. All rights reserved.