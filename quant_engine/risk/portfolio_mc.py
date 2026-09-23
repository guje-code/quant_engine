import json
import math
import sqlite3

import numpy as np


def calcular_ledoit_wolf_optimal_shrinkage(
    data_matrix: np.ndarray, target: np.ndarray
) -> tuple[np.ndarray, float]:
    n, t = data_matrix.shape
    if t <= 1:
        return target, 1.0

    sample_cov = np.cov(data_matrix)
    mu = np.trace(sample_cov) / n
    spec_dist = np.sum((sample_cov - mu * np.eye(n)) ** 2)
    delta = float(
        np.clip(
            spec_dist / (spec_dist + np.sum((sample_cov - target) ** 2) + 1e-8),
            0.05,
            0.95,
        )
    )
    optimal_sigma = (1.0 - delta) * sample_cov + delta * target
    return optimal_sigma, delta


def construir_matriz_covarianza_citadel(
    active_rules_in_portfolio: list, db_path: str
) -> dict:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT profit_units, triggered_rules_json FROM historical_picks WHERE actual_result != 'PENDING' ORDER BY created_at DESC LIMIT 500"
        )
        rows = cursor.fetchall()
        conn.close()
    except (sqlite3.Error, json.JSONDecodeError):
        rows = []

    rule_universe = set(active_rules_in_portfolio)
    for _, rules_json in rows:
        try:
            for r in json.loads(rules_json):
                rule_universe.add(r)
        except Exception:
            pass

    rules_list = list(rule_universe)
    n = len(rules_list)
    if n == 0:
        return {"rules": [], "sigma": np.array([[]]), "delta": 1.0, "fallback": True}

    target = np.eye(n) * 0.03

    if len(rows) >= 20:
        rule_returns = {r: [] for r in rules_list}
        for profit, rules_json in rows:
            try:
                r_list = json.loads(rules_json)
                for r in rules_list:
                    rule_returns[r].append(float(profit) if r in r_list else 0.0)
            except Exception:
                pass

        data_matrix = np.array([rule_returns[r] for r in rules_list])
        sigma, delta = calcular_ledoit_wolf_optimal_shrinkage(data_matrix, target)
    else:
        sigma = target
        delta = 1.0

    return {"rules": rules_list, "sigma": sigma, "delta": delta, "fallback": False}


def simular_portfolio_var_cvar_student_t(
    candidate_prob: float,
    candidate_odds: float,
    candidate_stake_pct: float,
    bankroll: float,
    candidate_triggered_rules: list,
    db_path: str,
    iterations: int = 25000,
) -> dict:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT recommended_stake_units, estimated_true_probability, bookmaker_odds, triggered_rules_json FROM historical_picks WHERE actual_result = 'PENDING'"
        )
        pending_picks = cursor.fetchall()
        conn.close()
    except Exception:
        pending_picks = []

    active_portfolio = [
        {
            "stake_pct": candidate_stake_pct,
            "prob": candidate_prob,
            "odds": candidate_odds,
            "rules": candidate_triggered_rules,
        }
    ]
    all_portfolio_rules = set(candidate_triggered_rules)

    for stake_pct, prob, odds, rules_json in pending_picks:
        try:
            r_list = json.loads(rules_json)
        except Exception:
            r_list = []
        active_portfolio.append(
            {
                "stake_pct": float(stake_pct),
                "prob": float(prob),
                "odds": float(odds),
                "rules": r_list,
            }
        )
        for r in r_list:
            all_portfolio_rules.add(r)

    cov_data = construir_matriz_covarianza_citadel(list(all_portfolio_rules), db_path)
    rules_index = {r: idx for idx, r in enumerate(cov_data["rules"])}
    sigma = cov_data["sigma"]

    # Corrección del bug de NumPy: usando chisquare en lugar de chisdf
    student_t_df = 4.0
    chi2_samples = np.random.chisquare(df=student_t_df, size=iterations)
    t_scaling = np.sqrt(student_t_df / chi2_samples)
    normal_shocks = np.random.normal(0.0, 1.0, iterations)
    student_t_shocks = normal_shocks * t_scaling

    pnl_matriz = np.zeros(iterations)

    for position in active_portfolio:
        monto = (position["stake_pct"] / 100.0) * bankroll
        pos_vol = 0.05
        pos_rules = position["rules"]
        if pos_rules and rules_index and not cov_data["fallback"]:
            valid_indices = [rules_index[r] for r in pos_rules if r in rules_index]
            if valid_indices:
                pos_vol = math.sqrt(
                    max(0.001, np.mean([sigma[idx, idx] for idx in valid_indices]))
                )

        adjusted_probs = np.clip(
            position["prob"] + student_t_shocks * pos_vol, 0.01, 0.99
        )
        wins = np.random.rand(iterations) < adjusted_probs

        retornos_pos = np.where(wins, monto * (position["odds"] - 1.0), -monto)
        pnl_matriz += retornos_pos

    pnl_matriz.sort()

    var_95_idx = int(iterations * 0.05)
    var_95_amount = abs(pnl_matriz[var_95_idx])
    var_95_pct = (var_95_amount / bankroll) * 100.0

    tail_losses = [-r for r in pnl_matriz[:var_95_idx] if r < 0]
    cvar_95_amount = (
        sum(tail_losses) / len(tail_losses) if tail_losses else var_95_amount
    )
    cvar_95_pct = (cvar_95_amount / bankroll) * 100.0

    is_safe = (var_95_pct <= 5.0) and (cvar_95_pct <= 7.5)

    return {
        "var_95_amount": round(var_95_amount, 2),
        "var_95_pct": round(var_95_pct, 2),
        "cvar_95_amount": round(cvar_95_amount, 2),
        "cvar_95_pct": round(cvar_95_pct, 2),
        "safe": is_safe,
        "active_positions_count": len(active_portfolio),
        "sigma_snapshot": {
            "fallback": cov_data["fallback"],
            "optimal_delta": round(cov_data["delta"], 4),
        },
    }
