from quant_engine.config.settings import STEAM_VELOCITY_THRESHOLD
from quant_engine.market.clv_engine import CLVEngine
from quant_engine.market.odds_provider import OddsProvider
from quant_engine.market.steam_detector import SteamDetector


class MarketFeedFacade:
    def __init__(
        self,
        max_drop_pct: float = 3.0,
        steam_velocity: float = STEAM_VELOCITY_THRESHOLD,
    ):
        self.provider = OddsProvider()
        self.clv_engine = CLVEngine(max_allowed_drop_pct=max_drop_pct)
        # Corrección de firma: velocity_threshold en lugar de velocity_threshold_pct_per_min
        self.steam_detector = SteamDetector(velocity_threshold=steam_velocity)

    def get_market_intelligence(
        self, match_name: str, opening_odds: float, time_delta_min: float = 15.0
    ) -> dict:
        validation = self.clv_engine.validate_live_odds(
            match_name, opening_odds, self.provider
        )
        current_odds = validation["current_odds"]

        steam = self.steam_detector.evaluate_steam_move(
            opening_odds, current_odds, time_delta_min
        )

        return {
            "valid": validation["valid"],
            "reason": validation["reason"],
            "current_odds": current_odds,
            "line_movement_pct": validation["drop_pct"],
            "clv_details": validation,
            "steam_detected": steam["steam_detected"],
            "steam_details": steam,
        }
