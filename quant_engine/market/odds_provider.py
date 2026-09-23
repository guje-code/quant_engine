import asyncio
import concurrent.futures  # <--- Import crítico incorporado para evitar NameError
import logging
import time

from playwright.async_api import async_playwright

from quant_engine.config.settings import (
    ODDS_CACHE_TTL_SECONDS,
    ODDS_SELECTORS,
    SEARCH_SELECTORS,
    SPORTSBOOK_URL,
)


class OddsProvider:
    def __init__(self):
        self.url = SPORTSBOOK_URL
        # Caché con TTL: {match_name: (odds_value, timestamp)}
        self._cache = {}

    async def _scrape_odds_async(self, match_name: str) -> dict:
        t_start = time.perf_counter()
        browser = None
        selector_hit = None
        scraped_val = 0.0

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                # Timeout de 15 segundos para la navegación de la página
                await page.goto(self.url, wait_until="networkidle", timeout=15000)

                # 1. Búsqueda robusta con selectores externalizados
                for sel in SEARCH_SELECTORS:
                    try:
                        locator = page.locator(sel)
                        if (
                            await locator.count() > 0
                            and await locator.first.is_visible()
                        ):
                            await locator.first.fill(match_name)
                            await page.keyboard.press("Enter")
                            await page.wait_for_timeout(3000)
                            break
                    except Exception:
                        continue

                # 2. Extracción de cuotas registrando el selector exitoso
                for sel in ODDS_SELECTORS:
                    try:
                        locator = page.locator(sel)
                        if await locator.count() > 0:
                            elements = await locator.all_text_contents()
                            for text in elements:
                                cleaned = text.strip()
                                if cleaned.replace(".", "", 1).isdigit():
                                    val = float(cleaned)
                                    if val > 1.0:
                                        scraped_val = val
                                        selector_hit = sel
                                        break
                            if scraped_val > 1.0:
                                break
                    except Exception:
                        continue
        except Exception as e:
            logging.warning(f"Error en OddsProvider scraping para {match_name}: {e}")
        finally:
            if browser:
                await browser.close()

        duration_ms = (time.perf_counter() - t_start) * 1000.0
        fallback_used = scraped_val <= 1.0

        logging.info(
            f"[ODDS TELEMETRY] Partido: {match_name} | "
            f"Duración: {duration_ms:.1f}ms | "
            f"Selector Hit: {selector_hit or 'NONE'} | "
            f"Fallback Usado: {fallback_used}"
        )

        return {
            "odds": scraped_val if not fallback_used else 0.0,
            "scrape_duration_ms": round(duration_ms, 2),
            "selector_hit": selector_hit,
            "fallback_used": fallback_used,
        }

    async def get_live_odds_async(self, match_name: str, fallback_odds: float) -> float:
        """Interfaz nativa asíncrona recomendada para arquitecturas ASGI (FastAPI / Quart)."""
        now = time.time()

        # 1. Validación de caché TTL
        if match_name in self._cache:
            cached_val, cached_time = self._cache[match_name]
            if now - cached_time < ODDS_CACHE_TTL_SECONDS:
                logging.info(
                    f"[ODDS CACHE HIT] Sirviendo cuota en caché para: {match_name}"
                )
                return cached_val

        # 2. Ejecución de scraping asíncrono real sin bloqueos
        scrape_result = await self._scrape_odds_async(match_name)
        final_odds = (
            scrape_result["odds"]
            if not scrape_result["fallback_used"]
            else fallback_odds
        )

        # 3. Actualización de caché
        self._cache[match_name] = (final_odds, now)
        return final_odds

    def get_live_odds(self, match_name: str, fallback_odds: float) -> float:
        """
        Interfaz síncrona de compatibilidad adaptativa.
        Maneja entornos con event loops activos usando un ThreadPoolExecutor aislado
        y un timeout de 20.0s (coherente con el timeout interno de 15.0s de Playwright).
        """
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run, self.get_live_odds_async(match_name, fallback_odds)
                    )
                    return future.result(timeout=20.0)
            else:
                return asyncio.run(self.get_live_odds_async(match_name, fallback_odds))
        except Exception as e:
            logging.warning(
                f"Fallo en OddsProvider adaptativo síncrono, usando fallback: {e}"
            )
            return fallback_odds
