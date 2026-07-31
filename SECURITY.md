# WekaSafe Backend - Security Implementation

## 🔒 Security Features Already Implemented

### ✅ Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **httpOnly Cookies**: Prevents XSS attacks on tokens
- **Role-Based Access Control**: Admin and Viewer roles
- **Bcrypt Password Hashing**: Industry-standard password security
- **Password Length Requirement**: Minimum 8 characters
- **Reset Limit**: Max 3 password resets per account

### ✅ Input Validation & Sanitization
- **XSS Prevention**: All user inputs sanitized before storage
- **Email Validation**: Using Pydantic EmailStr validation
- **Type Checking**: Pydantic models enforce data types
- **SQLAlchemy ORM**: Prevents SQL injection
- **Character Escaping**: HTML entities escaped in outputs

### ✅ File Upload Security
- **Type Whitelist**: Only safe file types allowed (`.jpg`, `.jpeg`, `.png`, `.pdf`, `.doc`, `.docx`, `.txt`)
- **Size Limits**: 10MB maximum per file
- **Secure Filenames**: Reference ID prefix + sanitized names
- **Isolated Directory**: Files stored in separate uploads folder
- **Content Validation**: File content checked, not just extension

### ✅ Session Security
- **Session Middleware**: Secure session management
- **Cookie Security Flags**: httpOnly, secure (production), samesite
- **Token Expiration**: 24-hour token lifetime
- **Logout Functionality**: Proper session cleanup

### ✅ API Security
- **CORS Configuration**: Controlled cross-origin requests
- **Endpoint Protection**: Public vs authenticated routes
- **Method Restrictions**: Appropriate HTTP methods only
- **Error Handling**: No sensitive data in error messages

---

## 🔐 Additional Security Recommendations

### For Production Deployment

#### 1. HTTPS/SSL (CRITICAL)
```python
# In production, enforce HTTPS
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(
        HTTPSRedirectMiddleware
    )
```

Update cookies for HTTPS:
```python
response.set_cookie(
    key="access_token",
    value=token,
    httponly=True,
    secure=True,  # Enable in production
    samesite="strict",  # More strict in production
    max_age=60*60*24
)
```

#### 2. Rate Limiting (Redis Implementation)
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Apply to login endpoint
@app.post("/admin/login")
@limiter.limit("5/minute")  # 5 attempts per minute
async def admin_login(request: Request, ...):
    ...
```

#### 3. Content Security Policy (CSP)
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

#### 4. Database Migration (PostgreSQL)
```python
# Replace SQLite with PostgreSQL for production
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/wekasafe"
)

engine = create_engine(DATABASE_URL)
```

#### 5. Environment-Based Configuration
```python
# config.py
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = environment == "development"
    allowed_origins: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    secure_cookies: bool = environment == "production"
    
settings = Settings()
```

#### 6. Logging & Monitoring
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('wekasafe.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Log security events
@app.post("/admin/login")
def admin_login(...):
    if not user:
        logger.warning(f"Failed login attempt for {email} from {request.client.host}")
        ...
    logger.info(f"Successful login: {email}")
```

#### 7. API Key for Public Endpoints (Optional)
```python
# For additional protection on public endpoints
API_KEY = os.getenv("API_KEY")

def verify_api_key(api_key: str = Header(...)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/api/submit-quote")
def submit_quote(
    payload: QuoteSchema,
    api_key: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    ...
```

#### 8. File Scanning (Virus Detection)
```python
# Using ClamAV or similar
import subprocess

def scan_file(file_path: str) -> bool:
    """Scan file for viruses"""
    try:
        result = subprocess.run(
            ['clamscan', file_path],
            capture_output=True,
            timeout=30
        )
        return result.returncode == 0
    except:
        return False

# Use in file upload endpoint
if not scan_file(path):
    raise HTTPException(status_code=400, detail="File rejected by security scan")
```

