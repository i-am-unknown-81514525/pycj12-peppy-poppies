// Modern JavaScript with functional programming approach
// API Configuration
const API_BASE_URL = 'http://localhost:8001';

// Application State
let appState = {
    pyodide: null,
    currentChallenge: null,
    lastResults: [],
    captchaCompleted: false
};

// DOM Elements Cache
const elements = {
    pythonCaptchaDiv: () => document.getElementById('python-captcha'),
    codeEditor: () => document.getElementById('python-code'),
    outputArea: () => document.getElementById('output'),
    runCodeBtn: () => document.getElementById('runCodeBtn'),
    submitChallengeBtn: () => document.getElementById('submitChallengeBtn'),
    captchaBtn: () => document.getElementById('captchaBtn'),
    loginBtn: () => document.getElementById('loginBtn'),
    statusIndicator: () => document.getElementById('statusIndicator'),
    loadingSpinner: () => document.getElementById('loadingSpinner'),
    submitLoadingSpinner: () => document.getElementById('submitLoadingSpinner'),
    usernameInput: () => document.getElementById('username'),
    passwordInput: () => document.getElementById('password'),
    challengeDiv: () => document.querySelector('.captcha-challenge')
};

// Utility Functions
const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
};

const extractFunctionName = (question) => {
    // Always use 'calc' as the function name since users must create a calc function
    return 'calc';
};

// Status Management
const showStatus = (message, type = 'info') => {
    const indicator = elements.statusIndicator();
    if (!indicator) return;

    indicator.textContent = message;
    indicator.className = `status-indicator status-${type}`;
    indicator.style.display = 'block';

    // Auto-hide after 3 seconds for non-error messages
    if (type !== 'error') {
        setTimeout(() => {
            indicator.style.display = 'none';
        }, 3000);
    }
};

// Button State Management
const updateCaptchaButton = () => {
    const btn = elements.captchaBtn();
    if (!btn) return;

    if (appState.captchaCompleted) {
        btn.innerHTML = '<i class="fas fa-check-circle"></i> Challenge Completed';
        btn.className = 'btn btn-success';
        btn.disabled = true;
    } else {
        btn.innerHTML = '<i class="fas fa-code"></i> Complete Programming Challenge';
        btn.className = 'btn btn-secondary';
        btn.disabled = false;
    }
};

const updateSubmitButton = () => {
    const btn = elements.submitChallengeBtn();
    if (!btn) return;

    const hasResults = appState.lastResults.length > 0;
    const hasChallenge = appState.currentChallenge !== null;

    btn.disabled = !(hasResults && hasChallenge);
    btn.innerHTML = '<i class="fas fa-check"></i> Submit Challenge';
};

const setRunCodeLoading = (isLoading) => {
    console.log('setRunCodeLoading called with:', isLoading);
    const btn = elements.runCodeBtn();
    const spinner = elements.loadingSpinner();
    console.log('Button found:', !!btn);
    console.log('Spinner found:', !!spinner);

    if (!btn) {
        console.error('Run code button not found!');
        return;
    }

    btn.disabled = isLoading;
    if (spinner) {
        spinner.style.display = isLoading ? 'inline-block' : 'none';
    }

    btn.innerHTML = isLoading
        ? '<div class="loading-spinner" style="display: inline-block;"></div> Running...'
        : '<i class="fas fa-play"></i> Execute Code';

    console.log('Button state updated. Disabled:', btn.disabled, 'HTML:', btn.innerHTML);
};

const setSubmitLoading = (isLoading) => {
    const btn = elements.submitChallengeBtn();
    const spinner = elements.submitLoadingSpinner();
    if (!btn || !spinner) return;

    btn.disabled = isLoading;
    spinner.style.display = isLoading ? 'inline-block' : 'none';

    if (isLoading) {
        btn.innerHTML = '<div class="loading-spinner" style="display: inline-block;"></div> Verifying...';
    } else if (!appState.captchaCompleted) {
        btn.innerHTML = '<i class="fas fa-check"></i> Submit Challenge';
    }
};

