// Test harness, part 4: a few of the animation tests. Each one steps the avatar frame by frame and checks
// her timing (in frames at 30 fps) against numbers measured from reference footage.
// Part of Remielle: the web front end's test suite (node:test). 6 of the file's 21 tests; all 21 pass at this commit.
// An excerpt (companion/web/tests/zzz_acting.test.mjs at commit f0790fd, lines 1-17, 48-53, 94-119, 136-157,
// 229-258, 289-302, 318-337) from a private repository. The code is unchanged, except that one test name was
// reworded (the last test); some comments were reworded for this showcase too.
// The import line is the full file's: EMOTIONS and ZZZ are used by tests not shown here.
// How to read it: f = frames; +8 = 8 frames after the trigger; t50 = when half the move is done;
// ^^ = eyes shut in a smile; "the footage" = my reference footage of her.
// Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

import test from 'node:test';
import assert from 'node:assert/strict';
import { EMOTIONS, LOG_MAX, ZZZ, ZZZ_MOODS } from '../js/motion.js';
import { makeMotion, run } from './stub.mjs';

test('log is capped at LOG_MAX', () => {
  const m = makeMotion();
  const oldest = { type: 'oldest' };
  const newest = { type: 'newest' };
  m.log.push(oldest);
  for (let i = 0; i < LOG_MAX + 500; i++) m.log.push({ type: 'filler' });
  m.log.push(newest);
  run(m, 1);
  assert.ok(m.log.length <= LOG_MAX, `log has ${m.log.length}`);
  assert.ok(!m.log.includes(oldest));
  assert.ok(m.log.includes(newest));
});

// ... (lines 18-47 not shown) ...

// Math.random pinned for one body, so random timings (like when the gaze blink fires) are deterministic
function withRandom(value, fn) {
  const saved = Math.random;
  Math.random = () => value;
  try { return fn(); } finally { Math.random = saved; }
}

// ... (lines 54-93 not shown) ...

test('^^ t50 is +2..+6 frames', () => {
  // measured: her eyes are half way to ^^ at +4.1 f and shut by about +8
  const m = makeMotion();
  m.setEmotion('neutral', 0.7, { line: true });
  run(m, 60);
  const start = m.lid.x;
  const half = start + (ZZZ_MOODS.happy.lid - start) / 2;
  m.setEmotion('happy', 0.7, { line: true });
  let prev = start, t50 = null, shut = null;
  run(m, 20, 1 / 30, (mm, i) => {
    if (t50 === null && mm.lid.x >= half) t50 = i + (half - prev) / (mm.lid.x - prev);  // (interpolated between frames)
    if (i === 7) shut = mm.lid.x;
    prev = mm.lid.x;
  });
  assert.ok(t50 >= 2 && t50 <= 6, `t50 is +${t50} f`);
  assert.ok(shut > ZZZ_MOODS.happy.lid - 0.03, `lid is ${shut} at +8`);
});

// a settled neutral line in a conversation (her talking lid is open, 0), ready for the next line
function settledNeutral() {
  const m = makeMotion();
  m.setState('speaking');
  m.setEmotion('neutral', 0.7, { line: true });
  run(m, 90);
  return m;
}

// ... (lines 120-135 not shown) ...

test('sad lids stay open until the gaze blink, then lower over lidSlow', () => {
  // the lowering takes lidSlow (1.0 s) from the gaze frame; the ease is within 0.01 of 0.22 after ~26 f and lands at 30
  for (const roll of [0.01, 0.99]) {  // (the gaze blink fires +6..+12 f after the trigger)
    withRandom(roll, () => {
      const m = settledNeutral();
      const start = m.lid.x;
      assert.ok(Math.abs(start) < 1e-3, `neutral's talking lid is ${start}`);
      const trigger = m.time;
      m.setEmotion('sad', 0.7, { line: true });
      const lids = [];
      run(m, 90, 1 / 30, (mm) => lids.push(mm.lid.x));
      const gaze = m.log.find((e) => e.type === 'gaze' && e.t > trigger);
      assert.ok(gaze, 'no gaze change fired');
      const gazeFrame = Math.round((gaze.t - trigger) * 30);  // frames after the trigger (the first update is +1)
      for (let i = 0; i < gazeFrame; i++) assert.ok(Math.abs(lids[i] - start) < 0.02, `lid is ${lids[i]} at +${i + 1}, before the gaze blink at +${gazeFrame}`);
      const arrived = lids.findIndex((v, i) => i >= gazeFrame && Math.abs(v - ZZZ_MOODS.sad.lid) < 0.01) + 1 - gazeFrame;
      assert.ok(arrived >= 24 && arrived <= 45, `lids within 0.01 of ${ZZZ_MOODS.sad.lid} ${arrived} f after the gaze blink`);
      assert.ok(Math.abs(lids[gazeFrame + 29] - ZZZ_MOODS.sad.lid) < 1e-3, `lid is ${lids[gazeFrame + 29]} at the gaze blink +30`);
      for (const v of lids.slice(gazeFrame + arrived - 1)) assert.ok(Math.abs(v - ZZZ_MOODS.sad.lid) < 0.01, `lid left 0.22 for ${v}`);
    });
  }
});

