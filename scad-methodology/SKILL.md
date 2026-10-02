---
name: scad-methodology
description: >
  Use this skill to develop a complete statistical methodology for any indicator at SCAD
  (Statistics Centre – Abu Dhabi). Triggers when the user says "develop a methodology for
  [indicator name]", "start the methodology workflow", "build the methodology for [indicator]",
  or any similar phrasing that implies developing, reviewing, or improving a SCAD statistical
  methodology document. Also trigger when the user mentions gap assessment, SCAD-specific
  methodology, standardized methodology, or indicator methodology development in a SCAD context.
  Do NOT trigger for general statistics questions or non-SCAD methodology queries.
---

# SCAD Statistical Methodology Development Skill

Guides the full end-to-end workflow for developing a statistical methodology at SCAD
(Statistics Centre – Abu Dhabi, Statistical Research, Methodology & Quality Standards).

---

## Institutional Context

Apply these rules across ALL steps:

- **Institution:** Statistics Centre – Abu Dhabi (SCAD)
- **Department:** Statistical Research, Methodology & Quality Standards
- **Language:** English (simple formal, objective — no personal opinions)
- **Translation note:** Documents are first written in English, then translated to Arabic
- **Annotation conventions:**
  - `[Aligned with: <source>]` — for elements consistent with international standards
  - `[Abu Dhabi exception]` — for any deviation or local adaptation (always include justification)
  - `[To be confirmed by SCAD]` — for unconfirmed items (render in *red italic* in .docx output)

---

## Workflow Overview

| Step | Action | Runs |
|------|--------|-------|
| 1 | Identify international sources | Auto |
| 2 | Develop standardized methodology | Auto → **PAUSE** |
| 3 | Receive SCAD input files + official .docx template | User uploads → Claude reads → **PAUSE** |
| 4 | Additional Information Q&A (if needed) | Conditional → **PAUSE** |
| 5 | SCAD-specific methodology (generate via professional-document-writer using the Step 3 template → compliance review) | On confirmation → **PAUSE** |
| 6 | Gap Assessment Report | On confirmation → **PAUSE** |

**Steps 1 and 2 run automatically in sequence.**
After Step 2 and every subsequent step, Claude pauses and waits for the user's explicit
confirmation or feedback before proceeding.

---

## Starting the Workflow

Begin immediately with Step 1 using the indicator name provided by the user. All
methodology content in Steps 1 and 2 is derived from international standards and best
practices — do NOT ask the user for methodological details upfront. SCAD-specific
implementation details (classification scope, data sources, frequency, base year,
geographic coverage, etc.) will be gathered in Step 3 via uploaded files and, if needed,
targeted questions in Step 4.

---

## Step 1 — Identify All Relevant International Sources *(auto)*

Identify ALL relevant international sources for the specified indicator. Organize by category:

1. Conceptual frameworks and definitions
2. Classification systems (activity, product, geographic)
3. Data collection standards and survey methodology
4. Index number theory and price/volume measurement
5. Quality frameworks (GSBPM, DQAF, Code of Practice)
6. Seasonal adjustment and time series methods
7. Dissemination and metadata standards (SDMX, SDDS)
8. Best practices from leading NSOs
9. GCC-Stat regional harmonization standards

For each source provide:
- Full name of the manual / handbook / classification / framework
- Issuing organization (UN, ILO, Eurostat, OECD, IMF, World Bank, GCC-Stat, etc.)
- Relevance: specific methodological guidance it provides for this indicator
- Reference URL if known

**Output:** Numbered list of all sources organized by category. Inline in chat (no file).

Proceed immediately to Step 2 without pausing.

---

## Step 2 — Develop Standardized Methodology *(auto → pause)*

Using ALL sources from Step 1, develop a COMPREHENSIVE STANDARDIZED METHODOLOGY representing
international best practice — the ideal methodology regardless of country-specific constraints.

Cover ALL sections with full detail. See `references/step2-template.md` for the complete
section structure, required content, and formatting guidance.

**Output:** Formal .docx file using the docx skill. Read `/mnt/skills/public/docx/SKILL.md`
before generating. File name: `Standardized_Methodology_[IndicatorName].docx`

**→ PAUSE after delivering the file.**

Prompt the user:
> "Step 2 complete — the standardized methodology document is ready. Please review it and
> confirm to proceed, or share any feedback or corrections."

---

