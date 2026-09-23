import json
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from model_validator import (
    calcular_brier_score,
    obtener_datos_evaluados,
    obtener_tabla_calibracion,
)

# ==========================================
# IMPORTACIONES DE LA ARQUITECTURA NUEVA (V10)
# ==========================================
from quant_engine.config.settings import (
    DB_PATH,
    LESSONS_MASTER_PATH,
    PERFORMANCE_FILE,
    REPORTS_DIR,
)
from quant_engine.pipeline.pipeline_facade import PipelineFacade
from quant_engine.settlement.settlement_facade import SettlementFacade

# Configuración de la página
st.set_page_config(
    page_title="BetGemini - AgentCrew Terminal", page_icon="⚽", layout="wide"
)

# Estilo CSS personalizado
st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("⚽ BetGemini — Terminal de Análisis y Riesgo")
st.caption("Sistema Multi-Agente para la detección de apuestas +EV y gestión de banca")

# Catálogo de Deportes, Confederaciones y Ligas
SPORTS_CATALOG = {
    "Fútbol": {
        "UEFA (Europa)": [
            "UEFA Champions League",
            "Bundesliga",
            "Premier League",
            "La Liga",
            "Serie A",
            "Ligue 1",
            "UEFA Europa League",
            "UEFA Conference League",
            "Eredivisie",
            "Primeira Liga",
            "Otra Liga UEFA / Personalizada",
        ],
        "CONCACAF (Norte y Centroamérica)": [
            "Liga MX",
            "MLS",
            "Liga de Expansión MX",
            "CONCACAF Champions Cup",
            "Leagues Cup",
            "Otra Liga CONCACAF",
        ],
        "CONMEBOL (Sudamérica)": [
            "Copa Libertadores",
            "Copa Sudamericana",
            "Liga Profesional (Argentina)",
            "Brasileirão Serie A",
            "Liga BetPlay (Colombia)",
            "Primera División (Chile)",
            "Otra Liga CONMEBOL",
        ],
        "AFC (Asia y Medio Oriente)": [
            "Saudi Pro League",
            "AFC Champions League",
            "J1 League (Japón)",
            "K League 1 (Corea)",
            "Qatar Stars League",
            "Otra Liga AFC",
        ],
        "CAF (África)": [
            "CAF Champions League",
            "Egyptian Premier League",
            "Botola Pro (Marruecos)",
            "Otra Liga CAF",
        ],
        "FIFA / Internacional": [
            "Copa del Mundo FIFA",
            "Eliminatorias Mundialistas",
            "Eurocopa",
            "Copa América",
            "UEFA Nations League",
            "Amistosos Internacionales",
            "Otra Competición FIFA",
        ],
        "Otra Confederación": ["Personalizada"],
    },
    "Béisbol": {
        "MLB / Norteamérica": [
            "MLB",
            "MLB Postseason",
            "MLB Spring Training",
            "MiLB (Triple-A)",
        ],
        "México": [
            "LMB (Liga Mexicana de Beisbol)",
            "LMP (Liga Mexicana del Pacífico)",
        ],
        "Asia": ["NPB (Japón)", "KBO (Corea del Sur)", "CPBL (Taiwán)"],
        "Internacional": [
            "Clásico Mundial de Béisbol (WBC)",
            "Serie del Caribe",
            "Premier 12",
            "Otra Liga de Béisbol",
        ],
    },
    "Baloncesto": {
        "Norteamérica": ["NBA", "WNBA", "NCAA Basketball", "NBA G-League"],
        "Europa / FIBA": [
            "EuroLeague",
            "EuroCup",
            "Liga ACB (España)",
            "Lega Basket Serie A (Italia)",
            "BBL (Alemania)",
            "BSN (Puerto Rico)",
        ],
        "Internacional": [
            "Copa Mundial FIBA",
            "Juegos Olímpicos",
            "EuroBasket",
            "Otra Liga de Baloncesto",
        ],
    },
    "Fútbol Americano": {
        "Norteamérica": [
            "NFL",
            "NFL Playoffs / Super Bowl",
            "NCAA College Football (FBS)",
            "UFL",
            "CFL",
        ],
        "Otro": ["Otra Liga de Fútbol Americano"],
    },
    "Tenis": {
        "ATP (Masculino)": [
            "ATP Tour",
            "ATP Masters 1000",
            "ATP 500",
            "ATP 250",
            "ATP Finals",
            "ATP Challenger",
        ],
        "WTA (Femenino)": [
            "WTA Tour",
            "WTA 1000",
            "WTA 500",
            "WTA 250",
            "WTA Finals",
            "WTA 125",
        ],
        "Grand Slam": ["Australian Open", "Roland Garros", "Wimbledon", "US Open"],
        "Equipos / ITF": [
            "Copa Davis",
            "Billie Jean King Cup",
            "Torneo ITF",
            "Otro Torneo de Tenis",
        ],
    },
    "Deportes de Combate": {
        "MMA": ["UFC", "Bellator / PFL", "ONE Championship", "Rizin"],
        "Boxeo": ["Título Mundial (WBC/WBA/IBF/WBO)", "Cartelera Profesional"],
    },
    "Hockey sobre Hielo": {
        "Norteamérica": ["NHL", "AHL"],
        "Europa / Internacional": ["KHL", "SHL", "IIHF World Championship"],
    },
    "Otro": {"General": ["Other"]},
}


