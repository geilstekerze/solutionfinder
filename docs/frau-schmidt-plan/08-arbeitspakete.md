# 08 – Arbeitspakete (WP0–WP11) mit Abnahmekriterien

**Arbeitsanweisung:**

1. Pakete werden in Reihenfolge umgesetzt. Ein WP ist erst fertig, wenn alle Abnahmekriterien dokumentiert sind.
2. Jedes WP endet mit einem deploybaren Zustand und einem Abnahmeprotokoll unter `docs/abnahme/WP<N>.md`.
3. Es wird nur gebaut, was für das aktuelle Gate erforderlich ist. Interfaces und Migrationspfade ersetzen vorsorgliche Implementierungen.
4. **Nach WP4 ist Gate A aus Dokument 09 zwingend. WP5 beginnt erst nach dokumentierter Freigabe.**
5. Ein WP darf in mehrere kleine PRs aufgeteilt werden; verschiedene WPs werden nicht in einem PR vermischt.

---

## WP0 – Repo, Werkzeuge und minimale CI

**Voraussetzungen:** Zielrepo und Container-Registry.

**Aufgaben:** Modularen Python-Workspace anlegen; Pakete `shared`, `app`, `voice_orchestrator`; `worker` als zweiter Entrypoint derselben Codebasis; ruff, mypy strict, pytest, gitleaks; minimale Dockerfiles; lokale Compose-Umgebung mit Postgres und Caddy; Healthchecks.

**Abnahme:** Frischer Klon startet in höchstens zehn dokumentierten Schritten; CI ist grün; alle Healthchecks liefern 200; keine Secrets im Repo.

## WP1 – Staging light

**Voraussetzungen:** Hetzner, Domain, sops/age.

**Aufgaben:** Staging-Server, TLS, Deploy-Pipeline, strukturierte Logs, Sentry, Basismetriken, verschlüsselte Secrets und Backup-Grundgerüst. Grafana/Loki/n8n sind in diesem WP ausdrücklich nicht erforderlich.

**Abnahme:** Merge nach `main` deployt nach Staging; TLS und WSS funktionieren; Fehler erscheinen mit Release-SHA und `call_id` in Sentry; ein verschlüsseltes Datenbankbackup kann testweise gelesen werden.

## WP2 – Datenmodell und Mandantentrennung

**Aufgaben:** Alembic, Kernschema, RLS, Outbox, UUIDv7, Audit-Log. DB-Rollen: `fs_app`, eingeschränkter `fs_router`, `fs_admin`. Mandantenübergreifende Rufnummernauflösung ausschließlich über eine minimal berechtigte DB-Funktion; kein allgemeiner frei setzbarer Systemkontext.

**Abnahme:** Migration up/down/up; Isolationstest für mindestens zwei Mandanten; ohne Tenant-Kontext keine Daten; `fs_router` kann ausschließlich die freigegebene Rufnummernfunktion ausführen; Outbox liefert nach simuliertem Zielausfall exakt einmal nach.

## WP3 – Telefonie bis Echo

**Voraussetzungen:** Twilio-Testkonto und deutsche Testnummer.

**Aufgaben:** Signaturvalidierter Voice-Webhook, Rufnummernauflösung, TwiML Media Stream, kurzlebiges WS-Token, Echo-Modus, statisches Not-TwiML, FakeTwilioMediaClient.

**Abnahme:** Echter Anruf wird in unter zwei Sekunden angenommen; Echo funktioniert; ungültige Signatur wird abgewiesen; unbekannte Nummer und DB-Ausfall erzeugen eine hörbare definierte Ansage statt Stille.

## WP4 – Realtime-Dialog und erster vollständiger Produktpfad

**Voraussetzungen:** freigegebenes Azure-Realtime-Deployment.

**Aufgaben:** Realtime-Bridge, Call-State-Machine, Barge-in, Transkript, Reconnect und Fallback. Zusätzlich: strukturierte Erfassung von Name, Rückrufnummer und Anliegen; `create_ticket`; direkte E-Mail-Zustellung aus Outbox/Worker; Kosten- und Dauererfassung; maximale Gesprächsdauer; Parallelitätslimit; FakeRealtimeServer.

**Abnahme:**

- flüssiges deutsches Testgespräch über echte Rufnummer;
- kontrolliertes Unterbrechen und Fortsetzen;
- Ticket-E-Mail innerhalb fünf Minuten;
- Realtime-Ausfall führt hörbar in den Fallback und erzeugt ein Ticket;
- Maximaldauer beendet das Gespräch freundlich und kontrolliert;
- Kosten und Minuten werden je Anruf und Tenant persistiert;
- kein Testszenario endet stumm oder unkontrolliert.

### Gate A – Pflicht nach WP4

Mindestens 100 interne oder Pilot-Testanrufe werden gemäß Dokument 09 ausgewertet. Gemessen werden Erfolgsquote, Pflichtfelder, Ticket-Zustellung, P95-Latenz, Barge-in, Fallback-Quote und variable Kosten.

**Gate bestanden:** Alle Freigabewerte aus Dokument 09 sind erfüllt und die erwarteten variablen Kosten liegen im vorgesehenen Tarifmodell bei höchstens 35 % des Netto-Umsatzes.

