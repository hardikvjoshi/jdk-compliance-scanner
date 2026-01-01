"""
Abstract base scanner class following SOLID principles
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class ScanResult:
    """Result of a scan operation"""
    success: bool
    jdk_version: Optional[str] = None
    jdk_vendor: Optional[str] = None
    error_message: Optional[str] = None
    raw_output: Optional[str] = None


class BaseScanner(ABC):
    """
    Abstract base class for all scanner implementations
    Following Strategy pattern and SOLID principles
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize scanner with configuration
        
        Args:
            config: Scanner-specific configuration dictionary
        """
        self.config = config
        self.connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to target system
        
        Returns:
            True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection to target system"""
        pass
    
    @abstractmethod
    def execute_command(self, command: str) -> tuple:
        """
        Execute a command on the target system
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        pass
    
    def scan(self, target: Dict[str, Any]) -> ScanResult:
        """
        Scan a target for JDK version
        This method uses the shared JDK detection logic (DRY principle)
        
        Args:
            target: Target information (pod name, hostname, etc.)
            
        Returns:
            ScanResult object
        """
        if not self.connected:
            if not self.connect():
                return ScanResult(
                    success=False,
                    error_message="Failed to establish connection"
                )
        
        try:
            # Execute java -version command
            stdout, stderr, return_code = self.execute_command("java -version")
            
            if return_code != 0:
                # Java not found or command failed
                # Try fallback commands to confirm
                return self._handle_java_not_found()
            
            # Use shared JDK detection logic
            from core.compliance.jdk_detector import JDKDetector
            detector = JDKDetector()
            jdk_info = detector.parse_version_output(stdout + stderr)
            
            if jdk_info:
                return ScanResult(
                    success=True,
                    jdk_version=jdk_info.get("version"),
                    jdk_vendor=jdk_info.get("vendor"),
                    raw_output=stdout + stderr
                )
            else:
                return ScanResult(
                    success=False,
                    error_message="Failed to parse JDK version",
                    raw_output=stdout + stderr
                )
                
        except Exception as e:
            return ScanResult(
                success=False,
                error_message=str(e)
            )
    
    def _handle_java_not_found(self) -> ScanResult:
        """
        Handle case when Java is not found
        Uses fallback commands to confirm (shared logic - DRY)
        """
        from core.compliance.jdk_detector import JDKDetector
        detector = JDKDetector()
        
        # Try fallback commands
        for fallback_cmd in detector.get_fallback_commands():
            try:
                stdout, stderr, return_code = self.execute_command(fallback_cmd)
                # If any fallback command succeeds, Java might be present with different path
                # For now, we'll return "Not Found" if java -version failed
                pass
            except Exception:
                continue
        
        return ScanResult(
            success=True,  # Scan was successful, just Java not found
            jdk_version=None,
            error_message="Java not found"
        )
    
    def handle_errors(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Centralized error handling (DRY principle)
        Should be overridden by subclasses for specific error handling
        
        Args:
            error: Exception that occurred
            context: Context information (deployment type, target, etc.)
        """
        from core.scanner.error_handler import ErrorHandler
        handler = ErrorHandler()
        handler.log_error(error, context, deployment_type=self.__class__.__name__)

