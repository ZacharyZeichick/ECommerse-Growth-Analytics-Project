# Project Plan — E-Commerce Growth Analytics

---

## 1. Project Objective

Build a polished, end-to-end analytics portfolio project that demonstrates job-ready skills in SQL, Python, data storytelling, and business thinking — targeting Data Analyst, Product Analyst, BI Analyst, and startup analytics roles.

The project will produce a complete analytical narrative: from raw data to executive recommendations, showing where an e-commerce business is leaking growth and what to do about it.

---

## 2. Core Business Question

> "Where is this e-commerce business leaking growth: acquisition, conversion, retention, product mix, or fulfillment?"

---

## 3. Starting Hypothesis

> "The business is likely losing more growth through conversion quality, repeat purchasing, and post-purchase experience than through raw acquisition volume alone."

This is a directional starting point, not a conclusion. The analysis will confirm, refute, or refine this hypothesis based on actual findings. The final narrative follows the data.

---

## 4. Dataset

**theLook eCommerce**
- Source: Google BigQuery public data (`bigquery-public-data.thelook_ecommerce`)
- Type: Synthetic but realistic e-commerce dataset
- Key tables: `orders`, `order_items`, `users`, `products`, `inventory_items`, `events`, `distribution_centers`
- Access: BigQuery via Python (`google-cloud-bigquery`) or BigQuery console

---

## 5. Tools

| Tool | Purpose |
|------|---------|
| BigQuery (SQL) | Data exploration, aggregation, metric calculation |
| Python (pandas, numpy, matplotlib, scipy) | Wrangling, analysis, visualization |
| Jupyter Notebooks | Exploratory analysis and documentation |
| Tableau | Executive dashboard |
| GitHub | Version control and portfolio presentation |
| ChatGPT | Narrative drafting, analysis framing, hypothesis generation |
| Claude Code | Implementation, code execution, file management |

---

## 6. Planned Deliverables

1. **SQL library** — Modular, documented queries for each analysis area (`sql/`)
2. **Analysis notebooks** — One notebook per major theme, clean and narrative-driven (`notebooks/`)
3. **Figures and tables** — Saved chart outputs and summary tables (`outputs/`)
4. **Tableau dashboard** — Executive-facing interactive dashboard (`dashboards/`)
5. **Written report** — Executive summary with findings and recommendations (`reports/`)
6. **Clean README** — Portfolio-ready project overview

---

## 7. Phase Breakdown

### Phase 0 — Project Setup
- Create folder structure, CLAUDE.md, PROJECT_PLAN.md, PROJECT_STATE.md
- Initialize Git repository
- Prepare for first commit
- Deliverable: working environment and documented plan

### Phase 1 — Dataset Access & Schema Discovery
- Confirm BigQuery access (console and/or Python)
- Inspect all key tables: row counts, columns, date ranges, table relationships
- Document initial data quality notes and schema observations
- Define key metrics (conversion rate, LTV, repeat rate, return rate)
- Deliverable: SQL exploration queries, schema notes, data quality observations

### Phase 2 — Acquisition Analysis
- Traffic volume and trend over time
- Channel mix and cost efficiency (if available)
- New vs. returning user ratio
- Deliverable: SQL queries, notebook section, key charts

### Phase 3 — Funnel & Conversion Analysis
- Full funnel: browse → cart → purchase
- Drop-off rates by stage, device, traffic source
- Identify the highest-leverage conversion bottleneck
- Deliverable: SQL queries, funnel visualization, notebook section

### Phase 4 — Retention & Repeat Purchasing
- Cohort retention analysis (monthly cohorts)
- Repeat purchase rate and time-to-second-order
- LTV segmentation by cohort
- Deliverable: cohort heatmap, retention curves, notebook section

### Phase 5 — Product Performance
- Revenue concentration by category and product
- Return rates by product/category
- Margin proxy (if cost data available) or revenue per order by category
- Deliverable: product ranking analysis, notebook section

