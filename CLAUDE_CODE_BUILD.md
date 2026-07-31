# Claude-Code-Bauauftrag: Frau Schmidt MVP

## Auftrag

Baue in diesem Repository eine lauffähige, getestete und deploybare MVP-Version der mandantenfähigen KI-Telefonassistenz **„Frau Schmidt“**.

Arbeite autonom. Stelle nur dann eine Rückfrage, wenn eine externe Zugangsinformation zwingend fehlt und weder Mock noch lokale Ersatzimplementierung möglich ist. Triff Detailentscheidungen nach den verbindlichen Regeln in `docs/frau-schmidt-plan/`.

## Verbindliche Lesereihenfolge

1. `CLAUDE_CODE_BUILD.md`
2. `docs/frau-schmidt-plan/09-mvp-optimierung-produktbetrieb.md`
3. `docs/frau-schmidt-plan/08-arbeitspakete.md`
4. `docs/frau-schmidt-plan/README.md`
5. `docs/frau-schmidt-plan/01-architektur.md` bis `07-qualitaet-betrieb.md`

Bei Widersprüchen gilt genau diese Reihenfolge.

## Ziel dieses Bauauftrags

Implementiere ausschließlich **WP0 bis WP4** als vollständigen vertikalen Produktbeweis.

Das Ergebnis muss folgenden realen Ablauf beherrschen:

1. Ein Anrufer ruft eine konfigurierte Twilio-Rufnummer an.
2. Der Anruf wird einem Mandanten zugeordnet.
3. Frau Schmidt begrüßt den Anrufer auf Deutsch.
4. Sie führt ein natürliches Audio-zu-Audio-Gespräch über Azure OpenAI Realtime.
5. Sie erkennt Unterbrechungen und stoppt ihre Ausgabe zuverlässig.
6. Sie erfasst mindestens Name, Rückrufnummer, Anliegen, Dringlichkeit und gewünschte Reaktion.
7. Sie legt daraus ein strukturiertes Ticket an.
8. Das Ticket wird unabhängig von n8n per E-Mail zugestellt.
9. Bei Ausfällen erfolgt eine hörbare Fallback-Ansage oder Voicemail. Kein Anruf endet stumm.
10. Gespräch, Ticket, Status, Kosten-Proxy und technische Metriken werden persistiert.

## Nicht Teil dieses Bauauftrags

Noch nicht implementieren:

- Stripe Checkout und vollautomatisches Kunden-Provisioning
- Bezahlpläne und Rechnungslogik
- n8n
- Kalenderbuchung
- WhatsApp-Zustellung
- vollständiges Kundenportal
- Qdrant
- Kubernetes
- mehrere Telefonieanbieter
- CRM-Integrationen
- Long-Term-Memory
- horizontale Skalierung
- Level 3 oder Level 4

Schnittstellen dürfen vorbereitet werden, aber es darf kein ungenutzter Platzhalter-Code entstehen.

## Technischer Zielstack

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy 2
- Alembic
- PostgreSQL 16 mit `citext` und `pgvector`
- Jinja2 und HTMX nur für minimale interne Ansichten
- Twilio Programmable Voice und bidirektionale Media Streams
- Azure OpenAI Realtime API
- `asyncio` und `websockets`
- `structlog`
- Prometheus-Metriken
- Sentry optional per Konfiguration
- Docker Compose
- Caddy
- `uv` als Paket- und Workspace-Manager
- `pytest`, `mypy --strict`, `ruff`

Alle Abhängigkeiten müssen exakt gepinnt und in `uv.lock` festgehalten werden.

## Zielarchitektur des MVP

Nur zwei langlebige Anwendungsprozesse:

### 1. `app`

Verantwortlich für:

- Twilio-Voice-Webhooks
- interne Tool-Endpunkte
- Ticket-Persistenz
- direkte Ticket-E-Mail aus der Outbox
- minimale Admin-/Debug-Seiten
- Healthchecks
- Datenbankzugriff
- Mandanten- und Rufnummernauflösung

### 2. `voice-orchestrator`

Verantwortlich für:

- Twilio Media Streams
- Azure-Realtime-WebSocket
- Audio-Bridge
- Call-State-Machine
- Barge-in
- Tool-Aufrufe
- Fallback-Verhalten
- Call-spezifische Metriken

PostgreSQL, Caddy und optional Redis laufen als Infrastrukturcontainer. Redis darf im ersten Stand nur verwendet werden, wenn es für Rate-Limits oder Replay-Schutz konkret benötigt wird. Persistente Geschäftsdaten dürfen niemals ausschließlich in Redis liegen.

## Verbindliche Repository-Struktur

```text
.
├── pyproject.toml
├── uv.lock
├── .env.example
├── README.md
├── packages/
│   └── shared/
│       └── fs_shared/
│           ├── config.py
│           ├── db/
│           ├── models/
│           ├── security/
│           ├── telemetry/
│           ├── telephony/
│           ├── realtime/
│           ├── mail.py
│           └── outbox.py
├── services/
│   ├── app/
│   │   ├── app/
│   │   └── tests/
│   └── voice_orchestrator/
│       ├── app/
│       └── tests/
├── migrations/
├── tests_e2e/
├── infra/
│   ├── compose/
│   ├── caddy/
│   └── scripts/
├── docs/
│   ├── adr-log.md
│   ├── abnahme/
│   └── runbooks/
└── .github/workflows/
```

