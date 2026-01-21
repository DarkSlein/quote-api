from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, ForeignKey,
    Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, declarative_base
import uuid

Base = declarative_base()


class AuthorModel(Base):
    __tablename__ = "authors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    quotes = relationship("QuoteModel", back_populates="author")
    
    __table_args__ = (
        Index("idx_author_name", "name"),
        Index("idx_author_years", "birth_year", "death_year"),
    )


class CategoryModel(Base):
    __tablename__ = "categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    quotes = relationship("QuoteModel", back_populates="category")


class EraModel(Base):
    __tablename__ = "eras"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    
    quotes = relationship("QuoteModel", back_populates="era")


class QuoteModel(Base):
    __tablename__ = "quotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("authors.id"), nullable=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=True)
    era_id = Column(UUID(as_uuid=True), ForeignKey("eras.id"), nullable=True)
    source = Column(String(500), nullable=True)
    language = Column(String(10), default="ru")
    rating = Column(Integer, default=0)
    created_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    author = relationship("AuthorModel", back_populates="quotes")
    category = relationship("CategoryModel", back_populates="quotes")
    era = relationship("EraModel", back_populates="quotes")
    stats = relationship("QuoteStatsModel", back_populates="quote", uselist=False)
    
    __table_args__ = (
        UniqueConstraint("text", "author_id", name="uq_quote_text_author"),
        Index("idx_quote_text", "text"),
        Index("idx_quote_rating", "rating"),
        Index("idx_quote_created", "created_at"),
        Index("idx_quote_language", "language"),
        CheckConstraint("rating >= 0", name="ck_quote_rating_non_negative"),
        CheckConstraint("length(text) >= 10", name="ck_quote_text_length"),
    )


class QuoteStatsModel(Base):
    __tablename__ = "quote_stats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), unique=True)
    views = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    last_viewed = Column(TIMESTAMP(timezone=True), nullable=True)
    
    quote = relationship("QuoteModel", back_populates="stats")


class UpdateLogModel(Base):
    __tablename__ = "update_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(100), nullable=False)
    quotes_added = Column(Integer, default=0)
    quotes_updated = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(20), nullable=False)  # success, partial, failed
    error_message = Column(Text, nullable=True)
    executed_at = Column(TIMESTAMP(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_ms = Column(Integer, nullable=True)
    
    __table_args__ = (
        Index("idx_update_log_source", "source_name"),
        Index("idx_update_log_date", "executed_at"),
    )