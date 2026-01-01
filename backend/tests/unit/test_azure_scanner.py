"""
Unit tests for AzureScanner
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from core.scanner.cloud.azure_scanner import AzureScanner


class TestAzureScanner:
    """Test cases for AzureScanner"""
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    def test_azure_scanner_init(self):
        """Test initialization"""
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123",
            "username": "azureuser",
            "ssh_key": "encrypted_key"
        }
        scanner = AzureScanner(config)
        assert scanner.resource_group == "test-rg"
        assert scanner.vm_name == "test-vm"
        assert scanner.subscription_id == "sub-123"
        assert scanner.username == "azureuser"
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', False)
    def test_azure_scanner_init_missing_sdk(self):
        """Test ImportError when SDK not available"""
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        with pytest.raises(ImportError, match="Azure SDK not available"):
            AzureScanner(config)
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.ClientSecretCredential', create=True)
    @patch('core.scanner.cloud.azure_scanner.get_encryption_manager')
    def test_azure_scanner_get_azure_credentials_service_principal(self, mock_encrypt, mock_cred_class):
        """Test service principal auth"""
        mock_manager = MagicMock()
        mock_manager.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
        mock_encrypt.return_value = mock_manager
        mock_cred = MagicMock()
        mock_cred_class.return_value = mock_cred
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123",
            "credentials": {
                "client_id": "encrypted_client_id",
                "client_secret": "encrypted_client_secret",
                "tenant_id": "encrypted_tenant_id"
            }
        }
        scanner = AzureScanner(config)
        cred = scanner._get_azure_credentials()
        
        mock_cred_class.assert_called_once()
        assert cred == mock_cred
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.DefaultAzureCredential', create=True)
    @patch('core.scanner.cloud.azure_scanner.get_encryption_manager')
    def test_azure_scanner_get_azure_credentials_default(self, mock_encrypt, mock_cred_class):
        """Test default credentials"""
        mock_cred = MagicMock()
        mock_cred_class.return_value = mock_cred
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        scanner = AzureScanner(config)
        cred = scanner._get_azure_credentials()
        
        mock_cred_class.assert_called_once()
        assert cred == mock_cred
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.NetworkManagementClient', create=True)
    @patch('core.scanner.cloud.azure_scanner.AzureScanner._get_azure_credentials')
    def test_azure_scanner_get_vm_ip(self, mock_get_cred, mock_client_class):
        """Test VM IP retrieval"""
        mock_cred = MagicMock()
        mock_get_cred.return_value = mock_cred
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123",
            "hostname": "1.2.3.4"
        }
        scanner = AzureScanner(config)
        ip = scanner._get_vm_ip()
        
        # If hostname provided, should return it
        assert ip == "1.2.3.4"
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.AzureScanner._get_vm_ip')
    @patch('core.scanner.cloud.azure_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.azure_scanner.paramiko.RSAKey')
    @patch('core.scanner.cloud.azure_scanner.get_encryption_manager')
    def test_azure_scanner_connect_success(self, mock_encrypt, mock_rsa_key_class,
                                          mock_ssh_client_class, mock_get_ip):
        """Test successful connection"""
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN RSA PRIVATE KEY-----"
        mock_key = MagicMock()
        mock_rsa_key_class.from_private_key.return_value = mock_key
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        mock_get_ip.return_value = "1.2.3.4"
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123",
            "username": "azureuser",
            "ssh_key": "encrypted_key"
        }
        scanner = AzureScanner(config)
        result = scanner.connect()
        
        assert result is True
        assert scanner.connected is True
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.AzureScanner._get_vm_ip')
    def test_azure_scanner_connect_failure_no_ip(self, mock_get_ip):
        """Test connection failure when IP cannot be retrieved"""
        mock_get_ip.return_value = None
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        scanner = AzureScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.AzureScanner._get_vm_ip')
    @patch('core.scanner.cloud.azure_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.azure_scanner.get_encryption_manager')
    def test_azure_scanner_connect_failure(self, mock_encrypt, mock_ssh_client_class, mock_get_ip):
        """Test connection failure"""
        mock_get_ip.return_value = "1.2.3.4"
        mock_encrypt.return_value.decrypt.return_value = "key"
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123",
            "ssh_key": "encrypted_key"
        }
        scanner = AzureScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    @patch('core.scanner.cloud.azure_scanner.get_encryption_manager')
    def test_azure_scanner_execute_command(self, mock_encrypt):
        """Test command execution"""
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        scanner = AzureScanner(config)
        scanner.connected = True
        
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        scanner.ssh_client = mock_client
        
        stdout, stderr, return_code = scanner.execute_command("java -version")
        
        assert stdout == "output"
        assert return_code == 0
    
    @patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True)
    def test_azure_scanner_disconnect(self):
        """Test disconnect"""
        config = {
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        scanner = AzureScanner(config)
        scanner.connected = True
        mock_client = MagicMock()
        scanner.ssh_client = mock_client
        
        scanner.disconnect()
        
        assert not scanner.connected
        assert scanner.ssh_client is None
        mock_client.close.assert_called_once()

