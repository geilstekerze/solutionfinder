# 03 – Voice-Orchestrator (Kernkomponente)

Der Voice-Orchestrator ist die kritischste Komponente. Für ihn gilt Null-Fehler-Toleranz im strengsten Sinn: **Kein Anruf darf jemals stumm bleiben oder unkontrolliert abbrechen.**

## 1. Anrufablauf (Happy Path)

```
1. Anrufer wählt Mandanten-Nummer → Twilio → Webhook POST /twilio/voice (Service: api)
2. api validiert Twilio-Signatur, löst Rufnummer → tenant_id auf (system_session),
   legt calls-Zeile an, antwortet mit TwiML:
     <Connect><Stream url="wss://.../media/{call_id}?token=..."/></Connect>
3. Twilio öffnet WebSocket zum voice-orchestrator (Media Stream, g711_ulaw 8kHz).
4. Orchestrator lädt Tenant-Konfiguration (Persona, Plan, Features) aus der DB,
   öffnet WebSocket zur Azure Realtime API, konfiguriert die Session
   (Instructions, Tools, Audioformat g711_ulaw in/out, Server-VAD).
5. Assistentin spricht Begrüßung + Pflicht-Hinweis (Dok. 06, Abschn. 4).
6. Audio fließt bidirektional durch die Audio-Bridge; Tool-Calls werden
   synchron gegen api /internal/tools/* ausgeführt.
7. Gesprächsende (Auflegen/Verabschiedung) → Abschluss-Sequenz (Abschn. 7).
```

## 2. Modulstruktur (`services/voice_orchestrator/app/`)

| Modul | Verantwortung |
| :--- | :--- |
| `main.py` | WS-Server (Route `/media/{call_id}`), Token-Prüfung, Health-Endpoint `/healthz`, Metrics `/metrics` |
| `call_session.py` | Eine Instanz pro Anruf; besitzt beide WebSockets, Lifecycle, Cleanup (garantiert via `try/finally`) |
| `state_machine.py` | Expliziter Zustandsautomat (Abschn. 3) |
| `audio_bridge.py` | Frame-Weiterleitung Twilio↔Realtime, Barge-in (Abschn. 5), Jitter-Toleranz |
| `tool_dispatcher.py` | Ausführung der Function-Calls (Abschn. 6), Timeouts, Fehlerantworten |
| `fallback.py` | Voicemail-Fallback: vorproduzierte Ansage abspielen, Aufnahme, asynchrone Transkription (Abschn. 8) |
| `session_config.py` | Aufbau der Realtime-`session.update`-Payload aus Tenant-Konfiguration (Instructions-Template, Tools je Plan) |

## 3. Zustandsautomat (verbindlich)

```
INIT ──▶ CONNECTING_AI ──▶ GREETING ──▶ CONVERSATION ⇄ TOOL_RUNNING
  │            │               │             │
  │            ▼               ▼             ▼
  └──────▶ FALLBACK_VOICEMAIL ◀──────── (bei irreparablem Fehler)
                    │
                    ▼
               CLOSING ──▶ DONE
```

