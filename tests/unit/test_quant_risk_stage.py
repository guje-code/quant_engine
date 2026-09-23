from unittest.mock import Mock, patch

from quant_engine.core.pipeline_steps.quant_risk_stage import ejecutar_etapa_quant_risk


class TestQuantRiskStage:

    def build_scout_res(self):

        return {"scout_json": {"opening_odds": 2.0, "data_quality_score": 0.95}}

    def build_rule_res(self):

        return {
            "total_adjustment": 0.10,
            "cluster_hits": {},
            "rule_audit": {"triggered": [{"rule": "CLV", "severity": "LOW"}]},
        }

    # ==========================================
    # SUCCESS
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.quant_risk_stage.simular_portfolio_var_cvar_student_t"
    )
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.calcular_stake_kelly")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.ProbabilityEngine")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Task")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.AgentFactory")
    def test_successful_quant_risk(
        self,
        mock_factory,
        mock_task,
        mock_crew,
        mock_extract,
        mock_probability,
        mock_kelly,
        mock_mc,
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extract.side_effect = [
            {
                "selection": "Boston",
                "market_type": "Moneyline",
                "estimated_true_probability": 0.60,
                "bookmaker_odds": 2.10,
            },
            {"final_verdict": "APPROVED", "recommended_stake_units": 2.0},
        ]

        mock_probability.ajustar_probabilidad_logit.return_value = 0.62
        mock_probability.calcular_expected_value.return_value = 8.5

        mock_kelly.return_value = {"stake_final_pct": 3.0}

        mock_mc.return_value = {
            "safe": True,
            "var_95_amount": 120.0,
            "var_95_pct": 1.2,
            "cvar_95_amount": 200.0,
            "cvar_95_pct": 2.0,
            "sigma_snapshot": {"fallback": False},
        }

        result = ejecutar_etapa_quant_risk(
            match_name="Boston vs Yankees",
            sport_league="MLB",
            bankroll=10000,
            scout_res=self.build_scout_res(),
            rule_res=self.build_rule_res(),
            api_key="fake",
        )

        assert result["success"] is True

    # ==========================================
    # VAR FAILURE
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.quant_risk_stage.simular_portfolio_var_cvar_student_t"
    )
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.calcular_stake_kelly")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.ProbabilityEngine")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Task")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.AgentFactory")
    def test_var_rejection(
        self,
        mock_factory,
        mock_task,
        mock_crew,
        mock_extract,
        mock_probability,
        mock_kelly,
        mock_mc,
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extract.side_effect = [
            {"estimated_true_probability": 0.60, "bookmaker_odds": 2.10},
            {"final_verdict": "APPROVED"},
        ]

        mock_probability.ajustar_probabilidad_logit.return_value = 0.62
        mock_probability.calcular_expected_value.return_value = 8.5

        mock_kelly.return_value = {"stake_final_pct": 3.0}

        mock_mc.return_value = {
            "safe": False,
            "var_95_amount": 1000,
            "var_95_pct": 12,
            "cvar_95_amount": 1500,
            "cvar_95_pct": 18,
        }

        result = ejecutar_etapa_quant_risk(
            match_name="Boston vs Yankees",
            sport_league="MLB",
            bankroll=10000,
            scout_res=self.build_scout_res(),
            rule_res=self.build_rule_res(),
            api_key="fake",
        )

        assert result["success"] is False

    # ==========================================
    # RETURN CONTRACT
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.quant_risk_stage.simular_portfolio_var_cvar_student_t"
    )
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.calcular_stake_kelly")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.ProbabilityEngine")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.Task")
    @patch("quant_engine.core.pipeline_steps.quant_risk_stage.AgentFactory")
    def test_return_contract(
        self,
        mock_factory,
        mock_task,
        mock_crew,
        mock_extract,
        mock_probability,
        mock_kelly,
        mock_mc,
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extract.side_effect = [
            {"estimated_true_probability": 0.60, "bookmaker_odds": 2.10},
            {},
        ]

        mock_probability.ajustar_probabilidad_logit.return_value = 0.62
        mock_probability.calcular_expected_value.return_value = 8.5

        mock_kelly.return_value = {"stake_final_pct": 3.0}

        mock_mc.return_value = {
            "safe": True,
            "var_95_amount": 120,
            "var_95_pct": 1.2,
            "cvar_95_amount": 200,
            "cvar_95_pct": 2.0,
            "sigma_snapshot": {},
        }

        result = ejecutar_etapa_quant_risk(
            match_name="Boston vs Yankees",
            sport_league="MLB",
            bankroll=10000,
            scout_res=self.build_scout_res(),
            rule_res=self.build_rule_res(),
            api_key="fake",
        )

        expected = {
            "success",
            "odds",
            "ev",
            "stake_final",
            "monto_apuesta",
            "var_amount",
            "cvar_amount",
            "duration_ms",
        }

        assert expected.issubset(result.keys())
