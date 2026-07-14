# Umsetzungsplan „Frau Schmidt" – DSGVO-konforme KI-Telefonassistenz für KMU

**Version:** 1.1 · **Stand:** 2026-07-15 · **Status:** Optimierte verbindliche Umsetzungsgrundlage

Dieser Plan ist so geschrieben, dass ein KI-Modell oder Entwicklungsteam ihn ohne unnötige Rückfragen umsetzen kann. Alle wesentlichen Entscheidungen, Schnittstellen und Abnahmekriterien sind festgelegt. Oberste Prioritäten sind **kontrollierte Degradation, Datenintegrität, Sicherheit, messbare Gesprächsqualität und wirtschaftlicher Betrieb**.

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
| 08 | [`08-arbeitspakete.md`](08-arbeitspakete.md) | Sequenzielle Arbeitspakete WP0–WP11 mit Abnahmekriterien |
| 09 | [`09-mvp-optimierung-produktbetrieb.md`](09-mvp-optimierung-produktbetrieb.md) | **Verbindliche MVP-Verschlankung, Produktökonomie, Kostenlimits und Sicherheitspräzisierungen** |

**Regel:** Bei Widerspruch zwischen Dokumenten gilt die Reihenfolge: `09-mvp-optimierung-produktbetrieb.md` > `08-arbeitspakete.md` > Fachdokument 01–07 > dieses README. Existiert zu einer Detailfrage keine Festlegung, gilt Abschnitt 5 („Default-Entscheidungsregeln").

---

## 2. Produktziel (Kurzfassung)

„Frau Schmidt" ist eine mandantenfähige SaaS-Telefonassistentin für KMU:

- **Level 1 – Intelligenter Anrufbeantworter:** Anrufannahme, Anliegen-Erfassung, strukturiertes Ticket per E-Mail an das Team.
- **Level 2 – Vorzimmerdame:** zusätzlich FAQ-Beantwortung aus Kundendokumenten, Terminbuchung und Anrufweiterleitung.
- **Level 3/4 – Chef-Sekretärin / Fach-Agenten:** CRM-Anbindung, Long-Term-Memory und Fach-Workflows nach validiertem MVP.

Die erste verkaufbare Version priorisiert Level 1 plus eine schlanke Wissensbasis. Vollautomatisches Checkout- und Self-Service-Provisioning folgt erst nach bestandenem technischen und wirtschaftlichen Gate aus Dokument 09.

Der vollständige Zielplan liefert Level 1 + Level 2 inklusive automatisiertem Onboarding. Level 3/4 sind nur architektonisch vorbereitet und werden nicht vor realem Kundenbedarf implementiert.

---

## 3. Verbindliche Architektur-Entscheidungen (ADRs)

Jede Entscheidung ist verbindlich. Änderungen erfolgen nur über eine dokumentierte neue ADR.

### ADR-1: Sprache & Laufzeit
**Python 3.12** für alle Backend-Prozesse. Ein einziges Ökosystem minimiert Fehlerquellen. Portal-Frontend: serverseitig gerendertes **FastAPI + Jinja2 + HTMX**; kein SPA-Framework im MVP.

### ADR-2: Telefonie-Anbindung
**Twilio Programmable Voice mit Media Streams** als primärer Weg. Deutsche Rufnummern, Media-Region `de1`, erforderliche Datenschutzverträge und Transferprüfung. Die Telefonie liegt hinter einem `TelephonyAdapter`.

### ADR-3: Sprach-KI
**Azure OpenAI Realtime API**, Region Sweden Central. Audio-zu-Audio im Gesprächspfad, `g711_ulaw`, Function-Calling für klar begrenzte Tools.

### ADR-4: Datenhaltung
**PostgreSQL 16 + pgvector** als primäres Datensystem. **Redis 7** nur für flüchtigen Zustand, Queue und Rate-Limiting, sobald der jeweilige Ausbauzustand es benötigt. Verlust von Redis-Daten darf keinen dauerhaften Datenverlust verursachen.

### ADR-5: Orchestrierung
**n8n self-hosted** ausschließlich für optionale asynchrone Post-Call- und Kundenautomatisierungen. Der Live-Gesprächspfad ist nie von n8n abhängig. Die erste Ticket-E-Mail wird aus einem eigenen Worker versendet.

### ADR-6: Infrastruktur & Deployment
**Hetzner Cloud**, Docker Compose, Caddy 2. Kein Kubernetes im MVP. Codebasis modular, aber zunächst wenige Prozesse gemäß Dokument 09. Staging und Production bleiben getrennt.

### ADR-7: Zahlungen & Provisioning
**Stripe Checkout + Billing**. Webhooks werden idempotent und gegen verspätete beziehungsweise ungeordnete Zustellung verarbeitet. Automatisches Provisioning startet erst nach bestandenem Gate A.

### ADR-8: Beobachtbarkeit
Strukturierte JSON-Logs, Sentry und Kostenmetriken sind ab Produktbeweis Pflicht. Prometheus/Grafana/Loki werden spätestens vor dem Verkaufs-MVP vollständig aktiviert. Jeder Anruf erhält eine durchgängige `call_id`.

### ADR-9: Kein Audio-Mitschnitt per Default
Standardmäßig wird kein Gesprächsaudio gespeichert, nur erforderliche Transkripte und strukturierte Ergebnisse. Aufzeichnung ist ein gesondertes Opt-in mit geprüfter Rechtsgrundlage.

### ADR-10: Produktbeweis vor Plattformausbau
Vor RAG-Vollausbau, mehreren Kalendern, n8n-Automatisierungen, Stripe-Provisioning und horizontaler Skalierung muss der vertikale End-to-End-Anruf das technische und wirtschaftliche Gate aus Dokument 09 bestehen. Funktionen ohne belegten Kundennutzen werden nicht vorsorglich gebaut.

---

## 4. Strategie für kontrollierte Degradation

1. **Typisierung erzwungen:** `mypy --strict` und `ruff` laufen in CI; Merge nur bei 0 Fehlern.
2. **Testpflicht:** Kernlogik ≥ 90 % Branch-Coverage; jedes Arbeitspaket definiert konkrete Tests.
3. **Der Gesprächspfad degradiert kontrolliert:** Jede externe Abhängigkeit hat ein definiertes Fallback-Verhalten. Kein einzelner Ausfall darf einen Anruf stumm oder unkontrolliert enden lassen.
4. **Idempotenz:** Webhooks, Outbox-Verarbeitung und Provisioning sind ohne Doppelwirkung wiederholbar.
5. **Keine stillen Fehler:** Jede abgefangene relevante Exception erzeugt ein strukturiertes Log und bei Betriebsrelevanz ein Sentry-Event.
6. **Migrations-Disziplin:** Schemaänderungen ausschließlich über Alembic und mit getesteter Wiederherstellung.
7. **Staging-Gate:** Jedes Release durchläuft Staging und einen automatisierten Testanruf.
8. **Canary-Mandant:** Vor Production-Freigabe wird ein echter Testanruf gegen einen internen Mandanten ausgeführt.
9. **Kosten-Gate:** Jeder Anruf und Mandant besitzt messbare und durchsetzbare Nutzungs- und Kostenlimits.

---

## 5. Default-Entscheidungsregeln für das umsetzende Modell

Wenn eine Detailfrage nicht geregelt ist:

1. Wähle die Option mit weniger externen Abhängigkeiten.
2. Wähle kontrollierte Degradation statt hartem Abbruch.
3. Wähle die explizite Variante statt Konvention oder Magie.
4. Wähle die kleinste Lösung, die das aktuelle Abnahmekriterium vollständig erfüllt.
5. Schreibe erst den Test, wenn das Verhalten unklar ist.
6. Dokumentiere neue Architekturentscheidungen im ADR-Log.
7. Baue keine Erweiterung nur „für später", wenn ein Interface oder dokumentierter Migrationspfad genügt.

**Verboten:** Platzhalter-Code, auskommentierte Altimplementierungen, hartcodierte Secrets, ungebremste externe Kosten, Abhängigkeiten ohne Versions-Pinning und `latest`-Docker-Tags.

---

## 6. Phasenmodell

| Phase | Arbeitspakete | Ergebnis / Gate |
| :--- | :--- | :--- |
| Phase 0 – Produktbeweis | WP0–WP4, gemäß Dok. 09 verschlankt | Echter End-to-End-Anruf mit Ticket-E-Mail und vollständigen Messwerten |
| **Gate A** | 100 Pilot-/Testanrufe | Technische und wirtschaftliche Kriterien aus Dok. 09 bestanden |
| Phase 1 – Pilot-MVP | WP5–WP7 reduziert | Markdown-Wissensbasis, Portal, belastbare Tickets, Cal.com |
| Phase 2 – Verkaufs-MVP | WP8–WP10 | Checkout, Provisioning, Self-Service, Production |
| Phase 3 – Härtung & Skalierung | WP11 nach realer Last | Security, Restore, Last und DSGVO-Abnahme |

Kein Arbeitspaket nach WP4 beginnt, bevor Gate A dokumentiert bestanden oder eine Abweichung ausdrücklich als ADR freigegeben wurde.

---

## 7. Erfolgskriterien des Gesamtprojekts

Das Projekt gilt als erfolgreich umgesetzt, wenn:

1. Gate A aus Dokument 09 bestanden ist.
2. Ein Anruf wird in < 2 s angenommen; Zielwert für erste Antwort P95 ≤ 1,5 s, Pilot-Freigabe spätestens bei P95 ≤ 2,0 s.
3. Barge-in stoppt die Ausgabe zuverlässig; Zielwert P95 ≤ 400 ms.
4. FAQ-Antworten stammen nur aus den Dokumenten des jeweiligen Mandanten.
5. Terminbuchungen werden verifiziert und verhindern Doppelbestätigungen.
6. Stripe-Testkauf erzeugt nach Freigabe der Automatisierungsphase einen funktionsfähigen Mandanten in < 10 min.
7. Externe Ausfälle führen zu dokumentierter Degradation statt stummen oder unkontrollierten Abbrüchen.
8. Kostenlimits, Missbrauchsschutz und Tarifkontingente funktionieren nachweisbar.
9. Alle CI-, Security-, Restore- und Staging-Gates sind grün.
10. Datenschutzunterlagen, Auftragsverarbeiterkette und Löschkonzept sind geprüft.
11. Mindestens drei Pilotmandanten wurden isoliert und ohne Datenvermischung betrieben.