"""
Database setup/teardown utilities for tests
"""
from sqlalchemy.orm import Session
from core.database.models import Base


def setup_test_db(session: Session):
    """Setup test database schema"""
    Base.metadata.create_all(bind=session.bind)


def teardown_test_db(session: Session):
    """Teardown test database schema"""
    Base.metadata.drop_all(bind=session.bind)

