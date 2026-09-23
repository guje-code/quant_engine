# Quantitative Citadel v10.0

Motor cuantitativo para análisis de apuestas deportivas con arquitectura modular, aprendizaje bayesiano, gestión de riesgo institucional y automatización completa de auditoría post-mortem.

## Estado del Proyecto

- Arquitectura auditada y validada.
- Más de 150 pruebas automatizadas.
- Cobertura aproximada superior al 65%.
- Integración continua mediante GitHub Actions.
- Linting con Ruff.
- Formateo con Black.

---

## Arquitectura General

```text
app.py
bot.py

        ↓

PipelineFacade

        ↓

Scout Stage
        ↓
Rule Stage
        ↓
Quant Risk Stage
        ↓
Persistence Stage

        ↓

SettlementFacade

        ↓

PostMortemEngine

        ↓

Lessons Learned
```

---

## Componentes

### Core

```text
agent_factory.py
json_extractor.py
parser.py
probability_engine.py
rule_engine.py
```

### Market

```text
feed.py
odds_provider.py
clv_engine.py
steam_detector.py
```

### Risk

```text
position_sizing.py
portfolio_mc.py
cluster_manager.py
```

### Settlement

```text
settlement_facade.py
result_updater.py
espn_provider.py
web_fallback_provider.py
postmortem_engine.py
lessons_learned.py
```

### Storage

```text
persistence.py
json_repository.py
```

---

## Funcionalidades

### Rule Engine

- Reglas declarativas.
- Circuit breakers.
- Ponderación bayesiana.
- Estados ACTIVE, MONITOR, DISABLED y RECOVERY.

### Market Intelligence

- Detección CLV.
- Steam Move Detection.
- Validación de cuotas vivas.
- Severidad de mercado.

### Risk Management

- Quarter Kelly.
- Stake Caps.
- Monte Carlo.
- VaR 95%.
- CVaR 95%.
- Ledoit-Wolf Shrinkage.
- Student-t Copula.

### Learning Loop

```text
Settlement
↓
Bayesian Feedback
↓
Rule Performance
↓
Post Mortem
↓
Knowledge Base
↓
Lessons Learned
```

---

## Testing

Suite automatizada:

```text
ProbabilityEngine
PositionSizing
Parser
RuleEngine
CLVEngine
SteamDetector
ClusterManager
SettlementFacade
PostMortemEngine
Persistence
PipelineFacade
JSONRepository
JSONExtractor
```

Más de 150 pruebas exitosas.

---

## Instalación

### Entorno virtual

```bash
python -m venv .venv
```

### Activación

Windows:

```bash
.venv\Scripts\activate
```

Linux / Mac:

```bash
source .venv/bin/activate
```

### Dependencias

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Calidad

### Ruff

```bash
ruff check .
```

### Black

```bash
black .
```

### Pytest

```bash
pytest
```

### Coverage

```bash
pytest --cov=quant_engine
```

---

## CI/CD

GitHub Actions ejecuta:

```text
Ruff
↓
Pytest
↓
Coverage Gate
↓
Artifacts
```

---

## Roadmap

### Fase 12 ✅

- Testing.
- Cobertura.
- GitHub Actions.
- Quality Gates.

### Fase 13

- Observabilidad.
- Prometheus.
- Grafana.
- Métricas LLM.
- Alertas Telegram.

---

## Licencia

Uso interno e investigación cuantitativa.
