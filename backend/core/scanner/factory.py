"""
Scanner Factory - Factory pattern for creating scanner instances
Follows Open/Closed Principle (SOLID)
"""
from typing import Dict, Any, Type, Optional
from core.scanner.base import BaseScanner


# Import scanner implementations to register them
def _register_scanners():
    """Register all available scanner implementations"""
    try:
        from core.scanner.openshift_scanner import OpenShiftScanner
        ScannerFactory.register_scanner("openshift", OpenShiftScanner)
    except ImportError:
        pass  # OpenShift scanner not available
    
    try:
        from core.scanner.unix_scanner import UnixScanner
        ScannerFactory.register_scanner("unix", UnixScanner)
    except ImportError:
        pass  # Unix scanner not available
    
    try:
        from core.scanner.cloud_scanner import CloudScanner
        ScannerFactory.register_scanner("cloud", CloudScanner)
    except ImportError:
        pass  # Cloud scanner not available
    
    # Register provider-specific cloud scanners directly
    try:
        from core.scanner.cloud.aws_scanner import AWSScanner
        ScannerFactory.register_scanner("aws", AWSScanner)
    except ImportError:
        pass  # AWS scanner not available
    
    try:
        from core.scanner.cloud.azure_scanner import AzureScanner
        ScannerFactory.register_scanner("azure", AzureScanner)
    except ImportError:
        pass  # Azure scanner not available
    
    try:
        from core.scanner.cloud.gcp_scanner import GCPScanner
        ScannerFactory.register_scanner("gcp", GCPScanner)
    except ImportError:
        pass  # GCP scanner not available


class ScannerFactory:
    """
    Factory for creating scanner instances based on deployment type
    Follows Factory pattern and Open/Closed Principle
    """
    
    _scanner_classes: Dict[str, Type[BaseScanner]] = {}
    
    @classmethod
    def register_scanner(cls, deployment_type: str, scanner_class: Type[BaseScanner]):
        """
        Register a scanner class for a deployment type
        
        Args:
            deployment_type: Type of deployment (e.g., "OpenShift", "UNIX", "Windows")
            scanner_class: Scanner class that extends BaseScanner
        """
        cls._scanner_classes[deployment_type.lower()] = scanner_class
    
    @classmethod
    def create_scanner(cls, deployment_type: str, config: Dict[str, Any]) -> BaseScanner:
        """
        Create a scanner instance for the given deployment type
        
        Args:
            deployment_type: Type of deployment
            config: Scanner configuration
            
        Returns:
            BaseScanner instance
            
        Raises:
            ValueError: If deployment type is not registered
        """
        deployment_type_lower = deployment_type.lower()
        
        if deployment_type_lower not in cls._scanner_classes:
            raise ValueError(
                f"Scanner for deployment type '{deployment_type}' not registered. "
                f"Available types: {list(cls._scanner_classes.keys())}"
            )
        
        scanner_class = cls._scanner_classes[deployment_type_lower]
        return scanner_class(config)
    
    @classmethod
    def get_available_types(cls):
        """Get list of available scanner types"""
        return list(cls._scanner_classes.keys())
    
    @classmethod
    def is_type_supported(cls, deployment_type: str) -> bool:
        """Check if a deployment type is supported"""
        return deployment_type.lower() in cls._scanner_classes


# Register scanners on module import
_register_scanners()

