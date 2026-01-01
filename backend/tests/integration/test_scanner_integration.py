"""
Integration tests for scanners
"""
import pytest
from unittest.mock import patch, MagicMock

from core.scanner.factory import ScannerFactory
from core.scanner.unix_scanner import UnixScanner
from core.scanner.parallel_executor import ParallelExecutor, ScanStrategy


class TestScannerIntegration:
    """Integration tests for scanner workflows"""
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_unix_scanner_full_workflow(self, mock_encrypt, mock_ssh_client_class):
        """Test complete Unix scan workflow with mocked SSH"""
        mock_encrypt.return_value.decrypt.return_value = "password"
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'openjdk version "11.0.1"'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client
        
        config = {
            "hostname": "test.example.com",
            "username": "user",
            "password": "encrypted_password"
        }
        scanner = UnixScanner(config)
        assert scanner.connect() is True
        
        from core.scanner.base import ScanResult
        result = scanner.scan({"hostname": "test.example.com"})
        assert result.success is True
        scanner.disconnect()
    
    @patch('core.scanner.cloud.aws_scanner.AWSScanner._get_instance_ip')
    @patch('core.scanner.cloud.aws_scanner.paramiko.SSHClient')
    @patch('core.scanner.cloud.aws_scanner.get_encryption_manager')
    def test_aws_scanner_full_workflow(self, mock_encrypt, mock_ssh_client_class, mock_get_ip):
        """Test complete AWS scan workflow with mocked EC2 and SSH"""
        mock_get_ip.return_value = "1.2.3.4"
        mock_encrypt.return_value.decrypt.return_value = "-----BEGIN RSA PRIVATE KEY-----"
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'java version "11.0.1"'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client
        
        from core.scanner.cloud.aws_scanner import AWSScanner
        config = {
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1",
            "username": "ec2-user",
            "ssh_key": "encrypted_key"
        }
        scanner = AWSScanner(config)
        assert scanner.connect() is True
        
        result = scanner.scan({"instance_id": "i-1234567890abcdef0"})
        assert result.success is True
        scanner.disconnect()
    
    def test_factory_scanner_creation_integration(self):
        """Test factory creates correct scanner types"""
        # Test Unix scanner
        try:
            from core.scanner.unix_scanner import UnixScanner
            ScannerFactory._scanner_classes.clear()
            ScannerFactory.register_scanner("unix", UnixScanner)
            config = {"hostname": "test.example.com", "username": "user"}
            scanner = ScannerFactory.create_scanner("unix", config)
            assert isinstance(scanner, UnixScanner)
        except ImportError:
            pytest.skip("UnixScanner not available")
    
    @patch('core.scanner.unix_scanner.paramiko.SSHClient')
    @patch('core.scanner.unix_scanner.get_encryption_manager')
    def test_parallel_executor_with_unix_scanners(self, mock_encrypt, mock_ssh_client_class):
        """Test parallel execution with Unix scanners"""
        mock_encrypt.return_value.decrypt.return_value = "password"
        mock_client = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b'java version "11"'
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b''
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout.channel = mock_channel
        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_ssh_client_class.return_value = mock_client
        
        from core.scanner.unix_scanner import UnixScanner
        targets = [
            {"hostname": "host1.example.com", "username": "user"},
            {"hostname": "host2.example.com", "username": "user"}
        ]
        
        def scanner_factory(target):
            return UnixScanner({**target, "password": "encrypted"})
        
        executor = ParallelExecutor(max_workers=2)
        results = executor.execute_scans(scanner_factory, targets, ScanStrategy.PARALLEL)
        
        assert len(results) == 2

