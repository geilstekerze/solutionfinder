# 02 – Datenmodell, Mandantentrennung & Migrationen

## 1. Grundprinzipien

1. **Eine Datenbank, strikte Mandantentrennung über PostgreSQL Row-Level-Security (RLS).** Jede mandantenbezogene Tabelle hat `tenant_id UUID NOT NULL` mit RLS-Policy. Die Anwendung setzt pro Verbindung/Transaktion `SET LOCAL app.tenant_id = '<uuid>'`. Es existiert **kein Codepfad**, der mandantenbezogene Tabellen ohne gesetzten Tenant-Kontext liest (erzwungen durch RLS, nicht nur durch Disziplin).
2. Zwei DB-Rollen: `fs_app` (RLS unterliegt, für alle Services) und `fs_admin` (nur Migrationen/Betrieb, `BYPASSRLS` nur hier).
3. Alle Zeitstempel `timestamptz`, UTC. Alle IDs `uuid` (v7 via App, sortierbar).
4. Jede Tabelle: `created_at`, `updated_at` (Trigger). Soft-Delete nur wo fachlich nötig (`deleted_at`), sonst hartes Löschen gemäß Löschkonzept (Dok. 06).

## 2. Schema (verbindlich; Alembic-Migration in WP2)

```sql
-- Erforderliche Erweiterungen (erste Migration, vor allen Tabellen)
CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS vector;

-- ===== Mandanten & Abo =====
CREATE TABLE tenants (
    id              uuid PRIMARY KEY,
    name            text NOT NULL,
    slug            text NOT NULL UNIQUE,          -- für Portal-URLs
    status          text NOT NULL CHECK (status IN
                    ('provisioning','active','suspended','terminated')),
    plan            text NOT NULL CHECK (plan IN ('level1','level2')),
    locale          text NOT NULL DEFAULT 'de-DE',
    persona_config  jsonb NOT NULL DEFAULT '{}',   -- Ton, Du/Sie, Begrüßung, Stimme
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE subscriptions (
    id                      uuid PRIMARY KEY,
    tenant_id               uuid NOT NULL REFERENCES tenants(id),
    stripe_customer_id      text NOT NULL,
    stripe_subscription_id  text NOT NULL UNIQUE,
    status                  text NOT NULL,          -- Spiegel des Stripe-Status
    current_period_end      timestamptz,
    created_at              timestamptz NOT NULL DEFAULT now(),
    updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (                                -- Portal-Logins des Kunden
    id            uuid PRIMARY KEY,
    tenant_id     uuid NOT NULL REFERENCES tenants(id),
    email         citext NOT NULL,
    password_hash text NOT NULL,                    -- argon2id
    role          text NOT NULL CHECK (role IN ('owner','member')),
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, email)
);

CREATE TABLE phone_numbers (
    id             uuid PRIMARY KEY,
    tenant_id      uuid NOT NULL REFERENCES tenants(id),
    e164           text NOT NULL UNIQUE,            -- +49...
    twilio_sid     text NOT NULL UNIQUE,
    status         text NOT NULL CHECK (status IN ('active','released')),
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== Anrufe =====
CREATE TABLE calls (
    id               uuid PRIMARY KEY,              -- = call_id in allen Logs
    tenant_id        uuid NOT NULL REFERENCES tenants(id),
    twilio_call_sid  text NOT NULL UNIQUE,
    from_e164        text NOT NULL,                 -- Pseudonymisierung: Dok. 06
    to_e164          text NOT NULL,
    started_at       timestamptz NOT NULL,
    answered_at      timestamptz,
    ended_at         timestamptz,
    outcome          text CHECK (outcome IN
                     ('completed','voicemail_fallback','transferred',
                      'caller_hangup','error_fallback')),
    summary          text,                          -- generierte Zusammenfassung
    intent           text,                          -- erkannte Anliegen-Kategorie
    metrics          jsonb NOT NULL DEFAULT '{}',   -- Latenzen, Token, Barge-ins
    created_at       timestamptz NOT NULL DEFAULT now(),
    updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE call_transcript_items (
    id          uuid PRIMARY KEY,
    tenant_id   uuid NOT NULL,
    call_id     uuid NOT NULL REFERENCES calls(id) ON DELETE CASCADE,
    seq         integer NOT NULL,                   -- Reihenfolge im Gespräch
    role        text NOT NULL CHECK (role IN ('caller','assistant','system','tool')),
    content     text NOT NULL,
    tool_name   text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    UNIQUE (call_id, seq)
);

-- ===== Tickets (Level 1) =====
CREATE TABLE tickets (
    id             uuid PRIMARY KEY,
    tenant_id      uuid NOT NULL REFERENCES tenants(id),
    call_id        uuid REFERENCES calls(id),
    status         text NOT NULL CHECK (status IN ('open','sent','failed','done')),
    category       text NOT NULL,                   -- z. B. 'rueckruf','auftrag','notfall'
    urgency        text NOT NULL CHECK (urgency IN ('low','normal','high')),
    caller_name    text,
    callback_e164  text,
    body           text NOT NULL,                   -- strukturierte Zusammenfassung
    delivery       jsonb NOT NULL DEFAULT '{}',     -- Kanäle + Zustellstatus
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now()
);

-- ===== Wissensbasis (RAG) =====
CREATE TABLE documents (
    id            uuid PRIMARY KEY,
    tenant_id     uuid NOT NULL REFERENCES tenants(id),
    filename      text NOT NULL,
    content_hash  text NOT NULL,                    -- sha256; Dedupe + Idempotenz
    mime_type     text NOT NULL,
    status        text NOT NULL CHECK (status IN
                  ('uploaded','processing','ready','failed')),
    error_detail  text,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, content_hash)
);

CREATE TABLE chunks (
    id           uuid PRIMARY KEY,
    tenant_id    uuid NOT NULL,
    document_id  uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    seq          integer NOT NULL,
    content      text NOT NULL,
    embedding    vector(1536) NOT NULL,
    token_count  integer NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, seq)
);
-- HNSW-Index; Filterung auf tenant_id geschieht IMMER zusätzlich per WHERE + RLS.
-- ACHTUNG Post-Filtering-Problem: Ein globaler HNSW-Index liefert die global
-- nächsten Nachbarn, die anschließende tenant_id-Filterung kann den Recall
-- drücken. Gegenmaßnahme (Pflicht): pgvector >= 0.8 einsetzen und bei
-- Retrieval-Queries iterative Index-Scans aktivieren:
--   SET LOCAL hnsw.iterative_scan = relaxed_order;
-- Der Recall@3-Eval (Dok. 04, Abschn. 6) misst genau diese Konfiguration.
-- Skalierungspfad bei großen Beständen: Partitionierung nach tenant_id
-- (Index je Partition) bzw. Qdrant-Migration (Dok. 04, Abschn. 7).
CREATE INDEX chunks_embedding_idx ON chunks
    USING hnsw (embedding vector_cosine_ops);
CREATE INDEX chunks_tenant_idx ON chunks (tenant_id);

-- ===== Termine =====
CREATE TABLE appointments (
    id             uuid PRIMARY KEY,
    tenant_id      uuid NOT NULL REFERENCES tenants(id),
    call_id        uuid REFERENCES calls(id),
    provider       text NOT NULL CHECK (provider IN ('calcom','calendly','m365')),
    external_id    text NOT NULL,                   -- ID beim Kalenderanbieter
    starts_at      timestamptz NOT NULL,
    ends_at        timestamptz NOT NULL,
    attendee_name  text,
    attendee_phone text,
    status         text NOT NULL CHECK (status IN ('booked','cancelled')),
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, provider, external_id)
);

-- ===== Integrationen (verschlüsselte Zugangsdaten) =====
CREATE TABLE integrations (
    id                uuid PRIMARY KEY,
    tenant_id         uuid NOT NULL REFERENCES tenants(id),
    kind              text NOT NULL,                -- 'calcom','calendly','m365','smtp','whatsapp'
    config            jsonb NOT NULL DEFAULT '{}',  -- unkritische Einstellungen
    credentials_enc   bytea,                        -- AES-GCM, Schlüssel via KMS/ENV (Dok. 06)
    status            text NOT NULL CHECK (status IN ('active','error','disabled')),
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, kind)
);

-- ===== Transaktionale Outbox =====
CREATE TABLE outbox_events (
    id            uuid PRIMARY KEY,
    tenant_id     uuid,                             -- nullable: Systemevents
    event_type    text NOT NULL,                    -- 'call.completed', ...
    payload       jsonb NOT NULL,
    status        text NOT NULL DEFAULT 'pending'
                  CHECK (status IN ('pending','delivered','failed')),
    attempts      integer NOT NULL DEFAULT 0,
    next_retry_at timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX outbox_pending_idx ON outbox_events (status, next_retry_at);

-- ===== Provisioning-State-Machine =====
CREATE TABLE provisioning_runs (
    id                 uuid PRIMARY KEY,
    tenant_id          uuid REFERENCES tenants(id),
    stripe_event_id    text NOT NULL UNIQUE,        -- Idempotenz-Anker
    state              text NOT NULL,               -- Dok. 05, Abschn. 3
    state_data         jsonb NOT NULL DEFAULT '{}',
    error_detail       text,
    created_at         timestamptz NOT NULL DEFAULT now(),
    updated_at         timestamptz NOT NULL DEFAULT now()
);

-- ===== Audit & Level-3-Vorbereitung =====
CREATE TABLE audit_log (
    id          uuid PRIMARY KEY,
    tenant_id   uuid,
    actor       text NOT NULL,                      -- 'system','user:<id>','admin:<id>'
    action      text NOT NULL,
    detail      jsonb NOT NULL DEFAULT '{}',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE memories (                             -- Level 3; im MVP ungenutzt
    id          uuid PRIMARY KEY,
    tenant_id   uuid NOT NULL REFERENCES tenants(id),
    subject     text NOT NULL,
    content     text NOT NULL,
    embedding   vector(1536),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
```

