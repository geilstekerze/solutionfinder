# 04 – RAG-Pipeline (Wissensbasis pro Mandant)

## 1. Ziel

Der Mandant lädt Dokumente (PDF, DOCX, TXT, MD, CSV) im Portal hoch; die Assistentin beantwortet Anrufer-Fragen **ausschließlich** aus diesen Dokumenten. Falsche Firmenauskünfte sind der schlimmste fachliche Fehler des Produkts → das Retrieval ist konservativ konfiguriert: lieber „weiß ich nicht + Ticket" als eine erfundene Antwort.

## 2. Ingestion (Service `ingestion-worker`)

```
Upload (Portal) → documents(status=uploaded) + Datei in /data/uploads/{tenant_id}/{document_id}
   → arq-Job ingest_document(document_id)
      1. Textextraktion  (pypdf; DOCX: python-docx; Fallback OCR bewusst NICHT im MVP –
         Scan-PDFs ohne Textlayer → status=failed mit klarer Nutzer-Meldung im Portal)
      2. Normalisierung  (Whitespace, Silbentrennung, Kopf-/Fußzeilen-Heuristik)
      3. Chunking        (token-basiert: Ziel 400 Token, Überlappung 60, harte Grenze 512;
                          Absatz-/Überschriften-Grenzen bevorzugt)
      4. Embeddings      (Azure text-embedding-3-large, dimensions=1536, Batch ≤ 64,
                          Retry mit Backoff bei 429/5xx)
      5. Atomarer Swap   (Transaktion: alte chunks des Dokuments löschen, neue einfügen,
                          status=ready) – Re-Ingestion ist dadurch idempotent
```

Regeln:
- Datei-Limits: 25 MB/Datei, 200 Dateien/Mandant, Gesamttextgröße 20 MB/Mandant (Portal validiert vor Upload UND Server-seitig).
- Upload-Validierung: MIME-Sniffing (nicht nur Endung), Größenlimit, Virenscan (`clamav`-Container) vor Verarbeitung.
- Jeder Schritt setzt bei Fehler `documents.status=failed` + `error_detail` (deutsch, nutzerverständlich) – kein Dokument bleibt in `processing` hängen (Watchdog: > 15 min processing → failed + Sentry).

## 3. Retrieval (Bibliothek `fs_shared/rag`, aufgerufen vom Tool-Endpunkt)

1. Query-Embedding (gleiche Modell-/Dimensionskonfiguration wie Ingestion; Konfigurationsdrift wird beim Start geprüft: gespeicherte Dimension == konfigurierte Dimension, sonst Startabbruch).
2. Vektorsuche: `ORDER BY embedding <=> :query_vec LIMIT 12` **immer** innerhalb `tenant_session` (RLS) + explizitem `WHERE tenant_id = :tid` (Defense in Depth). Wegen des Post-Filtering-Problems globaler HNSW-Indizes wird pro Retrieval-Query `SET LOCAL hnsw.iterative_scan = relaxed_order` gesetzt (pgvector ≥ 0.8, siehe Dok. 02) – sonst kann der Recall bei Tenant-Filterung einbrechen.
3. Schwellwert: Cosine-Distanz > 0,55 wird verworfen. Bleibt nichts übrig → `{"found": false}`.
4. Re-Ranking im MVP: einfacher MMR (Maximal Marginal Relevance) über die 12 Kandidaten → Top 3.
5. Antwort an das Tool: max. 3 Passagen à ≤ 512 Token, je mit `filename` – die Assistentin darf Quellen nennen („laut unserer Preisliste…").
6. Latenzbudget gesamt ≤ 600 ms (Dok. 01, Abschn. 8); Embedding-Call ist der größte Posten → HTTP/2-Connection-Pooling, Timeout 2 s, kein Retry im Live-Pfad (Fehler → Tool-Fehlerobjekt).

## 4. Prompt-Kopplung (kritisch für Korrektheit)

In den Realtime-Instructions steht verbindlich (deutsch formuliert):
- Fragen zu Firma/Produkten/Preisen/Öffnungszeiten → **immer** erst `search_knowledge` aufrufen.
- Antworte zu Firmenfakten ausschließlich mit Inhalten aus dem Tool-Ergebnis. Wenn `found=false` oder die Passagen die Frage nicht beantworten: sage ehrlich, dass du es nicht sicher weißt, und biete an, ein Ticket fürs Team aufzunehmen.
- Niemals Preise, Termine oder Zusagen erfinden.

## 5. Portal-Funktionen (Service `api`)

- Upload mit Fortschritt, Statusanzeige je Dokument (`uploaded/processing/ready/failed` + Fehlertext), Löschen (entfernt Datei + Chunks in einer Transaktion), Re-Ingest-Button.
- „Wissens-Test"-Feld im Portal: Kunde stellt eine Testfrage, sieht die gefundenen Passagen und die Antwort – identischer Codepfad wie das Live-Tool (kein separater Testmodus, damit Test = Realität).

## 6. Qualitätssicherung & Isolationsnachweis (Pflichttests)

1. **Isolationstest (WP5):** Zwei Mandanten mit überlappenden Themen aber unterschiedlichen Fakten (z. B. verschiedene Preise). 20 Testfragen je Mandant; Assertion: keine Antwortpassage stammt aus dem falschen Mandanten (prüfbar über `document_id`-Herkunft). Zusätzlich Negativtest direkt auf DB-Ebene (RLS-Test aus Dok. 02).
2. **Retrieval-Eval (WP5, wiederholbar):** Goldset aus 30 Frage→erwartete-Passage-Paaren über 3 Beispiel-Dokumentsets (Handwerker, Arztpraxis, Kanzlei). Metrik: Recall@3 ≥ 0,85. Eval läuft als CI-Job `make eval-rag` (nicht in jedem PR, aber vor jedem Release).
3. **„Weiß-nicht"-Eval:** 10 Fragen, deren Antwort NICHT in den Dokumenten steht; Assertion: `found=false` bzw. Distanz-Schwelle greift in ≥ 9/10 Fällen.

## 7. Skalierungspfad (nicht implementieren, nur einhalten)

- Interface `VectorStore` in `fs_shared/rag/store.py` mit einziger MVP-Implementierung `PgVectorStore`. Methoden: `upsert_chunks`, `delete_document`, `search(tenant_id, embedding, k)`.
- Ab > 200 Mandanten oder > 5 M Chunks: Qdrant-Implementierung desselben Interfaces (Namespace = tenant_id, API-Key-Auth, gleiche EU-Maschine oder dedizierter Node). Migration = Re-Ingestion aus `documents` (Quelle der Wahrheit bleibt Postgres).
