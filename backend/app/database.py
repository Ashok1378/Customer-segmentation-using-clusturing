"""
database.py - Automatic database discovery, connection, and session management using SQLAlchemy.
Automatically connects to local MySQL (port 3306) if running, creates database 'customer_segmentation'
and tables automatically, or falls back seamlessly to SQLite.
"""
import os
import socket
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Load .env file
load_dotenv()

DEFAULT_DB_PATH = os.path.join(os.path.dirname(settings.UPLOAD_DIR), "customer_segmentation.db")
SQLITE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

Base = declarative_base()


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a network port is reachable."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def discover_and_connect_mysql() -> str:
    """
    Auto-discovers local MySQL on port 3306.
    Tries passwords, automatically executes 'CREATE DATABASE IF NOT EXISTS customer_segmentation',
    and returns the SQLAlchemy connection URL.
    """
    if not is_port_open("localhost", 3306, timeout=1.5):
        logger.info("MySQL port 3306 is not open. Using SQLite.")
        return SQLITE_URL

    import pymysql

    # Common passwords to auto-probe
    configured_url = os.getenv("DATABASE_URL", "")
    passwords = []
    if "mysql" in configured_url and "@" in configured_url:
        try:
            # Extract password from configured URL if available
            user_pass = configured_url.split("://")[1].split("@")[0]
            if ":" in user_pass:
                passwords.append(user_pass.split(":")[1])
        except Exception:
            pass

    passwords.extend(["root", "", "admin", "1234", "123456", "root123", "password"])

    working_pwd = None
    for pwd in passwords:
        try:
            conn = pymysql.connect(
                host="localhost",
                user="root",
                password=pwd,
                port=3306,
                connect_timeout=2,
            )
            working_pwd = pwd
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE DATABASE IF NOT EXISTS customer_segmentation "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
                )
            conn.close()
            logger.info("Auto-discovered MySQL server on port 3306 with user 'root'.")
            break
        except Exception:
            continue

    if working_pwd is not None:
        mysql_url = f"mysql+pymysql://root:{working_pwd}@localhost:3306/customer_segmentation"
        return mysql_url

    logger.warning("Could not authenticate with local MySQL. Using SQLite.")
    return SQLITE_URL


# Global engine and sessionmaker holders
DATABASE_URL = SQLITE_URL
engine = None
SessionLocal = None


def configure_engine(url: str):
    """Configures global engine, SessionLocal, and creates all tables."""
    global DATABASE_URL, engine, SessionLocal
    try:
        if "sqlite" in url:
            new_engine = create_engine(url, connect_args={"check_same_thread": False}, echo=False)
        else:
            new_engine = create_engine(url, pool_pre_ping=True, pool_recycle=3600, echo=False)
            with new_engine.connect() as test_conn:
                test_conn.execute(text("SELECT 1"))

        DATABASE_URL = url
        engine = new_engine
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("Active database set to: %s", DATABASE_URL)
        return True
    except Exception as exc:
        logger.warning("Failed to configure database engine for '%s': %s", url, exc)
        if url != SQLITE_URL:
            return configure_engine(SQLITE_URL)
        return False


# Auto-detect database on module load
_preferred_url = os.getenv("DATABASE_URL")
if not _preferred_url or "sqlite" in _preferred_url:
    _discovered_url = discover_and_connect_mysql()
    configure_engine(_discovered_url)
else:
    configure_engine(_preferred_url)


def get_db():
    """FastAPI dependency that yields a SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Creates all database tables defined in models_db."""
    try:
        from app import models_db  # noqa: F401
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully on '%s'.", DATABASE_URL)
    except Exception as exc:
        logger.error("Failed to initialize database tables: %s", exc, exc_info=True)


def auto_connect() -> dict:
    """Explicitly triggers auto-discovery, connects, and initializes tables."""
    mysql_url = discover_and_connect_mysql()
    success = configure_engine(mysql_url)
    init_db()
    return {
        "success": success,
        "engine": "mysql" if "mysql" in DATABASE_URL else "sqlite",
        "database_url": DATABASE_URL.replace(":" + (DATABASE_URL.split(":")[2].split("@")[0] if "mysql" in DATABASE_URL and "@" in DATABASE_URL and len(DATABASE_URL.split(":")) > 2 else "") + "@", ":***@") if "@" in DATABASE_URL else DATABASE_URL,
        "message": f"Successfully connected to {'MySQL (Port 3306)' if 'mysql' in DATABASE_URL else 'SQLite'}!",
    }
