"""
Unit tests for AWSScanner
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
import boto3
from moto import mock_ec2

from core.scanner.cloud.aws_scanner import AWSScanner
from core.scanner.base import ScanResult


class TestAWSScanner:
    """Test cases for AWSScanner"""
    
    def test_aws_scanner_init(self):
        """Test initialization"""
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "username": "ec2-user",
            "ssh_key": "encrypted_key"
        }
        scanner = AWSScanner(config)
        assert scanner.instance_id == "i-1234567890abcdef0"
        assert scanner.region == "us-east-1"
        assert scanner.username == "ec2-user"
        assert scanner.ssh_key == "encrypted_key"
        assert scanner.port == 22
    
    @patch('core.scanner.cloud.aws_scanner.get_encryption_manager')
    def test_aws_scanner_get_aws_client_with_credentials(self, mock_encrypt):
        """Test boto3 client creation with credentials"""
        mock_manager = MagicMock()
        mock_manager.decrypt.side_effect = lambda x: x.replace("encrypted_", "")
        mock_encrypt.return_value = mock_manager
        
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "credentials": {
                "access_key": "encrypted_access_key",
                "secret_key": "encrypted_secret_key"
            }
        }
        
        with patch('core.scanner.cloud.aws_scanner.boto3.client') as mock_boto3_client:
            scanner = AWSScanner(config)
            client = scanner._get_aws_client()
            
            mock_boto3_client.assert_called_once()
            call_kwargs = mock_boto3_client.call_args[1]
            assert call_kwargs['region_name'] == "us-east-1"
            assert 'aws_access_key_id' in call_kwargs
    
    @patch('core.scanner.cloud.aws_scanner.boto3.client')
    def test_aws_scanner_get_aws_client_default_credentials(self, mock_boto3_client):
        """Test default credentials"""
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1"
        }
        scanner = AWSScanner(config)
        client = scanner._get_aws_client()
        
        mock_boto3_client.assert_called_once()
        call_kwargs = mock_boto3_client.call_args[1]
        assert call_kwargs['region_name'] == "us-east-1"
        assert 'aws_access_key_id' not in call_kwargs
    
    @mock_ec2
    def test_aws_scanner_get_instance_ip(self):
        """Test EC2 IP retrieval"""
        # Create a mock EC2 instance
        ec2_client = boto3.client('ec2', region_name='us-east-1')
        response = ec2_client.run_instances(ImageId='ami-12345', MinCount=1, MaxCount=1)
        instance_id = response['Instances'][0]['InstanceId']
        
        config = {
            "instance_id": instance_id,
            "region": "us-east-1"
        }
        scanner = AWSScanner(config)
        ip = scanner._get_instance_ip()
        
        # Should return private IP if no public IP
        assert ip is not None
    
    def test_aws_scanner_get_instance_ip_with_hostname(self):
        """Test IP retrieval when hostname is provided"""
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "hostname": "1.2.3.4"
        }
        scanner = AWSScanner(config)
        ip = scanner._get_instance_ip()
        
        assert ip == "1.2.3.4"
    
    @mock_ec2
    def test_aws_scanner_get_instance_ip_not_found(self):
        """Test instance not found handling"""
        config = {
            "instance_id": "i-nonexistent",
            "region": "us-east-1"
        }
        scanner = AWSScanner(config)
        ip = scanner._get_instance_ip()
        
        assert ip is None
    
    @patch('core.scanner.cloud.aws_scanner.AWSScanner._get_instance_ip')
    @patch('core.scanner.cloud.aws_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.aws_scanner.paramiko.RSAKey')
    @patch('core.scanner.cloud.aws_scanner.get_encryption_manager')
    def test_aws_scanner_connect_success(self, mock_encrypt, mock_rsa_key_class, 
                                         mock_ssh_client_class, mock_get_ip):
        """Test successful SSH connection"""
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN RSA PRIVATE KEY-----"
        mock_key = MagicMock()
        mock_rsa_key_class.from_private_key.return_value = mock_key
        mock_client = MagicMock()
        mock_ssh_client_class.return_value = mock_client
        mock_get_ip.return_value = "1.2.3.4"
        
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "username": "ec2-user",
            "ssh_key": "encrypted_key"
        }
        scanner = AWSScanner(config)
        result = scanner.connect()
        
        assert result is True
        assert scanner.connected is True
        mock_client.connect.assert_called_once()
    
    @patch('core.scanner.cloud.aws_scanner.AWSScanner._get_instance_ip')
    def test_aws_scanner_connect_failure_no_ip(self, mock_get_ip):
        """Test connection failure when IP cannot be retrieved"""
        mock_get_ip.return_value = None
        
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1"
        }
        scanner = AWSScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud.aws_scanner.AWSScanner._get_instance_ip')
    @patch('core.scanner.cloud.aws_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.aws_scanner.get_encryption_manager')
    def test_aws_scanner_connect_failure_ssh_error(self, mock_encrypt, mock_ssh_client_class, mock_get_ip):
        """Test connection failure with SSH error"""
        mock_get_ip.return_value = "1.2.3.4"
        mock_encrypt.return_value.decrypt.return_value = "key"
        mock_client = MagicMock()
        mock_client.connect.side_effect = Exception("SSH connection failed")
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "ssh_key": "encrypted_key"
        }
        scanner = AWSScanner(config)
        result = scanner.connect()
        
        assert result is False
    
    def test_aws_scanner_disconnect(self):
        """Test disconnect"""
        config = {"instance_id": "i-1234567890abcdef0", "region": "us-east-1"}
        scanner = AWSScanner(config)
        scanner.connected = True
        mock_client = MagicMock()
        scanner.ssh_client = mock_client
        
        scanner.disconnect()
        
        assert not scanner.connected
        assert scanner.ssh_client is None
        mock_client.close.assert_called_once()
    
    @patch('core.scanner.cloud.aws_scanner.get_encryption_manager')
    def test_aws_scanner_execute_command(self, mock_encrypt):
        """Test command execution"""
        config = {"instance_id": "i-1234567890abcdef0", "region": "us-east-1"}
        scanner = AWSScanner(config)
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
    
    @patch('core.scanner.cloud.aws_scanner.AWSScanner.connect')
    @patch('core.scanner.cloud.aws_scanner.AWSScanner.execute_command')
    @patch('core.compliance.jdk_detector.JDKDetector')
    def test_aws_scanner_scan_method(self, mock_detector_class, mock_execute, mock_connect):
        """Test full scan workflow"""
        mock_connect.return_value = True
        mock_execute.return_value = ("java version \"11.0.1\"", "", 0)
        mock_detector = MagicMock()
        mock_detector.parse_version_output.return_value = {"version": "11.0.1", "vendor": "Oracle"}
        mock_detector_class.return_value = mock_detector
        
        config = {"instance_id": "i-1234567890abcdef0", "region": "us-east-1"}
        scanner = AWSScanner(config)
        result = scanner.scan({"instance_id": "i-1234567890abcdef0"})
        
        assert result.success is True
        assert result.jdk_version == "11.0.1"

