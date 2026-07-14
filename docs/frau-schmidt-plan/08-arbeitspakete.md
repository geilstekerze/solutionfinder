# 08 – Arbeitspakete (WP0–WP11) mit Abnahmekriterien

**Arbeitsanweisung an das umsetzende Modell:**
1. Pakete strikt in Reihenfolge abarbeiten; ein WP gilt erst als fertig, wenn **alle** Abnahmekriterien nachweisbar erfüllt sind (Tests grün, manuell prüfbare Punkte dokumentiert in `docs/abnahme/WP<N>.md` im Zielrepo).
2. Jedes WP endet mit einem deploybaren Zustand (CI grün, Staging läuft).
3. Bei Unklarheiten gelten die Default-Regeln aus README Abschn. 5. Externe Konten (Twilio, Azure, Stripe, Hetzner, Domain) werden vom Auftraggeber bereitgestellt; benötigte Zugänge sind je WP unter „Voraussetzungen" gelistet und **vor** Beginn des WP anzufordern.
4. Ein WP = ein oder mehrere PRs; niemals mehrere WPs in einem PR mischen.

---

## WP0 – Repo, Werkzeuge, CI-Skelett
**Voraussetzungen:** GitHub-Repo `frau-schmidt`, Container-Registry.
**Aufgaben:** Repo-Struktur aus Dok. 01 Abschn. 3 anlegen; `uv`-Workspace; `ruff`/`mypy --strict`/`pytest`-Konfiguration; `pre-commit`; CI (`ci.yml`) mit lint/type/unit/gitleaks; Platzhalter-freie Minimal-Services (je ein `/healthz`); Dockerfiles (multi-stage, non-root User); `docker compose up` startet alle Services lokal.
**Abnahme:** CI grün auf leerem Funktionsumfang; `docker compose up` lokal: alle `/healthz` = 200; `mypy --strict` fehlerfrei; README des Zielrepos beschreibt Setup in ≤ 10 Schritten, die ein frischer Klon nachvollziehen kann.

## WP1 – Infrastruktur Staging (Server, TLS, Observability, Secrets)
**Voraussetzungen:** Hetzner-Zugang, Domain/Subdomains (`staging.…`, `api.…`), sops/age-Schlüssel.
**Aufgaben:** Staging-Server provisionieren (Cloud-Init-Skript versioniert); Compose-Stacks base/staging; Caddy mit TLS; Prometheus+Grafana+Loki+Promtail; Sentry-Anbindung; sops-Secrets-Workflow; Deploy-Pipeline (`deploy.yml`) bis Staging inkl. `migrate`-Job-Mechanik; Backup-Grundgerüst (pg_dump-Cron + restic).
**Abnahme:** `git push main` deployt automatisch auf Staging; `https://staging.…/healthz` über TLS erreichbar; Logs aller Services in Loki sichtbar; Test-Exception erscheint in Sentry; Grafana zeigt Basis-Metriken; Secrets liegen nirgends im Klartext im Repo (gitleaks grün).

## WP2 – Datenmodell & Mandanten-Framework
**Aufgaben:** Alembic einrichten; vollständiges Schema aus Dok. 02 als erste Migrationskette; RLS-Policies; DB-Rollen `fs_app`/`fs_admin`; `fs_shared.db` mit `tenant_session`/`system_session`; Outbox-Modul inkl. Dispatcher-Task (Ziel-URL konfigurierbar, Retry/Backoff); uuid7-Helper; testcontainers-Setup.
**Abnahme:** Alembic-Roundtrip-Test (up→down→up) grün; **RLS-Isolationstest** (Dok. 02 Abschn. 3) grün, inkl. Nachweis „ohne Kontext keine Zeile lesbar"; Outbox-Test: Event wird bei Ziel-Ausfall gepuffert und nach „Recovery" exakt einmal zugestellt; Coverage-Gates erfüllt.

