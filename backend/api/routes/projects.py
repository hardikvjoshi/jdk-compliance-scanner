"""
Project/Namespace onboarding and management API routes
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.database.models import Project, Cluster, User, ProjectStatus
from core.database.encryption import get_encryption_manager
from auth.middleware import get_current_active_user, require_role

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Project onboarding request - all fields required"""
    project_name: str = Field(..., description="Project/Namespace name in OpenShift")
    cluster_id: int = Field(..., description="Cluster ID")
    technology: str = Field(..., description="Technology stack (Java, Python, Node, Go, Mixed)")
    tribe: str = Field(..., description="Organizational tribe/team")
    tier: str = Field(..., description="Environment tier (Dev, UAT, Production)")
    cluster_name: str = Field(..., description="Cluster name")
    console_url: HttpUrl = Field(..., description="OpenShift console URL")
    retired: bool = Field(default=False, description="Whether project is retired")
    tech_read_token: str = Field(..., description="Read-only token for scanning")
    tech_edit_credentials: str = Field(..., description="Edit credentials for write operations")
    wrapper_cluster_token: str = Field(..., description="Wrapper cluster token")


class ProjectUpdate(BaseModel):
    """Project update request - credentials not included"""
    project_name: Optional[str] = None
    technology: Optional[str] = None
    tribe: Optional[str] = None
    tier: Optional[str] = None
    cluster_name: Optional[str] = None
    console_url: Optional[HttpUrl] = None
    retired: Optional[bool] = None
    status: Optional[str] = None


class ProjectCredentialsUpdate(BaseModel):
    """Project credentials update request"""
    tech_read_token: str
    tech_edit_credentials: str
    wrapper_cluster_token: str


class ProjectResponse(BaseModel):
    id: int
    project_name: str
    cluster_id: int
    technology: str
    tribe: str
    tier: str
    cluster_name: str
    console_url: str
    retired: bool
    status: str
    onboarded_at: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    cluster_id: Optional[int] = Query(None),
    tribe: Optional[str] = Query(None),
    technology: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    retired: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List projects with optional filters"""
    query = db.query(Project)
    
    if cluster_id:
        query = query.filter(Project.cluster_id == cluster_id)
    if tribe:
        query = query.filter(Project.tribe == tribe)
    if technology:
        query = query.filter(Project.technology == technology)
    if tier:
        query = query.filter(Project.tier == tier)
    if retired is not None:
        query = query.filter(Project.retired == retired)
    if status:
        query = query.filter(Project.status == status)
    
    projects = query.all()
    return projects


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Onboard a new project/namespace (Administrator only) - all fields required"""
    # Validate cluster exists
    cluster = db.query(Cluster).filter(Cluster.id == project_data.cluster_id).first()
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found"
        )
    
    # Check if project name already exists
    existing = db.query(Project).filter(Project.project_name == project_data.project_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists"
        )
    
    # Validate tier
    valid_tiers = ["Dev", "UAT", "Production"]
    if project_data.tier not in valid_tiers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tier must be one of: {', '.join(valid_tiers)}"
        )
    
    # Encrypt credentials
    encryptor = get_encryption_manager()
    encrypted_read_token = encryptor.encrypt(project_data.tech_read_token)
    encrypted_edit_credentials = encryptor.encrypt(project_data.tech_edit_credentials)
    encrypted_wrapper_token = encryptor.encrypt(project_data.wrapper_cluster_token)
    
    # Create project
    project = Project(
        project_name=project_data.project_name,
        cluster_id=project_data.cluster_id,
        technology=project_data.technology,
        tribe=project_data.tribe,
        tier=project_data.tier,
        cluster_name=project_data.cluster_name,
        console_url=str(project_data.console_url),
        retired=project_data.retired,
        tech_read_token=encrypted_read_token,
        tech_edit_credentials=encrypted_edit_credentials,
        wrapper_cluster_token=encrypted_wrapper_token,
        onboarded_by=current_user.id,
        status=ProjectStatus.ACTIVE
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get project details"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update project (Administrator only) - credentials not updated via this endpoint"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    if project_data.project_name is not None:
        # Check if new name conflicts
        existing = db.query(Project).filter(
            Project.project_name == project_data.project_name,
            Project.id != project_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project with this name already exists"
            )
        project.project_name = project_data.project_name
    
    if project_data.technology is not None:
        project.technology = project_data.technology
    if project_data.tribe is not None:
        project.tribe = project_data.tribe
    if project_data.tier is not None:
        valid_tiers = ["Dev", "UAT", "Production"]
        if project_data.tier not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tier must be one of: {', '.join(valid_tiers)}"
            )
        project.tier = project_data.tier
    if project_data.cluster_name is not None:
        project.cluster_name = project_data.cluster_name
    if project_data.console_url is not None:
        project.console_url = str(project_data.console_url)
    if project_data.retired is not None:
        project.retired = project_data.retired
    if project_data.status is not None:
        try:
            project.status = ProjectStatus(project_data.status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {project_data.status}"
            )
    
    db.commit()
    db.refresh(project)
    return project


@router.put("/{project_id}/credentials", response_model=ProjectResponse)
async def update_project_credentials(
    project_id: int,
    credentials_data: ProjectCredentialsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Update project credentials/tokens (Administrator only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Encrypt credentials
    encryptor = get_encryption_manager()
    project.tech_read_token = encryptor.encrypt(credentials_data.tech_read_token)
    project.tech_edit_credentials = encryptor.encrypt(credentials_data.tech_edit_credentials)
    project.wrapper_cluster_token = encryptor.encrypt(credentials_data.wrapper_cluster_token)
    
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Retire/delete project (Administrator only) - soft delete"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.retired = True
    project.status = ProjectStatus.RETIRED
    db.commit()
    return None


@router.post("/{project_id}/activate", response_model=ProjectResponse)
async def activate_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("Administrator"))
):
    """Reactivate a retired project (Administrator only)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.retired = False
    project.status = ProjectStatus.ACTIVE
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/validation")
async def validate_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Validate project onboarding completeness"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Check all required fields
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    required_fields = {
        "project_name": project.project_name,
        "cluster_id": project.cluster_id,
        "technology": project.technology,
        "tribe": project.tribe,
        "tier": project.tier,
        "cluster_name": project.cluster_name,
        "console_url": project.console_url,
        "tech_read_token": project.tech_read_token,
        "tech_edit_credentials": project.tech_edit_credentials,
        "wrapper_cluster_token": project.wrapper_cluster_token,
    }
    
    for field, value in required_fields.items():
        if not value:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Missing required field: {field}")
    
    # Check cluster exists
    cluster = db.query(Cluster).filter(Cluster.id == project.cluster_id).first()
    if not cluster:
        validation_results["valid"] = False
        validation_results["errors"].append("Referenced cluster does not exist")
    
    return validation_results