def clasificar_deporte(sport_league_str: str) -> str:
    sl = str(sport_league_str).lower()
    if any(
        k in sl
        for k in [
            "uefa",
            "bundesliga",
            "premier",
            "la liga",
            "laliga",
            "serie a",
            "ligue 1",
            "liga mx",
            "mls",
            "saudi",
            "copa",
            "futbol",
            "fútbol",
            "libertadores",
            "sudamericana",
            "eredivisie",
            "primeira",
            "champions",
            "soccer",
        ]
    ):
        return "Fútbol ⚽"
    elif any(
        k in sl
        for k in [
            "mlb",
            "lmb",
            "lmp",
            "npb",
            "kbo",
            "cpbl",
            "béisbol",
            "beisbol",
            "baseball",
        ]
    ):
        return "Béisbol ⚾"
    elif any(
        k in sl
        for k in [
            "nba",
            "wnba",
            "baloncesto",
            "basketball",
            "euroleague",
            "fiba",
            "acb",
        ]
    ):
        return "Baloncesto 🏀"
    elif any(k in sl for k in ["nfl", "american", "ncaa football", "ufl", "cfl"]):
        return "Fútbol Americano 🏈"
    elif any(
        k in sl
        for k in [
            "tennis",
            "tenis",
            "atp",
            "wta",
            "open",
            "wimbledon",
            "garros",
            "davis",
        ]
    ):
        return "Tenis 🎾"
    elif any(k in sl for k in ["ufc", "box", "mma", "bellator", "rizin"]):
        return "Deportes de Combate 🥊"
    elif any(k in sl for k in ["nhl", "hockey", "ahl", "khl"]):
        return "Hockey 🏒"
    else:
        return "Otro / General 📌"


# ==========================================
# SIDEBAR DE CONFIGURACIÓN
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuración del Evento")

    match_name = st.text_input(
        "Partido / Evento", value="Milwaukee Brewers vs Chicago Cubs"
    )

    col_sport1, col_sport2 = st.columns(2)
    with col_sport1:
        selected_sport = st.selectbox("Deporte", list(SPORTS_CATALOG.keys()), index=0)
    with col_sport2:
        confederaciones = list(SPORTS_CATALOG[selected_sport].keys())
        selected_confed = st.selectbox(
            "Confederación / Región", confederaciones, index=0
        )

    ligas = SPORTS_CATALOG[selected_sport][selected_confed]
    selected_league = st.selectbox("Liga / Torneo", ligas, index=0)

    if "Otra" in selected_league or selected_league in [
        "Personalizada",
        "Other",
        "Otro",
    ]:
        custom_league = st.text_input(
            "Especificar Liga / Torneo", placeholder="Ej. Liga 1 de Perú"
        )
        sport_league = (
            custom_league.strip() if custom_league.strip() else selected_league
        )
    else:
        sport_league = selected_league

    bankroll = st.number_input("Banca Total ($)", value=0.0, step=500.0)

    user_instructions = st.text_area(
        "Instrucciones o contexto adicional (Opcional)",
        value="Priorizar cuotas y momios de la casa de apuestas Playdoit (o TeamMexico). Extraer de esa fuente las líneas de Moneyline, Handicap y Totals...",
        height=150,
    )

    btn_ejecutar = st.button(
        "🚀 Ejecutar Análisis", type="primary", use_container_width=True
    )

