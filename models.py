import datetime as dt
from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from database import Base

def get_eat_time():
    """Get current time in East African Time (EAT - UTC+3)"""
    utc_now = datetime.now(timezone.utc)
    eat_offset = timedelta(hours=3)
    eat_time = utc_now + eat_offset
    return eat_time.replace(tzinfo=None)  # Return naive datetime for SQLite compatibility

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="viewer", nullable=False)  # 'admin' or 'viewer'
    created_at = Column(DateTime, default=get_eat_time)  # Changed to EAT
    # Move the reset functionality here
    reset_count = Column(Integer, default=0)

class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    service = Column(String, nullable=False)
    message = Column(Text)
    timestamp = Column(DateTime, default=get_eat_time)  # Changed to EAT

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    reference = Column(String, unique=True, nullable=False)
    reporter_name = Column(String)
    contact = Column(String)
    datetime = Column(String)
    location = Column(String)
    incident_type = Column(String)
    severity = Column(String)
    description = Column(Text)
    attachments = Column(Text)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=get_eat_time)  # Changed to EAT

# Deleted the Admin class to prevent confusion