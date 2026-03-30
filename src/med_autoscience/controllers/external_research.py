from __future__ import annotations

from datetime import date
from pathlib import Path

from med_autoscience.controllers import portfolio_memory as portfolio_memory_controller


EXTERNAL_RESEARCH_SCHEMA_VERSION = 1
DEFAULT_PROMPT_TOPIC = "workspace-topic-opportunity"
DEFAULT_REPORT_NAMING_PATTERN = "YYYY-MM-DD-topic-opportunity-scout-<provider>.md"


def _research_memory_root(workspace_root: Path) -> Path:
    return workspace_root / "portfolio" / "research_memory"


def _prompts_root(workspace_root: Path) -> Path:
    return _research_memory_root(workspace_root) / "prompts"


def _external_reports_root(workspace_root: Path) -> Path:
    return _research_memory_root(workspace_root) / "external_reports"


def _resolve_as_of_date(as_of_date: str | None) -> str:
    if as_of_date is None:
        return date.today().isoformat()
    return date.fromisoformat(as_of_date).isoformat()


def _prompt_filename(*, as_of_date: str) -> str:
    return f"{as_of_date}-{DEFAULT_PROMPT_TOPIC}-deep-research-prompt.md"


def _read_markdown_or_stub(*, workspace_root: Path, filename: str, fallback_title: str) -> str:
    path = _research_memory_root(workspace_root) / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return f"# {fallback_title}\n\n当前 workspace 尚未写入该资产。\n"


def _render_prompt(*, workspace_root: Path, as_of_date: str) -> str:
    topic_landscape = _read_markdown_or_stub(
        workspace_root=workspace_root,
        filename="topic_landscape.md",
        fallback_title="Disease Topic Landscape",
    )
    dataset_question_map = _read_markdown_or_stub(
        workspace_root=workspace_root,
        filename="dataset_question_map.md",
        fallback_title="Dataset Question Map",
    )
    venue_intelligence = _read_markdown_or_stub(
        workspace_root=workspace_root,
        filename="venue_intelligence.md",
        fallback_title="Venue Intelligence",
    )
    return (
        "# Workspace Topic Opportunity Deep Research Prompt\n\n"
        f"- 生成日期：{as_of_date}\n"
        f"- workspace：{workspace_root.name}\n\n"
        "## 你的角色\n\n"
        "你是一名偏医学论文选题与研究设计的 deep research analyst。你的目标不是写一篇空泛综述，而是基于我当前已经拿到的数据，帮助我筛出真正值得做、且有现实投稿机会的 SCI 论文方向。\n\n"
        "## 当前任务\n\n"
        "请围绕这个糖尿病研究 workspace，回答：\n\n"
        "1. 基于现有数据，最值得优先推进的 1-3 个论文方向是什么\n"
        "2. 第一篇论文最现实的设计应该怎么定\n"
        "3. 是否需要方法学创新，如果不需要，应该靠什么把文章做厚\n"
        "4. 是否值得引入易获取的外部公开数据，以及这些数据最合理的用途是什么\n"
        "5. 这些方向理想情况下大致能投到什么档次、什么邻域的期刊\n\n"
        "## 已知硬边界\n\n"
        "- refs/ 只用于理解数据与历史背景，不代表要复现旧代码、继承旧分析流程，或沿旧半成品课题继续执行。\n"
        "- 当前任务是做课题与论文布局，不是去重跑 legacy code。\n"
        "- 外部公开数据只考虑网上非常容易公开获取、可快速下载的数据；不要建议准入复杂、申请周期长的数据源。\n"
        "- 请优先评估“临床问题是否强、数据结构是否支持、叙事是否站得住”，不要先入为主地假设必须依赖炫技方法学创新。\n"
        "- 如果你判断第一篇不适合强求方法学创新，请直接说明为什么，并给出更现实的强化路径。\n"
        "- 已有一个重要 sidecar 候选是美国 `NHANES` mortality public-use 数据。请重点评估它是否适合形成中美对比、transportability、generalizability 或 calibration/shift 叙事，而不只是机械做鲁棒性验证。\n"
        "- 选刊时不要只看期刊官网 scope。请优先检索相似论文真实发到了哪些期刊，再给出现实主投带、stretch 带和 backup 带判断。\n\n"
        "## 当前已知数据背景\n\n"
        "- 中国 40 多家医院的糖尿病多中心临床数据是主数据底座。\n"
        "- 这个 workspace 的第一篇论文倾向于围绕 hard outcome、生存分析与风险分层来设计。\n"
        "- NHANES public mortality sidecar 已获取，可作为公开外部数据补强层。\n\n"
        "## 你必须输出的内容\n\n"
        "### 1. Executive Summary\n\n"
        "- 用最短篇幅回答：这批数据最该先做什么，为什么。\n\n"
        "### 2. Topic Shortlist Table\n\n"
        "请给出 3 个以内候选方向，表格至少包括：\n\n"
        "- topic name\n"
        "- core clinical question\n"
        "- primary endpoint\n"
        "- required data assets\n"
        "- role of external public data\n"
        "- novelty source\n"
        "- main risk\n"
        "- realistic journal band\n"
        "- priority\n\n"
        "### 3. Top 3 Detailed Assessment\n\n"
        "对每个候选方向分别说明：\n\n"
        "- 为什么这个问题值得做\n"
        "- 现有数据能不能真的支撑它\n"
        "- 需要不需要方法学创新\n"
        "- 最可能卡死它的点是什么\n"
        "- 如果第一版阴性或不够强，应该如何在同一论文内部调整路线，而不是立即废题\n\n"
        "### 4. First-paper Recommendation\n\n"
        "请明确推荐第一篇论文，并写清：\n\n"
        "- 推荐题目方向\n"
        "- 最合理的 primary / secondary endpoints\n"
        "- 中国主数据与 NHANES 各自扮演什么角色\n"
        "- 论文理想的图表/结果结构大概是什么\n"
        "- 哪些分析必须在同一篇里完成，哪些应该留给 future study\n\n"
        "### 5. Future Study Map\n\n"
        "说明同一批数据在第一篇之后还能自然分叉出的 future studies，但不要把本应留在同一篇里的 sensitivity analyses 或模型比较伪装成新课题。\n\n"
        "### 6. Venue Intelligence\n\n"
        "请基于 similar-paper 落刊证据，而不是仅靠官网 scope，给出：\n\n"
        "- 现实主投带\n"
        "- stretch 带\n"
        "- backup 带\n"
        "- 每个带的代表性相似论文或相似主题落刊\n"
        "- 为什么这篇第一文更像 diabetes / cardiometabolic / cardiovascular 哪一类稿件\n\n"
        "## 返回文档放置规则\n\n"
        "请把完整返回整理成一份可以直接保存的 Markdown 文档。默认保存位置是：\n\n"
        f"- `portfolio/research_memory/external_reports/{DEFAULT_REPORT_NAMING_PATTERN}`\n\n"
        "后续如果其中有稳定结论，会再回写到：\n\n"
        "- `portfolio/research_memory/topic_landscape.md`\n"
        "- `portfolio/research_memory/dataset_question_map.md`\n"
        "- `portfolio/research_memory/venue_intelligence.md`\n\n"
        "## 当前 workspace 研究记忆\n\n"
        "下面这些内容代表当前 workspace 已经形成的显式研究记忆。请在此基础上继续，不要忽略它们重新从空白开始想。\n\n"
        "### Topic Landscape\n\n"
        f"{topic_landscape}\n\n"
        "### Dataset Question Map\n\n"
        f"{dataset_question_map}\n\n"
        "### Venue Intelligence\n\n"
        f"{venue_intelligence}\n"
    )


