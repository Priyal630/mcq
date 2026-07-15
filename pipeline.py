# ============================================================================
# THREE-LAYER MCQ LOCALIZATION PIPELINE
#
# Layer 1: Translate natural language            -> sarvam-translate
# Layer 2: Protect + transliterate technical terms -> glossary + placeholder swap
# Layer 3: Fix MCQ sentence structure/mood        -> Qwen2.5-7B-Instruct
#
# Directly targets the 4 documented failure modes from Issues_with_Example.docx:
#   Issue 1 (technical words mistranslated)      -> fixed by Layer 2
#   Issue 2 (wrong letters/conjuncts)            -> mitigated by Layer 2
#       (transliteration via curated glossary avoids the broken phonetic
#        spelling the AI/Google Translate produced; for terms NOT yet in
#        the glossary, Layer 3's model is asked to use standard script
#        orthography, not phonetic guesswork)
#   Issue 3 (affirmative statement, not a question) -> fixed by Layer 3
#   Issue 4 (options not in matching noun form)      -> fixed by Layer 3
# ============================================================================

import re
import sys
import os

_GLOSSARY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "glossaries")
if _GLOSSARY_DIR not in sys.path:
    sys.path.insert(0, _GLOSSARY_DIR)
from glossary import lookup
from term_detector import scan_row

LANG_CODES = {"Hindi": "hi", "Marathi": "mr", "Gujarati": "gu"}

PLACEHOLDER_PATTERN = re.compile(r"\[\[TERM(\d+)\]\]")


def protect_terms(text: str, confirmed_terms: list):
    """
    Layer 2 step A: replace each confirmed technical term in `text` with a
    numbered placeholder ([[TERM0]], [[TERM1]], ...) so the translation
    model (Layer 1) cannot touch it. Returns (protected_text, term_map)
    where term_map maps placeholder index -> original English term.

    confirmed_terms should be ordered longest-first by the caller to avoid
    partial-substring collisions (e.g. "expansion gap" before "expansion").
    """
    term_map = {}
    protected = text
    for i, term in enumerate(confirmed_terms):
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(protected):
            placeholder = f"[[TERM{i}]]"
            protected = pattern.sub(placeholder, protected, count=1)
            term_map[str(i)] = term
    return protected, term_map


def restore_terms(translated_text: str, term_map: dict, lang_code: str):
    """
    Layer 2 step B: replace [[TERMn]] placeholders in the TRANSLATED text
    with the transliterated form of the original English term, pulled from
    the glossary. If a term isn't in the glossary yet, falls back to
    leaving the original English term in Latin script (safer than guessing
    a phonetic spelling that risks Issue 2 -- wrong conjuncts/letters).
    """
    def _replace(match):
        idx = match.group(1)
        original_term = term_map.get(idx, "")
        translit = lookup(original_term, lang_code)
        if translit:
            return translit
        # Not in glossary: keep original English term untranslated/untouched
        # rather than risk a broken phonetic guess (per documented Issue 2).
        return original_term

    return PLACEHOLDER_PATTERN.sub(_replace, translated_text)


def get_row_term_candidates(question: str, options: list):
    """Layer 2 step (pre-step): surface candidate terms for human review."""
    return scan_row(question, options)


def build_layer1_request(question: str, options: list, confirmed_terms: list):
    """
    Prepares the term-protected stem + options ready to send to
    sarvam-translate (Layer 1). Returns:
        protected_question, protected_options (list), term_map
    Term map is shared across stem + all options so the same placeholder
    numbering is consistent everywhere in the row.
    """
    # Sort longest-first to avoid "expansion" matching inside "expansion gap"
    ordered_terms = sorted(set(confirmed_terms), key=len, reverse=True)

    combined_term_map = {}
    next_idx = 0
    protected_question = question
    for term in ordered_terms:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        if pattern.search(protected_question):
            placeholder = f"[[TERM{next_idx}]]"
            protected_question = pattern.sub(placeholder, protected_question, count=1)
            combined_term_map[str(next_idx)] = term
            next_idx += 1

    protected_options = []
    for opt in options:
        if not opt:
            protected_options.append(opt)
            continue
        protected_opt = opt
        for term in ordered_terms:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            if pattern.search(protected_opt):
                placeholder = f"[[TERM{next_idx}]]"
                protected_opt = pattern.sub(placeholder, protected_opt, count=1)
                combined_term_map[str(next_idx)] = term
                next_idx += 1
        protected_options.append(protected_opt)

    return protected_question, protected_options, combined_term_map


def restore_row_terms(translated_question: str, translated_options: list, term_map: dict, language: str):
    lang_code = LANG_CODES.get(language, "hi")
    restored_question = restore_terms(translated_question, term_map, lang_code)
    restored_options = [
        restore_terms(opt, term_map, lang_code) if opt else opt
        for opt in translated_options
    ]
    return restored_question, restored_options


# ----------------------------------------------------------------------------
# Layer 3 prompt — MCQ structure/mood fix
# ----------------------------------------------------------------------------

LAYER3_SYSTEM_PROMPT = """You are an expert editor for multiple-choice hiring-assessment questions in {language}.

You will receive a question stem and its answer options that have ALREADY been translated from English into {language}. Your ONLY job is to fix grammatical structure — you must NOT change meaning, difficulty, or which option is correct.

THE SPECIFIC PROBLEM YOU ARE FIXING:
English assessment questions are often written as incomplete affirmative sentences, where the options grammatically complete the sentence. For example: "Module installation is done to reduce ____" with options like "heat loss" / "manpower". When this is translated literally into {language}, it often becomes a complete DECLARATIVE STATEMENT (e.g. something that reads as "Module installation has been done to reduce [X]" — a finished statement, not a question). The test-taker can no longer tell it's a question at all.

YOUR TASK:
1. Rewrite the {language} question stem so it unambiguously reads as a QUESTION (interrogative mood) — using a question word (क्या/काय/શું etc. as appropriate) or a clear blank-marker, NOT a finished declarative statement.
2. Make sure each option remains grammatically consistent with the question — options should stay in noun-phrase form if the original English options were noun phrases (e.g. "heat loss", not a full sentence like "to reduce heat loss"). Do not convert noun-phrase options into imperative/verb-form phrases.
3. Do NOT change any technical term that appears inside [[TERM]] markers or any term you recognize as a brand/technical/proper noun already in the target script — leave those exactly as given to you.
4. Do NOT add new information, do NOT change which option is correct, do NOT change the number of options.
5. Output ONLY valid JSON, nothing else, no markdown fences, no explanation:

{{"question": "<fixed question stem>", "options": ["<fixed option 1>", "<fixed option 2>", ...]}}

The user's next message contains the question and options to fix, as JSON."""


def build_layer3_user_message(question: str, options: list):
    import json
    return json.dumps({"question": question, "options": [o for o in options if o]}, ensure_ascii=False)


def build_layer3_messages(language: str, question: str, options: list):
    system = LAYER3_SYSTEM_PROMPT.format(language=language)
    user = build_layer3_user_message(question, options)
    return system, user
