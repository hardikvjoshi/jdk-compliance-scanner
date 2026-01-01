"""
Encryption utilities for database and credentials
"""
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
from typing import Optional


class EncryptionManager:
    """Manages encryption/decryption for credentials and sensitive data"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption manager
        
        Args:
            encryption_key: Base64-encoded Fernet key. If None, will use key from env var
                           or generate from password
        """
        if encryption_key:
            self.key = encryption_key.encode() if isinstance(encryption_key, str) else encryption_key
        else:
            # Try to get from environment variable
            key_from_env = os.getenv("ENCRYPTION_KEY")
            if key_from_env:
                self.key = key_from_env.encode()
            else:
                # Generate key from password if available
                password = os.getenv("ENCRYPTION_PASSWORD", "default_password_change_in_production")
                self.key = self._derive_key_from_password(password)
        
        self.fernet = Fernet(self.key)
    
    @staticmethod
    def _derive_key_from_password(password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive a Fernet key from a password"""
        if salt is None:
            salt = b'jdk_compliance_scanner_salt'  # Should be unique per installation
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        key = Fernet.generate_key()
        return key.decode()
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string"""
        if not data:
            return data
        encrypted_bytes = self.fernet.encrypt(data.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt a string"""
        if not encrypted_data:
            return encrypted_data
        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {str(e)}")


# Global encryption manager instance
_encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """Get or create the global encryption manager instance"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def set_encryption_manager(manager: EncryptionManager):
    """Set the global encryption manager instance"""
    global _encryption_manager
    _encryption_manager = manager

