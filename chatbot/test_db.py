from app.database import Database
from app.models.user import Base

# Create database instance
db = Database()

try:
    # Try to create all tables
    Base.metadata.create_all(db.engine)
    print("Database connection successful!")
    print("Tables created successfully!")
except Exception as e:
    print("Database connection failed!")
    print(f"Error: {str(e)}")
