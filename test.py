import httpx, time
with httpx.Client() as client:
    while True:
        client.get("https://demo.relay7f98.us.to/api/auth/get-challenge")
        time.sleep(1)