# Pestañas principales unificadas con las nuevas capacidades v10
(
    tab_analisis,
    tab_pnl,
    tab_cierre,
    tab_historico,
    tab_calibracion,
    tab_performance,
    tab_lessons,
) = st.tabs(
    [
        "🚀 Resultado del Análisis",
        "📈 Tablero PnL Diario",
        "🔒 Cierre Manual de Apuestas",
        "📋 Historial de Picks",
        "🎯 Calibración del Modelo",
        "🧠 Rule Performance",
        "📚 Lessons Learned",
    ]
)

# ==========================================
# PESTAÑA 1: RESULTADO DEL ANÁLISIS (PipelineFacade estático)
# ==========================================
with tab_analisis:
    if btn_ejecutar:
        with st.spinner("Ejecutando pipeline cuantitativo institucional..."):
            max_intentos = 3
            exito = False

            for intento in range(1, max_intentos + 1):
                try:
                    # Llamada estática limpia a PipelineFacade
                    PipelineFacade.ejecutar_analisis(
                        match_name=match_name,
                        sport_league=sport_league,
                        bankroll=bankroll,
                        user_instructions=user_instructions,
                    )
                    st.success("Análisis completado exitosamente.")
                    exito = True
                    break
                except Exception as e:
                    error_str = str(e)
                    if (
                        "503" in error_str
                        or "UNAVAILABLE" in error_str
                        or "overloaded" in error_str.lower()
                    ):
                        st.warning(
                            f"⚠️ Alta demanda en servidores (Intento {intento}/{max_intentos}). Reintentando en 4 segundos..."
                        )
                        time.sleep(4)
                    else:
                        st.error(f"Ocurrió un error al procesar el análisis: {e}")
                        break

            if (
                not exito
                and "error_str" in locals()
                and ("503" in error_str or "UNAVAILABLE" in error_str)
            ):
                st.error("❌ Servidores ocupados. Intenta de nuevo en unos momentos.")

    if os.path.exists(REPORTS_DIR):
        archivos = [f for f in os.listdir(REPORTS_DIR) if f.endswith(".txt")]
        archivos.sort(
            key=lambda x: os.path.getmtime(os.path.join(REPORTS_DIR, x)), reverse=True
        )

        if archivos:
            ultimo_reporte = os.path.join(REPORTS_DIR, archivos[0])
            with open(ultimo_reporte, "r", encoding="utf-8") as f:
                contenido = f.read()

            json_matches = re.findall(
                r"```json\s*(\{.*?\})\s*```", contenido, re.DOTALL
            )

            justificacion_cualitativa = (
                "No se encontró el desglose detallado en el reporte."
            )
            match_quant_sec = re.search(
                r"2\. FASE DE EVALUACIÓN MULTIMERCADO Y VALOR ESPERADO \(QUANT ANALYST\)\s*--------------------------------------------------------------------------------\s*(.*?)\s*--------------------------------------------------------------------------------",
                contenido,
                re.DOTALL,
            )
            if match_quant_sec:
                texto_quant = match_quant_sec.group(1)
                texto_limpio = re.split(
                    r"(?i)(?:\d+\.\s*Resumen\s*JSON|\d+\.\s*JSON\s*Summary|```json)",
                    texto_quant,
                )[0].strip()
                if texto_limpio:
                    justificacion_cualitativa = texto_limpio

            if len(json_matches) >= 2:
                try:
                    quant_data = json.loads(json_matches[-2])
                    risk_data = json.loads(json_matches[-1])

                    verdict = (
                        str(risk_data.get("final_verdict", "REJECTED")).strip().upper()
                    )
                    stake_units = float(risk_data.get("recommended_stake_units", 0.0))

                    if "recommended_stake_amount" in risk_data:
                        monto_exacto = float(
                            risk_data.get("recommended_stake_amount", 0.0)
                        )
                    else:
                        monto_exacto = (stake_units / 100.0) * bankroll

                    pct_real = (monto_exacto / bankroll) * 100 if bankroll > 0 else 0.0

                    st.divider()

                    if verdict == "APPROVED":
                        st.success(f"✅ **APUESTA APROBADA (VEREDICTO: {verdict})**")
                    else:
                        st.error(f"❌ **APUESTA RECHAZADA (VEREDICTO: {verdict})**")

                    c1, c2, c3, c4 = st.columns([2.2, 1.0, 1.0, 1.5])
                    c1.metric("🎯 Selección", quant_data.get("selection", "N/A"))
                    c2.metric(
                        "📈 Cuota",
                        f"{float(quant_data.get('bookmaker_odds', 0.0)):.2f}",
                    )
                    c3.metric(
                        "💡 Value (EV)",
                        f"{float(quant_data.get('expected_value_percentage', 0.0)):.2f}%",
                    )
                    c4.metric("💵 Apostar", f"${monto_exacto:,.2f} ({pct_real:.1f}%)")

                    st.markdown("---")
                    st.subheader(
                        "📋 Análisis Detallado del Pick y Evaluación de Riesgo"
                    )

                    mercado_str = quant_data.get("market_type", "N/A")
                    p_true_str = f"{float(quant_data.get('estimated_true_probability', 0.0)) * 100:.1f}%"
                    riesgo_summary = risk_data.get("reasoning_summary", "Sin detalles")

                    st.markdown(f"**Mercado Evaluado:** {mercado_str}")
                    st.markdown(
                        f"**Probabilidad Estimada ($P_{{true}}$):** {p_true_str}"
                    )
                    st.markdown(f"**Evaluación del Risk Manager:** {riesgo_summary}")

                    st.markdown("#### 🧠 Justificación Cuantitativa y Táctica")
                    st.markdown(justificacion_cualitativa)
                    st.caption(f"📁 Reporte procesado desde: `{archivos[0]}`")

                except (json.JSONDecodeError, ValueError) as err:
                    st.warning(
                        f"No se pudieron interpretar las métricas del reporte: {err}"
                    )

