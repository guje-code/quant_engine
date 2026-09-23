import logging
import re
import time

from crewai_tools import SerperDevTool

search_tool = SerperDevTool()


def buscar_marcador_web(match_name: str) -> dict:
    """
    Fallback web de alta precisión con telemetría, validación de contexto
    (sin falsos positivos de fútbol) y parsing robusto de sets y marcadores.
    """
    t_start = time.perf_counter()
    query = f"resultado final marcador {match_name} final score"

    logging.info(f"[WEB FALLBACK] Lanzando query de búsqueda: '{query}'")

    try:
        raw_res = search_tool.run(search_query=query)

        equipos = re.split(
            r"\s+vs\.?\s+|\s+@\s+|\s+-\s+", match_name, flags=re.IGNORECASE
        )
        if len(equipos) < 2:
            duration_ms = (time.perf_counter() - t_start) * 1000.0
            logging.warning(
                f"[WEB FALLBACK TELEMETRY] Latencia: {duration_ms:.1f}ms | Parsing Success: False | Motivo: Formato de match_name inválido"
            )
            return {
                "status": "PENDING",
                "reason": "Formato de nombre de evento no válido para split",
            }

        eq_a = equipos[0].strip()
        eq_b = equipos[1].strip()

        # Detección estricta de tenis (eliminando términos ambiguos como 'champions')
        is_tennis_context = any(
            k in match_name.lower()
            for k in [
                "atp",
                "wta",
                "open",
                "tennis",
                "tenis",
                "wimbledon",
                "garros",
                "us open",
                "australian open",
            ]
        )

        if is_tennis_context:
            # RegEx limpia sin corchetes escapados erróneamente para capturar sets tipo 2-1, 2:0, 0-2
            sets_match = re.search(r"\b([0-2])\s*[-–:]\s*([0-2])\b", raw_res)
            if sets_match:
                score_a, score_b = int(sets_match.group(1)), int(sets_match.group(2))
                duration_ms = (time.perf_counter() - t_start) * 1000.0
                logging.info(
                    f"[WEB FALLBACK TELEMETRY] Latencia: {duration_ms:.1f}ms | Parsing Success: True | Fallback Hit: True | Tipo: Tenis (Sets)"
                )
                return {"status": "FINAL", "scores": {eq_a: score_a, eq_b: score_b}}

        # Búsqueda segura de marcadores estándar con filtro anti-años y anti-estadísticas infladas (< 250)
        digits = re.findall(r"\b(\d{1,3})\s*[-–:]\s*(\d{1,3})\b", raw_res)
        if digits:
            for d_a, d_b in digits:
                sa, sb = int(d_a), int(d_b)
                if sa < 250 and sb < 250:
                    duration_ms = (time.perf_counter() - t_start) * 1000.0
                    logging.info(
                        f"[WEB FALLBACK TELEMETRY] Latencia: {duration_ms:.1f}ms | Parsing Success: True | Fallback Hit: True | Tipo: Estándar"
                    )
                    return {"status": "FINAL", "scores": {eq_a: sa, eq_b: sb}}

        duration_ms = (time.perf_counter() - t_start) * 1000.0
        logging.info(
            f"[WEB FALLBACK TELEMETRY] Latencia: {duration_ms:.1f}ms | Parsing Success: False | Fallback Hit: False"
        )

    except Exception as e:
        duration_ms = (time.perf_counter() - t_start) * 1000.0
        logging.warning(
            f"[WEB FALLBACK TELEMETRY] Latencia: {duration_ms:.1f}ms | Error crítico en web search: {e}"
        )

    return {
        "status": "PENDING",
        "reason": "No se pudo extraer un marcador confiable en la web",
    }