// ... (lines 158-228 not shown) ...

const DEG = 180 / Math.PI;
// her head roll as commanded (the shaped move plus any beat on it), radians, + toward HER right
const rollNow = (m) => m.shaped.headRoll.x + m.beatValue('headRoll');

// a settled line in `mood` after settledNeutral's (the start pose of the next line)
function settledIn(mood) {
  const m = settledNeutral();
  if (mood !== 'neutral') { m.setEmotion(mood, 0.7, { line: true }); run(m, 90); }
  return m;
}

test('pop peak/final from start is 1.9-2.5 and holds', () => {
  // measured: the pop peaks at +8 ± 1, at 2.2x (2.16x) the move from where her head was; the raise holds (no return by +16).
  // (from sad's lowered head only the ratio is checked: the hold's 0.5° is for the neutral line's 2.5° move)
  for (const [before, name] of [['neutral', 'surprised'], ['neutral', 'awkward'], ['sad', 'surprised']]) {
    const m = settledIn(before);
    const start = m.shaped.headPitch.x;
    m.setEmotion(name, 0.7, { line: true });
    const pitch = [];
    run(m, 45, 1 / 30, (mm) => pitch.push(mm.shaped.headPitch.x));
    const final = m.shaped.headPitch.goal;
    const peak = pitch.reduce((a, b) => (Math.abs(b - start) > Math.abs(a - start) ? b : a));
    const ratio = (peak - start) / (final - start);
    assert.ok(ratio >= 1.9 && ratio <= 2.5, `${before} -> ${name}: peak/final is ${ratio}`);
    const at = pitch.indexOf(peak) + 1;  // (frames after the trigger: the first update is +1)
    assert.ok(at >= 7 && at <= 9, `${before} -> ${name}: peak at +${at}`);
    if (before !== 'neutral') continue;
    for (let f = 16; f <= 45; f++) assert.ok(Math.abs(pitch[f - 1] - final) * DEG < 0.5, `${name}: pitch is ${(pitch[f - 1] - final) * DEG}° off the final at +${f}`);
  }
});

// ... (lines 259-288 not shown) ...

test('surprised roll dips by 3.3 ± 0.5 at +6 and lands on its row roll', () => {
  // a quick swing toward her right first, even when the settle to her row's roll is long (from think: 13°)
  for (const before of ['neutral', 'think']) {
    const m = settledIn(before);
    const start = rollNow(m);
    m.setEmotion('surprised', 0.7, { line: true });
    run(m, 6);
    const dip = (rollNow(m) - start) * DEG;
    assert.ok(Math.abs(dip - 3.3) <= 0.5, `from ${before}: dips ${dip}° toward her right at +6`);
    run(m, 54);
    assert.equal(m.zzzRoll, ZZZ_MOODS.surprised.rollCmd);
    assert.ok(Math.abs(rollNow(m) - m.poseGoal.headRoll) * DEG < 0.5, `from ${before}: ${(rollNow(m) - m.poseGoal.headRoll) * DEG}° off her row roll`);
  }
});

// ... (lines 303-317 not shown) ...

test('the settle fits the footage on a neutral -> think line', () => {
  // measured on the footage: onset +5, t50 12.7, t90 19.0, 10-90 % in 13.7 f, 3.8 % overshoot (pp)
  const m = settledNeutral();
  const start = m.shaped.headRoll.x;
  m.setEmotion('think', 0.7, { line: true });
  const move = m.poseGoal.headRoll - start;
  const done = [0];  // done[f]: share of the move f frames after the trigger
  run(m, 60, 1 / 30, (mm) => done.push((mm.shaped.headRoll.x - start) / move));
  const beyond = Math.max(0.05, 0.3 / (Math.abs(move) * DEG));
  const onset = done.findIndex((v, f) => f > 0 && f + 2 < done.length && done.slice(f, f + 3).every((x) => x > beyond));
  const cross = (q) => { const f = done.findIndex((v) => v >= q); return f - 1 + (q - done[f - 1]) / (done[f] - done[f - 1]); };
  const [t10, t50, t90] = [0.1, 0.5, 0.9].map(cross);
  const over = (Math.max(...done) - 1) * 100;
  const got = `onset ${onset}, t10 ${t10}, t50 ${t50}, t90 ${t90}, overshoot ${over} pp`;
  assert.ok(onset >= 3 && onset <= 5, got);
  assert.ok(t50 >= 10.5 && t50 <= 12.5, got);
  assert.ok(t90 >= 17.5 && t90 <= 19, got);
  assert.ok(t90 - t10 >= 13.3 && t90 - t10 <= 14.7, got);
  assert.ok(over >= 3 && over <= 6, got);
});
