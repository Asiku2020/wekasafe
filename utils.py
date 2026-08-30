# utils.py - Fixed for Python 3.14
import os
import resend
import uuid
from dotenv import load_dotenv
import hashlib
import secrets


load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

def generate_reference_id() -> str:
    return f"INC-{uuid.uuid4().hex[:10].upper()}"

def hash_password(password: str) -> str:
    """
    Hash password using PBKDF2 (more compatible than bcrypt with Python 3.14)
    """
    # Generate a random salt
    salt = secrets.token_bytes(32)
    
    # Hash the password
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000  # iterations
    )
    
    # Combine salt and hash, encode as hex
    combined = salt + pwd_hash
    return combined.hex()

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a password against its hash
    """
    try:
        # Decode the stored hash
        combined = bytes.fromhex(hashed)
        
        # Extract salt (first 32 bytes) and hash (rest)
        salt = combined[:32]
        stored_hash = combined[32:]
        
        # Hash the provided password with the same salt
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            plain.encode('utf-8'),
            salt,
            100000  # iterations
        )
        
        # Compare hashes
        return pwd_hash == stored_hash
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def send_email(to_email: str, subject: str, body: str):
    """
    Sends an email using the Resend API.
    Returns True if successful, False otherwise.
    """
    if not resend.api_key:
        print("Email error: RESEND_API_KEY is not set - email not sent")
        return False

    from_email = os.getenv("MAIL_FROM") or os.getenv("RESEND_FROM")
    if not from_email:
        print("Email error: MAIL_FROM (or RESEND_FROM) is not set - email not sent")
        return False

    try:
        resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "text": body,
        })
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False