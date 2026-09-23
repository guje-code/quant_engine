import json
import sqlite3
import tempfile
from pathlib import Path

from quant_engine.storage.persistence import guardar_pick_en_db_citadel, inicializar_db


class TestPersistence:

    def create_temp_db(self):

        temp_dir = tempfile.TemporaryDirectory()

        db_path = Path(temp_dir.name) / "test.db"

        inicializar_db(str(db_path))

        return temp_dir, str(db_path)

    # ==========================================
    # DB INIT
    # ==========================================

    def test_database_is_created(self):

        temp_dir, db_path = self.create_temp_db()

        assert Path(db_path).exists()

        temp_dir.cleanup()

    # ==========================================
    # INSERT PICK
    # ==========================================

    def test_save_pick(self):

        temp_dir, db_path = self.create_temp_db()

        quant_data = {
            "selection": "Boston Red Sox",
            "market_type": "Moneyline",
            "bookmaker_odds": 2.10,
            "estimated_true_probability": 0.58,
            "expected_value_percentage": 6.0,
            "confidence_score": 88,
            "meta_risk_score": 12,
            "risk_level": "LOW RISK",
            "rule_engine_audit": {"coverage": 100.0, "total_adjustment": 0.10},
        }

        risk_data = {"recommended_stake_units": 3.0}

        guardar_pick_en_db_citadel(
            data_quant=quant_data,
            data_risk=risk_data,
            match_name="Boston Red Sox vs Yankees",
            league="MLB",
            bankroll=10000,
            line_movement_pct=2.0,
            steam_detected=False,
            triggered_rules=[{"rule": "CLV"}],
            cluster_hits={},
            var_amount=100.0,
            cvar_amount=150.0,
            sigma_snapshot={"fallback": False, "optimal_delta": 0.8},
            db_path=db_path,
        )

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM historical_picks
            """)

        count = cursor.fetchone()[0]

        conn.close()

        assert count == 1

        temp_dir.cleanup()

    # ==========================================
    # RULES JSON
    # ==========================================

    def test_rules_are_saved(self):

        temp_dir, db_path = self.create_temp_db()

        quant_data = {
            "selection": "A",
            "market_type": "Moneyline",
            "bookmaker_odds": 2.0,
            "estimated_true_probability": 0.55,
            "expected_value_percentage": 5.0,
            "confidence_score": 80,
            "meta_risk_score": 10,
            "risk_level": "LOW",
            "rule_engine_audit": {"coverage": 100.0, "total_adjustment": 0.10},
        }

        risk_data = {"recommended_stake_units": 2.0}

        guardar_pick_en_db_citadel(
            quant_data,
            risk_data,
            "Match",
            "MLB",
            10000,
            1.0,
            False,
            [{"rule": "CLV"}, {"rule": "BFI"}],
            {},
            50,
            80,
            {"fallback": False, "optimal_delta": 0.5},
            db_path,
        )

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT triggered_rules_json
            FROM historical_picks
            LIMIT 1
            """)

        rules_json = cursor.fetchone()[0]

        conn.close()

        rules = json.loads(rules_json)

        assert "CLV" in rules
        assert "BFI" in rules

        temp_dir.cleanup()

    # ==========================================
    # SIGMA SNAPSHOT
    # ==========================================

    def test_sigma_snapshot_saved(self):

        temp_dir, db_path = self.create_temp_db()

        quant_data = {
            "selection": "A",
            "market_type": "Moneyline",
            "bookmaker_odds": 2.0,
            "estimated_true_probability": 0.55,
            "expected_value_percentage": 5.0,
            "confidence_score": 80,
            "meta_risk_score": 10,
            "risk_level": "LOW",
            "rule_engine_audit": {"coverage": 100.0, "total_adjustment": 0.10},
        }

        risk_data = {"recommended_stake_units": 2.0}

        guardar_pick_en_db_citadel(
            quant_data,
            risk_data,
            "Match",
            "MLB",
            10000,
            1.0,
            False,
            [],
            {},
            50,
            80,
            {"fallback": False, "optimal_delta": 0.77},
            db_path,
        )

        conn = sqlite3.connect(db_path)

        cursor = conn.cursor()

        cursor.execute("""
            SELECT sigma_snapshot_json
            FROM historical_picks
            LIMIT 1
            """)

        sigma_json = cursor.fetchone()[0]

        conn.close()

        sigma = json.loads(sigma_json)

        assert sigma["optimal_delta"] == 0.77

        temp_dir.cleanup()