#### 9. Account Lockout
```python
# Add to User model
class User(Base):
    ...
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

# In login endpoint
if user.locked_until and user.locked_until > datetime.utcnow():
    raise HTTPException(status_code=403, detail="Account locked. Try again later.")

if not verify_password(password, user.hashed_password):
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    db.commit()
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Reset on successful login
user.failed_login_attempts = 0
user.locked_until = None
db.commit()
```

#### 10. Two-Factor Authentication (2FA)
```python
import pyotp

class User(Base):
    ...
    otp_secret = Column(String, nullable=True)
    two_fa_enabled = Column(Boolean, default=False)

@app.post("/admin/enable-2fa")
def enable_2fa(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = pyotp.random_base32()
    user.otp_secret = secret
    user.two_fa_enabled = True
    db.commit()
    
    totp = pyotp.TOTP(secret)
    qr_uri = totp.provisioning_uri(user.email, issuer_name="WekaSafe")
    return {"qr_uri": qr_uri, "secret": secret}

@app.post("/admin/verify-2fa")
def verify_2fa(code: str, user: User = Depends(get_current_user)):
    totp = pyotp.TOTP(user.otp_secret)
    if not totp.verify(code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
    return {"success": True}
```

---

## 🛡️ Security Best Practices

### For Administrators

1. **Strong Passwords**
   - Minimum 12 characters
   - Mix of uppercase, lowercase, numbers, symbols
   - No dictionary words
   - Use a password manager

2. **Email Security**
   - Use app-specific passwords (not main password)
   - Enable 2FA on email account
   - Monitor for suspicious activity

3. **Regular Updates**
   - Keep Python and dependencies updated
   - Monitor security advisories
   - Apply patches promptly

4. **Backup Strategy**
   - Daily database backups
   - Store backups securely off-site
   - Test restoration procedures

5. **Access Control**
   - Limit admin accounts to minimum necessary
   - Use Viewer role for read-only access
   - Regular audit of user accounts

### For Developers

1. **Code Security**
   - Never commit secrets to Git
   - Use environment variables
   - Review code for vulnerabilities
   - Keep dependencies updated

2. **Testing**
   - Test authentication flows
   - Verify authorization checks
   - Test input validation
   - Simulate attack scenarios

3. **Monitoring**
   - Log all security events
   - Monitor failed login attempts
   - Track unusual patterns
   - Set up alerts

---

## 🔍 Security Audit Checklist

### Pre-Deployment
- [ ] All default secrets changed
- [ ] Strong admin password set
- [ ] Email configuration tested
- [ ] HTTPS certificate installed
- [ ] Database backed up
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] File upload restrictions tested
- [ ] Error messages don't leak info
- [ ] CORS properly configured

### Post-Deployment
- [ ] Monitor logs daily
- [ ] Test all endpoints
- [ ] Verify HTTPS works
- [ ] Check email notifications
- [ ] Test file uploads
- [ ] Verify authentication
- [ ] Check authorization
- [ ] Test logout functionality
- [ ] Verify session expiration

### Regular Maintenance
- [ ] Review access logs weekly
- [ ] Update dependencies monthly
- [ ] Backup database daily
- [ ] Test restoration quarterly
- [ ] Security audit annually
- [ ] Update SSL certificates before expiry

---

## 🚨 Incident Response

### If Breach Suspected

1. **Immediate Actions**
   - Disconnect affected systems
   - Preserve logs and evidence
   - Change all passwords
   - Revoke all active sessions

2. **Investigation**
   - Review access logs
   - Identify attack vector
   - Assess data exposure
   - Document timeline

3. **Recovery**
   - Patch vulnerabilities
   - Restore from clean backup
   - Strengthen security
   - Monitor for recurrence

4. **Notification**
   - Notify affected users
   - Report to authorities if required
   - Update security policies
   - Conduct post-mortem

---

## 📞 Security Contact

For security issues, please:
1. Do NOT open public issues
2. Contact security team directly
3. Provide detailed information
4. Allow time for patch before disclosure

---

## 📚 Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

---

**Remember: Security is not a one-time setup, it's an ongoing process!**