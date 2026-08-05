const fs = require('fs');
const path = require('path');

function resolvePythonInterpreter() {
  const venvUnix = path.join(__dirname, '.venv', 'bin', 'python');
  const venvWin = path.join(__dirname, '.venv', 'Scripts', 'python.exe');

  if (fs.existsSync(venvUnix)) {
    return venvUnix;
  }
  if (fs.existsSync(venvWin)) {
    return venvWin;
  }

  // Fallback para intérprete do sistema
  return process.platform === "win32" ? "python" : "python3";
}

module.exports = {
  apps: [
    {
      name: "duque-ia",
      script: "setup_and_run.py",
      interpreter: resolvePythonInterpreter(),
      env: {
        NODE_ENV: "production",
        PORT: 3000
      },
      max_memory_restart: "1G",
      autorestart: true,
      watch: false
    }
  ]
};
