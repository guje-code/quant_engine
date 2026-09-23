from datetime import datetime


class CLVEngine:
    def __init__(self, max_allowed_drop_pct: float = 3.0):
        self.max_allowed_drop_pct = max_allowed_drop_pct

    def calculate_line_movement(
        self, opening_odds: float, current_odds: float
    ) -> float:
        if opening_odds <= 1.0 or current_odds <= 1.0:
            return 0.0
        return round(((current_odds - opening_odds) / opening_odds) * 100.0, 2)

    def _clasificar_movimiento_y_severidad(self, drop_pct: float) -> tuple[str, str]:
        # 1. Clasificación del tipo de movimiento
        if drop_pct > 0.5:
            movement_type = "FAVORABLE"
        elif drop_pct < -0.5:
            movement_type = "ADVERSE"
        else:
            movement_type = "NEUTRAL"

        # 2. Severidad asimétrica: Solo los movimientos adversos (caídas) escalan en riesgo.
        # Los movimientos positivos (crecimiento de cuota) se marcan como oportunidad/bajos de riesgo.
        if drop_pct <= -7.0:
            severity = "CRITICAL"
        elif drop_pct <= -4.0:
            severity = "HIGH"
        elif drop_pct <= -self.max_allowed_drop_pct:
            severity = "MEDIUM"
        elif drop_pct < 0.0:
            severity = "LOW"
        else:
            severity = (
                "OPPORTUNITY"  # Movimientos positivos que mejoran nuestro EV teórico
            )

        return movement_type, severity

    def validate_live_odds(
        self, match_name: str, opening_odds: float, odds_provider
    ) -> dict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if opening_odds <= 1.0:
            return {
                "valid": False,
                "reason": "Cuota inicial inválida",
                "opening_odds": opening_odds,
                "current_odds": opening_odds,
                "drop_pct": 0.0,
                "movement_type": "NEUTRAL",
                "severity": "LOW",
                "timestamp": timestamp,
            }

        current_odds = odds_provider.get_live_odds(match_name, opening_odds)
        drop_pct = self.calculate_line_movement(opening_odds, current_odds)
        movement_type, severity = self._clasificar_movimiento_y_severidad(drop_pct)

        # Validación estricta con operador menor o igual (<=)
        if drop_pct <= -self.max_allowed_drop_pct:
            return {
                "valid": False,
                "reason": f"Caída crítica de línea en vivo: de {opening_odds:.2f} a {current_odds:.2f} ({drop_pct:.2f}%).",
                "opening_odds": opening_odds,
                "current_odds": current_odds,
                "drop_pct": drop_pct,
                "movement_type": movement_type,
                "severity": severity,
                "timestamp": timestamp,
            }

        return {
            "valid": True,
            "reason": f"Cuota viva verificada con éxito ({drop_pct:+.2f}%).",
            "opening_odds": opening_odds,
            "current_odds": current_odds,
            "drop_pct": drop_pct,
            "movement_type": movement_type,
            "severity": severity,
            "timestamp": timestamp,
        }
