// Test harness, part 2: a Node resolve hook that copies the page's import map, so 'three' resolves in Node.
// Part of Remielle: the web front end's test suite (node:test).
// A whole file (companion/web/tests/importmap-hook.mjs at commit f0790fd, 12 lines) from a private repository.
// Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

// The page's bare names (index.html import map) point at the vendored files; Node needs the same mapping.
const vendor = (path) => new URL(`../vendor/${path}`, import.meta.url).href;
const MAP = {
  three: vendor('three/three.module.min.js'),
  '@pixiv/three-vrm-animation': vendor('three-vrm/three-vrm-animation.module.min.js'),
};

export function resolve(specifier, context, next) {
  if (MAP[specifier]) return next(MAP[specifier], context);
  if (specifier.startsWith('three/addons/')) return next(vendor(`three/addons/${specifier.slice(13)}`), context);
  return next(specifier, context);
}
