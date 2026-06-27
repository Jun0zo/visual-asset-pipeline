"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const venvDir = path.join(root, ".venv");

function log(message) {
  console.log(`[visual-asset-pipeline] ${message}`);
}

function warn(message) {
  console.warn(`[visual-asset-pipeline] ${message}`);
}

function pythonCandidates() {
  if (process.platform === "win32") {
    return [
      { command: "py", prefix: ["-3"] },
      { command: "py", prefix: ["-3.13"] },
      { command: "py", prefix: ["-3.12"] },
      { command: "py", prefix: ["-3.11"] },
      { command: "py", prefix: ["-3.10"] },
      { command: "python", prefix: [] },
    ];
  }
  return [
    { command: "python3", prefix: [] },
    { command: "python3.13", prefix: [] },
    { command: "python3.12", prefix: [] },
    { command: "python3.11", prefix: [] },
    { command: "python3.10", prefix: [] },
    { command: "python", prefix: [] },
  ];
}

function spawn(candidate, args, options = {}) {
  return spawnSync(candidate.command, [...candidate.prefix, ...args], {
    cwd: root,
    stdio: options.stdio || "inherit",
    env: process.env,
  });
}

function resolvePythons() {
  const resolved = [];
  for (const candidate of pythonCandidates()) {
    const result = spawn(candidate, ["-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"], { stdio: "ignore" });
    if (!result.error && result.status === 0) {
      resolved.push(candidate);
    }
  }
  return resolved;
}

function venvPython() {
  if (process.platform === "win32") {
    return path.join(venvDir, "Scripts", "python.exe");
  }
  return path.join(venvDir, "bin", "python");
}

if (process.env.VAP_SKIP_PYTHON_INSTALL === "1") {
  log("Skipping Python dependency install because VAP_SKIP_PYTHON_INSTALL=1.");
  process.exit(0);
}

const pythons = resolvePythons();
if (pythons.length === 0) {
  warn("Python 3 was not found. Install Python 3.10+ and run `python3 -m pip install -e .` if the CLI cannot start.");
  process.exit(0);
}

for (const python of pythons) {
  if (!fs.existsSync(venvPython())) {
    log(`Creating package-local Python environment with ${python.command}.`);
    fs.rmSync(venvDir, { recursive: true, force: true });
    const result = spawn(python, ["-m", "venv", venvDir]);
    if (result.error || result.status !== 0) {
      warn(`Could not create .venv with ${python.command}; trying another Python if available.`);
      continue;
    }
  }

  log("Installing Python package dependencies into package-local environment.");
  const install = spawn({ command: venvPython(), prefix: [] }, ["-m", "pip", "install", "--disable-pip-version-check", "-e", "."]);
  if (install.error || install.status !== 0) {
    warn(`Python dependency install did not complete with ${python.command}; trying another Python if available.`);
    fs.rmSync(venvDir, { recursive: true, force: true });
    continue;
  }

  log("Python environment is ready.");
  process.exit(0);
}

if (!fs.existsSync(venvPython())) {
  warn("Could not create a package-local .venv. The CLI will fall back to your system Python.");
} else {
  warn("Python dependency install did not complete. The npm CLI wrapper is installed, but Python dependencies may need manual setup.");
}
process.exit(0);
