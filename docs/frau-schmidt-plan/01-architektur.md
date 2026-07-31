# 01 – Systemarchitektur & Tech-Stack

## 1. Gesamtbild

```text
Anrufer ──PSTN──▶ Twilio (DE-Nr., Media Region de1)
                         │ Media Stream (WSS)
                         ▼
                voice-orchestrator ──WS──▶ Azure OpenAI Realtime
                         │
                         │ signierte interne Tool-Aufrufe
                         ▼
                       app
        (API, Portal, Webhooks, Tools, Provisioning)
            │              │               │
            ▼              ▼               ▼
        PostgreSQL     Worker/Queue      optionale n8n-Flows
        + pgvector     (gleiche Codebasis; erst nach Gate A)

Edge/TLS: Caddy · Fehler: Sentry · Metriken: Prometheus/Grafana stufenweise
```

Der Gesprächspfad besitzt genau eine synchrone interne Abhängigkeit: `voice-orchestrator → app`. n8n, E-Mail-Versand, Dokumenten-Ingestion und Zusammenfassungen laufen asynchron.

## 2. Deployment-Einheiten nach Reifegrad

Die fachlichen Module bleiben getrennt, werden aber nicht vorsorglich als viele eigenständige Dienste betrieben.

| Stufe | Prozesse/Container | Zweck |
| :--- | :--- | :--- |
| Produktbeweis | `app`, `voice-orchestrator` | vollständiger End-to-End-Anruf, direkte Ticket-E-Mail, Messwerte |
| Pilot-MVP | zusätzlich `worker`, optional Redis | Ingestion, Outbox, Hintergrundjobs, Rate-Limiting |
| Verkaufs-MVP | zusätzlich n8n und vollständiges Monitoring | Self-Service, optionale Automatisierungen, Betriebsdashboards |
| Skalierung | mehrere Orchestratoren/Worker | horizontale Skalierung nach nachgewiesener Last |

`app` enthält zunächst FastAPI, Portal, Admin, Webhooks, Provisioning und interne Tools. `worker` importiert dieselben Pakete aus derselben Codebasis. Erst wenn unabhängige Skalierung oder Fehlerisolation messbar notwendig ist, werden Komponenten als eigene Deployments herausgelöst.

**Warum kein separater RAG-Service:** Retrieval bleibt eine Bibliotheksfunktion. Das spart einen Netzwerk-Hop und einen zusätzlichen Ausfallpunkt.

**Warum n8n nicht im Kern-MVP:** Die erste Ticket-E-Mail wird aus der transaktionalen Outbox durch den eigenen Worker zugestellt. n8n ergänzt später optionale Kundenautomatisierungen, ist aber nie Voraussetzung für einen erfolgreichen Anruf.

## 3. Ziel-Repository-Struktur

```text
frau-schmidt/
├── pyproject.toml                  # uv-Workspace; ein Lockfile
├── packages/
│   └── shared/
│       ├── fs_shared/
│       │   ├── config.py
│       │   ├── db/
│       │   ├── models/
│       │   ├── rag/
│       │   ├── telephony/
│       │   ├── realtime/
│       │   ├── telemetry/
│       │   ├── security/
│       │   └── outbox.py
│       └── tests/
├── services/
│   ├── app/
│   │   ├── app/
│   │   └── tests/
│   ├── voice_orchestrator/
│   │   ├── app/
│   │   └── tests/
│   └── worker/
│       ├── app/
│       └── tests/
├── migrations/
├── infra/
│   ├── compose/
│   ├── caddy/
│   ├── grafana/
│   ├── prometheus/
│   └── scripts/
├── n8n/workflows/                  # erst nach Gate A aktiv
├── tests_e2e/
├── docs/
│   ├── adr-log.md
│   ├── abnahme/
│   └── runbooks/
└── .github/workflows/
```

Die Paketgrenzen entsprechen den späteren Skalierungsgrenzen. Zusammenlegen im Betrieb bedeutet daher keine Vermischung der Fachlogik.

## 4. Versions-Pinning

Alle Abhängigkeiten und Images werden nach Auswahl exakt gepinnt. Updates erfolgen über eigene PRs mit grüner CI.

| Komponente | Vorgabe |
| :--- | :--- |
| Python | 3.12.x |
| FastAPI / Uvicorn | stabile Version, exakt gepinnt |
| SQLAlchemy / Alembic | 2.x / stabile Version, gepinnt |
| Pydantic | 2.x |
| websockets, arq, structlog, stripe, twilio, httpx | stabile Versionen, gepinnt |
| PostgreSQL | 16 mit Digest-Pin |
| pgvector | 0.8+ mit Digest-Pin |
| Redis | 7.2 mit Digest-Pin, erst ab tatsächlichem Bedarf verpflichtend |
| n8n | stabile freigegebene Version mit Digest-Pin |
| Caddy | 2.x mit Digest-Pin |
| Azure OpenAI | freigegebenes Realtime-Deployment und Embedding-Deployment in EU-Region |

Kein Production-Image verwendet `latest`.

## 5. Konfigurationsmanagement

