"""
Mock scanner implementations for testing
"""
from typing import Dict, Any
from core.scanner.base import BaseScanner, ScanResult


class MockScanner(BaseScanner):
    """Mock scanner for testing"""
    
    def __init__(self, config_dict: Dict[str, Any], connect_result: bool = True, 
                 execute_result: tuple = ("stdout", "stderr", 0)):
        super().__init__(config_dict)
        self.connect_result = connect_result
        self.execute_result = execute_result
        self.connect_called = False
        self.disconnect_called = False
        self.execute_command_called = False
        self.last_command = None
    
    def connect(self) -> bool:
        self.connect_called = True
        self.connected = self.connect_result
        return self.connect_result
    
    def disconnect(self):
        self.disconnect_called = True
        self.connected = False
    
    def execute_command(self, command: str) -> tuple:
        self.execute_command_called = True
        self.last_command = command
        return self.execute_result

