"""
Unit tests for CloudScanner routing
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from core.scanner.cloud_scanner import CloudScanner
from core.scanner.base import ScanResult


class TestCloudScanner:
    """Test cases for CloudScanner routing"""
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_aws_routing(self, mock_aws_scanner_class):
        """Test routing to AWS scanner"""
        mock_scanner = MagicMock()
        mock_aws_scanner_class.return_value = mock_scanner
        
        config = {
            "provider": "aws",
            "instance_id": "i-1234567890abcdef0",
            "region": "us-east-1"
        }
        scanner = CloudScanner(config)
        
        mock_aws_scanner_class.assert_called_once_with(config)
        assert scanner.scanner == mock_scanner
        assert scanner.provider == "aws"
    
    @patch('core.scanner.cloud_scanner.AzureScanner')
    def test_cloud_scanner_azure_routing(self, mock_azure_scanner_class):
        """Test routing to Azure scanner"""
        mock_scanner = MagicMock()
        mock_azure_scanner_class.return_value = mock_scanner
        
        config = {
            "provider": "azure",
            "resource_group": "test-rg",
            "vm_name": "test-vm",
            "subscription_id": "sub-123"
        }
        scanner = CloudScanner(config)
        
        mock_azure_scanner_class.assert_called_once_with(config)
        assert scanner.scanner == mock_scanner
        assert scanner.provider == "azure"
    
    @patch('core.scanner.cloud_scanner.GCPScanner')
    def test_cloud_scanner_gcp_routing(self, mock_gcp_scanner_class):
        """Test routing to GCP scanner"""
        mock_scanner = MagicMock()
        mock_gcp_scanner_class.return_value = mock_scanner
        
        config = {
            "provider": "gcp",
            "project_id": "test-project",
            "zone": "us-central1-a",
            "instance_name": "test-instance"
        }
        scanner = CloudScanner(config)
        
        mock_gcp_scanner_class.assert_called_once_with(config)
        assert scanner.scanner == mock_scanner
        assert scanner.provider == "gcp"
    
    def test_cloud_scanner_unsupported_provider(self):
        """Test unsupported provider error"""
        config = {
            "provider": "unknown",
            "region": "us-east-1"
        }
        
        with pytest.raises(ValueError, match="Unsupported cloud provider"):
            CloudScanner(config)
    
    @patch('core.scanner.cloud_scanner.AWSScanner', side_effect=ImportError("boto3 not available"))
    def test_cloud_scanner_missing_aws_sdk(self, mock_aws_scanner_class):
        """Test AWS SDK missing error"""
        config = {
            "provider": "aws",
            "instance_id": "i-1234567890abcdef0"
        }
        
        with pytest.raises(ValueError, match="AWS scanner not available"):
            CloudScanner(config)
    
    @patch('core.scanner.cloud_scanner.AzureScanner', side_effect=ImportError("azure not available"))
    def test_cloud_scanner_missing_azure_sdk(self, mock_azure_scanner_class):
        """Test Azure SDK missing error"""
        config = {
            "provider": "azure",
            "resource_group": "test-rg",
            "vm_name": "test-vm"
        }
        
        with pytest.raises(ValueError, match="Azure scanner not available"):
            CloudScanner(config)
    
    @patch('core.scanner.cloud_scanner.GCPScanner', side_effect=ImportError("gcp not available"))
    def test_cloud_scanner_missing_gcp_sdk(self, mock_gcp_scanner_class):
        """Test GCP SDK missing error"""
        config = {
            "provider": "gcp",
            "project_id": "test-project",
            "instance_name": "test-instance"
        }
        
        with pytest.raises(ValueError, match="GCP scanner not available"):
            CloudScanner(config)
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_delegate_connect(self, mock_aws_scanner_class):
        """Test method delegation - connect"""
        mock_scanner = MagicMock()
        mock_scanner.connect.return_value = True
        mock_aws_scanner_class.return_value = mock_scanner
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        result = scanner.connect()
        
        assert result is True
        mock_scanner.connect.assert_called_once()
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_delegate_disconnect(self, mock_aws_scanner_class):
        """Test method delegation - disconnect"""
        mock_scanner = MagicMock()
        mock_aws_scanner_class.return_value = mock_scanner
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        scanner.connected = True
        scanner.disconnect()
        
        mock_scanner.disconnect.assert_called_once()
        assert not scanner.connected
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_delegate_execute_command(self, mock_aws_scanner_class):
        """Test method delegation - execute_command"""
        mock_scanner = MagicMock()
        mock_scanner.execute_command.return_value = ("output", "error", 0)
        mock_aws_scanner_class.return_value = mock_scanner
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        stdout, stderr, return_code = scanner.execute_command("java -version")
        
        assert stdout == "output"
        mock_scanner.execute_command.assert_called_once_with("java -version")
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_delegate_scan(self, mock_aws_scanner_class):
        """Test method delegation - scan"""
        mock_scanner = MagicMock()
        mock_result = ScanResult(success=True, jdk_version="11.0.1")
        mock_scanner.scan.return_value = mock_result
        mock_aws_scanner_class.return_value = mock_scanner
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        result = scanner.scan({"instance_id": "i-123"})
        
        assert result.success is True
        assert result.jdk_version == "11.0.1"
        mock_scanner.scan.assert_called_once()
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_connect_no_scanner(self, mock_aws_scanner_class):
        """Test connect when no scanner initialized"""
        mock_aws_scanner_class.return_value = None
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        scanner.scanner = None
        result = scanner.connect()
        
        assert result is False
    
    @patch('core.scanner.cloud_scanner.AWSScanner')
    def test_cloud_scanner_scan_no_scanner(self, mock_aws_scanner_class):
        """Test scan when no scanner initialized"""
        mock_aws_scanner_class.return_value = None
        
        config = {"provider": "aws", "instance_id": "i-123"}
        scanner = CloudScanner(config)
        scanner.scanner = None
        result = scanner.scan({"instance_id": "i-123"})
        
        assert result.success is False
        assert "No scanner initialized" in result.error_message