# ==========================================
# PESTAÑA 2: TABLERO PnL DIARIO
# ==========================================
with tab_pnl:
    st.header("📈 Rendimiento Diario de Banca (PnL)")

    col_banca, col_filtro = st.columns([1, 1])

    with col_banca:
        banca_inicial_base = st.number_input(
            "Banca Inicial de Referencia ($)",
            value=10000.0,
            step=500.0,
            key="banca_pnl_input",
        )

    with col_filtro:
        hoy = datetime.now().date()
        hace_14_dias = hoy - timedelta(days=14)

        rango_fechas = st.date_input(
            "📅 Selecciona el rango de fechas a consultar",
            value=(hace_14_dias, hoy),
            max_value=hoy,
            key="pnl_date_range",
        )

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)

        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            fecha_inicio, fecha_fin = rango_fechas
            where_clause = (
                f"WHERE DATE(created_at) BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"
            )
        else:
            where_clause = ""
            fecha_inicio, fecha_fin = "Inicio", "Fin"

        query = f"""
            SELECT 
                DATE(created_at) as fecha,
                COUNT(*) as total_apuestas,
                SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as ganadas,
                SUM(CASE WHEN actual_result = 'LOSS' THEN 1 ELSE 0 END) as perdidas,
                SUM(CASE WHEN actual_result = 'PENDING' THEN 1 ELSE 0 END) as pendientes,
                SUM(COALESCE(profit_units, 0.0)) as profit_unidades,
                SUM(
                    CASE 
                        WHEN actual_result = 'WIN' THEN recommended_stake_amount * (bookmaker_odds - 1.0)
                        WHEN actual_result = 'LOSS' THEN -recommended_stake_amount
                        ELSE 0.0
                    END
                ) as profit_dinero
            FROM historical_picks
            {where_clause}
            GROUP BY DATE(created_at)
            ORDER BY fecha DESC
        """

        query_sport = f"""
            SELECT 
                sport_league,
                COUNT(*) as total_apuestas,
                SUM(CASE WHEN actual_result = 'WIN' THEN 1 ELSE 0 END) as ganadas,
                SUM(CASE WHEN actual_result = 'LOSS' THEN 1 ELSE 0 END) as perdidas,
                SUM(CASE WHEN actual_result = 'PENDING' THEN 1 ELSE 0 END) as pendientes,
                SUM(COALESCE(profit_units, 0.0)) as profit_unidades,
                SUM(
                    CASE 
                        WHEN actual_result = 'WIN' THEN recommended_stake_amount * (bookmaker_odds - 1.0)
                        WHEN actual_result = 'LOSS' THEN -recommended_stake_amount
                        ELSE 0.0
                    END
                ) as profit_dinero
            FROM historical_picks
            {where_clause}
            GROUP BY sport_league
            ORDER BY total_apuestas DESC, ganadas DESC
        """

        try:
            df_pnl = pd.read_sql_query(query, conn)
            df_sport_raw = pd.read_sql_query(query_sport, conn)
        except Exception as err:
            st.error(f"Error al consultar la base de datos: {err}")
            df_pnl = pd.DataFrame()
            df_sport_raw = pd.DataFrame()

        conn.close()

        if not df_pnl.empty:
            df_pnl_asc = df_pnl.sort_values("fecha").copy()
            df_pnl_asc["Profit Acumulado ($)"] = df_pnl_asc["profit_dinero"].cumsum()
            df_pnl_asc["Banca Cierre ($)"] = (
                banca_inicial_base + df_pnl_asc["Profit Acumulado ($)"]
            )

            df_display = df_pnl_asc.sort_values("fecha", ascending=False)

            total_profit_usd = df_pnl["profit_dinero"].sum()
            banca_actual = banca_inicial_base + total_profit_usd
            roi_periodo = (
                (total_profit_usd / banca_inicial_base) * 100
                if banca_inicial_base > 0
                else 0.0
            )

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("💰 Banca Inicial", f"${banca_inicial_base:,.2f}")
            m2.metric("🏦 Banca Final del Período", f"${banca_actual:,.2f}")
            m3.metric("📊 PnL del Período", f"${total_profit_usd:+,.2f}")
            m4.metric("📈 ROI en Período", f"{roi_periodo:+.2f}%")

            st.markdown("---")
            st.subheader(f"📉 Evolución de Banca ({fecha_inicio} ➔ {fecha_fin})")
            st.line_chart(df_pnl_asc.set_index("fecha")["Banca Cierre ($)"])

            st.markdown("---")
            st.subheader("🗓️ Desglose Diario")

            df_tabla = df_display[
                [
                    "fecha",
                    "total_apuestas",
                    "ganadas",
                    "perdidas",
                    "pendientes",
                    "profit_unidades",
                    "profit_dinero",
                    "Banca Cierre ($)",
                ]
            ].copy()

            df_tabla.columns = [
                "Fecha",
                "Apuestas",
                "Ganadas (W)",
                "Perdidas (L)",
                "Pendientes",
                "Profit (Unidades)",
                "PnL Día ($)",
                "Banca Cierre ($)",
            ]

            st.dataframe(
                df_tabla.style.format(
                    {
                        "Profit (Unidades)": "{:+.2f}u",
                        "PnL Día ($)": "${:+,.2f}",
                        "Banca Cierre ($)": "${:,.2f}",
                    }
                ),
                use_container_width=True,
            )

            st.markdown("---")
            st.subheader("📊 Rendimiento y Relación por Deporte / Liga")

            if not df_sport_raw.empty:
                df_sport_raw["deporte_macro"] = df_sport_raw["sport_league"].apply(
                    clasificar_deporte
                )

                vista_seleccionada = st.radio(
                    "Agrupar por:",
                    ["🏅 Deporte", "🏆 Liga / Competición Específica"],
                    horizontal=True,
                    key="radio_vista_deporte",
                )

                if vista_seleccionada == "🏅 Deporte":
                    df_agrupado = (
                        df_sport_raw.groupby("deporte_macro")
                        .agg(
                            {
                                "total_apuestas": "sum",
                                "ganadas": "sum",
                                "perdidas": "sum",
                                "pendientes": "sum",
                                "profit_unidades": "sum",
                                "profit_dinero": "sum",
                            }
                        )
                        .reset_index()
                    )
                    df_agrupado.rename(
                        columns={"deporte_macro": "Categoría"}, inplace=True
                    )
                else:
                    df_agrupado = df_sport_raw.copy()
                    df_agrupado.rename(
                        columns={"sport_league": "Categoría"}, inplace=True
                    )

                df_agrupado["total_cerradas"] = (
                    df_agrupado["ganadas"] + df_agrupado["perdidas"]
                )
                df_agrupado["Win Rate (%)"] = df_agrupado.apply(
                    lambda r: (
                        (r["ganadas"] / r["total_cerradas"] * 100)
                        if r["total_cerradas"] > 0
                        else 0.0
                    ),
                    axis=1,
                )

                df_agrupado = df_agrupado.sort_values(
                    by=["total_apuestas", "ganadas"], ascending=[False, False]
                )

                st.markdown("##### 📈 Comparativa de Ganadas (W) vs Perdidas (L)")
                df_chart_sport = df_agrupado.set_index("Categoría")[
                    ["ganadas", "perdidas"]
                ].copy()
                df_chart_sport.columns = ["Ganadas (W)", "Perdidas (L)"]
                st.bar_chart(df_chart_sport)

                st.markdown("##### 📋 Desglose Cuantitativo por Deporte / Liga")
                df_tabla_sport = df_agrupado[
                    [
                        "Categoría",
                        "total_apuestas",
                        "ganadas",
                        "perdidas",
                        "pendientes",
                        "Win Rate (%)",
                        "profit_unidades",
                        "profit_dinero",
                    ]
                ].copy()

                df_tabla_sport.columns = [
                    "Deporte / Liga",
                    "Total Apuestas",
                    "Ganadas (W)",
                    "Perdidas (L)",
                    "Pendientes",
                    "Win Rate (%)",
                    "Profit (Unidades)",
                    "PnL ($)",
                ]

                st.dataframe(
                    df_tabla_sport.style.format(
                        {
                            "Win Rate (%)": "{:.1f}%",
                            "Profit (Unidades)": "{:+.2f}u",
                            "PnL ($)": "${:+,.2f}",
                        }
                    ),
                    use_container_width=True,
                )
            else:
                st.info("No hay datos de deportes/ligas para el período seleccionado.")
        else:
            st.info(
                f"No hay apuestas registradas en el rango de fechas seleccionado ({fecha_inicio} a {fecha_fin})."
            )
    else:
        st.info("La base de datos aún no ha sido creada.")

