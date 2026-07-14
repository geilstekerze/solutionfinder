# 05 – Integrationen, Checkout & automatisiertes Onboarding

## 1. Stripe (Checkout & Billing)

- Zwei Produkte/Preise: `level1` (99 €/Monat), `level2` (199 €/Monat), monatlich, über **Stripe Checkout** (nicht nur Payment Links – Checkout-Sessions erlauben es, `client_reference_id`/Metadata sauber zu setzen; Payment Links bleiben als Marketing-Einstieg möglich und führen auf dieselben Preise).
- Landingpage (statisch, Caddy-served, unter promptwerker.de) verlinkt auf Checkout-Session-Erzeugung `GET /checkout/{plan}` (api erzeugt Session mit `success_url=/onboarding/danke`, `automatic_tax`, Pflichtfeld E-Mail).
- **Webhook `POST /webhooks/stripe`:** Signatur-Prüfung (`STRIPE_WEBHOOK_SECRET`), verarbeitete Event-IDs landen in `provisioning_runs.stripe_event_id` (UNIQUE) → exakt-einmalige Verarbeitung. Relevante Events: `checkout.session.completed` (startet Provisioning), `customer.subscription.updated/deleted` (Status-Sync → `subscriptions.status`; `past_due` → Mandant `suspended` nach Kulanzfrist 7 Tage, `deleted` → `terminated` + Löschfristen aus Dok. 06).
- `suspended`: Anrufe werden mit neutraler Ansage („vorübergehend nicht erreichbar") beantwortet, Portal zeigt Zahlungshinweis. Kein Datenverlust.

## 2. Provisioning-State-Machine (Service `api`, Modul `provisioning/`)

Zustände (persistiert in `provisioning_runs.state`, jede Transition idempotent und einzeln wiederholbar):

```
received → tenant_created → number_purchased → number_configured
        → portal_user_created → welcome_email_sent → completed
   (jeder Zustand: bei Fehler → retry mit Backoff, nach 5 Versuchen → state=stuck + Alert)
```

| Schritt | Aktion | Idempotenz |
| :--- | :--- | :--- |
| `tenant_created` | `tenants`-Zeile (status `provisioning`), `subscriptions`-Zeile | UNIQUE `stripe_subscription_id` |
| `number_purchased` | Twilio: verfügbare DE-Nummer suchen + kaufen | Twilio-SID in `state_data`; vor Kauf prüfen, ob schon gekauft |
| `number_configured` | Voice-Webhook-URL + Fallback-URL auf api setzen, `phone_numbers`-Zeile | Update ist per se idempotent |
| `portal_user_created` | User mit E-Mail aus Checkout, Passwort-Set-Link (Token 48 h) | UNIQUE (tenant, email) |
| `welcome_email_sent` | Onboarding-Mail: Rufnummer, Anleitung Rufumleitung, Portal-Link, Upload-Link | `state_data.email_message_id` |
| `completed` | Tenant `active`, Outbox-Event `tenant.provisioned` | – |

**Ziel < 10 min:** Alle Schritte laufen unmittelbar nacheinander in einem Hintergrund-Task; gemessen wird `completed_at - received_at` als Metrik `fs_provisioning_duration_seconds` (SLO: P95 < 5 min). Ein Admin-Dashboard (`/admin/provisioning`) zeigt alle Runs + Retry-Button für `stuck`.

**Nummern-Vorrat:** Konfigurierbarer Pool (Default 3) vorgekaufter DE-Nummern als Puffer gegen Twilio-Suchlatenz/Nichtverfügbarkeit; Pool wird nach Verbrauch automatisch aufgefüllt (täglicher Job + Alert bei Pool < 2).

## 3. Onboarding-Erlebnis des Kunden

1. Kauf → Danke-Seite: „Ihre Frau Schmidt wird gerade eingerichtet" (Status-Polling der Provisioning-Run, live).
2. E-Mail mit: dedizierter Rufnummer, Schritt-für-Schritt-Rufumleitungsanleitung (die 5 häufigsten Telefonanlagen/Anbieter), Portal-Zugang.
3. Portal-Ersteinrichtung als geführte Checkliste: (a) Firmenprofil & Persona (Begrüßungstext, Du/Sie, Tonfall aus 3 Presets), (b) Dokumente hochladen, (c) Ticket-Zustellung konfigurieren (E-Mail-Adressen; WhatsApp optional), (d) Level 2: Kalender verbinden, (e) **Testanruf-Button**: Portal zeigt die Nummer + Live-Transkript des eigenen Testanrufs → der „Wow-Moment" und zugleich unser Abnahmetest beim Kunden.

## 4. Ticket-Zustellung (Level 1-Kernfunktion)

- Kanäle: **E-Mail** (Pflicht, MVP) via SMTP-Relay mit EU-Sitz (konfiguriert als Integration `smtp`, Default: zentraler Versand über eigene Domain mit SPF/DKIM/DMARC); **WhatsApp** über Meta WhatsApp Business Cloud API als optionale Integration (Feature-Flag; erfordert Meta-Business-Verifizierung des Betreibers – Einrichtung parallel starten, MVP funktioniert ohne).
- Zustell-Logik: Outbox-Event `ticket.created` → n8n-Workflow `ticket-delivery`: formatiert Ticket (Kategorie, Dringlichkeit, Rückrufnummer, Zusammenfassung, Link zum Transkript im Portal) und versendet; Ergebnis wird via Callback `POST /internal/n8n/ticket-status` in `tickets.delivery` geschrieben. Bei Zustellfehler: Retry (3×), dann `tickets.status=failed` + Alert + Anzeige im Portal.
- **Dringend-Regel:** `urgency=high` (z. B. Rohrbruch) → zusätzlich SMS an konfigurierte Notfallnummer (Twilio SMS), direkt aus der api (nicht n8n), damit der Notfallpfad n8n-unabhängig ist.

## 5. Kalender-Integration (Level 2)

Interface `CalendarAdapter` (`fs_shared/telephony` analog): `list_slots(range, service_type) -> list[Slot]`, `book(slot, attendee) -> BookingResult`, `cancel(external_id)`.

| Adapter | MVP? | Hinweise |
| :--- | :--- | :--- |
| **Cal.com** (Cloud oder self-hosted) | **Ja (Referenz)** | Sauberste API (Event-Types, Availability, Bookings mit Idempotenz-Key). Für Kunden ohne eigenes System bieten wir gehostete Cal.com-Kalender an → voll kontrollierbarer Default. |
| Calendly | Ja | OAuth-App; Slots via Availability-API, Buchung via Scheduling-API. |
| Microsoft 365 | Phase 2 (direkt nach MVP) | Graph-API (`findMeetingTimes`, `events`); OAuth-Consent-Flow im Portal. Interface ist darauf ausgelegt. |

Regeln: Verfügbarkeiten werden **live** geprüft (kein Caching > 30 s); Buchung immer mit Idempotenz-Key; nach Buchung verifizierende Lese-Operation (Termin existiert wirklich) bevor die Assistentin bestätigt.

## 6. n8n-Workflows (alle versioniert in `n8n/workflows/*.json`)

| Workflow | Trigger (Outbox-Event) | Aktion |
| :--- | :--- | :--- |
| `ticket-delivery` | `ticket.created` | E-Mail/WhatsApp-Zustellung + Status-Callback |
| `call-summary` | `call.completed` | Tages-/Sofortbenachrichtigung an Kunden (konfigurierbar), Level-3-Hook: CRM-Sync (im MVP deaktiviert) |
| `tenant-provisioned` | `tenant.provisioned` | Interne Notifikation (Slack/E-Mail an Betreiber), Kunde in Betreiber-CRM anlegen |
| `daily-digest` | Cron in n8n | Tageszusammenfassung je Mandant (Anrufe, Tickets, Termine) |

Regeln: n8n hat **nur** Zugriff auf dedizierte `POST /internal/n8n/*`-Endpunkte (eigener Token) und niemals direkten DB-Zugriff. Jeder Workflow hat einen Error-Workflow (n8n-Feature), der Fehler an Sentry meldet.

## 7. E-Mail-Versand (transaktional)

Ein einziges Versandmodul `fs_shared/mail.py` (SMTP, TLS erzwungen, EU-Anbieter), Templates (Jinja2, deutsch, versioniert): `welcome`, `password_set`, `ticket`, `payment_issue`, `digest`. Jede Mail wird mit `message_id` + Zweck ins `audit_log` geschrieben (ohne Inhaltskopie personenbezogener Ticket-Daten).
