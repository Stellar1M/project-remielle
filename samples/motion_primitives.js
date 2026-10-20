// Animation building blocks, fitted to timings measured from reference footage: a damped spring, a small
// per-mood table, move curves (settle, startle pop, laugh, composure), the blink curve, and a gaze change
// hidden inside a blink.
// Part of Remielle: the web front end (three.js / VRM avatar). A small slice of a ~2,500-line file.
// An excerpt (companion/web/js/motion.js at commit f0790fd, lines 38-65, 217-218, 231-232, 237, 240, 249,
// 256-290, 382-383, 390-395, 1419-1436) from a private repository. The code is unchanged, except that the
// mood table shows 3 of its 9 rows. The comments were rewritten in plain English for this showcase.
// clamp, rand and FPS (30) are defined elsewhere in the file; setGaze is a method of the Motion class.
// How to read it: f = frames at 30 fps; +8 = 8 frames after the trigger; ZZZ = Zenless Zone Zero, the game
// the character comes from.
// Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

// A spring pulls a value toward a target. freq (Hz) sets how fast; zeta how bouncy:
// 1 arrives without overshooting, below 1 overshoots a little and settles, like anime timing.
class Spring {
  constructor(freq, zeta, value = 0) {
    this.set(freq, zeta);
    this.x = value;
    this.v = 0;
  }

  set(freq, zeta) {
    this.w = 2 * Math.PI * freq;
    this.zeta = zeta;
    return this;
  }

  update(target, dt) {
    const steps = Math.max(1, Math.ceil(dt * 120));  // small steps keep it steady on slow frames
    const h = dt / steps;
    for (let i = 0; i < steps; i++) {
      this.v += (this.w * this.w * (target - this.x) - 2 * this.zeta * this.w * this.v) * h;
      this.x += this.v * h;
    }
    return this.x;
  }

  kick(velocity) { this.v += velocity; }  // a push: nods, nudges, follow-through
  snap(value) { this.x = value; this.v = 0; }
}

// ... (lines 66-216 not shown) ...

// Gaze: how many degrees of measured gaze make one unit of the avatar's look-at (side, up),
// and the look-at's limits in those units.
const GAZE_DEG = { side: 8.4, up: 11 };
const GAZE_MAX = { side: 1 / 0.55, up: 1 / 0.4 };
// Per mood, measured from the footage. roll = head tilt in degrees (+ = toward her left); rollCmd = the tilt the
// code asks for so that her eye line shows `roll` on screen (calibrated in the app, since her arm poses tilt the
// head a little); lid = how far her lids lower (0 = open, 1 = shut); lidSlow = seconds they take to lower;
// gaze = [pitch, yaw] in degrees, changed only inside a blink; arms = the arm pose she holds; pitch = head pitch
// in degrees (- = chin up); shapes = the move curve a channel uses (default: settle); face = expression weights;
// faceFor = frames that face holds before it eases out.
export const ZZZ_MOODS = {
  neutral: { roll: 3.3, rollCmd: 3.34, lid: 0, gaze: [0, 0], arms: 'rest' },
  // ... (6 more moods not shown) ...
  sad: { roll: -6.5, rollCmd: -6.57, lid: 0.22, lidSlow: 1.0, gaze: [-10, 8], arms: 'chestR', face: { sad: 0.8, mouthFrown: 0.3 } },
  surprised: { roll: 2.9, rollCmd: 2.93, pitch: -2.5, lid: 0, gaze: [0, 0], arms: 'rest', shapes: { headPitch: 'pop' }, face: { surprised: 0.25 }, faceFor: 2 },
};
// Move shapes: the share of a move done f frames after it starts, each fitted to measured timings.
// settle: starts at +4, half done at +10.9, 90 % at +18.6 (10 -> 90 % in 13.7 f), 4.6 % overshoot;
// startle pop: half its peak at +4, peak 2.2x the move at +8, final by +18;
// laugh rise: half at +6, 23 % over at +14, settled by +19;
// composure: a 46 % dip the other way over 10 f, then 90 % by +15, 4 % over.
const SETTLE = { zeta: 0.70, wn: 0.156, onset: 1.75 };
const s3 = (x) => { x = clamp(x, 0, 1); return x * x * (3 - 2 * x); };
function moveShape(shape, f) {
  if (f <= 0) return 0;
  if (shape === 'pop') return f <= 8 ? s3(f / 8) : 1;  // the move itself; popBump adds the overshoot
  if (shape === 'laugh') return f <= 14 ? 1.23 * s3(f / 14) : 1 + 0.23 * (1 - s3((f - 14) / 7));
  if (shape === 'composure') return f <= 10 ? -0.46 * s3(f / 10) : f <= 16 ? -0.46 + 1.5 * s3((f - 10) / 6) : 1.04 - 0.04 * s3((f - 16) / 4);
  const { zeta: z, wn, onset } = SETTLE;
  const t = Math.max(0, f - onset);
  if (t > 120) return 1;
  const wd = wn * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * wn * t) * (Math.cos(wd * t) + (z / Math.sqrt(1 - z * z)) * Math.sin(wd * t));
}
// The startle pop's overshoot, as a share of the move from her start pose (measured: 2.16x at the peak):
// 1.2 more at +8, gone by +18.
const popBump = (f) => (f <= 0 ? 0 : f <= 8 ? 1.2 * s3(f / 8) : 1.2 * (1 - s3((f - 8) / 10)));
const CARRY_FRAMES = 3;  // a change mid-move keeps the old move's speed, fading out over ~6 f
// A value that moves to each new goal along a move shape (instead of a spring), from wherever it is now.
class Shaped {
  constructor(value = 0) { this.reset(value); }
  reset(value) { Object.assign(this, { x: value, goal: value, from: value, t0: 0, shape: 'settle', slow: 1, v: 0, carry: 0, last: null }); }
  update(goal, time, shape = 'settle', slow = 1) {
    // (a new goal starts from where it was last frame, so this frame already moves: no frame standing still)
    if (goal !== this.goal) Object.assign(this, { from: this.x, goal, t0: this.last ?? time, shape, slow, carry: this.v });
    const frames = (time - this.t0) * FPS;
    const f = frames / this.slow;
    let x = this.from + (this.goal - this.from) * moveShape(this.shape, f);
    if (this.shape === 'pop') x += (this.goal - this.from) * popBump(f);
    x += this.carry * frames * Math.exp(-frames / CARRY_FRAMES);  // starts at the old speed, back to 0 by ~+15
    const step = this.last === null ? 0 : (time - this.last) * FPS;
    if (step > 0) this.v = (x - this.x) / step;
    this.last = time;
    this.x = x;
    return x;
  }
}

