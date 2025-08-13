// A version of captcha_handler.py that only offer basic functionality which only load the captcha cookies
window.addEventListener("message", (e) => {
    if (e.origin !== window.document.currentScript.getAttribute("domain")) {
        return;
    }
    const date = new Date();
    date.setTime(date.getTime() + 86400);
    window.document.cookie = `CODECAPTCHA_JWT=${e.data}; expires=${date.toUTCString()}; path=/`;
    window.document.cookie = `CODECAPTCHA_REQUIRE_AUTH=false; Max-Age=0; path=/`;
    const redirect = new URLSearchParams(window.location.search).get(
        "redirect",
    );
    if (redirect !== null) {
        window.location.href = decodeURIComponent(redirect);
    }
});