# ==========================================
# PESTAÑA 3: CIERRE MANUAL (SettlementFacade)
# ==========================================
with tab_cierre:
    st.header("🔒 Cierre Manual de Apuestas")
    st.caption(
        "Registra el resultado final de un pick y ejecuta automáticamente el ciclo bayesiano, de riesgo y post-mortem."
    )

    if not os.path.exists(DB_PATH):
        st.info("La base de datos aún no ha sido creada.")
    else:
        conn = sqlite3.connect(DB_PATH)
        df_pendientes = pd.read_sql_query(
            """
            SELECT id, match_name, sport_league, selection, bookmaker_odds, recommended_stake_amount, created_at
            FROM historical_picks
            WHERE actual_result = "PENDING"
            ORDER BY created_at DESC
        """,
            conn,
        )
        conn.close()

        if df_pendientes.empty:
            st.info("No hay apuestas pendientes de resolver.")
        else:
            opciones = {
                f"#{r.id} — {r.match_name} ({r.sport_league}) | {r.selection} @ {r.bookmaker_odds}": r.id
                for r in df_pendientes.itertuples()
            }
            etiqueta_seleccionada = st.selectbox(
                "Selecciona la apuesta pendiente a cerrar", list(opciones.keys())
            )
            pick_id_seleccionado = opciones[etiqueta_seleccionada]
            match_name_seleccionado = df_pendientes.loc[
                df_pendientes["id"] == pick_id_seleccionado, "match_name"
            ].iloc[0]

            with st.form("form_cierre_apuesta"):
                col_partido, col_resultado = st.columns([1.5, 2])
                with col_partido:
                    st.caption("Partido")
                    st.code(match_name_seleccionado, language=None)
                with col_resultado:
                    resultado_final = st.radio(
                        "Resultado final", ["WIN", "LOSS", "PUSH"], horizontal=True
                    )
                marcador_real = st.text_input(
                    "Marcador / detalle real (opcional)", placeholder="Ej. 3-4"
                )
                usar_profit_manual = st.checkbox(
                    "Especificar ganancia/pérdida en unidades manualmente"
                )
                profit_manual = st.number_input(
                    "Unidades (profit_units)",
                    value=0.0,
                    step=0.1,
                    disabled=not usar_profit_manual,
                )

                enviar = st.form_submit_button(
                    "✅ Cerrar Apuesta y Ejecutar Auditoría Master",
                    type="primary",
                    use_container_width=True,
                )

            if enviar:
                with st.spinner(
                    "Actualizando SQLite, calculando feedback bayesiano y ejecutando auditoría Post-Mortem..."
                ):
                    try:
                        resultado_cierre = SettlementFacade.close_pick(
                            pick_id=int(pick_id_seleccionado),
                            result=resultado_final,
                            profit_units=profit_manual if usar_profit_manual else None,
                            run_postmortem=True,
                            marcador_real=marcador_real,
                        )
                        st.success(
                            f"Pick #{pick_id_seleccionado} cerrado con éxito como {resultado_cierre['actual_result']} (${resultado_cierre['profit_units']} MXN)."
                        )
                        st.subheader("📌 Informe de Hallazgo Post-Mortem")
                        st.json(resultado_cierre["postmortem"])
                    except ValueError as err:
                        st.error(f"No se pudo cerrar la apuesta: {err}")
                    except Exception as err:
                        st.error(
                            f"Ocurrió un error inesperado al ejecutar el cierre: {err}"
                        )

