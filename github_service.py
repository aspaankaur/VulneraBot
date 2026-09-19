import os
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def get_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

def fetch_pr_diff(pull_request_url: str) -> str:
    """Fetches the raw code diff file for a pull request."""
    headers = get_headers()
    headers["Accept"] = "application/vnd.github.v3.diff"
    response = requests.get(pull_request_url, headers=headers)
    if response.status_code == 200:
        return response.text
    print(f"Failed to fetch diff: {response.status_code} - {response.text}")
    return ""

def post_pr_comment(comments_url: str, comment_body: str) -> bool:
    """Posts a review comment back on the GitHub Pull Request."""
    if not GITHUB_TOKEN or GITHUB_TOKEN == "your_personal_access_token_here":
        print("Error: GITHUB_TOKEN missing or invalid in .env")
        return False

    headers = get_headers()
    payload = {"body": comment_body}
    response = requests.post(comments_url, json=payload, headers=headers)

    if response.status_code == 201:
        print("Comment posted to GitHub successfully!")
        return True
    else:
        print(f"Failed to post comment: {response.status_code} - {response.text}")
        return False