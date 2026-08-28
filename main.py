# main.py - Enhanced Version with Security & Complete Dashboard
import os
import datetime as dt
from datetime import datetime, timezone, timedelta
import csv
import io
from typing import List
from fastapi import FastAPI, Request, UploadFile, Form, File, HTTPException, Depends, Response, status
from fastapi.responses import RedirectResponse, HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import secrets

from database import Base, engine, SessionLocal
from models import Quote, Incident, User
from schemas import QuoteSchema, QuoteOut, IncidentOut, Token
from utils import generate_reference_id, hash_password, verify_password, send_email
from auth import create_access_token, get_current_user, require_role
import aiofiles

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "documents")
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

app = FastAPI(title="WekaSafe Admin System", version="2.0.0")

# Security: Session middleware with secure secret
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_urlsafe(32))
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=3600)

# Mount static & uploads
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/documents", StaticFiles(directory=DOCUMENTS_DIR), name="documents")

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# CORS - driven by ALLOWED_ORIGINS in .env (comma-separated). Falls back to "*"
# for local development only (note: "*" cannot be combined with credentials by
# browsers, so set ALLOWED_ORIGINS explicitly in production).
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base URL used in outgoing email links (set to your live domain in .env)
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

# Whether cookies require HTTPS - set SECURE_COOKIES=true in .env once the
# site is served over HTTPS (required for production)
SECURE_COOKIES = os.getenv("SECURE_COOKIES", "false").lower() == "true"

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ Security Helper Functions ============

def sanitize_input(text: str) -> str:
    """Basic XSS prevention"""
    if not text:
        return ""
    return text.replace("<", "&lt;").replace(">", "&gt;")

def get_eat_time():
    """Get current time in East African Time (EAT - UTC+3)"""
    utc_now = datetime.now(timezone.utc)
    eat_offset = timedelta(hours=3)
    eat_time = utc_now + eat_offset
    return eat_time.replace(tzinfo=None)  # Return naive datetime for database compatibility

def get_user_from_cookie(request: Request, db: Session = Depends(get_db)):
    """Extract user from JWT cookie"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    from jose import JWTError, jwt
    from auth import SECRET_KEY, ALGORITHM
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        user = db.query(User).filter(User.email == email).first()
        return user
    except JWTError:
        return None

# ============ Public API Endpoints ============

@app.post("/api/submit-quote")
def submit_quote(payload: QuoteSchema, db: Session = Depends(get_db)):
    """Handle quote submission with email confirmation"""
    # Sanitize inputs
    quote = Quote(
        name=sanitize_input(payload.name),
        email=payload.email.lower(),
        phone=sanitize_input(payload.phone),
        service=sanitize_input(payload.service),
        message=sanitize_input(payload.message) if payload.message else None
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    
    # Send confirmation email to customer
    try:
        customer_subject = "Quote Request Received - WekaSafe Solutions"
        customer_body = f"""Dear {payload.name},

Thank you for your interest in WekaSafe Solutions!

We have received your quote request for: {payload.service}

Our team will review your requirements and contact you within 24 hours (business days).

Request Details:
- Service: {payload.service}
- Contact: {payload.phone}
- Email: {payload.email}
- Reference ID: QT-{quote.id:06d}

If you have any urgent questions, please call us at +256 394 823 579.

Best regards,
WekaSafe Solutions Team
Safety & Compliance Made Simple

---
This is an automated confirmation. Please do not reply to this email.
Visit: {BASE_URL}
"""
        if not send_email(payload.email, customer_subject, customer_body):
            print(f"Failed to send customer email to {payload.email} (see Email error above)")
    except Exception as e:
        print(f"Failed to send customer email: {e}")
    
    # Send notification to admin
    try:
        admin_subject = f"[NEW QUOTE] {payload.service}"
        admin_body = f"""New Quote Request Received

Reference ID: QT-{quote.id:06d}

Name: {payload.name}
Email: {payload.email}
Phone: {payload.phone}
Service: {payload.service}

Message:
{payload.message or 'No message provided'}

View in admin panel: {BASE_URL}/admin/dashboard