# ==========================================
# PESTAÑA 4: HISTORIAL DE PICKS
# ==========================================
with tab_historico:
    st.header("Histórico de Apuestas Guardadas")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        query = "SELECT * FROM historical_picks ORDER BY id DESC"
        df = pd.read_sql_query(query, conn)
        conn.close()

        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No hay apuestas aprobadas en el historial.")
    else:
        st.info("La base de datos aún no ha sido creada.")

# ==========================================
# PESTAÑA 5: CALIBRACIÓN DEL MODELO
# ==========================================
with tab_calibracion:
    st.header("🎯 Diagnóstico y Calibración Cuantitativa")
    st.caption(
        "Evaluación Post-Mortem del sesgo y la precisión de las probabilidades estimadas (P_true)."
    )

    if os.path.exists(DB_PATH):
        df_eval = obtener_datos_evaluados(DB_PATH)

        if not df_eval.empty:
            metrics = calcular_brier_score(df_eval)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(
                "📊 Brier Score (BS)",
                f"{metrics['brier_score']:.4f}",
                help="Cercano a 0 es mejor. 0.25 es equivalente al azar.",
            )
            c2.metric(
                "📈 Brier Skill Score (BSS)",
                f"{metrics['brier_skill_score'] * 100:.1f}%",
                help="% de ventaja sobre el azar.",
            )
            c3.metric(
                "🎯 Prob. Promedio Estimada", f"{metrics['p_true_promedio']:.1f}%"
            )
            c4.metric("🏆 Tasa Real de Acierto", f"{metrics['win_rate_real']:.1f}%")

            st.markdown("---")
            st.subheader("📉 Diagrama de Confiabilidad (Reliability Curve)")

            df_bins = obtener_tabla_calibracion(df_eval, bins=5)

            if not df_bins.empty:
                chart_data = df_bins.dropna(subset=["bin"]).copy()
                chart_data["Rango de Probabilidad"] = chart_data["bin"].astype(str)
                df_plot = chart_data.set_index("Rango de Probabilidad")[
                    ["p_estimada_media", "tasa_acierto_real"]
                ]
                df_plot.columns = [
                    "Prob. Estimada Promedio (%)",
                    "Tasa Acierto Real (%)",
                ]
                st.bar_chart(df_plot)
        else:
            st.info(
                "Se requieren apuestas cerradas para calcular las métricas de calibración."
            )
    else:
        st.info("La base de datos aún no ha sido creada.")

