"""
Unit tests for GCPScanner
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import json

from core.scanner.cloud.gcp_scanner import GCPScanner


class TestGCPScanner:
    """Test cases for GCPScanner"""
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    def test_gcp_scanner_init(self):
        """Test initialization"""
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance",
            "username": "user",
            "ssh_key": "encrypted_key"
        }
        scanner = GCPScanner(config)
        assert scanner.project_id == "test-project"
        assert scanner.zone == "us-central1-a"
        assert scanner.instance_name == "test-instance"
        assert scanner.username == "user"
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', False)
    def test_gcp_scanner_init_missing_sdk(self):
        """Test ImportError when SDK not available"""
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        with pytest.raises(ImportError, match="GCP SDK not available"):
            GCPScanner(config)
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.service_account', create=True)
    @patch('core.scanner.cloud.gcp_scanner.compute_v1', create=True)
    @patch('core.scanner.cloud.gcp_scanner.get_encryption_manager')
    def test_gcp_scanner_get_gcp_client_with_service_account(self, mock_encrypt, 
                                                            mock_compute_v1, mock_service_account):
        """Test service account auth"""
        mock_manager = MagicMock()
        service_account_json = json.dumps({"type": "service_account", "project_id": "test"})
        mock_manager.decrypt.return_value = service_account_json
        mock_encrypt.return_value = mock_manager
        mock_cred = MagicMock()
        mock_service_account.Credentials.from_service_account_info.return_value = mock_cred
        mock_client = MagicMock()
        mock_compute_v1.InstancesClient.return_value = mock_client
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance",
            "credentials": {
                "service_account_json": "encrypted_json"
            }
        }
        scanner = GCPScanner(config)
        client = scanner._get_gcp_client()
        
        mock_service_account.Credentials.from_service_account_info.assert_called_once()
        assert client == mock_client
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.compute_v1', create=True)
    def test_gcp_scanner_get_gcp_client_default(self, mock_compute_v1):
        """Test default credentials"""
        mock_client = MagicMock()
        mock_compute_v1.InstancesClient.return_value = mock_client
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
        client = scanner._get_gcp_client()
        
        mock_compute_v1.InstancesClient.assert_called_once()
        assert client == mock_client
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.GCPScanner._get_gcp_client')
    def test_gcp_scanner_get_instance_ip_external(self, mock_get_client):
        """Test external IP retrieval"""
        mock_client = MagicMock()
        mock_instance = MagicMock()
        mock_network_interface = MagicMock()
        mock_access_config = MagicMock()
        mock_access_config.nat_i_p = "1.2.3.4"
        mock_network_interface.access_configs = [mock_access_config]
        mock_instance.network_interfaces = [mock_network_interface]
        mock_client.get.return_value = mock_instance
        mock_get_client.return_value = mock_client
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
        ip = scanner._get_instance_ip()
        
        assert ip == "1.2.3.4"
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.GCPScanner._get_gcp_client')
    def test_gcp_scanner_get_instance_ip_internal(self, mock_get_client):
        """Test internal IP fallback"""
        mock_client = MagicMock()
        mock_instance = MagicMock()
        mock_network_interface = MagicMock()
        mock_network_interface.access_configs = []  # No external IP
        mock_network_interface.network_i_p = "10.0.0.1"
        mock_instance.network_interfaces = [mock_network_interface]
        mock_client.get.return_value = mock_instance
        mock_get_client.return_value = mock_client
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
        ip = scanner._get_instance_ip()
        
        assert ip == "10.0.0.1"
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    def test_gcp_scanner_get_instance_ip_with_hostname(self):
        """Test IP retrieval when hostname is provided"""
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance",
            "hostname": "1.2.3.4"
        }
        scanner = GCPScanner(config)
        ip = scanner._get_instance_ip()
        
        assert ip == "1.2.3.4"
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.GCPScanner._get_instance_ip')
    @patch('core.scanner.cloud.gcp_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.gcp_scanner.paramiko.RSAKey')
    @patch('core.scanner.cloud.gcp_scanner.get_encryption_manager')
    def test_gcp_scanner_connect_success(self, mock_encrypt, mock_rsa_key_class,
                                        mock_ssh_client_class, mock_get_ip):
        """Test successful connection"""
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN RSA PRIVATE KEY-----"
        mock_key = MagicMock()
        mock_rsa_key_class.from_private_key.return_value = mock_key
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        mock_get_ip.return_value = "1.2.3.4"
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance",
            "username": "user",
            "ssh_key": "encrypted_key"
        }
        scanner = GCPScanner(config)
        result = scanner.connect()
        
        assert result is True
        assert scanner.connected is True
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.GCPScanner._get_instance_ip')
    def test_gcp_scanner_connect_failure_no_ip(self, mock_get_ip):
        """Test connection failure when IP cannot be retrieved"""
        mock_get_ip.return_value = None
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.GCPScanner._get_instance_ip')
    @patch('core.scanner.cloud.gcp_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.gcp_scanner.get_encryption_manager')
    def test_gcp_scanner_connect_failure(self, mock_encrypt, mock_ssh_client_class, mock_get_ip):
        """Test connection failure"""
        mock_get_ip.return_value = "1.2.3.4"
        mock_encrypt.return_value.decrypt.return_value = "key"
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("Connection failed")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance",
            "ssh_key": "encrypted_key"
        }
        scanner = GCPScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    @patch('core.scanner.cloud.gcp_scanner.get_encryption_manager')
    def test_gcp_scanner_execute_command(self, mock_encrypt):
        """Test command execution"""
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
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
    
    @patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True)
    def test_gcp_scanner_disconnect(self):
        """Test disconnect"""
        config = {
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = GCPScanner(config)
        scanner.connected = True
        mock_client = MagicMock()
        scanner.ssh_client = mock_client
        
        scanner.disconnect()
        
        assert not scanner.connected
        assert scanner.ssh_client is None
        mock_client.close.assert_called_once()

