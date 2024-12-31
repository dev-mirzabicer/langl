# vocabulary_lookup.py
from nltk.stem import WordNetLemmatizer
from db import DBService
from sqlalchemy.orm import Session


class VocabularyLookupService:
    def __init__(self, db_service: DBService):
        self.db_service = db_service
        self.lemmatizer = WordNetLemmatizer()

    def lookup_word(self, word: str, language: str):
        session: Session = self.db_service.get_session()
        try:
            from models import Vocabulary

            # Direct match (case-insensitive)
            direct_match = (
                session.query(Vocabulary)
                .filter(
                    Vocabulary.word.ilike(word), Vocabulary.language.ilike(language)
                )
                .first()
            )

            if direct_match:
                return {
                    "original_word": word,
                    "found_in_vocabulary": True,
                    "match_type": "direct",
                    "vocabulary_entry": {
                        "word": direct_match.word,
                        "language": direct_match.language,
                        "translation": direct_match.translation,
                        "state": direct_match.state,
                        "due": (
                            direct_match.due.isoformat() if direct_match.due else None
                        ),
                        "stability": direct_match.stability,
                        "difficulty": direct_match.difficulty,
                        "last_review": (
                            direct_match.last_review.isoformat()
                            if direct_match.last_review
                            else None
                        ),
                        "step": direct_match.step,
                    },
                }

            # Lemmatization match
            lemma = self.lemmatizer.lemmatize(word.lower())
            lemma_match = (
                session.query(Vocabulary)
                .filter(
                    Vocabulary.word.ilike(lemma), Vocabulary.language.ilike(language)
                )
                .first()
            )

            if lemma_match:
                return {
                    "original_word": word,
                    "found_in_vocabulary": True,
                    "match_type": "lemma",
                    "vocabulary_entry": {
                        "word": lemma_match.word,
                        "language": lemma_match.language,
                        "translation": lemma_match.translation,
                        "state": lemma_match.state,
                        "due": lemma_match.due.isoformat() if lemma_match.due else None,
                        "stability": lemma_match.stability,
                        "difficulty": lemma_match.difficulty,
                        "last_review": (
                            lemma_match.last_review.isoformat()
                            if lemma_match.last_review
                            else None
                        ),
                        "step": lemma_match.step,
                    },
                }

            # No match found
            return {
                "original_word": word,
                "found_in_vocabulary": False,
                "match_type": "none",
                "vocabulary_entry": None,
            }
        except Exception as e:
            # Log the exception as needed
            print(f"Error during vocabulary lookup: {str(e)}")
            return {
                "original_word": word,
                "found_in_vocabulary": False,
                "match_type": "error",
                "vocabulary_entry": None,
            }
        finally:
            session.close()