## WP3 – Telefonie-Eingang (Twilio bis Echo)
**Voraussetzungen:** Twilio-Konto, DE-Testnummer, Media Region de1 konfiguriert.
**Aufgaben:** `POST /twilio/voice` mit Signaturvalidierung, Nummer→Tenant-Auflösung (system_session), `calls`-Anlage, TwiML `<Connect><Stream>` mit signiertem Kurzzeit-Token; Orchestrator-WS-Endpunkt `/media/{call_id}` mit Token-Prüfung; `FakeTwilioMediaClient` (Test-Infrastruktur!); als Zwischenschritt Echo-Modus (Audio zurückspielen) hinter Feature-Flag; statisches Not-TwiML für DB-Ausfall (Dok. 03 Abschn. 8).
**Abnahme:** Realer Anruf auf Staging-Nummer wird < 2 s angenommen, Echo hörbar, `calls`-Zeile korrekt (started/ended, from maskierbar); Anruf auf unbekannte Nummer → definierte Ansage + Log; Webhook ohne gültige Signatur → 403; Integrationstest mit FakeTwilioMediaClient deckt Frame-Handling ab; DB-down-Test liefert Not-TwiML.

## WP4 – Realtime-Bridge (das Herzstück)
**Voraussetzungen:** Azure-OpenAI-Ressource Sweden Central, Deployments `gpt-realtime` + `text-embedding-3-large`, Abuse-Monitoring-Opt-out beantragt.
**Aufgaben:** Realtime-Client (`fs_shared/realtime`); `session_config.py` (Instructions-Template mit Pflichtbausteinen aus Dok. 06 Abschn. 4); Audio-Bridge inkl. Barge-in (clear + response.cancel + truncate, mark-Tracking); Zustandsautomat komplett; Transkript-Persistenz; Abschluss-Sequenz; Fallback-Voicemail-Modul inkl. asynchroner Transkription; Reconnect-Logik; `FakeRealtimeServer`; Metriken aus Dok. 03 Abschn. 10; Reaper-Task.
**Abnahme (Kern-Meilenstein = Konzept-Phase 1):**
- Reales Testgespräch (deutsch) über Staging-Nummer: flüssiger Dialog, erste Antwort < 1,5 s nach Sprechende (Messwert aus Metrik dokumentieren).
- Barge-in-Test: Unterbrechen stoppt Ausgabe < 400 ms; Transkript-Kontext danach konsistent (kein „Geister-Text").
- Contract-Tests gegen FakeRealtimeServer decken ab: Happy Path, speech_started während Ausgabe, WS-Abbruch mit Reconnect, WS-Abbruch mit Fallback, Connect-Timeout → Voicemail.
- Chaos-Probe auf Staging: Realtime-Endpoint per Firewall geblockt → Anruf landet hörbar in Fallback-Voicemail, Ticket-Datensatz entsteht, Outcome `voicemail_fallback`.
- Kein Anruf endet je stumm: Nachweis über Testmatrix-Protokoll `docs/abnahme/WP4.md`.

## WP5 – Wissensbasis (RAG) + Portal-Grundgerüst
**Aufgaben:** Portal-Login (argon2id, Sessions, CSRF); Dokumenten-Upload inkl. Validierung/ClamAV; ingestion-worker mit Pipeline aus Dok. 04; `PgVectorStore`; Tool-Endpunkt `search_knowledge`; „Wissens-Test"-Seite; Tool in Realtime-Session (Level 2) registrieren; Prompt-Kopplung (Dok. 04 Abschn. 4); Evals-Harness (`make eval-rag`).
**Abnahme:** Upload→ready-Durchlauf < 2 min für 10-Seiten-PDF; defektes/gescanntes PDF → `failed` mit verständlicher Meldung; **RAG-Isolationstest** (Dok. 04 Abschn. 6.1) grün; Recall@3 ≥ 0,85 auf Goldset; „Weiß-nicht"-Eval ≥ 9/10; reales Testgespräch: Frage aus hochgeladenem Dokument wird korrekt beantwortet, Frage außerhalb der Dokumente führt zu ehrlichem „weiß ich nicht" + Ticket-Angebot.

## WP6 – Tickets (Level 1 komplett)
**Aufgaben:** Tool `create_ticket` (inkl. `minimal=true`-Pfad für Verarbeitungs-Widerspruch); Zusammenfassungs-Job (arq) nach Gesprächsende; n8n aufsetzen (gepinnt, eigener Auth-Token) + Workflows `ticket-delivery`, `call-summary`, Error-Workflow; SMTP-Modul + Templates; Dringend-SMS-Pfad direkt aus api; Portal-Ansichten: Anrufliste, Transkript-Detail, Tickets.
**Abnahme:** Realer Testanruf „bitte um Rückruf wegen Heizungsausfall, dringend" → E-Mail-Ticket beim konfigurierten Empfänger < 5 min, korrekt kategorisiert (`urgency=high`) + SMS; n8n gestoppt → Anruf funktioniert, Event nachgeliefert nach n8n-Start (Test dokumentiert); Widerspruchs-Szenario: Transkript-Persistenz nachweislich minimal; Portal zeigt Anruf, Transkript, Ticket korrekt mandantengetrennt (IDOR-Test: fremde `call_id` → 404).

## WP7 – Terminbuchung (Level 2 komplett)
**Voraussetzungen:** Cal.com-Konto (Referenz), Calendly-Testkonto.
**Aufgaben:** `CalendarAdapter`-Interface + `CalcomAdapter` + `CalendlyAdapter`; Tools `check_availability`/`book_appointment` inkl. Idempotenz + Verifikations-Lesen; Portal: Kalender-Integration verbinden (Credentials verschlüsselt), Termin-Liste; Zeitzonen-Handling (Europe/Berlin, DST-Testfälle).
**Abnahme:** Reales Testgespräch bucht Termin: Eintrag existiert bei Cal.com UND in `appointments`, Assistentin nennt korrektes Datum/Uhrzeit auf Deutsch; Doppelbuchungs-Test (Slot parallel wegbuchen) → Assistentin bietet Alternativen; Kalender-API geblockt → Ticket-Fallback-Angebot; Unit-Tests für DST-Grenzfälle (letzter Sonntag März/Oktober) grün; identischer Testsatz gegen Calendly-Adapter grün.

## WP8 – Stripe-Checkout & Provisioning
**Voraussetzungen:** Stripe-Konto (Testmode), Preise angelegt; Twilio-Nummernkauf-Berechtigung; AVV-Muster-PDF.
**Aufgaben:** Checkout-Erzeugung, Webhook mit Signatur + Exakt-einmal-Verarbeitung; Provisioning-State-Machine (alle Zustände aus Dok. 05 Abschn. 2) inkl. Nummern-Pool; Passwort-Set-Flow; Welcome-Mail; Subscription-Status-Sync (`suspended`/`terminated`-Verhalten inkl. Ansage); Admin-Dashboard Provisioning + Retry; Metrik `fs_provisioning_duration_seconds`.
**Abnahme:** Stripe-Testkauf → ohne manuellen Eingriff: aktiver Mandant, erreichbare Rufnummer, Welcome-Mail, Portal-Login funktioniert — gemessen < 10 min (Ziel < 5); Webhook-Replay (gleiches Event 5× senden) erzeugt exakt einen Mandanten; Kauf mit künstlich fehlschlagendem Nummernkauf → Run `stuck` + Alert + Admin-Retry führt zum Erfolg; `subscription.deleted` → Mandant `terminated`, Anrufe erhalten definierte Ansage.

## WP9 – Onboarding-Erlebnis & Persona
**Aufgaben:** Danke-Seite mit Live-Provisioning-Status; geführte Portal-Checkliste (Dok. 05 Abschn. 3); Persona-Editor (Begrüßung, Du/Sie, 3 Tonfall-Presets, Auswahl aus verfügbaren Realtime-Stimmen) mit Live-Vorschau (Text-Rendering der Instructions); Testanruf-Seite mit Live-Transkript (SSE); Rufumleitungs-Anleitungen (statisch, 5 Anbieter); Datenschutz-Textbaustein.
**Abnahme:** Kompletter Selbst-Onboarding-Durchlauf durch eine projektfremde Testperson ohne Hilfe in < 20 min bis zum erfolgreichen Testanruf (protokolliert); Persona-Änderung wirkt beim nächsten Anruf (< 30 s Propagation); alle Checklisten-Schritte abhakbar und persistiert.

## WP10 – Production-Umgebung & Landingpage
**Voraussetzungen:** Production-Server, Domain promptwerker.de-Subdomain bzw. Produktdomain, Stripe Live-Mode, echte Twilio-Nummern.
**Aufgaben:** Production-Compose (Digest-Pins, `stop_grace_period`), Approval-Gate + Production-Deploy inkl. Canary-Smoke-Call + Auto-Rollback; Landingpage (statisch: Nutzenversprechen, Pricing, Demo-Nummer zum Anrufen!, AVV/Impressum/Datenschutz); Canary-Mandant; Blackbox-Monitoring; Backups + **erster bestandener Restore-Test**; Alertmanager-Routing an Betreiber.
**Abnahme:** Deploy nach Production ausschließlich via Pipeline inkl. bestandenem Canary-Anruf; absichtlich kaputtes Release → automatischer Rollback nachgewiesen; Demo-Nummer auf Landingpage funktioniert; Restore-Test-Protokoll liegt vor; alle Alerts feuern testweise (Alert-Probe) und erreichen den Betreiber.

## WP11 – Härtung, Last, DSGVO-Abnahme, Go-Live
**Aufgaben:** Lasttest 50 parallele Calls (synthetische Streams) auf Production-Hardware-Äquivalent; Chaos-Testplan vollständig durchführen (jede Zeile der Degradations-Matrix); Security-Runde aus Dok. 06 Abschn. 7 (ZAP, IDOR, Webhook-Spoofing, WS-Token, Prompt-Injection-Set); Purge-Job + Fristen-Tests; Betroffenenrechte-Werkzeuge; Runbooks vervollständigen; DSGVO-Checkliste (AVV-Kette, VVT, TIA, Subprozessorenliste) abhaken; Gesprächs-Evals als Release-Gate verdrahten; Kosten-Kontingente aktiv.
**Abnahme = Erfolgskriterien aus README Abschn. 7 vollständig**, zusätzlich: Lasttest hält alle P95-Budgets bei 50 Calls; Chaos-Protokoll ohne Abweichung von der Matrix; Security-Findings ≥ „mittel" sind behoben; DSGVO-Checkliste von Auftraggeber gegengezeichnet. Danach: Go-Live-Freigabe.

---

## Erweiterungs-Backlog nach Go-Live (nicht Teil dieses Plans, Reihenfolge empfohlen)

1. M365-Kalender-Adapter (Interface existiert).
2. WhatsApp-Ticket-Kanal aktivieren (Meta-Verifizierung abgeschlossen).
3. sipgate/SIP-Trunk-Adapter für volle Telefonie-Datenresidenz (ADR-2-Härtung).
4. Level 3: CRM-Adapter (HubSpot zuerst), Long-Term-Memory (Tabelle existiert), proaktive To-Dos.
5. Level 4: Fach-Agenten als getrennte Tool-Bundles je Branche; DATEV-/Shopify-Integrationen.
6. Qdrant-Migration bei Wachstum (Dok. 04 Abschn. 7); zweiter Orchestrator-Node + Load-Balancing.