// API Functions
const generateChallenge = async () => {
    try {
        const sessionId = generateUUID();
        const response = await fetch(`${API_BASE_URL}/api/challenge/generate-challenge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                website: window.location.hostname || 'localhost',
                session_id: sessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data.challenge_id;
    } catch (error) {
        console.error('Error generating challenge:', error);
        throw error;
    }
};

const getChallenge = async (challengeId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/challenge/get-challenge/${challengeId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error getting challenge:', error);
        throw error;
    }
};

const submitChallenge = async (challengeId, answers) => {
    try {
        const response = await fetch(`${API_BASE_URL}/api/challenge/submit-challenge`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                challenge_id: challengeId,
                answers: answers
            })
        });

        return {
            success: response.ok,
            status: response.status,
            data: response.ok ? await response.json() : await response.text()
        };
    } catch (error) {
        console.error('Error submitting challenge:', error);
        throw error;
    }
};

// UI Update Functions
const updateChallengeUI = () => {
    if (!appState.currentChallenge) return;

    const challengeDiv = elements.challengeDiv();
    const codeEditor = elements.codeEditor();

    if (challengeDiv) {
        challengeDiv.innerHTML = `
            <i class="fas fa-code"></i> ${appState.currentChallenge.question}
            <div class="code-highlight">
                <strong>Test Cases:</strong> Your function will be tested with inputs: [${appState.currentChallenge.tasks.join(', ')}]
            </div>
        `;
    }

    if (codeEditor) {
        const functionName = 'calc'; // Always use 'calc' as the function name

        codeEditor.placeholder = `# Write your Python code here
# ${appState.currentChallenge.question}

def calc(x: int):
    # Your implementation here
    # Example: return 673 + x
    pass`;

        codeEditor.value = '';
    }

    // Reset results
    appState.lastResults = [];
    updateSubmitButton();
};

// Challenge Management
const loadChallenge = async () => {
    try {
        showStatus('Loading challenge...', 'info');

        const challengeId = await generateChallenge();
        const challengeData = await getChallenge(challengeId);

        appState.currentChallenge = {
            id: challengeId,
            question: challengeData.question,
            tasks: challengeData.tasks
        };

        updateChallengeUI();

        const captchaDiv = elements.pythonCaptchaDiv();
        const codeEditor = elements.codeEditor();

        if (captchaDiv) captchaDiv.style.display = 'block';
        if (codeEditor) codeEditor.focus();

        showStatus('Challenge loaded! Complete the Python challenge to proceed', 'info');

    } catch (error) {
        showStatus('Failed to load challenge. Please try again.', 'error');
        console.error('Challenge loading error:', error);
    }
};

// Python Code Execution
const runPythonCode = async () => {
    console.log('Starting runPythonCode...');
    setRunCodeLoading(true);
    const outputArea = elements.outputArea();
    if (outputArea) outputArea.textContent = 'Initializing Python runtime...';

    try {
        console.log('Inside try block...');
        // Load Pyodide only once
        if (!appState.pyodide) {
            console.log('Loading Pyodide...');
            if (outputArea) outputArea.textContent = 'Loading Python interpreter... This may take a moment.';
            appState.pyodide = await loadPyodide();
            console.log('Pyodide loaded successfully');
        }

        if (!appState.currentChallenge) {
            throw new Error('No challenge loaded. Please refresh and try again.');
        }

        console.log('Preparing to execute code...');
        if (outputArea) outputArea.textContent = 'Python ready. Executing code...';

        const codeEditor = elements.codeEditor();
        const userCode = codeEditor ? codeEditor.value.trim() : '';

        if (!userCode) {
            throw new Error('Please enter some Python code first.');
        }

        console.log('Setting up output capture...');
        // Set up output capture
        appState.pyodide.runPython(`
            import sys
            import io
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
        `);

        console.log('Running user code...');
        // Run the user's code first
        appState.pyodide.runPython(userCode);

        console.log('Running test code...');
        // Then test the function with the challenge tasks
        const testCode = `
# Testing your function with the provided test cases
results = []
try:
    for task in ${JSON.stringify(appState.currentChallenge.tasks)}:
        result = calc(task)
        results.append(result)
        print(f"calc({task}) = {result}")

    # Store results for submission
    print(f"\\n📊 Results: {results}")
    print(f"\\n📊 Results Length: {len(results)}")
except Exception as e:
    print(f"❌ Error testing function: {e}")
    results = []
`;

        appState.pyodide.runPython(testCode);
        console.log('Test code executed successfully');

        console.log('Converting results...');

        // Get the results array - simplified conversion
        let jsResults = [];
        try {
            // Use JSON serialization for reliable conversion
            const resultsList = appState.pyodide.runPython(`
import json
json.dumps(results)
            `);
            jsResults = JSON.parse(resultsList);
            console.log('Converted results:', jsResults);
        } catch (e) {
            console.error('Failed to convert results:', e);
            // Fallback: try direct access
            try {
                const pythonResults = appState.pyodide.runPython("results");
                if (pythonResults && typeof pythonResults.toJs === 'function') {
                    jsResults = pythonResults.toJs();
                } else if (Array.isArray(pythonResults)) {
                    jsResults = pythonResults;
                }
            } catch (e2) {
                console.error('Fallback conversion also failed:', e2);
                jsResults = [];
            }
        }

        appState.lastResults = Array.isArray(jsResults) ? jsResults : [];
        console.log('Final results:', appState.lastResults);

        console.log('Getting output...');
        // Get captured output
        const stdout = appState.pyodide.runPython("sys.stdout.getvalue()");
        const stderr = appState.pyodide.runPython("sys.stderr.getvalue()");

        let finalOutput = '';
        if (stdout) finalOutput += stdout;
        if (stderr) finalOutput += `\n🚨 ERRORS:\n${stderr}`;

        console.log('Updating UI...');
        if (outputArea) {
            outputArea.textContent = finalOutput || '✅ Code executed successfully (no output)';
        }

        updateSubmitButton();

        console.log('Tasks length:', appState.currentChallenge.tasks.length);
        console.log('Results length:', appState.lastResults.length);
        console.log('Results:', appState.lastResults);

        if (appState.lastResults.length === appState.currentChallenge.tasks.length) {
            showStatus(`Code executed successfully! Results: [${appState.lastResults.join(', ')}]. Click "Submit Challenge" to verify.`, 'success');
        } else {
            showStatus(`Function executed but could not extract all results. Expected ${appState.currentChallenge.tasks.length} results, got ${appState.lastResults.length}. Please check your implementation.`, 'error');
        }

        console.log('runPythonCode completed successfully');

    } catch (error) {
        console.log('Error in runPythonCode:', error);
        let errorMsg = `❌ Error: ${error.message}`;

        if (error.name === "PythonError" && appState.pyodide) {
            errorMsg = appState.pyodide.runPython(`
                import sys
                exc = sys.last_exc
                f"❌ {type(exc).__name__}: {exc!s}"
            `);
        }

        if (outputArea) outputArea.textContent = errorMsg;
        showStatus('Code execution failed. Please check your syntax.', 'error');
        appState.lastResults = [];
        updateSubmitButton();
    } finally {
        console.log('In finally block, clearing loading state...');
        setRunCodeLoading(false);
        console.log('Loading state cleared');
    }
};

// Challenge Submission
const submitCaptcha = async () => {
    if (!appState.currentChallenge || appState.lastResults.length === 0) {
        showStatus('Please run your code first to generate results.', 'error');
        return;
    }

    if (appState.lastResults.length !== appState.currentChallenge.tasks.length) {
        showStatus(`Please provide results for all ${appState.currentChallenge.tasks.length} test cases.`, 'error');
        return;
    }

    setSubmitLoading(true);

    try {
        showStatus('Verifying solution...', 'info');

        const result = await submitChallenge(appState.currentChallenge.id, appState.lastResults);

        if (result.success) {
            appState.captchaCompleted = true;
            updateCaptchaButton();
            showStatus('🎉 Challenge solved correctly! You can now login.', 'success');

            const submitBtn = elements.submitChallengeBtn();
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-check-circle"></i> Challenge Verified';
                submitBtn.disabled = true;
            }
        } else {
            showStatus('Solution incorrect. Please check your implementation and try again.', 'error');
        }
    } catch (error) {
        showStatus('Error verifying solution. Please try again.', 'error');
        console.error('Challenge submission error:', error);
    } finally {
        setSubmitLoading(false);
    }
};

// Code Editor Management
const clearCode = () => {
    const codeEditor = elements.codeEditor();
    const outputArea = elements.outputArea();

    if (codeEditor) codeEditor.value = '';
    if (outputArea) outputArea.textContent = 'Code cleared. Ready for new input...';

    appState.captchaCompleted = false;
    appState.lastResults = [];

    updateCaptchaButton();
    updateSubmitButton();

    if (codeEditor) codeEditor.focus();

    // Update placeholder with current challenge
    if (appState.currentChallenge) {
        updateChallengeUI();
    }
};

// Login Management
const handleLogin = () => {
    const usernameInput = elements.usernameInput();
    const passwordInput = elements.passwordInput();
    const loginBtn = elements.loginBtn();

    const username = usernameInput ? usernameInput.value.trim() : '';
    const password = passwordInput ? passwordInput.value.trim() : '';

    if (!username || !password) {
        showStatus('Please fill in all fields.', 'error');
        return;
    }

    if (!appState.captchaCompleted) {
        showStatus('Please complete the Python challenge first.', 'error');
        loadChallenge();
        return;
    }

    // Simulate login process
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<div class="loading-spinner" style="display: inline-block;"></div> Logging in...';
    }

    setTimeout(() => {
        showStatus('🎉 Login successful! Welcome back.', 'success');
        if (loginBtn) {
            loginBtn.innerHTML = '<i class="fas fa-check"></i> Logged In';
            loginBtn.className = 'btn btn-success';
        }
    }, 1500);
};

// Event Handlers
const onCodeChange = () => {
    appState.captchaCompleted = false;
    appState.lastResults = [];
    updateCaptchaButton();
    updateSubmitButton();
};

// Initialize Application
const initApp = () => {
    const codeEditor = elements.codeEditor();

    if (codeEditor) {
        // Add input validation
        codeEditor.addEventListener('input', onCodeChange);

        // Add keyboard shortcuts
        codeEditor.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                runPythonCode();
            }
        });
    }
};

// Global Functions for HTML onclick handlers
window.showPythonCaptcha = loadChallenge;
window.runPythonCode = runPythonCode;
window.clearCode = clearCode;
window.submitCaptcha = submitCaptcha;
window.handleLogin = handleLogin;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initApp);
