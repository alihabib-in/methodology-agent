from app.agent.extractor import Extractor
from app.agent.gap_detector import GapDetector
from app.agent.question_generator import QuestionGenerator
from app.agent.state_manager import StateManager
from app.agent.terminology import detect_language
from app.core.logging import get_logger
from app.llm.client import LLMClient
from app.models.extraction import ExtractionResult
from app.models.methodology_state import MethodologyState
from app.models.question import MethodologyQuestion

logger = get_logger(__name__)


class MethodologyAgent:
    """Orchestrates the bilingual methodology reasoning pipeline."""

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm
        self.extractor = Extractor(llm)
        self.gap_detector = GapDetector()
        self.question_generator = QuestionGenerator()
        self.state_manager = StateManager()

    def extract(
        self,
        text: str,
        language: str | None = None,
    ) -> ExtractionResult:
        return self.extractor.extract(text, language)

    def analyze(
        self,
        text: str,
        language: str | None = None,
        state: MethodologyState | None = None,
        use_rag: bool = True,
    ) -> dict:
        detected = language or detect_language(text)

        relevant_knowledge: list[dict] = []
        if use_rag:
            relevant_knowledge = self._retrieve(text)

        try:
            extraction = self.extractor.extract(
                text,
                detected,
                known_context=relevant_knowledge,
            )
        except Exception as exc:  # noqa: BLE001 - surface graceful error to API
            logger.exception("extraction failed")
            return {
                "original_input": text,
                "language": detected,
                "parse_error": True,
                "error": str(exc),
            }

        manager = StateManager(
            state if state is not None else self.state_manager.state
        )
        updated_state = manager.apply(extraction)
        gaps = self.gap_detector.detect(updated_state)
        question = self.question_generator.generate(
            gaps,
            recommended=extraction.recommended_question,
        )

        return {
            "original_input": text,
            "language": extraction.language or detected,
            "summary": extraction.summary,
            "extraction": extraction.model_dump(),
            "methodology_state": updated_state.model_dump(),
            "gaps": gaps,
            "recommended_question": question.model_dump(),
            "relevant_knowledge": relevant_knowledge,
        }

    def answer(
        self,
        answer_text: str,
        state: MethodologyState,
        language: str | None = None,
        use_rag: bool = True,
    ) -> dict:
        """Apply a human answer to a question, updating the methodology state."""
        return self.analyze(
            text=answer_text,
            language=language,
            state=state,
            use_rag=use_rag,
        )

    @staticmethod
    def _retrieve(query: str, limit: int = 5) -> list[dict]:
        try:
            from app.knowledge.rag import retrieve

            return retrieve(query, limit=limit)
        except Exception:  # noqa: BLE001 - retrieval is best-effort
            return []

    def generate_question(
        self,
        state: MethodologyState,
        recommended=None,
    ) -> MethodologyQuestion:
        gaps = self.gap_detector.detect(state)
        return self.question_generator.generate(gaps, recommended=recommended)

    def get_state(self) -> MethodologyState:
        return self.state_manager.state
