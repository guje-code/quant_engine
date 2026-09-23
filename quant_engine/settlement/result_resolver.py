import re

from quant_engine.settlement.espn_provider import consultar_espn
from quant_engine.settlement.web_fallback_provider import buscar_marcador_web


class ResultResolver:
    @staticmethod
    def obtener_resultado_evento(
        match_name: str, sport_league: str, created_at: str
    ) -> dict:
        # 1. Intento principal con ESPN API
        resultado = consultar_espn(match_name, sport_league, created_at)
        if resultado.get("status") == "FINAL":
            return resultado

        # 2. Intento de respaldo con Web Search
        print(
            f" 🔍 API ESPN sin respuesta para '{match_name}'. Ejecutando Fallback de Búsqueda Web..."
        )
        return buscar_marcador_web(match_name)

    @staticmethod
    def evaluar_pick(selection: str, market_type: str, scores: dict) -> str:
        if not scores or len(scores) < 2:
            return "PENDING"

        sel_lower = selection.lower()
        mkt_lower = market_type.lower()

        selected_team = None
        rival_team = None

        for team in scores.keys():
            clean_team = re.sub(
                r"\b(fc|cd|sc|club|deportivo|real)\b", "", team.lower()
            ).strip()
            partes_nombre = clean_team.split()
            if (
                clean_team in sel_lower
                or team.lower() in sel_lower
                or any(p in sel_lower for p in partes_nombre if len(p) > 3)
            ):
                selected_team = team
                break

        if selected_team:
            for t in scores.keys():
                if t != selected_team:
                    rival_team = t
                    break

        # 1. Hándicap / Spread
        match_hcap = re.search(r"([+-]?\d+\.?\d*)", sel_lower)
        is_handicap = (
            "handicap" in mkt_lower
            or "spread" in mkt_lower
            or "run line" in mkt_lower
            or ("asian" in mkt_lower and match_hcap)
        )

        if is_handicap and selected_team and rival_team and match_hcap:
            handicap_val = float(match_hcap.group(1))
            score_sel = scores[selected_team]
            score_riv = scores[rival_team]
            score_ajustado = score_sel + handicap_val

            if score_ajustado > score_riv:
                return "WIN"
            elif score_ajustado < score_riv:
                return "LOSS"
            else:
                return "PUSH"

        # 2. Totals (Over / Under)
        if "total" in mkt_lower or "over" in sel_lower or "under" in sel_lower:
            total_puntos = sum(scores.values())
            match_line = re.search(r"(over|under)\s*([+-]?\d+\.?\d*)", sel_lower)
            if match_line:
                linea = float(match_line.group(2))
                return (
                    "WIN"
                    if total_puntos > linea
                    else ("LOSS" if total_puntos < linea else "PUSH")
                )

        # 3. Moneyline / Ganador Directo
        if selected_team and rival_team:
            score_sel = scores[selected_team]
            score_riv = scores[rival_team]
            return "WIN" if score_sel > score_riv else "LOSS"

        return "PENDING"
