from fastapi import FastAPI


app = FastAPI(title="Captcha Service")


@app.get("/get-captcha")
def get_captcha() -> dict[str, str]:
    return {"status": "success"}


