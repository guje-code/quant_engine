from unittest.mock import patch

from quant_engine.core.rule_engine import ejecutar_rule_engine_modular


class TestRuleEngine:

    # ==========================================
    # HELPERS
    # ==========================================

    @staticmethod
    def registry_single_rule():
        return {
            "RULES": {
                "TEST_RULE": {
                    "name": "Test Rule",
                    "priority": 1,
                    "weight": 1.0,
                    "severity": "MEDIUM",
                    "leagues": ["MLB"],
                    "eval_type": "SIMPLE",
                    "metric": "ev",
                    "operator": ">",
                    "threshold": 5,
                }
            }
        }

    # ==========================================
    # BASIC EXECUTION
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_rule_triggered(self, mock_json):

        mock_json.side_effect = [
            self.registry_single_rule(),
            {"PERFORMANCE": {}},
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["rules_applicable"] == 1
        assert len(result["rule_audit"]["triggered"]) == 1

    # ==========================================
    # RULE NOT TRIGGERED
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_rule_not_triggered(self, mock_json):

        mock_json.side_effect = [
            self.registry_single_rule(),
            {"PERFORMANCE": {}},
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 1}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert len(result["rule_audit"]["triggered"]) == 0

    # ==========================================
    # COVERAGE
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_coverage_is_calculated(self, mock_json):

        mock_json.side_effect = [
            self.registry_single_rule(),
            {"PERFORMANCE": {}},
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["coverage"] >= 0

    # ==========================================
    # DISABLED RULE
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_disabled_rule_not_triggered(self, mock_json):

        performance = {
            "PERFORMANCE": {"TEST_RULE": {"backtest_samples": 500, "last_90d_roi": -10}}
        }

        mock_json.side_effect = [
            self.registry_single_rule(),
            performance,
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert len(result["rule_audit"]["triggered"]) == 0

    # ==========================================
    # CIRCUIT BREAKER
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_circuit_breaker_triggered(self, mock_json):

        registry = {
            "RULES": {
                "CB_RULE": {
                    "name": "Critical Rule",
                    "priority": 0,
                    "weight": 1.0,
                    "severity": "CRITICAL",
                    "leagues": ["MLB"],
                    "eval_type": "SIMPLE",
                    "metric": "ev",
                    "operator": ">",
                    "threshold": 1,
                }
            }
        }

        mock_json.side_effect = [registry, {"PERFORMANCE": {}}, {"CLUSTERS": {}}]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert result["circuit_breaker_triggered"] is True

    # ==========================================
    # CLUSTER STRUCTURE
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_cluster_hits_exists(self, mock_json):

        mock_json.side_effect = [
            self.registry_single_rule(),
            {"PERFORMANCE": {}},
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert "cluster_hits" in result

    # ==========================================
    # TOTAL ADJUSTMENT
    # ==========================================

    @patch("quant_engine.core.rule_engine.JSONRepository.cargar_json")
    def test_total_adjustment_exists(self, mock_json):

        mock_json.side_effect = [
            self.registry_single_rule(),
            {"PERFORMANCE": {}},
            {"CLUSTERS": {}},
        ]

        scout_data = {"advanced_metrics": {"ev": 10}}

        result = ejecutar_rule_engine_modular(
            scout_data=scout_data,
            sport_league="MLB",
            line_movement_pct=0,
            steam_detected=False,
        )

        assert "total_adjustment" in result
