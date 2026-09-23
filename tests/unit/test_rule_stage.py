from unittest.mock import patch

from quant_engine.core.pipeline_steps.rule_stage import ejecutar_etapa_reglas


class TestRuleStage:

    # ==========================================
    # SUCCESS
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_successful_stage(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "rules_applicable": 10,
            "coverage": 100.0,
            "circuit_breaker_triggered": False,
            "rule_audit": {"triggered": []},
            "cluster_hits": {},
            "total_adjustment": 1.25,
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=1.0,
            steam_detected=False,
        )

        assert result["coverage"] == 100.0
        assert result["total_adjustment"] == 1.25

    # ==========================================
    # CIRCUIT BREAKER
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_circuit_breaker(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "circuit_breaker_triggered": True,
            "circuit_breaker_reason": "CRITICAL_EDGE",
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["circuit_breaker_triggered"] is True

    # ==========================================
    # COVERAGE
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_coverage_is_returned(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "coverage": 75.0,
            "circuit_breaker_triggered": False,
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["coverage"] == 75.0

    # ==========================================
    # CLUSTER HITS
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_cluster_hits_pass_through(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "cluster_hits": {"VALUE_CLUSTER": 2},
            "circuit_breaker_triggered": False,
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert "cluster_hits" in result

    # ==========================================
    # RULE AUDIT
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_rule_audit_returned(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "rule_audit": {"triggered": [{"rule": "CLV"}]},
            "circuit_breaker_triggered": False,
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert "rule_audit" in result

    # ==========================================
    # TOTAL ADJUSTMENT
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_total_adjustment_returned(self, mock_rule_engine):

        mock_rule_engine.return_value = {
            "total_adjustment": 2.5,
            "circuit_breaker_triggered": False,
        }

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["total_adjustment"] == 2.5

    # ==========================================
    # DURATION TELEMETRY
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.rule_stage.ejecutar_rule_engine_modular")
    def test_duration_added(self, mock_rule_engine):

        mock_rule_engine.return_value = {"coverage": 100.0}

        result = ejecutar_etapa_reglas(
            scout_json={"advanced_metrics": {}},
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert "duration_ms" in result
        assert result["duration_ms"] >= 0
