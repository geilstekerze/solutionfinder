# 07 – Qualitätssicherung, CI/CD & Betrieb

## 1. Teststrategie (Pyramide, alle Ebenen verpflichtend)

| Ebene | Werkzeug | Umfang / Regeln |
| :--- | :--- | :--- |
| Statisch | `ruff` (inkl. Verbot `except: pass`), `mypy --strict`, `gitleaks`, `pip-audit`, `trivy` (Images) | 0 Findings = Merge-Bedingung |
| Unit | `pytest` | Kernlogik (State-Machine, Chunking, Provisioning-Transitions, Fristenlogik, Tool-Schemas) ≥ 90 % Branch-Coverage; Gesamt ≥ 80 % |
| Integration | `pytest` + `testcontainers` (Postgres+pgvector, Redis) | DB-Layer inkl. RLS-Isolationstests, Outbox-Dispatcher, arq-Jobs, Alembic-Roundtrip |
| Contract/Mocks | **`FakeRealtimeServer`** (eigener WS-Server, spielt aufgezeichnete Event-Sequenzen ab), **`FakeTwilioMediaClient`** (sendet echte μ-law-Frames aus WAV-Fixtures), `respx` für Stripe/Twilio/Kalender-HTTP | Orchestrator wird vollständig ohne echte Cloud-Dienste getestet: Happy Path, Barge-in, alle Zeilen der Degradations-Matrix (Dok. 03, Abschn. 8) |
| E2E (Staging) | Skript `tests_e2e/live_call_test.py`: ruft per Twilio-API die Staging-Nummer an, spielt TTS-generierte Testsätze ein, prüft Transkript/Ticket/Termin in der DB | Läuft vor jedem Production-Deploy + nachts (Cron) |
| Evals | RAG-Evals (Dok. 04, Abschn. 6) + Gesprächs-Evals: 15 Szenario-Skripte (Terminwunsch, FAQ, Notfall, Widerspruch zur Verarbeitung, Nuschel-Kontext) gegen FakeRealtime-Aufzeichnungen bzw. periodisch live | Release-Gate: keine Regression gegen Vorversion |
| Last | Lastskript mit 50 parallelen synthetischen Media-Streams gegen Staging | P95-Latenzbudgets (Dok. 01, Abschn. 8) halten |
| Chaos | Testplan WP11: gezieltes Stoppen von n8n/Redis/Realtime-Mock, DB-Failover-Simulation | Verhalten exakt gemäß Degradations-Matrix |

## 2. CI-Pipeline (GitHub Actions, `ci.yml` – jeder PR)

```
lint+type → unit → integration (testcontainers) → build images → trivy → coverage-gate
```
Merge in `main` nur bei grünem Pflicht-Check. `main` ist geschützt (keine Direkt-Pushes).

## 3. CD-Pipeline (`deploy.yml`)

```
merge in main
  → build+push Images (Registry, Tag = git SHA, zusätzlich Digest)
  → deploy staging (ssh: compose pull + migrate-job + up)
  → Staging-Smoke: /healthz aller Services + E2E-Live-Call-Test
  → manuelles Approval-Gate (GitHub Environment "production")
  → deploy production (gleiches Skript)
  → Production-Smoke: Canary-Mandant-Testanruf (automatisiert) + Healthchecks
  → bei Smoke-Fehlschlag: automatischer Rollback auf vorherigen SHA (Skript hält
    letzte 3 Releases vor) + Alert
```
Deploy-Skript (`infra/scripts/deploy.sh`) ist idempotent und einziger Deployment-Weg.

## 4. Monitoring & Alerting

**Dashboards (Grafana, als JSON versioniert):** (1) Anruf-Übersicht (aktive Calls, Outcomes, Latenz-Histogramme, Barge-in-Zeiten), (2) Fehler & Fallbacks, (3) Provisioning & Billing, (4) Infrastruktur (CPU/RAM/Disk, DB-Verbindungen, Redis), (5) Kosten-Proxy (Realtime-Minuten, Token, Twilio-Minuten je Mandant).

