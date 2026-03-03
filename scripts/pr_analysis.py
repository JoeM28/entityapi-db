#!/usr/bin/env python3
"""
PR Analysis Script — Entity API

1. Reads .github/skills/pr-analysis/SKILLS.md as the review criteria
2. Gets the PR diff via git
3. Sends both to GitHub Copilot (via GitHub Models API) using GITHUB_TOKEN
4. Writes the markdown report to OUTPUT_FILE
"""

import json
import os
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT  = Path(__file__).parent.parent
SKILLS_MD  = REPO_ROOT / ".github" / "skills" / "pr-analysis" / "SKILLS.md"
MAX_DIFF   = 15000   # chars — keeps prompt within token limits

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/chat/completions"
COPILOT_MODEL     = "gpt-4o"


# ── Git helpers ───────────────────────────────────────────────────────────────

def run_git(args):
    r = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=REPO_ROOT)
    return r.stdout.strip()

def get_changed_files(base_sha, head_sha):
    out = run_git(["diff", "--name-only", f"{base_sha}...{head_sha}"])
    return [f for f in out.splitlines() if f.strip()]

def get_diff(base_sha, head_sha):
    diff = run_git(["diff", f"{base_sha}...{head_sha}"])
    if len(diff) > MAX_DIFF:
        diff = diff[:MAX_DIFF] + f"\n\n...[diff truncated at {MAX_DIFF} chars]"
    return diff


# ── GitHub Copilot via GitHub Models API ─────────────────────────────────────

def call_copilot(github_token, skills_content, diff, changed_files, pr_branch):
    system = (
        "You are an automated PR reviewer for the Entity API project.\n\n"
        "Your review criteria are fully defined in the SKILLS.md below. "
        "Apply every check described in it to the PR diff the user provides.\n\n"
        "=== SKILLS.md ===\n"
        f"{skills_content}\n"
        "=== END SKILLS.md ===\n\n"
        "Produce a markdown report with:\n"
        "1. A summary table: Branch | Files Changed | ✅ Passed | ⚠️ Warnings | ❌ Failed\n"
        "2. Three sections matching SKILLS.md: **Code Quality**, **OpenAPI Standards**, **Application Logic**\n"
        "3. Each section has a table with columns: Check | Status | Detail\n"
        "   - Use ✅ PASS, ❌ FAIL, ⚠️ WARN, ℹ️ INFO for status\n"
        "4. An **Overall Result** line at the bottom\n\n"
        "Only report issues clearly evident in the diff. Do not invent problems. "
        "If a section has no relevant changes, mark all its checks as ℹ️ INFO — Not modified in this PR."
    )

    user = (
        f"**PR branch:** `{pr_branch}`\n"
        f"**Changed files ({len(changed_files)}):** {', '.join(changed_files) or 'none'}\n\n"
        f"**Diff:**\n```diff\n{diff}\n```"
    )

    payload = {
        "model": COPILOT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user}
        ],
        "max_tokens": 2048,
        "temperature": 0.2
    }

    req = urllib.request.Request(
        GITHUB_MODELS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {github_token}",
            "Content-Type":  "application/json"
        }
    )

    with urllib.request.urlopen(req, timeout=90) as resp:
        result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    github_token = os.environ.get("GITHUB_TOKEN", "")
    base_sha     = os.environ.get("BASE_SHA",          "origin/main")
    head_sha     = os.environ.get("HEAD_SHA",           "HEAD")
    pr_branch    = os.environ.get("GITHUB_HEAD_REF",    "feature branch")
    out_file     = os.environ.get("OUTPUT_FILE",        "pr_report.md")

    lines = []

    if not github_token:
        lines += [
            "## ❌ PR Analysis — Configuration Error",
            "",
            "`GITHUB_TOKEN` is not available. Ensure the workflow has `permissions: pull-requests: write`.",
        ]
    else:
        # Read SKILLS.md — this is the single source of truth for review criteria
        try:
            skills = SKILLS_MD.read_text(encoding="utf-8")
        except Exception as e:
            lines += ["## ❌ PR Analysis Error", "", f"Could not read SKILLS.md: {e}"]
            Path(out_file).write_text("\n".join(lines), encoding="utf-8")
            return

        changed = get_changed_files(base_sha, head_sha)
        diff    = get_diff(base_sha, head_sha)

        if not diff:
            lines += ["## ℹ️ PR Analysis", "", "No changes detected against `main`."]
        else:
            try:
                report = call_copilot(github_token, skills, diff, changed, pr_branch)
                lines.append(report)
            except urllib.error.HTTPError as e:
                body = e.read().decode()
                lines += [
                    "## ❌ PR Analysis — GitHub Copilot API Error",
                    "",
                    f"GitHub Models API returned HTTP {e.code}:",
                    f"```\n{body}\n```",
                    "",
                    "> Ensure the repository has access to GitHub Models "
                    "(Settings → Copilot → Enable GitHub Models)."
                ]
            except Exception as e:
                lines += ["## ❌ PR Analysis — Unexpected Error", "", f"```\n{e}\n```"]

    lines += [
        "",
        "---",
        "_Automated by [PR Analysis Skill](.github/skills/pr-analysis/SKILLS.md) · powered by GitHub Copilot_"
    ]

    Path(out_file).write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {out_file}")


if __name__ == "__main__":
    main()
