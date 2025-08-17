console.log("[Worker] Downloading pyodide");
import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.28.1/full/pyodide.mjs";
console.log("[Worker] Loading pyodide");
let pyodide = await loadPyodide();
console.log("[Worker] Complete pyodide load");
self.onmessage = function (e) {
    let json_value = JSON.parse(e.data);
    console.log(json_value);
    let code = json_value["code"];
    let test_value = json_value["task"];
    const dict = pyodide.globals.get("dict"); // https://github.com/pyodide/pyodide/issues/703#issuecomment-1937774811
    const globals = dict();
    pyodide.runPython(
        `
def reformat_exc():
    import sys
    from traceback import format_exception
    return "".join(format_exception(sys.last_type, sys.last_value, sys.last_traceback))
`,
        { globals, locals: globals },
    );
    postMessage("start;0");
    let results = [];
    try {
        pyodide.runPython(code, { globals, locals: globals });
        postMessage("load;0");
        for (let i = 0; i < test_value.length; i++) {
            let value = test_value[i];
            let result = pyodide.runPython(`str(calc(${value}))`, {
                globals,
                locals: globals,
            });
            results.push(result);
            postMessage(`run;${i}`);
        }
    } catch (error) {
        const message = globals.get("reformat_exc")();
        console.error(message);
        postMessage(`error;message`);
        return;
    }
    globals.destroy();
    dict.destroy();
    postMessage(`result;${JSON.stringify(results)}`);
};
postMessage("pyodide-loaded;0");