---
Quote ID: {quote.id}
Submitted: {quote.timestamp}
"""
        admin_email = os.getenv("ADMIN_EMAIL", "wekasafesolutions@gmail.com")
        if not send_email(admin_email, admin_subject, admin_body):
            print(f"Failed to send admin email to {admin_email} (see Email error above)")
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
    
    return {"success": True, "id": quote.id, "reference": f"QT-{quote.id:06d}"}

@app.post("/api/incident-report")
async def incident_report(
    reporter_name: str = Form(""),
    contact: str = Form(""),
    datetime_field: str = Form(""),
    location: str = Form(""),
    incident_type: str = Form(""),
    severity: str = Form(""),
    description: str = Form(""),
    files: List[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Handle incident report with file uploads and email notifications"""
    reference_id = generate_reference_id()
    saved_files = []
    
    # Handle file uploads securely
    if files:
        for f in files:
            if f.filename:
                # Security: Validate file extensions
                allowed_extensions = {'.jpg', '.jpeg', '.png', '.pdf', '.doc', '.docx', '.txt'}
                file_ext = os.path.splitext(f.filename)[1].lower()
                
                if file_ext not in allowed_extensions:
                    raise HTTPException(status_code=400, detail=f"File type {file_ext} not allowed")
                
                # Security: Limit file size (10MB)
                content = await f.read()
                if len(content) > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
                
                safe_filename = f"{reference_id}_{os.path.basename(f.filename)}"
                path = os.path.join(UPLOAD_DIR, safe_filename)
                saved_files.append(safe_filename)
                
                async with aiofiles.open(path, "wb") as out:
                    await out.write(content)
    
    # Create incident record
    inc = Incident(
        reference=reference_id,
        reporter_name=sanitize_input(reporter_name),
        contact=sanitize_input(contact),
        datetime=datetime_field,
        location=sanitize_input(location),
        incident_type=sanitize_input(incident_type),
        severity=severity,
        description=sanitize_input(description),
        attachments=";".join(saved_files) if saved_files else None
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    
    # Send confirmation email to reporter
    if contact and "@" in contact:
        try:
            reporter_subject = f"Incident Report Confirmation - Ref: {reference_id}"
            reporter_body = f"""Dear {reporter_name or 'Reporter'},

Thank you for submitting an incident report to WekaSafe Solutions.

Your report has been received and logged securely.

REFERENCE NUMBER: {reference_id}
Please save this reference number for tracking purposes.

Report Details:
- Date/Time: {datetime_field}
- Location: {location}
- Type: {incident_type}
- Severity: {severity}
- Attachments: {len(saved_files)} file(s)

Our safety team will investigate this incident and take appropriate action. 
If immediate action is required, please contact us at +256 394 823 579S.

All incident reports are treated as confidential and handled in accordance 
with our privacy policy.

Best regards,
WekaSafe Solutions Safety Team

---
This is an automated confirmation. Please do not reply to this email.
"""
            if not send_email(contact, reporter_subject, reporter_body):
                print(f"Failed to send reporter confirmation to {contact} (see Email error above)")
        except Exception as e:
            print(f"Failed to send reporter confirmation: {e}")
    
    # Send notification to admin
    try:
        severity_prefix = {"Critical": "[CRITICAL]", "High": "[HIGH]", "Medium": "[MEDIUM]", "Low": "[LOW]"}.get(severity, "[INCIDENT]")
        admin_subject = f"{severity_prefix} New Incident Report: {incident_type}"
        admin_body = f"""NEW INCIDENT REPORT RECEIVED

Reference: {reference_id}
Severity: {severity}
Type: {incident_type}

Reporter: {reporter_name or 'Anonymous'}
Contact: {contact or 'Not provided'}
Date/Time: {datetime_field}
Location: {location}

Description:
{description}

Attachments: {len(saved_files) if saved_files else 0} file(s)
{chr(10).join(['- ' + f for f in saved_files]) if saved_files else ''}

View details: {BASE_URL}/admin/dashboard

---
Incident ID: {inc.id}
Submitted: {inc.timestamp}
"""
        admin_email = os.getenv("ADMIN_EMAIL", "wekasafesolutions@gmail.com")
        if not send_email(admin_email, admin_subject, admin_body):
            print(f"Failed to send admin email to {admin_email} (see Email error above)")
    except Exception as e:
        print(f"Failed to send admin notification: {e}")
    
    return {"success": True, "reference": reference_id}

# ============ Admin Authentication ============

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request, error: str = None):
    """Display login page"""
    return templates.TemplateResponse(request, "login.html", {
        "error": error
    })

