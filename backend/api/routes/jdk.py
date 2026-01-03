"""
JDK Versions management API routes
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_serializer
from sqlalchemy.orm import Session

from core.database import get_db
from core.database.models import JDKVersion, User
from auth.middleware import get_current_active_user, require_role

router = APIRouter(prefix="/api/jdk-versions", tags=["jdk-versions"])


class JDKVersionCreate(BaseModel):
    major_version: int
    vendor: str
    compliance_status: str  # Compliant, Non-Compliant, CompliantStar
    is_active: bool = True


class JDKVersionUpdate(BaseModel):
    vendor: Optional[str] = None
    compliance_status: Optional[str] = None
    is_active: Optional[bool] = None


class JDKVersionResponse(BaseModel):
    id: int
    major_version: int
    vendor: str
    compliance_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        return dt.isoformat() if dt else ""
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[JDKVersionResponse])
async def list_jdk_versions(
    vendor: Optional[str] = None,
    compliance_status: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List JDK versions with optional filters"""
    query = db.query(JDKVersion)
    
    if vendor:
        query = query.filter(JDKVersion.vendor == vendor)
    if compliance_status:
        query = query.filter(JDKVersion.compliance_status == compliance_status)
    if is_active is not None:
        query = query.filter(JDKVersion.is_active == is_active)
    
    versions = query.all()
    return versions


@router.post("", response_model=JDKVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_jdk_version(
    version_data: JDKVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Add new JDK version (Administrator only)"""
    valid_statuses = ["Compliant", "Non-Compliant", "CompliantStar"]
    if version_data.compliance_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"compliance_status must be one of: {', '.join(valid_statuses)}"
        )
    
    # Check if version+vendor combination already exists
    existing = db.query(JDKVersion).filter(
        JDKVersion.major_version == version_data.major_version,
        JDKVersion.vendor == version_data.vendor
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="JDK version with this major_version and vendor already exists"
        )
    
    jdk_version = JDKVersion(
        major_version=version_data.major_version,
        vendor=version_data.vendor,
        compliance_status=version_data.compliance_status,
        is_active=version_data.is_active
    )
    
    db.add(jdk_version)
    db.commit()
    db.refresh(jdk_version)
    
    return jdk_version


@router.get("/{version_id}", response_model=JDKVersionResponse)
async def get_jdk_version(
    version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get JDK version details"""
    jdk_version = db.query(JDKVersion).filter(JDKVersion.id == version_id).first()
    if not jdk_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JDK version not found"
        )
    return jdk_version


@router.put("/{version_id}", response_model=JDKVersionResponse)
async def update_jdk_version(
    version_id: int,
    version_data: JDKVersionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update JDK version (Administrator only)"""
    jdk_version = db.query(JDKVersion).filter(JDKVersion.id == version_id).first()
    if not jdk_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JDK version not found"
        )
    
    if version_data.vendor is not None:
        jdk_version.vendor = version_data.vendor
    if version_data.compliance_status is not None:
        valid_statuses = ["Compliant", "Non-Compliant", "CompliantStar"]
        if version_data.compliance_status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"compliance_status must be one of: {', '.join(valid_statuses)}"
            )
        jdk_version.compliance_status = version_data.compliance_status
    if version_data.is_active is not None:
        jdk_version.is_active = version_data.is_active
    
    db.commit()
    db.refresh(jdk_version)
    return jdk_version


@router.put("/{version_id}/compliance-status", response_model=JDKVersionResponse)
async def update_compliance_status(
    version_id: int,
    compliance_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update JDK version compliance status (Administrator only)"""
    jdk_version = db.query(JDKVersion).filter(JDKVersion.id == version_id).first()
    if not jdk_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="JDK version not found"
        )
    
    valid_statuses = ["Compliant", "Non-Compliant", "CompliantStar"]
    if compliance_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"compliance_status must be one of: {', '.join(valid_statuses)}"
        )
    
    jdk_version.compliance_status = compliance_status
    db.commit()
    db.refresh(jdk_version)
    return jdk_version

