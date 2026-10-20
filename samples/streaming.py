# Streaming LLM replies: reads the model's reply token by token (Server-Sent Events)
# and cuts off the first full sentence so her voice can start before the reply is done.
# Part of Remielle: the Python backend (the reply pipeline). OpenRouter = the LLM API gateway it calls;
# AIRI = an open-source AI companion app I used before building this one.
# A whole file (companion/streaming.py at commit f0790fd, 78 lines) from a private repository.
# Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

"""Streaming: read her reply word by word as it's written, and cut it where she can start speaking.

OpenRouter streams with Server-Sent Events: the response stays open and sends lines like
    data: {"choices": [{"delta": {"content": "Welcome"}}]}
    data: {"choices": [{"delta": {"content": " back"}}]}
    data: [DONE]
Each line adds a few words. The last chunk also carries the token usage.
"""
import json
import re

# Any sentence end: . ! ? or ~ (and closing quotes), then a space. body.py judges her sentences between these,
# so every place the Chunker can cut is also a place body.py splits.
SENTENCE_GAP = re.compile(r"[.!?~]+[\"')\]]*\s+")
# A real sentence end: one followed by a capital letter that starts the next sentence. Not after
# Mr./Ms./Dr./St., and not a mid-sentence "..." followed by a lowercase word.
SENTENCE_END = re.compile(r"(?<!\bMr)(?<!\bMs)(?<!\bDr)(?<!\bSt)" + SENTENCE_GAP.pattern + r"(?=[A-Z\"(])")
FIRST_MIN_CHARS = 30  # a tiny first piece ("Oh my.") would sound choppy, so it joins the next sentence


def stream_chat(session, url, payload, timeout=60):
    """POST with stream=True and yield the reply text so far, every time more arrives.
    Returns (reply, usage) when the stream ends. Raises RuntimeError on any error."""
    text = ""
    usage = {}
    finish = None
    with session.post(url, json={**payload, "stream": True}, stream=True, timeout=timeout) as resp:
        if not resp.ok:
            raise RuntimeError(f"{resp.status_code} {resp.text[:300]}")
        # chunk_size=None hands over data as soon as it arrives instead of waiting to fill a buffer.
        for raw in resp.iter_lines(chunk_size=None):
            line = raw.decode("utf-8", "replace")
            if not line.startswith("data: "):
                continue  # blank lines and ": OPENROUTER PROCESSING" keep-alive comments
            data = line[6:]
            if data == "[DONE]":
                break
            chunk = json.loads(data)
            if "error" in chunk:
                raise RuntimeError(f"error mid-reply: {chunk['error']}")
            if chunk.get("usage"):
                usage = chunk["usage"]
            for choice in chunk.get("choices") or []:
                finish = choice.get("finish_reason") or finish
                piece = (choice.get("delta") or {}).get("content")
                if piece:
                    text += piece
                    yield text
    if not text.strip():
        raise RuntimeError(f"empty reply (finish_reason={finish})")
    return text.strip(), usage


class Chunker:
    """Splits her reply into at most two pieces to speak: the first sentence (so she can start
    early), then everything else once the reply is complete. Two pieces keep her speech smooth;
    many small pieces sounded choppy in AIRI."""

    def __init__(self):
        self.taken = 0  # how much of the text the first piece used
        self.first_sent = False

    def feed(self, text):
        """The text so far. Returns the first piece as soon as it's ready, else None."""
        if self.first_sent:
            return None
        for match in SENTENCE_END.finditer(text):
            if match.end() >= FIRST_MIN_CHARS:
                self.first_sent = True
                self.taken = match.end()
                return text[:match.end()].strip()
        return None

    def finish(self, text):
        """The complete text. Returns whatever hasn't been spoken yet (or None)."""
        rest = text[self.taken:].strip()
        self.first_sent = True
        return rest or None
