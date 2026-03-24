from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(72), unique=True, nullable=False)
    image = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    host_port = Column(Integer, nullable=False)
    container_port = Column(Integer, default=80)
    status = Column(String(32), default="running")
    created_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
