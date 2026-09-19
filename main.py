import os
import requests
from fastapi import FastAPI, Request, BackgroundTasks, Header
from mangum import Mangum
from analyzer import run_static_analysis

app = FastAPI(title="DevSecOps Code Reviewer Bot")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

def process_github_payload(payload: dict):
    """Background process for evaluating code diffs."""
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return

    pull_request = payload.get("pull_request", {})
    diff_url = pull_request.get("diff_url")
    
    diff_text = ""
    if diff_url:
        headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
        res = requests.get(diff_url, headers=headers)
        if res.status_code == 200:
            diff_text = res.text

    if not diff_text:
        diff_text = payload.get("mock_diff", "")

    detected_issues = run_static_analysis(diff_text)

    if detected_issues:
        summary = "### 🛡️ Static Code Review Findings\n\n" + "\n".join(detected_issues)
    else:
        summary = "### 🛡️ Static Code Review Findings\n\n✅ Code clean. No immediate security issues or high complexity detected."

    print("\n===== SCAN RESULTS =====")
    print(summary)
    print("=========================\n")
    
    return detected_issues


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook_listener(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = Header(default="pull_request")
):
    """Webhook entry point for incoming GitHub events."""
    payload = await request.json()
    background_tasks.add_task(process_github_payload, payload)
    return {
        "status": "Accepted",
        "message": "Security scan initiated in background"
    }


# Mangum handler wrapper for AWS Lambda execution
handler = Mangum(app)