from datetime import datetime

from quant_engine.config.settings import (
    STEAM_TOTAL_MOVE_THRESHOLD,
    STEAM_VELOCITY_THRESHOLD,
)


class SteamDetector:
    def __init__(self, velocity_threshold: float = STEAM_VELOCITY_THRESHOLD):
        self.velocity_threshold = velocity_threshold

    def _clasificar_movimiento_y_severidad(
        self, total_move_pct: float, velocity: float
    ) -> tuple[str, str]:
        # 1. Clasificación unificada del tipo de movimiento
        if total_move_pct > 0.0:
            movement_type = "FAVORABLE"
        elif total_move_pct < 0.0:
            movement_type = "ADVERSE"
        else:
            movement_type = "NEUTRAL"

        # 2. Severidad basada en la velocidad y la magnitud del Steam Move
        abs_move = abs(total_move_pct)
        if velocity >= 3.0 or abs_move >= 10.0:
            severity = "CRITICAL"
        elif velocity >= 2.0 or abs_move >= 7.0:
            severity = "HIGH"
        elif (
            velocity >= self.velocity_threshold
            or abs_move >= STEAM_TOTAL_MOVE_THRESHOLD
        ):
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return movement_type, severity

    def evaluate_steam_move(
        self, opening_odds: float, live_odds: float, time_delta_minutes: float = 15.0
    ) -> dict:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if opening_odds <= 1.0 or live_odds <= 1.0 or time_delta_minutes <= 0:
            return {
                "steam_detected": False,
                "velocity_pct_min": 0.0,
                "total_move_pct": 0.0,
                "movement_type": "NEUTRAL",
                "severity": "LOW",
                "timestamp": timestamp,
                "reason": "Datos insuficientes",
            }

        total_move_pct = ((live_odds - opening_odds) / opening_odds) * 100.0
        velocity = abs(total_move_pct) / time_delta_minutes

        steam_detected = (
            velocity >= self.velocity_threshold
            or abs(total_move_pct) >= STEAM_TOTAL_MOVE_THRESHOLD
        )
        movement_type, severity = self._clasificar_movimiento_y_severidad(
            total_move_pct, velocity
        )

        return {
            "steam_detected": steam_detected,
            "velocity_pct_min": round(velocity, 4),
            "total_move_pct": round(total_move_pct, 2),
            "movement_type": movement_type,
            "severity": severity,
            "timestamp": timestamp,
            "reason": f"Velocidad: {velocity:.2f}%/min | Movimiento total: {total_move_pct:+.2f}% | Tipo: {movement_type} | Severidad: {severity}",
        }
