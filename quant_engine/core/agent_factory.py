from crewai import LLM, Agent
from crewai_tools import SerperDevTool


class AgentFactory:
    def __init__(
        self, llm_instance: LLM, search_tool: SerperDevTool, custom_tools: dict = None
    ):
        self.llm = llm_instance
        self.search_tool = search_tool
        self.custom_tools = custom_tools or {}

    def crear_scout_agent(self, match_name: str) -> Agent:
        # Filtrado defensivo de herramientas para evitar valores None
        tools = [self.search_tool]
        val_tool = self.custom_tools.get("validar_cuota_viva")
        if val_tool:
            tools.append(val_tool)

        return Agent(
            role="Market Intelligence Scout",
            goal=f"Recolectar datos precisos, métricas avanzadas y verificar condiciones de mercado en tiempo real para {match_name}.",
            backstory=(
                "Eres un experto analista de inteligencia de mercados deportivos, especializado en scraping avanzado, "
                "detección de movimientos de línea y validación de cuotas vivas en casas de apuestas globales."
            ),
            tools=tools,
            llm=self.llm,
            verbose=False,
        )

    def crear_quant_agent(self) -> Agent:
        # Filtrado defensivo de herramientas
        tools = []
        hist_tool = self.custom_tools.get("consultar_performance_historica")
        if hist_tool:
            tools.append(hist_tool)

        return Agent(
            role="Quantitative Probability Analyst",
            goal="Analizar el valor esperado (EV), evaluar probabilidades matemáticas avanzadas y aplicar el motor de reglas cuantitativo.",
            backstory=(
                "Eres un investigador cuantitativo con amplia experiencia en modelos estadísticos bayesianos, sabermétricas "
                "y análisis de valor esperado (EV) para fondos de inversión y apuestas deportivas de alta frecuencia."
            ),
            tools=tools,
            llm=self.llm,
            verbose=False,
        )

    def crear_risk_agent(self) -> Agent:
        return Agent(
            role="Portfolio Risk Manager",
            goal="Gestionar el riesgo global del portafolio mediante simulación de Monte Carlo, VaR, CVaR con Cópula Student-t y dimensionamiento de capital.",
            backstory=(
                "Eres el director de gestión de riesgos de un Hedge Fund cuantitativo. Tu prioridad absoluta es la preservación "
                "del capital, aplicando controles estrictos de Valor en Riesgo (VaR), Expected Shortfall y asignación óptima de Kelly fraccional."
            ),
            tools=[],
            llm=self.llm,
            verbose=False,
        )
