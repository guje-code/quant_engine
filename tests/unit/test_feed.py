from unittest.mock import Mock, patch

from quant_engine.market.feed import MarketFeedFacade


class TestMarketFeedFacade:

    # ==========================================
    # SUCCESS CASE
    # ==========================================

    @patch("quant_engine.market.feed.SteamDetector")
    @patch("quant_engine.market.feed.CLVEngine")
    @patch("quant_engine.market.feed.OddsProvider")
    def test_market_intelligence_success(self, mock_provider, mock_clv, mock_steam):

        mock_clv_instance = Mock()
        mock_clv.return_value = mock_clv_instance

        mock_clv_instance.validate_live_odds.return_value = {
            "valid": True,
            "reason": "OK",
            "current_odds": 2.10,
            "drop_pct": 5.0,
        }

        mock_steam_instance = Mock()
        mock_steam.return_value = mock_steam_instance

        mock_steam_instance.evaluate_steam_move.return_value = {
            "steam_detected": True,
            "severity": "HIGH",
        }

        facade = MarketFeedFacade()

        result = facade.get_market_intelligence(
            match_name="Boston vs Yankees", opening_odds=2.00
        )

        assert result["valid"] is True
        assert result["steam_detected"] is True

    # ==========================================
    # INVALID CLV
    # ==========================================

    @patch("quant_engine.market.feed.SteamDetector")
    @patch("quant_engine.market.feed.CLVEngine")
    @patch("quant_engine.market.feed.OddsProvider")
    def test_market_intelligence_invalid_clv(self, mock_provider, mock_clv, mock_steam):

        mock_clv_instance = Mock()
        mock_clv.return_value = mock_clv_instance

        mock_clv_instance.validate_live_odds.return_value = {
            "valid": False,
            "reason": "Critical CLV",
            "current_odds": 1.80,
            "drop_pct": -10.0,
        }

        mock_steam_instance = Mock()
        mock_steam.return_value = mock_steam_instance

        mock_steam_instance.evaluate_steam_move.return_value = {"steam_detected": False}

        facade = MarketFeedFacade()

        result = facade.get_market_intelligence("Match", 2.0)

        assert result["valid"] is False

    # ==========================================
    # STEAM DETECTED
    # ==========================================

    @patch("quant_engine.market.feed.SteamDetector")
    @patch("quant_engine.market.feed.CLVEngine")
    @patch("quant_engine.market.feed.OddsProvider")
    def test_steam_detection_propagates(self, mock_provider, mock_clv, mock_steam):

        mock_clv_instance = Mock()
        mock_clv.return_value = mock_clv_instance

        mock_clv_instance.validate_live_odds.return_value = {
            "valid": True,
            "reason": "OK",
            "current_odds": 2.20,
            "drop_pct": 10.0,
        }

        mock_steam_instance = Mock()
        mock_steam.return_value = mock_steam_instance

        mock_steam_instance.evaluate_steam_move.return_value = {
            "steam_detected": True,
            "movement_type": "FAVORABLE",
        }

        facade = MarketFeedFacade()

        result = facade.get_market_intelligence("Match", 2.0)

        assert result["steam_detected"] is True

    # ==========================================
    # LINE MOVEMENT
    # ==========================================

    @patch("quant_engine.market.feed.SteamDetector")
    @patch("quant_engine.market.feed.CLVEngine")
    @patch("quant_engine.market.feed.OddsProvider")
    def test_line_movement_propagates(self, mock_provider, mock_clv, mock_steam):

        mock_clv_instance = Mock()
        mock_clv.return_value = mock_clv_instance

        mock_clv_instance.validate_live_odds.return_value = {
            "valid": True,
            "reason": "OK",
            "current_odds": 2.10,
            "drop_pct": 7.5,
        }

        mock_steam_instance = Mock()
        mock_steam.return_value = mock_steam_instance

        mock_steam_instance.evaluate_steam_move.return_value = {"steam_detected": False}

        facade = MarketFeedFacade()

        result = facade.get_market_intelligence("Match", 2.0)

        assert result["line_movement_pct"] == 7.5

    # ==========================================
    # CONTRACT
    # ==========================================

    @patch("quant_engine.market.feed.SteamDetector")
    @patch("quant_engine.market.feed.CLVEngine")
    @patch("quant_engine.market.feed.OddsProvider")
    def test_return_contract(self, mock_provider, mock_clv, mock_steam):

        mock_clv_instance = Mock()
        mock_clv.return_value = mock_clv_instance

        mock_clv_instance.validate_live_odds.return_value = {
            "valid": True,
            "reason": "OK",
            "current_odds": 2.0,
            "drop_pct": 1.0,
        }

        mock_steam_instance = Mock()
        mock_steam.return_value = mock_steam_instance

        mock_steam_instance.evaluate_steam_move.return_value = {"steam_detected": False}

        facade = MarketFeedFacade()

        result = facade.get_market_intelligence("Match", 2.0)

        expected_keys = {
            "valid",
            "reason",
            "current_odds",
            "line_movement_pct",
            "clv_details",
            "steam_detected",
            "steam_details",
        }

        assert expected_keys.issubset(result.keys())
