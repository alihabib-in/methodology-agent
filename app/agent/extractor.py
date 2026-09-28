import json
import re

from app.agent.prompts import (
    EXTRACTION_JSON_SCHEMA,
    EXTRACTION_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)
from app.agent.terminology import detect_language, normalize_language
from app.core.logging import get_logger
from app.llm.client import LLMClient
from app.models.extraction import ExtractionResult

logger = get_logger(__name__)


def extract_json(text: str) -> str:
    """Extract the first balanced JSON object/array from a free-form string."""
    text = text.strip()

    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()

    first_brace = text.find("{")
    first_bracket = text.find("[")

    candidates = [i for i in (first_brace, first_bracket) if i != -1]
    if not candidates:
        return text

    start = min(candidates)
    open_ch = text[start]
    close_ch = "}" if open_ch == "{" else "]"

    depth = 0
    in_string = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
        elif ch == open_ch:
            depth += 1
        elif ch == close_ch:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return text[start:]


class Extractor:
    """Runs LLM extraction and validates the result against Pydantic models."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def extract(
        self,
        text: str,
        language: str | None = None,
        known_context: list[dict] | None = None,
    ) -> ExtractionResult:
        detected = language or detect_language(text)

        user_prompt = EXTRACTION_PROMPT_TEMPLATE.format(
            language=detected,
            text=text,
            schema=EXTRACTION_JSON_SCHEMA,
        )

        if known_context:
            context_block = "\n\nExisting approved methodology knowledge "
            context_block += "(reuse canonical definitions, do not contradict):\n"
            context_block += "\n".join(
                f"- [{item.get('concept') or item.get('domain') or 'knowledge'}] "
                f"{item.get('statement')}"
                for item in known_context
            )
            user_prompt += context_block

        raw = self.llm.chat(SYSTEM_PROMPT, user_prompt)

        try:
            return self._parse_and_normalize(raw, detected)
        except (json.JSONDecodeError, ValueError):
            logger.warning("LLM output failed validation; retrying once")

        retry_prompt = (
            user_prompt
            + "\n\nIMPORTANT: Return ONLY valid JSON matching the schema above. "
            "Do not wrap it in markdown and do not add commentary."
        )
        raw_retry = self.llm.chat(SYSTEM_PROMPT, retry_prompt)
        return self._parse_and_normalize(raw_retry, detected)

    def _parse_and_normalize(self, raw: str, detected: str) -> ExtractionResult:
        result = self._parse(raw)
        result.language = normalize_language(result.language, fallback=detected)
        return result

    @staticmethod
    def _parse(raw: str) -> ExtractionResult:
        data = json.loads(extract_json(raw))
        data = Extractor._sanitize(data)
        return ExtractionResult.model_validate(data)

    _LIST_FIELDS = {
        "requirements", "definitions", "statistical_units", "populations",
        "reference_periods", "frequencies", "geographic_scopes", "indicators",
        "dimensions", "data_sources", "business_rules", "quality_rules",
        "constraints", "decisions", "open_questions",
    }

    @staticmethod
    def _sanitize(data) -> dict:
        if not isinstance(data, dict):
            raise ValueError("extraction result is not a JSON object")

        for key in Extractor._LIST_FIELDS:
            value = data.get(key)
            if value is None:
                data[key] = []
            elif isinstance(value, dict):
                data[key] = [value]
            elif isinstance(value, list):
                data[key] = [item for item in value if isinstance(item, dict)]
            else:
                data[key] = []

        data = {
            key: (
                [item for item in value if Extractor._has_identifier(item)]
                if key in Extractor._LIST_FIELDS and isinstance(value, list)
                else value
            )
            for key, value in data.items()
        }

        recommended = data.get("recommended_question")
        if recommended is not None and (
            not isinstance(recommended, dict)
            or not (recommended.get("question") or "").strip()
        ):
            data["recommended_question"] = None

        return data

    @staticmethod
    def _has_identifier(item: dict) -> bool:
        return bool((item.get("concept") or "").strip() or (item.get("name") or "").strip())
