import os
import time
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

PROMPTCHAN_API_KEY = os.environ.get("PROMPTCHAN_API_KEY")
BASE_URL = "https://prod.aicloudnetservices.com"

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "").strip()

    if not prompt:
        return render_template("index.html", error="Please enter a prompt.")

    if not PROMPTCHAN_API_KEY:
        return render_template("index.html", error="Missing Promptchan API key in Render.")

    headers = {
        "x-api-key": PROMPTCHAN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "prompt": prompt,
        "video_quality": "Standard",
        "aspect": "Portrait",
        "audioEnabled": False,
        "seed": -1,
        "age_slider": 18
    }

    submit = requests.post(
        f"{BASE_URL}/api/external/video_v2/submit",
        headers=headers,
        json=payload,
        timeout=60
    )

    if submit.status_code != 200:
        return render_template("index.html", error=f"Submit failed: {submit.text}")

    request_id = submit.json().get("request_id")

    if not request_id:
        return render_template("index.html", error="No request ID returned.")

    for _ in range(60):
        status = requests.get(
            f"{BASE_URL}/api/external/video_v2/status/{request_id}",
            headers=headers,
            timeout=30
        )

        if status.status_code != 200:
            return render_template("index.html", error=f"Status failed: {status.text}")

        status_data = status.json()
        if status_data.get("status") == "Completed":
            result = requests.get(
                f"{BASE_URL}/api/external/video_v2/result/{request_id}",
                headers=headers,
                timeout=30
            )

            if result.status_code != 200:
                return render_template("index.html", error=f"Result failed: {result.text}")

            data = result.json()
            video = data.get("video")

            if isinstance(video, list):
                video_url = video[0]
            else:
                video_url = video

            return render_template("index.html", video_url=video_url, prompt=prompt)

        time.sleep(5)

    return render_template("index.html", error="Video is still processing. Try again later.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
