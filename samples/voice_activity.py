# Turn-taking from the microphone: Silero voice activity detection on 32 ms blocks decides
# when the user starts talking, pauses and stops, with a stricter rule while she is speaking (barge-in).
# Part of Remielle: the Python backend (her ears). Imports are not shown: numpy as np,
# collections.deque, queue, sounddevice as sd, silero_vad_lite.SileroVAD.
# An excerpt (companion/ears.py at commit f0790fd, lines 54-146) from a private repository.
# Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

RATE = 16000      # Silero only works at 16 kHz (or 8 kHz)
BLOCK = 512       # Silero needs exactly 512 samples per call = 32 ms
THRESHOLD = 0.5   # Silero's "this is a voice" cutoff

START_BLOCKS = 6     # ~200 ms of voice in a row = you started talking (a cough won't count)
# While she's talking: 11 voiced blocks within the last 16 (~350 ms of voice in half a second).
# Speech has tiny gaps, so this counts them instead of needing one unbroken run.
BARGE_IN_WINDOW = 16
BARGE_IN_VOICED = 11
EARLY_BLOCKS = 28    # every ~0.9 s while you talk, the audio so far is handed over for an early look
PAUSE_BLOCKS = 9     # ~290 ms of quiet mid-sentence = a pause (where a listener nods), well before END_BLOCKS
PREROLL_BLOCKS = 15  # ~480 ms kept from just before that, so your first word isn't clipped
END_BLOCKS = 20      # ~640 ms of silence = you're done
TAIL_BLOCKS = 6      # ~200 ms of that silence is kept so your last word isn't clipped
MAX_BLOCKS = 15 * RATE // BLOCK  # 15 s cap

vad = SileroVAD(RATE)  # one instance: it remembers recent audio between calls


def is_voice(block):
    return vad.process((block.astype(np.float32) / 32768).tobytes()) >= THRESHOLD


def record_turn(blocks, stop=None, cancel=None, she_talking=None, on_start=None, on_early=None, on_beat=None):
    """Read 32 ms blocks until you've said something and gone quiet. Returns int16 samples, or None
    if stop() turned true before you started talking, or cancel() turned true at any point.
    she_talking(): true while she's speaking out loud; then a start is ~350 ms of voice within half a
        second (see BARGE_IN_*), not ~200 ms in a row.
    on_start(): called the moment you start talking (before you've finished), so she can react.
    on_early(samples): called about every 0.9 s while you're still talking, with the audio so far,
        so what you're saying can be checked before you finish. It mustn't block.
    on_beat(kind): "pause" when you go quiet for a moment mid-sentence, "resume" when you carry on.
        It mustn't block either."""
    before = deque(maxlen=PREROLL_BLOCKS + BARGE_IN_WINDOW)  # rolling window while we wait
    recent = deque(maxlen=BARGE_IN_WINDOW)                     # voice yes/no for the last half second
    voiced_run = 0
    for block in blocks:
        if stop and stop():
            return None  # e.g. you typed in the page instead, or switched the mic off
        before.append(block)
        voiced = is_voice(block)
        voiced_run = voiced_run + 1 if voiced else 0
        recent.append(voiced)
        if she_talking and she_talking():
            lead = BARGE_IN_WINDOW
            started = sum(recent) >= BARGE_IN_VOICED
        else:
            lead = voiced_run
            started = voiced_run >= START_BLOCKS
        if started:
            break  # you started talking
    else:
        return None  # the mic stream ended
    if on_start:
        on_start()

    # The same lead-in either way: ~480 ms from just before you started, plus the start itself.
    recording = list(before)[-(PREROLL_BLOCKS + lead):]
    started_at = len(recording)
    silent_run = 0
    paused = False
    for block in blocks:
        if cancel and cancel():
            return None  # e.g. the mic was switched off mid-sentence: throw the turn away
        recording.append(block)
        voiced = is_voice(block)
        silent_run = 0 if voiced else silent_run + 1
        if silent_run >= END_BLOCKS or len(recording) >= MAX_BLOCKS:
            break  # you stopped (or talked for 15 s)
        if on_beat and not paused and silent_run == PAUSE_BLOCKS:
            paused = True
            on_beat("pause")
        elif on_beat and paused and voiced:
            paused = False
            on_beat("resume")
        if on_early and (len(recording) - started_at) % EARLY_BLOCKS == 0:
            on_early(np.concatenate(recording))

    if silent_run > TAIL_BLOCKS:
        recording = recording[: len(recording) - (silent_run - TAIL_BLOCKS)]  # drop extra silence
    return np.concatenate(recording)


def mic_blocks():
    """Yield 32 ms blocks from the mic. The mic is only open while this is running."""
    q = queue.Queue()

    def on_audio(indata, frames, time, status):
        q.put(indata[:, 0].copy())  # runs on the audio thread: just hand the block over

    with sd.InputStream(samplerate=RATE, channels=1, dtype="int16", blocksize=BLOCK, callback=on_audio):
        while True:
            yield q.get()
