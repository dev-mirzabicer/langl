# api/dictionary.py

from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus

dictionary_bp = Blueprint("dictionary_bp", __name__)


@dictionary_bp.route("/lookup", methods=["GET"])
def lookup_word():
    """
    GET /api/dictionary/lookup?word=...&language=...
    Returns JSON:
      {
        "word": "...",
        "language": "...",
        "translation": "..."
      }

    We can rely on current_app.translation_service.translate(...)
    or a specialized dictionary API call if you prefer.
    """
    word = request.args.get("word", "").strip()
    language = request.args.get("language", "").strip()  # e.g., "sv"

    if not word or not language:
        return (
            jsonify({"error": "Missing 'word' or 'language' query param"}),
            HTTPStatus.BAD_REQUEST,
        )

    # Let's call the existing translationService with target_lang=EN for simplicity,
    # or you can do a specialized dictionary approach.
    try:
        # We'll do a minimal 1-word translation, sourceLang= e.g. 'SV', targetLang='EN'
        translated = current_app.translation_service.translate(
            word, source_lang=language.upper(), target_lang="EN"
        )
        return (
            jsonify({"word": word, "language": language, "translation": translated}),
            HTTPStatus.OK,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
