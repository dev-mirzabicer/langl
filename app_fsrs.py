# fsrs.py
from fsrs import Scheduler, Card, Rating, State
from datetime import datetime, timezone
from models import Vocabulary, ReviewHistory, WordList
from sqlalchemy.orm import Session
from sqlalchemy import and_
from flask import current_app


class FSRS_Service:
    def __init__(self, db_service):
        self.db_service = db_service
        self.scheduler = Scheduler()  # Load custom parameters here if needed

    def add_word(self, word: str, language: str, translation: str = ""):
        """
        Adds a new word to the database as a new FSRS card if it doesn't exist.
        """
        session: Session = self.db_service.get_session()
        try:
            # Normalize to lowercase
            word_lower = word.lower()
            lang_lower = language.lower()

            existing = session.get(Vocabulary, (word_lower, lang_lower))
            if existing:
                # Word already in vocab; optionally we update translation if it's empty
                if not existing.translation and translation:
                    existing.translation = translation.lower()
                    session.commit()
                return

            # If no translation is provided, let's fetch it from dictionary
            final_translation = translation.strip().lower()
            if not final_translation:
                # We'll call the dictionary logic directly or reuse the translation service
                try:
                    fetched = current_app.translation_service.translate(
                        word, source_lang=language.upper(), target_lang="EN"
                    )
                    final_translation = fetched.lower()
                except Exception as e:
                    print(f"Warning: Could not fetch translation: {str(e)}")
                    final_translation = ""

            # Create a new FSRS card
            card = Card()

            # Initialize Vocabulary entry without setting stability and difficulty
            vocab = Vocabulary(
                word=word_lower,
                language=lang_lower,
                translation=final_translation if final_translation else None,
                state=State.Learning.value,  # 1
                step=0,
                stability=None,  # Changed: Do not set, let FSRS initialize
                difficulty=None,  # Changed: Do not set, let FSRS initialize
                last_review=None,  # Never reviewed yet
                due=datetime.now(timezone.utc),  # Due immediately for first review
            )
            session.add(vocab)
            session.commit()
        finally:
            session.close()

    def review_word(self, word: str, language: str, user_rating: str):
        """
        Updates the FSRS card data for a word based on the user's rating.
        user_rating can be: "again", "hard", "good", "easy"
        Returns the updated Vocabulary object or None if not found.
        """
        rating_map = {
            "again": Rating.Again,
            "hard": Rating.Hard,
            "good": Rating.Good,
            "easy": Rating.Easy,
        }
        rating_key = user_rating.lower().strip()
        rating = rating_map.get(rating_key)
        if not rating:
            raise ValueError(
                f"Invalid user rating '{user_rating}'. Must be one of: again, hard, good, easy"
            )

        now = datetime.now(timezone.utc)

        session: Session = self.db_service.get_session()
        try:
            vocab = (
                session.query(Vocabulary)
                .filter(
                    and_(
                        Vocabulary.word == word.lower(),
                        Vocabulary.language == language.lower(),
                    )
                )
                .first()
            )
            if not vocab:
                return None

            # Ensure stability and difficulty are not negative if they are already set
            if vocab.stability is not None and vocab.stability < 0.0001:
                vocab.stability = 0.0001

            if vocab.difficulty is not None and vocab.difficulty < 0.0001:
                vocab.difficulty = 0.0001

            # Recreate FSRS Card from Vocabulary data
            card = Card(
                state=State(vocab.state),
                due=vocab.due,
                stability=vocab.stability,
                difficulty=vocab.difficulty,
                last_review=vocab.last_review,
                step=vocab.step,
            )

            # Update the card with the user's rating
            updated_card, review_log = self.scheduler.review_card(card, rating, now)

            # Prevent math domain errors if stability ended up <= 0
            if updated_card.stability is not None and updated_card.stability <= 0:
                updated_card.stability = 0.0001

            # Update Vocabulary with updated Card data
            vocab.state = updated_card.state.value
            vocab.due = updated_card.due
            vocab.stability = updated_card.stability
            vocab.difficulty = updated_card.difficulty
            vocab.last_review = updated_card.last_review
            vocab.step = updated_card.step

            # Log the review in ReviewHistory
            rh = ReviewHistory(
                review_time=now,
                word=word.lower(),
                language=language.lower(),
                rating=rating.value,
                state=updated_card.state.value,
            )
            session.add(rh)
            session.commit()
            return vocab
        finally:
            session.close()

    def get_words_due_for_review(self):
        """
        Returns all Vocabulary items whose due date is <= now
        """
        now = datetime.now(timezone.utc)
        session: Session = self.db_service.get_session()
        try:
            results = session.query(Vocabulary).filter(Vocabulary.due <= now).all()

            return [
                {"word": v.word, "language": v.language, "translation": v.translation}
                for v in results
            ]
        finally:
            session.close()

    def import_word_list(self, language: str, level: str, words: list[str]):
        """
        Inserts words into WordList, ignoring duplicates.
        """
        session: Session = self.db_service.get_session()
        try:
            for w in words:
                w_lower = w.lower()
                existing = (
                    session.query(WordList)
                    .filter(
                        and_(
                            WordList.language == language.lower(),
                            WordList.level == level.upper(),
                            WordList.word == w_lower,
                        )
                    )
                    .first()
                )
                if not existing:
                    wl = WordList(
                        language=language.lower(), level=level.upper(), word=w_lower
                    )
                    session.add(wl)
            session.commit()
        finally:
            session.close()

    def get_learning_list(self, language: str, level: str):
        """
        Returns all words from WordList for the given language & level.
        """
        session: Session = self.db_service.get_session()
        try:
            rows = (
                session.query(WordList)
                .filter_by(language=language.lower(), level=level.upper())
                .all()
            )

            return [r.word for r in rows]
        finally:
            session.close()

    def get_all_vocabulary(self):
        """
        Returns all vocab entries from user_vocabulary with FSRS fields in dictionary form.
        """
        session: Session = self.db_service.get_session()
        try:
            rows = session.query(Vocabulary).all()
            output = []
            for v in rows:
                output.append(
                    {
                        "word": v.word,
                        "language": v.language,
                        "translation": v.translation,
                        "state": v.state,
                        "due": v.due.isoformat() if v.due else None,
                        "stability": v.stability,
                        "difficulty": v.difficulty,
                        "last_review": (
                            v.last_review.isoformat() if v.last_review else None
                        ),
                        "step": v.step,
                    }
                )
            return output
        finally:
            session.close()
