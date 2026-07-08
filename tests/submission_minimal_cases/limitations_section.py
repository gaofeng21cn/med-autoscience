from __future__ import annotations

from med_autoscience.controllers.submission_minimal.profile_builders import (
    build_general_medical_submission_markdown,
)


def test_general_medical_submission_markdown_preserves_limitations_section(tmp_path) -> None:
    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    submission_root = paper_root / "submission_minimal"
    submission_root.mkdir()
    draft_path = paper_root / "draft.md"
    draft_path.write_text(
        """---
title: "Example title"
bibliography: references.bib
---

# Abstract

Abstract text.

# Introduction

Introduction text.

# Methods

Methods text.

# Results

Results text.

# Discussion

Discussion text.

# Limitations

Limitations text.

# Conclusion

Conclusion text.
""",
        encoding="utf-8",
    )

    output_path = build_general_medical_submission_markdown(
        compiled_markdown_path=draft_path,
        submission_root=submission_root,
    )

    output_text = output_path.read_text(encoding="utf-8")
    assert "# Limitations\n\nLimitations text." in output_text
    assert output_text.index("# Discussion") < output_text.index("# Limitations") < output_text.index("# Conclusion")

