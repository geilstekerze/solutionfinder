# 01 – Systemarchitektur & Tech-Stack

## 1. Gesamtbild

```
                       ┌────────────────────────── Hetzner Cloud (EU) ──────────────────────────┐
                       │                                                                        │
 Anrufer ──PSTN──▶ Twilio (DE-Nr.,     ┌──────────────────────┐      ┌─────────────────────┐    │
                   Media Region de1)   │  voice-orchestrator  │◀────▶│ Azure OpenAI        │    │
                       │  Media Stream │  (Python, asyncio)   │  WS  │ Realtime API        │    │
                       └──────WS──────▶│  - Call-StateMachine │      │ (Sweden Central)    │    │
                                       │  - Audio-Bridge      │      └─────────────────────┘    │
                                       │  - Tool-Dispatcher   │                                 │
                                       └───────┬──────────────┘                                 │
                                               │ SQL / Redis                                    │
                       ┌───────────────────────┼──────────────────────────────┐                 │
                       │                       ▼                              │                 │
   Kunde (Browser) ──▶ Caddy 2 ──▶ ┌──────────────────┐   ┌───────────┐  ┌────────────┐        │
   Stripe Webhooks ──▶ (TLS)       │ api (FastAPI)    │──▶│ Postgres  │  │ Redis 7    │        │
   Twilio Webhooks ──▶             │ - Portal (HTMX)  │   │ 16 +      │  │ (flüchtig) │        │
                                   │ - Provisioning   │   │ pgvector  │  └────────────┘        │
                                   │ - Webhooks       │   └───────────┘                        │
                                   └──────┬───────────┘        ▲                               │
                                          │ Outbox-Events      │                               │
                                          ▼                    │                               │
                                   ┌──────────────┐   ┌────────┴─────────┐                     │
                                   │ n8n          │   │ ingestion-worker │                     │
                                   │ (Post-Call,  │   │ (Docs → Chunks   │                     │
                                   │  Benachricht.)│  │  → Embeddings)   │                     │
                                   └──────────────┘   └──────────────────┘                     │
                                                                                                │
                       Observability: Prometheus + Grafana + Loki + Sentry (EU)                 │
                       └────────────────────────────────────────────────────────────────────────┘
```

## 2. Services (4 Deployment-Einheiten + Infrastruktur)

| Service | Zweck | Technologie | Skalierung |
| :--- | :--- | :--- | :--- |
| `voice-orchestrator` | Nimmt Twilio-Media-Streams an, bridged Audio zur Realtime API, führt die Call-State-Machine und Tool-Aufrufe aus | Python 3.12, `websockets`, `asyncio` | horizontal (stateless bzgl. Persistenz; Call-State in Prozess + Redis) |
| `api` | Kundenportal (HTMX), Admin, Stripe-/Twilio-Webhooks, Provisioning-State-Machine, interne Tool-Endpunkte für den Orchestrator | FastAPI, Uvicorn, Jinja2, HTMX | horizontal |
| `ingestion-worker` | Verarbeitet hochgeladene Dokumente zu Chunks + Embeddings (Queue-basiert) | Python 3.12, `arq` (Redis-Queue) | horizontal |
| `n8n` | Post-Call-Automatisierung, Onboarding-Benachrichtigungen, CRM-Sync (Level 3-Vorbereitung) | n8n (gepinnte LTS-Version) | 1 Instanz |
| Infrastruktur | Postgres 16 + pgvector, Redis 7, Caddy 2, Prometheus, Grafana, Loki, Promtail | Docker Compose | vertikal |

**Warum kein separater „RAG-Service":** Retrieval ist eine Bibliotheksfunktion (`packages/shared/rag`), aufgerufen von `api` (Tool-Endpunkt) – ein Netzwerk-Hop weniger im Gesprächspfad.

## 3. Ziel-Repository-Struktur (neues Repo `frau-schmidt`)

Das umsetzende Modell legt exakt diese Struktur an:

```
frau-schmidt/
├── pyproject.toml                  # uv-Workspace; ein Lockfile (uv.lock) für alles
├── packages/
│   └── shared/                     # importierbar als `fs_shared`
│       ├── fs_shared/
│       │   ├── config.py           # Pydantic-Settings (Abschn. 5)
│       │   ├── db/                 # SQLAlchemy-Modelle, Session, RLS-Helper
│       │   ├── models/             # Pydantic-Domänenmodelle (Call, Ticket, …)
│       │   ├── rag/                # Chunking, Embedding-Client, Retrieval
│       │   ├── telephony/          # TelephonyAdapter-Interface + TwilioAdapter
│       │   ├── realtime/           # Azure-Realtime-Client (WS, Session-Config)
│       │   ├── telemetry/          # Logging (structlog), Metriken, Tracing-IDs
│       │   └── outbox.py           # Transaktionale Outbox (Abschn. 6)
│       └── tests/
├── services/
│   ├── voice_orchestrator/
│   │   ├── app/                    # main.py, call_session.py, state_machine.py,
│   │   │                           # audio_bridge.py, tool_dispatcher.py, fallback.py
│   │   └── tests/
│   ├── api/
│   │   ├── app/                    # main.py, routers/ (portal, webhooks_stripe,
│   │   │                           # webhooks_twilio, tools, admin), provisioning/
│   │   ├── templates/              # Jinja2 + HTMX
│   │   └── tests/
│   └── ingestion_worker/
│       ├── app/                    # worker.py, pipeline.py
│       └── tests/
├── migrations/                     # Alembic (eine Historie für die gesamte DB)
├── infra/
│   ├── compose/
│   │   ├── docker-compose.base.yml
│   │   ├── docker-compose.staging.yml
│   │   └── docker-compose.production.yml
│   ├── caddy/Caddyfile
│   ├── grafana/                    # Dashboards als JSON (versioniert)
│   ├── prometheus/prometheus.yml + alerts.yml
│   └── scripts/                    # deploy.sh, backup.sh, restore_test.sh
├── n8n/workflows/                  # exportierte Workflow-JSONs (versioniert)
├── tests_e2e/                      # Ende-zu-Ende: Test-Call, Stripe-Testkauf
├── docs/
│   ├── adr-log.md
│   └── runbooks/
└── .github/workflows/ci.yml + deploy.yml
```

## 4. Versions-Pinning (verbindlich, Stand Planerstellung)

Alle Versionen werden in `pyproject.toml`/`uv.lock` bzw. Compose-Dateien exakt gepinnt. Minor-Updates nur über eigene PRs mit grüner CI.

| Komponente | Version/Vorgabe |
| :--- | :--- |
| Python | 3.12.x |
| FastAPI / Uvicorn | aktuellste zum Umsetzungszeitpunkt stabile Version, dann gepinnt |
| SQLAlchemy / Alembic | 2.x / aktuellste stabile, gepinnt |
| Pydantic | 2.x |
| websockets, arq, structlog, stripe, twilio, httpx | aktuellste stabile, gepinnt |
| PostgreSQL | 16 (Docker-Image `postgres:16.<aktuell>` mit Digest-Pin) |
| pgvector | 0.8+ (Image `pgvector/pgvector:pg16`, Digest-Pin) – 0.8 ist Pflicht wegen iterativer Index-Scans bei Tenant-Filterung (Dok. 02/04) |
| Redis | 7.2 (Digest-Pin) |
| n8n | aktuelle LTS, Digest-Pin |
| Caddy | 2.x, Digest-Pin |
| Azure OpenAI | Realtime-Deployment `gpt-realtime` (GA), Embeddings `text-embedding-3-large` (dimensions=1536), beide Region Sweden Central |

**Regel:** Kein Docker-Tag `latest`; jedes Image mit `@sha256:`-Digest in Production-Compose.

## 5. Konfigurationsmanagement