## Step 3 — Receive SCAD Input Files *(user uploads → pause)*

After the user confirms Step 2, request the SCAD input files:

> "Please upload the SCAD files reflecting the current situation for this indicator. These
> typically include:
> - Assessment Response File
> - Indicator Portfolio File
> - Indicator Cards
> - Official SCAD methodology template (.docx) — used in Step 5 for formatting
> - Any other available file related to this indicator (reports, metadata, questionnaires, publications, etc.)
>
> Upload whichever are available — we will work with what you provide."

Once files are uploaded:
- Read EVERY uploaded file in full — extract ALL information available in each file;
  do not skim or rely on partial reading. No detail (definitions, classifications, data
  sources, frequency, coverage, base year, sample design, quality practices, dissemination,
  etc.) should be overlooked
- Identify which uploaded file is the official .docx template and confirm it will be used
  for Step 5 formatting (do NOT summarize its content — it governs formatting only)
- Summarize what SCAD's current practices are based on the other files, covering all
  extracted information
- Confirm your understanding with the user before proceeding

**→ PAUSE after summarizing.**

Prompt the user:
> "I've read the SCAD files. Here is my understanding of the current practices:
> [summary]. Please confirm this is correct, or clarify anything before we continue."

---

## Step 4 — Additional Information Q&A *(conditional → pause)*

After Step 3 is confirmed, compare the SCAD input files against the standardized methodology
from Step 2. Identify where MORE INFORMATION is needed — dimensions, practices, or data
points that are missing, ambiguous, or not addressed in the SCAD files.

**If NO additional information is needed:**
> "The SCAD files provide all the information needed. Step 4 is skipped — ready to
> proceed to Step 5 when you confirm."

**If additional information is needed:**
- List clearly all items where more information is required, organized by methodology dimension
- For each item, explain what information is needed and why it matters for the methodology
- Ask targeted follow-up questions only about the missing information
- Do NOT ask about things already confirmed in the SCAD files
- Wait for the user to answer before proceeding

**→ PAUSE after Q&A is resolved (or step is skipped).**

Prompt the user:
> "All additional information has been provided. Please confirm to proceed to Step 5 —
> the SCAD-specific methodology document."

---

## Step 5 — Develop SCAD-Specific Methodology *(on confirmation → pause)*

### 5a. Locate the SCAD template file

Use the official SCAD .docx template uploaded in Step 3. If it was NOT provided in Step 3,
request it now:

> "Please upload the official SCAD methodology template (.docx) so the document can be
> generated with full formatting compliance."

Do NOT generate the document without the template. If the user says no template is
available for this run, fall back to the default formatting in File Output Rules.

### 5b. Develop the content

Develop the FULL SCAD-SPECIFIC METHODOLOGY content. This must:
- Reflect SCAD's ACTUAL current practices, using ALL information extracted from the Step 3
  files + Step 4 answers — every relevant detail from the uploaded files must be reflected
- Be comprehensive, formal, and publication-ready
- **Prefer paragraphs over tables:** write the content as formal prose paragraphs by
  default. Use a table ONLY when the information is genuinely better presented that way
  (e.g., classification breakdowns, weight structures, source-by-source comparisons,
  revision calendars). Do not convert narrative content into tables for convenience
- Note `[Aligned with: source]` for every element consistent with international standards
- Note `[Abu Dhabi exception]` with justification for every deviation or local adaptation
- Mark all unconfirmed items as `[To be confirmed by SCAD]` in *red italic*
- For any SCAD detail STILL missing after Steps 3–4: do NOT leave it blank — fill it using
  the international best practice from the Step 2 standardized methodology, and mark it
  `[To be confirmed by SCAD]` in *red italic* so SCAD can validate or replace it

Use `references/step5-template.md` for the required section structure (9 sections including
cover page and approval blocks). The uploaded .docx template governs FORMATTING; the
reference file governs CONTENT coverage.

### 5c. Apply the template via professional-document-writer

Read `/mnt/skills/user/professional-document-writer/SKILL.md` and follow it to place the
content into the uploaded template. Key requirements:
- First analyze the uploaded template: extract all styles, fonts, sizes, colors, spacing,
  margins, headers/footers, page numbering, numbering styles, table styles, cover page layout
- Preserve every formatting element of the template — 100% compliance
- Place every paragraph under its correct heading; never paste sequentially
- If content has no matching heading in the template, create the heading at the correct
  level and color it **Red** to flag it as an addition
