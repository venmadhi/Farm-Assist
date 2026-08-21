from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# For SQLite, we need connect_args={"check_same_thread": False}
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    # If MySQL, ensure the database exists
    if settings.DATABASE_URL.startswith("mysql"):
        try:
            import pymysql
            from urllib.parse import urlparse
            url = urlparse(settings.DATABASE_URL)
            db_name = url.path.lstrip('/')
            
            # Connect to MySQL server (without database name)
            conn = pymysql.connect(
                host=url.hostname or 'localhost',
                user=url.username or 'root',
                password=url.password or 'root',
                port=url.port or 3306
            )
            try:
                with conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            print(f"Warning: Could not check/create MySQL database: {e}")

    engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
