"""
AWS Scanner - Implementation for AWS EC2 instances
"""
import boto3
import paramiko
from typing import Dict, Any, Optional
from io import StringIO

from core.scanner.base import BaseScanner, ScanResult
from core.database.encryption import get_encryption_manager


class AWSScanner(BaseScanner):
    """
    Scanner implementation for AWS EC2 instances
    Uses SSH to connect to EC2 instances
    Supports:
    - EC2 instances via SSH
    - Session Manager for SSH-less access (future enhancement)
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize AWS scanner
        
        Args:
            config_dict: Configuration containing:
                - instance_id: EC2 instance ID
                - region: AWS region (e.g., "us-east-1")
                - credentials: AWS credentials (access_key, secret_key) or IAM role
                - username: SSH username (e.g., "ec2-user", "ubuntu")
                - ssh_key: SSH private key for instance (encrypted)
                - hostname: Optional - if not provided, will query EC2 for public IP
                - port: SSH port (default: 22)
                - timeout: Connection timeout (default: 30)
        """
        super().__init__(config_dict)
        self.instance_id = config_dict.get("instance_id")
        self.region = config_dict.get("region", "us-east-1")
        self.credentials = config_dict.get("credentials", {})
        self.username = config_dict.get("username", "ec2-user")
        self.ssh_key = config_dict.get("ssh_key")
        self.hostname = config_dict.get("hostname")
        self.port = config_dict.get("port", 22)
        self.timeout = config_dict.get("timeout", 30)
        
        self.ec2_client: Optional[boto3.client] = None
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
    
    def _get_aws_client(self):
        """Get AWS EC2 client"""
        if self.ec2_client:
            return self.ec2_client
        
        # Decrypt credentials if provided
        access_key = self._decrypt_value(self.credentials.get("access_key"))
        secret_key = self._decrypt_value(self.credentials.get("secret_key"))
        
        if access_key and secret_key:
            self.ec2_client = boto3.client(
                'ec2',
                region_name=self.region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        else:
            # Use default credentials (IAM role, environment, etc.)
            self.ec2_client = boto3.client('ec2', region_name=self.region)
        
        return self.ec2_client
    
    def _get_instance_ip(self) -> Optional[str]:
        """Get public IP address of EC2 instance"""
        if self.hostname:
            return self.hostname
        
        try:
            ec2 = self._get_aws_client()
            response = ec2.describe_instances(InstanceIds=[self.instance_id])
            
            if response['Reservations']:
                instance = response['Reservations'][0]['Instances'][0]
                # Try public IP first, fallback to private IP
                return instance.get('PublicIpAddress') or instance.get('PrivateIpAddress')
        except Exception as e:
            self.handle_errors(
                e,
                {"operation": "get_instance_ip", "instance_id": self.instance_id}
            )
        
        return None
    
    def connect(self) -> bool:
        """
        Establish SSH connection to AWS EC2 instance
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.instance_id:
            return False
        
        # Get instance IP if not provided
        hostname = self._get_instance_ip()
        if not hostname:
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
                {"operation": "connect", "instance_id": self.instance_id, "hostname": hostname}
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
        Execute command on EC2 instance via SSH
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if not self.connected or not self.ssh_client:
            raise RuntimeError("Not connected to instance")
        
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
                    "instance_id": self.instance_id,
                    "command": command
                }
            )
            return "", str(e), 1

