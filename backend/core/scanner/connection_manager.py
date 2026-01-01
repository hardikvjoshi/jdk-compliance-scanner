"""
Connection Manager - Shared component for handling different connection types (DRY)
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class Connection(ABC):
    """Abstract connection interface"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Close connection"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class ConnectionManager:
    """
    Manages connections for different deployment types
    Shared component for all scanners (DRY principle)
    """
    
    _connection_cache: Dict[str, Connection] = {}
    
    @staticmethod
    def create_connection(connection_type: str, config: Dict[str, Any]) -> Connection:
        """
        Create a connection instance
        
        Args:
            connection_type: Type of connection (OpenShift, SSH, WinRM, Cloud)
            config: Connection configuration
            
        Returns:
            Connection instance
        """
        # This will be implemented by specific connection classes
        # For now, return None - connections will be created by scanners
        raise NotImplementedError(
            f"Connection type '{connection_type}' not yet implemented. "
            "Connections are currently managed directly by scanner implementations."
        )
    
    @staticmethod
    def get_cached_connection(connection_id: str) -> Optional[Connection]:
        """
        Get cached connection if available
        
        Args:
            connection_id: Unique connection identifier
            
        Returns:
            Cached Connection or None
        """
        return ConnectionManager._connection_cache.get(connection_id)
    
    @staticmethod
    def cache_connection(connection_id: str, connection: Connection):
        """
        Cache a connection for reuse
        
        Args:
            connection_id: Unique connection identifier
            connection: Connection instance to cache
        """
        ConnectionManager._connection_cache[connection_id] = connection
    
    @staticmethod
    def clear_cache():
        """Clear all cached connections"""
        for connection in ConnectionManager._connection_cache.values():
            if connection.is_connected():
                connection.disconnect()
        ConnectionManager._connection_cache.clear()

