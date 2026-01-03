"""
Cluster management API routes
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl, ConfigDict, field_serializer
from sqlalchemy.orm import Session

from core.database import get_db
from core.database.models import Cluster, User
from auth.middleware import get_current_active_user, require_role

router = APIRouter(prefix="/api/clusters", tags=["clusters"])


class ClusterCreate(BaseModel):
    cluster_name: str
    console_url: Optional[HttpUrl] = None
    api_url: Optional[HttpUrl] = None
    environment: Optional[str] = None


class ClusterUpdate(BaseModel):
    cluster_name: Optional[str] = None
    console_url: Optional[HttpUrl] = None
    api_url: Optional[HttpUrl] = None
    environment: Optional[str] = None


class ClusterResponse(BaseModel):
    id: int
    cluster_name: str
    console_url: Optional[str] = None
    api_url: Optional[str] = None
    environment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info) -> str:
        return dt.isoformat() if dt else ""
    
    model_config = ConfigDict(from_attributes=True)


@router.get("", response_model=List[ClusterResponse])
async def list_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all clusters"""
    clusters = db.query(Cluster).all()
    return [ClusterResponse.model_validate(cluster) for cluster in clusters]


@router.post("", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
async def create_cluster(
    cluster_data: ClusterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Create a new cluster (Administrator only)"""
    # Check if cluster name already exists
    existing = db.query(Cluster).filter(Cluster.cluster_name == cluster_data.cluster_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cluster with this name already exists"
        )
    
    cluster = Cluster(
        cluster_name=cluster_data.cluster_name,
        console_url=str(cluster_data.console_url) if cluster_data.console_url else None,
        api_url=str(cluster_data.api_url) if cluster_data.api_url else None,
        environment=cluster_data.environment
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    
    return ClusterResponse.model_validate(cluster)


@router.get("/{cluster_id}", response_model=ClusterResponse)
async def get_cluster(
    cluster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get cluster details"""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
    return ClusterResponse.model_validate(cluster)


@router.put("/{cluster_id}", response_model=ClusterResponse)
async def update_cluster(
    cluster_id: int,
    cluster_data: ClusterUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update cluster (Administrator only)"""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
    
    if cluster_data.cluster_name is not None:
        # Check if new name conflicts
        existing = db.query(Cluster).filter(
            Cluster.cluster_name == cluster_data.cluster_name,
            Cluster.id != cluster_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cluster with this name already exists"
            )
        cluster.cluster_name = cluster_data.cluster_name
    
    if cluster_data.console_url is not None:
        cluster.console_url = str(cluster_data.console_url)
    if cluster_data.api_url is not None:
        cluster.api_url = str(cluster_data.api_url)
    if cluster_data.environment is not None:
        cluster.environment = cluster_data.environment
    
    db.commit()
    db.refresh(cluster)
    return ClusterResponse.model_validate(cluster)


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Delete cluster (Administrator only)"""
    cluster = db.query(Cluster).filter(Cluster.id == cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
    
    # Check if cluster has projects
    if cluster.projects:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete cluster with existing projects"
        )
    
    db.delete(cluster)
    db.commit()
    return None

