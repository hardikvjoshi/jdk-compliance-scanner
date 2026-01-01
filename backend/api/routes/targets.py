"""
Targets API routes - For managing Unix/Cloud scan targets
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel, Field, field_serializer
from sqlalchemy.orm import Session
import json

from core.database import get_db
from core.database.models import Target, DeploymentType, User
from core.database.encryption import get_encryption_manager
from auth.middleware import get_current_active_user, require_role

router = APIRouter(prefix="/api/targets", tags=["targets"])


class TargetCreate(BaseModel):
    """Target creation request"""
    name: str = Field(..., description="Target name/hostname")
    deployment_type: str = Field(..., description="Deployment type: Unix, Cloud, etc.")
    hostname: Optional[str] = Field(None, description="Hostname or IP address")
    ip_address: Optional[str] = Field(None, description="IP address")
    connection_config: dict = Field(..., description="Connection configuration (credentials, keys, etc.)")
    project_id: Optional[int] = Field(None, description="Associated project ID (for OpenShift)")
    cluster_id: Optional[int] = Field(None, description="Associated cluster ID")
    tier: str = Field(..., description="Environment tier: Dev, UAT, Production")


class TargetUpdate(BaseModel):
    """Target update request"""
    name: Optional[str] = None
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    connection_config: Optional[dict] = None
    tier: Optional[str] = None
    status: Optional[str] = None


class TargetResponse(BaseModel):
    id: int
    name: str
    deployment_type: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    tier: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        return dt.isoformat() if dt else ""
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[TargetResponse])
async def list_targets(
    deployment_type: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all targets with optional filters"""
    query = db.query(Target)
    
    if deployment_type:
        try:
            dep_type = DeploymentType(deployment_type)
            query = query.filter(Target.deployment_type == dep_type)
        except ValueError:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid deployment_type: {deployment_type}"
            )
    
    if status:
        query = query.filter(Target.status == status)
    if tier:
        query = query.filter(Target.tier == tier)
    if status:
        query = query.filter(Target.status == status)
    
    targets = query.all()
    return targets


@router.post("", response_model=TargetResponse, status_code=http_status.HTTP_201_CREATED)
async def create_target(
    target_data: TargetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Create a new scan target (Administrator only)"""
    # Validate deployment type
    try:
        dep_type = DeploymentType(target_data.deployment_type)
    except ValueError:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid deployment_type: {target_data.deployment_type}. Valid types: {[e.value for e in DeploymentType]}"
        )
    
    # Validate tier
    valid_tiers = ["Dev", "UAT", "Production"]
    if target_data.tier not in valid_tiers:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Tier must be one of: {', '.join(valid_tiers)}"
        )
    
    # Encrypt connection config
    encryptor = get_encryption_manager()
    encrypted_config = encryptor.encrypt(json.dumps(target_data.connection_config))
    
    # Create target
    target = Target(
        name=target_data.name,
        deployment_type=dep_type,
        hostname=target_data.hostname,
        ip_address=target_data.ip_address,
        connection_config=encrypted_config,
        project_id=target_data.project_id,
        cluster_id=target_data.cluster_id,
        tier=target_data.tier,
        status="Active",
        created_by=current_user.id
    )
    
    db.add(target)
    db.commit()
    db.refresh(target)
    
    return target


@router.get("/{target_id}", response_model=TargetResponse)
async def get_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get target details"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    return target


@router.put("/{target_id}", response_model=TargetResponse)
async def update_target(
    target_id: int,
    target_data: TargetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update target (Administrator only)"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    if target_data.name is not None:
        target.name = target_data.name
    if target_data.hostname is not None:
        target.hostname = target_data.hostname
    if target_data.ip_address is not None:
        target.ip_address = target_data.ip_address
    if target_data.connection_config is not None:
        encryptor = get_encryption_manager()
        target.connection_config = encryptor.encrypt(json.dumps(target_data.connection_config))
    if target_data.tier is not None:
        valid_tiers = ["Dev", "UAT", "Production"]
        if target_data.tier not in valid_tiers:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Tier must be one of: {', '.join(valid_tiers)}"
            )
        target.tier = target_data.tier
    if target_data.status is not None:
        target.status = target_data.status
    
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{target_id}", status_code=http_status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Delete target (Administrator only)"""
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    db.delete(target)
    db.commit()
    return None

