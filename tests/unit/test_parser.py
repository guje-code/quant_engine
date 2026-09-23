from quant_engine.core.parser import QuantEngineCore


class TestParser:

    # ==========================================
    # EVALUAR CONDICION INDIVIDUAL
    # ==========================================

    def test_greater_than(self):
        assert QuantEngineCore.evaluar_condicion_individual(10, ">", 5) is True

    def test_less_than(self):
        assert QuantEngineCore.evaluar_condicion_individual(5, "<", 10) is True

    def test_equal(self):
        assert QuantEngineCore.evaluar_condicion_individual(10, "==", 10) is True

    def test_not_equal(self):
        assert QuantEngineCore.evaluar_condicion_individual(10, "!=", 20) is True

    def test_none_value_returns_false(self):
        assert QuantEngineCore.evaluar_condicion_individual(None, ">", 10) is False

    # ==========================================
    # SIMPLE RULE
    # ==========================================

    def test_simple_rule_triggered(self):
        rule = {"eval_type": "SIMPLE", "metric": "ev", "operator": ">", "threshold": 5}

        metrics = {"ev": 10}

        evaluable, triggered = QuantEngineCore.evaluar_regla_declarativa(
            rule, metrics, 0, False
        )

        assert evaluable is True
        assert triggered is True

    def test_simple_rule_not_triggered(self):
        rule = {"eval_type": "SIMPLE", "metric": "ev", "operator": ">", "threshold": 50}

        metrics = {"ev": 10}

        evaluable, triggered = QuantEngineCore.evaluar_regla_declarativa(
            rule, metrics, 0, False
        )

        assert evaluable is True
        assert triggered is False

    # ==========================================
    # AND RULE
    # ==========================================

    def test_and_rule_triggered(self):
        rule = {
            "eval_type": "AND",
            "conditions": [
                {"metric": "a", "operator": ">", "threshold": 5},
                {"metric": "b", "operator": ">", "threshold": 5},
            ],
        }

        metrics = {"a": 10, "b": 10}

        evaluable, triggered = QuantEngineCore.evaluar_regla_declarativa(
            rule, metrics, 0, False
        )

        assert evaluable is True
        assert triggered is True

    def test_and_rule_fails(self):
        rule = {
            "eval_type": "AND",
            "conditions": [
                {"metric": "a", "operator": ">", "threshold": 5},
                {"metric": "b", "operator": ">", "threshold": 5},
            ],
        }

        metrics = {"a": 10, "b": 1}

        evaluable, triggered = QuantEngineCore.evaluar_regla_declarativa(
            rule, metrics, 0, False
        )

        assert evaluable is True
        assert triggered is False

    # ==========================================
    # OR RULE
    # ==========================================

    def test_or_rule_triggered(self):
        rule = {
            "eval_type": "OR",
            "conditions": [
                {"metric": "a", "operator": ">", "threshold": 100},
                {"metric": "b", "operator": ">", "threshold": 5},
            ],
        }

        metrics = {"a": 1, "b": 10}

        evaluable, triggered = QuantEngineCore.evaluar_regla_declarativa(
            rule, metrics, 0, False
        )

        assert evaluable is True
        assert triggered is True

    # ==========================================
    # AUTO STATUS
    # ==========================================

    def test_status_active_when_empty(self):
        assert QuantEngineCore.evaluar_auto_status_regla({}) == "ACTIVE"

    def test_status_disabled(self):
        perf = {"total_bets": 500, "last_90d_roi": -10.0}

        assert QuantEngineCore.evaluar_auto_status_regla(perf) == "DISABLED"

    def test_status_monitor(self):
        perf = {"total_bets": 150, "roi_pct": -3.0}

        assert QuantEngineCore.evaluar_auto_status_regla(perf) == "MONITOR"

    def test_status_recovery(self):
        perf = {"status": "MONITOR", "total_bets": 200, "roi_pct": 2.0}

        assert QuantEngineCore.evaluar_auto_status_regla(perf) == "RECOVERY"

    # ==========================================
    # BAYESIAN WEIGHTS
    # ==========================================

    def test_disabled_weight_is_zero(self):
        perf = {"total_bets": 500, "last_90d_roi": -10.0}

        result = QuantEngineCore.actualizar_peso_bayesiano(1.0, perf)

        assert result == 0.0

    def test_positive_performance_increases_weight(self):
        perf = {
            "alpha_success": 80,
            "beta_failures": 20,
            "total_bets": 500,
            "roi_pct": 10,
            "status": "ACTIVE",
        }

        result = QuantEngineCore.actualizar_peso_bayesiano(1.0, perf)

        assert result > 1.0

    def test_negative_performance_reduces_weight(self):
        perf = {
            "alpha_success": 20,
            "beta_failures": 80,
            "total_bets": 500,
            "status": "ACTIVE",
        }

        result = QuantEngineCore.actualizar_peso_bayesiano(1.0, perf)

        assert result < 1.0

    def test_zero_samples_keeps_base_weight(self):
        perf = {"alpha_success": 80, "beta_failures": 20, "total_bets": 0}

        result = QuantEngineCore.actualizar_peso_bayesiano(1.0, perf)

        assert result == 1.0
