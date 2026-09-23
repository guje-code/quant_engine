import json
import os
import sqlite3
from datetime import datetime

from quant_engine.config.settings import DB_PATH, MONTE_CARLO_ITERATIONS, STUDENT_T_DF


def inicializar_db(db_path: str = DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historical_picks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_name TEXT,
            sport_league TEXT,
            selection TEXT,
            market_type TEXT,
            bookmaker_odds REAL,
            estimated_true_probability REAL,
            expected_value_percentage REAL,
            confidence_score INTEGER,
            meta_risk_score INTEGER,
            risk_level TEXT,
            line_movement_pct REAL,
            steam_move_active INTEGER DEFAULT 0,
            rule_coverage_pct REAL,
            recommended_stake_units REAL,
            recommended_stake_amount REAL,
            triggered_rules_json TEXT,
            cluster_hits_json TEXT,
            elasticity_factor REAL,
            var_95_amount REAL,
            cvar_95_amount REAL,
            sigma_snapshot_json TEXT,
            engine_state_snapshot_json TEXT,
            actual_result TEXT DEFAULT 'PENDING',
            profit_units REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def guardar_pick_en_db_citadel(
    data_quant: dict,
    data_risk: dict,
    match_name: str,
    league: str,
    bankroll: float,
    line_movement_pct: float,
    steam_detected: bool,
    triggered_rules: list,
    cluster_hits: dict,
    var_amount: float,
    cvar_amount: float,
    sigma_snapshot: dict,
    db_path: str = DB_PATH,
):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stake_units = float(data_risk.get("recommended_stake_units", 0.0))
    monto_apuesta = round((stake_units / 100.0) * bankroll, 2)

    engine_state_snapshot = {
        "monte_carlo_iter": MONTE_CARLO_ITERATIONS,
        "copula": f"Student-t (df={STUDENT_T_DF})",
        "optimal_delta": sigma_snapshot.get("optimal_delta", 1.0),
        "total_adjustment": data_quant.get("rule_engine_audit", {}).get(
            "total_adjustment", 0.0
        ),
    }

    cursor.execute(
        """
        INSERT INTO historical_picks 
        (created_at, match_name, sport_league, selection, market_type, bookmaker_odds, 
         estimated_true_probability, expected_value_percentage, confidence_score, meta_risk_score, risk_level,
         line_movement_pct, steam_move_active, rule_coverage_pct, recommended_stake_units, recommended_stake_amount, 
         triggered_rules_json, cluster_hits_json, elasticity_factor, var_95_amount, cvar_95_amount, 
         sigma_snapshot_json, engine_state_snapshot_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            fecha_actual,
            match_name,
            league,
            data_quant.get("selection"),
            data_quant.get("market_type"),
            float(data_quant.get("bookmaker_odds", 0.0)),
            float(data_quant.get("estimated_true_probability", 0.0)),
            float(data_quant.get("expected_value_percentage", 0.0)),
            int(data_quant.get("confidence_score", 0)),
            int(data_quant.get("meta_risk_score", 0)),
            str(data_quant.get("risk_level", "LOW RISK")),
            line_movement_pct,
            1 if steam_detected else 0,
            float(data_quant.get("rule_engine_audit", {}).get("coverage", 100.0)),
            stake_units,
            monto_apuesta,
            json.dumps([r["rule"] for r in triggered_rules]),
            json.dumps(cluster_hits),
            1.0,
            var_amount,
            cvar_amount,
            json.dumps(
                {
                    "fallback": sigma_snapshot["fallback"],
                    "optimal_delta": sigma_snapshot.get("optimal_delta", 1.0),
                }
            ),
            json.dumps(engine_state_snapshot),
        ),
    )
    conn.commit()
    conn.close()
