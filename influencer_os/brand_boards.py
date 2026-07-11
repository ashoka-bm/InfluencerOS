"""Reusable personal-brand-board projection over a creator-specific JSON spec."""

import hashlib
import html
import os
import re
import tempfile
from pathlib import Path

from influencer_os.validation import ValidationError, load_json, validate_file


TEMPLATE_PATH = Path(__file__).with_name("templates") / "personal-brand-board.html"
SPEC_RELATIVE_PATH = Path("references/brand/personal-brand-board.json")
BOARD_RELATIVE_PATH = Path("references/brand/personal-brand-board.html")
SOURCE_DIGEST_PATTERN = re.compile(
    r'<meta name="influencer-os-brand-board-source-digest" content="([0-9a-f]{64})">'
)
GENERIC_FAMILIES = {"serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"}
AVATAR_ASSET_TYPES = {"brand", "character"}
AVATAR_READY_STATUSES = {"prompted", "user_provided", "generated", "approved"}


def spec_path_for(workspace_dir):
    return Path(workspace_dir) / SPEC_RELATIVE_PATH


def brand_board_path_for(workspace_dir):
    return Path(workspace_dir) / BOARD_RELATIVE_PATH


def _source_digest(spec_path, reference_library_path):
    digest = hashlib.sha256()
    for path in (Path(spec_path), Path(reference_library_path), TEMPLATE_PATH, Path(__file__)):
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _semantic_validate(spec, spec_path):
    roles = [item["role"] for item in spec["palette"]]
    required_roles = {"Base", "Surface", "Primary", "Text"}
    missing = sorted(required_roles - set(roles))
    if missing:
        raise ValidationError(f"{spec_path}: palette is missing required roles {missing}")
    if len(roles) != len(set(roles)):
        raise ValidationError(f"{spec_path}: palette roles must be unique")
    if sum(int(item["usage"].removesuffix("%")) for item in spec["palette"]) != 100:
        raise ValidationError(f"{spec_path}: palette usage percentages must total 100%")
    for role, item in spec["typography"].items():
        families = [part.strip().strip("'\"").lower() for part in item["stack"].split(",")]
        if not families or families[-1] not in GENERIC_FAMILIES:
            raise ValidationError(
                f"{spec_path}: typography.{role}.stack must end in a generic CSS family"
            )


def _load_spec(workspace_dir):
    spec_path = spec_path_for(workspace_dir)
    if not spec_path.exists():
        raise FileNotFoundError(f"Missing personal brand board spec: {spec_path}")
    validate_file("personal-brand-board", spec_path)
    spec = load_json(spec_path)
    _semantic_validate(spec, spec_path)
    reference_library_path = Path(workspace_dir) / "references" / "reference-library.json"
    if not reference_library_path.exists():
        raise FileNotFoundError(f"Missing reference library: {reference_library_path}")
    validate_file("reference-library", reference_library_path)
    reference_library = load_json(reference_library_path)
    return spec_path, spec, reference_library_path, reference_library


def _asset_media_source(
    workspace_dir,
    assets_by_id,
    asset_id,
    *,
    label,
    expected_types,
    allowed_statuses,
    placeholder_statuses,
):
    asset = assets_by_id.get(asset_id)
    if asset is None:
        raise ValidationError(f"brand board references missing {label} asset {asset_id!r}")
    if asset["asset_type"] not in expected_types:
        expected = " or ".join(sorted(expected_types))
        raise ValidationError(
            f"brand board {label} asset {asset_id!r}: expected {expected}, "
            f"got {asset['asset_type']}"
        )
    if asset["asset_status"] not in allowed_statuses:
        allowed = ", ".join(sorted(allowed_statuses))
        raise ValidationError(
            f"brand board {label} asset {asset_id!r} must use one of these statuses: "
            f"{allowed}"
        )
    if asset["asset_status"] in placeholder_statuses:
        return ""
    source = asset["path"]
    suffix = Path(source).suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp", ".avif"}:
        raise ValidationError(
            f"brand board {label} asset {asset_id!r} must use a supported image file"
        )
    source_path = (Path(workspace_dir) / source).resolve()
    if not source_path.is_file():
        raise ValidationError(f"brand board {label} asset is missing: {source}")
    return source


def _reference_media_source(workspace_dir, assets_by_id, asset_id, expected_type):
    return _asset_media_source(
        workspace_dir,
        assets_by_id,
        asset_id,
        label=expected_type,
        expected_types={expected_type},
        allowed_statuses={"planned", "prompted", "user_provided", "generated", "approved"},
        placeholder_statuses={"planned", "prompted"},
    )


def _avatar_media_source(workspace_dir, assets_by_id, asset_id):
    return _asset_media_source(
        workspace_dir,
        assets_by_id,
        asset_id,
        label="avatar",
        expected_types=AVATAR_ASSET_TYPES,
        allowed_statuses=AVATAR_READY_STATUSES,
        placeholder_statuses={"prompted"},
    )


def _esc(value):
    return html.escape(str(value or ""), quote=True)


def _css_stack(value):
    return str(value).replace("\\", "\\\\").replace(";", "")


