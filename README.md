<a name="readme-top"></a>

<div align="center">

<a href="#see-her"><img src=".github/readme/banner.png" width="100%" alt="Remielle, a 3D anime character with short pink hair, a white dress and pale wings, at dusk beside the title: Remielle, a personal AI desktop companion. She listens, talks back, remembers and moves in 3D, in a corner of my screen."></a>

<h1>Project Remielle</h1>

<p><b>Microphone → speech-to-text → streaming LLM → text-to-speech → 3D character, in real time.</b><br>Built in Python and JavaScript, with automated tests.</p>

<p>A personal AI companion modeled on Remielle Dan from <i>Zenless Zone Zero</i>, built step by step as a learning project to understand how an AI app is put together.<br>I design it and test every feature myself; AI coding agents (Claude Code) write much of the code.</p>

<p>Made by Thinh Nguyen, a finance student at Rutgers (class of 2029) aiming for fintech, financial systems and FP&A roles. <a href="#about-me">About me ↓</a></p>

<p>
<a href="#see-her"><img src="https://img.shields.io/badge/01-See%20her-3382ed?style=for-the-badge&labelColor=000000" alt="Jump to See her"></a>
<a href="#whats-built"><img src="https://img.shields.io/badge/02-What%27s%20built-3382ed?style=for-the-badge&labelColor=000000" alt="Jump to What's built"></a>
<a href="#code-samples"><img src="https://img.shields.io/badge/03-Code%20samples-3382ed?style=for-the-badge&labelColor=000000" alt="Jump to Code samples"></a>
<a href="#where-its-going"><img src="https://img.shields.io/badge/04-Roadmap-3382ed?style=for-the-badge&labelColor=000000" alt="Jump to the roadmap"></a>
<a href="#about-me"><img src="https://img.shields.io/badge/05-About%20me-3382ed?style=for-the-badge&labelColor=000000" alt="Jump to About me"></a>
</p>

<p>
<img src="https://img.shields.io/badge/Windows-desktop-3382ed?style=flat-square&labelColor=000000" alt="Windows desktop app">
<img src="https://img.shields.io/badge/Python-3-3382ed?style=flat-square&labelColor=000000&logo=python&logoColor=white" alt="Python 3">
<img src="https://img.shields.io/badge/Node.js-tests-3382ed?style=flat-square&labelColor=000000&logo=nodedotjs&logoColor=white" alt="Node.js, for the animation tests">
<img src="https://img.shields.io/badge/Electron-44-3382ed?style=flat-square&labelColor=000000&logo=electron&logoColor=white" alt="Electron 44">
<br>
<img src="https://img.shields.io/badge/three.js-r180-3382ed?style=flat-square&labelColor=000000&logo=threedotjs&logoColor=white" alt="three.js r180">
<img src="https://img.shields.io/badge/three--vrm-3.5-3382ed?style=flat-square&labelColor=000000" alt="three-vrm 3.5">
<img src="https://img.shields.io/badge/OpenRouter-Claude%20Sonnet%205.5-3382ed?style=flat-square&labelColor=000000&logo=openrouter&logoColor=white" alt="LLM: Claude Sonnet 5.5 through OpenRouter">
<img src="https://img.shields.io/badge/Fish%20Audio-voice%20%2B%20ears-3382ed?style=flat-square&labelColor=000000" alt="Fish Audio for her voice and ears">
<br>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-view%20only-ff7ab0?style=flat-square&labelColor=000000" alt="License: view only"></a>
</p>

</div>

> [!NOTE]
> This is a showcase. The source code is private: it's a personal project I don't want others to run or reuse, and it is built around her persona, her memory of me and a 3D model whose license doesn't allow sharing. This repo has a demo, screenshots, the architecture and [a few code samples](#code-samples). It is for viewing only (see the [LICENSE](LICENSE) and [What is not in this repo](#what-is-not-in-this-repo)).

## See her

<p align="center">
  <img src=".github/readme/outfit-black.png" width="35%" title="Black outfit" alt="Remielle standing in her black outfit with dark wings, full body, rendered in the app on a dusk sky">
  &nbsp;
  <img src=".github/readme/outfit-white.png" width="35%" title="White outfit" alt="Remielle standing in her white outfit with pale wings, full body, rendered in the app on a dusk sky">
</p>
<p align="center"><sub>Her black and white outfits, rendered live in the app's 3D view (three.js + three-vrm) on its own dusk sky.</sub></p>

