# api/translation.py

from flask import Blueprint, request, jsonify, current_app
from http import HTTPStatus
import nltk
from nltk.stem import WordNetLemmatizer

translation_bp = Blueprint("translation_bp", __name__)

lemmatizer = WordNetLemmatizer()


@translation_bp.route("", methods=["POST"])
def translate_text():
    """
    POST /api/translation
    Expects JSON:
    {
      "text": "Jag älskar dig",
      "sourceLanguage": "SV",
      "targetLanguage": "EN",
      "splitSentences": true,
      "markWords": true
    }
    Returns JSON with:
    {
      "originalText": ...,
      "translatedText": ...,
      "alignment": ...,
      "sentences": [
        {
          "original": ...,
          "translated": ...,
          "src_tokenized": [...],
          "trg_tokenized": [...],
          "alignment": [(src_idx, trg_idx), ...],
          "wordInfo": [
            {
              "original_word": "Jag",
              "found_in_vocabulary": true/false,
              "match_type": "direct"/"lemma"/...,
              "vocabulary_entry": { ... } or null
            },
            ...
          ]
        },
        ...
      ]
    }
    """

    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), HTTPStatus.BAD_REQUEST

    text = data.get("text", "").strip()
    source_lang = data.get("sourceLanguage", "").upper()  # e.g. "SV"
    target_lang = data.get("targetLanguage", "").upper()  # e.g. "EN"
    split_sentences = data.get("splitSentences", True)
    mark_words = data.get("markWords", True)

    if not text:
        return (
            jsonify({"error": "Field 'text' cannot be empty."}),
            HTTPStatus.BAD_REQUEST,
        )

    try:
        # 1) Translate the full text from source_lang -> target_lang
        translated_text = current_app.translation_service.translate(
            text, source_lang=source_lang, target_lang=target_lang
        )

        # 2) Split text into sentences if requested
        if split_sentences:
            original_sentences = nltk.sent_tokenize(text)
            translated_sentences = nltk.sent_tokenize(translated_text)
        else:
            original_sentences = [text]
            translated_sentences = [translated_text]

        results = []
        # 3) For each (original, translated) sentence pair:
        for idx, (orig, tran) in enumerate(
            zip(original_sentences, translated_sentences)
        ):
            # Use alignment service to get tokenization & alignment
            align_data = current_app.alignment_service.align(orig, tran)
            # align_data = {
            #    "src_tokenized": [...],
            #    "trg_tokenized": [...],
            #    "alignment": [(src_idx, trg_idx), ...]
            # }

            # 4) If markWords == True, look up the source tokens in the vocabulary
            #    because the source language is the one we're learning
            word_info_list = []
            if mark_words:
                for token in align_data["src_tokenized"]:
                    info = current_app.vocabulary_lookup_service.lookup_word(
                        token, source_lang
                    )
                    # info has keys: "original_word", "found_in_vocabulary", "match_type", etc.
                    word_info_list.append(info)

            results.append(
                {
                    "original": orig,
                    "translated": tran,
                    "src_tokenized": align_data["src_tokenized"],
                    "trg_tokenized": align_data["trg_tokenized"],
                    "alignment": align_data["alignment"],
                    "wordInfo": word_info_list,
                }
            )

        # 5) Build the final response
        response_data = {
            "originalText": text,
            "translatedText": translated_text,
            "alignment": (
                [r["alignment"] for r in results]
                if split_sentences
                else results[0]["alignment"]
            ),
            "sentences": results if split_sentences else [results[0]],
        }

        # If not splitting, remove the array of sentences to keep it consistent
        if not split_sentences:
            del response_data["sentences"]

        return jsonify(response_data), HTTPStatus.OK

    except Exception as e:
        return jsonify({"error": str(e)}), HTTPStatus.INTERNAL_SERVER_ERROR
