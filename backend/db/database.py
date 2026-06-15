import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

IS_VERCEL = os.environ.get("VERCEL", False)

if not DATABASE_URL:
    if IS_VERCEL:
        DATABASE_URL = "sqlite:////tmp/memory.db"
    else:
        DATABASE_URL = "sqlite:///./memory.db"

# For SQLite, we need connect_args
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, index=True)
    extracted_text = Column(Text, nullable=True)
    image_description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tags = relationship("Tag", back_populates="screenshot")
    embeddings = relationship("Embedding", back_populates="screenshot")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"))
    tag_name = Column(String, index=True)
    
    screenshot = relationship("Screenshot", back_populates="tags")

class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    screenshot_id = Column(Integer, ForeignKey("screenshots.id"))
    # We will use text-based storage for now or vector type if available
    # pgvector can be used directly with 'vector' type in SQL
    vector = Column(Text) # Storing as string representation for simplicity in SQLAlchemy without extension
    
    screenshot = relationship("Screenshot", back_populates="embeddings")

def init_db():
    Base.metadata.create_all(bind=engine)
    # Ensure pgvector extension is enabled (PostgreSQL ONLY)
    if not DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        try:
            with engine.begin() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                print("pgvector extension enabled.")
        except Exception as e:
            print(f"Warning: Could not enable pgvector extension: {e}")
            print("Falling back to in-memory similarity search for local development.")
