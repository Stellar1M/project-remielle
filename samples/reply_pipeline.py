# The reply pipeline: one reply is written, voiced and played at the same time on three threads,
# and the user can talk over her (barge-in) to pause or cut it off cleanly.
# Part of Remielle: the Python backend (the main chat loop). Imports and setup are not shown: math, queue,
# threading, time, requests; stream_chat and Chunker (streaming.py); body (websocket_bridge.py: send, play, ...);
# voice (text-to-speech with Fish Audio: wav_seconds, speech_wav, mood_delivery, play); session, API_URL and
# build_payload (the request to the LLM through OpenRouter). The terminal is one of her interfaces, so print()
# here is chat output, not debugging. respond() stays one function on purpose: its threads share its local state.
# An excerpt (companion/chat.py at commit f0790fd, lines 142-371) from a private repository. One line is not
# shown: the one that spells out her emotion tag, whose format is part of her prompt. The rest is unchanged.
# Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

class HerTurn:
    """One reply of hers, and whether you're talking over it. The mic (OpenMic) sets:
        hold: while anything you're saying over her is still undecided, she drops to a whisper
              (or, before her first word, waits)
        cut:  it was real words, so she fades out and drops the rest of this reply
    and she sets speaking once her first words play (talking over her thinking is different)."""

    def __init__(self, since=None):
        self.hold = threading.Event()
        self.cut = threading.Event()
        self.speaking = threading.Event()
        # When the message she's answering started. Only what you start saying after this can talk
        # over this reply; anything earlier is about the reply before it.
        self.since = time.monotonic() if since is None else since
        self.holders = set()     # the things you're saying over her that aren't decided yet
        self.noise = None        # (text, when you started) of an "mm-hm" / "yeah, sure" that didn't cut her
        self.cut_after = None    # how long after you started talking it took to cut her off
        self.ended_at = None     # when she finished this reply

    def hold_for(self, said):
        self.holders.add(said)
        self.hold.set()

    def release(self, said):
        self.holders.discard(said)
        if not self.holders:
            self.hold.clear()

    def over(self):
        """She's done with this reply (cut off, or finished)."""
        return self.cut.is_set() or self.ended_at is not None


_line_open = threading.Event()  # her line is half printed (she's still speaking it)


def aside(note):
    """Print a note from the mic, on its own line even if her line is half printed."""
    print(("\n" if _line_open.is_set() else "") + note, flush=True)


def with_mood_changes(piece, changes):
    """The piece as printed in the terminal, with each mood change shown where it happens: "[→ sad]"."""
    for at, mood in sorted(changes, reverse=True):
        piece = f"{piece[:at].rstrip()} [→ {mood}] {piece[at:].lstrip()}"
    return piece.strip()


def heard_part(piece, wav, seconds):
    """The words of a piece you heard before you cut in, guessed from how far into the clip she got.
    Once a clip has started, you heard at least its first word."""
    words = piece.split()
    share = min(1.0, seconds / max(voice.wav_seconds(wav), 0.1))
    return " ".join(words[:math.ceil(len(words) * share)])


