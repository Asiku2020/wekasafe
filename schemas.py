# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

class QuoteSchema(BaseModel):
    name: str
    email: EmailStr
    phone: str
    service: str
    message: Optional[str] = None

class PortalLinkRequest(BaseModel):
    email: EmailStr

class QuoteOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    service: str
    message: Optional[str]
    timestamp: datetime.datetime
    class Config:
        from_attributes = True

class IncidentOut(BaseModel):
    id: int
    reference: str
    reporter_name: Optional[str]
    contact: Optional[str]
    datetime: Optional[str]
    location: Optional[str]
    incident_type: Optional[str]
    severity: Optional[str]
    description: Optional[str]
    attachments: Optional[List[str]]
    resolved: bool
    resolved_at: Optional[datetime.datetime]
    timestamp: datetime.datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
