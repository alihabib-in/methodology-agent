from app.models.extraction import RecommendedQuestion
from app.models.question import MethodologyQuestion

DOMAIN_QUESTION_TEMPLATES: dict[str, dict[str, str]] = {
    "definition": {
        "question": "How should this concept be defined?",
        "reason": "A clear definition is required to determine what is included in the indicator.",
    },
    "objective": {
        "question": "What is the statistical objective of this indicator?",
        "reason": "The objective is required to scope the whole methodology.",
    },
    "statistical_unit": {
        "question": "What is the statistical unit to be counted?",
        "reason": "The statistical unit determines what is counted and affects comparability.",
    },
    "target_population": {
        "question": "What is the target population for this indicator?",
        "reason": "The target population determines the coverage of the indicator.",
    },
    "reference_period": {
        "question": "What reference period should be used for measurement?",
        "reason": "The reference period determines when the phenomenon is measured.",
    },
    "data_source": {
        "question": "What data source should be used for this indicator?",
        "reason": "The data source determines where the data comes from and its update frequency.",
    },
    "frequency": {
        "question": "At what frequency should the indicator be produced?",
        "reason": "The frequency determines how often the indicator is published.",
    },
    "geographic_scope": {
        "question": "What geographic scope should the indicator cover?",
        "reason": "The geographic scope determines the coverage area.",
    },
}


