"""
Unix/Linux Scanner - Implementation for Unix/Linux systems using SSH
"""
import paramiko
from typing import Dict, Any, Optional
from io import StringIO

from core.scanner.base import BaseScanner, ScanResult
from core.database.encryption import get_encryption_manager


class UnixScanner(BaseScanner):
    """
    Scanner implementation for Unix/Linux systems
    Uses SSH (paramiko) to execute commands on remote hosts
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Initialize Unix scanner
        
        Args:
            config_dict: Configuration containing:
                - hostname: Target hostname or IP address
                - port: SSH port (default: 22)
                - username: SSH username
                - password: SSH password (encrypted, optional if using key)
                - ssh_key: SSH private key (encrypted, optional)
                - ssh_key_passphrase: Passphrase for SSH key (encrypted, optional)
                - timeout: Connection timeout in seconds (default: 30)
        """
        super().__init__(config_dict)
        self.hostname = config_dict.get("hostname")
        self.port = config_dict.get("port", 22)
        self.username = config_dict.get("username")
        self.password = config_dict.get("password")  # Will be decrypted
        self.ssh_key = config_dict.get("ssh_key")  # Will be decrypted
        self.ssh_key_passphrase = config_dict.get("ssh_key_passphrase")  # Will be decrypted
        self.timeout = config_dict.get("timeout", 30)
        
        self.client: Optional[paramiko.SSHClient] = None
    
    def _decrypt_value(self, encrypted_value: Optional[str]) -> Optional[str]:
        """Decrypt a value using the encryption manager"""
        if not encrypted_value:
            return None
        
        encryptor = get_encryption_manager()
        try:
            return encryptor.decrypt(encrypted_value)
        except Exception:
            # If decryption fails, assume it's not encrypted (for backward compatibility)
            return encrypted_value
    
    def connect(self) -> bool:
        """
        Establish SSH connection to Unix system
        
        Returns:
            True if connection successful, False otherwise
        """
        if not self.hostname or not self.username:
            return False
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Decrypt credentials
            password = self._decrypt_value(self.password)
            ssh_key_data = self._decrypt_value(self.ssh_key)
            key_passphrase = self._decrypt_value(self.ssh_key_passphrase)
            
            # Connect using key-based or password authentication
            if ssh_key_data:
                # Use SSH key authentication
                key_file = StringIO(ssh_key_data)
                try:
                    # Try RSA key first
                    private_key = paramiko.RSAKey.from_private_key(
                        key_file, 
                        password=key_passphrase
                    )
                except paramiko.ssh_exception.SSHException:
                    # Try ECDSA key
                    key_file.seek(0)
                    try:
                        private_key = paramiko.ECDSAKey.from_private_key(
                            key_file,
                            password=key_passphrase
                        )
                    except paramiko.ssh_exception.SSHException:
                        # Try Ed25519 key
                        key_file.seek(0)
                        try:
                            private_key = paramiko.Ed25519Key.from_private_key(
                                key_file,
                                password=key_passphrase
                            )
                        except Exception:
                            # Try generic private key (handles DSA, etc.)
                            key_file.seek(0)
                            private_key = paramiko.PKey.from_private_key(
                                key_file,
                                password=key_passphrase
                            )
                
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    pkey=private_key,
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
            elif password:
                # Use password authentication
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    password=password,
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
            else:
                # Try with system SSH keys
                self.client.connect(
                    hostname=self.hostname,
                    port=self.port,
                    username=self.username,
                    timeout=self.timeout
                )
            
            self.connected = True
            return True
            
        except paramiko.AuthenticationException as e:
            self.handle_errors(
                e,
                {"operation": "connect", "hostname": self.hostname, "error_type": "authentication"}
            )
            return False
        except paramiko.SSHException as e:
            self.handle_errors(
                e,
                {"operation": "connect", "hostname": self.hostname, "error_type": "ssh_error"}
            )
            return False
        except Exception as e:
            self.handle_errors(
                e,
                {"operation": "connect", "hostname": self.hostname, "error_type": "connection_error"}
            )
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        
        self.client = None
        self.connected = False
    
    def execute_command(self, command: str) -> tuple:
        """
        Execute command on Unix system via SSH
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if not self.connected or not self.client:
            raise RuntimeError("Not connected to host")
        
        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=self.timeout)
            
            # Wait for command to complete
            exit_status = stdout.channel.recv_exit_status()
            
            # Read output
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')
            
            return stdout_text, stderr_text, exit_status
            
        except Exception as e:
            self.handle_errors(
                e,
                {
                    "operation": "execute_command",
                    "hostname": self.hostname,
                    "command": command
                }
            )
            return "", str(e), 1

