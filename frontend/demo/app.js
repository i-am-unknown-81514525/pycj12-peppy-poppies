// Modern JavaScript with functional programming approach
// API Configuration
const API_BASE_URL = "[domain]";

// Application State
let appState = {
    captchaCompleted: false,
};

const NOT_LOGIN = '<i class="fas fa-sign-in-alt"></i> Sign In to Account';
const LOGIN_SUCCESS = '<i class="fas fa-check"></i> Logged In';
const LOGGING_IN =
    '<div class="loading-spinner" style="display: inline-block;"></div> Logging in...';
const SIGN_OUT = '<i class="fas fa-sign-in-alt"></i> Sign Out';

// DOM Elements Cache
const elements = {
    pythonCaptchaDiv: () => document.getElementById("python-captcha"),
    loginBtn: () => document.getElementById("loginBtn"),
    signoutBtn: () => document.getElementById("signoutBtn"),
    usernameInput: () => document.getElementById("username"),
    passwordInput: () => document.getElementById("password"),
    captchaIframe: () => document.getElementById("captchaFrame"),
    statusIndicator: () => document.getElementById("statusIndicator"),
};

const showStatus = (message, type = "info") => {
    console.log(`${type}: ${message}`);
    const indicator = elements.statusIndicator();
    if (!indicator) return;

    indicator.textContent = message;
    indicator.className = `status-indicator status-${type}`;
    indicator.style.display = "block";

    // Auto-hide after 3 seconds for non-error messages
    if (type !== "error") {
        setTimeout(() => {
            indicator.style.display = "none";
        }, 3000);
    }
};

// Login Management
const handleLogin = async () => {
    const usernameInput = elements.usernameInput();
    const passwordInput = elements.passwordInput();
    const loginBtn = elements.loginBtn();

    const username = usernameInput ? usernameInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value.trim() : "";

    if (!username || !password) {
        showStatus("Please fill in all fields.", "error");
        return;
    }

    if (!appState.captchaCompleted) {
        showStatus("Please complete the Python challenge first.", "error");
        return;
    }

    // Simulate login process
    if (loginBtn) {
        loginBtn.disabled = true;
        loginBtn.innerHTML = LOGGING_IN;
    }
    const splitted = document.cookie.split(";");
    let result = "";
    for (let i = 0; i < splitted.length; i++) {
        const item = splitted[i].trimStart(" ");
        if (item.startsWith("CODECAPTCHA_JWT=")) {
            result = item.substring("CODECAPTCHA_JWT=".length, item.length);
        }
    }

    resp = await fetch("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
            username: username,
            password: password,
            captcha_jwt: result,
        }),
    });
    document.cookie = "CODECAPTCHA_JWT=false;Max-Age=0; path=/"; // since single use anyway
    if (resp.ok) {
        showStatus("🎉 Login successful! Welcome back.", "success");
        if (loginBtn) {
            loginBtn.innerHTML = LOGIN_SUCCESS;
            loginBtn.className = "btn btn-success";
        }
        await hideIFrame();
        elements.signoutBtn().classList.remove("hidden");
    } else {
        showStatus(
            "Login failed! You need to solve the capture again.",
            "error",
        );
        await captchaReset();
    }
};

const handleSignout = async () => {
    elements.signoutBtn().classList.add("hidden");
    await fetch("/api/auth/logout");
    const loginBtn = elements.loginBtn();
    loginBtn.innerHTML = NOT_LOGIN;
    loginBtn.className = "btn btn-primary";
    await captchaReset();
};

const hideIFrame = async () => {
    const div = elements.pythonCaptchaDiv();
    div.classList.add("hidden");
};

const configIFrame = async () => {
    showStatus("Loading challenge...", "info");
    const resp = await fetch("/api/auth/get-challenge"); // Get a challenge ID from website server
    const json = await resp.json();
    const challenge_id = json.challenge_id;
    const element = elements.captchaIframe();
    const url = element.getAttribute("data-src");
    element.src = url.replace("[challenge_id]", challenge_id);
    const div = elements.pythonCaptchaDiv();
    div.classList.remove("hidden");
};

// Initialize Application
const initApp = async () => {
    resp = await fetch("/api/auth/me");
    if (resp.ok) {
        elements.signoutBtn().classList.remove("hidden");
        const loginBtn = elements.loginBtn();
        loginBtn.innerHTML = LOGIN_SUCCESS;
        loginBtn.className = "btn btn-success";
    } else {
        await configIFrame();
    }
    console.log("Completed init");
};

const captchaReset = async () => {
    elements.loginBtn().innerHTML = NOT_LOGIN;
    loginBtn.className = "btn btn-primary";
    appState.captchaCompleted = false;
    elements.loginBtn().disabled = true;
    await configIFrame();
};

const captchaCompletionListener = (e) => {
    console.log(`Received message from ${e.origin}: ${e.data}`);
    window.handle_message(e);
    if (e.origin !== window.origin) {
        return;
    }
    if (e.data === "captchaCompleted") {
        appState.captchaCompleted = true;
        elements.loginBtn().disabled = false;
    }
};

// Global Functions for HTML onclick handlers
window.handleLogin = handleLogin;
window.handleSignout = handleSignout;

// Initialize when DOM is loaded
document.addEventListener("DOMContentLoaded", initApp);
window.addEventListener("message", captchaCompletionListener);