**Gate nicht bestanden:** Keine weiteren Produktfunktionen. Zuerst werden Gesprächslogik, Provider, Modell, Limits oder Preise korrigiert.

## WP5 – Markdown-Wissensbasis

**Aufgaben:** Portal-Login, validierter Markdown-Upload gemäß Dokument 09, Chunking, Embeddings, pgvector-Retrieval, Wissens-Testseite, Tool `search_knowledge`, Tenant-Isolation, Goldset-Evals. PDF/DOCX bleiben deaktiviert.

**Abnahme:** Markdown-Upload wird schema-validiert; fehlende Bereiche werden verständlich angezeigt; Recall@3 ≥ 0,85; Fragen außerhalb des Wissens führen zu ehrlichem Nichtwissen und Ticket-Angebot; Tenant-Isolation besteht.

## WP6 – Portal und belastbare Ticketprozesse

**Aufgaben:** Anrufliste, Transkript, Ticketansicht, Zustellstatus, Empfänger-Konfiguration, Retry, dringende SMS optional. Direkter Worker bleibt Standard. n8n darf ergänzend als Feature-Flag für optionale Automatisierungen installiert werden, ist aber kein Abnahmekriterium.

**Abnahme:** Ticket-E-Mail P95 ≤ fünf Minuten; Zustellfehler sind sichtbar und wiederholbar; IDOR-Test auf fremde IDs liefert 404; Worker-Ausfall puffert Events und liefert nach Wiederanlauf nach.

## WP7 – Terminbuchung mit Cal.com

**Voraussetzungen:** Cal.com-Testkonto.

**Aufgaben:** `CalendarAdapter`, ausschließlich `CalcomAdapter`, Live-Verfügbarkeit, idempotente Buchung, Verifikations-Lesen, Portalverbindung, DST-Tests.

**Abnahme:** Realer Anruf bucht einen nachweislich existierenden Termin; parallele Slotbelegung führt zu Alternativen; API-Ausfall führt zum Ticket-Angebot; keine Doppelbestätigung. Calendly und Microsoft 365 sind nicht Teil dieses WP.

## WP8 – Stripe, Tarife und Provisioning

**Voraussetzungen:** Stripe-Testmode und Twilio-Nummernberechtigung.

**Aufgaben:** Checkout, signaturvalidierte idempotente Webhooks, Schutz vor ungeordneter Zustellung, Provisioning-State-Machine, Nummernpool, Welcome-Mail, Passwort-Set-Flow. Tarife enthalten Gesprächsminuten, Mehrminutenregel, Parallelitätslimit, Maximaldauer, Tages- und Monatslimit sowie hartes Kostenlimit.

**Abnahme:** Testkauf erzeugt in unter zehn Minuten genau einen Mandanten; Event-Replay und ältere Events verändern keinen neueren Zustand; Limits werden im Portal angezeigt und technisch durchgesetzt; künstlicher Provisioning-Fehler ist wiederaufsetzbar.

## WP9 – Self-Service-Onboarding und Persona

**Aufgaben:** Danke-Seite, Statusanzeige, geführte Checkliste, Markdown-Editor/Upload, Persona mit Begrüßung, Du/Sie und Ton-Presets, Testanrufseite, Rufumleitungsanleitungen.

**Abnahme:** Projektfremde Testperson erreicht ohne Hilfe in unter 20 Minuten einen erfolgreichen Testanruf; Konfigurationsfehler werden konkret erklärt; Persona-Änderung wirkt beim nächsten Anruf.

## WP10 – Production und erster Pilotverkauf

**Voraussetzungen:** Production-Server, Live-Konten, Verträge und Datenschutzunterlagen.

**Aufgaben:** Production-Deployment, Canary-Anruf, Rollback, Landingpage, Demo-Nummer, physisches Base-Backup mit WAL-Archivierung, logischer Zweitdump, Restore-Test, Alarmrouting, mindestens drei Pilotmandanten.

**Abnahme:** Pipeline und Rollback nachgewiesen; Restore erfolgreich; drei Mandanten sind isoliert produktiv; Kosten und Limits stimmen mit Abrechnung überein; Support- und Incident-Prozess ist dokumentiert.

## WP11 – Härtung und bedarfsgerechte Skalierung

**Aufgaben:** Security-Tests, Prompt-Injection-Set, Lösch- und Betroffenenrechte, vollständiges Monitoring, Runbooks, Lasttest anhand realistisch erwarteter Pilotlast. 50 parallele Calls sind erst Pflicht, wenn Vertrieb oder reale Nutzung diese Kapazität absehbar erfordern.

**Abnahme:** Keine offenen Findings ab mittel; Restore, Chaos- und Security-Protokoll vollständig; Datenschutz-Checkliste geprüft; Lasttest hält die für die nächste Wachstumsstufe erforderliche Parallelität mit dokumentierter Reserve.

---

## Erweiterungs-Backlog nach Go-Live

1. n8n-Kundenautomatisierungen ausbauen.
2. Microsoft-365- und Calendly-Adapter nach zahlendem Bedarf.
3. WhatsApp-Ticketkanal.
4. Zweiter Telefonieprovider.
5. CRM-Adapter und Long-Term-Memory.
6. Qdrant oder horizontale Orchestrator-Skalierung erst nach gemessenem Grenzwert.