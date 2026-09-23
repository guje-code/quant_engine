from quant_engine.settlement.espn_provider import consultar_espn
from quant_engine.settlement.web_fallback_provider import buscar_marcador_web


class ResultProvider:
    @staticmethod
    def resolve(match_name: str, sport_league: str, created_at: str) -> dict:
        """
        Orquestador unificado de obtención de resultados:
        1. Consulta la API de ESPN (con caché TTL y telemetría).
        2. Si no hay éxito, ejecuta el fallback de búsqueda web en tiempo real.
        3. Normaliza y retorna el estatus y los puntajes del evento.
        """
        # 1. Intento principal con ESPN
        resultado = consultar_espn(match_name, sport_league, created_at)
        if resultado.get("status") == "FINAL":
            return resultado

        # 2. Intento secundario con Web Fallback
        print(
            f"🔍 [RESULT PROVIDER] ESPN sin match final para '{match_name}'. Ejecutando Fallback Web..."
        )
        return buscar_marcador_web(match_name)
