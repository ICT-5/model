from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..core.config import get_setting

settings = get_setting()

SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
