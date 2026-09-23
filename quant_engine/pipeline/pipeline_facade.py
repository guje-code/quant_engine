import os
import time

from dotenv import load_dotenv

from quant_engine.config.settings import DB_PATH, REPORTS_DIR
from quant_engine.core.pipeline_steps.persistence_stage import (
    ejecutar_etapa_persistencia,
)
from quant_engine.core.pipeline_steps.quant_risk_stage import ejecutar_etapa_quant_risk
from quant_engine.core.pipeline_steps.rule_stage import ejecutar_etapa_reglas
from quant_engine.core.pipeline_steps.scout_stage import ejecutar_etapa_scout
from quant_engine.storage.persistence import inicializar_db

load_dotenv()
os.makedirs(REPORTS_DIR, exist_ok=True)


class PipelineFacade:
    def __init__(self, api_key: str = None):
        """
        Inicializa la fachada del pipeline permitiendo llamadas sin parámetros obligatorios,
        recuperando la API Key del entorno de manera automática si no se proporciona.
        """
        inicializar_db(DB_PATH)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def ejecutar_analisis(
        self,
        match_name: str,
        sport_league: str,
        bankroll: float,
        user_instructions: str = "",
        custom_tools: dict = None,
    ) -> dict:
        """
        Ejecuta el pipeline multietapa, persiste el reporte en disco y retorna un
        diccionario estructurado con todas las métricas y la ruta del archivo.
        """
        t_inicio = time.time()
        print(
            f"\n📊 [PIPELINE FACADE v10.0 - {sport_league.upper()}] Iniciando para: {match_name}..."
        )

        # Etapa 1: Scout y Inteligencia de Mercado (CLV / Steam Moves)
        scout_res = ejecutar_etapa_scout(
            match_name, sport_league, user_instructions, self.api_key, custom_tools
        )
        if not scout_res["success"]:
            return {
                "success": False,
                "stage": "SCOUT",
                "reason": scout_res["reason"],
                "message": f"🛑 *ABORTADO EN SCOUT/MERCADO:* {scout_res['reason']}",
            }

        # Etapa 2: Rule Engine Modular & Circuit Breakers (P0)
        rule_res = ejecutar_etapa_reglas(
            scout_res["scout_json"],
            sport_league,
            scout_res["line_movement_pct"],
            scout_res["steam_detected"],
        )
        if rule_res.get("circuit_breaker_triggered"):
            return {
                "success": False,
                "stage": "CIRCUIT_BREAKER",
                "reason": rule_res["circuit_breaker_reason"],
                "message": f"🛑 *ABORTADO EN P0 (CIRCUIT BREAKER):* {rule_res['circuit_breaker_reason']}",
            }

        # Etapa 3: Quant, Probabilidades, Kelly y Monte Carlo (VaR/CVaR Student-t)
        qr_res = ejecutar_etapa_quant_risk(
            match_name,
            sport_league,
            bankroll,
            scout_res,
            rule_res,
            self.api_key,
            custom_tools,
        )
        if not qr_res["success"]:
            return {
                "success": False,
                "stage": "RISK",
                "reason": qr_res["reason"],
                "message": f"🛑 *ABORTADO EN RIESGO:* {qr_res['reason']}",
            }

        # Etapa 4: Persistencia Forense en SQLite
        ejecutar_etapa_persistencia(qr_res, DB_PATH)

        t_total = (time.time() - t_inicio) * 1000

        # Generación y persistencia del archivo de reporte en disco
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_match_name = "".join([c if c.isalnum() else "_" for c in match_name])
        report_filename = f"report_{safe_match_name}_{timestamp}.txt"
        report_filepath = os.path.join(REPORTS_DIR, report_filename)

        formatted_message = (
            f"📊 *RESULTADO QUANTITATIVE CITADEL v10.0 [{sport_league.upper()}]*\n"
            f"⚔️ *Partido:* {match_name} | *Cuota Viva:* {qr_res['odds']} | *EV:* {qr_res['ev']}%\n"
            f"📈 *CLV Movement:* {scout_res['line_movement_pct']:+.2f}% | ⚡ *Steam Move:* {'ACTIVADO' if scout_res['steam_detected'] else 'INACTIVO'}\n"
            f"🧠 *Ledoit-Wolf Optimal Delta & Student-t Copula:* Activos\n"
            f"🎲 *Portfolio VaR 95%:* ${qr_res['var_amount']} ({qr_res['var_pct']}% banca) [SEGURO]\n"
            f"📉 *Portfolio CVaR 95%:* ${qr_res['cvar_amount']} ({qr_res['cvar_pct']}% banca) [SEGURO]\n"
            f"💰 *Stake Sugerido:* {qr_res['stake_final']}% (${qr_res['monto_apuesta']:,.2f} MXN)\n"
            f"⏱️ *Telemetría Total:* {t_total:.1f}ms\n"
            f"✅ *Estatus:* APROBADA, persistida y auditada bajo pipeline multietapa."
        )

        with open(report_filepath, "w", encoding="utf-8") as f:
            f.write(formatted_message)

        # Retorno estructurado completo con la ruta del reporte físico
        return {
            "success": True,
            "match_name": match_name,
            "sport_league": sport_league,
            "odds": qr_res.get("odds"),
            "ev": qr_res.get("ev"),
            "stake_pct": qr_res.get("stake_final"),
            "stake_amount": qr_res.get("monto_apuesta"),
            "var_amount": qr_res.get("var_amount"),
            "cvar_amount": qr_res.get("cvar_amount"),
            "line_movement_pct": scout_res.get("line_movement_pct"),
            "steam_detected": scout_res.get("steam_detected"),
            "telemetry_ms": t_total,
            "report_path": report_filepath,
            "message": formatted_message,
        }
