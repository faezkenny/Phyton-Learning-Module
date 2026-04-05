# NEBULOUS-CORE Copywriting Guide

> Reference this before writing any new module text, section headings, notes, or quiz prompts.

---

## The Voice

The app talks **to Ain, not at her.** It sounds like a sharp senior colleague who skips the lecture and goes straight to what she needs to know.

---

## Core Rules

### 1. Always name Ain
Bad → *"The model classifies the shipment."*
Good → *"The model tells Ain which shipments to flag."*

### 2. One idea per sentence
Bad → *"FTS captures linguistic uncertainty and applies it to the output domain through aggregation before producing a defuzzified crisp result."*
Good → *"FTS bends when standard math breaks. The centroid turns a fuzzy cloud into one usable number."*

### 3. Ground every concept in the factory floor
Bad → *"Uncertainty management is a key advantage."*
Good → *"Standard regression breaks during a shipping war. FTS bends instead of snapping."*

### 4. Never use passive voice for things Ain should do
Bad → *"The centroid formula is applied to the aggregated curve."*
Good → *"Ain applies the centroid formula to collapse the curve into one crisp number."*

### 5. Logistics nouns over academic nouns
Use → *shipment, coil, delay, supplier, port, discrepancy, week, sprint*
Avoid → *domain, methodology, framework, paradigm, implementation, leverage*

### 6. Section headings are imperatives or short titles — never long sentences
Bad → *"This section demonstrates how fuzzy logic applies to global logistics under disruption."*
Good → *"Scenario Simulator"* or *"Place the Centroid"*

### 7. `render_plain_note()` is for one-liner gut-punch truths
It should read like a sticky note above a desk, not a paragraph from a dissertation.
Bad → *"A good thesis figure is really an argument. Ain should be able to say why this chart type was chosen and what decision signal it reveals."*
Good → *"Choose the chart for the question, not the other way around."*

### 8. Vibe Explanation = one paragraph max, in plain English, tied to the live numbers on screen
It should complete this sentence: *"What Ain is actually seeing right now is…"*

---

## Word Swaps

| Avoid | Use instead |
|---|---|
| apply FTS logic | plug the fuzzy rule in |
| leverage | use |
| demonstrate | show |
| utilize | use |
| novel approach | different angle |
| in order to | to |
| it is worth noting | note: |
| it is important to understand | — (just say the thing) |
| advantages and limitations | wins and watch-outs |
| domain expert | someone who already thinks in these terms |

---

## Section Header Patterns (by type)

| Type | Pattern | Example |
|---|---|---|
| Interactive demo | One-liner action | *"Move the sliders to see the fuzzy engine classify in real time."* |
| Code section | *"This is the exact [X] call that drew [Y]."* | *"This is the exact NumPy call powering the result above."* |
| Math section | *"See the formula behind [the chart / the number / the slider]."* | *"See the formula behind the centroid slider."* |
| Vibe section | *"[What Ain just did] in plain language."* | *"This is the moment Ain stops thinking one row at a time."* |
| Note | One sentence. Gut punch. | *"FTS bends where standard regression snaps."* |

---

## Module Structure Template

Every module follows this same skeleton — keep section headings short and direct:

1. **Hero** (eyebrow + headline + one-liner description)
2. **KPIs** (3 short cards — Focus / Role / Next Unlock)
3. **What You Will Learn** (bullet list, max 4 items)
4. **Interactive Demo** — *action verb + what changes*
5. **Live Code** — *"This is the exact [library] call…"*
6. **How this works in Python** — 3 breakdown cards
7. **Mathematical Visualization** — formula + one caption sentence
8. **Vibe Explanation** — one paragraph tied to live numbers
9. **Study Notes** (Gemini RAG panel)
10. **Quiz** (3–4 questions)

---

## Quiz Prompt Template

Format: **Scenario → Challenge → Options**

- Scenario is a real logistics situation, not a generic textbook question.
- One distractor should be "almost right but subtly wrong."
- The correct answer is never the longest option.

Example:
> *"Ain's professor asks why FTS beats a 5-day threshold rule. What is the strongest answer?"*
> A) FTS allows partial membership, so a 5.1-day delay is not treated the same as a 20-day delay ✓
> B) FTS is faster in Python
> C) FTS removes outliers automatically

---

## What "AI-looking" Means Here (Anti-Patterns to Delete)

These phrases signal that the text was written by AI and not checked:

- *"It is worth noting that…"*
- *"This approach offers significant advantages…"*
- *"Ain should be able to explain…"* (too meta — just say what to explain)
- *"This is exactly how professional software is built."*
- *"These four scenarios anchor the math to real decisions."*
- Any sentence that could appear unchanged in five other apps.

Replace them with something specific to this dataset, this module, this moment.
