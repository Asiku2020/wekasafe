# utils.py - Fixed for Python 3.14
import os
import uuid
import socket
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import hashlib
import secrets

load_dotenv()

def _resolve_ipv4(hostname: str) -> str:
    """
    Resolve a hostname to its IPv4 address only.
    Some hosts (e.g. Railway) can't route outbound IPv6, which causes
    '[Errno 101] Network is unreachable' when smtplib picks an IPv6
    address for a host like smtp.gmail.com that has both A and AAAA
    records. Connecting to the resolved IPv4 address sidesteps that.
    """
    infos = socket.getaddrinfo(hostname, None, socket.AF_INET)
    return infos[0][4][0]

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
    Sends an email using SMTP settings from environment variables.
    Returns True if successful, False otherwise.
    """
    host = os.getenv("MAIL_HOST")
    if not host:
        print("Email error: MAIL_HOST is not set - email not sent")
        return False
    
    try:
        port = int(os.getenv("MAIL_PORT", 587))
        user = os.getenv("MAIL_USERNAME")
        password = os.getenv("MAIL_PASSWORD")
        from_email = os.getenv("MAIL_FROM", user)
        
        msg = EmailMessage()
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        
        try:
            connect_host = _resolve_ipv4(host)
        except Exception:
            # Fall back to the original hostname if IPv4 resolution fails
            connect_host = host

        with smtplib.SMTP(timeout=15) as smtp:
            smtp.connect(connect_host, port)
            # Keep the real hostname on the SMTP object so starttls()
            # uses it (not the IP) for the TLS/SNI hostname check -
            # otherwise certificate verification against smtp.gmail.com
            # would fail when connecting via a raw IP.
            smtp._host = host
            smtp.ehlo(host)
            smtp.starttls()
            smtp.ehlo(host)
            smtp.login(user, password)
            smtp.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False