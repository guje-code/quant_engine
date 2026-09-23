from quant_engine.config.settings import (
    CORRELATIONS_FILE,
    PERFORMANCE_FILE,
    PRIORITY_MULTIPLIERS,
    REGISTRY_FILE,
)
from quant_engine.core.parser import QuantEngineCore
from quant_engine.risk.cluster_manager import ClusterManager
from quant_engine.storage.json_repository import JSONRepository


def ejecutar_rule_engine_modular(
    scout_data: dict, sport_league: str, line_movement_pct: float, steam_detected: bool
) -> dict:
    registry = JSONRepository.cargar_json(REGISTRY_FILE)
    performance = JSONRepository.cargar_json(PERFORMANCE_FILE).get("PERFORMANCE", {})
    clusters_config = JSONRepository.cargar_json(CORRELATIONS_FILE).get("CLUSTERS", {})

    rules_catalog = registry.get("RULES", {})
    league_upper = sport_league.upper().strip()

    sorted_rules = sorted(rules_catalog.items(), key=lambda x: x[1].get("priority", 99))
    rules_applicable, evaluable_rules, triggered_rules_raw, missing_data_rules = (
        0,
        [],
        [],
        [],
    )
    circuit_breaker_triggered, circuit_breaker_reason = False, ""
    metrics = scout_data.get("advanced_metrics", {})

    for code, r_def in sorted_rules:
        if league_upper in [
            league.upper() for league in r_def.get("leagues", [])
        ] or "GENERIC_SPORTS" in [league.upper() for league in r_def.get("leagues", [])]:
            rules_applicable += 1
            priority = int(r_def.get("priority", 99))
            w_base = float(r_def.get("weight", 0.0))

            perf_info = performance.get(code, {})
            auto_status = QuantEngineCore.evaluar_auto_status_regla(perf_info)

            p_mult = PRIORITY_MULTIPLIERS.get(priority, 1.0)
            w_eff = (
                QuantEngineCore.actualizar_peso_bayesiano(w_base, perf_info) * p_mult
            )

            if auto_status == "DISABLED" or w_eff == 0.0:
                missing_data_rules.append(code)
                continue

            is_evaluable, is_triggered = QuantEngineCore.evaluar_regla_declarativa(
                r_def, metrics, line_movement_pct, steam_detected
            )

            if is_evaluable:
                evaluable_rules.append(code)
                if is_triggered:
                    severity = r_def.get("severity", "MEDIUM")
                    if code in ["CXI", "QBI", "AVR"] and severity == "CRITICAL":
                        severity = "CRITICAL_DATA"
                    elif severity == "CRITICAL":
                        severity = "CRITICAL_EDGE"

                    triggered_rules_raw.append(
                        {
                            "rule": code,
                            "name": r_def.get("name"),
                            "priority": priority,
                            "severity": severity,
                            "status": auto_status,
                            "weight_effective": round(w_eff, 4),
                        }
                    )

                    if priority == 0 and severity == "CRITICAL_EDGE":
                        circuit_breaker_triggered = True
                        circuit_breaker_reason = f"Circuit Breaker P0 [{code} - CRITICAL_EDGE]: {r_def.get('name')}"
            else:
                missing_data_rules.append(code)

    cluster_manager = ClusterManager(clusters_config)
    cluster_hits, final_triggered_rules = (
        cluster_manager.evaluar_penalizaciones_cluster(triggered_rules_raw)
    )

    total_adjustment = sum(item["weight_effective"] for item in final_triggered_rules)

    return {
        "rules_applicable": rules_applicable,
        "coverage": (
            round((len(evaluable_rules) / rules_applicable) * 100, 2)
            if rules_applicable > 0
            else 100.0
        ),
        "circuit_breaker_triggered": circuit_breaker_triggered,
        "circuit_breaker_reason": circuit_breaker_reason,
        "rule_audit": {
            "evaluable": evaluable_rules,
            "triggered": final_triggered_rules,
            "missing_data": missing_data_rules,
        },
        "cluster_hits": cluster_hits,
        "total_adjustment": round(total_adjustment, 4),
    }
