"""Commercial Pressure derivation (ADR 0030).

Pressure is derived, never authored: every Project stores its exact
planned Offer Integration and CTA Intensity, and the fixed matrix below
maps that pair to a pressure tier. Absent or embedded offer integration
with a direct transactional CTA is invalid state, not high pressure.
Pressure Indicator v1 maps the four tiers to 0-3 and reports the
normalized mean on a 0-100 scale while always retaining tier counts —
the score never replaces source classifications, and unknown is never
reported as zero pressure.
"""

from influencer_os.validation import ValidationError

OFFER_INTEGRATIONS = ("absent", "embedded", "contextual", "central")
CTA_INTENSITIES = ("none", "soft", "direct")
PRESSURE_TIERS = ("none", "low", "moderate", "high")
TIER_VALUES = {"none": 0, "low": 1, "moderate": 2, "high": 3}

# The ten valid cells of the ADR 0030 matrix; the two missing cells
# (absent+direct, embedded+direct) are invalid combinations.
PRESSURE_MATRIX = {
    ("absent", "none"): "none",
    ("absent", "soft"): "low",
    ("embedded", "none"): "low",
    ("embedded", "soft"): "low",
    ("contextual", "none"): "low",
    ("contextual", "soft"): "moderate",
    ("contextual", "direct"): "high",
    ("central", "none"): "moderate",
    ("central", "soft"): "high",
    ("central", "direct"): "high",
}

# Advisory only: the calendar projection warns when a platform's known
# high-pressure share exceeds this; it never blocks approvals or creation.
HIGH_PRESSURE_SHARE_ADVISORY_THRESHOLD = 0.25


def _check_vocabulary(value, allowed, label):
    if value not in allowed:
        raise ValidationError(
            f"unknown {label} {value!r}; allowed: {list(allowed)}"
        )


def derive_commercial_pressure(offer_integration, cta_intensity):
    """Map one offer-integration/CTA-intensity pair to its pressure tier.
    The two matrix holes fail as invalid state (ADR 0030)."""
    _check_vocabulary(offer_integration, OFFER_INTEGRATIONS, "offer integration")
    _check_vocabulary(cta_intensity, CTA_INTENSITIES, "CTA intensity")
    tier = PRESSURE_MATRIX.get((offer_integration, cta_intensity))
    if tier is None:
        raise ValidationError(
            f"invalid commercial expression: {offer_integration!r} offer "
            "integration cannot carry a direct transactional CTA (ADR 0030)"
        )
    return tier


def is_valid_expression(offer_integration, cta_intensity):
    """Whether the pair is a valid matrix cell (vocabulary must be known)."""
    _check_vocabulary(offer_integration, OFFER_INTEGRATIONS, "offer integration")
    _check_vocabulary(cta_intensity, CTA_INTENSITIES, "CTA intensity")
    return (offer_integration, cta_intensity) in PRESSURE_MATRIX


def pressure_indicator(tiers):
    """Pressure Indicator v1 over known pressure tiers.

    Returns known touch count, zero-filled tier counts, the 0-100
    normalized mean score, and the high-tier share. An empty input
    reports score and share as None — unknown is never scored as 0.
    """
    tier_counts = {tier: 0 for tier in PRESSURE_TIERS}
    values = []
    for tier in tiers:
        _check_vocabulary(tier, PRESSURE_TIERS, "pressure tier")
        tier_counts[tier] += 1
        values.append(TIER_VALUES[tier])
    known_touches = len(values)
    if not known_touches:
        return {
            "known_touches": 0,
            "tier_counts": tier_counts,
            "score": None,
            "high_share": None,
        }
    return {
        "known_touches": known_touches,
        "tier_counts": tier_counts,
        "score": round(sum(values) / known_touches / 3 * 100),
        "high_share": tier_counts["high"] / known_touches,
    }


def expression_within_ceilings(offer_integration, cta_intensity,
                               max_offer_integration, max_cta_intensity):
    """Whether exact planned values sit at or below the Concept Approval
    ceilings, by vocabulary order. Matrix validity is checked separately."""
    for value in (offer_integration, max_offer_integration):
        _check_vocabulary(value, OFFER_INTEGRATIONS, "offer integration")
    for value in (cta_intensity, max_cta_intensity):
        _check_vocabulary(value, CTA_INTENSITIES, "CTA intensity")
    return (
        OFFER_INTEGRATIONS.index(offer_integration)
        <= OFFER_INTEGRATIONS.index(max_offer_integration)
        and CTA_INTENSITIES.index(cta_intensity)
        <= CTA_INTENSITIES.index(max_cta_intensity)
    )
