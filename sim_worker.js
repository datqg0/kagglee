// Web Worker for Kaggriculture In-Browser Python Simulation (Pyodide)

importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

let pyodide = null;
let engineReady = false;
let enginePyCode = "";
let runnerCorePyCode = "";

async function initPyodide(engineCode, runnerCode) {
  if (engineCode) enginePyCode = engineCode;
  if (runnerCode) runnerCorePyCode = runnerCode;

  if (!pyodide) {
    self.postMessage({ type: 'STATUS', message: '🚀 Loading Pyodide WebAssembly Python runtime...' });
    pyodide = await loadPyodide({
      indexURL: "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/"
    });
    
    self.postMessage({ type: 'STATUS', message: '📦 Loading NumPy & Math libraries...' });
    try {
      await pyodide.loadPackage(["numpy"]);
    } catch (e) {
      console.warn("NumPy preloading warning:", e);
    }
  }

  self.postMessage({ type: 'STATUS', message: '🌾 Setting up Kaggriculture Simulation Engine...' });
  
  // Write engine and runner files into virtual filesystem
  if (enginePyCode) {
    pyodide.FS.writeFile('kaggriculture_engine.py', enginePyCode);
  }
  if (runnerCorePyCode) {
    pyodide.FS.writeFile('runner_core.py', runnerCorePyCode);
  }
  
  await pyodide.runPythonAsync(`
import sys
import runner_core
import kaggriculture_engine
print("Kaggriculture Simulation Worker initialized successfully!")
  `);
  
  engineReady = true;
  self.postMessage({ type: 'READY' });
}

self.onmessage = async function(e) {
  const data = e.data;
  
  if (data.type === 'INIT') {
    try {
      await initPyodide(data.enginePy, data.runnerPy);
    } catch (err) {
      self.postMessage({ type: 'ERROR', error: 'Failed to initialize Python runtime: ' + err.message });
    }
  } else if (data.type === 'RUN_MATCH') {
    try {
      if (data.enginePy) enginePyCode = data.enginePy;
      if (data.runnerPy) runnerCorePyCode = data.runnerPy;

      if (!engineReady || !pyodide) {
        await initPyodide(enginePyCode, runnerCorePyCode);
      } else {
        if (enginePyCode) pyodide.FS.writeFile('kaggriculture_engine.py', enginePyCode);
        if (runnerCorePyCode) pyodide.FS.writeFile('runner_core.py', runnerCorePyCode);
      }
      
      const { agent0Code, agent1Code, agent0Name, agent1Name, seed, episodeSteps, startingMoney, boardSize } = data;
      
      // Auto-load any packages requested by agent codes
      if (agent0Code || agent1Code) {
        try {
          await pyodide.loadPackagesFromImports((agent0Code || "") + "\n" + (agent1Code || ""));
        } catch (e) {
          console.warn("loadPackagesFromImports warning:", e);
        }
      }
      
      // Callback for python to notify JS about simulation progress
      self.js_progress = (step, total, day, m0, m1) => {
        self.postMessage({
          type: 'PROGRESS',
          step,
          total,
          day,
          m0,
          m1,
          percent: Math.min(100, Math.round((step / total) * 100))
        });
      };
      
      pyodide.globals.set('g_agent0_code', agent0Code);
      pyodide.globals.set('g_agent1_code', agent1Code);
      pyodide.globals.set('g_agent0_name', agent0Name || "Player 1");
      pyodide.globals.set('g_agent1_name', agent1Name || "Player 2");
      pyodide.globals.set('g_seed', seed !== undefined && seed !== null && seed !== "" ? Number(seed) : null);
      pyodide.globals.set('g_steps', episodeSteps || 720);
      pyodide.globals.set('g_money', startingMoney || 3000);
      pyodide.globals.set('g_board_size', boardSize || 10);
      
      await pyodide.runPythonAsync(`
import js
import json
import runner_core

def py_progress(step, total, day, m0, m1):
    js.js_progress(step, total, day, m0, m1)

result = runner_core.run_match_simulation(
    g_agent0_code,
    g_agent1_code,
    agent0_name=g_agent0_name,
    agent1_name=g_agent1_name,
    seed=g_seed,
    episode_steps=g_steps,
    starting_money=g_money,
    board_size=g_board_size,
    progress_fn=py_progress
)

result_json = json.dumps(result)
      `);
      
      const resultJson = pyodide.globals.get('result_json');
      const parsedResult = JSON.parse(resultJson);
      
      self.postMessage({
        type: 'COMPLETE',
        result: parsedResult
      });
      
    } catch (err) {
      self.postMessage({
        type: 'ERROR',
        error: err.message || String(err)
      });
    }
  }
};
