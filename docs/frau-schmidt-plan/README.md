# Umsetzungsplan „Frau Schmidt" – DSGVO-konforme KI-Telefonassistenz für KMU

**Version:** 1.0 · **Stand:** 2026-07-14 · **Status:** Verbindliche Umsetzungsgrundlage

Dieser Plan ist so geschrieben, dass ein KI-Modell (oder ein Entwicklungsteam) ihn **ohne Rückfragen deterministisch umsetzen kann**. Alle Entscheidungen sind getroffen, alle Schnittstellen spezifiziert, alle Arbeitspakete haben testbare Abnahmekriterien. Oberste Prioritäten: **Stabilität, Zuverlässigkeit, Null-Fehler-Toleranz im Kernpfad (Telefonat)**.

---

## 1. Dokumentstruktur (Lesereihenfolge für das umsetzende Modell)

| Nr. | Dokument | Inhalt |
| :-- | :--- | :--- |
| 00 | `README.md` (dieses Dokument) | Ziele, Prinzipien, Entscheidungen (ADRs), Phasenmodell, Arbeitsanweisungen |
| 01 | [`01-architektur.md`](01-architektur.md) | Systemarchitektur, Tech-Stack mit Versionen, Repo-Struktur, Konfiguration |
| 02 | [`02-datenmodell.md`](02-datenmodell.md) | Vollständiges PostgreSQL-Schema, Mandantentrennung (RLS), Migrationen |
| 03 | [`03-voice-orchestrator.md`](03-voice-orchestrator.md) | Kernkomponente: Telefonie ↔ Realtime-API-Bridge, State-Machine, Fallbacks |
| 04 | [`04-rag-pipeline.md`](04-rag-pipeline.md) | Dokumenten-Ingestion, Embeddings, Retrieval, Qualitätssicherung |
| 05 | [`05-integrationen-onboarding.md`](05-integrationen-onboarding.md) | Stripe, Provisioning, n8n, Kalender, E-Mail/WhatsApp-Tickets |
| 06 | [`06-sicherheit-dsgvo.md`](06-sicherheit-dsgvo.md) | TOMs, Verschlüsselung, Einwilligung, Löschkonzept, Auftragsverarbeiter |
| 07 | [`07-qualitaet-betrieb.md`](07-qualitaet-betrieb.md) | Teststrategie, CI/CD, Monitoring, SLOs, Runbooks, Rollback |
| 08 | [`08-arbeitspakete.md`](08-arbeitspakete.md) | **Sequenzielle Arbeitspakete WP0–WP11 mit Abnahmekriterien** |

