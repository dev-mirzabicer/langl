# app.py
from flask import Flask
from flask_cors import CORS
from config import Config
from db import DBService
from api.translation import translation_bp
from api.fsrs import fsrs_bp
from api.dictionary import dictionary_bp
from alignment import AlignmentService
from translation import TranslationService
from app_fsrs import FSRS_Service
from vocabulary_lookup import VocabularyLookupService  # Import the new service
import nltk


def create_app():
    app = Flask(__name__)

    # Enable CORS for all routes
    CORS(app)

    # Initialize DB & create tables
    app.db_service = DBService()
    app.db_service.create_tables()

    # Initialize services
    app.translation_service = TranslationService()
    app.alignment_service = AlignmentService()
    app.fsrs_service = FSRS_Service(app.db_service)
    app.vocabulary_lookup_service = VocabularyLookupService(
        app.db_service
    )  # Initialize the new service

    with app.app_context():  # Ensure we have an application context
        nltk.download("punkt", quiet=True)
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)

    # Register Blueprints
    app.register_blueprint(translation_bp, url_prefix="/api/translation")
    app.register_blueprint(fsrs_bp, url_prefix="/api/fsrs")
    app.register_blueprint(dictionary_bp, url_prefix="/api/dictionary")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
