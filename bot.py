import asyncio
import json
import logging
import os
import sqlite3

import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ==========================================
# IMPORTACIONES DE LA ARQUITECTURA NUEVA (V10)
# ==========================================
from quant_engine.config.settings import DB_PATH, LESSONS_MASTER_PATH, PERFORMANCE_FILE
from quant_engine.pipeline.pipeline_facade import PipelineFacade
from quant_engine.settlement.settlement_facade import SettlementFacade

load_dotenv()

# Configuración del Bot y Seguridad
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
AUTHORIZED_USER_ID = int(os.environ["TELEGRAM_AUTHORIZED_USER_ID"])

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


def es_usuario_autorizado(update: Update) -> bool:
    """Verifica si el mensaje proviene exclusivamente del dueño autorizado."""
    return update.effective_user.id == AUTHORIZED_USER_ID


# ==========================================
# COMANDOS DEL BOT INSTITUCIONAL
# ==========================================


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal de comandos operativos."""
    if not es_usuario_autorizado(update):
        return

    mensaje = (
        "🤖 *BetGemini Operational Bot (Hedge Fund Grade)*\n\n"
        "Comandos disponibles para gestión remota:\n\n"
        "🔹 `/analizar <Partido> | <Liga> | <Banca>`\n"
        "   _Ejecuta análisis multi-agente +EV._\n\n"
        "🔹 `/pending`\n"
        "   _Lista las apuestas pendientes de resolución en SQLite._\n\n"
        "🔹 `/cerrar <ID> <WIN/LOSS/PUSH>`\n"
        "   _Cierra un pick, actualiza bayesianamente, y lanza post-mortem JSON._\n\n"
        "🔹 `/rules`\n"
        "   _Muestra la salud y estatus de las reglas analíticas._\n\n"
        "🔹 `/lessons`\n"
        "   _Consulta los últimos hallazgos estructurados de la base de conocimiento._\n\n"
        "🔹 `/status`\n"
        "   _Muestra el ROI del portafolio y estado de riesgo global._\n\n"
        "🔹 `/ayuda`\n"
        "   _Muestra guías y ejemplos de formato._"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra ayuda detallada sobre los nuevos comandos."""
    if not es_usuario_autorizado(update):
        return

    mensaje = (
        "💡 *Guía de Operación Remota BetGemini*\n\n"
        "1. *Analizar un partido:*\n"
        "   `/analizar Toluca vs America | Liga MX | 10000`\n\n"
        "2. *Ver pendientes:*\n"
        "   `/pending`\n\n"
        "3. *Cerrar un pick manualmente:*\n"
        "   `/cerrar 12 WIN` (o `LOSS` / `PUSH`)\n\n"
        "4. *Monitorear reglas y conocimiento:*\n"
        "   `/rules` y `/lessons`"
    )
    await update.message.reply_text(mensaje, parse_mode="Markdown")


async def cmd_analizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ejecuta el pipeline cuantitativo utilizando PipelineFacade."""
    if not es_usuario_autorizado(update):
        return

    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso: `/analizar Partido | Liga | Banca`", parse_mode="Markdown"
        )
        return

    texto_entrada = " ".join(context.args)
    partes = [p.strip() for p in texto_entrada.split("|")]

    match_name = partes[0]
    sport_league = partes[1] if len(partes) > 1 and partes[1] else "General"

    try:
        bankroll = float(partes[2]) if len(partes) > 2 and partes[2] else 10000.0
    except ValueError:
        bankroll = 10000.0

    msg_espera = await update.message.reply_text(
        f"⏳ *Ejecutando Pipeline Institucional...*\n• *Partido:* {match_name}\n• *Liga:* {sport_league}",
        parse_mode="Markdown",
    )

    try:
        loop = asyncio.get_running_loop()
        # Instanciación limpia sin parámetros estrictos de PipelineFacade
        resultado = await loop.run_in_executor(
            None,
            lambda: PipelineFacade().ejecutar_analisis(
                match_name=match_name,
                sport_league=sport_league,
                bankroll=bankroll,
                user_instructions="Priorizar cuotas y aplicar rigor sabermétrico.",
            ),
        )

        report_path = resultado.get("report_path")
        if report_path and os.path.exists(report_path):
            await msg_espera.edit_text(
                f"✅ *Análisis Completado.*\n\nReporte guardado en: `{report_path}`",
                parse_mode="Markdown",
            )
        else:
            await msg_espera.edit_text(
                "✅ Análisis finalizado con éxito.", parse_mode="Markdown"
            )

    except Exception as e:
        logging.error(f"Error en comando analizar: {e}")
        await msg_espera.edit_text(
            f"❌ *Error en ejecución:* `{str(e)}`", parse_mode="Markdown"
        )


async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lista las apuestas pendientes usando SettlementFacade."""
    if not es_usuario_autorizado(update):
        return

    try:
        picks_pendientes = SettlementFacade.get_pending_picks()
        if not picks_pendientes:
            await update.message.reply_text(
                "ℹ️ No hay apuestas pendientes registradas actualmente.",
                parse_mode="Markdown",
            )
            return

        respuesta = "📋 *Apuestas Pendientes de Resolución:*\n\n"
        for p in picks_pendientes[:10]:
            respuesta += f"• *ID #{p.get('id')}:* {p.get('match_name')} | *Sel:* {p.get('selection')} (@{p.get('bookmaker_odds')})\n"

        await update.message.reply_text(respuesta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error al consultar pendientes: {e}", parse_mode="Markdown"
        )


