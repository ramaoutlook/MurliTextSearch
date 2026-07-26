"""
Splits a normalized text stream into sentences using the Hindi sentence-ending
punctuation marks (। and ॥), keeping the offset span of each sentence so callers
can map a match position back to "which sentence is this" and gather
neighbouring sentences.
"""
import re
from dataclasses import dataclass
from typing import List

SENTENCE_END_RE = re.compile(r'[।॥]')


@dataclass
class Sentence:
    text: str
    start: int   # offset in the stream (inclusive)
    end: int     # offset in the stream (exclusive, after the ।)
    index: int   # position in the sentence list


def split_into_sentences(stream: str) -> List[Sentence]:
    sentences: List[Sentence] = []
    start = 0
    idx = 0
    for m in SENTENCE_END_RE.finditer(stream):
        end = m.end()
        text = stream[start:end].strip()
        if text:
            sentences.append(Sentence(text=text, start=start, end=end, index=idx))
            idx += 1
        start = end

    # trailing text after the final । (rare, e.g. end of document) — keep as a sentence too
    tail = stream[start:].strip()
    if tail:
        sentences.append(Sentence(text=tail, start=start, end=len(stream), index=idx))

    return sentences


def find_sentence_containing(sentences: List[Sentence], offset: int) -> int:
    """Binary search for the sentence index whose [start, end) contains `offset`."""
    lo, hi = 0, len(sentences) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        s = sentences[mid]
        if offset < s.start:
            hi = mid - 1
        elif offset >= s.end:
            lo = mid + 1
        else:
            return mid
    # offset fell in inter-sentence whitespace/gap — clamp to nearest sentence
    return max(0, min(lo, len(sentences) - 1))
