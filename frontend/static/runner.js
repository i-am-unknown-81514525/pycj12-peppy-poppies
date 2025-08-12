console.log("[Worker] Downloading pyodide");
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.28.1/full/pyodide.mjs";
console.log("[Worker] Loading pyodide");
let pyodide = await loadPyodide();
console.log("[Worker] Complete pyodide load");
self.onmessage = function (e) {
    let json_value = JSON.parse(e.data);
    let code = json_value.code;
    let test_value = json_value.task;
    const dict = pyodide.globals.get("dict"); // https://github.com/pyodide/pyodide/issues/703#issuecomment-1937774811
    const globals = dict();
    let results = [];
    this.pyodide.runPython(code, { globals, locals: globals });
    postMessage("load;0");
    for (let i = 0; i < test_value.length; i++) {
        let value = test_value[i];
        let result = this.pyodide.runPython(`calc(${value})`, {
            globals,
            locals: globals,
        });
        results.push(result);
        postMessage(`run;${i}`);
    }
    globals.destroy();
    dict.destroy();
    postMessage(`result;${JSON.stringify(results)}`);
};
postMessage("pyodide-loaded;0");
