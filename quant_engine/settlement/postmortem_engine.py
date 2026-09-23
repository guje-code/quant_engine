import json
import logging
import os

from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Instanciación unificada del LLM institucional (consistente con el resto del pipeline)
llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
)


class PostMortemEngine:
    @staticmethod
    def analizar_post_mortem(
        pick_id: int,
        match_name: str,
        sport_league: str,
        selection: str,
        odds: float,
        resultado: str,
        marcador_real: str = "",
        triggered_rules: list = None,
        confidence_score: float = 0.0,
        ev: float = 0.0,
        stake: float = 0.0,
    ) -> dict:
        """
        Ejecuta una auditoría cognitiva post-mortem inyectando explícitamente el LLM unificado.
        Valida estrictamente que el resultado sea un diccionario JSON estructurado.
        Incluye fallback robusto ante fallos del modelo.
        """
        triggered_rules = triggered_rules or []

        prompt_descripcion = (
            f"Analiza de manera sabermétrica y cuantitativa el siguiente pick liquidado:\n"
            f"- Partido: {match_name} ({sport_league})\n"
            f"- Selección: {selection} | Momio (Odds): {odds}\n"
            f"- Resultado Real: {resultado} | Marcador: {marcador_real}\n"
            f"- Reglas Disparadas: {json.dumps(triggered_rules)}\n"
            f"- Confianza del Modelo: {confidence_score} | EV: {ev} | Stake: {stake}\n\n"
            f"Tu objetivo es actuar como un Auditor Cuantitativo Senior de un Hedge Fund.\n"
            f"Debes devolver EXCLUSIVAMENTE un objeto JSON válido (sin markdown adicional ni texto fuera del JSON) con la siguiente estructura:\n"
            f"{{\n"
            f'  "classification": "LOSS" | "BAD_BEAT" | "MODEL_ERROR" | "DATA_ERROR" | "MARKET_SHIFT",\n'
            f'  "root_cause": "Explicación detallada de por qué falló o acertó la predicción.",\n'
            f'  "finding": "Hallazgo clave sabermétrico extraído del evento.",\n'
            f'  "rule_candidate": "Propuesta de ajuste o nueva regla analítica para mitigar el error.",\n'
            f'  "confidence": 0.0 a 1.0\n'
            f"}}"
        )

        try:
            # Inyección explícita del llm para garantizar idéntico comportamiento en todo el pipeline
            auditor_agent = Agent(
                role="Senior Quantitative Betting Auditor",
                goal="Auditar rigurosamente los resultados de apuestas algorítmicas y extraer patrones lógicos.",
                backstory="Experto en modelado predictivo deportivo, análisis de valor esperado (EV) y control de riesgos.",
                verbose=False,
                llm=llm,
                allow_delegation=False,
            )

            audit_task = Task(
                description=prompt_descripcion,
                expected_output="Un objeto JSON estructurado estrictamente con las claves: classification, root_cause, finding, rule_candidate, confidence.",
                agent=auditor_agent,
            )

            crew = Crew(
                agents=[auditor_agent],
                tasks=[audit_task],
                process=Process.sequential,
                verbose=False,
            )

            resultado_analisis = crew.kickoff()
            raw_output = getattr(resultado_analisis, "raw", str(resultado_analisis))

            # Limpieza y parsing seguro del JSON
            cleaned_output = raw_output.strip()
            if cleaned_output.startswith("```json"):
                cleaned_output = cleaned_output[7:]
            if cleaned_output.endswith("```"):
                cleaned_output = cleaned_output[:-3]
            cleaned_output = cleaned_output.strip()

            postmortem_data = json.loads(cleaned_output)

            # Validación estricta de tipo dict
            if not isinstance(postmortem_data, dict):
                raise ValueError("El output del LLM no es un diccionario JSON válido.")

            logging.info(
                f"[POST-MORTEM] Auditoría completada con éxito para Pick #{pick_id}"
            )
            return postmortem_data

        except Exception as e:
            logging.warning(
                f"[POST-MORTEM FALLBACK] Error ejecutando auditoría para Pick #{pick_id}: {e}"
            )

            fallback_classification = (
                "BAD_BEAT" if resultado == "LOSS" else "MODEL_ERROR"
            )
            return {
                "classification": fallback_classification,
                "root_cause": f"Fallback automático activado por fallo técnico/parseo: {str(e)}",
                "finding": f"Liquidación de pick {resultado} sin auditoría profunda.",
                "rule_candidate": "N/A - Requiere revisión manual.",
                "confidence": 0.5,
            }


def analizar_post_mortem(
    pick_id: int,
    match_name: str,
    sport_league: str,
    selection: str,
    odds: float,
    resultado: str,
    marcador_real: str = "",
    **kwargs,
) -> dict:
    return PostMortemEngine.analizar_post_mortem(
        pick_id=pick_id,
        match_name=match_name,
        sport_league=sport_league,
        selection=selection,
        odds=odds,
        resultado=resultado,
        marcador_real=marcador_real,
        triggered_rules=kwargs.get("triggered_rules"),
        confidence_score=kwargs.get("confidence_score", 0.0),
        ev=kwargs.get("ev", 0.0),
        stake=kwargs.get("stake", 0.0),
    )
