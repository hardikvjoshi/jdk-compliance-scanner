"""
Cloud Scanner - Base/routing class for cloud provider scanners
Supports AWS, Azure, GCP
"""
from typing import Dict, Any, Optional

from core.scanner.base import BaseScanner, ScanResult


class CloudScanner(BaseScanner):
    """
    Cloud scanner that routes to provider-specific implementations
    Supports AWS, Azure, GCP
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize cloud scanner
        
        Args:
            config_dict: Configuration containing:
                - provider: Cloud provider ("aws", "azure", "gcp")
                - credentials: Provider-specific credentials (encrypted)
                - region: Cloud region
                - Additional provider-specific config
        """
        super().__init__(config_dict)
        self.provider = config_dict.get("provider", "").lower()
        self.scanner: Optional[BaseScanner] = None
        
        # Route to provider-specific scanner
        if self.provider == "aws":
            try:
                from core.scanner.cloud.aws_scanner import AWSScanner
                self.scanner = AWSScanner(config_dict)
            except ImportError:
                raise ValueError("AWS scanner not available. Install boto3.")
        elif self.provider == "azure":
            try:
                from core.scanner.cloud.azure_scanner import AzureScanner
                self.scanner = AzureScanner(config_dict)
            except ImportError:
                raise ValueError("Azure scanner not available. Install azure-* packages.")
        elif self.provider == "gcp":
            try:
                from core.scanner.cloud.gcp_scanner import GCPScanner
                self.scanner = GCPScanner(config_dict)
            except ImportError:
                raise ValueError("GCP scanner not available. Install google-cloud-* packages.")
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}. Supported: aws, azure, gcp")
    
    def connect(self) -> bool:
        """Establish connection - delegate to provider scanner"""
        if not self.scanner:
            return False
        return self.scanner.connect()
    
    def disconnect(self):
        """Close connection - delegate to provider scanner"""
        if self.scanner:
            self.scanner.disconnect()
        self.connected = False
    
    def execute_command(self, command: str) -> tuple:
        """Execute command - delegate to provider scanner"""
        if not self.scanner:
            raise RuntimeError("No scanner initialized")
        return self.scanner.execute_command(command)
    
    def scan(self, target: Dict[str, Any]) -> ScanResult:
        """Scan target - delegate to provider scanner"""
        if not self.scanner:
            return ScanResult(
                success=False,
                error_message="No scanner initialized"
            )
        return self.scanner.scan(target)

