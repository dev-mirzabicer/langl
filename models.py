# models.py
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Vocabulary(Base):
    """
    Represents a single word in the user's vocabulary, with FSRS data attached.
    """

    __tablename__ = "user_vocabulary"

    word = Column(String, primary_key=True)
    language = Column(String, primary_key=True)
    translation = Column(String, nullable=True)

    # FSRS fields
    state = Column(
        Integer, nullable=False, default=1
    )  # 1=Learning, 2=Review, 3=Relearning
    due = Column(DateTime, nullable=True)
    stability = Column(Float, nullable=True)  # Changed: Allow NULL, removed default
    difficulty = Column(Float, nullable=True)  # Changed: Allow NULL, removed default
    last_review = Column(DateTime, nullable=True, default=None)
    step = Column(Integer, default=0)

    # Relationships
    reviews = relationship(
        "ReviewHistory", back_populates="vocabulary", cascade="all, delete-orphan"
    )


class ReviewHistory(Base):
    """
    Detailed logs for each review event, used for FSRS optimization or analytics.
    """

    __tablename__ = "review_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    word = Column(String, nullable=False)
    language = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    state = Column(Integer, nullable=True)  # 1=Learning, 2=Review, 3=Relearning

    # Composite Foreign Key Constraint
    __table_args__ = (
        ForeignKeyConstraint(
            ["word", "language"], ["user_vocabulary.word", "user_vocabulary.language"]
        ),
    )

    # Relationships
    vocabulary = relationship(
        "Vocabulary", back_populates="reviews", foreign_keys=[word, language]
    )


class WordList(Base):
    """
    Stores initial words (like A1, A2 lists) for import.
    """

    __tablename__ = "word_lists"
    language = Column(String, primary_key=True)
    level = Column(String, primary_key=True)
    word = Column(String, primary_key=True)