<p align="center"><b>Acting, measured from footage</b><br><sub><i>Still being tuned (see the <a href="#where-its-going">roadmap</a>).</i></sub></p>

<p align="center">
  <img src=".github/readme/demo.webp" width="320" alt="Short looping clip of Remielle in her black outfit, head and shoulders: she laughs with closed ^^ eyes while her mouth moves, startles with a quick head pop, then tilts her head, curious, and settles back. A label in the corner names each mood.">
</p>
<p align="center"><sub>Recorded from the app's own page by a script that steps the real animation code frame by frame through a scripted sequence of moods, saved at 30 fps. The mouth is the app's lip-sync test, so there is no sound.</sub></p>

She laughs with ^^ eyes, startles, then tilts her head, curious. The label in the corner names the mood of each line.

Her timing isn't guessed. AI agents I direct track her face and head in Zenless Zone Zero footage frame by frame with Python scripts, and her animation is fitted to those numbers. My rule is that every new version is compared with the footage side by side and reviewed before I test it. The ^^ closes over about 8 frames. A startle peaks 8 frames in, and its wide eyes last only 2 frames. Her head moves settle along a curve fitted to the footage. The footage is never shared; only the numbers are in the code.

<details>
<summary><b>Four of her moods, and the numbers behind her acting</b></summary>

<p align="center">
  <img src=".github/readme/moods.png" width="556" alt="Four close-ups of Remielle in her white outfit in a 2 by 2 grid, one per mood: happy with closed ^^ eyes, curious with her biggest head tilt, sad with lowered lids, and thinking with her gaze down and to the side.">
</p>
<p align="center"><sub>Four of her nine moods, each as the face of a new line. Her hands stay down in these shots: the poses where her hands touch her face and chest are still being solved (roadmap, Next 5).</sub></p>

| What was measured | The number | In the code |
|---|---|---|
| Her face lands before her voice | 0.20 s (6 frames) | `FACE_LEAD` |
| An ordinary head move | starts at frame 4, half done at 10.9, 90% at 18.6 | `SETTLE`, `moveShape()` |
| A startle | peaks at 2.2× the move at frame 8, settled by frame 18 | `popBump()` |
| Surprise on her face | at most 0.25 strength, for only 2 frames | `ZZZ_MOODS.surprised` |
| Her closed-eye smile (^^) | half shut at frame 4.1, shut by about frame 8 | `setZzzEmotion()` |
| A blink | 0.233 s | `BLINK_CURVE` |
| Where she looks | changes inside a blink (in a fluster, under a squint), settled 15 to 29 frames in | `setGaze()` |
| Her idle | one exact 4 s loop, two 2 s sways from the hips | `IDLE_EXACT` |

