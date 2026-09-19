import os
from fastapi import FastAPI, Request
from mangum import Mangum
from github_service import fetch_pr_diff, post_pr_comment

# Import Person 1's static analyzer
try:
    from analyzer import run_static_analysis
except ImportError:
    def run_static_analysis(diff): return []

# Import Person 2's AI review engine
try:
    from ai_engine import run_ai_review
except ImportError:
    try:
        from ai_engine import review_code as run_ai_review
    except ImportError:
        def run_ai_review(diff): return "AI Engine response unavailable."

app = FastAPI(title="VulneraBot")
handler = Mangum(app)

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "healthy", "bot": "VulneraBot"}

@app.post("/webhook")
async def github_webhook(request: Request):
    payload = await request.json()
    action = payload.get("action")

    # Trigger on PR opened or when new commits are pushed
    if action in ["opened", "synchronize"]:
        pull_request = payload.get("pull_request", {})
        diff_url = pull_request.get("url")
        comments_url = pull_request.get("comments_url")

        if diff_url and comments_url:
            # 1. Fetch code diff from GitHub
            raw_diff = fetch_pr_diff(diff_url)

            # 2. Run Person 1's Static Security Analyzer
            static_issues = run_static_analysis(raw_diff)

            # 3. Run Person 2's AI Review Engine
            ai_feedback = run_ai_review(raw_diff)

            # 4. Construct Markdown Report
            review_body = "## 🛡️ VulneraBot Code Review & Security Report\n\n"
            
            if static_issues:
                review_body += "### 🚨 Static Security Flags\n"
                for issue in static_issues:
                    review_body += f"- {issue}\n"
                review_body += "\n"
            else:
                review_body += "### ✅ Static Security Flags\nNo immediate static vulnerabilities detected.\n\n"

            review_body += f"### 🤖 AI Analysis & Recommendations\n{ai_feedback}\n"

            # 5. Post review comment to GitHub PR
            post_pr_comment(comments_url, review_body)

    return {"status": "webhook processed"}