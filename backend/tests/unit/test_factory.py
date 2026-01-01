"""
Unit tests for ScannerFactory
"""
import pytest
from unittest.mock import Mock, MagicMock, patch

from core.scanner.factory import ScannerFactory
from core.scanner.base import BaseScanner
from tests.fixtures.mock_scanner import MockScanner


class TestScannerFactory:
    """Test cases for ScannerFactory"""
    
    def setup_method(self):
        """Reset factory state before each test"""
        ScannerFactory._scanner_classes.clear()
    
    def test_factory_register_scanner(self):
        """Test scanner registration"""
        ScannerFactory.register_scanner("test_type", MockScanner)
        assert "test_type" in ScannerFactory._scanner_classes
        assert ScannerFactory._scanner_classes["test_type"] == MockScanner
    
    @patch('core.scanner.factory._register_scanners')
    def test_factory_create_scanner_openshift(self, mock_register):
        """Test OpenShift scanner creation"""
        # Mock the registration
        try:
            from core.scanner.openshift_scanner import OpenShiftScanner
            ScannerFactory.register_scanner("openshift", OpenShiftScanner)
            config = {"cluster": "test-cluster"}
            scanner = ScannerFactory.create_scanner("openshift", config)
            assert isinstance(scanner, OpenShiftScanner)
        except ImportError:
            pytest.skip("OpenShiftScanner not available")
    
    def test_factory_create_scanner_unix(self):
        """Test Unix scanner creation"""
        try:
            from core.scanner.unix_scanner import UnixScanner
            ScannerFactory.register_scanner("unix", UnixScanner)
            config = {"hostname": "test.example.com", "username": "user"}
            scanner = ScannerFactory.create_scanner("unix", config)
            assert isinstance(scanner, UnixScanner)
        except ImportError:
            pytest.skip("UnixScanner not available")
    
    def test_factory_create_scanner_aws(self):
        """Test AWS scanner creation"""
        try:
            from core.scanner.cloud.aws_scanner import AWSScanner
            ScannerFactory.register_scanner("aws", AWSScanner)
            config = {"instance_id": "i-123", "region": "us-east-1"}
            scanner = ScannerFactory.create_scanner("aws", config)
            assert isinstance(scanner, AWSScanner)
        except ImportError:
            pytest.skip("AWSScanner not available")
    
    def test_factory_create_scanner_azure(self):
        """Test Azure scanner creation"""
        try:
            from core.scanner.cloud.azure_scanner import AzureScanner
            with patch('core.scanner.cloud.azure_scanner.AZURE_AVAILABLE', True):
                ScannerFactory.register_scanner("azure", AzureScanner)
                config = {
                    "resource_group": "test-rg",
                    "vm_name": "test-vm",
                    "subscription_id": "sub-123"
                }
                scanner = ScannerFactory.create_scanner("azure", config)
                assert isinstance(scanner, AzureScanner)
        except ImportError:
            pytest.skip("AzureScanner not available")
    
    def test_factory_create_scanner_gcp(self):
        """Test GCP scanner creation"""
        try:
            from core.scanner.cloud.gcp_scanner import GCPScanner
            with patch('core.scanner.cloud.gcp_scanner.GCP_AVAILABLE', True):
                ScannerFactory.register_scanner("gcp", GCPScanner)
                config = {
                    "project_id": "test-project",
                    "zone": "us-central1-a",
                    "instance_name": "test-instance"
                }
                scanner = ScannerFactory.create_scanner("gcp", config)
                assert isinstance(scanner, GCPScanner)
        except ImportError:
            pytest.skip("GCPScanner not available")
    
    def test_factory_create_scanner_cloud(self):
        """Test Cloud scanner creation (routing)"""
        try:
            from core.scanner.cloud_scanner import CloudScanner
            ScannerFactory.register_scanner("cloud", CloudScanner)
            with patch('core.scanner.cloud_scanner.AWSScanner') as mock_aws:
                mock_scanner = MagicMock()
                mock_aws.return_value = mock_scanner
                config = {"provider": "aws", "instance_id": "i-123"}
                scanner = ScannerFactory.create_scanner("cloud", config)
                assert isinstance(scanner, CloudScanner)
        except ImportError:
            pytest.skip("CloudScanner not available")
    
    def test_factory_create_scanner_not_registered(self):
        """Test unregistered scanner error"""
        with pytest.raises(ValueError, match="not registered"):
            ScannerFactory.create_scanner("nonexistent", {})
    
    def test_factory_case_insensitive(self):
        """Test case-insensitive deployment type matching"""
        ScannerFactory.register_scanner("test_type", MockScanner)
        
        # Test various case combinations
        config = {}
        scanner1 = ScannerFactory.create_scanner("test_type", config)
        scanner2 = ScannerFactory.create_scanner("TEST_TYPE", config)
        scanner3 = ScannerFactory.create_scanner("Test_Type", config)
        
        assert isinstance(scanner1, MockScanner)
        assert isinstance(scanner2, MockScanner)
        assert isinstance(scanner3, MockScanner)
    
    def test_factory_get_available_types(self):
        """Test getting available scanner types"""
        ScannerFactory._scanner_classes.clear()
        ScannerFactory.register_scanner("type1", MockScanner)
        ScannerFactory.register_scanner("type2", MockScanner)
        
        available = ScannerFactory.get_available_types()
        assert "type1" in available
        assert "type2" in available
    
    def test_factory_is_type_supported(self):
        """Test checking if type is supported"""
        ScannerFactory._scanner_classes.clear()
        ScannerFactory.register_scanner("supported", MockScanner)
        
        assert ScannerFactory.is_type_supported("supported") is True
        assert ScannerFactory.is_type_supported("SUPPORTED") is True  # Case insensitive
        assert ScannerFactory.is_type_supported("not_supported") is False