Regeln:
- Jeder Zustandsübergang wird geloggt (`call_id`, `from`, `to`, `reason`) und als Metrik gezählt.
- `CONNECTING_AI` hat ein Budget von **3 s**; danach zwingend `FALLBACK_VOICEMAIL` (kein weiteres Warten).
- Aus jedem Zustand führt jeder unbehandelte Fehler nach `FALLBACK_VOICEMAIL`, nie zum Verbindungsabbruch. Nur wenn auch der Fallback fehlschlägt (z. B. Twilio-WS tot), wird aufgelegt – das ist der einzige erlaubte harte Abbruch und erzeugt einen Sentry-Alert mit höchster Priorität.
- `TOOL_RUNNING` blockiert nicht die Audio-Bridge: Während ein Tool läuft, kann die Assistentin Füll-Feedback geben („Einen Moment, ich schaue nach…" – von der Realtime API selbst gesteuert; das Tool-Ergebnis wird nachgereicht).

## 4. Realtime-Session-Konfiguration

- **Turn-Detection:** Server-VAD der Realtime API (semantische VAD-Variante, sofern im Deployment verfügbar; sonst Standard-Server-VAD mit `silence_duration_ms=500`).
- **Audio:** `input_audio_format=g711_ulaw`, `output_audio_format=g711_ulaw` – identisch zu Twilio, keine Transcodierung im Orchestrator (nur Base64-Umverpackung der Frames).
- **Instructions:** gerendertes Template aus `persona_config` des Mandanten. Feste Bestandteile (nicht kundenkonfigurierbar): Datenschutz-Verhalten (keine Halluzination von Firmenfakten – Antworten zu Firmenwissen NUR aus `search_knowledge`-Ergebnissen), Eskalationsregeln, Gesprächsende-Protokoll, Sprachvorgabe Deutsch (weitere Sprachen als Tenant-Option).
- **Transkription:** `input_audio_transcription` aktiviert; Assistentin-Text aus `response.output_audio_transcript.done`-Events. Beide Seiten werden fortlaufend als `call_transcript_items` gepuffert (Batch-Insert alle 2 s, Flush am Ende).
- **Tools je Plan:**
  - Level 1: `create_ticket`, `end_call`
  - Level 2: zusätzlich `search_knowledge`, `check_availability`, `book_appointment`, `transfer_call`

## 5. Audio-Bridge & Barge-in

1. Twilio-`media`-Frames (20 ms) → `input_audio_buffer.append` an Realtime API. Kein eigener Puffer > 100 ms (Latenz).
2. Realtime-`response.output_audio.delta` → Twilio-`media`-Frames. Der Orchestrator hält einen **Auslauf-Puffer** und trackt via Twilio-`mark`-Events, wie viel Audio bereits abgespielt wurde.
3. **Barge-in:** Bei `input_audio_buffer.speech_started` von der Realtime API: sofort (a) Twilio `clear`-Message senden (verwirft gepuffertes Audio beim Anbieter), (b) laufende Response mit `response.cancel` abbrechen, (c) via `conversation.item.truncate` das Assistentin-Item auf die tatsächlich gehörte Audiodauer kürzen (aus `mark`-Tracking), damit der Gesprächskontext der Wahrheit entspricht. Zielzeit gesamt: **< 400 ms** (Metrik `barge_in_latency_seconds`).
4. Verbindungsüberwachung: Heartbeat/Ping auf beiden WebSockets alle 5 s; ausbleibende Twilio-Frames > 10 s → Anruf gilt als tot → Cleanup; Realtime-WS-Fehler → Abschn. 8.

## 6. Tool-Contracts (JSON-Schemas für Function-Calling)

Alle Tools antworten in ≤ 3 s oder mit definiertem Fehlerobjekt `{"ok": false, "user_message": "<vorformulierter deutscher Satz für die Assistentin>"}` – die Assistentin liest bei Fehlern **nur** `user_message` vor, nie technische Details.

| Tool | Parameter (Pflicht) | Verhalten |
| :--- | :--- | :--- |
| `create_ticket` | `category`, `urgency`, `summary`, optional `caller_name`, `callback_number` | Legt `tickets`-Zeile an, triggert Outbox-Event `ticket.created` (Zustellung via Dok. 05). Antwort enthält Bestätigungstext. |
| `search_knowledge` | `query` | RAG-Retrieval (Dok. 04); Antwort: max. 3 Passagen + Quellen-Dateinamen. Leeres Ergebnis → explizites `{"found": false}` (Assistentin sagt, dass sie es nicht weiß und bietet Ticket an). |
| `check_availability` | `date_range_start`, `date_range_end`, optional `service_type` | Fragt CalendarAdapter; Antwort: max. 5 konkrete Slots (ISO 8601 + menschenlesbar deutsch). |
| `book_appointment` | `slot_start`, `attendee_name`, optional `attendee_phone`, `note` | Bucht via CalendarAdapter mit Idempotenz-Key `call_id + slot_start`; legt `appointments`-Zeile an. Slot inzwischen weg → `{"ok": false, "reason": "slot_taken", "alternatives": [...]}` . |
| `transfer_call` | `target` (konfigurierter Ziel-Alias, z. B. `"notfall"`) | Nur konfigurierte Ziele des Mandanten zulässig (nie freie Nummern vom Modell). Twilio-Call-Update auf `<Dial>`. |
| `end_call` | `farewell_said: bool` | Startet Abschluss-Sequenz (Abschn. 7). |

Alle Schemas liegen als Pydantic-Modelle in `fs_shared/models/tools.py`; dieselben Modelle erzeugen die JSON-Schemas für die Realtime-Session (eine Quelle der Wahrheit).

## 7. Abschluss-Sequenz (immer, auch nach Fallback)

1. `calls`-Zeile finalisieren (`ended_at`, `outcome`, `metrics`).
2. Transkript-Restpuffer flushen.
3. Zusammenfassung + Intent generieren: asynchroner Job (arq) mit normalem Chat-Completion-Modell (Azure, EU) – **nicht** im Anrufprozess.
4. Outbox-Event `call.completed` schreiben (eine Transaktion mit Schritt 1).
5. WebSockets schließen, Redis-State löschen, Metriken emittieren.
Schritte 1–4 laufen in `try/finally` – auch bei Crash der Session wird ein `error_fallback`-Outcome persistiert (Reaper-Task findet verwaiste Calls > 2 h und finalisiert sie).

## 8. Degradations-Matrix (verbindlich, wird in WP4/WP11 getestet)

| Ausfall | Erkennung | Verhalten |
| :--- | :--- | :--- |
| Realtime API nicht erreichbar / Verbindungsaufbau > 3 s | Timeout in `CONNECTING_AI` | Fallback-Voicemail: vorproduzierte Ansage („…hinterlassen Sie Ihr Anliegen…"), Aufnahme via Twilio `<Record>`, asynchrone Transkription (Azure STT, EU) → Ticket. Outcome `voicemail_fallback`. |
| Realtime-WS bricht mitten im Gespräch ab | WS-Close/Error-Event | **Ein** Reconnect-Versuch mit Kontext-Neuaufbau (Instructions + Kurzzusammenfassung des bisherigen Transkripts) in ≤ 2 s, Assistentin überbrückt nicht (Stille ≤ 2 s ist akzeptabel); scheitert er → Entschuldigungssatz aus Fallback-Ansage + Voicemail. |
| Tool-Timeout (api antwortet nicht in 3 s) | httpx-Timeout | Tool-Fehlerobjekt mit `user_message`; Gespräch läuft weiter (z. B. Ticket statt Terminbuchung anbieten). |
| DB nicht erreichbar beim Anrufeingang | Fehler in `/twilio/voice` | Statisches Not-TwiML (ohne DB): allgemeine Ansage + `<Record>`; Aufnahme wird nach DB-Recovery nachverarbeitet (Twilio-Recording-Webhook). |
| Kalender-Provider down | Adapter-Fehler | `check_availability`/`book_appointment` liefern Fehlerobjekt → Assistentin bietet Rückruf-Ticket an. |
| n8n down | Outbox-Retry | Keinerlei Auswirkung auf Anrufe; Events werden nachgeliefert. |
| Orchestrator-Deploy während laufender Gespräche | SIGTERM | Graceful Shutdown: keine neuen Sessions, laufende Gespräche bis max. 10 min zu Ende führen (Compose `stop_grace_period: 600s`); Rolling-Ersatz startet parallel. |

## 9. Kapazität & Nebenläufigkeit

- Eine Orchestrator-Instanz: Ziel **50 gleichzeitige Gespräche** (asyncio; CPU-arm, da keine Transcodierung). Lasttest in WP11 verifiziert das mit synthetischen Media-Streams.
- Semaphore `MAX_CONCURRENT_CALLS` (konfigurierbar); darüber hinausgehende Anrufe erhalten sofort die Fallback-Voicemail (nie Warteschleife ohne Info).
- Pro Anruf gilt ein Gesprächs-Zeitlimit (Default 15 min, Tenant-konfigurierbar) mit höflicher Ansage vor dem Ende – Schutz vor Kosten-Runaway.

## 10. Metriken (Pflicht, Prometheus)

`fs_calls_active`, `fs_call_setup_seconds` (Histogramm), `fs_first_response_seconds`, `fs_response_latency_seconds`, `fs_barge_in_latency_seconds`, `fs_tool_latency_seconds{tool=…}`, `fs_call_outcome_total{outcome=…}`, `fs_realtime_reconnects_total`, `fs_fallback_total{reason=…}`, `fs_ws_frames_dropped_total`.