- Update only the cover page title fields; keep logos, spacing, and layout unchanged
- English content: LTR, left-aligned (Arabic, if ever requested: RTL, right-aligned)

Also read `/mnt/skills/public/docx/SKILL.md` before generating.
File name: `SCAD_Methodology_[IndicatorName].docx`

### 5d. Compliance review (this skill reviews the output)

After generating the file, re-open it and verify BEFORE presenting it:

1. **Template compliance:** fonts, sizes, colors, spacing, margins, headers/footers, page
   numbering, table styles, and cover page all match the uploaded template
2. **Content completeness:** all sections from `references/step5-template.md` are present;
   no content missing or duplicated; every paragraph under the correct heading
3. **SCAD conventions:** `[Aligned with:]`, `[Abu Dhabi exception]` (with justification),
   and `[To be confirmed by SCAD]` in red italic are applied consistently
4. **New headings** (if any) are colored Red
5. Tables fit within page margins with balanced columns
6. **Prose preference:** content is written as paragraphs; any table used is justified
   by the nature of the information (not a convenience substitute for prose)

Fix any issue found, then report the review result to the user as a short checklist
(pass/fixed per item) alongside the file.

**→ PAUSE after delivering the file and the review checklist.**

Prompt the user:
> "Step 5 complete — the SCAD-specific methodology document is ready. Please review it and
> confirm to proceed to the Gap Assessment Report, or share any feedback."

---

## Step 6 — Gap Assessment Report *(on confirmation → pause)*

Compare SCAD's current methodology (Step 5) against the standardized methodology (Step 2)
and produce a formal Gap Assessment Report. See `references/step6-template.md` for the
complete report structure (6 sections including executive summary, gap matrix, priority
areas, compliance summary, and improvement roadmap).

**Output:** Formal .docx file using the docx skill. Read `/mnt/skills/public/docx/SKILL.md`
before generating. File name: `Gap_Assessment_[IndicatorName].docx`

**→ PAUSE after delivering the file.**

Prompt the user:
> "Step 6 complete — the Gap Assessment Report is ready. The full methodology workflow is
> now complete. Let me know if you need any revisions to any of the documents."

---

## International Standards Reference

Apply across all steps:

| Standard | Issuing Body | Purpose |
|----------|-------------|---------|
| IRIIP 2010 | UNSD | Principal methodological reference |
| ISIC Rev.4 | UNSD | Activity classification |
| SNA 2008 | UN | Volume measurement conceptual framework |
| CPC Ver.2.1 | UNSD | Product classification |
| GSBPM v5.1 | UNECE | Statistical process framework |
| IMF DQAF | IMF | Data quality assessment |
| PPI Manual | IMF | Deflation and price index guidance |
| ESS Seasonal Adjustment Guidelines | Eurostat | Seasonal adjustment methods |
| European Statistics Code of Practice | Eurostat | Quality framework |
| SDMX Content-Oriented Guidelines | SDMX | Metadata standards |
| IMF SDDS / GDDS | IMF | Dissemination standards |
| GCC-Stat standards | GCC-Stat | Regional harmonization |

---

## File Output Rules

- Always read `/mnt/skills/public/docx/SKILL.md` before generating any .docx file
- Each step that produces a file generates a **separate** .docx — never combine steps
- Apply SCAD annotation conventions (`[Aligned with:]`, `[Abu Dhabi exception]`,
  `[To be confirmed by SCAD]` in red italic) consistently
- Present files using the `present_files` tool after creation

**Steps 2 and 6 (default formatting):**
- A4 page size (docx-js default) with 1-inch margins
- Arial font throughout

**Step 5 (template-driven formatting):**
- Formatting comes ENTIRELY from the SCAD .docx template uploaded in Step 3, applied via the
  professional-document-writer skill (`/mnt/skills/user/professional-document-writer/SKILL.md`)
- The default A4/Arial rules do NOT apply — the template governs all fonts, layout,
  margins, headers/footers, and styles
- Always run the Step 5d compliance review before presenting the file
- Fallback: if no template is uploaded for this run, use the Steps 2/6 default formatting

---

## Reference Files

- `references/step2-template.md` — Full section structure for the standardized methodology
- `references/step5-template.md` — Full SCAD template structure (9 sections + approval blocks)
- `references/step6-template.md` — Full gap assessment report structure
