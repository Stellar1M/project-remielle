// Test harness, part 1: registers a Node module hook so the browser code can be tested in Node.
// Part of Remielle: the web front end's test suite (node:test).
// A whole file (companion/web/tests/register.mjs at commit f0790fd, 4 lines) from a private repository,
// minus one comment line (the command that runs the suite).
// Copyright (c) 2026 Thinh Nguyen. All rights reserved. Shown for viewing only.

import { register } from 'node:module';

register('./importmap-hook.mjs', import.meta.url);
