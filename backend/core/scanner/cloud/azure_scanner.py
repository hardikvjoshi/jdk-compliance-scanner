"""
Azure Scanner - Implementation for Azure VMs
"""
import paramiko
from typing import Dict, Any, Optional
from io import StringIO

from core.scanner.base import BaseScanner, ScanResult
from core.database.encryption import get_encryption_manager

try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.network import NetworkManagementClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class AzureScanner(BaseScanner):
    """
    Scanner implementation for Azure VMs
    Uses SSH to connect to Azure Virtual Machines
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize Azure scanner
        
        Args:
            config_dict: Configuration containing:
                - resource_group: Azure resource group name
                - vm_name: Azure VM name
                - subscription_id: Azure subscription ID
                - credentials: Azure credentials (client_id, client_secret, tenant_id) or use DefaultAzureCredential
                - username: SSH username
                - ssh_key: SSH private key (encrypted)
                - hostname: Optional - if not provided, will query Azure for public IP
                - port: SSH port (default: 22)
                - timeout: Connection timeout (default: 30)
        """
        super().__init__(config_dict)
        
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK not available. Install azure-identity and azure-mgmt-compute.")
        
        self.resource_group = config_dict.get("resource_group")
        self.vm_name = config_dict.get("vm_name")
        self.subscription_id = config_dict.get("subscription_id")
        self.credentials = config_dict.get("credentials", {})
        self.username = config_dict.get("username", "azureuser")
        self.ssh_key = config_dict.get("ssh_key")
        self.hostname = config_dict.get("hostname")
        self.port = config_dict.get("port", 22)
        self.timeout = config_dict.get("timeout", 30)
        
        self.compute_client: Optional[ComputeManagementClient] = None
        self.network_client: Optional[NetworkManagementClient] = None
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
    
    def _get_azure_credentials(self):
        """Get Azure credentials"""
        client_id = self._decrypt_value(self.credentials.get("client_id"))
        client_secret = self._decrypt_value(self.credentials.get("client_secret"))
        tenant_id = self._decrypt_value(self.credentials.get("tenant_id"))
        
        if client_id and client_secret and tenant_id:
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            # Use DefaultAzureCredential (Managed Identity, Environment, etc.)
            return DefaultAzureCredential()
    
    def _get_vm_ip(self) -> Optional[str]:
        """Get public IP address of Azure VM"""
        if self.hostname:
            return self.hostname
        
        try:
            credential = self._get_azure_credentials()
            self.network_client = NetworkManagementClient(credential, self.subscription_id)
            
            # Get network interfaces for the VM
            vm = self.network_client.virtual_machines.get(
                self.resource_group,
                self.vm_name
            )
            
            # Get public IP from network interface
            # This is simplified - actual implementation may need to traverse network interfaces
            # For now, return None if hostname not provided
            # TODO: Implement full IP resolution logic
            
        except Exception as e:
            self.handle_errors(
                e,
                {"operation": "get_vm_ip", "vm_name": self.vm_name, "resource_group": self.resource_group}
            )
        
        return None
    
    def connect(self) -> bool:
        """
        Establish SSH connection to Azure VM
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.vm_name or not self.resource_group:
            return False
        
        # Get VM IP if not provided
        hostname = self._get_vm_ip()
        if not hostname:
            # If we can't get IP, connection will fail
            return False
        
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
                username=self.username,
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
                {"operation": "connect", "vm_name": self.vm_name, "hostname": hostname}
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
        Execute command on Azure VM via SSH
        
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
                    "vm_name": self.vm_name,
                    "command": command
                }
            )
            return "", str(e), 1

