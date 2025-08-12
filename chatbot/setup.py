from setuptools import setup, find_packages

setup(
    name="chatbot",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.111.0",
        "pydantic>=2.7.0",
        "pydantic-settings>=2.2.0",  # Pydantic v2 설정 관리를 위해 추가
        "uvicorn[standard]>=0.29.0",
        "SQLAlchemy>=2.0.0",
        "pymysql>=1.1.0",
        "email-validator>=2.0.0",
        "python-multipart",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "alembic>=1.13.0",
    ],
)
