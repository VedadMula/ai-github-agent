import json
import os
import urllib.request
import time
import urllib.error



def summarize_issue_simple(title: str, body: str) -> str:
    body = (body or "").strip()
    first_lines = "\n".join(body.splitlines()[:5]).strip()

    summary = f"### 🧠 Issue Summary\n- **Title:** {title}\n"
    if first_lines:
        summary += f"- **Key details (first lines):**\n```\n{first_lines}\n```\n"
    else:
        summary += "- **Key details:** (No description provided)\n"

    summary += (
        "\n### ✅ Suggested Next Steps\n"
        "- Confirm expected behavior vs actual behavior\n"
        "- Add reproduction steps (if this is a bug)\n"
        "- Add logs/screenshots (if available)\n"
    )
    return summary


def summarize_issue_llm(title: str, body: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return summarize_issue_simple(title, body)

    base_url = (os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").strip().rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""
Classify and summarize this GitHub issue.

Return JSON in this format:
{{
  "summary_markdown": "...",
  "category": "bug | feature | question"
}}

Issue Title: {title}
Issue Body:
{body}
"""

    payload = {
        "model": model,
        "input": prompt
    }

    req = urllib.request.Request(
        f"{base_url}/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    last_error = None
    for attempt in range(4):  # 4 tries total
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            text = data["output"][0]["content"][0]["text"]
            return text
        except urllib.error.HTTPError as e:
            last_error = e
            # Retry on rate limits and transient server errors
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s
                continue
            # Non-retryable HTTP error
            break
        except Exception as e:
            last_error = e
            time.sleep(2 ** attempt)
            continue

    # If LLM fails, fall back so workflow still comments
    return summarize_issue_simple(title, body)



def main() -> None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not found.")

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    issue = event.get("issue", {})
    title = issue.get("title", "(no title)")
    body = issue.get("body", "")

    # LLM first, fallback to simple if no key
    print(summarize_issue_llm(title, body))


if __name__ == "__main__":
    main()
