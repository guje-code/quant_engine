from unittest.mock import patch

from quant_engine.core.pipeline_steps.persistence_stage import (
    ejecutar_etapa_persistencia,
)


class TestPersistenceStage:

    def build_qr_res(self):

        return {
            "quant_json": {
                "match_name": "Boston Red Sox vs Yankees",
                "sport_league": "MLB",
                "selection": "Boston",
            },
            "risk_json": {"final_verdict": "APPROVED"},
            "triggered_rules_list": [{"rule": "CLV"}],
            "cluster_hits": {},
            "var_amount": 100.0,
            "cvar_amount": 150.0,
            "sigma_snapshot": {"fallback": False, "optimal_delta": 0.8},
        }

    # ==========================================
    # APPROVED PICK
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.persistence_stage.guardar_pick_en_db_citadel"
    )
    def test_persistence_called_for_approved_pick(self, mock_persist):

        ejecutar_etapa_persistencia(self.build_qr_res(), "test.db")

        mock_persist.assert_called_once()

    # ==========================================
    # REJECTED PICK
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.persistence_stage.guardar_pick_en_db_citadel"
    )
    def test_persistence_not_called_for_rejected_pick(self, mock_persist):

        qr_res = self.build_qr_res()

        qr_res["risk_json"]["final_verdict"] = "REJECTED"

        ejecutar_etapa_persistencia(qr_res, "test.db")

        mock_persist.assert_not_called()

    # ==========================================
    # DB PATH FORWARDED
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.persistence_stage.guardar_pick_en_db_citadel"
    )
    def test_db_path_forwarded(self, mock_persist):

        ejecutar_etapa_persistencia(self.build_qr_res(), "custom.db")

        _, kwargs = mock_persist.call_args

        assert kwargs["db_path"] == "custom.db"

    # ==========================================
    # REQUIRED PAYLOAD FIELDS
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.persistence_stage.guardar_pick_en_db_citadel"
    )
    def test_expected_arguments_forwarded(self, mock_persist):

        qr_res = self.build_qr_res()

        ejecutar_etapa_persistencia(qr_res, "test.db")

        _, kwargs = mock_persist.call_args

        expected_fields = {
            "data_quant",
            "data_risk",
            "match_name",
            "league",
            "triggered_rules",
            "cluster_hits",
            "var_amount",
            "cvar_amount",
            "sigma_snapshot",
            "db_path",
        }

        assert expected_fields.issubset(kwargs.keys())

    # ==========================================
    # MATCH NAME PASSTHROUGH
    # ==========================================

    @patch(
        "quant_engine.core.pipeline_steps.persistence_stage.guardar_pick_en_db_citadel"
    )
    def test_match_name_forwarded(self, mock_persist):

        qr_res = self.build_qr_res()

        ejecutar_etapa_persistencia(qr_res, "test.db")

        _, kwargs = mock_persist.call_args

        assert kwargs["match_name"] == "Boston Red Sox vs Yankees"
