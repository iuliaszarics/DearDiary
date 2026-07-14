const { spawn } = require('child_process');
const path = require('path');
process.env.NODE_OPTIONS = (process.env.NODE_OPTIONS || '') + ' --max-old-space-size=4096';

const scriptPath = path.join(__dirname, 'node_modules', 'react-scripts', 'bin', 'react-scripts.js');
const child = spawn('node', [scriptPath, 'start'], {
  stdio: 'inherit',
  shell: true,
  env: process.env
});
child.on('close', (code) => {
  process.exit(code);
});
