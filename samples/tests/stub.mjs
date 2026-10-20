// Test harness, part 3: a fake VRM model with no bones, so the whole animation loop runs headless
// and tests can step it frame by frame. Part of Remielle: the web front end's test suite (node:test).
// A whole file (companion/web/tests/stub.mjs at commit f0790fd, 25 lines) from a private repository.
// Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

import * as THREE from 'three';
import { Motion } from '../js/motion.js';

const EXPRESSIONS = ['blink', 'happy', 'sad', 'angry', 'surprised', 'relaxed', 'aa', 'ee', 'oh', 'halfLidded', 'mouthFrown', 'mouthNarrow', 'blush'];

// A VRM with no bones: enough for Motion to run its whole update loop; the face values it sets land in m.values.
export function makeMotion() {
  const values = {};
  const vrm = {
    scene: new THREE.Object3D(),
    humanoid: { getNormalizedBoneNode: () => null, getRawBoneNode: () => null, humanBones: {} },
    lookAt: {},
    meta: { metaVersion: '1' },
    expressionManager: { expressions: EXPRESSIONS.map((expressionName) => ({ expressionName })), setValue: (n, v) => { values[n] = v; } },
  };
  const camera = new THREE.PerspectiveCamera();
  camera.position.set(0, 1.4, 1.5);
  const m = new Motion(vrm, camera, new THREE.Scene(), {});
  m.values = values;
  return m;
}

export function run(m, frames, dt = 1 / 30, each) {
  for (let i = 0; i < frames; i++) { m.update(dt, null); each?.(m, i); }
}
