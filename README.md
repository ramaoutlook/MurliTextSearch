# Murli Text Search API

A local FastAPI service that searches an exact Hindi phrase across a **Sakar Murli**
or **Avyakt Murli** `.docx` file, pulls 2 sentences before + 2 sentences after every
match, and exports **all** results (date + excerpt, matched phrase bolded) into a
single new `.docx` file.

## 1. Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

Everything runs 100% locally/offline — no external API calls, no internet
required at request time, and no extra system tools needed.

## 2. Run the server

```bash
uvicorn main:app --reload --port 8000
```

## 3. Call the API

The easiest way: open **http://127.0.0.1:8000/docs** in your browser — FastAPI
auto-generates an interactive test page where you can type the search text
and file path and click "Execute", no curl needed.

Or via curl (Windows cmd):
```bash
curl -X POST http://127.0.0.1:8000/search -H "Content-Type: application/json" -d "{\"search_text\": \"विश्व का मालिक\", \"file_path\": \"C:\\path\\to\\Sakar_Murli_first_29_pages_for_claude.docx\"}"
```

Response:
```json
{
  "murli_type": "SakarMurli",
  "total_matches": 11,
  "output_file": "विश्व_का_मालिक_SakarMurli_20260717_091448.docx",
  "results": [
    {"result_number": 1, "date": "१-१-९४", "excerpt": "..."}
  ]
}
```

Download the generated Word file:
```bash
curl -O http://127.0.0.1:8000/download/विश्व_का_मालिक_SakarMurli_20260717_091448.docx
```

The file is also saved on disk under `outputs/`.

## How it works (short version)

1. **File type** is detected from the filename — must contain `Sakar Murli`
   or `Avyakt Murli`.
2. **Dates** are located via a type-specific pattern:
   - Sakar Murli: Devanagari-digit date + `प्रात:मुरली` (e.g. `१-१-९४ प्रात:मुरली...`)
   - Avyakt Murli: Latin-digit date + `ओम शान्ति अव्यक्त बापदादा मधुबन` (e.g. `21-01-69 ...`)
3. The whole document is flattened into one whitespace-normalized text stream,
   split into sentences on the Hindi purna viram `।`.
4. The exact search phrase is located (every occurrence, whitespace-tolerant
   so line-wraps inside a phrase don't break matching).
5. For each match, up to 2 sentences before/after are collected — capped so
   context never crosses into the previous/next lecture.
6. The date is resolved as the nearest preceding date heading.
7. All matches are written into one output `.docx`, named
   `{search_text}_{SakarMurli|AvyaktMurli}_{timestamp}.docx`.

## Files

| File | Purpose |
|---|---|
| `main.py` | FastAPI app (`/search`, `/download/{filename}`) |
| `date_detector.py` | Regex rules to detect murli type + date headings |
| `docx_reader.py` | Loads a `.docx` into a normalized text stream |
| `sentence_engine.py` | Splits text into sentences on `।` / `॥` |
| `matcher.py` | Finds phrase occurrences + builds before/after context |
| `result_writer.py` | Builds the final result `.docx` |
