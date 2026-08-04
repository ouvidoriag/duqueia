module.exports = {
  apps: [
    {
      name: "duque-ia",
      script: "setup_and_run.py",
      interpreter: process.platform === "win32" ? "python" : "python3",
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