## Umsetzungsreihenfolge

### Phase 1 – Fundament

1. Workspace und Paketstruktur anlegen.
2. Konfiguration mit `pydantic-settings` implementieren.
3. `.env.example` vollständig erstellen.
4. Dockerfiles als Multi-Stage-Builds mit Non-Root-User erstellen.
5. Docker Compose für lokale Entwicklung erstellen.
6. `/healthz` und `/readyz` für beide Services implementieren.
7. CI mit `ruff`, `mypy --strict`, Unit- und Integrationstests einrichten.

### Phase 2 – Datenmodell

Implementiere mindestens:

- `tenants`
- `phone_numbers`
- `calls`
- `call_events`
- `transcript_segments`
- `tickets`
- `outbox_events`
- `usage_counters`
- `audit_log`

Regeln:

- UUIDs
- `timestamptz`
- Alembic-Migrationen
- `CREATE EXTENSION IF NOT EXISTS citext`
- `CREATE EXTENSION IF NOT EXISTS vector`
- Row-Level-Security für alle mandantenbezogenen Tabellen
- `current_setting('app.tenant_id', true)` verwenden
- ohne Tenant-Kontext sind keine Mandantendaten lesbar
- separate eingeschränkte Rolle oder Funktion für Rufnummer-zu-Mandant-Auflösung
- kein allgemeiner, frei gesetzter Systemkontext mit Vollzugriff

### Phase 3 – Twilio-Eingang

Implementiere:

- `POST /twilio/voice`
- Twilio-Signaturprüfung
- Rufnummer-zu-Mandant-Auflösung
- Anlage des Call-Datensatzes
- TwiML mit `<Connect><Stream>`
- kurzlebiges signiertes Stream-Token
- statisches Notfall-TwiML bei Datenbankausfall
- definierte Ansage für unbekannte Rufnummern
- `FakeTwilioMediaClient`
- Echo-Modus ausschließlich hinter Test-Feature-Flag

### Phase 4 – Realtime-Bridge

Implementiere:

- Azure-Realtime-Client
- Session-Konfiguration für deutsche Sprache
- bidirektionale G.711-μ-law-Audio-Weiterleitung
- vollständige Call-State-Machine
- Barge-in mit `response.cancel`, Audio-Clear und konsistentem Kontext
- Transkript-Persistenz
- Reconnect mit begrenzten Versuchen
- Timeout-Regeln
- hörbare Fallback-Voicemail
- `FakeRealtimeServer`

### Phase 5 – Ticket-Erfassung

Implementiere ein strikt typisiertes Tool `create_ticket`.

Pflichtfelder:

- `caller_name`
- `callback_number`
- `subject`
- `summary`
- `urgency`
- `requested_action`
- `tenant_id`
- `call_id`

Regeln:

- Pydantic-Schema
- serverseitige Validierung
- idempotente Erstellung
- Zuordnung zum Call
- Outbox-Event `ticket.created`
- direkter E-Mail-Worker ohne n8n
- Retry mit Backoff
- Zustellstatus persistieren
- bei endgültigem Fehler Alert und sichtbarer Status

## Interne Service-Authentifizierung

Kein dauerhaftes einfaches Shared-Token.

Implementiere:

- kurzlebige signierte Service-Tokens
- `iss`, `aud`, `iat`, `exp`, `jti`
- maximale Lebensdauer 60 Sekunden
- Replay-Schutz über `jti`
- Request-ID
- Timestamp-Prüfung
- isoliertes Compose-Netzwerk
- Rate-Limits auf internen Tool-Endpunkten

mTLS ist für Phase 2 vorbereitet, aber noch nicht verpflichtend umzusetzen.

## Kosten- und Missbrauchsschutz

Von Anfang an implementieren:

- maximale Gesprächsdauer pro Anruf
- maximale parallele Anrufe pro Mandant
- Tages- und Monatsminuten je Mandant
- globales Tageskostenlimit
- mandantenbezogenes Kostenlimit
- Abuse-Erkennung für auffällige Anrufmuster
- Metriken für Twilio-Minuten, Realtime-Minuten und geschätzte variable Kosten

Bei Grenzerreichung:

- kein stummer Abbruch
- neutrale hörbare Ansage
- kontrolliertes Gesprächsende oder Voicemail
- Audit-Log-Eintrag

## Mindestkonfiguration

Die `.env.example` muss mindestens enthalten:

```text
ENVIRONMENT=
PUBLIC_BASE_URL=
DATABASE_URL=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_DEFAULT_NUMBER=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_REALTIME_DEPLOYMENT=
INTERNAL_TOKEN_SIGNING_KEY=
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=
SENTRY_DSN=
MAX_CALL_DURATION_SECONDS=
MAX_CONCURRENT_CALLS_PER_TENANT=
DEFAULT_MONTHLY_MINUTES=
GLOBAL_DAILY_COST_LIMIT_EUR=
```

