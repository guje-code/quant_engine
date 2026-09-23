from unittest.mock import patch

import numpy as np

from quant_engine.risk.portfolio_mc import (
    calcular_ledoit_wolf_optimal_shrinkage,
    construir_matriz_covarianza_citadel,
    simular_portfolio_var_cvar_student_t,
)


class TestPortfolioMC:

    # ==========================================
    # LEDOIT WOLF
    # ==========================================

    def test_ledoit_wolf_returns_matrix(self):

        data = np.array([[1, 2, 3], [2, 3, 4]])

        target = np.eye(2)

        sigma, delta = calcular_ledoit_wolf_optimal_shrinkage(data, target)

        assert sigma.shape == (2, 2)
        assert 0.0 <= delta <= 1.0

    # ==========================================
    # EMPTY COVARIANCE
    # ==========================================

    @patch("quant_engine.risk.portfolio_mc.sqlite3.connect")
    def test_empty_covariance(self, mock_connect):

        cursor = mock_connect.return_value.cursor.return_value

        cursor.fetchall.return_value = []

        result = construir_matriz_covarianza_citadel([], "fake.db")

        assert result["fallback"] is True

    # ==========================================
    # COVARIANCE STRUCTURE
    # ==========================================

    @patch("quant_engine.risk.portfolio_mc.sqlite3.connect")
    def test_covariance_returns_structure(self, mock_connect):

        cursor = mock_connect.return_value.cursor.return_value

        cursor.fetchall.return_value = []

        result = construir_matriz_covarianza_citadel(["CLV"], "fake.db")

        assert "rules" in result
        assert "sigma" in result
        assert "delta" in result

    # ==========================================
    # MONTE CARLO
    # ==========================================

    @patch("quant_engine.risk.portfolio_mc.construir_matriz_covarianza_citadel")
    @patch("quant_engine.risk.portfolio_mc.sqlite3.connect")
    def test_mc_returns_contract(self, mock_connect, mock_cov):

        cursor = mock_connect.return_value.cursor.return_value

        cursor.fetchall.return_value = []

        mock_cov.return_value = {
            "rules": ["CLV"],
            "sigma": np.array([[0.05]]),
            "delta": 0.8,
            "fallback": False,
        }

        result = simular_portfolio_var_cvar_student_t(
            candidate_prob=0.60,
            candidate_odds=2.0,
            candidate_stake_pct=2.0,
            bankroll=10000,
            candidate_triggered_rules=["CLV"],
            db_path="fake.db",
            iterations=1000,
        )

        expected_keys = {
            "var_95_amount",
            "var_95_pct",
            "cvar_95_amount",
            "cvar_95_pct",
            "safe",
            "active_positions_count",
            "sigma_snapshot",
        }

        assert expected_keys.issubset(result.keys())

    # ==========================================
    # SIGMA SNAPSHOT
    # ==========================================

    @patch("quant_engine.risk.portfolio_mc.construir_matriz_covarianza_citadel")
    @patch("quant_engine.risk.portfolio_mc.sqlite3.connect")
    def test_sigma_snapshot(self, mock_connect, mock_cov):

        cursor = mock_connect.return_value.cursor.return_value

        cursor.fetchall.return_value = []

        mock_cov.return_value = {
            "rules": ["CLV"],
            "sigma": np.array([[0.05]]),
            "delta": 0.91,
            "fallback": False,
        }

        result = simular_portfolio_var_cvar_student_t(
            candidate_prob=0.55,
            candidate_odds=2.0,
            candidate_stake_pct=1.0,
            bankroll=10000,
            candidate_triggered_rules=["CLV"],
            db_path="fake.db",
            iterations=500,
        )

        assert result["sigma_snapshot"]["optimal_delta"] == 0.91