@app.post("/admin/login")
def admin_login(
    request: Request, 
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    """Handle login with rate limiting"""
    # Security: Basic rate limiting (implement Redis in production)
    user = db.query(User).filter(User.email == email.lower()).first()
    
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(request, "login.html", {
            "error": "Invalid email or password"
        }, status_code=401)
    
    # Create JWT token
    token = create_access_token({"sub": user.email, "role": user.role})
    
    response = RedirectResponse(url="/admin/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=SECURE_COOKIES,  # True in production once served over HTTPS
        samesite="lax",
        max_age=60*60*24  # 24 hours
    )
    
    return response

@app.get("/admin/logout")
def admin_logout():
    """Handle logout"""
    resp = RedirectResponse(url="/admin/login")
    resp.delete_cookie("access_token")
    return resp

# ============ Admin Dashboard ============

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Main admin dashboard with statistics"""
    user = get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")
    
    # Gather statistics
    total_quotes = db.query(Quote).count()
    total_incidents = db.query(Incident).count()
    pending_incidents = db.query(Incident).filter(Incident.resolved == False).count()
    resolved_incidents = db.query(Incident).filter(Incident.resolved == True).count()
    
    # Recent activity
    recent_quotes = db.query(Quote).order_by(Quote.timestamp.desc()).limit(5).all()
    recent_incidents = db.query(Incident).order_by(Incident.timestamp.desc()).limit(8).all()
    
    # Severity breakdown
    severity_stats = {}
    for inc in db.query(Incident).all():
        sev = inc.severity or "Unknown"
        severity_stats[sev] = severity_stats.get(sev, 0) + 1
    
    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "total_quotes": total_quotes,
        "total_incidents": total_incidents,
        "pending_incidents": pending_incidents,
        "resolved_incidents": resolved_incidents,
        "recent_quotes": recent_quotes,
        "recent_incidents": recent_incidents,
        "severity_stats": severity_stats
    })

@app.get("/admin/quotes", response_class=HTMLResponse)
def admin_quotes_page(request: Request, db: Session = Depends(get_db)):
    """View all quotes"""
    user = get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")
    
    quotes = db.query(Quote).order_by(Quote.timestamp.desc()).all()
    
    return templates.TemplateResponse(request, "quotes.html", {
        "user": user,
        "quotes": quotes
    })

@app.get("/admin/incidents", response_class=HTMLResponse)
def admin_incidents_page(request: Request, db: Session = Depends(get_db)):
    """View all incidents"""
    user = get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")
    
    incidents = db.query(Incident).order_by(Incident.timestamp.desc()).all()
    
    return templates.TemplateResponse(request, "incidents.html", {
        "user": user,
        "incidents": incidents
    })

@app.get("/admin/incident/{incident_id}", response_class=HTMLResponse)
def admin_incident_detail(request: Request, incident_id: int, db: Session = Depends(get_db)):
    """View incident details"""
    user = get_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/admin/login")
    
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return templates.TemplateResponse(request, "incident_detail.html", {
        "user": user,
        "incident": incident
    })

# ============ Admin API Endpoints ============

@app.get("/api/admin/quotes", response_model=List[QuoteOut])
def api_admin_list_quotes(user: User = Depends(require_role("viewer")), db: Session = Depends(get_db)):
    """API: List all quotes"""
    return db.query(Quote).order_by(Quote.id.desc()).all()

@app.get("/api/admin/incidents")
def api_admin_list_incidents(user: User = Depends(require_role("viewer")), db: Session = Depends(get_db)):
    """API: List all incidents"""
    rows = db.query(Incident).order_by(Incident.id.desc()).all()
    return [{
        "id": r.id,
        "reference": r.reference,
        "reporter_name": r.reporter_name,
        "contact": r.contact,
        "datetime": r.datetime,
        "location": r.location,
        "incident_type": r.incident_type,
        "severity": r.severity,
        "description": r.description,
        "attachments": (r.attachments or "").split(";") if r.attachments else [],
        "resolved": bool(r.resolved),
        "resolved_at": r.resolved_at,
        "timestamp": r.timestamp
    } for r in rows]

@app.post("/api/admin/incidents/{incident_id}/resolve")
def api_admin_resolve_incident(
    incident_id: int,
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    """API: Mark incident as resolved"""
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    if inc.resolved:
        return {"success": True, "message": "Already resolved"}
    
    inc.resolved = True
    inc.resolved_at = get_eat_time()
    db.commit()
    db.refresh(inc)
    
    return {"success": True, "resolved_at": inc.resolved_at}

@app.get("/api/admin/stats")
def api_admin_stats(user: User = Depends(require_role("viewer")), db: Session = Depends(get_db)):
    """API: Get dashboard statistics"""
    total_quotes = db.query(Quote).count()
    total_incidents = db.query(Incident).count()
    
    by_severity = {}
    for i in db.query(Incident).all():
        by_severity[i.severity or "Unknown"] = by_severity.get(i.severity or "Unknown", 0) + 1
    
    recent_incidents = [
        {
            "reference": r.reference,
            "severity": r.severity,
            "timestamp": r.timestamp
        }
        for r in db.query(Incident).order_by(Incident.timestamp.desc()).limit(10).all()
    ]
    
    return {
        "total_quotes": total_quotes,
        "total_incidents": total_incidents,
        "by_severity": by_severity,
        "recent_incidents": recent_incidents
    }

# ============ Admin Setup & Management ============

@app.get("/admin/setup", response_class=HTMLResponse)
def setup_page(request: Request, db: Session = Depends(get_db)):
    """One-time setup page - displays form if no users exist"""
    try:
        existing_user = db.query(User).first()
        if existing_user:
            # If users already exist, redirect to login
            return RedirectResponse(url="/admin/login", status_code=303)
    except Exception as e:
        # If database doesn't exist or table doesn't exist, show setup page
        print(f"Database error (expected on first run): {e}")
    
    # Serve the setup form
    return templates.TemplateResponse(request, "setup.html", {})

@app.post("/admin/setup")
def setup_create_admin(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Create first admin user"""
    try:
        existing_user = db.query(User).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Setup disabled: Users already exist. Please ask an admin to create your account."
            )
    except HTTPException:
        raise
    except Exception as e:
        # If table doesn't exist, it will be created by the next operation
        print(f"Database check error (expected on first setup): {e}")
    
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    
    try:
        hashed = hash_password(password)
        user = User(
            email=email.lower(),
            hashed_password=hashed,
            role="admin",
            reset_count=0
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "Admin account created successfully! You may now login.",
            "login_url": "/admin/login"
        }
    except Exception as e:
        db.rollback()
        print(f"User creation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create admin account. Please check server logs. Error: {str(e)}"
        )