def _image(workspace_dir, output_dir, source, alt, class_name=""):
    if not source:
        initials = "".join(part[:1] for part in alt.split()[:2]).upper() or "PB"
        return f'<div class="image-placeholder {class_name}">{_esc(initials)}</div>'
    source_path = (Path(workspace_dir) / source).resolve()
    workspace_root = Path(workspace_dir).resolve()
    if not source_path.is_relative_to(workspace_root) or not source_path.is_file():
        raise ValidationError(f"brand board image must resolve inside the workspace: {source}")
    relative = os.path.relpath(source_path, output_dir)
    return f'<img class="{_esc(class_name)}" src="{_esc(relative)}" alt="{_esc(alt)}">'


def _list(items):
    return "".join(f"<li>{_esc(item)}</li>" for item in items)


def _chips(items, anti=False):
    klass = "chips anti" if anti else "chips"
    return f'<div class="{klass}">' + "".join(
        f'<span class="chip">{_esc(item)}</span>' for item in items
    ) + "</div>"


def _replace_once(template, placeholder, value):
    if template.count(placeholder) != 1:
        raise ValidationError(f"brand board template must contain exactly one {placeholder}")
    return template.replace(placeholder, value)


def _write_text_atomic(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", text=True
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


def _render(workspace_dir, spec_path, spec, reference_library_path, reference_library):
    output_path = brand_board_path_for(workspace_dir)
    output_dir = output_path.parent
    palette = spec["palette"]
    colors = {item["role"]: item["hex"].upper() for item in palette}
    typography = spec["typography"]
    assets_by_id = {asset["asset_id"]: asset for asset in reference_library["assets"]}
    swatches = "".join(
        '<article class="swatch"><div class="swatch-color" style="background:'
        f'{_esc(item["hex"].upper())}"></div><strong>{_esc(item["name"])}</strong>'
        f'<code>{_esc(item["hex"].upper())}</code><span>{_esc(item["role"])} / '
        f'{_esc(item["usage"])}</span></article>'
        for item in palette
    )
    type_rows = "".join(
        f'<article class="type-row {role}"><span class="label">{_esc(role.replace("_", " "))}</span>'
        f'<div class="type-sample">{_esc(item["sample"])}</div><div class="type-meta">'
        f'<strong>{_esc(item["name"])}</strong><code>{_esc(item["stack"])}</code>'
        f'<span>{_esc(item["spec"])}</span></div></article>'
        for role, item in typography.items()
    )
    production_spaces = "".join(
        '<article class="space">'
        + _image(
            workspace_dir,
            output_dir,
            _reference_media_source(
                workspace_dir, assets_by_id, item["reference_asset_id"], "location"
            ),
            item["title"],
        )
        + f'<div class="space-copy"><strong>{_esc(item["title"])}</strong><p>{_esc(item["purpose"])}</p>'
        + f'<span class="label">Best for</span><ul>{_list(item["best_for"])}</ul>'
        + f'<span class="label">Continuity</span><p>{_esc(item["continuity_notes"])}</p></div></article>'
        for item in spec["production_spaces"]
    )
    prop_cards = "".join(
        '<article class="prop">'
        + _image(
            workspace_dir,
            output_dir,
            _reference_media_source(
                workspace_dir, assets_by_id, item["reference_asset_id"], "object"
            ),
            item["title"],
        )
        + f'<div class="prop-copy"><strong>{_esc(item["title"])}</strong><p>{_esc(item["role"])}</p>'
        + f'<span class="label">Best for</span><ul>{_list(item["best_for"])}</ul>'
        + f'<span class="label">Continuity</span><p>{_esc(item["continuity_notes"])}</p></div></article>'
        for item in spec["signature_props"]
    )
    signature_props_section = (
        '<section class="content"><h2 class="section-title">Signature Props</h2>'
        f'<div class="props">{prop_cards}</div></section>'
        if prop_cards else ""
    )
    rule_panels = "".join(
        f'<article class="rule-panel"><span class="label">{_esc(title)}</span><ul>{_list(spec["imagery_rules"][key])}</ul></article>'
        for title, key in (("Framing", "framing"), ("Lighting", "lighting"), ("Use", "use"), ("Avoid", "avoid"))
    )
    templates = "".join(
        f'<article class="content-template {"accent" if item.get("variant") == "accent" else ""}">'
        + (_image(workspace_dir, output_dir, item["image"], item["title"]) if item["image"] else "")
        + f'<span class="label">{_esc(item["title"])}</span><h3>{_esc(item["headline"])}</h3><p>{_esc(item["caption"])}</p></article>'
        for item in spec["content_templates"]
    )
    sliders = "".join(
        f'<div class="slider"><div><span>{_esc(item["left"])}</span><span>{_esc(item["right"])}</span></div>'
        f'<div class="track"><i style="left:{item["position"]}%"></i></div></div>'
        for item in spec["voice"]["sliders"]
    )
    pillars = "".join(
        f'<article class="pillar"><span class="pillar-index">{index:02d}</span>'
        f'<h3>{_esc(item["name"])}</h3><p>{_esc(item["description"])}</p></article>'
        for index, item in enumerate(spec["pillars"], start=1)
    )
    notes = "".join(
        f'<article class="note"><span class="label">{_esc(item["title"])}</span><p>{_esc(item["body"])}</p></article>'
        for item in spec["qa_notes"]
    )
    replacements = {
        "__SOURCE_DIGEST__": _source_digest(spec_path, reference_library_path),
        "__DOCUMENT_TITLE__": _esc(f'{spec["name"]} Personal Brand Board'),
        "__BASE__": colors["Base"],
        "__SURFACE__": colors["Surface"],
        "__PRIMARY__": colors["Primary"],
        "__TEXT__": colors["Text"],
        "__DISPLAY_STACK__": _css_stack(typography["display"]["stack"]),
        "__SUBHEAD_STACK__": _css_stack(typography["subhead"]["stack"]),
        "__BODY_STACK__": _css_stack(typography["body"]["stack"]),
        "__DATA_STACK__": _css_stack(typography["caption_data"]["stack"]),
        "__BOARD_TYPE__": _esc(spec["board_type"].replace("_", " ").title()),
        "__HERO_IMAGE__": _image(workspace_dir, output_dir, spec["hero_image"], spec["name"], "hero-image"),
        "__NAME__": _esc(spec["name"]),
        "__HANDLE__": _esc(spec["handle"]),
        "__TAGLINE__": _esc(spec["tagline"]),
        "__DESCRIPTOR__": _esc(spec["descriptor"]),
        "__SUMMARY__": _esc(spec["summary"]),
        "__AUDIENCE__": _esc(spec["audience"]),
        "__PROMISE__": _esc(spec["promise"]),
        "__DIFFERENTIATOR__": _esc(spec["differentiator"]),
        "__ADJECTIVES__": _chips(spec["brand_adjectives"]),
        "__ANTI_ADJECTIVES__": _chips(spec["anti_adjectives"], True),
        "__SWATCHES__": swatches,
        "__WORDMARK__": _esc(spec["wordmark"]["primary"]),
        "__HANDLE_TREATMENT__": _esc(spec["wordmark"]["handle_treatment"]),
        "__SUBMARK__": _esc(spec["wordmark"]["submark"]),
        "__AVATAR__": _image(
            workspace_dir,
            output_dir,
            _avatar_media_source(
                workspace_dir, assets_by_id, spec["avatar_asset_id"]
            ),
            "Avatar crop",
            "avatar",
        ),
        "__AVATAR_GUIDANCE__": _esc(spec["wordmark"]["avatar_guidance"]),
        "__TYPE_ROWS__": type_rows,
        "__PRODUCTION_SPACES__": production_spaces,
        "__SIGNATURE_PROPS_SECTION__": signature_props_section,
        "__RULE_PANELS__": rule_panels,
        "__CONTENT_TEMPLATES__": templates,
        "__HEADLINES__": _list(spec["voice"]["headlines"]),
        "__CAPTION_STARTERS__": _list(spec["voice"]["caption_starters"]),
        "__USE_WORDS__": _esc(", ".join(spec["voice"]["use_words"])),
        "__AVOID_WORDS__": _esc(", ".join(spec["voice"]["avoid_words"])),
        "__SLIDERS__": sliders,
        "__PILLARS__": pillars,
        "__QA_NOTES__": notes,
        "__FOOTER__": "".join(f"<span>{_esc(item)}</span>" for item in spec["footer"]),
    }
    output = TEMPLATE_PATH.read_text()
    for placeholder, value in replacements.items():
        output = _replace_once(output, placeholder, value)
    return output_path, output


def rebuild_brand_board(workspace_path):
    workspace_dir = Path(workspace_path)
    spec_path, spec, reference_library_path, reference_library = _load_spec(workspace_dir)
    output_path, output = _render(
        workspace_dir, spec_path, spec, reference_library_path, reference_library
    )
    _write_text_atomic(output_path, output)
    return {
        "board_path": output_path,
        "source_digest": _source_digest(spec_path, reference_library_path),
    }


def validate_brand_board(workspace_path):
    workspace_dir = Path(workspace_path)
    spec_path, spec, reference_library_path, reference_library = _load_spec(workspace_dir)
    output_path = brand_board_path_for(workspace_dir)
    if not output_path.exists():
        raise FileNotFoundError(f"Missing personal brand board: {output_path} (run rebuild-brand-board)")
    actual = output_path.read_text()
    match = SOURCE_DIGEST_PATTERN.search(actual)
    expected_digest = _source_digest(spec_path, reference_library_path)
    if match is None or match.group(1) != expected_digest:
        raise ValidationError(f"{output_path}: stale personal brand board projection (run rebuild-brand-board)")
    _expected_path, expected = _render(
        workspace_dir, spec_path, spec, reference_library_path, reference_library
    )
    if actual != expected:
        raise ValidationError(f"{output_path}: rendered content does not match its sources (run rebuild-brand-board)")
    return {
        "board_path": output_path,
        "source_digest": expected_digest,
        "approval_status": spec["approval_status"],
    }