**Alerts (Prometheus Alertmanager → E-Mail + Pushover/Slack):**

| Alert | Bedingung | Schwere |
| :--- | :--- | :--- |
| Anrufannahme gestört | `fs_fallback_total{reason="connect_timeout"}` > 3 in 5 min | kritisch |
| Latenzbudget verletzt | `fs_first_response_seconds` P95 > 1,5 s über 10 min | hoch |
| Harte Abbrüche | `fs_call_outcome_total{outcome="error_fallback"}` > 0 in 15 min | kritisch |
| Outbox-Stau | pending > 100 oder ältestes pending > 30 min | hoch |
| Provisioning stuck | `provisioning_runs.state='stuck'` > 0 | kritisch |
| Disk/DB | Disk > 80 %, DB-Connections > 80 % Pool | hoch |
| Zertifikat/Erreichbarkeit | Blackbox-Probe auf 443 + WSS fehlschlägt | kritisch |
| Ingestion hängt | Dokument > 15 min in `processing` | mittel |

Sentry fängt alle unbehandelten Exceptions aller Services (Release-Tagging = git SHA).

## 5. SLOs (öffentlich intern, Grundlage für Alert-Feintuning)

1. Anrufannahme-Erfolgsquote (angenommen + korrekt behandelt, inkl. geplanter Fallback): ≥ 99,5 %/Monat.
2. Erste-Antwort-Latenz P95 ≤ 1,5 s; Barge-in P95 ≤ 400 ms.
3. Ticket-Zustellung ≤ 5 min nach Gesprächsende (P95).
4. Provisioning P95 ≤ 5 min, Maximum ≤ 10 min.
5. Portal-Verfügbarkeit ≥ 99,5 %.

## 6. Backups & Desaster-Recovery

- Postgres, zweigleisig: (a) **PITR-Strategie (primär):** physisches Base-Backup täglich via `wal-g backup-push` + kontinuierliche WAL-Archivierung (`wal-g`) auf Hetzner Storage Box (verschlüsselt) – WAL-Replay setzt zwingend auf dem physischen Base-Backup auf, nicht auf einem Dump. (b) **Logischer Dump (sekundär):** täglicher `pg_dump` (Custom-Format) als portables, unabhängig wiederherstellbares Zweitbackup. RPO ≤ 5 min (via WAL), RTO ≤ 60 min.
- Uploads-Verzeichnis: täglicher inkrementeller Sync (restic, verschlüsselt).
- **Restore-Test ist Pflicht:** monatlicher automatisierter Job stellt Backup auf Staging wieder her und führt Smoke-Tests aus; ohne bestandenen Restore-Test gilt das Backup als nicht existent.
- Server-Totalausfall-Runbook: neuen Hetzner-Server aus Cloud-Init-Snapshot provisionieren, Compose + Secrets deployen, Restore, Twilio-Webhook-URLs zeigen auf DNS-Namen (nur DNS-Umschwenk nötig).

## 7. Runbooks (in `docs/runbooks/`, je 1 Seite, vor Go-Live vorhanden)

`realtime-api-ausfall.md`, `twilio-stoerung.md`, `db-restore.md`, `rollback.md`, `secrets-rotation.md`, `provisioning-stuck.md`, `nummer-portierung-kuendigung.md`, `kosten-anomalie.md`.

## 8. Betriebs-Routinen

- Wöchentlich: Dependency-PR reviewen, Fallback-Quote & Evals ansehen, Kosten je Mandant prüfen.
- Monatlich: Restore-Test-Report, Security-Scan-Report, SLO-Review.
- Kosten-Schutz: Budget-Alerts bei Azure und Twilio; pro Mandant Monats-Kontingent an Gesprächsminuten je Plan (Überschreitung → Ansage-Hinweis + Upsell-Mail statt harter Sperre; Notfall-Tickets funktionieren immer).
