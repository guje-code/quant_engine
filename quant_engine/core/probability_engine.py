import math


class ProbabilityEngine:
    @staticmethod
    def calcular_implied_probability(odds: float) -> float:
        """Calcula la probabilidad implícita de la cuota de la casa de apuestas."""
        if odds <= 1.0:
            return 0.0
        return round(1.0 / odds, 4)

    @staticmethod
    def calcular_roi_teorico(prob_final: float, odds: float) -> float:
        """Calcula el Return on Investment (ROI) teórico esperado por unidad arriesgada."""
        if odds <= 1.0:
            return 0.0
        return round((prob_final * odds) - 1.0, 4)

    @staticmethod
    def ajustar_probabilidad_logit(prob_base: float, total_adjustment: float) -> dict:
        """
        Aplica contracción logit y devuelve un diccionario completo con la
        pista de auditoría matemática para debugging y trazabilidad avanzada.
        """
        p = max(0.001, min(0.999, prob_base))
        logit_base = math.log(p / (1.0 - p))
        logit_final = logit_base + total_adjustment
        prob_final = round(1.0 / (1.0 + math.exp(-logit_final)), 4)

        return {
            "prob_base": round(prob_base, 4),
            "logit_base": round(logit_base, 4),
            "adjustment": round(total_adjustment, 4),
            "logit_final": round(logit_final, 4),
            "prob_final": prob_final,
        }

    @staticmethod
    def calcular_probabilidad_final(prob_base: float, total_adjustment: float) -> float:
        """
        Método de conveniencia que mantiene el contrato original devolviendo
        estrictamente un float, utilizando internamente el motor logit.
        """
        audit_res = ProbabilityEngine.ajustar_probabilidad_logit(
            prob_base, total_adjustment
        )
        return audit_res["prob_final"]

    @staticmethod
    def calcular_expected_value(prob_final: float, odds: float) -> float:
        """Calcula el Expected Value (EV) expresado en porcentaje (%) reutilizando el ROI teórico."""
        if odds <= 1.0:
            return 0.0
        roi_teorico = ProbabilityEngine.calcular_roi_teorico(prob_final, odds)
        return round(roi_teorico * 100.0, 2)
