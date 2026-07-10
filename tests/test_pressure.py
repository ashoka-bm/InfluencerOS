"""Exhaustive Commercial Pressure matrix and indicator tests (ADR 0030)."""

import unittest

from influencer_os.pressure import (
    CTA_INTENSITIES,
    HIGH_PRESSURE_SHARE_ADVISORY_THRESHOLD,
    OFFER_INTEGRATIONS,
    PRESSURE_MATRIX,
    PRESSURE_TIERS,
    TIER_VALUES,
    derive_commercial_pressure,
    expression_within_ceilings,
    is_valid_expression,
    pressure_indicator,
)
from influencer_os.validation import ValidationError

# The full ADR 0030 matrix, spelled out cell by cell; None marks the two
# invalid combinations.
EXPECTED_MATRIX = {
    ("absent", "none"): "none",
    ("absent", "soft"): "low",
    ("absent", "direct"): None,
    ("embedded", "none"): "low",
    ("embedded", "soft"): "low",
    ("embedded", "direct"): None,
    ("contextual", "none"): "low",
    ("contextual", "soft"): "moderate",
    ("contextual", "direct"): "high",
    ("central", "none"): "moderate",
    ("central", "soft"): "high",
    ("central", "direct"): "high",
}


class PressureMatrixTests(unittest.TestCase):
    def test_every_combination_is_pinned(self):
        """All 4x3 cells: ten exact tiers, two invalid holes."""
        self.assertEqual(len(EXPECTED_MATRIX), 12)
        self.assertEqual(len(PRESSURE_MATRIX), 10)
        for offer in OFFER_INTEGRATIONS:
            for cta in CTA_INTENSITIES:
                expected = EXPECTED_MATRIX[(offer, cta)]
                if expected is None:
                    with self.assertRaisesRegex(
                        ValidationError, "invalid commercial expression"
                    ):
                        derive_commercial_pressure(offer, cta)
                else:
                    self.assertEqual(
                        derive_commercial_pressure(offer, cta), expected,
                        f"({offer}, {cta})",
                    )

    def test_tier_values_are_ordinal(self):
        self.assertEqual(
            [TIER_VALUES[tier] for tier in PRESSURE_TIERS], [0, 1, 2, 3]
        )

    def test_unknown_offer_integration_rejected(self):
        with self.assertRaisesRegex(ValidationError, "offer integration"):
            derive_commercial_pressure("sponsored", "soft")

    def test_unknown_cta_intensity_rejected(self):
        with self.assertRaisesRegex(ValidationError, "CTA intensity"):
            derive_commercial_pressure("central", "aggressive")

    def test_is_valid_expression(self):
        self.assertTrue(is_valid_expression("contextual", "direct"))
        self.assertFalse(is_valid_expression("absent", "direct"))
        self.assertFalse(is_valid_expression("embedded", "direct"))
        with self.assertRaises(ValidationError):
            is_valid_expression("sponsored", "soft")


class PressureIndicatorTests(unittest.TestCase):
    def test_empty_input_reports_unknown_not_zero(self):
        result = pressure_indicator([])
        self.assertEqual(result["known_touches"], 0)
        self.assertIsNone(result["score"])
        self.assertIsNone(result["high_share"])
        self.assertEqual(
            result["tier_counts"],
            {"none": 0, "low": 0, "moderate": 0, "high": 0},
        )

    def test_mixed_tiers_score_arithmetic(self):
        result = pressure_indicator(["none", "low", "moderate", "high"])
        self.assertEqual(result["known_touches"], 4)
        # mean 1.5 of 3 -> 50
        self.assertEqual(result["score"], 50)
        self.assertEqual(result["high_share"], 0.25)
        self.assertEqual(
            result["tier_counts"],
            {"none": 1, "low": 1, "moderate": 1, "high": 1},
        )

    def test_all_high_scores_100(self):
        result = pressure_indicator(["high", "high"])
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["high_share"], 1.0)

    def test_all_none_scores_0(self):
        result = pressure_indicator(["none"])
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["high_share"], 0.0)

    def test_unknown_tier_rejected(self):
        with self.assertRaisesRegex(ValidationError, "pressure tier"):
            pressure_indicator(["low", "extreme"])

    def test_advisory_threshold_is_25_percent(self):
        self.assertEqual(HIGH_PRESSURE_SHARE_ADVISORY_THRESHOLD, 0.25)


class ExpressionCeilingTests(unittest.TestCase):
    def test_at_ceiling_passes(self):
        self.assertTrue(
            expression_within_ceilings("embedded", "soft", "embedded", "soft")
        )

    def test_below_ceiling_passes(self):
        self.assertTrue(
            expression_within_ceilings("absent", "none", "central", "direct")
        )

    def test_above_offer_ceiling_fails(self):
        self.assertFalse(
            expression_within_ceilings("central", "none", "contextual", "direct")
        )

    def test_above_cta_ceiling_fails(self):
        self.assertFalse(
            expression_within_ceilings("embedded", "soft", "central", "none")
        )

    def test_unknown_values_rejected(self):
        with self.assertRaises(ValidationError):
            expression_within_ceilings("embedded", "soft", "sky_high", "soft")
        with self.assertRaises(ValidationError):
            expression_within_ceilings("embedded", "loud", "central", "direct")


if __name__ == "__main__":
    unittest.main()
