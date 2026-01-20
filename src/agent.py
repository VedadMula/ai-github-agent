import json
import os


def summarize_issue(title: str, body: str) -> str:
    """
    v1 deterministic summarizer.
    Later this will be replaced by a real LLM call.
    """
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


def main() -> None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        raise RuntimeError("GITHUB_EVENT_PATH not found.")

    with open(event_path, "r", encoding='utf-8') as f:
        event = json.load(f)

    issue = event.get("issue", {})
    title = issue.get("title", "(no title)")
    body = issue.get("body", "")

    print(summarize_issue(title, body))


if __name__ == "__main__":
    main()
