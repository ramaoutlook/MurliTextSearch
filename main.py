"""
FastAPI web API for searching Hindi text across Sakar/Avyakt Murli .docx files.

Run locally with:
    uvicorn main:app --reload --port 8000

Then POST to /search:
    {
      "search_text": "विश्व का मालिक",
      "file_path": "/absolute/path/to/Sakar_Murli_first_29_pages_for_claude.docx"
    }
"""
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from date_detector import detect_murli_type
from docx_reader import parse_docx
from matcher import find_matches
from result_writer import write_results_docx
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

from typing import Literal
import threading

DATA_DIR = os.path.join(BASE_DIR, "data")

MURLI_FILES = {
    "sakar": os.path.join(DATA_DIR, "Sakar Murli 94-99.docx"),
    "avyakt": os.path.join(DATA_DIR, "All Avyakt Murlis Latest.docx"),
}
MURLI_TYPE_LABEL = {"sakar": "SakarMurli", "avyakt": "AvyaktMurli"}

_parsed_cache: dict[str, object] = {}
_cache_lock = threading.Lock()  # avoids two requests parsing the same big file at once

def get_parsed_document(murli_key: str):
    if murli_key in _parsed_cache:
        return _parsed_cache[murli_key]
    with _cache_lock:
        if murli_key in _parsed_cache:          # re-check after acquiring lock
            return _parsed_cache[murli_key]
        file_path = MURLI_FILES[murli_key]
        if not os.path.isfile(file_path):
            raise HTTPException(
                status_code=500,
                detail=f"Server data file missing: {os.path.basename(file_path)}",
            )
        parsed = parse_docx(file_path, MURLI_TYPE_LABEL[murli_key])
        _parsed_cache[murli_key] = parsed
        return parsed

app = FastAPI(title="Murli Text Search API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class SearchRequest(BaseModel):
    murli_type: Literal["sakar", "avyakt"] = Field(..., description="Which fixed murli to search")
    search_text: str = Field(..., description="Hindi phrase to search for, e.g. 'विश्व का मालिक'")
    sentences_before: int = Field(2, ge=0)
    sentences_after: int = Field(2, ge=0)


class MatchOut(BaseModel):
    result_number: int
    date: str
    excerpt: str


class SearchResponse(BaseModel):
    murli_type: str
    total_matches: int
    # output_file: str
    results: list[MatchOut]


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest):
    if not req.search_text or not req.search_text.strip():
        raise HTTPException(status_code=400, detail="search_text must not be empty")

    try:
        parsed = get_parsed_document(req.murli_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read docx: {e}")

    try:
        matches = find_matches(parsed, req.search_text, req.sentences_before, req.sentences_after)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

    return SearchResponse(
        murli_type=parsed.murli_type,
        total_matches=len(matches),
        results=[
            MatchOut(result_number=i + 1, date=m.date_string, excerpt=m.context_text)
            for i, m in enumerate(matches)
        ],
    )


@app.get("/download/{filename}")
def download(filename: str):
    safe_name = os.path.basename(filename)  # prevent path traversal
    path = os.path.join(OUTPUT_DIR, safe_name)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=safe_name,
    )


@app.get("/")
def root():
    return {"status": "ok", "message": "Murli Text Search API — POST to /search"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
