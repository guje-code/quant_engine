from quant_engine.market.steam_detector import SteamDetector


class TestSteamDetector:

    # ==========================================
    # INVALID INPUTS
    # ==========================================

    def test_invalid_opening_odds(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(opening_odds=1.0, live_odds=2.0)

        assert result["steam_detected"] is False

    def test_invalid_live_odds(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(opening_odds=2.0, live_odds=1.0)

        assert result["steam_detected"] is False

    def test_invalid_time_delta(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.1, time_delta_minutes=0
        )

        assert result["steam_detected"] is False

    # ==========================================
    # MOVEMENT TYPE
    # ==========================================

    def test_favorable_movement(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=5.0, velocity=1.0
        )

        assert movement == "FAVORABLE"

    def test_adverse_movement(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=-5.0, velocity=1.0
        )

        assert movement == "ADVERSE"

    def test_neutral_movement(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=0.0, velocity=0.0
        )

        assert movement == "NEUTRAL"

    # ==========================================
    # SEVERITY
    # ==========================================

    def test_low_severity(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=1.0, velocity=0.1
        )

        assert severity == "LOW"

    def test_medium_severity(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=5.0, velocity=1.0
        )

        assert severity == "MEDIUM"

    def test_high_severity(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=7.0, velocity=2.0
        )

        assert severity == "HIGH"

    def test_critical_severity(self):
        detector = SteamDetector()

        movement, severity = detector._clasificar_movimiento_y_severidad(
            total_move_pct=12.0, velocity=3.5
        )

        assert severity == "CRITICAL"

    # ==========================================
    # STEAM DETECTION
    # ==========================================

    def test_detects_steam_by_velocity(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.4, time_delta_minutes=1
        )

        assert result["steam_detected"] is True

    def test_detects_steam_by_total_move(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.12, time_delta_minutes=60
        )

        assert result["steam_detected"] is True

    def test_no_steam_detected(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.01, time_delta_minutes=30
        )

        assert result["steam_detected"] is False

    # ==========================================
    # RETURN STRUCTURE
    # ==========================================

    def test_returns_required_fields(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.2, time_delta_minutes=10
        )

        expected_fields = {
            "steam_detected",
            "velocity_pct_min",
            "total_move_pct",
            "movement_type",
            "severity",
            "timestamp",
            "reason",
        }

        assert expected_fields.issubset(result.keys())

    def test_velocity_is_positive(self):
        detector = SteamDetector()

        result = detector.evaluate_steam_move(
            opening_odds=2.0, live_odds=2.3, time_delta_minutes=5
        )

        assert result["velocity_pct_min"] > 0