# ==========================================
# PESTAÑA 6: RULE PERFORMANCE
# ==========================================
with tab_performance:
    st.header("🧠 Monitoreo de Estatus y Rendimiento por Regla")
    st.caption(
        "Salud bayesiana, ROI porcentual y control autónomo de activación (ACTIVE / MONITOR / DISABLED) por cada regla analítica."
    )

    if os.path.exists(PERFORMANCE_FILE):
        try:
            with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
                perf_json = json.load(f)

            perf_dict = perf_json.get("PERFORMANCE", {})
            if perf_dict:
                rows = []
                for rule_name, metrics in perf_dict.items():
                    rows.append(
                        {
                            "Rule": rule_name,
                            "Status": metrics.get("status", "ACTIVE"),
                            "ROI (%)": metrics.get("roi_pct", 0.0),
                            "Total Bets": metrics.get("total_bets", 0),
                            "Alpha (Win)": round(metrics.get("alpha_success", 0), 1),
                            "Beta (Loss)": round(metrics.get("beta_failures", 0), 1),
                            "Total Profit ($)": metrics.get("total_profit", 0.0),
                        }
                    )

                df_perf = pd.DataFrame(rows)
                st.dataframe(
                    df_perf.style.format(
                        {"ROI (%)": "{:+.2f}%", "Total Profit ($)": "${:+,.2f}"}
                    ),
                    use_container_width=True,
                )
            else:
                st.info(
                    "No hay registros de rendimiento de reglas en `rule_performance.json`."
                )
        except Exception as e:
            st.error(f"Error al leer el archivo de rendimiento: {e}")
    else:
        st.info(
            "El archivo `rule_performance.json` aún no ha sido generado. Se inicializará tras la primera liquidación de apuestas."
        )

