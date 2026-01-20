import json
import os
import urllib.request


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
    """
    Uses OpenAI-compatible API via HTTPS.
    Requires secret: OPENAI_API_KEY
    Optional: OPENAI_BASE_URL (defaults to https://api.openai.com/v1)
    Optional: OPENAI_MODEL (defaults to gpt-4o-mini)
    """
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return summarize_issue_simple(title, body)

    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    prompt = f"""You are an assistant that summarizes GitHub issues for engineers.

Return markdown with these sections:
1) Summary (2-4 bullets)
2) Repro Steps (if present)
3) Likely Category (bug/feature/question)
4) Suggested Next Actions (3-6 bullets)

Issue Title: {title}
Issue Body:
{body}
"""

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You write concise, helpful engineering summaries in markdown."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        resp_json = json.loads(resp.read().decode("utf-8"))

    return resp_json["choices"][0]["message"]["content"]


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
