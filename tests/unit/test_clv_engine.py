from quant_engine.market.clv_engine import CLVEngine


class MockOddsProvider:
    def __init__(self, odds):
        self.odds = odds

    def get_live_odds(self, match_name, opening_odds):
        return self.odds


class TestCLVEngine:

    # ==========================================
    # LINE MOVEMENT
    # ==========================================

    def test_line_movement_positive(self):
        engine = CLVEngine()

        result = engine.calculate_line_movement(opening_odds=2.00, current_odds=2.10)

        assert result == 5.0

    def test_line_movement_negative(self):
        engine = CLVEngine()

        result = engine.calculate_line_movement(opening_odds=2.00, current_odds=1.90)

        assert result == -5.0

    def test_invalid_odds_returns_zero(self):
        engine = CLVEngine()

        result = engine.calculate_line_movement(opening_odds=1.0, current_odds=2.0)

        assert result == 0.0

    # ==========================================
    # MOVEMENT TYPE
    # ==========================================

    def test_favorable_movement(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(2.0)

        assert movement == "FAVORABLE"

    def test_adverse_movement(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(-2.0)

        assert movement == "ADVERSE"

    def test_neutral_movement(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(0.0)

        assert movement == "NEUTRAL"

    # ==========================================
    # SEVERITY
    # ==========================================

    def test_opportunity_severity(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(6.0)

        assert severity == "OPPORTUNITY"

    def test_low_severity(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(-1.0)

        assert severity == "LOW"

    def test_medium_severity(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(-3.0)

        assert severity == "MEDIUM"

    def test_high_severity(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(-5.0)

        assert severity == "HIGH"

    def test_critical_severity(self):
        engine = CLVEngine()

        movement, severity = engine._clasificar_movimiento_y_severidad(-8.0)

        assert severity == "CRITICAL"

    # ==========================================
    # VALIDATION
    # ==========================================

    def test_valid_live_odds(self):
        engine = CLVEngine()
        provider = MockOddsProvider(2.05)

        result = engine.validate_live_odds(
            match_name="A vs B", opening_odds=2.00, odds_provider=provider
        )

        assert result["valid"] is True

    def test_invalid_due_to_drop(self):
        engine = CLVEngine(max_allowed_drop_pct=3.0)

        provider = MockOddsProvider(1.90)

        result = engine.validate_live_odds(
            match_name="A vs B", opening_odds=2.00, odds_provider=provider
        )

        assert result["valid"] is False

    def test_returns_required_fields(self):
        engine = CLVEngine()

        provider = MockOddsProvider(2.05)

        result = engine.validate_live_odds(
            match_name="A vs B", opening_odds=2.00, odds_provider=provider
        )

        expected_fields = {
            "valid",
            "reason",
            "opening_odds",
            "current_odds",
            "drop_pct",
            "movement_type",
            "severity",
            "timestamp",
        }

        assert expected_fields.issubset(result.keys())

    def test_invalid_opening_odds(self):
        engine = CLVEngine()

        provider = MockOddsProvider(2.00)

        result = engine.validate_live_odds(
            match_name="A vs B", opening_odds=1.0, odds_provider=provider
        )

        assert result["valid"] is False
