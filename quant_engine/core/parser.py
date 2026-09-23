class QuantEngineCore:
    @staticmethod
    def evaluar_condicion_individual(metrica_val, operador: str, threshold) -> bool:
        if metrica_val is None:
            return False
        try:
            if operador == "==":
                return metrica_val == threshold
            elif operador == "!=":
                return metrica_val != threshold
            elif operador == ">":
                return float(metrica_val) > float(threshold)
            elif operador == ">=":
                return float(metrica_val) >= float(threshold)
            elif operador == "<":
                return float(metrica_val) < float(threshold)
            elif operador == "<=":
                return float(metrica_val) <= float(threshold)
        except (ValueError, TypeError):
            return False
        return False

    @staticmethod
    def evaluar_regla_declarativa(
        rule_def: dict, metrics: dict, line_movement_pct: float, steam_detected: bool
    ) -> tuple[bool, bool]:
        if rule_def.get("internal_engine", False):
            if "fallback_flag" in rule_def and rule_def["fallback_flag"] in metrics:
                return True, bool(metrics[rule_def["fallback_flag"]])
            if rule_def.get("name") == "Closing Line Value":
                return True, (line_movement_pct < -3.0)
            if rule_def.get("name") == "Market Steam Move":
                return True, steam_detected

        eval_type = rule_def.get("eval_type", "SIMPLE")
        if eval_type == "SIMPLE":
            target_metric = rule_def.get("metric")
            if target_metric not in metrics:
                return False, False
            return True, QuantEngineCore.evaluar_condicion_individual(
                metrics[target_metric],
                rule_def.get("operator", "=="),
                rule_def.get("threshold"),
            )
        elif eval_type in ["AND", "OR"]:
            conditions = rule_def.get("conditions", [])
            if not conditions or not any(c["metric"] in metrics for c in conditions):
                return False, False
            resultados = [
                QuantEngineCore.evaluar_condicion_individual(
                    metrics.get(c["metric"]), c["operator"], c["threshold"]
                )
                for c in conditions
            ]
            return True, (all(resultados) if eval_type == "AND" else any(resultados))
        return False, False

    @staticmethod
    def evaluar_auto_status_regla(perf_data: dict) -> str:
        if not perf_data:
            return "ACTIVE"

        # Lectura retrocompatible: prioriza backtest_samples, luego total_bets
        samples = int(perf_data.get("backtest_samples", perf_data.get("total_bets", 0)))

        # Unificación de ROI: prioriza roi_pct unificado del settlement moderno, con fallback histórico
        roi_current = float(
            perf_data.get(
                "roi_pct",
                perf_data.get("last_30d_roi", perf_data.get("lifetime_roi", 0.0)),
            )
        )
        roi_90d = float(
            perf_data.get("last_90d_roi", perf_data.get("lifetime_roi", 0.0))
        )
        status = perf_data.get("status", "ACTIVE")

        if roi_90d < -5.0 and samples > 200:
            return "DISABLED"
        if roi_current < -2.0 and samples > 100:
            return "MONITOR"
        if status in ["DISABLED", "MONITOR"] and roi_current > 0.0:
            return "RECOVERY"
        if status == "RECOVERY" and roi_current > 1.5 and samples >= 30:
            return "ACTIVE"
        return (
            status
            if status in ["ACTIVE", "MONITOR", "DISABLED", "RECOVERY"]
            else "ACTIVE"
        )

    @staticmethod
    def actualizar_peso_bayesiano(
        w_base: float, perf_data: dict, k_prior: float = 50.0
    ) -> float:
        if not perf_data:
            return w_base
        auto_status = QuantEngineCore.evaluar_auto_status_regla(perf_data)
        if auto_status == "DISABLED":
            return 0.0

        alpha = float(perf_data.get("alpha_success", 1.0))
        beta_fail = float(perf_data.get("beta_failures", 1.0))

        # Lectura retrocompatible idéntica para evitar bloqueos por muestras en cero
        samples = int(perf_data.get("backtest_samples", perf_data.get("total_bets", 0)))
        if samples == 0:
            return w_base

        posterior_mean = alpha / (alpha + beta_fail)
        shrinkage = samples / (samples + k_prior)
        performance_boost = (posterior_mean - 0.5) * 2.0
        w_final = w_base * (1.0 + performance_boost * shrinkage)

        if auto_status == "MONITOR":
            w_final *= 0.25
        elif auto_status == "RECOVERY":
            w_final *= 0.75

        return round(w_final, 4)