async def cmd_cerrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cierra un pick manualmente y ejecuta actualización bayesiana y post-mortem."""
    if not es_usuario_autorizado(update):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Uso incorrecto. Ejemplo: `/cerrar 12 WIN` o `/cerrar 12 LOSS`",
            parse_mode="Markdown",
        )
        return

    try:
        pick_id = int(context.args[0])
        resultado = context.args[1].upper()

        if resultado not in ["WIN", "LOSS", "PUSH"]:
            await update.message.reply_text(
                "⚠️ El resultado debe ser `WIN`, `LOSS` o `PUSH`.",
                parse_mode="Markdown",
            )
            return

        msg = await update.message.reply_text(
            f"🔄 Procesando cierre del Pick #{pick_id} como {resultado}...",
            parse_mode="Markdown",
        )

        loop = asyncio.get_running_loop()
        res_cierre = await loop.run_in_executor(
            None,
            lambda: SettlementFacade.close_pick(
                pick_id=pick_id, result=resultado, run_postmortem=True
            ),
        )

        post_data = res_cierre.get("postmortem", {})
        respuesta = (
            f"✅ *Pick #{pick_id} Cerrado Exitosamente*\n"
            f"• *Resultado:* {res_cierre.get('actual_result')}\n"
            f"• *Profit:* {res_cierre.get('profit_units'):+.2f}u\n\n"
            f"🧠 *Auditoría Post-Mortem:*\n"
            f"• *Clasificación:* `{post_data.get('classification', 'N/A')}`\n"
            f"• *Causa Raíz:* {post_data.get('root_cause', 'N/A')}"
        )
        await msg.edit_text(respuesta, parse_mode="Markdown")

    except Exception as e:
        logging.error(f"Error cerrando pick: {e}")
        await update.message.reply_text(
            f"❌ Error al cerrar la apuesta: {e}", parse_mode="Markdown"
        )


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el rendimiento de las reglas analíticas desde rule_performance.json."""
    if not es_usuario_autorizado(update):
        return

    if not os.path.exists(PERFORMANCE_FILE):
        await update.message.reply_text(
            "ℹ️ Aún no existe el archivo `rule_performance.json`.",
            parse_mode="Markdown",
        )
        return

    try:
        with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        perf_dict = data.get("PERFORMANCE", {})
        if not perf_dict:
            await update.message.reply_text(
                "ℹ️ No hay reglas registradas en rendimiento.", parse_mode="Markdown"
            )
            return

        respuesta = "🧠 *Monitoreo de Reglas Analíticas*\n\n"
        for rule, metrics in list(perf_dict.items())[:8]:
            respuesta += (
                f"• *{rule}*\n"
                f"  Status: `{metrics.get('status')}` | ROI: `{metrics.get('roi_pct', 0.0):+.1f}%` | "
                f"Alpha: {round(metrics.get('alpha_success', 0), 1)} | Beta: {round(metrics.get('beta_failures', 0), 1)}\n\n"
            )
        await update.message.reply_text(respuesta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error al leer reglas: {e}", parse_mode="Markdown"
        )


