"""
Core matching engine: given a ParsedDocument and a search phrase, find every
occurrence, and for each one build a context window of up to 2 sentences
before + the matched sentence(s) + up to 2 sentences after, clipped so the
window never crosses into the previous/next lecture's date heading.
"""
import re
from dataclasses import dataclass
from typing import List, Optional

from docx_reader import ParsedDocument
from sentence_engine import Sentence, split_into_sentences, find_sentence_containing


def _normalize_search_text(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


@dataclass
class MatchResult:
    occurrence_index: int      # 0-based order of this match within the document
    date_string: str
    paragraph_index: int
    context_text: str          # the full before+matched+after excerpt
    bold_start: int            # offset of the matched phrase within context_text
    bold_end: int
    stream_offset: int         # offset of the match within the parsed document's stream


def _resolve_date(doc: ParsedDocument, offset: int) -> tuple[str, int]:
    """Return (date_string, paragraph_index) of the lecture containing this offset:
    the last date heading whose offset is <= the given offset."""
    date_string = "UNKNOWN"
    paragraph_index = -1
    for heading in doc.date_headings:
        if heading.offset <= offset:
            date_string = heading.date_string
            paragraph_index = heading.paragraph_index
        else:
            break
    return date_string, paragraph_index


def _lecture_bounds(doc: ParsedDocument, offset: int) -> tuple[int, int]:
    """Return (start, end) offsets in the stream for the lecture containing `offset`,
    i.e. from its date heading up to (but not including) the next date heading."""
    start = 0
    end = len(doc.stream)
    headings = doc.date_headings
    for i, heading in enumerate(headings):
        if heading.offset <= offset:
            start = heading.offset
            end = headings[i + 1].offset if i + 1 < len(headings) else len(doc.stream)
        else:
            break
    return start, end


def find_matches(doc: ParsedDocument, search_text: str, sentences_before: int = 2, sentences_after: int = 2) -> List[MatchResult]:
    norm_query = _normalize_search_text(search_text)
    if not norm_query:
        return []

    sentences = split_into_sentences(doc.stream)

    results: List[MatchResult] = []
    occurrence_index = 0
    search_start = 0
    stream = doc.stream

    while True:
        found_at = stream.find(norm_query, search_start)
        if found_at == -1:
            break
        match_end = found_at + len(norm_query)

        # bound the context window to this lecture only
        lecture_start, lecture_end = _lecture_bounds(doc, found_at)

        first_sent_idx = find_sentence_containing(sentences, found_at)
        last_sent_idx = find_sentence_containing(sentences, max(found_at, match_end - 1))

        # extend up to 2 sentences before, not crossing lecture_start
        before_idx = first_sent_idx
        taken_before = 0
        while taken_before < sentences_before and before_idx > 0 and sentences[before_idx - 1].start >= lecture_start:
            before_idx -= 1
            taken_before += 1

        # extend up to 2 sentences after, not crossing lecture_end
        after_idx = last_sent_idx
        taken_after = 0
        while taken_after < sentences_after and after_idx + 1 < len(sentences) and sentences[after_idx + 1].end <= lecture_end:
            after_idx += 1
            taken_after += 1

        context_start = sentences[before_idx].start
        context_end = sentences[after_idx].end
        context_text = stream[context_start:context_end]

        date_string, paragraph_index = _resolve_date(doc, found_at)

        results.append(
            MatchResult(
                occurrence_index=occurrence_index,
                date_string=date_string,
                paragraph_index=paragraph_index,
                context_text=context_text,
                bold_start=found_at - context_start,
                bold_end=match_end - context_start,
                stream_offset=found_at,
            )
        )

        occurrence_index += 1
        search_start = found_at + 1  # allow overlapping occurrences to be found too

    return results