def respond(history, heard_at, turn, first=None):
    """Her reply, spoken while it's still being written. Three things run at once:
        thread 1 (write): her reply streams in; the first full sentence is passed on right away
        thread 2 (voice): each piece of text becomes her voice (Fish)
        this thread:      each piece plays as soon as its voice is ready
    While you talk over her (turn.hold) she pauses. If it was real words (turn.cut), all three stop:
    the stream is closed (so she stops writing and it stops costing), unvoiced text is dropped, and
    the clip playing is cut off mid-word.
    first: it's her move (see her_move); typing before her first word drops it, like talking does.
    Returns (reply, emotion, usage, timings, cut). reply holds only what you heard, ending in "—"
    if you cut in ("" if she hadn't said anything yet). Raises if she couldn't say anything at all."""
    to_voice = queue.Queue()  # (text, mood changes) pieces in order; None = no more
    to_play = queue.Queue()   # (text, wav, mood changes) in order; None = no more
    result = {"emotion": "neutral"}
    cut_in = turn.cut

    def write():
        spent = 0.0  # what a reply with no words cost (it gets one more go)
        try:
            for tries_left in (1, 0):
                chunker = Chunker()
                emotion_sent = False
                first_length = 0  # how long the first piece is, once it's been cut off
                stream = stream_chat(session, API_URL, build_payload(history))
                while True:
                    try:
                        text = next(stream)
                    except StopIteration as done:
                        result["reply"], result["usage"] = done.value
                        break
                    if cut_in.is_set():
                        stream.close()  # closes the connection, which tells OpenRouter to stop writing
                        return
                    if text.lstrip().startswith("<|") and "|>" not in text:
                        continue  # her emotion tag isn't complete yet
                    emotion, clean = body.read_emotion(text)
                    if not emotion_sent and "|>" in text:
                        # Her face and pose change now, a moment before she speaks (like in the game).
                        result["emotion"] = emotion
                        body.send({"type": "emotion", "name": emotion})
                        emotion_sent = True
                    piece = chunker.feed(clean)
                    if piece:
                        result["first_piece_at"] = time.perf_counter()
                        first_length = len(piece)  # a change right after its last word starts the next piece
                        changes = [(at, mood) for at, mood in body.mood_changes(text) if at < first_length]
                        to_voice.put((piece, changes))
                taken = chunker.taken  # (what the first piece already used, before finish() moves it on)
                whole = body.read_emotion(result["reply"])[1]
                if whole:
                    break
                # Only a face tag, or only slips (body.THINKING_RE): nothing to say or keep, so she tries again.
                if not tries_left:
                    raise RuntimeError(f"her reply had no words, twice: {result['reply'][:100]!r}")
                aside(f"  (her reply had no words, so she's trying again: {result['reply'][:80]!r})")
                spent += result["usage"].get("cost", 0)
            if spent:
                result["usage"] = {**result["usage"], "cost": result["usage"].get("cost", 0) + spent}
            piece = chunker.finish(whole)
            if piece:
                result.setdefault("first_piece_at", time.perf_counter())
                skipped = taken + len(whole[taken:]) - len(whole[taken:].lstrip())  # where this piece starts
                done = first_length if taken else 0
                changes = [(max(0, at - skipped), mood) for at, mood in body.mood_changes(result["reply"]) if at >= done]
                to_voice.put((piece, changes))
        except (RuntimeError, ValueError, requests.RequestException) as e:
            result["error"] = e
        finally:
            to_voice.put(None)

    def make_voices():
        mood, reply_start = None, True  # her mood as the next piece starts
        while (item := to_voice.get()) is not None:
            if cut_in.is_set():
                continue  # you cut in: don't make voices nobody will hear
            piece, changes = item
            # Her voice follows her mood (voice.mood_delivery): the mood this piece starts in, and
            # whether it's fresh (her reply starts, or her mood turns right where this piece starts).
            fresh = reply_start or bool(changes and changes[0][0] == 0)
            mood = changes[0][1] if changes and changes[0][0] == 0 else mood or result["emotion"]
            delivery = voice.mood_delivery(mood, fresh, reply_start)
            reply_start = False
            if changes:
                mood = changes[-1][1]
            start = time.perf_counter()
            wav = voice.speech_wav(piece, quiet=True, **delivery)
            result.setdefault("first_voice_took", time.perf_counter() - start)
            to_play.put((piece, wav, changes))
        to_play.put(None)

    if cut_in.is_set():
        to_play.put(None)  # you'd already carried on talking before she started: nothing to say
    else:
        threading.Thread(target=write, daemon=True).start()
        threading.Thread(target=make_voices, daemon=True).start()

    spoken = ""  # her caption so far: every piece she started saying
    heard = ""   # what you actually heard (all of it, unless you cut in)
    first_words = None
    try:
        while not cut_in.is_set():
            if first and not turn.speaking.is_set() and not body.inbox.empty():
                cut_in.set()  # you typed before she'd said anything: you go first
                break
            if turn.hold.is_set() and not turn.speaking.is_set():
                time.sleep(0.03)  # you're talking before she's said a word: she waits to hear what it is
                continue
            try:
                item = to_play.get(timeout=0.05)  # wakes up often to notice you talking
            except queue.Empty:
                continue
            if item is None:
                break
            piece, wav, changes = item
            shown = with_mood_changes(piece, changes)
            if first_words is None:
                first_words = time.perf_counter() - heard_at
                turn.speaking.set()
                body.send({"type": "state", "value": "speaking"})
                print(f"Remielle [{result['emotion']}]: {shown}", end="", flush=True)
            else:
                print(f" {shown}", end="", flush=True)
            _line_open.set()
            spoken = f"{spoken} {piece}".strip()
            body.send({"type": "reply", "text": spoken, "partial": True})  # her caption, as she says it
            if changes and wav:
                # Where in this clip her face changes, as a fraction of the way through it (the page times
                # each change to the audio). Speech is roughly even, so the share of the words is close enough.
                body.send({"type": "moods", "at": [[round(at / max(len(piece), 1), 3), mood] for at, mood in changes]})
            # The page if it can (it lip-syncs), else the speakers. Both whisper while you talk.
            played = body.play(wav, cut_in, turn.hold) if wav and body.connected() else None
            if wav and played is None:
                played = voice.play(wav, cut_in, turn.hold)
            if cut_in.is_set():
                part = heard_part(piece, wav, played) if wav else ""
                heard = f"{heard} {part}".strip()
            else:
                heard = spoken
    except KeyboardInterrupt:
        body.stop()  # Ctrl+C: don't leave her talking on the page
        raise
    cut = cut_in.is_set()
    if cut:
        body.stop()  # every open page, not just the one that was playing
    else:
        body.whisper(False)  # back to her normal voice for next time
    if spoken:
        print(" —" if cut else "")
    _line_open.clear()
    if cut:
        tail = " ".join(heard.split()[-5:])
        where = f'after "...{tail}"' if tail else "before she said anything"
        took = f", {turn.cut_after:.1f}s after you started" if turn.cut_after is not None else ""
        print(f"  (you cut in {where}{took})")

    if "error" in result and not spoken and not cut:
        raise result["error"]
    if "error" in result and not cut:
        print(f"  [her reply was cut off: {result['error']}]")
    if cut:
        # ... (1 line not shown: it sets tag, her emotion tag for this reply. Its format is part of her prompt.) ...
        reply = f"{tag}{heard}—" if heard else ""  # only what you heard; "—" marks where you cut in
    else:
        # Kept without her slips (body.tidy); cut off midway, it's what she actually said.
        reply = body.tidy(result["reply"]) if result.get("reply") else spoken
    if reply:
        body.send({"type": "reply", "text": body.read_emotion(reply)[1]})  # the whole line, for the page's history
    body.send({"type": "state", "value": "listening" if cut else "idle"})
    timings = {
        "first_words": first_words,
        "writing": result["first_piece_at"] - heard_at if "first_piece_at" in result else None,
        "voice": result.get("first_voice_took"),
    }
    return reply, result["emotion"], result.get("usage", {}), timings, cut