# ==========================================
# PESTAÑA 7: LESSONS LEARNED (Ruta Centralizada)
# ==========================================
with tab_lessons:
    st.header("📚 Base de Conocimiento Post-Mortem (Lessons Learned)")
    st.caption(
        "Registro acumulado de hallazgos sabermétricos, causas raíz y propuestas de reglas candidatas estructuradas."
    )

    if os.path.exists(LESSONS_MASTER_PATH):
        try:
            with open(LESSONS_MASTER_PATH, "r", encoding="utf-8") as f:
                lessons_data = json.load(f)

            if isinstance(lessons_data, list) and lessons_data:
                df_lessons = pd.DataFrame(lessons_data)

                status_filter = st.selectbox(
                    "Filtrar por Review Status",
                    ["TODOS", "PENDING", "APPROVED", "REJECTED"],
                )
                if status_filter != "TODOS":
                    df_lessons = df_lessons[
                        df_lessons["review_status"] == status_filter
                    ]

                st.dataframe(df_lessons, use_container_width=True)
            else:
                st.info("La base de conocimiento `lessons_master.json` está vacía.")
        except Exception as e:
            st.error(f"Error al leer la base de conocimiento: {e}")
    else:
        st.info(
            "El archivo `lessons_master.json` aún no ha sido creado. Se poblará automáticamente conforme se ejecuten auditorías post-mortem."
        )
