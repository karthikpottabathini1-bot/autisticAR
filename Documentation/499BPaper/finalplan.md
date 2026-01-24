# AIris Thesis Comprehensive Expansion Plan

## Objective
Transform `AIris.tex` into a **publication-quality final thesis** that comprehensively documents the entire 7-month development journey, including all research, iterations, testing, and technical decisions.

---

## Source Material Analyzed

| Source | Content for Thesis |
|:---|:---|
| **Log.md** | 60+ development entries (May-Dec 2025), 4 phases, milestone dates |
| **Archive/README.md** | 15 archived iterations, evolution timeline, key learnings per phase |
| **Idea.md** | Original vision, problem statement, key differentiators |
| **Vision.md** | Brand identity, voice/tone guide for accessibility |
| **PRD.md** | Functional/Non-functional requirements, success metrics |
| **EvaluationReport.md** | 41x latency improvement (14s → 340ms), failure analysis |
| **LitReview0.md, LitReview1.md** | 12+ academic papers on VLMs, Edge AI, Wearables |
| **YOLO_Models_Research.md** | YOLO26 vs YOLOv8 comparison, model size variants |
| **Structure.md** | Codebase architecture, backend/frontend organization |

---

## Document Modifications

### 1. Remove Appendices A and B
**Action:** Delete the `\appendix` section and its two chapters (User Manual, Developer Reference) currently added before the bibliography.

---

### 2. Expand Chapter 1: Introduction
Add a detailed **"Project Genesis"** section:
- Describe initial inspiration, academic context (CSE 499A/B).
- Include a "Research Questions" subsection formalizing the thesis contributions.
- Add a "Chapter Outline" subsection summarizing the thesis structure.

---

### 3. Expand Chapter 2: Literature Review
**New Subsections:**
1.  **LVLMs for Assistive Tech**: Integrate content from `LitReview1.md` on MiniGPT-4 and LLaVA's "visual instruction tuning."
2.  **Wearable Systems Survey**: Add comparison table from `LitReview0.md` (Table 1: Comparison of Wearable Assistive Devices).
3.  **Gap Analysis**: Formalize the 5 research gaps identified in `LitReview0.md` Section 5 and directly state how AIris addresses each.

---

### 4. Expand Chapter 3: Methodology & Design
**New Content:**
1.  **Timeline & Phases**: Insert a table representation of the 4-phase development (Research, Prototype, System, Completion) from `Log.md`.
2.  **Hardware Decision Matrix**: Why ESP32-CAM over USB camera, why laptop over Raspberry Pi (citing `EvaluationReport.md` and `Archive/README.md` benchmarking learnings).
3.  **Model Selection Justification (Extended)**: Detailed comparison table for YOLO variants from `YOLO_Models_Research.md`.

---

### 5. Add Chapter: Project Evolution & Iterations (NEW)
**Source:** `Archive/README.md`, `Log.md`

Create a dedicated chapter documenting the iterative development process.

**Sections:**
1.  **Phase 1: Research & Exploration**: BLIP experiments, Gradio UI, initial LLM integration.
2.  **Phase 2: Prototype Development**: Ollama benchmarking on RPi 5 (and why it failed), Groq API pivot.
3.  **Phase 3: Full System Build**: FastAPI/React architecture, RSPB, Merged System, Activity Guide v1.
4.  **Phase 4: Software Completion**: Handsfree mode, Guardian Alerts, YOLO26s upgrade.
5.  **Lessons Learned Per Iteration**: A summary table based on `Archive/README.md` "Key Learnings from Each Phase."

---

### 6. Expand Chapter 7: Technical Implementation
**New Content:**
1.  **Service-Oriented Design Deep Dive**: Detail the responsibility of each backend service file from `Structure.md`.
2.  **State Machine Expansion**: Describe all states and transitions for `ActivityGuideService` with a formal state diagram.
3.  **Voice Control Implementation**: Explain the `voiceControl.ts` service and Web Speech API integration.

---

### 7. Expand Chapter 8: Results & Analysis
**New Content:**
1.  **Historical Performance Comparison**: Include Table 1/2 from `EvaluationReport.md` showing Early Prototype vs. Current System.
2.  **Latency Breakdown Analysis**: Detail the 41x improvement (BLIP → YOLO + Groq).
3.  **Extended User Testing Observations**: Add qualitative insights from testing (e.g., "hot-and-cold" feedback analogy).

---

### 8. Expand Chapter 9: Discussion & Impact
**New Content:**
1.  **Contributions Summary (Restated)**: Reframe the Summary of Contributions in the context of the research gaps identified in the Literature Review.
2.  **Validation Against Success Metrics**: Table comparing target metrics (from `Idea.md`) against achieved results.
3.  **Broader Impact on Accessibility**: Expand the Societal Impact section with specific statistics on global visual impairment (WHO data).

---

### 9. Expand Chapter 10: Conclusion & Future Work
**New Content:**
1.  **Reflection on Development Journey**: Tie back to the iterative phases.
2.  **Extended Future Work**: Add specific items like YOLO26 migration, on-device LLM exploration (Ollama lessons), and formal IRB-approved user studies.

---

## Execution Order
1.  Remove Appendices A & B.
2.  Add "Project Evolution & Iterations" chapter after Methodology.
3.  Expand Literature Review with tables from LitReview docs.
4.  Expand Methodology with Timeline/Hardware tables.
5.  Expand Technical Implementation with service details.
6.  Expand Results with historical comparison.
7.  Expand Discussion with gap validation.
8.  Expand Conclusion with reflection.