Secrets dürfen nie im Repository stehen.

## Testpflicht

### Unit-Tests

Mindestens für:

- Call-State-Machine
- Barge-in
- Token-Signierung und Replay-Schutz
- Ticket-Schema
- Outbox-Retry
- Kostenlimits
- Rufnummernnormalisierung
- Twilio-Signaturprüfung

### Integrationstests

Mit Testcontainers:

- PostgreSQL-Migrationen up/down/up
- RLS-Isolation mit zwei Mandanten
- kein Datenzugriff ohne Tenant-Kontext
- Ticket plus Outbox in einer Transaktion
- Outbox-Retry nach temporärem SMTP-Ausfall

### Contract-Tests

- Fake Twilio Media Stream
- Fake Azure Realtime Server
- Happy Path
- Barge-in
- Realtime-Verbindungsabbruch
- Reconnect erfolgreich
- Reconnect endgültig fehlgeschlagen
- Fallback-Voicemail
- Tool-Timeout

### E2E lokal

Ein reproduzierbares Skript muss ohne echte Cloud-Zugänge einen kompletten simulierten Anruf ausführen:

```text
FakeTwilio → voice-orchestrator → FakeRealtime → create_ticket → Postgres → FakeSMTP
```

Das E2E-Ergebnis muss automatisiert prüfen:

- Call wurde angelegt
- Transkript wurde gespeichert
- Ticket wurde erstellt
- E-Mail wurde zugestellt
- Call endete kontrolliert
- keine fremden Mandantendaten wurden gelesen

## Qualitäts-Gates

Vor Abschluss müssen alle folgenden Befehle erfolgreich laufen:

```bash
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict packages services
uv run pytest -q
Docker compose -f infra/compose/docker-compose.local.yml config
Docker compose -f infra/compose/docker-compose.local.yml up -d --build
```

Verwende in echten Dateinamen und Befehlen selbstverständlich `docker compose` in Kleinschreibung.

Mindestanforderungen:

- keine `TODO`-Platzhalter
- keine leeren Implementierungen
- keine hartcodierten Secrets
- keine `latest`-Tags
- keine ungetestete Kernlogik
- keine stummen Exceptions
- keine direkte DB-Session-Erzeugung außerhalb des gemeinsamen DB-Layers
- Kernlogik mindestens 90 % Branch-Coverage
- Gesamtprojekt mindestens 80 % Coverage

## Abnahme-Gate A

WP4 gilt erst als abgeschlossen, wenn dokumentiert ist:

- mindestens 100 automatisierte oder Pilot-Testanrufe
- mindestens 98 % kontrollierte Gesprächsabschlüsse
- kein stummer Anruf
- P95 erste Antwort höchstens 1,5 Sekunden unter realistischen Bedingungen
- P95 Barge-in höchstens 400 Millisekunden
- Fallback-Quote höchstens 2 % ohne absichtlich erzeugte Ausfälle
- keine Mandantenüberschneidung
- geschätzte variable Kosten bei normaler Nutzung höchstens 35 % des Netto-Tarifumsatzes

Lege den Bericht unter `docs/abnahme/GATE_A.md` ab. Wo echte Cloud-Zugänge fehlen, liefere zunächst einen reproduzierbaren synthetischen Bericht und markiere ausschließlich die echten Live-Messungen als noch extern auszuführen.

## Dokumentation

Erstelle oder aktualisiere:

- Root-`README.md` mit lokalem Setup in höchstens zehn Schritten
- `docs/adr-log.md`
- `docs/abnahme/WP0.md` bis `WP4.md`
- `docs/abnahme/GATE_A.md`
- Runbook für Realtime-Ausfall
- Runbook für DB-Ausfall
- Runbook für Kostenanomalie
- Runbook für Secrets-Rotation

## Arbeitsweise

- Implementiere in kleinen, logisch getrennten Commits.
- Nach jeder Phase alle relevanten Tests ausführen.
- Fehler selbstständig beheben.
- Keine Architektur austauschen, nur weil eine andere Technologie bequemer erscheint.
- Keine Erweiterungen außerhalb des Scopes bauen.
- Bestehende Planungsdokumente nicht löschen.
- Änderungen an verbindlichen Entscheidungen ausschließlich in `docs/adr-log.md` dokumentieren.

## Abschlussbericht

Am Ende liefere:

1. Zusammenfassung der implementierten Funktionen.
2. Liste aller geänderten und neuen Dateien.
3. Exakte Startbefehle.
4. Testergebnisse und Coverage.
5. Noch benötigte externe Zugangsdaten.
6. Bekannte Grenzen.
7. Sicherheitsrelevante Entscheidungen.
8. Kosten- und Skalierungsannahmen.
9. Ergebnis von Gate A oder klar markierte noch ausstehende Live-Messungen.

Der Auftrag ist erst abgeschlossen, wenn das Repository lokal reproduzierbar startet und alle ohne externe Cloud-Zugänge ausführbaren Qualitäts-Gates grün sind.