async def cmd_lessons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta los últimos hallazgos estructurados de lessons_master.json."""
    if not es_usuario_autorizado(update):
        return

    if not os.path.exists(LESSONS_MASTER_PATH):
        await update.message.reply_text(
            "ℹ️ Aún no hay lecciones registradas en `lessons_master.json`.",
            parse_mode="Markdown",
        )
        return

    try:
        with open(LESSONS_MASTER_PATH, "r", encoding="utf-8") as f:
            lessons = json.load(f)

        if not lessons or not isinstance(lessons, list):
            await update.message.reply_text(
                "ℹ️ La base de conocimiento está vacía.", parse_mode="Markdown"
            )
            return

        ultimas = lessons[-3:]
        respuesta = "📚 *Últimos Hallazgos (Lessons Learned)*\n\n"
        for lesson in ultimas:
            respuesta += (
                f"• *Pick #{lesson.get('pick_id')} ({lesson.get('match_name')})*\n"
                f"  Clasificación: `{lesson.get('classification')}`\n"
                f"  Hallazgo: {lesson.get('finding')}\n"
                f"  Regla Propuesta: _{lesson.get('rule_candidate')}_\n\n"
            )
        await update.message.reply_text(respuesta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error al leer lecciones: {e}", parse_mode="Markdown"
        )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el ROI real y el estado de riesgo dinámico del portafolio."""
    if not os.path.exists(DB_PATH):
        await update.message.reply_text(
            "ℹ️ La base de datos de apuestas aún no existe.", parse_mode="Markdown"
        )
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT bookmaker_odds, recommended_stake_amount, actual_result, profit_units FROM historical_picks"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if df.empty:
            await update.message.reply_text(
                "ℹ️ No hay apuestas registradas en el historial.", parse_mode="Markdown"
            )
            return

        # Corrección aplicada: Se valida contra 'PUSH' y se descarta el typo 'PUMP'
        cerradas = df[df["actual_result"].isin(["WIN", "LOSS", "PUSH"])]
        total_bets = len(df)
        total_cerradas = len(cerradas)

        profit_total_u = df["profit_units"].sum()
        win_count = len(df[df["actual_result"] == "WIN"])
        win_rate = (win_count / total_cerradas * 100) if total_cerradas > 0 else 0.0

        # Lectura dinámica del estado de riesgo real desde rule_performance.json
        risk_state = "ACTIVE"
        if os.path.exists(PERFORMANCE_FILE):
            try:
                with open(PERFORMANCE_FILE, "r", encoding="utf-8") as pf:
                    perf_data = json.load(pf)
                risk_state = perf_data.get("GLOBAL_RISK_STATE", "ACTIVE")
            except Exception:
                pass

        respuesta = (
            f"📊 *Estado del Portafolio (Hedge Fund)*\n\n"
            f"• *Total de Picks:* {total_bets} ({total_cerradas} cerrados)\n"
            f"• *Win Rate Global:* {win_rate:.1f}%\n"
            f"• *Profit Acumulado:* {profit_total_u:+.2f} Unidades\n"
            f"• *Estado de Riesgo:* `{risk_state}`"
        )
        await update.message.reply_text(respuesta, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(
            f"❌ Error al calcular estatus: {e}", parse_mode="Markdown"
        )


# ==========================================
# INICIALIZACIÓN DE LA APLICACIÓN
# ==========================================


def main():
    if TELEGRAM_TOKEN == "TU_TELEGRAM_BOT_TOKEN_AQUI":
        print("🛑 ERROR: Debes ingresar tu TELEGRAM_TOKEN en bot.py antes de ejecutar.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ayuda", cmd_ayuda))
    app.add_handler(CommandHandler("analizar", cmd_analizar))
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("cerrar", cmd_cerrar))
    app.add_handler(CommandHandler("rules", cmd_rules))
    app.add_handler(CommandHandler("lessons", cmd_lessons))
    app.add_handler(CommandHandler("status", cmd_status))

    print("🤖 Bot de Telegram institucional activo y escuchando comandos...")
    app.run_polling()


if __name__ == "__main__":
    main()
