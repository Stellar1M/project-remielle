# Code samples

A few hand-picked files and excerpts from Remielle's private repository, so you can see how the project is built.
They are for reading only. They are not the whole app and do not run on their own.

| File | Whole file or excerpt | What it shows | Skills / keywords |
|---|---|---|---|
| [streaming.py](streaming.py) | Whole file | Reads the LLM's reply as it streams in and cuts off the first full sentence, so her voice can start before the reply is finished. | Python, LLM streaming, OpenRouter, Server-Sent Events, regex, generators, latency |
| [reply_pipeline.py](reply_pipeline.py) | Excerpt | One reply is written, turned into speech and played at the same time on three threads. If you talk over her, she drops to a whisper, then stops cleanly and keeps only the words you heard. | Python, concurrency, threads and queues, producer/consumer, streaming, text-to-speech (TTS), latency, barge-in, cancellation, error handling |
| [voice_activity.py](voice_activity.py) | Excerpt | Decides from the microphone when you start talking, pause and stop, with a stricter rule while she is speaking so small noises don't cut her off. | Python, real-time audio, voice activity detection (Silero VAD), NumPy, turn-taking, signal thresholds |
| [websocket_bridge.py](websocket_bridge.py) | Excerpt | The link between the Python backend and the avatar web page: JSON messages, binary audio, one thread per page, shared state behind a lock, and an origin check so other websites can't connect. | Python, WebSockets, message protocol, thread safety, locks and events, web security (origin check) |
| [motion_primitives.js](motion_primitives.js) | Excerpt | A slice of the animation code: a spring, motion curves fitted to measured timings, part of the per-mood table, the blink curve, and gaze changes hidden inside a blink. | JavaScript, three.js, VRM, 3D animation, curve fitting, easing curves, damped springs, numerical integration, data-driven tuning |
| [tests/](tests/) | Three whole files (one comment line cut from register.mjs) and one excerpt | A small Node test harness that runs the browser animation code headless with a fake 3D model, plus 6 of the 21 animation tests (all 21 pass). Each steps the avatar frame by frame and checks its timing against measured numbers. | JavaScript, Node test runner (node:test), module resolve hooks, test doubles, deterministic tests, regression testing |

Each file's header says where it comes from (the file, the commit and the line ranges) and anything changed for
this showcase, such as a line not shown or a reworded comment.

## How to read the comments

- **f** = frames at 30 fps. **+8** = 8 frames after the trigger (for example, after her mood changes).
- **t50 / t90** = when half / 90 % of a move is done.
- **^^** = eyes shut in a smile.
- **ZZZ** = Zenless Zone Zero, the game the character comes from. Timings were measured from reference footage of her.
- **Fish** = Fish Audio, the text-to-speech service. **OpenRouter** = the LLM API gateway. **AIRI** = an open-source
  AI companion app I used before building this one.

Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.
