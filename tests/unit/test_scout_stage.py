from unittest.mock import Mock, patch

from quant_engine.core.pipeline_steps.scout_stage import ejecutar_etapa_scout


class TestScoutStage:

    # ==========================================
    # SUCCESS
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.scout_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Task")
    @patch("quant_engine.core.pipeline_steps.scout_stage.AgentFactory")
    @patch("quant_engine.core.pipeline_steps.scout_stage.MarketFeedFacade")
    def test_scout_success(
        self, mock_market, mock_factory, mock_task, mock_crew, mock_extractor
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extractor.return_value = {"opening_odds": 2.0, "advanced_metrics": {}}

        market = mock_market.return_value

        market.get_market_intelligence.return_value = {
            "valid": True,
            "line_movement_pct": 2.0,
            "steam_detected": False,
        }

        result = ejecutar_etapa_scout(
            match_name="Boston vs Yankees",
            sport_league="MLB",
            user_instructions="",
            api_key="fake",
        )

        assert result["success"] is True

    # ==========================================
    # MARKET INVALID
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.scout_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Task")
    @patch("quant_engine.core.pipeline_steps.scout_stage.AgentFactory")
    @patch("quant_engine.core.pipeline_steps.scout_stage.MarketFeedFacade")
    def test_market_invalid(
        self, mock_market, mock_factory, mock_task, mock_crew, mock_extractor
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extractor.return_value = {"opening_odds": 2.0}

        market = mock_market.return_value

        market.get_market_intelligence.return_value = {
            "valid": False,
            "reason": "Bad CLV",
        }

        result = ejecutar_etapa_scout(
            match_name="Match", sport_league="MLB", user_instructions="", api_key="fake"
        )

        assert result["success"] is False

    # ==========================================
    # STEAM PROPAGATION
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.scout_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Task")
    @patch("quant_engine.core.pipeline_steps.scout_stage.AgentFactory")
    @patch("quant_engine.core.pipeline_steps.scout_stage.MarketFeedFacade")
    def test_steam_flag(
        self, mock_market, mock_factory, mock_task, mock_crew, mock_extractor
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extractor.return_value = {"opening_odds": 2.0}

        market = mock_market.return_value

        market.get_market_intelligence.return_value = {
            "valid": True,
            "line_movement_pct": 5.0,
            "steam_detected": True,
        }

        result = ejecutar_etapa_scout(
            match_name="Match", sport_league="MLB", user_instructions="", api_key="fake"
        )

        assert result["steam_detected"] is True

    # ==========================================
    # CLV PROPAGATION
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.scout_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Task")
    @patch("quant_engine.core.pipeline_steps.scout_stage.AgentFactory")
    @patch("quant_engine.core.pipeline_steps.scout_stage.MarketFeedFacade")
    def test_clv_propagation(
        self, mock_market, mock_factory, mock_task, mock_crew, mock_extractor
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extractor.return_value = {"opening_odds": 2.0}

        market = mock_market.return_value

        market.get_market_intelligence.return_value = {
            "valid": True,
            "line_movement_pct": 4.25,
            "steam_detected": False,
        }

        result = ejecutar_etapa_scout(
            match_name="Match", sport_league="MLB", user_instructions="", api_key="fake"
        )

        assert result["line_movement_pct"] == 4.25

    # ==========================================
    # CONTRACT
    # ==========================================

    @patch("quant_engine.core.pipeline_steps.scout_stage.extract_json_response")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Crew")
    @patch("quant_engine.core.pipeline_steps.scout_stage.Task")
    @patch("quant_engine.core.pipeline_steps.scout_stage.AgentFactory")
    @patch("quant_engine.core.pipeline_steps.scout_stage.MarketFeedFacade")
    def test_return_contract(
        self, mock_market, mock_factory, mock_task, mock_crew, mock_extractor
    ):

        fake_task = Mock()
        fake_task.output.raw = "{}"

        mock_task.return_value = fake_task

        mock_extractor.return_value = {"opening_odds": 2.0}

        market = mock_market.return_value

        market.get_market_intelligence.return_value = {
            "valid": True,
            "line_movement_pct": 1.0,
            "steam_detected": False,
        }

        result = ejecutar_etapa_scout(
            match_name="Match", sport_league="MLB", user_instructions="", api_key="fake"
        )

        expected = {
            "success",
            "scout_json",
            "line_movement_pct",
            "steam_detected",
            "duration_ms",
        }

        assert expected.issubset(result.keys())
