"""
GCP Scanner - Implementation for GCP Compute Engine VMs
"""
import paramiko
from typing import Dict, Any, Optional
from io import StringIO

from core.scanner.base import BaseScanner, ScanResult
from core.database.encryption import get_encryption_manager

try:
    from google.cloud import compute_v1
    from google.oauth2 import service_account
    import json
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


class GCPScanner(BaseScanner):
    """
    Scanner implementation for GCP Compute Engine VMs
    Uses SSH to connect to GCP VMs
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize GCP scanner
        
        Args:
            config_dict: Configuration containing:
                - project_id: GCP project ID
                - zone: GCP zone (e.g., "us-central1-a")
                - instance_name: GCP VM instance name
                - credentials: Service account JSON key (encrypted) or use default credentials
                - username: SSH username (default: based on OS)
                - ssh_key: SSH private key (encrypted)
                - hostname: Optional - if not provided, will query GCP for external IP
                - port: SSH port (default: 22)
                - timeout: Connection timeout (default: 30)
        """
        super().__init__(config_dict)
        
        if not GCP_AVAILABLE:
            raise ImportError("GCP SDK not available. Install google-cloud-compute.")
        
        self.project_id = config_dict.get("project_id")
        self.zone = config_dict.get("zone")
        self.instance_name = config_dict.get("instance_name")
        self.credentials = config_dict.get("credentials", {})
        self.username = config_dict.get("username")
        self.ssh_key = config_dict.get("ssh_key")
        self.hostname = config_dict.get("hostname")
        self.port = config_dict.get("port", 22)
        self.timeout = config_dict.get("timeout", 30)
        
        self.instances_client: Optional[compute_v1.InstancesClient] = None
        self.ssh_client: Optional[paramiko.SSHClient] = None
    
    def _decrypt_value(self, encrypted_value: Optional[str]) -> Optional[str]:
        """Decrypt a value using the encryption manager"""
        if not encrypted_value:
            return None
        
        encryptor = get_encryption_manager()
        try:
            return encryptor.decrypt(encrypted_value)
        except Exception:
            return encrypted_value
    
    def _get_gcp_client(self):
        """Get GCP Compute client"""
        if self.instances_client:
            return self.instances_client
        
        # Decrypt service account key if provided
        service_account_json = self._decrypt_value(self.credentials.get("service_account_json"))
        
        if service_account_json:
            credentials_info = json.loads(service_account_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            self.instances_client = compute_v1.InstancesClient(credentials=credentials)
        else:
            # Use default credentials (Application Default Credentials)
            self.instances_client = compute_v1.InstancesClient()
        
        return self.instances_client
    
    def _get_instance_ip(self) -> Optional[str]:
        """Get external IP address of GCP VM"""
        if self.hostname:
            return self.hostname
        
        try:
            client = self._get_gcp_client()
            instance = client.get(
                project=self.project_id,
                zone=self.zone,
                instance=self.instance_name
            )
            
            # Get external IP from network interfaces
            for network_interface in instance.network_interfaces:
                for access_config in network_interface.access_configs:
                    if access_config.nat_i_p:
                        return access_config.nat_i_p
            
            # Fallback to internal IP
            if instance.network_interfaces:
                return instance.network_interfaces[0].network_i_p
            
        except Exception as e:
            self.handle_errors(
                e,
                {
                    "operation": "get_instance_ip",
                    "instance_name": self.instance_name,
                    "project_id": self.project_id,
                    "zone": self.zone
                }
            )
        
        return None
    
    def connect(self) -> bool:
        """
        Establish SSH connection to GCP VM
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.instance_name or not self.project_id or not self.zone:
            return False
        
        # Get VM IP if not provided
        hostname = self._get_instance_ip()
        if not hostname:
            return False
        
        # Determine username if not provided (defaults vary by OS image)
        username = self.username or "user"  # Default, should be configured per image
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Decrypt SSH key
            ssh_key_data = self._decrypt_value(self.ssh_key)
            
            if not ssh_key_data:
                return False
            
            # Load private key
            key_file = StringIO(ssh_key_data)
            try:
                private_key = paramiko.RSAKey.from_private_key(key_file)
            except paramiko.ssh_exception.SSHException:
                key_file.seek(0)
                try:
                    private_key = paramiko.ECDSAKey.from_private_key(key_file)
                except paramiko.ssh_exception.SSHException:
                    key_file.seek(0)
                    private_key = paramiko.PKey.from_private_key(key_file)
            
            # Connect via SSH
            self.ssh_client.connect(
                hostname=hostname,
                port=self.port,
                username=username,
                pkey=private_key,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            self.connected = True
            return True
            
        except Exception as e:
            self.handle_errors(
                e,
                {
                    "operation": "connect",
                    "instance_name": self.instance_name,
                    "hostname": hostname
                }
            )
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            try:
                self.ssh_client.close()
            except Exception:
                pass
        
        self.ssh_client = None
        self.connected = False
    
    def execute_command(self, command: str) -> tuple:
        """
        Execute command on GCP VM via SSH
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if not self.connected or not self.ssh_client:
            raise RuntimeError("Not connected to VM")
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command, timeout=self.timeout)
            exit_status = stdout.channel.recv_exit_status()
            
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')
            
            return stdout_text, stderr_text, exit_status
            
        except Exception as e:
            self.handle_errors(
                e,
                {
                    "operation": "execute_command",
                    "instance_name": self.instance_name,
                    "command": command
                }
            )
            return "", str(e), 1

