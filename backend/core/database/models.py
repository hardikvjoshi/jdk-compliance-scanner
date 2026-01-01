"""
Database models for JDK Compliance Scanner
"""
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, Integer, String, Text, DateTime, Date, ForeignKey, 
    Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class UserRole(str, enum.Enum):
    ADMINISTRATOR = "Administrator"
    VIEWER = "Viewer"
    OPERATOR = "Operator"


class ComplianceStatus(str, enum.Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    COMPLIANT_STAR = "CompliantStar"
    EXEMPTED = "Exempted"
    NOT_FOUND = "Not Found"


class ExemptionStatus(str, enum.Enum):
    ACTIVE = "Active"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class ExemptionType(str, enum.Enum):
    TEMPORARY = "Temporary"
    PERMANENT = "Permanent"


class ProjectStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    RETIRED = "Retired"


class ScanJobStatus(str, enum.Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class JobType(str, enum.Enum):
    MANUAL = "Manual"
    SCHEDULED = "Scheduled"
    TRIGGERED = "Triggered"


class DeploymentType(str, enum.Enum):
    OPENSHIFT = "OpenShift"
    UNIX = "Unix"
    WINDOWS = "Windows"
    CLOUD = "Cloud"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    onboarded_projects = relationship("Project", back_populates="onboarded_by_user")
    created_exemptions = relationship("Exemption", back_populates="creator")
    initiated_scans = relationship("ScanJob", back_populates="initiator")


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    cluster_name = Column(String(255), unique=True, nullable=False, index=True)
    console_url = Column(String(500), nullable=True)
    api_url = Column(String(500), nullable=True)
    environment = Column(String(50), nullable=True)  # Dev/UAT/Production
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="cluster")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(255), nullable=False, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    technology = Column(String(100), nullable=False)  # Java, Python, Node, Go, Mixed
    tribe = Column(String(255), nullable=False)
    tier = Column(String(50), nullable=False)  # Dev, UAT, Production
    retired = Column(Boolean, default=False, nullable=False)
    cluster_name = Column(String(255), nullable=False)
    console_url = Column(String(500), nullable=False)
    
    # Encrypted credentials
    tech_read_token = Column(Text, nullable=False)  # Encrypted
    tech_edit_credentials = Column(Text, nullable=False)  # Encrypted
    wrapper_cluster_token = Column(Text, nullable=False)  # Encrypted
    
    # Metadata
    onboarded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    onboarded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.ACTIVE, nullable=False)

    # Relationships
    cluster = relationship("Cluster", back_populates="projects")
    onboarded_by_user = relationship("User", back_populates="onboarded_projects")
    exemptions = relationship("Exemption", back_populates="project")
    scan_results = relationship("ScanResult", back_populates="project")


class JDKVersion(Base):
    __tablename__ = "jdk_versions"

    id = Column(Integer, primary_key=True, index=True)
    major_version = Column(Integer, nullable=False, index=True)  # 8, 11, 17, 18, 19, 21, 22
    vendor = Column(String(100), nullable=False)  # Zulu, Oracle, Amazon, etc.
    compliance_status = Column(String(50), nullable=False)  # Compliant, Non-Compliant, CompliantStar
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    exemptions = relationship("Exemption", back_populates="jdk_version")


class Exemption(Base):
    __tablename__ = "exemptions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    application_name = Column(String(255), nullable=False, index=True)
    jdk_version_id = Column(Integer, ForeignKey("jdk_versions.id"), nullable=False)
    exemption_reason = Column(Text, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)  # Null for permanent exemptions
    exemption_status = Column(SQLEnum(ExemptionStatus), default=ExemptionStatus.ACTIVE, nullable=False)
    exemption_type = Column(SQLEnum(ExemptionType), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="exemptions")
    jdk_version = relationship("JDKVersion", back_populates="exemptions")
    creator = relationship("User", back_populates="created_exemptions")


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(String(36), primary_key=True)  # UUID
    job_type = Column(SQLEnum(JobType), nullable=False)
    status = Column(SQLEnum(ScanJobStatus), default=ScanJobStatus.PENDING, nullable=False)
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_targets = Column(Integer, default=0, nullable=False)
    targets_scanned = Column(Integer, default=0, nullable=False)
    targets_failed = Column(Integer, default=0, nullable=False)

    # Relationships
    initiator = relationship("User", back_populates="initiated_scans")
    scan_results = relationship("ScanResult", back_populates="scan_job")


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)  # Nullable for non-OpenShift targets
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=True, index=True)  # For Unix/Cloud targets
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)  # Nullable for non-OpenShift targets
    scan_job_id = Column(String(36), ForeignKey("scan_jobs.id"), nullable=False, index=True)
    application_name = Column(String(255), nullable=False)
    pod_name = Column(String(255), nullable=True)  # For OpenShift pods
    hostname = Column(String(255), nullable=True)  # For Unix/Cloud systems
    deployment_type = Column(SQLEnum(DeploymentType), nullable=True)  # Type of deployment scanned
    detected_jdk_version = Column(String(100), nullable=True)
    detected_jdk_vendor = Column(String(100), nullable=True)
    compliance_status = Column(String(50), nullable=False)
    jdk_found = Column(Boolean, default=False, nullable=False)
    scan_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    error_message = Column(Text, nullable=True)
    raw_output = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scan_results")
    target = relationship("Target", foreign_keys=[target_id])
    scan_job = relationship("ScanJob", back_populates="scan_results")


class Target(Base):
    """Unified table for scan targets (Unix, Cloud, etc.)"""
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Target name/hostname
    deployment_type = Column(SQLEnum(DeploymentType), nullable=False, index=True)
    hostname = Column(String(255), nullable=True)  # For Unix systems
    ip_address = Column(String(50), nullable=True)
    connection_config = Column(Text, nullable=False)  # JSON string with connection details (encrypted)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)  # For OpenShift projects
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=True)
    tier = Column(String(50), nullable=False)  # Dev, UAT, Production
    status = Column(String(50), default="Active", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    cluster = relationship("Cluster", foreign_keys=[cluster_id])


class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)  # JSON string for complex values
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