- Eine einzige Settings-Klasse pro Service (`pydantic-settings`), Quelle: Environment-Variablen. **Beim Start werden alle Pflichtwerte validiert; fehlende Konfiguration = sofortiger Startabbruch mit klarer Fehlermeldung** (nie Laufzeitfehler später).
- Secrets liegen ausschließlich in einer `.env.production` auf dem Server (Dateirechte `600`, Besitzer Deploy-User), verwaltet über `sops` + `age` im Repo (`infra/secrets/*.enc.env`). Klartext-Secrets im Repo sind verboten (CI-Gate: `gitleaks`).
- Vollständige Variablenliste (Auszug, wird in WP1 finalisiert):
  `DATABASE_URL`, `REDIS_URL`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_REALTIME_DEPLOYMENT`, `AZURE_EMBEDDING_DEPLOYMENT`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `PUBLIC_BASE_URL`, `SENTRY_DSN`, `ENVIRONMENT` (`staging`|`production`), `SMTP_*`.

## 6. Interne Kommunikationsmuster

1. **Orchestrator → api (Tools):** HTTP (localhost-Netz im Compose), Endpunkte `POST /internal/tools/{search_knowledge|book_appointment|create_ticket|transfer_call}`. Auth über internes Shared-Secret-Header (`X-Internal-Token`), Timeout 3 s, 1 Retry. Antwortschema strikt (Pydantic), damit die Realtime-Function-Calls deterministisch beantwortet werden.
2. **api → n8n:** Transaktionale **Outbox-Tabelle** (`outbox_events`): Domänen-Events (`call.completed`, `tenant.provisioned`, `ticket.created`) werden in derselben DB-Transaktion wie die Datenänderung geschrieben. Ein Dispatcher-Task pusht sie an n8n-Webhooks (Retry mit Exponential Backoff, max. 24 h, danach Alert). → n8n-Ausfall verliert nie Events.
3. **api → ingestion-worker:** `arq`-Job über Redis; Job-Payload enthält nur IDs (Daten kommen aus der DB), Jobs sind idempotent (Re-Run überschreibt Chunks desselben Dokuments atomar).
4. **Kein Service ruft je direkt einen anderen im Gesprächs-Hotpath auf außer Orchestrator→api-Tools** (bewusst einziger synchroner Pfad, mit definiertem Fallback bei Timeout, siehe Dok. 03 Abschn. 8).

## 7. Netzwerk & Deployment-Topologie

- **Production-Server** (Hetzner, z. B. CCX33): alle Services via Compose; Postgres-Daten auf separatem Hetzner-Volume (verschlüsselt, siehe Dok. 06).
- **Staging-Server** (kleiner, z. B. CPX31): identische Topologie, eigene Twilio-Testnummer, Stripe-Testmode, eigenes Azure-Deployment.
- Eingehende Ports: nur 80/443 (Caddy) und 22 (SSH, Key-only, IP-beschränkt). Twilio-Media-Streams laufen als WSS über Caddy → `voice-orchestrator`.
- Twilio-Webhook-Signaturvalidierung und Stripe-Signaturvalidierung sind Pflicht (Requests ohne gültige Signatur → 403 + Log).
- Grafana/Prometheus nur über VPN/SSH-Tunnel oder Basic-Auth + IP-Allowlist erreichbar, nie öffentlich offen.

## 8. Latenzbudget Gesprächspfad (Grundlage für Dok. 03 und SLOs)

| Abschnitt | Budget (P95) |
| :--- | :--- |
| Twilio → Orchestrator (Frame-Weiterleitung) | ≤ 50 ms |
| Orchestrator → Azure Realtime (WS, EU) | ≤ 150 ms RTT |
| Realtime-Antwortbeginn nach Sprechpausen-Erkennung | ≤ 900 ms |
| Tool-Roundtrip (`search_knowledge`) inkl. Retrieval | ≤ 600 ms |
| **Gesamt: Antwortbeginn nach Nutzeräußerung** | **≤ 1,5 s** |

Jeder Abschnitt bekommt eine eigene Prometheus-Metrik (Histogramm), damit Budgetverletzungen lokalisierbar sind.

## 9. Erweiterungspunkte für Level 3/4 (nur vorbereiten, nicht bauen)

- `TelephonyAdapter` (zweiter Provider), `CalendarAdapter` (bereits mehrere Backends, Dok. 05), `CrmAdapter` (Interface-Datei + No-Op-Implementierung anlegen).
- Outbox-Events sind bereits das Integrationsereignis-Rückgrat für spätere Fach-Agenten.
- Tabelle `memories` (Long-Term-Memory) wird im Schema angelegt, aber im MVP nicht beschrieben (Dok. 02).