// ... (lines 291-381 not shown) ...

// The blink: how closed her eyes are (0 = open, 1 = shut) on each frame of a 60 fps clip, measured from footage
// and smoothed: close in 1-2 frames, shut for 3, open in 1, then a short tail. 14 frames = 0.23 s.
const BLINK_CURVE = [0, 0.674, 1, 1, 0.946, 0.652, 0.141, 0.087, 0.065, 0.038, 0.032, 0.016, 0.011, 0];
const BLINK_HZ = 60;
const blinkAt = (t) => {  // closure at t s after the close starts
  const f = t * BLINK_HZ;
  if (f >= BLINK_CURVE.length - 1) return 0;
  const i = Math.floor(f);
  return BLINK_CURVE[i] + (BLINK_CURVE[i + 1] - BLINK_CURVE[i]) * (f - i);
};

// ... (lines 396-1418 not shown) ...

  // Her gaze changes only inside a blink, fired 6-12 frames after the trigger, and holds until her next line,
  // so her eyes never visibly slide. Offsets in degrees: [pitch (+ up), yaw (+ toward her left)].
  // at: fire after this many frames instead; blink: false when something else hides the change (a squint).
  setGaze([pitch, yaw], { at = null, blink = true } = {}) {
    const goal = { x: clamp(yaw / GAZE_DEG.side, -GAZE_MAX.side, GAZE_MAX.side), y: clamp(pitch / GAZE_DEG.up, -GAZE_MAX.up, GAZE_MAX.up), pitch };
    const same = (a) => a && goal.x === a.x && goal.y === a.y;
    if (same(this.gazePending ?? this.gaze)) return;  // (already there, or already on its way)
    this.cancel('gaze');
    this.gazePending = null;
    if (same(this.gaze)) return;  // (back to the gaze she's showing before a pending change landed: nothing to do)
    this.gazePending = goal;
    const delay = (at ?? rand(6, 12)) / FPS;
    this.gazeAt = this.time + delay;
    this.schedule(delay, () => {
      if (blink) this.startBlink(true, true);
      this.gaze = goal;
      this.gazePending = null;
      this.gazeSlow = this.time + 1;
      this.log.push({ t: this.time, type: 'gaze', pitch, yaw });
    }, 'gaze');
  }