class QuestionGenerator:
    """Produces the single highest-priority methodology question.

    Prefers the LLM's recommended question when it aligns with the top
    detected gap; otherwise falls back to deterministic domain templates.
    """

    def _question_for_gap(self, gap: dict) -> MethodologyQuestion:
        domain = gap["domain"]
        template = DOMAIN_QUESTION_TEMPLATES.get(domain)
        if template:
            return MethodologyQuestion(
                question=template["question"],
                domain=domain,
                reason=template["reason"],
                priority=gap["priority"],
                status="candidate",
            )
        return MethodologyQuestion(
            question=f"Please clarify the following methodology element: "
            f"{gap['label']}.",
            domain=domain,
            reason=gap["reason"],
            priority=gap["priority"],
            status="candidate",
        )

    def generate(
        self,
        gaps: list[dict],
        recommended: RecommendedQuestion | None = None,
    ) -> MethodologyQuestion:
        if not gaps:
            return MethodologyQuestion(
                question="No outstanding methodology question was identified.",
                domain="general",
                reason="All required methodology fields appear to be resolved.",
                priority=0.0,
                status="candidate",
            )

        top = gaps[0]
        domain = top["domain"]

        if recommended and recommended.question:
            if recommended.domain is None or recommended.domain == domain:
                priority = recommended.priority or top["priority"]
                return MethodologyQuestion(
                    question=recommended.question,
                    domain=recommended.domain or domain,
                    reason=recommended.reason or top["reason"],
                    priority=priority,
                    status="candidate",
                )
            gap_domains = {g["domain"] for g in gaps}
            if recommended.domain in gap_domains or recommended.domain in DOMAIN_QUESTION_TEMPLATES:
                matched = next(
                    (g for g in gaps if g["domain"] == recommended.domain),
                    None,
                )
                priority = recommended.priority or (
                    matched["priority"] if matched else top["priority"]
                )
                return MethodologyQuestion(
                    question=recommended.question,
                    domain=recommended.domain,
                    reason=recommended.reason or top["reason"],
                    priority=priority,
                    status="candidate",
                )

        return self._question_for_gap(top)

    def generate_many(
        self,
        state,
        gaps: list[dict],
    ) -> list[MethodologyQuestion]:
        """Produce a broad set of plain-language questions across every part of
        the methodology (gaps, indicators, dimensions, definitions, sources,
        open questions) so the assistant keeps the discussion moving."""
        questions: list[MethodologyQuestion] = []

        for gap in gaps:
            questions.append(
                MethodologyQuestion(
                    question=self._simple_gap_question(gap),
                    domain=gap["domain"],
                    reason=gap["reason"],
                    priority=gap["priority"],
                    status="candidate",
                )
            )

        for ind in state.indicators:
            label = ind.get("value") or ind.get("concept") or "this"
            questions.append(
                MethodologyQuestion(
                    question=f"How should we measure: {label}?",
                    domain="indicator",
                    reason="We need a clear and consistent way to measure this.",
                    priority=0.7,
                    status="candidate",
                )
            )

        for dim in state.dimensions:
            label = dim.get("value") or dim.get("concept") or "this"
            questions.append(
                MethodologyQuestion(
                    question=f"Should we look at the results separately by {label}?",
                    domain="dimension",
                    reason="Looking at the results separately can show useful differences.",
                    priority=0.55,
                    status="candidate",
                )
            )

        for definition in state.definitions:
            concept = self._readable(
                definition.get("concept") or definition.get("statement") or "this"
            )
            questions.append(
                MethodologyQuestion(
                    question=f"What exactly do we mean by \"{concept}\"?",
                    domain="definition",
                    reason="A clear definition avoids confusion later.",
                    priority=0.75,
                    status="candidate",
                )
            )

        for source in state.data_sources:
            name = source.get("name") or source.get("concept") or "this source"
            questions.append(
                MethodologyQuestion(
                    question=f"Where should we get this information from — for example, {name}?",
                    domain="data_source",
                    reason="We need reliable sources for the data.",
                    priority=0.6,
                    status="candidate",
                )
            )

        for oq in state.open_questions:
            note = oq.get("note") or oq.get("concept") or "this point"
            questions.append(
                MethodologyQuestion(
                    question=f"Can you help clarify: {note}?",
                    domain="open_question",
                    reason="This point is still open.",
                    priority=0.5,
                    status="candidate",
                )
            )

        questions.append(
            MethodologyQuestion(
                question="What exactly should this study cover, and what should we leave out?",
                domain="scope",
                reason="Being clear on the scope keeps the work focused.",
                priority=0.8,
                status="candidate",
            )
        )

        questions.append(
            MethodologyQuestion(
                question="Do we have a set budget for this study?",
                domain="budget",
                reason="Knowing the budget helps us plan what is possible.",
                priority=0.7,
                status="candidate",
            )
        )

        for c in state.constraints:
            value = c.get("value") or c.get("concept") or "this limit"
            questions.append(
                MethodologyQuestion(
                    question=f"Do we need to keep this limit in mind: {value}?",
                    domain="constraint",
                    reason="Limits affect how we can run the study.",
                    priority=0.6,
                    status="candidate",
                )
            )

        for r in state.roles:
            role = r.get("role") or r.get("value") or r.get("concept") or "this task"
            questions.append(
                MethodologyQuestion(
                    question=f"Who should be responsible for: {role}?",
                    domain="roles",
                    reason="Clear roles help everyone know what they should do.",
                    priority=0.55,
                    status="candidate",
                )
            )

        for m in state.success_metrics:
            metric = m.get("metric") or m.get("value") or m.get("concept") or "success"
            questions.append(
                MethodologyQuestion(
                    question=f"How will we know if this is successful: {metric}?",
                    domain="success_metrics",
                    reason="We need a clear way to tell if the study worked.",
                    priority=0.65,
                    status="candidate",
                )
            )

        for t in state.training_needs:
            need = t.get("need") or t.get("value") or t.get("concept") or "this area"
            questions.append(
                MethodologyQuestion(
                    question=f"Will the team need training on: {need}?",
                    domain="training_needs",
                    reason="Making sure the team is ready avoids problems later.",
                    priority=0.5,
                    status="candidate",
                )
            )

        questions.append(
            MethodologyQuestion(
                question="When do we need to finish this study?",
                domain="timeline",
                reason="Knowing the deadline helps us plan the work.",
                priority=0.6,
                status="candidate",
            )
        )

        questions.append(
            MethodologyQuestion(
                question="Who will use the results of this study?",
                domain="audience",
                reason="Knowing the audience helps us make the results useful.",
                priority=0.6,
                status="candidate",
            )
        )

        seen: set[str] = set()
        unique: list[MethodologyQuestion] = []
        for q in questions:
            if q.question not in seen:
                seen.add(q.question)
                unique.append(q)

        unique.sort(key=lambda q: q.priority, reverse=True)
        return unique

    @staticmethod
    def _simple_gap_question(gap: dict) -> str:
        simple = {
            "objective": "What is the main goal of this study?",
            "target_population": "Who exactly should we include in this study?",
            "statistical_unit": "What exactly are we counting?",
            "reference_period": "What time period should we look at?",
            "frequency": "How often should we update the results?",
            "geographic_scope": "Which areas should we cover?",
            "definition": "What do we mean by this?",
            "data_source": "Where should we get the data from?",
        }
        return simple.get(
            gap.get("domain"),
            f"Can you tell us more about: {gap.get('label', 'this')}?",
        )

    @staticmethod
    def _readable(concept: str) -> str:
        return str(concept).replace("_", " ").strip()
