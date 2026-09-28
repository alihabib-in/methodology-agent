"""Canonical Arabic/English methodology terminology and language detection."""

TERMINOLOGY = {
    "منشأة": "establishment",
    "المنشآت": "establishments",
    "منشآت": "establishments",
    "مؤشر": "indicator",
    "مؤشر شهري": "monthly indicator",
    "السجل التجاري": "business register",
    "الوحدة الإحصائية": "statistical unit",
    "السكان المستهدفون": "target population",
    "الفترة المرجعية": "reference period",
    "التكرار": "frequency",
    "المصدر": "data source",
    "التعريف": "definition",
    "النطاق الجغرافي": "geographic scope",
    "شهري": "monthly",
    "سنوي": "annual",
    "ربع سنوي": "quarterly",
    "يومي": "daily",
    "أسبوعي": "weekly",
    "نشط": "active",
    "النشطة": "active",
    "المنشأة النشطة": "active establishment",
    "المنشآت النشطة": "active establishments",
    "بيانات": "data",
    "سجل": "register",
    "تحديث": "update",
    "الفترة": "period",
    "النطاق": "scope",
}

_ARABIC_FIRST = "\u0600"
_ARABIC_LAST = "\u06FF"


def is_arabic(text: str) -> bool:
    return any(_ARABIC_FIRST <= ch <= _ARABIC_LAST for ch in text)


def has_latin(text: str) -> bool:
    return any("a" <= ch.lower() <= "z" for ch in text)


def detect_language(text: str) -> str:
    arabic = is_arabic(text)
    latin = has_latin(text)
    if arabic and latin:
        return "mixed"
    if arabic:
        return "ar"
    if latin:
        return "en"
    return "unknown"


_LANG_ALIASES = {
    "ar": "ar",
    "arabic": "ar",
    "en": "en",
    "english": "en",
    "mixed": "mixed",
    "ar-en": "mixed",
    "en-ar": "mixed",
    "auto": "auto",
    "auto-detect": "auto",
}


def normalize_language(value: str | None, fallback: str = "unknown") -> str:
    key = (value or "").strip().lower()
    return _LANG_ALIASES.get(key, fallback)


def canonicalize(text: str) -> str:
    """Replace known Arabic terms with their canonical English concepts.

    This is a light normalization aid only; the LLM performs the actual
    semantic interpretation and must not be forced into literal translation.
    """
    result = text
    for arabic in sorted(TERMINOLOGY, key=len, reverse=True):
        if arabic in result:
            result = result.replace(arabic, TERMINOLOGY[arabic])
    return result
