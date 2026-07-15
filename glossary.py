# ============================================================================
# DOMAIN TERM GLOSSARY — terms to TRANSLITERATE, never semantically translate
#
# This is the fix for documented Issue 1 and Issue 4 from Issues_with_Example.docx:
#   "Refractory is not an original [target language] word... My proposed
#    solution: Instead of translating the technical words, 'Transliterate'
#    this... For example: 'Refractory' transliteration would be रिफ्रैक्टरी
#    in Hindi."
#
# Format: english_term -> {hindi, marathi, gujarati}
# Transliterations follow standard phonetic mapping (how the word SOUNDS),
# not semantic translation (what the word MEANS).
#
# This list is seeded from terms found in the actual uploaded assessment
# files (Civil-Supervisor-Refractory, Civil-Fitter-General) plus common
# construction/trade terms. Extend freely — the auto-detector in
# term_detector.py will also flag NEW candidate terms not yet in this list
# for human review before they're locked in.
# ============================================================================

GLOSSARY = {
    # --- Refractory trade ---
    "refractory":        {"hi": "रिफ्रैक्टरी",     "mr": "रिफ्रॅक्टरी",     "gu": "રિફ્રેક્ટરી"},
    "castable":          {"hi": "कैस्टेबल",        "mr": "कॅस्टेबल",        "gu": "કેસ્ટેબલ"},
    "module installation": {"hi": "मॉड्यूल इंस्टॉलेशन", "mr": "मॉड्यूल इन्स्टॉलेशन", "gu": "મોડ્યુલ ઇન્સ્ટોલેશન"},
    "module":            {"hi": "मॉड्यूल",         "mr": "मॉड्यूल",         "gu": "મોડ્યુલ"},
    "brick lining":      {"hi": "ब्रिक लाइनिंग",    "mr": "ब्रिक लायनिंग",   "gu": "બ્રિક લાઇનિંગ"},
    "lining":            {"hi": "लाइनिंग",          "mr": "लायनिंग",         "gu": "લાઇનિંગ"},
    "patch repair":      {"hi": "पैच रिपेयर",       "mr": "पॅच रिपेअर",      "gu": "પેચ રિપેર"},
    "expansion gap":     {"hi": "एक्सपेंशन गैप",    "mr": "एक्स्पान्शन गॅप", "gu": "એક્સપાન્શન ગેપ"},
    "wet curing":        {"hi": "वेट क्यूरिंग",     "mr": "वेट क्युरिंग",    "gu": "વેટ ક્યુરિંગ"},
    "curing":            {"hi": "क्यूरिंग",         "mr": "क्युरिंग",        "gu": "ક્યુરિંગ"},
    "dryout":            {"hi": "ड्रायआउट",        "mr": "ड्रायआउट",        "gu": "ડ્રાયઆઉટ"},
    "gunning":           {"hi": "गनिंग",            "mr": "गनिंग",           "gu": "ગનિંગ"},
    "rebound":           {"hi": "रिबाउंड",          "mr": "रिबाउंड",         "gu": "રિબાઉન્ડ"},
    "mortar":            {"hi": "मोर्टार",          "mr": "मोर्टार",         "gu": "મોર્ટાર"},
    "ppe":               {"hi": "पीपीई",            "mr": "पीपीई",           "gu": "પીપીઈ"},

    # --- Civil / Fitter / Construction general ---
    "reinforcement":     {"hi": "रीइन्फोर्समेंट",   "mr": "रीइन्फोर्समेंट",  "gu": "રીઇન્ફોર્સમેન્ટ"},
    "rebar":             {"hi": "रीबार",            "mr": "रीबार",           "gu": "રીબાર"},
    "concrete":          {"hi": "कंक्रीट",          "mr": "काँक्रीट",        "gu": "કોન્ક્રિટ"},
    "scaffolding":       {"hi": "स्कैफोल्डिंग",     "mr": "स्कॅफोल्डिंग",    "gu": "સ્કેફોલ્ડિંગ"},
    "shuttering":        {"hi": "शटरिंग",           "mr": "शटरिंग",          "gu": "શટરિંગ"},
    "formwork":          {"hi": "फॉर्मवर्क",        "mr": "फॉर्मवर्क",       "gu": "ફોર્મવર્ક"},
    "welding":           {"hi": "वेल्डिंग",         "mr": "वेल्डिंग",        "gu": "વેલ્ડિંગ"},
    "riveting":          {"hi": "रिवेटिंग",         "mr": "रिव्हेटिंग",      "gu": "રિવેટિંગ"},
    "bolting":           {"hi": "बोल्टिंग",         "mr": "बोल्टिंग",        "gu": "બોલ્ટિંગ"},
    "fixing":            {"hi": "फिक्सिंग",         "mr": "फिक्सिंग",        "gu": "ફિક્સિંગ"},
    "tying":             {"hi": "टाईंग",            "mr": "टायिंग",          "gu": "ટાઈંગ"},
    "micrometer":        {"hi": "माइक्रोमीटर",      "mr": "मायक्रोमीटर",     "gu": "માઇક્રોમીટર"},
    "site":              {"hi": "साइट",             "mr": "साइट",            "gu": "સાઇટ"},

    # --- Safety / generic technical (often transliterated by convention) ---
    "supervisor":        {"hi": "सुपरवाइज़र",       "mr": "सुपरवायझर",       "gu": "સુપરવાઇઝર"},
    "manpower":          {"hi": "मैनपावर",          "mr": "मॅनपॉवर",         "gu": "મેનપાવર"},
}


def lookup(term: str, lang_code: str):
    """Case-insensitive glossary lookup. Returns None if not found."""
    return GLOSSARY.get(term.strip().lower(), {}).get(lang_code)


def all_terms():
    return list(GLOSSARY.keys())
