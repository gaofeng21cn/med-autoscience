<p align="center">
  <img src="assets/branding/medautoscience-logo.png" alt="Med Auto Science logo" width="132" />
</p>

<p align="center">
  <a href="./README.md"><strong>English</strong></a> | <a href="./README.zh-CN.md">中文</a>
</p>

<!--
Owner: MedAutoScience
Purpose: public repository entry
State: current_public_entry
Machine boundary: Human-readable public entry only. Machine truth remains in agent/, contracts, MAS domain-handler/authority results, OPL generated/readback surfaces, study workspace artifacts, and owner receipts.
-->

<h1 align="center">Med Auto Science</h1>

<p align="center"><strong>An AI research agent for real medical studies, built to turn data, evidence, and drafts into manuscript-ready work</strong></p>
<p align="center">Disease Studies · Evidence Building · Analysis Support · Manuscript Delivery</p>

<table>
  <tr>
    <td width="33%" valign="top">
      <strong>Who It Serves</strong><br/>
      Clinicians, PIs, and medical research teams working with disease-specific data and moving studies toward manuscripts
    </td>
    <td width="33%" valign="top">
      <strong>What It Organizes</strong><br/>
      Study questions, data assets, analysis progress, evidence gaps, and manuscript-facing files inside one governed workspace
    </td>
    <td width="33%" valign="top">
      <strong>How To Start</strong><br/>
      Tell it the disease area, the dataset you have, the question you want to answer, and the paper outcome you want
    </td>
  </tr>
</table>

<p align="center">
  <img src="assets/branding/medautoscience-overview-v3.png" alt="Med Auto Science journey from research question to publication handoff" width="100%" />
</p>

> `Med Auto Science` is for teams already doing real medical research. It keeps study questions, data, analyses, evidence, drafts, and delivery files connected on one governed study line so the work can keep moving and stay reviewable.

## Why Med Auto Science

The hard part of medical research is rarely a single paragraph. It is moving a study from data and ideas toward a paper that can be reviewed, revised, and submitted.

Medical teams often run into the same problems:

- You have data, but it is not clear which question is worth pursuing.
- You have preliminary results, but they do not yet form one manuscript line.
- Figures, drafts, analysis notes, and validation results drift across folders and conversations.
- Review, extra analysis, claim revision, and delivery files overlap until progress is hard to explain.
- Multiple disease studies run in parallel, and key evidence or decisions can be lost.

**Med Auto Science is built around those research problems.**

It organizes a medical study as a research line: frame the valuable question, prepare the data and evidence, advance analysis and validation, build the manuscript story, and keep paper-facing files ready for review and delivery.

It does not treat medical research as a rigid pipeline. A study can start with several possible directions, return to data and evidence for comparison, and gradually converge into a clearer manuscript line. AI keeps the work moving, organized, and revised; researchers keep clinical framing, claim acceptance, and final submission judgment.

## One-Sentence Quick Start

You can start with prompts like:

- "Help me find a paper-worthy question from this colorectal cancer dataset, tell me what evidence is still missing, and propose the next step."
- "I already have preliminary results. Turn them into one manuscript line and tell me what validation to do next."
- "Keep pushing this disease study toward a publishable paper, and keep the progress plus files organized as we go."

## Core Highlights

<table width="100%">
<tr>
<td width="50%" valign="top">

**Identify paper-worthy questions from data**

Start with a disease cohort, registry, or real-world dataset, then identify questions with clinical value, evidence support, and manuscript potential before piling up analyses.

</td>
<td width="50%" valign="top">

**Turn scattered results into a manuscript line**

Existing analyses, early findings, figures, and drafts are organized into a clearer research story with explicit next evidence steps.

</td>
</tr>
<tr>
<td width="50%" valign="top">

**Keep progress and delivery files together**

Tasks, files, figures, drafts, validation notes, and deliverables stay tied to the same study workspace so the line remains reviewable and easy to continue.