### Phase 6 — Fulfillment & Post-Purchase Experience
- Shipping time distribution and SLA adherence
- Return volume and return rate trends
- Cancellation rate analysis
- Deliverable: fulfillment analysis, notebook section

### Phase 7 — Synthesis & Narrative
- Confirm, refute, or refine starting hypothesis
- Identify the 2–3 highest-leverage growth leakage points
- Draft executive summary with prioritized recommendations
- Deliverable: written report, slide-ready summary

### Phase 8 — Visualization & Dashboard
- Build Tableau executive dashboard (or equivalent)
- Polish all charts and figures for portfolio quality
- Deliverable: Tableau workbook, exported figures

### Phase 9 — Portfolio Packaging
- Finalize README, clean notebooks, organize repo
- Write project summary for resume/portfolio
- Deliverable: clean, presentation-ready GitHub repo

---

## 8. Definition of Done (Per Phase)

| Phase | Done When |
|-------|-----------|
| 0 | Folder structure exists, Git initialized, planning docs complete |
| 1 | BigQuery access confirmed, all tables inspected, schema documented, key metrics defined |
| 2 | Acquisition trends analyzed, charts saved, findings noted |
| 3 | Funnel built, drop-off rates calculated, bottleneck identified |
| 4 | Cohort table built, retention curves plotted, LTV segmented |
| 5 | Product performance ranked, return rates calculated |
| 6 | Fulfillment SLA and return trends quantified |
| 7 | Narrative written, hypothesis verdict stated, recommendations prioritized |
| 8 | Dashboard built, all figures polished |
| 9 | Repo clean, README final, portfolio-ready |

---

## 9. Analysis Decision Rules

- Follow the data. If findings contradict the starting hypothesis, update the narrative — do not force a conclusion.
- Quantify every claim. Every finding should be backed by a number (%, $, ratio, or trend).
- Document all data quality issues and decisions made to handle them.
- Use statistical tests only when sample size and distribution justify it; otherwise use descriptive stats.
- Prioritize business impact over analytical complexity — the goal is actionable insight, not academic rigor.
- If a finding is ambiguous, note the uncertainty rather than overstating confidence.

---

## 10. Rules to Prevent Scope Creep

- Do not add new analysis areas not listed in this plan without explicit approval.
- Do not build predictive models unless explicitly scoped.
- Do not create new files, folders, notebooks, or scripts unless explicitly instructed.
- Log interesting tangents in IDEAS_BACKLOG.md — do not pursue them mid-project.
- Each phase must be approved as complete before beginning the next.
- If a question cannot be answered by the existing dataset, document the limitation and move on.

---

## 11. Rules for Claude Code Usage

- Always follow PROJECT_PLAN.md and PROJECT_STATE.md.
- Use scoped, specific implementation prompts — one task at a time.
- Do not change project scope without explicit user instruction.
- Edit only the files requested unless told otherwise.
- Prefer small, testable changes over large rewrites.
- Do not create new notebooks, scripts, dependencies, or folders unless explicitly requested.
- If stuck after 3 attempts, stop and summarize the blocker clearly.
- Put speculative ideas in IDEAS_BACKLOG.md, not in code or notebooks.
- Keep README.md public-facing and polished at all times.
- Update PROJECT_STATE.md when asked — keep it concise and current.

---

## 12. Role Split: ChatGPT, Claude Code, and Optional Codex

| Tool | Role |
|------|------|
| **ChatGPT** | Thinking partner: hypothesis generation, narrative framing, analysis structuring, executive summary drafting, interpreting findings in business context |
| **Claude Code** | Implementation: writing and executing SQL, Python, notebooks; managing files; running analysis; saving outputs |
| **Codex (optional)** | Boilerplate code generation for repetitive patterns (e.g., chart templates, query scaffolds) — only if helpful |

**Protocol:** Use ChatGPT to decide *what* to analyze and *how* to frame it. Use Claude Code to *build* it. Avoid asking Claude Code to make major analytical or narrative decisions without prior framing from ChatGPT or explicit user direction.
