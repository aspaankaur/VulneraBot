import os
from groq import Groq
from prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

def get_ai_review(git_diff: str) -> str:
    """Queries Groq (Llama 3.3 70B) to analyze a git diff with an 8s timeout and fallback."""
    if not git_diff.strip():
        return "✅ No code changes to analyze."

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "⚠️ *AI logic review skipped (GROQ_API_KEY missing). Static security checks applied.*"

    try:
        # Initialize Groq client
        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(git_diff=git_diff)}
            ],
            temperature=0.2,
            max_tokens=500,
            timeout=8.0  # 8-second execution cap to prevent webhook timeouts
        )
        return response.choices[0].message.content.strip()
    
    except Exception:
        # Fallback if API times out, fails, or key is invalid
        return "⚠️ *AI logic review skipped (API timeout or limit reached). Static security checks applied.*"


def combine_reviews(static_issues: list, ai_review_text: str) -> str:
    """
    Combines Person 1's static security list with Person 2's AI feedback
    into a unified Markdown string ready for GitHub PR comments.
    """
    markdown_output = "### 🛡️ SentinelPR Code Review\n\n"
    
    # Section 1: Person 1's Static Results
    markdown_output += "#### 🔒 Security & Static Scan\n"
    if static_issues:
        for issue in static_issues:
            markdown_output += f"- {issue}\n"
    else:
        markdown_output += "- ✅ No hardcoded secrets or static security flaws detected.\n"
    
    markdown_output += "\n---\n\n"
    
    # Section 2: Person 2's AI Results
    markdown_output += "#### 🧠 AI Logic & Quality Review\n"
    markdown_output += f"{ai_review_text}\n"
    
    return markdown_output


if __name__ == "__main__":
    # Local Test Execution Block
    sample_diff = """
    + def process_users(users):
    +     for i in range(len(users)):
    +         for j in range(len(users)):
    +             print(users[i], users[j])
    """
    mock_static_issues = ["🚨 **Security Hazard**: Potential unhandled input found."]
    
    print("\n--- Testing AI Engine Call ---")
    ai_result = get_ai_review(sample_diff)
    print(ai_result)
    
    print("\n--- Testing Combined Output ---")
    final_md = combine_reviews(mock_static_issues, ai_result)
    print(final_md)