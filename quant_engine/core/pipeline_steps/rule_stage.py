import time

from quant_engine.core.rule_engine import ejecutar_rule_engine_modular


def ejecutar_etapa_reglas(
    scout_json: dict, sport_league: str, line_movement_pct: float, steam_detected: bool
) -> dict:
    t_start = time.time()
    rule_engine_res = ejecutar_rule_engine_modular(
        scout_json, sport_league, line_movement_pct, steam_detected
    )
    t_duration = (time.time() - t_start) * 1000

    rule_engine_res["duration_ms"] = t_duration
    return rule_engine_res
