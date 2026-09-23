import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from quant_engine.settlement.result_updater import (
    actualizar_resultado_db,
    listar_apuestas_pendientes,
)


class TestResultUpdater:

    # ==========================================
    # DATABASE HELPER
    # ==========================================

    def create_test_db(self):

        tmp = tempfile.TemporaryDirectory()

        db_path = Path(tmp.name) / "test.db"

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE historical_picks (
        id INTEGER PRIMARY KEY,
        match_name TEXT,
        sport_league TEXT,
        selection TEXT,
        bookmaker_odds REAL,
        recommended_stake_amount REAL,
        actual_result TEXT,
        profit_units REAL,
        created_at TEXT
        )
        """)

        cursor.execute("""
            INSERT INTO historical_picks (
                id,
                match_name,
                sport_league,
                selection,
                bookmaker_odds,
                recommended_stake_amount,
                actual_result,
                profit_units,
                created_at
            )
            VALUES (
                1,
                'Boston vs Yankees',
                'MLB',
                'Boston',
                2.0,
                1000.0,
                'PENDING',
                0.0,
                '2024-06-01 00:00:00'
            )
        """)

        conn.commit()
        conn.close()

        return tmp, str(db_path)

    # ==========================================
    # LIST PENDING
    # ==========================================

    @patch("quant_engine.settlement.result_updater.DB_PATH")
    def test_list_pending_picks(self, mock_db_path):

        tmp, db_path = self.create_test_db()

        mock_db_path.__str__ = lambda self=None: db_path

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            result = listar_apuestas_pendientes()

        assert len(result) == 1

        tmp.cleanup()

    # ==========================================
    # WIN
    # ==========================================

    def test_update_win(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            result = actualizar_resultado_db(pick_id=1, resultado="WIN")

        assert result["actual_result"] == "WIN"
        assert result["profit_units"] == 1000.0

        tmp.cleanup()

    # ==========================================
    # LOSS
    # ==========================================

    def test_update_loss(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            result = actualizar_resultado_db(pick_id=1, resultado="LOSS")

        assert result["actual_result"] == "LOSS"
        assert result["profit_units"] == -1000.0

        tmp.cleanup()

    # ==========================================
    # PUSH
    # ==========================================

    def test_update_push(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            result = actualizar_resultado_db(pick_id=1, resultado="PUSH")

        assert result["actual_result"] == "PUSH"
        assert result["profit_units"] == 0.0

        tmp.cleanup()

    # ==========================================
    # INVALID PICK
    # ==========================================

    def test_invalid_pick_id(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            try:
                actualizar_resultado_db(pick_id=999, resultado="WIN")

                assert False

            except ValueError:
                assert True

        tmp.cleanup()

    # ==========================================
    # INVALID RESULT
    # ==========================================

    def test_invalid_result(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            try:
                actualizar_resultado_db(pick_id=1, resultado="INVALID")

                assert False

            except ValueError:
                assert True

        tmp.cleanup()

    # ==========================================
    # RETURN CONTRACT
    # ==========================================

    def test_return_contract(self):

        tmp, db_path = self.create_test_db()

        with patch("quant_engine.settlement.result_updater.DB_PATH", db_path):
            result = actualizar_resultado_db(1, "WIN")

        expected_keys = {
            "pick_id",
            "match_name",
            "sport_league",
            "selection",
            "odds",
            "stake",
            "actual_result",
            "profit_units",
        }

        assert expected_keys.issubset(result.keys())

        tmp.cleanup()
