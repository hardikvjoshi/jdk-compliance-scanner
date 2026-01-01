"""
Unit tests for UnixScanner
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, StringIO
import paramiko

from core.scanner.unix_scanner import UnixScanner
from core.scanner.base import ScanResult


class TestUnixScanner:
    """Test cases for UnixScanner"""
    
    def test_unix_scanner_init(self):
        """Test initialization with various configs"""
        config = {
            "hostname": "test.example.com",
            "port": 22,
            "username": "testuser",
            "password": "testpass",
            "timeout": 30
        }
        scanner = UnixScanner(config)
        assert scanner.hostname == "test.example.com"
        assert scanner.port == 22
        assert scanner.username == "testuser"
        assert scanner.password == "testpass"
        assert scanner.timeout == 30
        assert not scanner.connected
    
    def test_unix_scanner_init_with_key(self):
        """Test initialization with SSH key"""
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "ssh_key": "-----BEGIN RSA PRIVATE KEY-----",
            "ssh_key_passphrase": "passphrase"
        }
        scanner = UnixScanner(config)
        assert scanner.ssh_key == "-----BEGIN RSA PRIVATE KEY-----"
        assert scanner.ssh_key_passphrase == "passphrase"
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_connect_with_password(self, mock_encrypt, mock_ssh_client_class):
        """Test SSH connection with password auth"""
        mock_encrypt.return_value.decrypt.return_value = "decrypted_password"
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "encrypted_password"
        }
        scanner = UnixScanner(config)
        result = scanner.connect()
        
        assert result is True
        assert scanner.connected is True
        mock_client.set_missing_host_key_policy.assert_called_once()
        mock_client.connect.assert_called_once()
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.paramiko.RSAKey')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_connect_with_key(self, mock_encrypt, mock_rsa_key_class, mock_ssh_client_class):
        """Test SSH connection with RSA key"""
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN RSA PRIVATE KEY-----"
        mock_key = MagicMock()
        mock_rsa_key_class.from_private_key.return_value = mock_key
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "ssh_key": "encrypted_key"
        }
        scanner = UnixScanner(config)
        result = scanner.connect()
        
        assert result is True
        mock_client.connect.assert_called_once()
        call_kwargs = mock_client.connect.call_args[1]
        assert 'pkey' in call_kwargs
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.paramiko.ECDSAKey')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_connect_with_ecdsa_key(self, mock_encrypt, mock_ecdsa_key_class, mock_ssh_client_class):
        """Test SSH connection with ECDSA key"""
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN EC PRIVATE KEY-----"
        mock_key = MagicMock()
        mock_ecdsa_key_class.from_private_key.return_value = mock_key
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "ssh_key": "encrypted_key"
        }
        scanner = UnixScanner(config)
        # RSA will fail, ECDSA should work
        with patch('core.scanner.unix_scanner.paramiko.RSAKey.from_private_key', side_effect=paramiko.ssh_exception.SSHException()):
            result = scanner.connect()
            assert result is True
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_connect_auth_failure(self, mock_encrypt, mock_ssh_client_class):
        """Test authentication failure handling"""
        mock_encrypt.return_value.decrypt.return_value = "wrong_password"
        mock_client = MagicMock()
        mock_client.connect.side_effect = paramiko.AuthenticationException("Auth failed")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "encrypted_password"
        }
        scanner = UnixScanner(config)
        result = scanner.connect()
        
        assert result is False
        assert not scanner.connected
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_connect_connection_error(self, mock_encrypt, mock_ssh_client_class):
        """Test connection error handling"""
        mock_encrypt.return_value.decrypt.return_value = "password"
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "encrypted_password"
        }
        scanner = UnixScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    def test_unix_scanner_disconnect(self):
        """Test disconnect functionality"""
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        scanner.connected = True
        mock_client = MagicMock()
        scanner.client = mock_client
        
        scanner.disconnect()
        
        assert not scanner.connected
        assert scanner.client is None
        mock_client.close.assert_called_once()
    
    def test_unix_scanner_disconnect_not_connected(self):
        """Test disconnect when not connected"""
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        scanner.connected = False
        
        scanner.disconnect()  # Should not raise error
    
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_execute_command_success(self, mock_encrypt):
        """Test successful command execution"""
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        scanner.connected = True
        
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"command output"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        scanner.client = mock_client
        
        stdout, stderr, return_code = scanner.execute_command("java -version")
        
        assert stdout == "command output"
        assert return_code == 0
        mock_client.exec_command.assert_called_once_with("java -version", timeout=30)
    
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_execute_command_failure(self, mock_encrypt):
        """Test command execution failure"""
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        scanner.connected = True
        
        mock_client = MagicMock()
        mock_client.exec_command.side_effect = Exception("Command failed")
        scanner.client = mock_client
        
        stdout, stderr, return_code = scanner.execute_command("java -version")
        
        assert return_code == 1
        assert "Command failed" in stderr
    
    def test_unix_scanner_execute_command_not_connected(self):
        """Test execution when not connected"""
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        scanner.connected = False
        
        with pytest.raises(RuntimeError, match="Not connected"):
            scanner.execute_command("java -version")
    
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_decrypt_credentials(self, mock_encrypt):
        """Test credential decryption"""
        mock_manager = MagicMock()
        mock_manager.decrypt.return_value = "decrypted_value"
        mock_encrypt.return_value = mock_manager
        
        config = {"hostname": "test.example.com", "username": "testuser", "password": "encrypted"}
        scanner = UnixScanner(config)
        result = scanner._decrypt_value("encrypted_value")
        
        assert result == "decrypted_value"
        mock_manager.decrypt.assert_called_once_with("encrypted_value")
    
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_decrypt_credentials_not_encrypted(self, mock_encrypt):
        """Test decryption with non-encrypted value"""
        mock_manager = MagicMock()
        mock_manager.decrypt.side_effect = Exception("Not encrypted")
        mock_encrypt.return_value = mock_manager
        
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        result = scanner._decrypt_value("plain_value")
        
        # Should return original value if decryption fails
        assert result == "plain_value"
    
    @patch('core.scanner.unix_scanner.UnixScanner.connect')
    @patch('core.scanner.unix_scanner.UnixScanner.execute_command')
    @patch('core.compliance.jdk_detector.JDKDetector')
    def test_unix_scanner_scan_method(self, mock_detector_class, mock_execute, mock_connect):
        """Test full scan workflow"""
        mock_connect.return_value = True
        mock_execute.return_value = ("java version \"11.0.1\"", "", 0)
        mock_detector = MagicMock()
        mock_detector.parse_version_output.return_value = {"version": "11.0.1", "vendor": "Oracle"}
        mock_detector_class.return_value = mock_detector
        
        config = {"hostname": "test.example.com", "username": "testuser"}
        scanner = UnixScanner(config)
        result = scanner.scan({"hostname": "test.example.com"})
        
        assert result.success is True
        assert result.jdk_version == "11.0.1"
        assert result.jdk_vendor == "Oracle"
        mock_connect.assert_called_once()
        mock_execute.assert_called_once()
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_timeout_handling(self, mock_encrypt, mock_ssh_client_class):
        """Test timeout scenarios"""
        mock_encrypt.return_value.decrypt.return_value = "password"
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Timeout")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "encrypted_password",
            "timeout": 10
        }
        scanner = UnixScanner(config)
        result = scanner.connect()
        
        assert result is False

