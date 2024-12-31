# api/fsrs.py
from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus

fsrs_bp = Blueprint("fsrs_bp", __name__)


@fsrs_bp.route("/update", methods=["POST"])
def update_fsrs_data():
    """
    POST /api/fsrs/update
    Expects JSON:
    {
      "word": "example",
      "language": "sv",
      "response": "good"  // again|hard|good|easy
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), HTTPStatus.BAD_REQUEST

    word = data.get("word")
    language = data.get("language")
    response = data.get("response")

    # Validate input
    if not word or not language or not response:
        return (
            jsonify({"error": "Required fields: word, language, response"}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        updated_vocab = current_app.fsrs_service.review_word(word, language, response)
        if not updated_vocab:
            return (
                jsonify({"error": "Word not found in vocabulary"}),
                HTTPStatus.NOT_FOUND,
            )

        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"FSRS data updated for word '{word}'.",
                }
            ),
            HTTPStatus.OK,
        )

    except ValueError as ve:
        return jsonify({"error": str(ve)}), HTTPStatus.BAD_REQUEST
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/review", methods=["GET"])
def get_review_words():
    """
    GET /api/fsrs/review
    Returns JSON of words that are due for review
    """
    try:
        words = current_app.fsrs_service.get_words_due_for_review()
        return jsonify({"words": words}), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/vocabulary/import", methods=["POST"])
def import_wordlist():
    """
    POST /api/fsrs/vocabulary/import
    Expects JSON:
    {
      "language": "sv",
      "level": "A1",
      "wordList": ["hej", "tack", "snälla"]
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), HTTPStatus.BAD_REQUEST

    language = data.get("language")
    level = data.get("level")
    word_list = data.get("wordList") or []

    # Validate input
    if not language or not level or not isinstance(word_list, list):
        return (
            jsonify(
                {
                    "error": "Fields 'language', 'level' and 'wordList' (as list) are required."
                }
            ),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        current_app.fsrs_service.import_word_list(language, level, word_list)
        return (
            jsonify(
                {
                    "status": "success",
                    "message": f"Word list imported for language '{language.upper()}', level '{level.upper()}'.",
                }
            ),
            HTTPStatus.OK,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/vocabulary/learning_list", methods=["GET"])
def get_learning_list():
    """
    GET /api/fsrs/vocabulary/learning_list?language=sv&level=A1
    """
    language = request.args.get("language")
    level = request.args.get("level")

    # Validate input
    if not language or not level:
        return (
            jsonify({"error": "Query parameters 'language' and 'level' are required."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        words = current_app.fsrs_service.get_learning_list(language, level)
        return jsonify({"words": words}), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/vocabulary", methods=["GET"])
def get_vocabulary():
    """
    GET /api/fsrs/vocabulary
    Returns the full user vocabulary with FSRS fields.
    """
    try:
        vocab = current_app.fsrs_service.get_all_vocabulary()
        return jsonify({"words": vocab}), HTTPStatus.OK
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/vocabulary/add", methods=["POST"])
def add_word():
    """
    POST /api/fsrs/vocabulary/add
    Expects JSON:
    {
      "word": "minnas",
      "language": "sv",
      "translation": "to remember"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), HTTPStatus.BAD_REQUEST

    word = data.get("word")
    language = data.get("language")
    translation = data.get("translation") or ""

    # Validate input
    if not word or not language:
        return (
            jsonify({"error": "Fields 'word' and 'language' are required."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        current_app.fsrs_service.add_word(word, language, translation)
        return (
            jsonify(
                {"status": "success", "message": f"Word '{word}' added to vocabulary."}
            ),
            HTTPStatus.OK,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR


@fsrs_bp.route("/vocabulary/lookup", methods=["GET"])
def lookup_fsrs_word():
    """
    GET /api/fsrs/vocabulary/lookup?word=...&language=...
    Returns JSON:
    {
        "word": "älskar",
        "language": "sv",
        "translation": "love",
        "state": 1,
        "due": "...",
        "stability": 0.0,
        "difficulty": 0.0,
        "last_review": "...",
        "step": 0
    }
    or 404 if not found
    """
    from models import Vocabulary

    word = request.args.get("word", "").strip().lower()
    language = request.args.get("language", "").strip().lower()

    if not word or not language:
        return (
            jsonify({"error": "Missing 'word' or 'language' query parameter"}),
            HTTPStatus.BAD_REQUEST,
        )

    session = current_app.db_service.get_session()
    try:
        vocab = session.get(Vocabulary, (word, language))
        if not vocab:
            return jsonify({"error": "Not found"}), HTTPStatus.NOT_FOUND

        return (
            jsonify(
                {
                    "word": vocab.word,
                    "language": vocab.language,
                    "translation": vocab.translation,
                    "state": vocab.state,
                    "due": vocab.due.isoformat() if vocab.due else None,
                    "stability": vocab.stability,
                    "difficulty": vocab.difficulty,
                    "last_review": (
                        vocab.last_review.isoformat() if vocab.last_review else None
                    ),
                    "step": vocab.step,
                }
            ),
            HTTPStatus.OK,
        )

    finally:
        session.close()