**Regel:** Bei Widerspruch zwischen Dokumenten gilt die Reihenfolge: `08-arbeitspakete.md` > Fachdokument (01–07) > dieses README. Existiert zu einer Detailfrage keine Festlegung, gilt Abschnitt 5 („Default-Entscheidungsregeln").

---

## 2. Produktziel (Kurzfassung)

„Frau Schmidt" ist eine mandantenfähige SaaS-Telefonassistentin für KMU:

- **Level 1 – Intelligenter Anrufbeantworter:** Anrufannahme, Anliegen-Erfassung, strukturiertes Ticket per E-Mail/WhatsApp an das Team.
- **Level 2 – Vorzimmerdame (MVP):** zusätzlich FAQ-Beantwortung aus Kundendokumenten (RAG), Terminbuchung in Echtzeit, Anrufweiterleitung.
- **Level 3/4 – Chef-Sekretärin / Fach-Agenten:** CRM-Anbindung, Long-Term-Memory, Fach-Workflows (nach MVP, hier nur als Erweiterungspfad berücksichtigt).

Kaufabschluss und Bereitstellung laufen vollautomatisch: Stripe-Zahlung → automatisches Provisioning → Kunde ist in < 10 Minuten live.

**Dieser Plan liefert Level 1 + Level 2 produktionsreif inkl. automatisiertem Onboarding.** Level 3/4 sind architektonisch vorbereitet (Erweiterungspunkte sind markiert), werden aber nicht implementiert.

---

## 3. Verbindliche Architektur-Entscheidungen (ADRs)

Jede Entscheidung ist final. Das umsetzende Modell darf sie nicht ändern, ohne dass der Auftraggeber es explizit verlangt.

### ADR-1: Sprache & Laufzeit
**Python 3.12** für alle Backend-Services (Voice-Orchestrator, API, Ingestion-Worker). Ein einziges Ökosystem minimiert Fehlerquellen. Kein Node.js im Backend. Portal-Frontend: serverseitig gerendertes **FastAPI + Jinja2 + HTMX** (kein SPA-Framework) – weniger bewegliche Teile, kein separates Build-Toolchain-Risiko.

### ADR-2: Telefonie-Anbindung
**Twilio Programmable Voice mit Media Streams** (bidirektionales Audio über WebSocket, G.711 μ-law, 8 kHz) als primärer Weg. Begründung: dokumentiertes, erprobtes Streaming-Interface; kein eigener SIP-Stack (Asterisk/FreeSWITCH entfällt → massiv weniger Fehlerpotenzial). Deutsche Rufnummern über Twilio, Media-Region `de1` (Frankfurt), Auftragsverarbeitungsvertrag + EU-SCCs abschließen (siehe Dok. 06).
Die Telefonie ist hinter einem **Adapter-Interface** (`TelephonyAdapter`) gekapselt; ein späterer Wechsel auf sipgate/eigenen SIP-Trunk (volle Datenresidenz) ist als Phase-2-Härtung vorgesehen, ohne den Kern zu ändern.

### ADR-3: Sprach-KI
**Azure OpenAI Realtime API** (Modell-Deployment `gpt-realtime`), Region **Sweden Central** (EU). Audio-zu-Audio (kein STT→LLM→TTS-Umweg im Gesprächspfad). Audioformat Ende-zu-Ende `g711_ulaw` (Twilio-nativ, keine Transcodierung → weniger Latenz, weniger Fehler). Function-Calling für Terminbuchung, Ticket-Erfassung, Weiterleitung, Wissensabfrage.

### ADR-4: Datenhaltung
**PostgreSQL 16 + pgvector** als einziges Datensystem für MVP (relationale Daten UND Vektoren). Begründung Null-Fehler-Toleranz: ein System weniger (kein Qdrant), transaktionale Konsistenz zwischen Dokument-Metadaten und Vektoren, Mandantentrennung über **Row-Level-Security** in einer Datenbank statt über zwei Systeme hinweg. Qdrant ist als dokumentierter Migrationspfad ab > 200 Mandanten vorgesehen (Dok. 04, Abschn. 7). Zusätzlich **Redis 7** ausschließlich für flüchtigen Call-State und Rate-Limiting (Verlust von Redis-Daten darf nie Datenverlust bedeuten).

### ADR-5: Orchestrierung
**n8n (self-hosted)** ausschließlich für asynchrone Post-Call- und Onboarding-Automatisierung. **Harte Regel: Der Live-Gesprächspfad hat keine Abhängigkeit zu n8n.** Fällt n8n aus, funktionieren Telefonate vollständig weiter; Events werden in einer Outbox-Tabelle gepuffert und nachgeholt.

### ADR-6: Infrastruktur & Deployment
**Hetzner Cloud** (EU, bestehende Ressourcen), **Docker Compose** mit Healthchecks, **Caddy 2** als Reverse Proxy (automatisches TLS). Kein Kubernetes im MVP (Komplexität ohne Bedarf). Deployments ausschließlich über CI-Pipeline (GitHub Actions → SSH), niemals manuell. Zwei Umgebungen: `staging` und `production` auf getrennten Servern.

### ADR-7: Zahlungen & Provisioning
**Stripe Checkout + Billing** (Subscriptions), Webhook-getriebenes Provisioning mit **Idempotenz-Keys** (jedes Stripe-Event wird genau einmal verarbeitet, Wiederholungen sind wirkungslos). Provisioning ist eine idempotente State-Machine in der API (nicht in n8n), n8n übernimmt nur Benachrichtigungen.

### ADR-8: Beobachtbarkeit
Strukturierte JSON-Logs (ein Schema für alle Services), **Prometheus + Grafana + Loki** (self-hosted, EU) und **Sentry (EU-Region)** für Fehler-Tracking. Jeder Anruf erhält eine `call_id`, die durch alle Systeme propagiert wird (Logs, Metriken, DB, n8n).

### ADR-9: Kein Audio-Mitschnitt per Default
Es wird standardmäßig **kein Gesprächsaudio gespeichert**, nur Transkripte + strukturierte Ergebnisse. Audio-Aufzeichnung ist ein Opt-in-Feature pro Mandant mit dokumentierter Rechtsgrundlage (Dok. 06).

---

## 4. Null-Fehler-Strategie (gilt für jedes Arbeitspaket)

1. **Typisierung erzwungen:** `mypy --strict` und `ruff` laufen in CI; Merge nur bei 0 Fehlern.
2. **Testpflicht:** Kernlogik ≥ 90 % Branch-Coverage; jedes Arbeitspaket definiert konkrete Tests, die grün sein müssen (Dok. 07 + 08).
3. **Der Gesprächspfad degradiert, er fällt nie hart aus:** Jede externe Abhängigkeit (Realtime API, Kalender, DB) hat definiertes Fallback-Verhalten (Dok. 03, Abschn. 8). Schlimmster Fall ist immer: freundliche Ansage + Voicemail-Aufnahme + asynchrones Ticket – niemals ein stummer oder abgebrochener Anruf.
4. **Idempotenz überall:** Webhooks (Stripe, Twilio, n8n) sind wiederholbar ohne Doppelwirkung; Provisioning ist eine wiederaufsetzbare State-Machine.
5. **Keine stillen Fehler:** Jede abgefangene Exception erzeugt ein Sentry-Event + strukturiertes Log; leere `except:`-Blöcke sind verboten (Lint-Regel).
6. **Migrations-Disziplin:** Schemaänderungen nur über Alembic-Migrationen, nie manuell; jede Migration hat einen getesteten Downgrade-Pfad.
7. **Staging-Gate:** Jedes Release durchläuft Staging inkl. automatisiertem Test-Telefonat, bevor Production deployt wird (Dok. 07, Abschn. 5).
8. **Canary-Mandant:** In Production existiert ein interner Test-Mandant; nach jedem Deploy läuft ein echter Testanruf gegen diesen Mandanten (Smoke-Test), sonst automatischer Rollback.

---

## 5. Default-Entscheidungsregeln für das umsetzende Modell

Wenn eine Detailfrage in den Dokumenten nicht geregelt ist:

1. Wähle die Option mit **weniger externen Abhängigkeiten**.
2. Wähle die Option, die bei Teilausfall **degradiert statt abbricht**.
3. Wähle die **explizite** Variante (Konfiguration, Typen, Schemas) statt Konvention/Magie.
4. Schreibe erst den Test, dann die Implementierung, wenn Verhalten unklar erscheint.
5. Dokumentiere die getroffene Entscheidung als Kommentar im relevanten ADR-Abschnitt (neue ADR-Nummer, Datei `docs/adr-log.md` im Zielrepo).

**Verboten:** Platzhalter-Code („TODO: später implementieren"), auskommentierte Codeblöcke, hartcodierte Secrets, Abhängigkeiten ohne Versions-Pinning, `latest`-Docker-Tags.

---

## 6. Phasenmodell (Zuordnung zur Roadmap des Konzepts)

| Phase (Konzept) | Arbeitspakete (Dok. 08) | Ergebnis |
| :--- | :--- | :--- |
| Phase 1 – Prototyping (Level-2-MVP) | WP0–WP4 | Latenzarmes Testgespräch über echte Rufnummer inkl. Barge-in |
| Phase 2 – Infrastruktur & RAG | WP5–WP7 | Mandantengetrennte Wissensbasis + Terminbuchung + Tickets |
| Phase 3 – Checkout & Onboarding | WP8–WP10 | Stripe → automatisches Provisioning → Kunde live < 10 min |
| Phase 4 – Launch & Skalierung | WP11 | Lasttest, DSGVO-Abnahme, Go-Live unter promptwerker.de |

Die Arbeitspakete sind **strikt sequenziell** definiert (jedes WP baut auf dem vorherigen auf und endet mit einem überprüfbaren, deploybaren Zustand).

---

## 7. Erfolgskriterien des Gesamtprojekts (Abnahme)

Das Projekt gilt als erfolgreich umgesetzt, wenn alle folgenden Punkte nachweisbar erfüllt sind:

1. Ein Anruf auf eine Mandanten-Rufnummer wird in **< 2 s** angenommen; die erste Antwort der Assistentin beginnt **< 1,5 s** nach Ende der Nutzeräußerung (P95, gemessen über Metriken aus Dok. 07).
2. Barge-in (Anrufer unterbricht) stoppt die Sprachausgabe in **< 400 ms** (P95).
3. FAQ-Antworten stammen nachweislich nur aus den Dokumenten des jeweiligen Mandanten (Isolationstest aus Dok. 04, Abschn. 6 besteht).
4. Terminbuchung erzeugt einen realen Kalendereintrag und bestätigt ihn im Gespräch; Doppelbuchungen sind durch Verfügbarkeitsprüfung ausgeschlossen.
5. Stripe-Testkauf → funktionsfähiger Mandant mit Rufnummer + Onboarding-E-Mail in **< 10 min** ohne manuellen Eingriff.
6. Ausfall-Szenarien (Realtime API down, DB down, Kalender down, n8n down) führen zu definiertem Degradationsverhalten, nie zu stummen/abgebrochenen Anrufen (Chaos-Testplan Dok. 07, Abschn. 6).
7. Alle CI-Gates grün: Lint, Typen, Tests, Coverage, Security-Scan, Staging-Smoke-Call.
8. DSGVO-Checkliste aus Dok. 06 vollständig abgehakt (inkl. AVV-Kette, Löschkonzept, Verzeichnis von Verarbeitungstätigkeiten).
