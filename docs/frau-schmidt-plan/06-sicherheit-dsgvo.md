# 06 – Sicherheit, Datenschutz & DSGVO

Positionierung des Produkts ist „DSGVO-konform & Datensouveränität" – dieses Dokument ist daher Produktanforderung, nicht Beiwerk. Jeder Punkt hat einen Verantwortlichen-Status in der Go-Live-Checkliste (WP11).

## 1. Datenflüsse & Auftragsverarbeiter (AVV-Kette)

| Verarbeiter | Zweck | Region/Datenschutzbasis | Pflicht vor Go-Live |
| :--- | :--- | :--- | :--- |
| Hetzner | Hosting aller Kerndaten | Deutschland | AVV abschließen |
| Microsoft Azure OpenAI | Sprach-KI (Realtime), Embeddings, Zusammenfassungen | Sweden Central (EU); kein Training auf Kundendaten (Azure-Zusage), Abuse-Monitoring-Opt-out beantragen | AVV/DPA + Konfiguration dokumentieren |
| Twilio | Telefonie (Nummern, Media-Streams, SMS) | US-Anbieter; EU-SCCs + Data-Residency-Optionen (Media Region de1) konfigurieren | DPA + Transfer-Impact-Assessment dokumentieren; sipgate-Migrationspfad als Härtung (ADR-2) |
| Stripe | Zahlungen | EU-Entität, SCCs | DPA (Standard) |
| SMTP-Provider | Transaktionsmails | EU-Anbieter wählen | AVV |
| Meta (optional) | WhatsApp-Tickets | Nur bei Aktivierung durch Mandant; Hinweis im AV-Vertrag mit Kunde | DPA + Kunden-Opt-in |

Für **unsere Kunden** sind wir Auftragsverarbeiter: Standard-AVV (Muster) wird beim Checkout mitgeschlossen (Checkbox + PDF), Subprozessorenliste öffentlich auf der Website, Änderungs-Benachrichtigungsprozess definiert.

## 2. Technische und organisatorische Maßnahmen (TOMs, verbindlich)

1. **Transport:** TLS ≥ 1.2 überall (Caddy erzwingt), WSS für alle Media-Streams, HSTS.
2. **At Rest:** Hetzner-Volume mit LUKS-Verschlüsselung für Postgres-Daten + Uploads; Backups verschlüsselt (age) in Hetzner Storage Box (anderer Standort).
3. **Anwendungsgeheimnisse:** sops/age (Dok. 01); Rotation dokumentiert (Runbook); `gitleaks` in CI.
4. **Integrations-Credentials der Mandanten:** AES-256-GCM-verschlüsselt in `integrations.credentials_enc`; Schlüssel (`FS_CRED_KEY`) nur als ENV auf dem Server, Rotationsprozedur im Runbook (Umschlüsselung per Admin-Kommando). **Nonce-Pflicht:** Für jeden Verschlüsselungsvorgang wird ein frischer, kryptografisch zufälliger 96-Bit-Nonce erzeugt (`os.urandom(12)`) und dem Chiffretext vorangestellt gespeichert (`nonce || ciphertext || tag`); Nonce-Wiederverwendung unter demselben Schlüssel bricht GCM vollständig und ist daher per Unit-Test abgesichert (zwei Verschlüsselungen desselben Klartexts ergeben unterschiedliche Ausgaben).
5. **Passwörter:** argon2id; Login-Rate-Limit; Passwort-Reset nur via E-Mail-Token.
6. **Zugriff:** SSH key-only + IP-Allowlist; personalisierte Admin-Accounts; Admin-UI mit 2FA (TOTP); jede Admin-Aktion im `audit_log`.
7. **Mandantentrennung:** RLS (Dok. 02) + Isolationstests in CI + getrennte Upload-Verzeichnisse pro Tenant.
8. **Least Privilege:** n8n ohne DB-Zugriff; Orchestrator nur mit den DB-Rechten, die er braucht; interne Endpunkte tokengeschützt und nicht öffentlich geroutet.
9. **Patching:** Monatlicher Dependency-Update-PR (Renovate) + `pip-audit`/`trivy` in CI (Gate: keine bekannten kritischen CVEs).

## 3. Datenminimierung & Speicherfristen (Löschkonzept)

