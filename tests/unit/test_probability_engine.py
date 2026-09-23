# tests/unit/test_probability_engine.py


from quant_engine.core.probability_engine import ProbabilityEngine


class TestProbabilityEngine:

    # ==========================================
    # IMPLIED PROBABILITY
    # ==========================================

    def test_implied_probability_even_odds(self):
        assert ProbabilityEngine.calcular_implied_probability(2.0) == 0.5

    def test_implied_probability_invalid_odds(self):
        assert ProbabilityEngine.calcular_implied_probability(1.0) == 0.0
        assert ProbabilityEngine.calcular_implied_probability(0.0) == 0.0

    def test_implied_probability_positive(self):
        result = ProbabilityEngine.calcular_implied_probability(1.80)
        assert result > 0
        assert result < 1

    # ==========================================
    # ROI
    # ==========================================

    def test_roi_teorico_positive_ev(self):
        roi = ProbabilityEngine.calcular_roi_teorico(prob_final=0.60, odds=2.0)

        assert roi == 0.2

    def test_roi_teorico_negative_ev(self):
        roi = ProbabilityEngine.calcular_roi_teorico(prob_final=0.40, odds=2.0)

        assert roi == -0.2

    def test_roi_teorico_invalid_odds(self):
        assert ProbabilityEngine.calcular_roi_teorico(0.6, 1.0) == 0.0

    # ==========================================
    # EXPECTED VALUE
    # ==========================================

    def test_expected_value_positive(self):
        ev = ProbabilityEngine.calcular_expected_value(prob_final=0.60, odds=2.0)

        assert ev == 20.0

    def test_expected_value_negative(self):
        ev = ProbabilityEngine.calcular_expected_value(prob_final=0.40, odds=2.0)

        assert ev == -20.0

    # ==========================================
    # LOGIT ENGINE
    # ==========================================

    def test_logit_returns_dict(self):
        result = ProbabilityEngine.ajustar_probabilidad_logit(
            prob_base=0.55, total_adjustment=0.25
        )

        assert isinstance(result, dict)

    def test_logit_contains_all_keys(self):
        result = ProbabilityEngine.ajustar_probabilidad_logit(
            prob_base=0.55, total_adjustment=0.25
        )

        expected_keys = {
            "prob_base",
            "logit_base",
            "adjustment",
            "logit_final",
            "prob_final",
        }

        assert expected_keys.issubset(result.keys())

    def test_logit_probability_bounds(self):
        result = ProbabilityEngine.ajustar_probabilidad_logit(
            prob_base=0.55, total_adjustment=0.25
        )

        assert 0.0 <= result["prob_final"] <= 1.0

    def test_positive_adjustment_increases_probability(self):
        base = ProbabilityEngine.calcular_probabilidad_final(0.50, 0.0)

        boosted = ProbabilityEngine.calcular_probabilidad_final(0.50, 0.50)

        assert boosted > base

    def test_negative_adjustment_decreases_probability(self):
        base = ProbabilityEngine.calcular_probabilidad_final(0.50, 0.0)

        penalized = ProbabilityEngine.calcular_probabilidad_final(0.50, -0.50)

        assert penalized < base

    # ==========================================
    # LEGACY FLOAT CONTRACT
    # ==========================================

    def test_calcular_probabilidad_final_returns_float(self):
        result = ProbabilityEngine.calcular_probabilidad_final(0.55, 0.10)

        assert isinstance(result, float)

    def test_probability_clipping_lower_bound(self):
        result = ProbabilityEngine.calcular_probabilidad_final(0.0, 0.0)

        assert result > 0.0

    def test_probability_clipping_upper_bound(self):
        result = ProbabilityEngine.calcular_probabilidad_final(1.0, 0.0)

        assert result < 1.0
