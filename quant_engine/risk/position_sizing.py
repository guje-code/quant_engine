from quant_engine.config.settings import (
    CONFIDENCE_CAP_FACTOR,
    KELLY_FRACTION,
    MAX_STAKE_PCT,
    SEVERITY_PENALTIES,
)


def calcular_stake_kelly(
    prob_est: float, odds: float, confidence_score: int, triggered_rules: list
) -> dict:
    if odds <= 1.0 or prob_est <= 0.0 or prob_est >= 1.0:
        return {
            "stake_final_pct": 0.0,
            "kelly_full_pct": 0.0,
            "confidence_factor": 0.0,
            "severity_penalty": 1.0,
            "status": "INVALID",
        }

    b = odds - 1.0
    f_star = (prob_est * b - (1.0 - prob_est)) / b
    if f_star <= 0:
        return {
            "stake_final_pct": 0.0,
            "kelly_full_pct": 0.0,
            "confidence_factor": 0.0,
            "severity_penalty": 1.0,
            "status": "NO_VALUE",
        }

    # Métricas de auditoría intermedias
    kelly_full_pct = round(f_star * 100.0, 4)
    conf_factor = round((confidence_score / 100.0) * CONFIDENCE_CAP_FACTOR, 4)

    sev_penalty = 1.0
    for r in triggered_rules:
        sev_key = r.get("severity", "LOW").upper()
        sev_penalty *= SEVERITY_PENALTIES.get(sev_key, 1.0)
    sev_penalty = round(sev_penalty, 4)

    # Cálculo preliminar de stake
    raw_stake = kelly_full_pct * conf_factor * sev_penalty * KELLY_FRACTION

    # Protección defensiva: asegurar que el stake nunca sea negativo ante valores atípicos
    raw_stake = max(0.0, raw_stake)

    # Aplicación del tope máximo institucional (Max Stake Cap)
    is_capped = raw_stake > MAX_STAKE_PCT
    stake_final = min(raw_stake, MAX_STAKE_PCT)

    status = "CAPPED" if is_capped else "APPROVED"

    return {
        "stake_final_pct": round(stake_final, 2),
        "kelly_full_pct": kelly_full_pct,
        "confidence_factor": conf_factor,
        "severity_penalty": sev_penalty,
        "status": status,
    }
