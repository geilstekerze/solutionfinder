# 09 – MVP-Optimierung, Produktökonomie & sichere Betriebsgrenzen

**Status:** Verbindlicher Optimierungsbeschluss · **Stand:** 2026-07-15

Dieses Dokument präzisiert und verschlankt die Dokumente 01–08. Bei Widersprüchen gilt dieses Dokument. Ziel ist kein maximal ausgestattetes System zum frühestmöglichen Zeitpunkt, sondern ein **schnell validierbares, sicher betreibbares und wirtschaftlich skalierbares SaaS-Produkt**.

---

## 1. Leitentscheidung: vertikaler Produktbeweis vor Plattformausbau

Vor RAG, Kalender, Stripe-Provisioning, n8n und vollständigem Observability-Stack wird ein vollständiger vertikaler Pfad gebaut und gemessen:

1. Eine echte deutsche Rufnummer nimmt den Anruf an.
2. Frau Schmidt führt einen flüssigen deutschen Dialog.
3. Sie erfasst Name, Rückrufnummer und Anliegen strukturiert.
4. Sie erstellt ein Ticket und stellt es zuverlässig per E-Mail zu.
5. Sie beendet den Anruf kontrolliert.
6. Latenz, Kosten, Fallback-Quote und Gesprächserfolg werden gemessen.

**Harter Gate:** WP5 und alle folgenden Arbeitspakete dürfen erst beginnen, wenn dieser Pfad die Kriterien aus Abschnitt 2 erfüllt. Ein technisch beeindruckender Teilaufbau ohne funktionierenden End-to-End-Anruf gilt nicht als Fortschritt zum Produktziel.

---

## 2. Gate A – technische und wirtschaftliche Freigabe

Für mindestens 100 interne oder Pilot-Testanrufe müssen folgende Werte nachweisbar sein:

| Kriterium | Freigabewert |
| :--- | :--- |
| Anrufannahme | ≥ 99 % |
| Kontrolliert beendete Gespräche | ≥ 98 % |
| Stumme oder unkontrollierte Abbrüche | 0 |
| Erste Antwort nach Sprechende | P95 ≤ 2,0 s; Zielwert später ≤ 1,5 s |
| Barge-in | P95 ≤ 500 ms; Zielwert später ≤ 400 ms |
| Erfolgreich zugestellte Tickets | ≥ 99 % innerhalb 5 min |
| Strukturierte Pflichtfelder korrekt | ≥ 95 % |
| Fallback-Quote wegen Realtime-/Tool-Fehlern | < 3 % |
| Variable Kosten | dokumentiert je Gespräch und Minute |

Zusätzlich muss für jedes geplante Preismodell gelten:

> Erwartete variable Kosten aus Telefonie, Realtime-KI, Transkription, Nachrichten und Infrastruktur dürfen bei normaler Nutzung höchstens 35 % des Netto-Umsatzes des Tarifs betragen.

Ist das nicht erfüllt, werden Modell, Gesprächsführung, Kontingente oder Preise angepasst, bevor weitere Funktionen gebaut werden.

---

## 3. Reduzierter MVP-Umfang

### 3.1 Sofort bauen

- Twilio-Telefonie und Realtime-Dialog
- Kontrollierte Fallback-Ansage und Voicemail/Ticket-Erfassung
- Mandantenfähige Kern-Datenhaltung
- Direkte Ticket-Zustellung per E-Mail aus einem eigenen Worker
- Einfaches Admin- und Kundenportal
- Upload einer strukturierten Markdown-Datei als primäres Onboarding-Format
- Basismetriken, strukturierte Logs, Sentry und Kostenmetriken
- Harte Nutzungs-, Kosten- und Missbrauchsgrenzen

### 3.2 Nach Gate A bauen

- PDF/DOCX-Ingestion und vollständige RAG-Pipeline
- Cal.com als erster und zunächst einziger Kalender-Adapter
- Stripe Checkout und automatisiertes Provisioning
- Self-Service-Onboarding
- n8n für optionale Post-Call-Automatisierungen
- Grafana/Loki und erweiterte Betriebsdashboards

### 3.3 Nicht im ersten verkaufbaren MVP

- Calendly und Microsoft 365 parallel
- WhatsApp-Ticket-Zustellung
- CRM-Synchronisation
- Long-Term-Memory
- Qdrant
- mehrere Voice-Provider
- mehrere Orchestrator-Nodes
- 50 parallele Anrufe als Launch-Voraussetzung

