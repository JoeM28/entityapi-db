#!/usr/bin/env python3
"""
PR Analysis Script — Entity API
Runs code quality, OpenAPI standards, and application logic checks on PR-changed files.
Outputs a markdown report to stdout, which the workflow posts as a PR comment.
"""

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


# ── Helpers ───────────────────────────────────────────────────────────────────

def run_git(args):
    result = subprocess.run(["git"] + args, capture_output=True, text=True, cwd=REPO_ROOT)
    return result.stdout.strip()


def get_changed_files(base_sha, head_sha):
    out = run_git(["diff", "--name-only", f"{base_sha}...{head_sha}"])
    return [f for f in out.splitlines() if f.strip()]


def read_file(rel_path):
    try:
        return (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


class Check:
    def __init__(self, name, status, detail=""):
        # status: pass | fail | warn | info
        self.name   = name
        self.status = status
        self.detail = detail


ICON = {"pass": "✅", "fail": "❌", "warn": "⚠️", "info": "ℹ️"}


# ── Code Quality ──────────────────────────────────────────────────────────────

def check_code_quality(java_files):
    checks = []

    controller_files = [f for f in java_files if "Controller" in f]
    service_files    = [f for f in java_files if "Service" in f and "Test" not in f]
    document_files   = [f for f in java_files if "Document" in f]

    # @Valid on @RequestBody
    for f in controller_files:
        content = read_file(f)
        if "@RequestBody" in content:
            missing = re.search(r"@RequestBody\s+(?!.*@Valid)\w", content)
            if missing and "@Valid" not in content:
                checks.append(Check(
                    "@Valid on @RequestBody", "fail",
                    f"`{Path(f).name}` — @Valid missing on @RequestBody parameter"
                ))
            else:
                checks.append(Check("@Valid on @RequestBody", "pass", Path(f).name))

    # Couchbase operation timeouts
    for f in service_files:
        content = read_file(f)
        has_ops     = bool(re.search(r"collection\.(get|upsert|exists|remove)\(", content))
        has_options = bool(re.search(r"(GetOptions|UpsertOptions|ExistsOptions|RemoveOptions)", content))
        if has_ops and not has_options:
            checks.append(Check(
                "Couchbase operation timeouts", "warn",
                f"`{Path(f).name}` — KV operations found but no explicit Options/timeout detected"
            ))
        elif has_ops:
            checks.append(Check("Couchbase operation timeouts", "pass", Path(f).name))

    # @JsonProperty snake_case in Document classes
    for f in document_files:
        content = read_file(f)
        props     = re.findall(r'@JsonProperty\("([^"]+)"\)', content)
        camel     = [p for p in props if re.search(r"[A-Z]", p)]
        if camel:
            checks.append(Check(
                "@JsonProperty snake_case", "fail",
                f"`{Path(f).name}` — camelCase values found: {camel}"
            ))
        elif props:
            checks.append(Check("@JsonProperty snake_case", "pass", Path(f).name))

    # Layer separation — controller must not reference Document classes
    for f in controller_files:
        content = read_file(f)
        if re.search(r"import.*Document|AccountDocument", content):
            checks.append(Check(
                "Layer separation", "fail",
                f"`{Path(f).name}` — Controller imports a Document class; use AccountRecord (API model) only"
            ))
        else:
            checks.append(Check("Layer separation", "pass", Path(f).name))

    if not checks:
        checks.append(Check("No controller/service/document files changed", "info", ""))

    return checks


# ── OpenAPI Standards ─────────────────────────────────────────────────────────

def check_openapi(changed_files):
    checks = []
    yaml_files = [f for f in changed_files if "entity-api" in f and f.endswith((".yaml", ".yml"))]

    if not yaml_files:
        checks.append(Check("entity-api.yaml", "info", "Not modified in this PR"))
        return checks

    for f in yaml_files:
        content = read_file(f)

        # operationId on every operation
        ops        = re.findall(r"^\s+(get|post|put|delete|patch):\s*$", content, re.MULTILINE)
        op_ids     = re.findall(r"operationId:", content)
        if ops and len(op_ids) < len(ops):
            checks.append(Check(
                "operationId on all endpoints", "fail",
                f"Found {len(ops)} operation(s) but only {len(op_ids)} operationId(s)"
            ))
        else:
            checks.append(Check("operationId on all endpoints", "pass", f))

        # 400 / 404 responses
        for code, label in [("400", "400 Bad Request"), ("404", "404 Not Found")]:
            if f"'{code}'" in content or f'"{code}"' in content or f"\n          {code}:" in content:
                checks.append(Check(f"{label} response defined", "pass", ""))
            else:
                checks.append(Check(f"{label} response defined", "warn", f"No {label} response documented"))

        # required fields
        if "required:" in content:
            checks.append(Check("required fields specified", "pass", ""))
        else:
            checks.append(Check("required fields specified", "warn", "No required fields found in any schema"))

    return checks


# ── Application Logic ─────────────────────────────────────────────────────────

def check_app_logic(java_files):
    checks = []

    service_files    = [f for f in java_files if "Service" in f and "Test" not in f]
    controller_files = [f for f in java_files if "Controller" in f]

    # Server-set fields must not come from client input
    for f in service_files + controller_files:
        content = read_file(f)
        reads_server_field = re.search(r"\.(getLastUpdateDate|getLastUpdateTimestamp)\(\)", content)
        sets_server_field  = re.search(r"(LocalDate\.now|Instant\.now|OffsetDateTime\.now)", content)
        if reads_server_field and not sets_server_field:
            checks.append(Check(
                "Server-set fields (lastUpdateDate/Timestamp)", "warn",
                f"`{Path(f).name}` — reads server-set fields but does not set them — confirm these are not accepted from client"
            ))
        elif sets_server_field:
            checks.append(Check("Server-set fields (lastUpdateDate/Timestamp)", "pass", Path(f).name))

    # docType set in service (not trusted from client)
    for f in service_files:
        content = read_file(f)
        if "doc_type" in content or "docType" in content:
            checks.append(Check("docType assigned in service", "pass", Path(f).name))
        else:
            checks.append(Check(
                "docType assigned in service", "warn",
                f"`{Path(f).name}` — no doc_type/docType assignment found"
            ))

    # Test coverage for every changed service file
    for f in service_files:
        test_name    = Path(f).stem + "Test.java"
        test_in_pr   = any(test_name in cf for cf in java_files)
        test_on_disk = list((REPO_ROOT / "entity-api-service/src/test").rglob(test_name)) if (REPO_ROOT / "entity-api-service/src/test").exists() else []
        if test_in_pr or test_on_disk:
            checks.append(Check(f"Test coverage", "pass", test_name))
        else:
            checks.append(Check(
                "Test coverage", "warn",
                f"No `{test_name}` found for `{Path(f).name}`"
            ))

    if not checks:
        checks.append(Check("No service/controller logic files changed", "info", ""))

    return checks


# ── Report rendering ──────────────────────────────────────────────────────────

def render_table(checks):
    lines = ["| Check | Status | Detail |", "|-------|--------|--------|"]
    for c in checks:
        icon = ICON.get(c.status, "❓")
        lines.append(f"| {c.name} | {icon} {c.status.upper()} | {c.detail} |")
    return "\n".join(lines)


def overall(all_checks):
    if any(c.status == "fail" for c in all_checks):
        return "❌", "FAILED — issues must be fixed before merging"
    if any(c.status == "warn" for c in all_checks):
        return "⚠️", "WARNINGS — review carefully before merging"
    return "✅", "ALL CHECKS PASSED"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    base_sha   = os.environ.get("BASE_SHA", "origin/main")
    head_sha   = os.environ.get("HEAD_SHA", "HEAD")
    pr_branch  = os.environ.get("GITHUB_HEAD_REF", "feature branch")
    pr_number  = os.environ.get("PR_NUMBER", "")

    changed    = get_changed_files(base_sha, head_sha)
    java_files = [f for f in changed if f.endswith(".java")]

    quality_checks = check_code_quality(java_files)
    openapi_checks = check_openapi(changed)
    logic_checks   = check_app_logic(java_files)

    all_checks     = quality_checks + openapi_checks + logic_checks
    icon, summary  = overall(all_checks)

    fails  = sum(1 for c in all_checks if c.status == "fail")
    warns  = sum(1 for c in all_checks if c.status == "warn")
    passes = sum(1 for c in all_checks if c.status == "pass")

    print(f"## {icon} PR Analysis Report")
    print()
    print(f"| | |")
    print(f"|---|---|")
    print(f"| **Branch** | `{pr_branch}` |")
    print(f"| **Files changed** | {len(changed)} ({len(java_files)} Java) |")
    print(f"| **Result** | {passes} passed · {warns} warnings · {fails} failed |")
    print()
    print("---")
    print()
    print("### 🔍 Code Quality")
    print(render_table(quality_checks))
    print()
    print("### 📋 OpenAPI Standards")
    print(render_table(openapi_checks))
    print()
    print("### ⚙️ Application Logic")
    print(render_table(logic_checks))
    print()
    print("---")
    print(f"**Overall: {icon} {summary}**")
    print()
    print("_Automated by [PR Analysis Skill](.github/skills/pr-analysis/SKILLS.md)_")


if __name__ == "__main__":
    main()
