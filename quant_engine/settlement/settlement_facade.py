import json
import os
import sqlite3

from quant_engine.config.settings import DB_PATH, PERFORMANCE_FILE, RULE_MIN_SAMPLE_SIZE
from quant_engine.settlement.postmortem_engine import analizar_post_mortem
from quant_engine.settlement.result_updater import (
    actualizar_resultado_db,
    listar_apuestas_pendientes,
)


class SettlementFacade:
    @staticmethod
    def get_pending_picks() -> list:
        """Obtiene el listado de apuestas pendientes de liquidar desde SQLite."""
        return listar_apuestas_pendientes()

    @staticmethod
    def close_pick(
        pick_id: int,
        result: str,
        profit_units: float = None,
        run_postmortem: bool = True,
        marcador_real: str = "",
    ) -> dict:
        """
        Fachada maestra de liquidación institucional (Versión Final Completa):
        1. Actualiza SQLite y calcula el profit monetario real.
        2. Actualiza el rendimiento bayesiano, ROI y microrregulación de estatus por regla analítica.
        3. Recalcula los ROIs móviles globales del portafolio.
        4. Evalúa el estado de riesgo global del portafolio.
        5. (Opcional) Ejecuta análisis post-mortem cognitivo y registra lecciones aprendidas.
        """
        # ==========================================
        # PASO 1: Actualización Operativa en SQLite
        # ==========================================
        pick_data = actualizar_resultado_db(pick_id, result, profit_units)
        print(
            f"✅ [DB SYNC] Pick #{pick_id} cerrado: {pick_data['actual_result']} (${pick_data['profit_units']} MXN)."
        )

        if not os.path.exists(DB_PATH):
            raise ValueError(f"No se encontró la base de datos en {DB_PATH}")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            # ==========================================
            # PASO 2: Feedback Bayesiano, ROI y Status por Regla
            # ==========================================
            cursor.execute(
                "SELECT sport_league, triggered_rules_json FROM historical_picks WHERE id = ?",
                (pick_id,),
            )
            meta_row = cursor.fetchone()

            triggered_rules = []
            if meta_row and meta_row[1]:
                try:
                    triggered_rules = json.loads(meta_row[1])
                except Exception:
                    triggered_rules = []

            is_win = 1 if pick_data["actual_result"] == "WIN" else 0
            is_loss = 1 if pick_data["actual_result"] == "LOSS" else 0
            pick_profit = pick_data["profit_units"]
            pick_stake = pick_data["stake"]

            if os.path.exists(PERFORMANCE_FILE):
                try:
                    with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
                        file_content = json.load(f)
                except Exception:
                    file_content = {}
            else:
                file_content = {}

            if "PERFORMANCE" not in file_content or not isinstance(
                file_content["PERFORMANCE"], dict
            ):
                file_content["PERFORMANCE"] = {}

            perf_data = file_content["PERFORMANCE"]

            # Actualización y microrregulación autónoma por cada regla disparada
            for rule in triggered_rules:
                rule_id = (
                    rule.get("rule")
                    or rule.get("rule_id")
                    or rule.get("name")
                    or "GENERAL"
                )
                if rule_id not in perf_data:
                    perf_data[rule_id] = {
                        "alpha_success": 50.0,
                        "beta_failures": 50.0,
                        "total_bets": 0,
                        "total_profit": 0.0,
                        "total_staked": 0.0,
                        "roi_pct": 0.0,
                        "status": "ACTIVE",
                    }

                # Actualizar métricas financieras y bayesianas
                perf_data[rule_id]["alpha_success"] += is_win
                perf_data[rule_id]["beta_failures"] += is_loss
                perf_data[rule_id]["total_bets"] += 1
                perf_data[rule_id]["total_profit"] = round(
                    perf_data[rule_id].get("total_profit", 0.0) + pick_profit, 2
                )
                perf_data[rule_id]["total_staked"] = round(
                    perf_data[rule_id].get("total_staked", 0.0) + pick_stake, 2
                )

                staked_rule = perf_data[rule_id]["total_staked"]
                if staked_rule > 0:
                    perf_data[rule_id]["roi_pct"] = round(
                        (perf_data[rule_id]["total_profit"] / staked_rule) * 100.0, 2
                    )

                # Evaluación autónoma de estatus individual por regla usando RULE_MIN_SAMPLE_SIZE
                rule_roi = perf_data[rule_id]["roi_pct"]
                rule_bets = perf_data[rule_id]["total_bets"]

                if rule_bets >= RULE_MIN_SAMPLE_SIZE:
                    if rule_roi < -15.0:
                        perf_data[rule_id]["status"] = "DISABLED"
                    elif rule_roi < -5.0:
                        perf_data[rule_id]["status"] = "MONITOR"
                    else:
                        perf_data[rule_id]["status"] = "ACTIVE"
                else:
                    perf_data[rule_id]["status"] = "ACTIVE"

                print(
                    f"📈 [RULE ENGINE] Regla '{rule_id}' -> ROI: {perf_data[rule_id]['roi_pct']}% | Status: [{perf_data[rule_id]['status']}]"
                )

            file_content["PERFORMANCE"] = perf_data
            with open(PERFORMANCE_FILE, "w", encoding="utf-8") as f:
                json.dump(file_content, f, indent=4, ensure_ascii=False)
            print(
                f"💾 [PERSISTENCE] Rendimiento y estados por regla actualizados en {PERFORMANCE_FILE}."
            )

            # ==========================================
            # PASO 3: Recálculo de ROIs Móviles Globales
            # ==========================================
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(profit_units), 0.0) as total_profit,
                    COALESCE(SUM(recommended_stake_amount), 1.0) as total_staked
                FROM historical_picks
                WHERE actual_result IN ('WIN', 'LOSS', 'PUSH')
            """)
            lifetime_stats = cursor.fetchone()
            lifetime_roi = (
                round((lifetime_stats[0] / lifetime_stats[1]) * 100.0, 2)
                if lifetime_stats[1] > 0
                else 0.0
            )

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(profit_units), 0.0) as p30,
                    COALESCE(SUM(recommended_stake_amount), 1.0) as s30
                FROM historical_picks
                WHERE actual_result IN ('WIN', 'LOSS', 'PUSH')
                AND created_at >= datetime('now', '-30 days')
            """)
            r30_stats = cursor.fetchone()
            last_30d_roi = (
                round((r30_stats[0] / r30_stats[1]) * 100.0, 2)
                if r30_stats[1] > 0
                else 0.0
            )

            cursor.execute("""
                SELECT 
                    COALESCE(SUM(profit_units), 0.0) as p90,
                    COALESCE(SUM(recommended_stake_amount), 1.0) as s90
                FROM historical_picks
                WHERE actual_result IN ('WIN', 'LOSS', 'PUSH')
                AND created_at >= datetime('now', '-90 days')
            """)
            r90_stats = cursor.fetchone()
            last_90d_roi = (
                round((r90_stats[0] / r90_stats[1]) * 100.0, 2)
                if r90_stats[1] > 0
                else 0.0
            )

            print(
                f"📊 [GLOBAL ROI] Lifetime: {lifetime_roi}% | 30d: {last_30d_roi}% | 90d: {last_90d_roi}%"
            )

            # ==========================================
            # PASO 4: Estado de Riesgo Global del Portafolio
            # ==========================================
            if last_30d_roi < -20.0:
                risk_state = "DISABLED"
            elif last_30d_roi < -10.0:
                risk_state = "MONITOR"
            else:
                risk_state = "ACTIVE"

            print(
                f"🛡️ [RISK STATES] Estado global evaluado: [{risk_state}] (Basado en ROI 30d: {last_30d_roi}%)"
            )

        except Exception as e:
            print(f"❌ [CRITICAL] Error en ciclo bayesiano/riesgo: {e}")
            risk_state = "ACTIVE"
            lifetime_roi, last_30d_roi, last_90d_roi = 0.0, 0.0, 0.0
        finally:
            conn.close()

        # ==========================================
        # PASO 5: Post-Mortem Cognitivo y Lessons Learned
        # ==========================================
        postmortem_text = None
        if run_postmortem:
            print(
                f"🧠 [POST-MORTEM ENGINE] Iniciando auditoría con agentes para Pick #{pick_id}..."
            )
            postmortem_text = analizar_post_mortem(
                pick_id=pick_id,
                match_name=pick_data["match_name"],
                sport_league=pick_data["sport_league"],
                selection=pick_data["selection"],
                odds=pick_data["odds"],
                resultado=pick_data["actual_result"],
                marcador_real=marcador_real,
            )
            print(
                "📚 [LESSONS LEARNED] Hallazgos sabermétricos inyectados en el Log Maestro."
            )

        return {
            "pick_id": pick_id,
            "match_name": pick_data["match_name"],
            "sport_league": pick_data["sport_league"],
            "selection": pick_data["selection"],
            "odds": pick_data["odds"],
            "profit_units": pick_data["profit_units"],
            "actual_result": pick_data["actual_result"],
            "lifetime_roi": lifetime_roi,
            "last_30d_roi": last_30d_roi,
            "last_90d_roi": last_90d_roi,
            "risk_state": risk_state,
            "postmortem": postmortem_text,
        }
