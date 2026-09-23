from unittest.mock import patch

from quant_engine.pipeline.pipeline_facade import PipelineFacade


class TestPipelineFacade:

    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_persistencia")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_quant_risk")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_reglas")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_scout")
    def test_pipeline_success(
        self, mock_scout, mock_rules, mock_quant_risk, mock_persist
    ):

        mock_scout.return_value = {
            "success": True,
            "scout_json": {"advanced_metrics": {}},
            "line_movement_pct": 2.0,
            "steam_detected": False,
        }

        mock_rules.return_value = {
            "circuit_breaker_triggered": False,
            "total_adjustment": 0.10,
        }

        mock_quant_risk.return_value = {
            "success": True,
            "odds": 2.10,
            "ev": 6.5,
            "stake_final": 3.0,
            "monto_apuesta": 300.0,
            "var_amount": 150.0,
            "var_pct": 1.5,
            "cvar_amount": 250.0,
            "cvar_pct": 2.5,
        }

        facade = PipelineFacade()

        result = facade.ejecutar_analisis(
            match_name="Boston Red Sox vs Yankees", sport_league="MLB", bankroll=10000
        )

        assert result["success"] is True
        assert result["ev"] == 6.5
        assert result["stake_pct"] == 3.0

        mock_persist.assert_called_once()

    # ==========================================
    # SCOUT FAILURE
    # ==========================================

    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_scout")
    def test_pipeline_aborts_in_scout(self, mock_scout):

        mock_scout.return_value = {"success": False, "reason": "Market unavailable"}

        facade = PipelineFacade()

        result = facade.ejecutar_analisis(
            match_name="Test", sport_league="MLB", bankroll=1000
        )

        assert result["success"] is False
        assert result["stage"] == "SCOUT"

    # ==========================================
    # CIRCUIT BREAKER
    # ==========================================

    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_reglas")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_scout")
    def test_pipeline_circuit_breaker(self, mock_scout, mock_rules):

        mock_scout.return_value = {
            "success": True,
            "scout_json": {"advanced_metrics": {}},
            "line_movement_pct": 0.0,
            "steam_detected": False,
        }

        mock_rules.return_value = {
            "circuit_breaker_triggered": True,
            "circuit_breaker_reason": "Critical Edge",
        }

        facade = PipelineFacade()

        result = facade.ejecutar_analisis(
            match_name="Test", sport_league="MLB", bankroll=1000
        )

        assert result["success"] is False
        assert result["stage"] == "CIRCUIT_BREAKER"

    # ==========================================
    # RISK FAILURE
    # ==========================================

    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_quant_risk")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_reglas")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_scout")
    def test_pipeline_risk_abort(self, mock_scout, mock_rules, mock_quant_risk):

        mock_scout.return_value = {
            "success": True,
            "scout_json": {},
            "line_movement_pct": 0.0,
            "steam_detected": False,
        }

        mock_rules.return_value = {"circuit_breaker_triggered": False}

        mock_quant_risk.return_value = {
            "success": False,
            "reason": "VaR limit exceeded",
        }

        facade = PipelineFacade()

        result = facade.ejecutar_analisis(
            match_name="Test", sport_league="MLB", bankroll=1000
        )

        assert result["success"] is False
        assert result["stage"] == "RISK"

    # ==========================================
    # RETURN CONTRACT
    # ==========================================

    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_persistencia")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_quant_risk")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_reglas")
    @patch("quant_engine.pipeline.pipeline_facade.ejecutar_etapa_scout")
    def test_return_contract(
        self, mock_scout, mock_rules, mock_quant_risk, mock_persist
    ):

        mock_scout.return_value = {
            "success": True,
            "scout_json": {},
            "line_movement_pct": 1.0,
            "steam_detected": False,
        }

        mock_rules.return_value = {
            "circuit_breaker_triggered": False,
            "total_adjustment": 0.1,
        }

        mock_quant_risk.return_value = {
            "success": True,
            "odds": 2.0,
            "ev": 5.0,
            "stake_final": 2.0,
            "monto_apuesta": 200.0,
            "var_amount": 100.0,
            "var_pct": 1.0,
            "cvar_amount": 200.0,
            "cvar_pct": 2.0,
        }

        result = PipelineFacade().ejecutar_analisis("Test", "MLB", 10000)

        expected_keys = {
            "success",
            "match_name",
            "sport_league",
            "odds",
            "ev",
            "stake_pct",
            "stake_amount",
            "var_amount",
            "cvar_amount",
            "message",
        }

        assert expected_keys.issubset(result.keys())
