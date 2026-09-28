# Extraction Prompt

> Reference copy of the runtime prompt defined in `app/agent/prompts.py`.

Analyze the following business discussion.

Language hint:
`{language}`

Discussion:
`{text}`

Return valid JSON only, using this exact schema:

`{schema}`

Rules:

- Never invent facts. Preserve uncertainty.
- Separate inference (`status "inferred"`) from confirmation (`status "confirmed"`).
- Preserve original Arabic evidence inside statements where possible.
- Use canonical English concepts (for example: `active establishment`).
- The recommended_question must be written in English and target the single
  most important missing methodology element.
