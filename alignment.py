# alignment.py
from simalign import SentenceAligner
import nltk


class AlignmentService:
    def __init__(self, model_name="bert", token_type="bpe", matching_methods="mai"):
        self.aligner = SentenceAligner(
            model=model_name, token_type=token_type, matching_methods=matching_methods
        )
        self.cache = {}

    def align(self, original: str, translated: str):
        """
        Returns alignment data:
        {
            'src_tokenized': [...],
            'trg_tokenized': [...],
            'alignment': [(src_idx, trg_idx), ...]
        }
        """
        if not original or not translated:
            return {"src_tokenized": [], "trg_tokenized": [], "alignment": []}

        cache_key = (original, translated)
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Tokenize sentences using nltk for consistency
        src_tokens = nltk.word_tokenize(original)
        trg_tokens = nltk.word_tokenize(translated)

        # Perform alignment
        try:
            alignments = self.aligner.get_word_aligns(src_tokens, trg_tokens)
        except Exception as e:
            raise RuntimeError(f"Alignment failed: {str(e)}")

        # print(src_tokens, trg_tokens, alignments, sep="\n")

        alignment_data = {
            "src_tokenized": src_tokens,
            "trg_tokenized": trg_tokens,
            "alignment": list(alignments["mwmf"]),  # Convert set to list
        }

        # Cache the result
        self.cache[cache_key] = alignment_data
        return alignment_data
