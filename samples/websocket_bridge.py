# The WebSocket bridge between the Python backend and the avatar web page: one thread per page,
# JSON control messages, binary audio frames, a lock around shared state, and an origin check.
# Part of Remielle: the Python backend (her body). Other helpers and screen sharing are not shown.
# An excerpt (companion/body.py at commit f0790fd, lines 1-11, 94-216, 307-355) from a private repository.
# The code is unchanged; a few comments were shortened for this showcase.
# Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

"""Her body: the avatar page (web/) and the WebSocket bridge it talks to.

The protocol is documented at the top of web/js/app.js. In short:
    page -> us:  user_text (typed in the page), mic (button on/off), sound (it can play audio now),
                 windows (list my windows), share (this window, or none), audio_done (she finished speaking)
    us -> page:  state, user_text (what you said out loud), reply (with her emotion tag), audio (WAV bytes),
                 windows (the list), sharing (which window, if any), glance (the picture she just took),
                 elsewhere (she's in her desktop window, so a browser tab stays quiet), goodbye (chat.py quit)

Her page usually runs in her own desktop window (Electron).
"""

# ... (lines 12-93 not shown) ...

inbox = queue.Queue()         # messages you typed (in the page or the terminal)
mic_on = threading.Event()    # set while at least one page has its mic button on
mic_off_count = 0             # how many times the mic has gone off (a stream must not outlive one)
audio_done = threading.Event()
ever_connected = threading.Event()  # a page has connected this session, so its mic button is in charge

_pages = set()                # open page connections (one per browser tab, or her desktop window)
_desktop_pages = set()        # the ones that are her desktop window: her voice goes only there
_mic_pages = set()            # the pages whose mic button is on; each tab has its own button
_sound_pages = set()          # the pages that can play her voice (browsers need one click on a page first)
_shared = {"id": None, "title": None, "fresh_until": 0.0}  # the window (or screen) you share, if any
JUST_SHARED_SECONDS = 60  # the first thing you say this soon after you start sharing counts as "look"
_last_clip = {"played": None}  # what the page said about the last clip: True, False (couldn't), None
_lock = threading.Lock()      # guards the sets above, and makes sends from different threads take turns


def _update_mic():
    """Call with _lock held. The mic is on only while some open page has its button on."""
    global mic_off_count
    if _mic_pages:
        mic_on.set()
    elif mic_on.is_set():
        mic_off_count += 1
        mic_on.clear()


def _handle(ws):
    """Runs on its own thread for each connected page, reading what the page sends."""
    desktop = "RemielleDesktop/" in (ws.request.headers.get("User-Agent", "") if ws.request else "")  # her desktop window says so
    with _lock:
        _pages.add(ws)  # a new page's mic button starts off, so it isn't in _mic_pages
        if desktop:
            _desktop_pages.add(ws)
        sharing = _shared["title"]
        whole = _shared["id"] is not None and eyes.is_screen(_shared["id"])
    ever_connected.set()
    try:
        ws.send(json.dumps({"type": "sharing", "title": sharing, "screen": whole}))  # so its screen button matches
    except ConnectionClosed:
        pass
    _tell_tabs_where_she_is()
    try:
        for raw in ws:
            try:
                msg = json.loads(raw)
            except (ValueError, TypeError):
                continue
            kind = msg.get("type")
            if kind == "user_text" and str(msg.get("text", "")).strip():
                inbox.put(str(msg["text"]).strip())
            elif kind == "mic":
                with _lock:
                    _mic_pages.add(ws) if msg.get("on") else _mic_pages.discard(ws)
                    _update_mic()
            elif kind == "sound":
                with _lock:
                    _sound_pages.add(ws) if msg.get("ready") else _sound_pages.discard(ws)
            elif kind == "windows":  # the screen button: which screens and windows could she see?
                listed = [{"id": cid, "title": name, "screen": eyes.is_screen(cid)}
                          for cid, name in eyes.list_screens() + eyes.list_windows()]
                with _lock:
                    try:
                        ws.send(json.dumps({"type": "windows", "list": listed}))
                    except ConnectionClosed:
                        pass
            elif kind == "share":
                wanted = msg.get("id")
                titles = dict(eyes.list_screens() + eyes.list_windows()) if isinstance(wanted, int) else {}
                _share(wanted if wanted in titles else None, titles.get(wanted))
            elif kind == "audio_done":
                _last_clip["played"] = msg.get("played", True)
                audio_done.set()
    except ConnectionClosed:
        pass
    finally:
        with _lock:
            _pages.discard(ws)
            _desktop_pages.discard(ws)
            _mic_pages.discard(ws)  # closing or refreshing a page never leaves the mic on
            _sound_pages.discard(ws)
            _update_mic()
            if not _pages or desktop:
                audio_done.set()  # nobody is left to finish playing her voice, so don't keep waiting
        _tell_tabs_where_she_is()


