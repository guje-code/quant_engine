import time

from crewai import LLM, Crew, Process, Task
from crewai_tools import SerperDevTool

from quant_engine.core.agent_factory import AgentFactory
from quant_engine.core.json_extractor import extract_json_response
from quant_engine.market.feed import MarketFeedFacade


def ejecutar_etapa_scout(
    match_name: str,
    sport_league: str,
    user_instructions: str,
    api_key: str,
    custom_tools: dict = None,
) -> dict:
    market_facade = MarketFeedFacade()
    llm = LLM(model="gemini/gemini-3.1-flash-lite", api_key=api_key, temperature=0.0)
    search_tool = SerperDevTool()

    factory = AgentFactory(llm, search_tool, custom_tools)
    scout_agent = factory.crear_scout_agent(match_name)

    task_scout = Task(
        description=f"Analizar {match_name}. {user_instructions}",
        expected_output="JSON estricto con opening_odds, current_odds y advanced_metrics.",
        agent=scout_agent,
    )

    t_start = time.time()
    Crew(agents=[scout_agent], tasks=[task_scout], process=Process.sequential).kickoff()
    t_duration = (time.time() - t_start) * 1000

    scout_fallback = {
        "opening_odds": 1.90,
        "current_odds": 1.85,
        "advanced_metrics": {},
        "data_quality_score": 0.95,
    }
    scout_json = extract_json_response(task_scout.output.raw, scout_fallback)
    opening_odds = float(scout_json.get("opening_odds", 1.90))

    # Inteligencia de Mercado Activa
    market_intel = market_facade.get_market_intelligence(match_name, opening_odds)
    if not market_intel["valid"]:
        return {"success": False, "reason": market_intel["reason"]}

    return {
        "success": True,
        "scout_json": scout_json,
        "line_movement_pct": market_intel["line_movement_pct"],
        "steam_detected": market_intel["steam_detected"],
        "duration_ms": t_duration,
    }
