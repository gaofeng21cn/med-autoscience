from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib import request

from med_autoscience.publication_profiles import (
    FRONTIERS_FAMILY_HARVARD_PROFILE,
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    JACS_PROFILE,
    normalize_publication_profile,
)


STYLES_ROOT = Path(__file__).resolve().parents[2] / "styles"
FRONTIERS_TEMPLATE_ZIP_URL = "https://www.frontiersin.org/Design/zip/Frontiers_Word_Templates.zip"
FRONTIERS_HARVARD_CSL_URL = "https://raw.githubusercontent.com/citation-style-language/styles/master/frontiers.csl"
FRONTIERS_KEYWORDS = [
    "NF-PitNET",
    "pituitary neuroendocrine tumor",
    "residual disease",
    "non-gross-total resection",
    "risk stratification",
    "pituitary surgery",
]
SUBMISSION_FRONT_MATTER_FIELD_ALIASES = {
    "authors": ("authors", "author"),
    "affiliations": ("affiliations",),
    "corresponding_author": ("corresponding_author", "correspondence"),
    "funding": ("funding",),
    "conflict_of_interest": ("conflict_of_interest", "conflicts_of_interest"),
    "ethics": ("ethics", "ethics_statement"),
    "data_availability": ("data_availability", "data_availability_statement"),
}


@dataclass(frozen=True)
class PublicationProfileConfig:
    publication_profile: str
    citation_style: str
    csl_path: Path
    output_dir_rel: Path
    reference_doc_path: Path | None = None
    supplementary_reference_doc_path: Path | None = None
    supplementary_docx_name: str | None = None
    journal_name: str | None = None
    journal_family: str | None = None
    reference_style_family: str | None = None

def default_ama_csl_path() -> Path:
    return STYLES_ROOT / "american-medical-association.csl"


def default_frontiers_harvard_csl_path() -> Path:
    return STYLES_ROOT / "frontiers.csl"


def default_acs_csl_path() -> Path:
    return STYLES_ROOT / "american-chemical-society.csl"


def frontiers_cache_dir() -> Path:
    xdg_cache = os.getenv("XDG_CACHE_HOME", "").strip()
    if xdg_cache:
        return Path(xdg_cache).expanduser() / "med-autoscience" / "frontiers_word_templates"
    return Path.home() / ".cache" / "med-autoscience" / "frontiers_word_templates"


def default_frontiers_template_docx_path() -> Path:
    return frontiers_cache_dir() / "Frontiers_Template.docx"


def default_frontiers_supplementary_template_docx_path() -> Path:
    return frontiers_cache_dir() / "Supplementary_Material.docx"

def resolve_override_path(env_name: str) -> Path | None:
    value = os.getenv(env_name, "").strip()
    if not value:
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"missing override resource for {env_name}: {path}")
    return path


def download_to_path(*, url: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with request.urlopen(url) as response:  # noqa: S310
        output_path.write_bytes(response.read())
    return output_path


def ensure_frontiers_word_templates() -> tuple[Path, Path]:
    manuscript_override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_TEMPLATE_DOCX")
    supplementary_override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_SUPPLEMENTARY_TEMPLATE_DOCX")
    manuscript_template = manuscript_override or default_frontiers_template_docx_path()
    supplementary_template = supplementary_override or default_frontiers_supplementary_template_docx_path()
    if manuscript_template.exists() and supplementary_template.exists():
        return manuscript_template, supplementary_template

    archive_path = frontiers_cache_dir() / "Frontiers_Word_Templates.zip"
    if not archive_path.exists():
        download_to_path(url=FRONTIERS_TEMPLATE_ZIP_URL, output_path=archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        if not manuscript_template.exists():
            manuscript_template.write_bytes(archive.read("Frontiers_Word_Templates/Frontiers_Template.docx"))
        if not supplementary_template.exists():
            supplementary_template.write_bytes(
                archive.read("Frontiers_Word_Templates/Supplementary_Material.docx")
            )
    return manuscript_template, supplementary_template


def ensure_frontiers_harvard_csl_path() -> Path:
    override = resolve_override_path("DEEPSCIENTIST_FRONTIERS_CSL")
    if override is not None:
        return override
    csl_path = default_frontiers_harvard_csl_path()
    if csl_path.exists():
        return csl_path
    return download_to_path(url=FRONTIERS_HARVARD_CSL_URL, output_path=csl_path)


def resolve_publication_profile_config(
    *,
    publication_profile: str,
    citation_style: str | None,
) -> PublicationProfileConfig:
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    normalized_citation_style = str(citation_style or "auto").strip()

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        resolved_citation_style = "AMA" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        if resolved_citation_style != "AMA":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        csl_path = default_ama_csl_path()
        if not csl_path.exists():
            raise FileNotFoundError(f"missing AMA CSL file: {csl_path}")
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=csl_path,
            output_dir_rel=Path("submission_minimal"),
        )

    if normalized_publication_profile == FRONTIERS_FAMILY_HARVARD_PROFILE:
        resolved_citation_style = (
            "FrontiersHarvard" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        )
        if resolved_citation_style != "FrontiersHarvard":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        manuscript_template, supplementary_template = ensure_frontiers_word_templates()
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=ensure_frontiers_harvard_csl_path(),
            output_dir_rel=Path("journal_submissions") / normalized_publication_profile,
            reference_doc_path=manuscript_template,
            supplementary_reference_doc_path=supplementary_template,
            supplementary_docx_name="Supplementary_Material.docx",
            journal_family="Frontiers",
            reference_style_family="FrontiersHarvard",
        )

    if normalized_publication_profile == JACS_PROFILE:
        resolved_citation_style = "ACS" if normalized_citation_style in {"", "auto"} else normalized_citation_style
        if resolved_citation_style != "ACS":
            raise ValueError(
                f"unsupported citation style for {normalized_publication_profile}: {resolved_citation_style}"
            )
        csl_path = default_acs_csl_path()
        if not csl_path.exists():
            raise FileNotFoundError(f"missing ACS CSL file: {csl_path}")
        return PublicationProfileConfig(
            publication_profile=normalized_publication_profile,
            citation_style=resolved_citation_style,
            csl_path=csl_path,
            output_dir_rel=Path("journal_submissions") / normalized_publication_profile,
            journal_name="Journal of the American Chemical Society",
            journal_family="ACS",
            reference_style_family="ACS",
        )

    raise ValueError(f"unsupported publication profile: {publication_profile}")
