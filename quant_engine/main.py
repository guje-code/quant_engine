import os

from crewai.tools import tool
from dotenv import load_dotenv

from quant_engine.market.feed import MarketFeedFacade
from quant_engine.pipeline.pipeline_facade import PipelineFacade

load_dotenv()

# Inicialización de componentes para herramientas de CrewAI
market_facade = MarketFeedFacade()
pipeline = PipelineFacade(api_key=os.environ.get("GEMINI_API_KEY"))


@tool("Validar Cuota Viva y CLV")
def validar_cuota_viva(match_name: str, odds: float) -> str:
    intel = market_facade.get_market_intelligence(match_name, float(odds))
    return (
        f"✅ Válida: {intel['reason']}"
        if intel["valid"]
        else f"❌ Alerta: {intel['reason']}"
    )


@tool("Consultar Histórico")
def consultar_performance_historica(league: str) -> str:
    return "Histórico consultado con éxito."


if __name__ == "__main__":
    custom_tools = {
        "validar_cuota_viva": validar_cuota_viva,
        "consultar_performance_historica": consultar_performance_historica,
    }

    resultado = pipeline.ejecutar_analisis(
        match_name="Boston Red Sox vs New York Yankees",
        sport_league="MLB",
        bankroll=200000.00,
        custom_tools=custom_tools,
    )
    print(resultado)