def start():
    """Start both servers in the background. Returns False if her body can't run (port busy)."""
    try:
        # Only her own page may connect. Without this, any website open in your browser could
        # connect to this port, turn the mic on and read the conversation.
        origins = [f"http://{host}:{PAGE_PORT}" for host in ("127.0.0.1", "localhost")]
        # max_size: a screenshot (a JPEG up to 1280 px wide, as base64) can be a few hundred KB.
        ws_server = serve(_handle, "127.0.0.1", WS_PORT, origins=origins, max_size=8 * 2**20)
    except OSError:
        print(f"  [body: port {WS_PORT} is busy (is chat.py already running?), so no avatar page this time]")
        return False
    threading.Thread(target=ws_server.serve_forever, daemon=True).start()
    try:
        handler = functools.partial(Handler, directory=str(WEB_DIR))
        page_server = http.server.ThreadingHTTPServer(("127.0.0.1", PAGE_PORT), handler)
        threading.Thread(target=page_server.serve_forever, daemon=True).start()
    except OSError:
        pass  # something else is already serving the page, which works just as well
    return True


def connected(desktop=False):
    """Some page is open (desktop: her desktop window is)."""
    with _lock:
        return bool(_desktop_pages if desktop else _pages)


def _tell_tabs_where_she_is():
    """While her desktop window is open, browser tabs stay quiet (no second voice, no "mm-hm")."""
    with _lock:
        here = bool(_desktop_pages)
        tabs = [ws for ws in _pages if ws not in _desktop_pages]
    for ws in tabs:
        try:
            ws.send(json.dumps({"type": "elsewhere", "on": here}))
        except ConnectionClosed:
            pass

# ... (lines 217-306 not shown) ...

def send(msg):
    """Send a message to every open page: a dict as JSON text, or bytes as a binary frame (audio).
    Her voice goes only to her desktop window while it's open, so a browser tab can't double it."""
    data = msg if isinstance(msg, bytes) else json.dumps(msg)
    with _lock:
        for ws in list(_desktop_pages if isinstance(msg, bytes) and _desktop_pages else _pages):
            try:
                ws.send(data)
            except ConnectionClosed:
                pass


_whispering = {"on": False}  # what the page was last told


def whisper(on):
    """Tell the page to drop her to a whisper (you started talking) or back to normal."""
    if _whispering["on"] != on:
        _whispering["on"] = on
        send({"type": "duck" if on else "unduck"})


def stop():
    """Fade her out and stop (you talked over her). Her volume is back to normal for next time."""
    _whispering["on"] = False
    send({"type": "stop"})


def play(wav, cancel=None, hold=None):
    """Her voice through the page (it lip-syncs), waiting until the page says she's done with it.
    While hold (a threading.Event) is set she drops to a whisper (you started talking); once cancel
    is set she fades out and stops (you talked over her). Gives up a few seconds after the clip
    should have ended. Returns how many seconds of it played, or None if the page couldn't play it
    (nobody has clicked the page yet), so the caller can use the speakers instead."""
    audio_done.clear()
    _last_clip["played"] = None
    send(wav)
    started = time.monotonic()
    while not audio_done.wait(timeout=0.03):
        if cancel is not None and cancel.is_set():
            stop()
            break
        if hold is not None:
            whisper(hold.is_set())
        if time.monotonic() - started > wav_seconds(wav) + 5:
            break  # the page never answered
    if _last_clip["played"] is False:
        return None
    return min(wav_seconds(wav), time.monotonic() - started)
