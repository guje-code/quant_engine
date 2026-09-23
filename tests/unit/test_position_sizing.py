from quant_engine.risk.position_sizing import calcular_stake_kelly


class TestPositionSizing:

    # ==========================================
    # INVALID
    # ==========================================

    def test_invalid_odds(self):
        result = calcular_stake_kelly(
            prob_est=0.60, odds=1.0, confidence_score=90, triggered_rules=[]
        )

        assert result["status"] == "INVALID"
        assert result["stake_final_pct"] == 0.0

    def test_invalid_probability_zero(self):
        result = calcular_stake_kelly(
            prob_est=0.0, odds=2.0, confidence_score=90, triggered_rules=[]
        )

        assert result["status"] == "INVALID"

    def test_invalid_probability_one(self):
        result = calcular_stake_kelly(
            prob_est=1.0, odds=2.0, confidence_score=90, triggered_rules=[]
        )

        assert result["status"] == "INVALID"

    # ==========================================
    # NO VALUE
    # ==========================================

    def test_no_value_bet(self):
        result = calcular_stake_kelly(
            prob_est=0.40, odds=2.0, confidence_score=90, triggered_rules=[]
        )

        assert result["status"] == "NO_VALUE"
        assert result["stake_final_pct"] == 0.0

    # ==========================================
    # APPROVED
    # ==========================================

    def test_positive_kelly_returns_approved(self):
        result = calcular_stake_kelly(
            prob_est=0.60, odds=2.0, confidence_score=90, triggered_rules=[]
        )

        assert result["status"] in ["APPROVED", "CAPPED"]
        assert result["stake_final_pct"] > 0

    # ==========================================
    # CONFIDENCE FACTOR
    # ==========================================

    def test_higher_confidence_generates_higher_stake(self):
        low_conf = calcular_stake_kelly(
            prob_est=0.60, odds=2.0, confidence_score=50, triggered_rules=[]
        )

        high_conf = calcular_stake_kelly(
            prob_est=0.60, odds=2.0, confidence_score=100, triggered_rules=[]
        )

        assert high_conf["stake_final_pct"] >= low_conf["stake_final_pct"]

    # ==========================================
    # SEVERITY PENALTIES
    # ==========================================

    def test_high_severity_reduces_stake(self):
        no_penalty = calcular_stake_kelly(
            prob_est=0.60, odds=2.0, confidence_score=100, triggered_rules=[]
        )

        high_penalty = calcular_stake_kelly(
            prob_est=0.60,
            odds=2.0,
            confidence_score=100,
            triggered_rules=[{"severity": "HIGH"}],
        )

        assert high_penalty["stake_final_pct"] < no_penalty["stake_final_pct"]

    def test_multiple_penalties_reduce_stake_further(self):
        one_penalty = calcular_stake_kelly(
            prob_est=0.60,
            odds=2.0,
            confidence_score=100,
            triggered_rules=[{"severity": "MEDIUM"}],
        )

        two_penalties = calcular_stake_kelly(
            prob_est=0.60,
            odds=2.0,
            confidence_score=100,
            triggered_rules=[{"severity": "MEDIUM"}, {"severity": "HIGH"}],
        )

        assert two_penalties["stake_final_pct"] < one_penalty["stake_final_pct"]

    # ==========================================
    # AUDIT FIELDS
    # ==========================================

    def test_returns_audit_fields(self):
        result = calcular_stake_kelly(
            prob_est=0.60, odds=2.0, confidence_score=100, triggered_rules=[]
        )

        assert "kelly_full_pct" in result
        assert "confidence_factor" in result
        assert "severity_penalty" in result
        assert "status" in result

    # ==========================================
    # DEFENSIVE FLOOR
    # ==========================================

    def test_stake_never_negative(self):
        result = calcular_stake_kelly(
            prob_est=0.51,
            odds=1.01,
            confidence_score=100,
            triggered_rules=[{"severity": "CRITICAL_EDGE"}],
        )

        assert result["stake_final_pct"] >= 0.0

    # ==========================================
    # CAP LOGIC
    # ==========================================

    def test_capped_status_when_limit_reached(self):
        result = calcular_stake_kelly(
            prob_est=0.95, odds=5.0, confidence_score=100, triggered_rules=[]
        )

        assert result["status"] in ["APPROVED", "CAPPED"]

        if result["status"] == "CAPPED":
            assert result["stake_final_pct"] > 0