Diese Erweiterungen bleiben über Interfaces vorbereitet, werden aber erst nach realem Bedarf implementiert.

---

## 4. Deployment-Vereinfachung ohne Architektur-Sackgasse

Die Codebasis bleibt modular, startet aber mit möglichst wenigen betrieblichen Einheiten:

| Phase | Prozesse/Container | Pflicht-Infrastruktur |
| :--- | :--- | :--- |
| Produktbeweis | `app`, `voice-orchestrator` | Postgres, Caddy |
| Pilot-MVP | zusätzlich `worker`, optional Redis | Postgres, Caddy, Sentry, Basismetriken |
| Verkaufs-MVP | zusätzlich n8n und vollständiges Monitoring | Postgres, Redis, Caddy, n8n, Prometheus/Grafana/Loki |
| Skalierung | getrennte Worker, mehrere Orchestratoren | Load-Balancing und skalierte Daten-/Queue-Komponenten |

`app` enthält zu Beginn API, Portal, Webhooks, Retrieval und Provisioning. Hintergrundaufgaben laufen als eigener Prozess aus derselben Codebasis. Die Modulgrenzen aus Dok. 01 bleiben bestehen; ein späteres Herauslösen erfordert daher keine fachliche Neuentwicklung.

Redis darf im Produktbeweis entfallen, solange genau ein Orchestrator-Prozess betrieben wird und der Verlust eines laufenden Prozesszustands kontrolliert in den Fallback führt. Vor horizontaler Skalierung ist Redis verpflichtend.

---

## 5. Interne Service-Sicherheit

Ein dauerhaft gültiges statisches `X-Internal-Token` allein ist nicht zulässig.

Verbindlich ist:

1. Interne Endpunkte werden durch Caddy nicht öffentlich geroutet.
2. Services laufen in einem isolierten Compose-Netz.
3. Requests verwenden kurzlebige signierte Service-Tokens mit `iss`, `aud`, `iat`, `exp` und eindeutiger Request-ID; maximale Gültigkeit 60 Sekunden.
4. Jede schreibende Anfrage ist gegen Replay geschützt, indem Request-ID und Zeitfenster geprüft werden.
5. Schlüsselrotation muss ohne Downtime möglich sein; zwei gültige Schlüsselstände dürfen während der Rotation überlappen.
6. Ab der ersten horizontal skalierten Produktionsstufe wird mTLS zwischen Orchestrator und API eingesetzt.

---

## 6. Begrenzter Systemzugriff auf Mandantendaten

Ein allgemeiner Anwendungszugriff mit frei gesetztem `app.context = system` ist verboten.

Stattdessen gelten drei getrennte Zugriffswege:

- `fs_app`: normale Tenant-Sessions, immer RLS-gebunden.
- `fs_router`: ausschließlich Ausführung eng begrenzter Funktionen wie `resolve_tenant_by_phone(number)`; kein direktes Tabellen-SELECT.
- `fs_admin`: nur Migrationen, Restore und ausdrücklich protokollierte Betriebsaufgaben; nie im normalen API- oder Call-Pfad.

Mandantenübergreifende Operationen werden als geprüfte PostgreSQL-Funktionen mit minimalen Rechten umgesetzt. Jede Verwendung erzeugt einen Audit-Eintrag mit Zweck, Request-ID und aufrufendem Service.

---

## 7. Kosten-, Tarif- und Missbrauchsschutz

Jeder Mandant besitzt verbindliche Limits:

- enthaltene Gesprächsminuten pro Abrechnungsmonat
- Preis pro Mehrminute oder Upgrade-Regel
- maximale parallele Anrufe
- maximale Gesprächsdauer, Standard 15 Minuten
- tägliches Sicherheitslimit
- monatliches hartes Kostenlimit
- maximale Tool-Aufrufe je Gespräch
- maximale Dokumentgröße und Chunk-Anzahl

Vor Gesprächsbeginn prüft das System Sperren und Kontingente. Während des Gesprächs werden Dauer und geschätzte Kosten fortlaufend überwacht.

### Reaktionen auf Limits

- 80 % Monatskontingent: Hinweis im Portal und E-Mail.
- 100 % Monatskontingent: Mehrminuten gemäß Tarif oder kontrollierte Upgrade-Regel.
- Kostenanomalie: neue Gespräche des Mandanten werden auf einen sicheren Level-1-Modus begrenzt; bestehende Gespräche werden freundlich abgeschlossen.
- Maximaldauer erreicht: Gespräch wird zusammengefasst, Ticket erstellt und kontrolliert beendet.
- Notfallklassifikation: Ticket-Erfassung bleibt möglich, auch wenn optionale Komfortfunktionen deaktiviert sind.

