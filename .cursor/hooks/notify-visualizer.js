#!/usr/bin/env node
/**
 * Cursor afterFileEdit / afterTabFileEdit hook: notifies the Codebase Visualizer
 * server (when running) that a file was edited by AI, so it shows up as a cursor change.
 * Reads port from .cursor/codebase-visualizer-port.txt (written by the extension when the visualizer starts).
 */
const fs = require('fs');
const path = require('path');
const http = require('http');

let input = '';
process.stdin.setEncoding('utf-8');
process.stdin.on('data', (chunk) => { input += chunk; });
process.stdin.on('end', () => {
  try {
    const data = JSON.parse(input);
    const filePath = data.file_path;
    if (!filePath || typeof filePath !== 'string') return done();

    const cwd = process.cwd();
    const relPath = path.relative(cwd, path.resolve(filePath)).replace(/\\/g, '/');
    if (relPath.startsWith('..')) return done();

    const portFile = path.join(cwd, '.cursor', 'codebase-visualizer-port.txt');
    if (!fs.existsSync(portFile)) return done();
    const port = parseInt(fs.readFileSync(portFile, 'utf-8').trim(), 10);
    if (!port || port <= 0) return done();

    const ts = Date.now();
    const body = JSON.stringify({
      changes: [{ type: 'file_body_edited', path: relPath, timestamp: ts }],
      lastSendTimestamp: ts,
      source: 'cursor',
    });

    const req = http.request({
      hostname: 'localhost',
      port,
      path: '/api/rescan',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body, 'utf-8'),
      },
    }, () => done());
    req.on('error', () => done());
    req.setTimeout(2000, () => { req.destroy(); done(); });
    req.write(body);
    req.end();
  } catch (e) {
    done();
  }
});

function done() {
  process.exit(0);
}