- Eine `pydantic-settings`-Klasse je Prozess; fehlende Pflichtkonfiguration beendet den Start mit klarer Fehlermeldung.
- Secrets liegen verschlüsselt mit `sops` + `age`; Klartext-Secrets sind im Repo verboten.
- Produktionsdateien besitzen minimale Dateirechte und einen dedizierten Deploy-User.
- `gitleaks` läuft als CI-Gate.
- Provider-, Tarif- und Kostenlimits sind Konfiguration, nicht hartcodierte Geschäftslogik.

Pflichtwerte umfassen mindestens:

`DATABASE_URL`, `PUBLIC_BASE_URL`, Azure-/Twilio-Zugangsdaten, Signaturschlüssel für interne Service-Tokens, `ENVIRONMENT`, Sentry, SMTP sowie Tariflimits (`MAX_CALL_SECONDS`, `MAX_CONCURRENT_CALLS_PER_TENANT`, `DAILY_MINUTE_LIMIT`, `MONTHLY_MINUTE_LIMIT`, `MONTHLY_COST_LIMIT`).

## 6. Interne Kommunikationsmuster

### 6.1 Orchestrator → app

Endpunkte:

`POST /internal/tools/{search_knowledge|book_appointment|create_ticket|transfer_call}`

Verbindliche Absicherung:

1. Endpunkte sind nicht über Caddy öffentlich geroutet.
2. Kommunikation läuft in einem isolierten Compose-Netz.
3. Jeder Request trägt ein kurzlebiges signiertes Service-Token mit `iss`, `aud`, `iat`, `exp`, `jti`; Gültigkeit maximal 60 Sekunden.
4. `jti`/Request-ID und Zeitfenster werden gegen Replay geprüft.
5. Schlüsselrotation unterstützt überlappende aktive Schlüsselstände.
6. Ab horizontaler Skalierung ist mTLS Pflicht.
7. Tool-Antworten besitzen strikte Pydantic-Schemas, harte Timeouts und definierte Fallbacks.

Ein dauerhaft gültiger statischer Shared-Secret-Header allein ist nicht zulässig.

### 6.2 app → Worker/n8n

Domänenänderung und Outbox-Event werden in derselben Datenbanktransaktion geschrieben. Der Worker verarbeitet E-Mail, Ingestion und Post-Call-Jobs idempotent. n8n erhält ausschließlich explizite, versionierte Events und hat keinen direkten Datenbankzugriff.

### 6.3 Queue

Im Produktbeweis darf der Worker per DB-Outbox pollen. Redis/arq wird eingeführt, sobald parallele Jobs oder Durchsatz dies rechtfertigen. Job-Payloads enthalten ausschließlich IDs; fachliche Daten werden unter Tenant-Kontext aus PostgreSQL gelesen.

## 7. Netzwerk & Deployment-Topologie

- Staging und Production sind getrennt.
- Eingehend offen: 80/443 sowie eingeschränktes SSH.
- Twilio- und Stripe-Webhooks werden vor jeder Verarbeitung kryptografisch validiert.
- Interne Tool- und n8n-Endpunkte werden nie öffentlich exponiert.
- Datenbank und Redis sind nicht aus dem Internet erreichbar.
- Monitoring-Oberflächen sind nur per VPN/SSH-Tunnel oder gleichwertiger starker Zugriffskontrolle erreichbar.
- Servergröße wird anhand gemessener paralleler Calls, CPU, Speicher und Provider-Latenzen gewählt; keine überdimensionierte Startarchitektur ohne Messdaten.

## 8. Latenzbudget Gesprächspfad

| Abschnitt | Ziel P95 |
| :--- | :--- |
| Twilio → Orchestrator | ≤ 50 ms |
| Orchestrator → Realtime-API | ≤ 150 ms RTT |
| Realtime-Antwortbeginn nach Sprechpausen-Erkennung | ≤ 900 ms |
| Tool-Roundtrip Wissenssuche | ≤ 600 ms |
| Gesamtziel Antwortbeginn | ≤ 1,5 s |
| Gate-A-Freigabe während Pilot | ≤ 2,0 s |

Jeder Abschnitt erhält eine eigene Histogramm-Metrik. Optimierung erfolgt am gemessenen Engpass, nicht durch vorsorgliche zusätzliche Infrastruktur.

## 9. Kosten- und Kapazitätsbudgets

Jeder Anruf propagiert zusätzlich zur `call_id` eine Kosten- und Nutzungsdimension:

- Telefonie-Minuten
- Realtime-Minuten und geschätzte Modellkosten
- Tool-Aufrufe
- Nachrichtenkosten
- Tenant, Tarif und Abrechnungsperiode

Vor und während eines Gesprächs werden Parallelitäts-, Dauer-, Tages-, Monats- und Kostenlimits geprüft. Bei Anomalien degradiert der Tenant kontrolliert in einen sicheren Level-1-Modus. Bestehende Gespräche werden nicht hart getrennt, sondern zusammengefasst und kontrolliert beendet.

## 10. Erweiterungspunkte

- `TelephonyAdapter`: zweiter Provider erst nach Bedarf.
- `CalendarAdapter`: Cal.com zuerst; weitere Adapter nach zahlendem Bedarf.
- `CrmAdapter`: nur Interface bis zur ersten konkreten Integration.
- Qdrant: erst nach nachgewiesenem pgvector-Limit.
- Long-Term-Memory: nicht Bestandteil des MVP.

Die verbindlichen Produkt- und Betriebsgrenzen stehen in Dokument 09.