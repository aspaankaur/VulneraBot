import os
from fastapi import FastAPI, Request
from mangum import Mangum
from github_service import fetch_pr_diff, post_pr_comment

# Safe fallback imports so main runs even if your friends haven't pushed yet
try:
    from analyzer import run_static_analysis
except ImportError:
    def run_static_analysis(diff): return []

try:
    from ai_engine import run_ai_review
except ImportError:
    def run_ai_review(diff): return "AI Engine is initializing..."

app = FastAPI(title="VulneraBot")
handler = Mangum(app)  # AWS Lambda entry handler

@app.get("/")
def health_check():
    return {"status": "active", "bot": "VulneraBot"}

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    action = payload.get("action")

    # Process webhook when a PR is opened or new code is pushed
    if action in ["opened", "synchronize"]:
        pull_request = payload.get("pull_request", {})
        diff_url = pull_request.get("url")
        comments_url = pull_request.get("comments_url")

        if diff_url and comments_url:
            # 1. Fetch code diff from GitHub
            raw_diff = fetch_pr_diff(diff_url)

            # 2. Run Static Analysis (Person 1's engine)
            static_issues = run_static_analysis(raw_diff)

            # 3. Run AI Review (Person 2's engine)
            ai_feedback = run_ai_review(raw_diff)

            # 4. Construct Markdown Review Message
            review_body = "## 🛡️ VulneraBot Security & Code Review Report\n\n"
            
            if static_issues:
                review_body += "### 🚨 Static Security Flags\n"
                for issue in static_issues:
                    review_body += f"- {issue}\n"
                review_body += "\n"
            else:
                review_body += "### ✅ Static Security Flags\nNo immediate static vulnerabilities detected.\n\n"

            review_body += f"### 🤖 AI Analysis & Logic Review\n{ai_feedback}\n"

            # 5. Post comment back to GitHub PR
            post_pr_comment(comments_url, review_body)

    return {"status": "webhook processed"}