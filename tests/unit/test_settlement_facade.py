from unittest.mock import mock_open, patch

from quant_engine.settlement.settlement_facade import SettlementFacade


class TestSettlementFacade:

    # ==========================================
    # HELPERS
    # ==========================================

    @staticmethod
    def sample_pick():
        return {
            "pick_id": 1,
            "match_name": "Boston Red Sox vs New York Yankees",
            "sport_league": "MLB",
            "selection": "Boston Red Sox",
            "odds": 2.10,
            "stake": 1000.0,
            "profit_units": 1100.0,
            "actual_result": "WIN",
        }

    # ==========================================
    # PENDING PICKS
    # ==========================================

    @patch("quant_engine.settlement.settlement_facade.listar_apuestas_pendientes")
    def test_get_pending_picks(self, mock_pending):

        mock_pending.return_value = [{"id": 10}, {"id": 20}]

        result = SettlementFacade.get_pending_picks()

        assert len(result) == 2

    # ==========================================
    # CLOSE PICK
    # ==========================================

    @patch("quant_engine.settlement.settlement_facade.analizar_post_mortem")
    @patch("quant_engine.settlement.settlement_facade.actualizar_resultado_db")
    @patch("quant_engine.settlement.settlement_facade.os.path.exists")
    @patch("quant_engine.settlement.settlement_facade.sqlite3.connect")
    @patch("builtins.open", new_callable=mock_open, read_data='{"PERFORMANCE":{}}')
    def test_close_pick_success(
        self, mock_file, mock_connect, mock_exists, mock_update, mock_postmortem
    ):

        mock_exists.return_value = True

        mock_update.return_value = self.sample_pick()

        mock_postmortem.return_value = {
            "classification": "BAD_BEAT",
            "root_cause": "Late bullpen collapse",
        }

        conn = mock_connect.return_value
        cursor = conn.cursor.return_value

        cursor.fetchone.side_effect = [
            ("MLB", '[{"rule":"CLV"}]'),
            (100.0, 1000.0),
            (50.0, 500.0),
            (80.0, 800.0),
        ]

        result = SettlementFacade.close_pick(
            pick_id=1, result="WIN", run_postmortem=True
        )

        assert result["actual_result"] == "WIN"
        assert result["profit_units"] == 1100.0

    # ==========================================
    # POSTMORTEM OPTIONAL
    # ==========================================

    @patch("quant_engine.settlement.settlement_facade.analizar_post_mortem")
    @patch("quant_engine.settlement.settlement_facade.actualizar_resultado_db")
    @patch("quant_engine.settlement.settlement_facade.os.path.exists")
    @patch("quant_engine.settlement.settlement_facade.sqlite3.connect")
    @patch("builtins.open", new_callable=mock_open, read_data='{"PERFORMANCE":{}}')
    def test_close_pick_without_postmortem(
        self, mock_file, mock_connect, mock_exists, mock_update, mock_postmortem
    ):

        mock_exists.return_value = True

        mock_update.return_value = self.sample_pick()

        conn = mock_connect.return_value
        cursor = conn.cursor.return_value

        cursor.fetchone.side_effect = [
            ("MLB", '[{"rule":"CLV"}]'),
            (100.0, 1000.0),
            (50.0, 500.0),
            (80.0, 800.0),
        ]

        result = SettlementFacade.close_pick(
            pick_id=1, result="WIN", run_postmortem=False
        )

        mock_postmortem.assert_not_called()

        assert result["postmortem"] is None

    # ==========================================
    # RISK STATE
    # ==========================================

    @patch("quant_engine.settlement.settlement_facade.actualizar_resultado_db")
    @patch("quant_engine.settlement.settlement_facade.os.path.exists")
    @patch("quant_engine.settlement.settlement_facade.sqlite3.connect")
    @patch("builtins.open", new_callable=mock_open, read_data='{"PERFORMANCE":{}}')
    def test_risk_state_disabled(
        self, mock_file, mock_connect, mock_exists, mock_update
    ):

        mock_exists.return_value = True

        mock_update.return_value = self.sample_pick()

        conn = mock_connect.return_value
        cursor = conn.cursor.return_value

        cursor.fetchone.side_effect = [
            ("MLB", '[{"rule":"CLV"}]'),
            (100.0, 1000.0),
            (-250.0, 1000.0),  # ROI 30d = -25%
            (-250.0, 1000.0),
        ]

        result = SettlementFacade.close_pick(
            pick_id=1, result="LOSS", run_postmortem=False
        )

        assert result["risk_state"] == "DISABLED"

    # ==========================================
    # RETURN CONTRACT
    # ==========================================

    @patch("quant_engine.settlement.settlement_facade.analizar_post_mortem")
    @patch("quant_engine.settlement.settlement_facade.actualizar_resultado_db")
    @patch("quant_engine.settlement.settlement_facade.os.path.exists")
    @patch("quant_engine.settlement.settlement_facade.sqlite3.connect")
    @patch("builtins.open", new_callable=mock_open, read_data='{"PERFORMANCE":{}}')
    def test_return_fields(
        self, mock_file, mock_connect, mock_exists, mock_update, mock_postmortem
    ):

        mock_exists.return_value = True

        mock_update.return_value = self.sample_pick()

        mock_postmortem.return_value = {}

        conn = mock_connect.return_value
        cursor = conn.cursor.return_value

        cursor.fetchone.side_effect = [
            ("MLB", '[{"rule":"CLV"}]'),
            (100.0, 1000.0),
            (50.0, 500.0),
            (80.0, 800.0),
        ]

        result = SettlementFacade.close_pick(pick_id=1, result="WIN")

        expected_keys = {
            "pick_id",
            "match_name",
            "sport_league",
            "selection",
            "odds",
            "profit_units",
            "actual_result",
            "lifetime_roi",
            "last_30d_roi",
            "last_90d_roi",
            "risk_state",
            "postmortem",
        }

        assert expected_keys.issubset(result.keys())