## 3. Row-Level-Security (verbindliches Muster)

Für **jede** Tabelle mit `tenant_id` (außer `tenants` selbst, s. u.):

```sql
ALTER TABLE calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE calls FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON calls
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
```

**Wichtig:** `current_setting` immer mit `missing_ok = true` (zweiter Parameter) aufrufen: Ist der Parameter nicht gesetzt, liefert die Funktion `NULL` statt eines Fehlers – der Vergleich ergibt `NULL` → keine Zeile sichtbar. So bleibt das Verhalten „ohne Kontext ist nichts lesbar" ein sauberes Fail-Closed ohne Query-Abbrüche (z. B. auf frischen Pool-Verbindungen).

- `tenants`: RLS mit Policy `id = current_setting('app.tenant_id')::uuid`; zusätzlich Policy für den System-Kontext (`current_setting('app.context') = 'system'`) für Provisioning/Nummern-Routing (nur von klar gekennzeichneten Systemcodepfaden gesetzt, z. B. „Rufnummer → Tenant auflösen" beim Anrufeingang).
- Der DB-Zugriffs-Layer in `fs_shared.db` stellt genau zwei Einstiege bereit:
  `tenant_session(tenant_id)` und `system_session(reason: str)` (loggt `reason` ins `audit_log`). Direkte Session-Erzeugung außerhalb dieser Helper ist per Lint-Regel (Import-Verbot) untersagt.
- **Isolationstest (Pflicht, WP2):** Automatisierter Test erzeugt 2 Mandanten mit Daten in allen Tabellen und beweist: Mit Tenant-A-Kontext ist keine Zeile von Tenant B les- oder schreibbar; ohne Kontext ist gar nichts lesbar.

## 4. Migrationsstrategie

1. Eine Alembic-Historie; jede Migration enthält getestetes `upgrade()` **und** `downgrade()`.
2. CI-Gate: frische DB → alle Migrationen hoch → alle runter → wieder hoch (Roundtrip-Test).
3. Migrationen laufen im Deploy **vor** dem Start neuer Container, als eigener Compose-Job (`migrate`), niemals implizit beim App-Start.
4. Nur additive Migrationen bei laufendem Betrieb (expand/contract-Muster): Spalte hinzufügen → Code deployen → alte Spalte in späterem Release entfernen.

## 5. Redis-Nutzung (abschließend definiert)

| Key-Muster | Inhalt | TTL |
| :--- | :--- | :--- |
| `call:{call_id}:state` | serialisierter Call-State (Recovery/Debugging) | 1 h |
| `ratelimit:{scope}:{id}` | Token-Bucket-Zähler | ≤ 1 min |
| `arq:*` | Job-Queue ingestion-worker | Queue-verwaltet |

**Regel:** Redis-Inhalte sind jederzeit verlustfähig; kein Datum existiert nur in Redis.
