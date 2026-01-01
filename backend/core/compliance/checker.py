"""
Compliance checker - validates JDK versions against database
"""
from typing import Optional, Dict
from sqlalchemy.orm import Session

from core.database.models import JDKVersion, ComplianceStatus, Exemption, ExemptionStatus
from core.compliance.jdk_detector import JDKDetector


class ComplianceChecker:
    """Checks JDK version compliance against database"""
    
    def __init__(self, db: Session):
        """
        Initialize compliance checker
        
        Args:
            db: Database session
        """
        self.db = db
        self.detector = JDKDetector()
    
    def check_compliance(
        self,
        detected_version: Optional[str],
        detected_vendor: Optional[str],
        project_id: int,
        application_name: str
    ) -> Dict[str, any]:
        """
        Check if detected JDK version is compliant
        
        Args:
            detected_version: Detected JDK major version (e.g., "17")
            detected_vendor: Detected JDK vendor (e.g., "Zulu")
            project_id: Project ID
            application_name: Application name to check for exemptions
            
        Returns:
            Dictionary with compliance status and details
        """
        # Check if Java was found
        if not detected_version:
            return {
                "status": ComplianceStatus.NOT_FOUND.value,
                "compliant": False,
                "reason": "Java not found"
            }
        
        # Check for exemptions first
        exemption = self._check_exemption(project_id, application_name, detected_version)
        if exemption:
            return {
                "status": ComplianceStatus.EXEMPTED.value,
                "compliant": True,
                "reason": f"Exempted: {exemption.exemption_reason}",
                "exemption_id": exemption.id
            }
        
        # Check JDK version against compliant versions
        try:
            major_version = int(detected_version)
        except (ValueError, TypeError):
            return {
                "status": ComplianceStatus.NOT_FOUND.value,
                "compliant": False,
                "reason": f"Invalid version format: {detected_version}"
            }
        
        # Find JDK version in database
        jdk_version = self.db.query(JDKVersion).filter(
            JDKVersion.major_version == major_version,
            JDKVersion.is_active == True
        ).first()
        
        if not jdk_version:
            return {
                "status": ComplianceStatus.NOT_FOUND.value,
                "compliant": False,
                "reason": f"JDK version {major_version} not in database"
            }
        
        # Check compliance status
        if jdk_version.compliance_status == "Compliant":
            return {
                "status": ComplianceStatus.COMPLIANT.value,
                "compliant": True,
                "reason": f"JDK {major_version} ({jdk_version.vendor}) is compliant",
                "jdk_version_id": jdk_version.id
            }
        elif jdk_version.compliance_status == "CompliantStar":
            return {
                "status": ComplianceStatus.COMPLIANT_STAR.value,
                "compliant": True,
                "reason": f"JDK {major_version} ({jdk_version.vendor}) is compliant*",
                "jdk_version_id": jdk_version.id
            }
        else:  # Non-Compliant
            return {
                "status": ComplianceStatus.NON_COMPLIANT.value,
                "compliant": False,
                "reason": f"JDK {major_version} ({jdk_version.vendor}) is non-compliant",
                "jdk_version_id": jdk_version.id
            }
    
    def _check_exemption(
        self,
        project_id: int,
        application_name: str,
        jdk_version: str
    ) -> Optional[Exemption]:
        """
        Check if there's an active exemption for this application/version
        
        Args:
            project_id: Project ID
            application_name: Application name
            jdk_version: JDK version string
            
        Returns:
            Exemption object if found, None otherwise
        """
        from datetime import date
        
        try:
            major_version = int(jdk_version)
        except (ValueError, TypeError):
            return None
        
        # Find JDK version ID
        jdk_version_obj = self.db.query(JDKVersion).filter(
            JDKVersion.major_version == major_version
        ).first()
        
        if not jdk_version_obj:
            return None
        
        # Check for active exemption
        exemption = self.db.query(Exemption).filter(
            Exemption.project_id == project_id,
            Exemption.application_name == application_name,
            Exemption.jdk_version_id == jdk_version_obj.id,
            Exemption.exemption_status == ExemptionStatus.ACTIVE
        ).first()
        
        if exemption:
            # Check if exemption is expired (for temporary exemptions)
            if exemption.end_date and exemption.end_date < date.today():
                return None
        
        return exemption