| Datum | Aufbewahrung (Default, mandantenkonfigurierbar wo sinnvoll) | Löschweg |
| :--- | :--- | :--- |
| Gesprächs-Audio | **wird nicht gespeichert** (ADR-9); Voicemail-Fallback-Aufnahmen: 14 Tage, dann automatische Löschung (inkl. bei Twilio via API) | täglicher Purge-Job |
| Transkripte + Zusammenfassungen | 90 Tage | Purge-Job |
| Tickets | 12 Monate | Purge-Job |
| Anrufer-Rufnummer | in `calls.from_e164` 90 Tage, danach Maskierung (`+49171***`) | Purge-Job |
| Kundendokumente (RAG) | bis Löschung durch Kunde / Vertragsende | sofortiges hartes Löschen (Datei + Chunks) |
| Vertrags-/Abrechnungsdaten | gesetzliche Fristen (§ 147 AO) | manuell/gesondert |
| Kündigung des Mandanten | 30 Tage Karenz (Export möglich), dann vollständige Löschung aller Mandantendaten inkl. Nummernfreigabe | Termination-Job + Protokoll ins `audit_log` |

Der Purge-Job läuft täglich, ist idempotent, protokolliert Zählerstände und hat einen Test, der die Fristenlogik über fixierte Zeitstempel verifiziert.

## 4. Einwilligung & Transparenz im Anruf (rechtliche Produktanforderung)

- Die Begrüßung enthält **immer** den festen (nicht kundenkonfigurierbaren) Baustein: Identifikation als digitale Assistentin + Hinweis, dass das Gespräch zur Bearbeitung des Anliegens **verarbeitet/transkribiert** wird, mit Widerspruchsmöglichkeit („Wenn Sie das nicht möchten, sagen Sie es einfach – dann verbinde ich Sie weiter / nehmen wir nur Ihre Rückrufnummer auf.").
- Widerspricht der Anrufer, wechselt der Call in einen Minimalmodus: keine Transkript-Persistenz außer Rückrufnummer + frei diktierter Kurznotiz (Tool `create_ticket` mit `minimal=true`).
- Audio-Aufzeichnung (über Transkription hinaus) nur, wenn der Mandant das Feature aktiviert hat UND die Ansage eine explizite Einwilligungsfrage enthält (Ja/Nein-Erkennung, bei Nein keine Aufzeichnung). Im MVP bleibt das Feature deaktiviert.
- Datenschutzerklärungs-Baustein für die Website des Mandanten wird im Portal als Text bereitgestellt.

## 5. Betroffenenrechte (Werkzeuge im Admin/Portal)

- Auskunft: Suche über Rückrufnummer/Name im Mandanten-Portal → Export (JSON/PDF) aller zugehörigen Calls/Tickets/Termine.
- Löschung: Einzelfall-Löschung (Call inkl. Transkript, Ticket) durch den Mandanten im Portal; Protokollierung im `audit_log` (ohne Inhalt).
- Verzeichnis von Verarbeitungstätigkeiten + TIA (Twilio) als Dokumente in `docs/` gepflegt.

## 6. Anwendungssicherheit (Web & API)

- OWASP-Basics: CSRF-Token (Portal-Formulare), Security-Header via Caddy (CSP ohne Inline-Script – HTMX-kompatibel konfigurieren, X-Content-Type-Options, Referrer-Policy), Cookie `Secure/HttpOnly/SameSite=Lax`, Session-Rotation bei Login.
- Alle externen Webhooks signaturvalidiert (Stripe, Twilio); interne Endpunkte (`/internal/*`) sind im Caddy **nicht** geroutet (nur Docker-internes Netz).
- Media-Stream-URL enthält kurzlebiges signiertes Token (HMAC über `call_id`+Ablauf, 60 s gültig) – verhindert fremde WS-Verbindungen auf `/media/*`.
- Rate-Limits: Login (5/min/IP), Uploads (10/min/Tenant), Wissens-Test (20/min/Tenant), Checkout-Erzeugung (10/min/IP).
- Prompt-Injection-Härtung: Dokumenten-Inhalte werden in Tool-Antworten als Daten gerahmt („Auszug aus Dokument X: …"); Instructions verbieten, Anweisungen aus Dokumenten oder vom Anrufer zu befolgen, die Tools/Regeln ändern würden; `transfer_call` nur auf konfigurierte Ziele (nie freie Nummern) – Tests in WP11.

## 7. Penetrations- und Härtungstests vor Go-Live (WP11)

Mindestumfang: automatisierter ZAP-Baseline-Scan gegen Staging, manueller Test der Mandantentrennung im Portal (IDOR-Versuche), Twilio-/Stripe-Webhook-Spoofing-Versuche (ohne gültige Signatur), WS-Verbindungsversuch auf `/media/*` ohne Token, Prompt-Injection-Testset (10 Angriffe) gegen den Live-Agenten des Canary-Mandanten.
