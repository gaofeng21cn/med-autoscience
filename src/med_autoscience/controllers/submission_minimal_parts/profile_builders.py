from .shared import *
from .markdown_surface import *

def should_build_general_medical_submission_markdown(*, compiled_text: str) -> bool:
    metadata, _ = split_front_matter(compiled_text)
    if compiled_text.lstrip().startswith("# Draft"):
        return True
    return not metadata.get("title") or not metadata.get("bibliography")


def build_general_medical_submission_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    paper_root = compiled_markdown_path.parent if compiled_markdown_path.name == "draft.md" else compiled_markdown_path.parents[1]
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    main_tables = ""
    main_figures = ""
    figure_semantics_map: dict[str, dict[str, Any]] = {}
    manuscript_title, manuscript_sections, manuscript_auxiliary_blocks = parse_manuscript_shaped_draft(compiled_text)

    if compiled_text.lstrip().startswith("# Draft"):
        title = extract_block_between_markers(
            compiled_text,
            start_marker="## Title\n\n",
            end_markers=["\n## Abstract\n"],
            label="Title",
        )
        abstract = extract_block_between_markers(
            compiled_text,
            start_marker="## Abstract\n\n",
            end_markers=["\n## Introduction\n", "\n## Methods\n", "\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Abstract",
        )
        introduction = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Introduction\n\n",
            end_markers=["\n## Methods\n", "\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Introduction",
        )
        methods = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Methods\n\n",
            end_markers=["\n## Results\n", "\n## Discussion\n", "\n## Conclusion\n"],
            label="Methods",
        )
        results = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Results\n\n",
            end_markers=["\n## Discussion\n", "\n## Conclusion\n"],
            label="Results",
        )
        discussion = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Discussion\n\n",
            end_markers=["\n## Conclusion\n"],
            label="Discussion",
        )
        conclusion = extract_optional_block_between_markers(
            compiled_text,
            start_marker="\n## Conclusion\n\n",
            end_markers=[],
            label="Conclusion",
        )
        bibliography_path = (paper_root / "references.bib").resolve()
    elif manuscript_title and (manuscript_sections or manuscript_auxiliary_blocks):
        title = manuscript_title
        abstract = first_nonempty_block(manuscript_sections, "Abstract")
        introduction = first_nonempty_block(manuscript_sections, "Introduction")
        methods = first_nonempty_block(manuscript_sections, "Methods", "Materials and Methods", "Materials & Methods")
        results = first_nonempty_block(manuscript_sections, "Results")
        discussion = first_nonempty_block(manuscript_sections, "Discussion")
        conclusion = first_nonempty_block(manuscript_sections, "Conclusion", "Conclusions")
        main_tables = first_nonempty_block(manuscript_sections, "Main Tables", "Tables")
        if not main_tables:
            main_tables = first_nonempty_named_block(manuscript_auxiliary_blocks, "Main Tables", "Tables")
        main_figures = first_nonempty_block(manuscript_sections, "Main Figures", "Figures", "Main-text figures")
        if not main_figures:
            main_figures = first_nonempty_named_block(
                manuscript_auxiliary_blocks,
                "Main Figures",
                "Figures",
                "Main-text figures",
            )
        figure_semantics_map = load_figure_semantics_map(paper_root)
        bibliography_path = (paper_root / "references.bib").resolve()
    else:
        title = metadata.get("title", "Article Title")
        bibliography_value = metadata.get("bibliography", "../references.bib")
        bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
        abstract = extract_optional_markdown_block(
            body,
            "Abstract",
            ["Introduction", "Methods", "Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        introduction = extract_optional_markdown_block(
            body,
            "Introduction",
            ["Methods", "Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        methods = extract_optional_markdown_block(
            body,
            "Methods",
            ["Results", "Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        results = extract_optional_markdown_block(
            body,
            "Results",
            ["Discussion", "Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        discussion = extract_optional_markdown_block(
            body,
            "Discussion",
            ["Conclusion", "Main Tables", "Main Figures", "Appendix"],
        )
        conclusion = extract_optional_markdown_block(
            body,
            "Conclusion",
            ["Main Tables", "Main Figures", "Appendix"],
        )
        main_tables = extract_optional_markdown_block(body, "Main Tables", ["Main Figures", "Appendix"])
        main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix"])
        if not main_figures.strip():
            main_figures = extract_optional_markdown_block(body, "Figures", ["Figure Legends", "Tables", "Appendix"])
        figure_semantics_map = load_figure_semantics_map(paper_root)

    if not main_figures.strip():
        main_figures = build_catalog_backed_main_figures(
            paper_root=paper_root,
            submission_root=submission_root,
        )
        if main_figures.strip() and not figure_semantics_map:
            figure_semantics_map = load_figure_semantics_map(paper_root)

    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())
    catalog_image_map = build_catalog_backed_submission_figure_image_map(
        paper_root=paper_root,
        submission_root=submission_root,
    )
    submission_figure_blocks = build_submission_figure_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
        catalog_image_map=catalog_image_map,
    )
    figure_legend_blocks = build_figure_legend_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
    )
    table_blocks = build_table_blocks(main_tables=main_tables)
    section_blocks = [
        ("# Abstract", abstract),
        ("# Introduction", introduction),
        ("# Methods", methods),
        ("# Results", results),
        ("# Discussion", discussion),
        ("# Conclusion", conclusion),
    ]
    markdown_parts = [
        "---\n"
        f'title: "{title}"\n'
        f"bibliography: {bibliography_rel}\n"
        "link-citations: true\n"
        "---"
    ]
    for heading, content in section_blocks:
        if content.strip():
            markdown_parts.append(f"{heading}\n\n{content.strip()}")
    if submission_figure_blocks:
        markdown_parts.append(f"# Figures\n\n{'\n\n'.join(submission_figure_blocks).strip()}")
    if figure_legend_blocks:
        markdown_parts.append(f"# Figure Legends\n\n{'\n\n'.join(figure_legend_blocks).strip()}")
    if table_blocks:
        markdown_parts.append(f"# Tables\n\n{'\n\n'.join(table_blocks).strip()}")
    output_path = submission_root / "manuscript_submission.md"
    write_text(output_path, "\n\n".join(markdown_parts).strip() + "\n")
    return output_path


def build_frontiers_manuscript_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    paper_root = compiled_markdown_path.parents[1]
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    title = metadata.get("title", "Article Title")
    bibliography_value = metadata.get("bibliography", "../references.bib")
    bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())

    abstract = extract_markdown_block(
        body,
        "Abstract",
        ["Introduction", "Methods", "Results", "Discussion", "Main Figures", "Main Tables", "Appendix"],
    )
    introduction = extract_optional_markdown_block(
        body,
        "Introduction",
        ["Methods", "Results", "Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    methods = extract_optional_markdown_block(
        body,
        "Methods",
        ["Results", "Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    results = extract_optional_markdown_block(
        body,
        "Results",
        ["Discussion", "Main Tables", "Main Figures", "Appendix"],
    )
    discussion = extract_optional_markdown_block(
        body,
        "Discussion",
        ["Main Tables", "Main Figures", "Appendix"],
    )
    main_tables = extract_optional_markdown_block(body, "Main Tables", ["Main Figures"])
    main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix"])
    figure_semantics_map = load_figure_semantics_map(paper_root)

    figure_legend_blocks = build_figure_legend_blocks(
        main_figures=main_figures,
        figure_semantics_map=figure_semantics_map,
    )
    table_blocks = build_table_blocks(main_tables=main_tables)

    markdown_text = (
        f"---\n"
        f'title: "{title}"\n'
        f"bibliography: {bibliography_rel}\n"
        f"link-citations: true\n"
        f"---\n\n"
        f"Authors: [To be completed before submission.]\n\n"
        f"Affiliations: [To be completed before submission.]\n\n"
        f"*Correspondence:* [To be completed before submission.]\n\n"
        f"Keywords: {', '.join(FRONTIERS_KEYWORDS)}\n\n"
        f"# Abstract\n\n{abstract}\n\n"
        f"# Introduction\n\n{introduction}\n\n"
        f"# Materials and methods\n\n{methods}\n\n"
        f"# Results\n\n{results}\n\n"
        f"# Discussion\n\n{discussion}\n\n"
        f"{build_frontiers_required_sections()}\n\n"
        f"# Figure Legends\n\n{'\n\n'.join(figure_legend_blocks).strip()}\n\n"
        f"# Tables\n\n{'\n\n'.join(table_blocks).strip()}\n"
    )
    output_path = submission_root / "frontiers_manuscript.md"
    write_text(output_path, markdown_text)
    return output_path


def build_frontiers_supplementary_markdown(
    *,
    compiled_markdown_path: Path,
    submission_root: Path,
    compiled_markdown_text: str | None = None,
) -> Path:
    compiled_text = compiled_markdown_text if compiled_markdown_text is not None else compiled_markdown_path.read_text(encoding="utf-8")
    metadata, body = split_front_matter(compiled_text)
    bibliography_value = metadata.get("bibliography", "../references.bib")
    bibliography_path = (compiled_markdown_path.parent / bibliography_value).resolve()
    bibliography_rel = os.path.relpath(bibliography_path, submission_root.resolve())
    appendix = extract_optional_markdown_block(body, "Appendix", [])
    if not appendix.strip():
        main_figures = extract_optional_markdown_block(body, "Main Figures", ["Appendix", "Main Tables"])
        supplementary_blocks = [
            f"## {heading}\n\n{block_body}"
            for heading, block_body in parse_heading_blocks(main_figures, "Supplementary Figure ")
        ]
        appendix = "\n\n".join(supplementary_blocks).strip()
    rewritten_appendix = rewrite_image_paths(
        markdown_text=appendix,
        source_markdown_dir=compiled_markdown_path.parent,
        target_markdown_dir=submission_root,
    )
    markdown_text = (
        "---\n"
        'title: "Supplementary Material"\n'
        f"bibliography: {bibliography_rel}\n"
        "link-citations: true\n"
        "---\n\n"
        "# Supplementary Material\n\n"
        "This file contains supplementary figures and appendix material prepared for journal submission.\n\n"
        f"{rewritten_appendix.strip()}\n"
    )
    output_path = submission_root / "frontiers_supplementary_material.md"
    write_text(output_path, markdown_text)
    return output_path


