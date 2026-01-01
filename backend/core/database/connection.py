"""
Database connection manager for SQLite
"""
import os
from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseManager:
    """Manages database connection"""
    
    def __init__(self, db_path: str, db_password: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            db_path: Path to SQLite database file
            db_password: Database password (for future encryption support)
        """
        self.db_path = db_path
        self.db_password = db_password or os.getenv("DB_PASSWORD", "")
        
        # Ensure database directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, mode=0o755)
        
        # Create SQLite connection string
        connection_string = f"sqlite:///{self.db_path}"
        
        # Create engine
        self.engine = create_engine(
            connection_string,
            connect_args={
                'check_same_thread': False
            },
            poolclass=StaticPool,
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Initialize database (create tables)
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get database session as generator (for FastAPI dependency injection)
        
        Usage:
            db = next(db_manager.get_session())
            try:
                # Use db session
                db.commit()
            finally:
                db.close()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db_manager = get_db_manager()
    yield from db_manager.get_session()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create the global database manager instance"""
    global _db_manager
    if _db_manager is None:
        db_path = os.getenv("DB_PATH", "data/compliance.db")
        db_manager = DatabaseManager(db_path)
        _db_manager = db_manager
    return _db_manager


def set_db_manager(db_manager: DatabaseManager):
    """Set the global database manager instance"""
    global _db_manager
    _db_manager = db_manager


def init_database(db_path: str, db_password: str) -> DatabaseManager:
    """
    Initialize database manager with given path and password
    
    Args:
        db_path: Path to database file
        db_password: Database password
        
    Returns:
        DatabaseManager instance
    """
    db_manager = DatabaseManager(db_path, db_password)
    set_db_manager(db_manager)
    return db_manager