</td>
<td width="50%" valign="top">

**Let AI do the heavy lifting while researchers keep judgment**

AI can help prepare data, run analyses, organize evidence, and report progress. Clinical framing, claim acceptance, and final submission decisions stay with researchers and PIs.

**Compare, revise, and review repeatedly**

Medical papers do not finish in one generation. The system can keep multiple claims, evidence gaps, analysis routes, and review findings on the same research line, then keep producing the next more-reviewable manuscript and evidence package.

</td>
</tr>
</table>

## What It Helps With

- Finding a study question worth continuing from a disease-specific dataset, registry, or cohort.
- Turning existing analyses and early results into one manuscript line.
- Managing validation, subgroup analysis, calibration, clinical utility analysis, and other supporting evidence.
- Keeping multiple related studies organized in one workspace.
- Keeping paper-facing results, figures, drafts, and delivery files tied to their study.
- Comparing study claims, evidence gaps, analysis routes, and review findings inside the same study stage, then producing the next manuscript and evidence package.

## Current Position And Boundary

- `Med Auto Science` is the medical research Foundry Agent for turning disease data, study questions, evidence, and manuscript work into one governed research line.
- In the OPL family, MAS is an `OPL Package(kind=agent)`: MAS retains medical-domain authority, while OPL owns generic runtime and hosted surfaces. Package identity, capabilities, dependencies, research work items, and typed views remain independent of any one carrier or executor.
- It can be used as the Research Foundry inside One Person Lab, and it can also be called directly by Codex or another agent through stable capability entries.
- Codex is the current first-class path because it offers the best implementation and maintenance economics. Its Plugin is a carrier projection and its CLI is an executor; neither is MAS package identity or the complete installed package.
- MAS owns the medical work itself: study questions, evidence organization, manuscript direction, manuscript quality, and delivery materials. One Person Lab handles hosted runtime, progress display, recovery/retry, and the cross-agent product entry.
- Manuscript quality is governed by study charters, evidence ledgers, review records, AI reviewer workflow, publication gates, and controller records. Status panels and script checks provide supporting evidence.
- Clinical framing, claim acceptance, and final submission decisions stay with researchers and PIs.
- Journal submission and external system interaction stay under human supervision.

## How To Read This Repository

1. Potential users and medical experts should start here, then continue to the [Docs Guide](./docs/README.md).
2. Technical readers and planners should read [Project](./docs/project.md), [Status](./docs/status.md), [Architecture](./docs/architecture.md), [Invariants](./docs/invariants.md), and [Decisions](./docs/decisions.md).
3. Developers and maintainers should continue from the [Docs Guide](./docs/README.md) into `docs/active/`, `docs/runtime/`, `docs/delivery/`, `docs/references/`, and `docs/policies/`.

## Install And Start

Use `opl packages install mas` for the OPL Package. MAS requires
`mas-scholar-skills`; installing a Plugin carrier alone does not prove that the
complete Package or managed runtime is ready.

[Codex Plugin Setup](./docs/references/integration/codex_plugin.md) owns native
Codex marketplace installation, removal and installed-state checks.
[Workspace Quickstart](./docs/references/workspace/disease_workspace_quickstart.md)
covers study binding and first use. Technical ownership and verification are
documented in [Architecture](./docs/architecture.md) and [Status](./docs/status.md).

## Further Reading

- [MAS Whitepaper (HTML)](https://gaofeng21cn.github.io/one-person-lab/latest/whitepapers/mas-whitepaper.html)
- [MAS Whitepaper (PDF)](https://gaofeng21cn.github.io/one-person-lab/latest/whitepapers/mas-whitepaper.pdf)
- [Docs Guide](./docs/README.md)
- [Project](./docs/project.md)
- [Status](./docs/status.md)
- [Architecture](./docs/architecture.md)
- [Invariants](./docs/invariants.md)
- [Decisions](./docs/decisions.md)
