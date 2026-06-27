#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const root = path.resolve(__dirname, "..");
const script = path.join(root, "scripts", "run_visual_pipeline.py");
const srcPath = path.join(root, "src");
const userArgs = process.argv.slice(2);

function packageVenvPython() {
  if (process.platform === "win32") {
    return path.join(root, ".venv", "Scripts", "python.exe");
  }
  return path.join(root, ".venv", "bin", "python");
}

function candidatePythons() {
  const candidates = [];
  const venvPython = packageVenvPython();
  if (fs.existsSync(venvPython)) {
    candidates.push({ command: venvPython, prefix: [] });
  }
  if (process.platform === "win32") {
    candidates.push({ command: "py", prefix: ["-3"] });
    candidates.push({ command: "py", prefix: ["-3.13"] });
    candidates.push({ command: "py", prefix: ["-3.12"] });
    candidates.push({ command: "py", prefix: ["-3.11"] });
    candidates.push({ command: "py", prefix: ["-3.10"] });
    candidates.push({ command: "python", prefix: [] });
  } else {
    candidates.push({ command: "python3", prefix: [] });
    candidates.push({ command: "python3.13", prefix: [] });
    candidates.push({ command: "python3.12", prefix: [] });
    candidates.push({ command: "python3.11", prefix: [] });
    candidates.push({ command: "python3.10", prefix: [] });
    candidates.push({ command: "python", prefix: [] });
  }
  return candidates;
}

function run(candidate) {
  const env = {
    ...process.env,
    PYTHONPATH: [srcPath, process.env.PYTHONPATH].filter(Boolean).join(path.delimiter),
  };
  return spawnSync(candidate.command, [...candidate.prefix, script, ...userArgs], {
    cwd: root,
    env,
    stdio: "inherit",
  });
}

function runtimeStatus(candidate) {
  const version = spawnSync(candidate.command, [...candidate.prefix, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 4)"], {
    cwd: root,
    stdio: "ignore",
  });
  if (version.error && version.error.code === "ENOENT") {
    return "missing";
  }
  if (version.error || version.status === 4) {
    return "bad-python";
  }
  if (version.status !== 0) {
    return "missing";
  }

  const deps = spawnSync(candidate.command, [...candidate.prefix, "-c", "import PIL, numpy, skimage"], {
    cwd: root,
    stdio: "ignore",
  });
  if (deps.error && deps.error.code === "ENOENT") {
    return "missing";
  }
  return !deps.error && deps.status === 0 ? "ready" : "missing-deps";
}

let sawPythonWithoutDependencies = false;
let sawOldPython = false;
for (const candidate of candidatePythons()) {
  const status = runtimeStatus(candidate);
  if (status === "missing") {
    continue;
  }
  if (status === "bad-python") {
    sawOldPython = true;
    continue;
  }
  if (status === "missing-deps") {
    sawPythonWithoutDependencies = true;
    continue;
  }
  const result = run(candidate);
  if (result.error && result.error.code === "ENOENT") {
    continue;
  }
  if (result.error) {
    console.error(`visual-asset-pipeline failed to start ${candidate.command}: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status ?? 1);
}

if (sawPythonWithoutDependencies) {
  console.error("visual-asset-pipeline found Python, but the required Python packages are missing.");
  console.error("Run one of:");
  console.error("  npm install");
  console.error("  python3 -m pip install -e .");
} else if (sawOldPython) {
  console.error("visual-asset-pipeline requires Python 3.10+.");
  console.error("Install a newer Python, then run one of:");
  console.error("  npm install");
  console.error("  python3 -m pip install -e .");
} else {
  console.error("visual-asset-pipeline requires Python 3.10+.");
  console.error("Install Python, then run one of:");
  console.error("  npm install");
  console.error("  python3 -m pip install -e .");
}
process.exit(1);