def prepare_external_research(*, workspace_root: Path, as_of_date: str | None = None) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    portfolio_memory_controller.init_portfolio_memory(workspace_root=resolved_workspace_root)
    prompts_root = _prompts_root(resolved_workspace_root)
    external_reports_root = _external_reports_root(resolved_workspace_root)
    created_directories: list[str] = []
    for path in (prompts_root, external_reports_root):
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_directories.append(str(path))

    resolved_as_of_date = _resolve_as_of_date(as_of_date)
    prompt_path = prompts_root / _prompt_filename(as_of_date=resolved_as_of_date)
    created_files: list[str] = []
    skipped_files: list[str] = []
    if prompt_path.exists():
        skipped_files.append(str(prompt_path))
    else:
        prompt_path.write_text(
            _render_prompt(workspace_root=resolved_workspace_root, as_of_date=resolved_as_of_date),
            encoding="utf-8",
        )
        created_files.append(str(prompt_path))

    return {
        "schema_version": EXTERNAL_RESEARCH_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "research_memory_root": str(_research_memory_root(resolved_workspace_root)),
        "prompts_root": str(prompts_root),
        "external_reports_root": str(external_reports_root),
        "prompt_path": str(prompt_path),
        "created_directories": created_directories,
        "created_files": created_files,
        "skipped_files": skipped_files,
        "status": "ready",
        "report_naming_pattern": DEFAULT_REPORT_NAMING_PATTERN,
        "write_back_targets": [
            "portfolio/research_memory/topic_landscape.md",
            "portfolio/research_memory/dataset_question_map.md",
            "portfolio/research_memory/venue_intelligence.md",
        ],
        "recommendations": [
            "external_research_prompt_ready",
            "external_research_is_optional_enrichment",
        ],
    }


def external_research_status(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    prompts_root = _prompts_root(resolved_workspace_root)
    external_reports_root = _external_reports_root(resolved_workspace_root)
    prompt_files = sorted(path for path in prompts_root.glob("*.md") if path.is_file()) if prompts_root.exists() else []
    external_reports = (
        sorted(path for path in external_reports_root.glob("*.md") if path.is_file()) if external_reports_root.exists() else []
    )
    recommendations: list[str] = []
    if prompt_files:
        recommendations.append("external_research_prompt_ready")
    else:
        recommendations.append("prepare_external_research_prompt")
    if external_reports:
        recommendations.append("review_external_reports_and_write_back_stable_findings")
    else:
        recommendations.append("external_research_optional_not_yet_run")
    return {
        "schema_version": EXTERNAL_RESEARCH_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "research_memory_root": str(_research_memory_root(resolved_workspace_root)),
        "prompts_root": str(prompts_root),
        "external_reports_root": str(external_reports_root),
        "prompt_file_count": len(prompt_files),
        "external_report_count": len(external_reports),
        "prompt_files": [str(path) for path in prompt_files],
        "external_reports": [str(path) for path in external_reports],
        "optional_module_ready": prompts_root.exists() and external_reports_root.exists() and bool(prompt_files),
        "report_naming_pattern": DEFAULT_REPORT_NAMING_PATTERN,
        "recommendations": recommendations,
    }
