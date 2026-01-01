"""
Setup script for JDK Compliance Scanner Backend
"""
from setuptools import setup, find_packages

setup(
    name="jdk-compliance-scanner-backend",
    version="1.0.0",
    description="JDK Compliance Scanner Backend API",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.23",
        "alembic>=1.12.1",
        "pyjwt>=2.8.0",
        "passlib[bcrypt]>=1.7.4",
        "python-jose[cryptography]>=3.3.0",
        "cryptography>=41.0.7",
        "kubernetes>=28.1.0",
        "reportlab>=4.0.7",
        "openpyxl>=3.1.2",
        "jinja2>=3.1.2",
        "weasyprint>=60.1",
        "aiosmtplib>=3.0.1",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dateutil>=2.8.2",
        "python-json-logger>=2.0.7",
        "python-multipart>=0.0.6",
    ],
)