@app.post("/admin/reset")
def reset_admin_password(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """Reset admin password (limited to 3 times)"""
    user = db.query(User).filter(User.email == email.lower(), User.role == "admin").first()
    
    if not user:
        raise HTTPException(status_code=404, detail="No admin account found with that email.")
    
    if user.reset_count >= 3:
        raise HTTPException(
            status_code=403,
            detail="Admin reset limit reached (3 times). Contact system administrator."
        )
    
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    
    user.hashed_password = hash_password(password)
    user.reset_count += 1
    db.commit()
    
    return {
        "success": True,
        "message": "Admin password reset successful",
        "resets_used": user.reset_count,
        "resets_remaining": 3 - user.reset_count
    }

# ============ Export Functions ============

@app.get("/admin/export/quotes")
def export_quotes(request: Request, db: Session = Depends(get_db)):
    """Export quotes to CSV"""
    # Check authentication using cookie
    user = get_user_from_cookie(request, db)
    if not user or user.role not in ["admin", "viewer"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    quotes = db.query(Quote).order_by(Quote.timestamp.desc()).all()

    # Use proper CSV writer to handle commas and special characters
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    # Write header
    writer.writerow(['ID', 'Reference', 'Name', 'Email', 'Phone', 'Service', 'Message', 'Timestamp'])
    
    # Write data
    for q in quotes:
        writer.writerow([
            q.id,
            f"QT-{q.id:06d}",
            q.name,
            q.email,
            q.phone,
            q.service,
            q.message or '',
            q.timestamp.strftime('%Y-%m-%d %H:%M:%S') if q.timestamp else ''
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=quotes_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.get("/admin/export/incidents")
def export_incidents(request: Request, db: Session = Depends(get_db)):
    """Export incidents to CSV"""
    # Check authentication using cookie
    user = get_user_from_cookie(request, db)
    if not user or user.role not in ["admin", "viewer"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    incidents = db.query(Incident).order_by(Incident.timestamp.desc()).all()
    
    # Use proper CSV writer to handle commas and special characters
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)
    
    # Write header
    writer.writerow([
        'ID', 'Reference', 'Reporter', 'Contact', 'Date/Time of Incident', 
        'Location', 'Type', 'Severity', 'Description', 'Attachments', 
        'Resolved', 'Resolved At', 'Submitted At'
    ])
    
    # Write data
    for inc in incidents:
        writer.writerow([
            inc.id,
            inc.reference,
            inc.reporter_name or 'Anonymous',
            inc.contact or '',
            inc.datetime or '',
            inc.location,
            inc.incident_type or '',
            inc.severity or '',
            inc.description or '',
            inc.attachments or '',
            'Yes' if inc.resolved else 'No',
            inc.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if inc.resolved_at else '',
            inc.timestamp.strftime('%Y-%m-%d %H:%M:%S') if inc.timestamp else ''
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=incidents_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

# Root route - serves the public marketing site (index.html)
@app.get("/", response_class=HTMLResponse)
def home_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

# Dynamic route - serves other public HTML pages (equipment, environmental, training, etc.)
@app.get("/{page}.html", response_class=HTMLResponse)
def serve_page(request: Request, page: str):
    """Serve any HTML page from the templates folder"""
    try:
        return templates.TemplateResponse(request, f"{page}.html", {})
    except Exception:
        raise HTTPException(status_code=404, detail=f"Page '{page}.html' not found")

# Health check
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": get_eat_time()}