Anruferbezogene Rate-Limits, ungewöhnlich lange Calls, wiederholte Stille und automatisierte Ping-Anrufe werden als Abuse-Signale erfasst. Das System darf einzelne Quellnummern temporär drosseln, aber keine Notruf- oder Sicherheitsversprechen abgeben.

---

## 8. Produktkonfiguration durch Markdown

Das Standard-Onboarding verwendet zunächst eine validierte Markdown-Datei. Sie enthält mindestens:

```markdown
# Unternehmen
Name, Branche, Standorte, Öffnungszeiten

# Persona
Begrüßung, Du/Sie, Tonalität, Aussprache wichtiger Namen

# Leistungen
Leistung, Kurzbeschreibung, Preisangaben nur wenn freigegeben

# Häufige Fragen
Frage und verbindliche Antwort

# Regeln
Was Frau Schmidt sagen, fragen, buchen oder niemals behaupten darf

# Eskalation
Notfälle, Ansprechpartner, Weiterleitungs- und Ticketregeln
```

Die Datei wird gegen ein Schema validiert. Fehlende Pflichtbereiche werden im Portal konkret angezeigt. Ungeprüfter Freitext darf keine Systemregeln, Tool-Rechte oder Sicherheitsvorgaben überschreiben.

---

## 9. Vereinfachtes Integrationsprinzip

- Ticket-E-Mail im Kern-MVP: eigener Worker aus der transaktionalen Outbox.
- n8n: erst nach Gate A, nur für optionale Kundenautomatisierungen und externe Systeme.
- Kalender: zuerst ausschließlich Cal.com; weitere Adapter erst nach zahlendem Bedarf.
- Stripe: erst nach stabiler Pilotversion. Webhooks bleiben idempotent und gegen Out-of-Order-Zustellung geschützt.
- RAG: Markdown zuerst; PDF/DOCX erst nach stabilem Wissens-Test und messbaren Evals.

---

## 10. Realistische Zuverlässigkeitsformulierung

Der Begriff „Null-Fehler-Toleranz“ wird nicht als Versprechen verwendet. Verbindliches Ziel ist:

> Kein einzelner Ausfall einer externen Abhängigkeit darf einen Anruf stumm oder unkontrolliert enden lassen. Das System muss kontrolliert degradieren, den Vorgang nachvollziehbar protokollieren und – soweit möglich – ein Ticket erzeugen.

Externe Dienste können ausfallen. Die Abnahme bewertet daher kontrolliertes Verhalten, Wiederanlauf und Datenintegrität, nicht die unrealistische Behauptung absoluter Fehlerfreiheit.

---

## 11. Angepasste Reihenfolge

1. WP0: Codebasis und minimale CI.
2. WP1-light: Staging, TLS, Logs, Sentry; vollständiger Observability-Stack später.
3. WP2: Mandantentrennung mit eingeschränktem Router-Zugriff.
4. WP3: Telefonie bis Echo.
5. WP4: Realtime-Dialog plus direkte Ticket-E-Mail.
6. **Gate A durchführen.**
7. WP5: Markdown-Wissensbasis; danach weitere Dokumentformate.
8. WP6: Portal und belastbare Ticketprozesse; n8n optional ergänzen.
9. WP7: ausschließlich Cal.com.
10. WP8–WP10: Checkout, Provisioning, Self-Service und Production.
11. WP11: Härtung nach realistischer Pilotlast; 50 parallele Calls erst bei nachgewiesenem Bedarf.

---

## 12. Definition des ersten verkaufbaren Produkts

Das erste Produkt darf verkauft werden, wenn:

- Gate A bestanden ist,
- mindestens drei Pilotmandanten erfolgreich isoliert betrieben wurden,
- Kostenlimits und Abrechnung nachvollziehbar funktionieren,
- ein Restore-Test bestanden wurde,
- Datenschutzunterlagen und Auftragsverarbeiterkette geprüft sind,
- Support- und Incident-Prozess dokumentiert sind,
- der Kunde sein Unternehmen per Markdown konfigurieren und selbst einen erfolgreichen Testanruf durchführen kann.

Alles darüber hinaus ist Optimierung oder Ausbau – nicht Voraussetzung dafür, den realen Markt zu testen.