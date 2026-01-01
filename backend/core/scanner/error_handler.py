"""
Centralized error handler for all scanners (DRY principle)
"""
import logging
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling for scanners"""
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        deployment_type: str = "Unknown"
    ):
        """
        Log error with context information
        
        Args:
            error: Exception that occurred
            context: Context information (target, command, etc.)
            deployment_type: Type of deployment (OpenShift, UNIX, etc.)
        """
        error_details = {
            "timestamp": datetime.utcnow().isoformat(),
            "deployment_type": deployment_type,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        logger.error(
            f"Scanner error in {deployment_type}: {str(error)}",
            extra=error_details
        )
    
    def log_connection_failure(
        self,
        target: str,
        deployment_type: str,
        error: Exception
    ):
        """
        Log connection failure specifically
        
        Args:
            target: Target that failed to connect
            deployment_type: Type of deployment
            error: Connection error
        """
        self.log_error(
            error,
            {"target": target, "operation": "connection"},
            deployment_type
        )
    
    def log_scan_failure(
        self,
        target: str,
        deployment_type: str,
        error: Exception
    ):
        """
        Log scan failure specifically
        
        Args:
            target: Target that failed to scan
            deployment_type: Type of deployment
            error: Scan error
        """
        self.log_error(
            error,
            {"target": target, "operation": "scan"},
            deployment_type
        )