Frames are 30 per second. Most of these are in the sample [`motion_primitives.js`](samples/motion_primitives.js); the rest of the animation code is private. The animation tests check these rules (see [Tests](#tests)).

</details>

## What's built

<table>
  <tr>
    <td width="50%" valign="top"><b>🧠 Brain</b><br>An LLM through OpenRouter. Replies stream in; the first sentence is voiced while the rest is still being written. History is trimmed and the persona is cached to keep each turn cheap.<br><sub>Sample: <a href="samples/streaming.py"><code>streaming.py</code></a> · <a href="samples/reply_pipeline.py"><code>reply_pipeline.py</code></a></sub></td>
    <td width="50%" valign="top"><b>🗣️ Voice</b><br>Fish Audio text-to-speech. Her pace and a little sound before she speaks follow her mood. Made-up lore names are pronounced with phoneme tags.</td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>👂 Ears</b><br>Microphone, Silero VAD and Fish speech-to-text. Hands-free by default.<br><sub>Sample: <a href="samples/voice_activity.py"><code>voice_activity.py</code></a></sub></td>
    <td width="50%" valign="top"><b>🤫 Talking over her</b><br>If I talk while she speaks she whispers, and she only stops for real words.<br><sub>Sample: <a href="samples/reply_pipeline.py"><code>reply_pipeline.py</code></a></sub></td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>🎧 Active listening</b><br>While I talk to her she leans in, nods, shows a soft face and makes small sounds.</td>
    <td width="50%" valign="top"><b>💾 Memory</b><br>Long-term facts and session summaries, updated in the background.</td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>💬 She speaks first</b><br>A greeting when she starts, check-ins after a quiet while, a welcome-back when I return to the PC.</td>
    <td width="50%" valign="top"><b>👀 Eyes</b><br>Looks at a window or screen I share.</td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>🎮 Game reactions</b><br>Notices wins, defeats and fights while I play and says one short line.</td>
    <td width="50%" valign="top"><b>🧍 Body</b><br>A VRM model in three.js and three-vrm: lip sync, blinking, eye contact, moods, life moments.<br><sub>Sample: <a href="samples/motion_primitives.js"><code>motion_primitives.js</code></a></sub></td>
  </tr>
  <tr>
    <td width="50%" valign="top"><b>🪟 Desktop window</b><br>Electron: frameless, transparent, always on top, click-through, in the corner of the screen.</td>
    <td width="50%" valign="top"><b>🎭 Dialogue acting</b><br>Her faces, head moves and timing in conversation, measured from Zenless Zone Zero footage instead of guessed, and checked by Node tests. <i>Still being tuned.</i><br><sub>Sample: <a href="samples/motion_primitives.js"><code>motion_primitives.js</code></a> · <a href="samples/tests"><code>tests/</code></a></sub></td>
  </tr>
</table>

<sub>Linked files are in <a href="samples/"><code>samples/</code></a>. The rest of the code is private.</sub>

<p align="right"><a href="#readme-top"><sub>back to top ↑</sub></a></p>

## How it fits together

```mermaid
flowchart TB
    subgraph backend["Python backend"]
        mic["Microphone"] --> vad["Silero VAD"] --> stt["Fish speech-to-text"] --> brain["LLM via OpenRouter"]
        screen["Shared screen"] --> eyes["Eyes and game watch"] --> brain
        brain <--> memory[("Long-term memory")]
        brain --> tts["Fish Audio voice"]
    end
    body["Page in Electron<br>3D body<br>three.js + three-vrm"]
    brain -->|"text and mood"| body
    tts -->|"audio, for lip sync"| body
    body -.->|"typed text"| brain
    classDef blue fill:#2a6fd6,stroke:#1b3a78,color:#ffffff
    classDef pink fill:#ff7ab0,stroke:#b8467a,color:#0a0c12
    class mic,vad,stt,screen,eyes,memory,tts blue
    class brain,body pink
```

The Python backend and the 3D page talk over a local WebSocket: JSON messages for text and moods, and binary frames for her voice. Besides what I type, the page sends the mic button and the windows I pick to share. Screen pictures are taken in Python; the page never sends them. The bridge is in the sample [`websocket_bridge.py`](samples/websocket_bridge.py).

## Code samples

The source is private, so [`samples/`](samples/) has a few hand-picked files and excerpts from it, for reading only. They are not the whole app and do not run on their own. [`samples/README.md`](samples/README.md) explains each one and how to read the comments. Start with [`streaming.py`](samples/streaming.py): it's the whole file, 78 lines.

- [`streaming.py`](samples/streaming.py): streaming an LLM reply and cutting off the first full sentence, so her voice starts before the reply is finished.
- [`reply_pipeline.py`](samples/reply_pipeline.py): concurrency, with one reply written, voiced and played at the same time on three threads, and a clean stop when I talk over her.
- [`voice_activity.py`](samples/voice_activity.py): real-time audio, deciding from the microphone when I start talking, pause and stop.
- [`websocket_bridge.py`](samples/websocket_bridge.py): a WebSocket message protocol between Python and the 3D page, with thread-safe shared state and an origin check.
- [`motion_primitives.js`](samples/motion_primitives.js): 3D animation in JavaScript, with a spring, curves fitted to measured timings and the blink curve.
- [`tests/`](samples/tests/): a small Node test harness that runs the browser animation code headless, and a few of the animation tests.

<p align="right"><a href="#readme-top"><sub>back to top ↑</sub></a></p>

## Tests

There are two test suites.

- **Animation tests** (21 Node tests): a small harness runs the browser animation code headless with a fake 3D model. Each test steps her frame by frame and checks her timing against the numbers measured from footage: when the ^^ closes, how high a startle peaks and how a head move settles. The harness and 6 of the tests are in [`samples/tests/`](samples/tests/).
- **Character tests**: 23 moments replayed against her real brain with a made-up memory and a made-up game screen. Her rules are checked automatically, and a small model (Haiku) scores each reply. A run costs about $0.10.

## What is not in this repo

- The full source code.
- Her persona and prompts.
- Her memory.
- API keys.
- The 3D model: 杏子酱Kyouko's fan edit of HoYoverse's official model. It is not included here and is never shared.

Every picture of her on this page is rendered by the app from my local copy of her model. None of them are game footage or game screenshots.

## Where it's going

<p>
<img src="https://img.shields.io/badge/done-8-3382ed?style=flat-square&labelColor=000000" alt="8 done">
<img src="https://img.shields.io/badge/in%20progress-3-ff7ab0?style=flat-square&labelColor=000000" alt="3 in progress">
<img src="https://img.shields.io/badge/todo-5-6e7681?style=flat-square&labelColor=000000" alt="5 to do">
</p>

Current work: making her dialogue acting match Zenless Zone Zero, measured from game footage.

**Now**

1. Acting fixes, round 2: surprise and fluster are built and wait for an independent review.
2. Arm moves that ease in and out like the footage, with blinks covering them so nothing pops.
3. Cutting build costs: routine animation work moves to free AI models, a stronger free model reviews each task, and Claude Code checks the result last.

**Next**

4. Dialogue blinks, a new face on every line, and a test of every mood-to-mood transition.
5. Contact hand poses solved in Blender so her hands meet her face and chest correctly.
6. Outfit fixes (skirt springs, sleeve cuffs) and a wing mesh fix.
7. Her idle stance.
8. Switching outfits at runtime.

<details>
<summary><b>Done so far (8)</b></summary>

- Brain: a streaming LLM with her persona.
- Voice that follows her mood.
- Ears: talking over her and active listening.
- Long-term memory and speaking first.
- Eyes: shared screen and game reactions.
- 3D body and Electron desktop window.
- ZZZ-accurate dialogue acting, v1.
- Acting fixes v2, part 1: test harness, idle, happy, sad.

</details>

<p align="right"><a href="#readme-top"><sub>back to top ↑</sub></a></p>

## Lessons so far

- **Whisper, don't pause.** Pausing her on every sound felt like buffering, so she whispers instead of stopping.
- **Compare in averages.** Fish's emotion tags made no steady difference over several takes each; speaking speed and sound tags do. Compare takes in averages, never one against one.
- **Phoneme tags for made-up names.** Fish makes up pronunciations for invented names; phoneme tags fix it, plain respellings get spelled out.
- **Small memory, whole memory.** At this size, every remembered fact in the prompt beats retrieval.
- **Hidden pages don't animate.** A hidden browser page or Electron window renders no frames, so time-based checks need frames driven by hand.

## About me

I'm Thinh Nguyen, a finance student at Rutgers University (class of 2029) and an accounting analyst intern, and I build my own software in Python and JavaScript. I'm aiming for fintech, financial systems and FP&A roles, where knowing both the accounting and the code helps.

📊 At work I process vendor invoices in Microsoft Dynamics 365. My first project there: a daily duplicate-invoice check in Excel Power Query that flags invoices at risk of being paid twice. I wrote the rules, Claude (AI) wrote the queries and the dashboard, and I set it up and run it every day.

Remielle isn't a finance tool, but it taught me how APIs, real-time data and automated testing fit together. I set the design, direct AI coding agents (Claude Code) to write much of the code, and test each feature myself.

💼 Open to summer 2027 internships and part-time roles: fintech, financial systems, FP&A, financial analysis

<p>
<a href="https://github.com/Stellar1M"><img src="https://img.shields.io/badge/GitHub-Stellar1M-3382ed?style=for-the-badge&labelColor=000000&logo=github&logoColor=white" alt="My GitHub profile"></a>
<a href="https://www.linkedin.com/in/thinh-nguyen-4a13082b3/"><img src="https://img.shields.io/badge/LinkedIn-Thinh%20Nguyen-3382ed?style=for-the-badge&labelColor=000000" alt="My LinkedIn profile"></a>
</p>

<div align="center">

<sub>A fan project, not affiliated with HoYoverse. Zenless Zone Zero and Remielle Dan belong to HoYoverse.<br>The 3D model is 杏子酱Kyouko's fan edit of HoYoverse's official model. It is not included here and is never shared; only renders of it appear on this page.</sub>

<br><br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117%2C45:1b3a78%2C75:3382ed%2C100:ff7ab0&height=140&section=footer&reversal=true&animation=twinkling">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:ffffff,45:cfe0fb,75:3382ed,100:ff7ab0&height=140&section=footer&reversal=true&animation=twinkling" alt="" width="100%">
</picture>

</div>
