---
name: Standards Agent
description: >
  A custom agent that verifies Java coding standards, security standards (OWASP Top 10),
  and OpenAPI specification standards across the Entity API codebase. When invoked, the
  agent runs the full standards review task and writes a markdown report with findings.
mode: agent
tools:
  - codebase
  - githubRepo
  - terminalLastCommand
---

# Standards Agent

## Purpose

This agent performs automated standards verification across the Entity API repository. It is the enforcement layer for the standards defined in `.github/prompts/standards-review.prompt.md`.

When invoked, the agent **must**:
1. Read all source files identified in `.github/analyze/analysis-instructions.md`
2. Execute the full standards review defined in `.github/prompts/standards-review.prompt.md`
3. Write the findings to a timestamped markdown report

---

## Invocation

Trigger this agent by saying:

> "Run the standards agent" — or — "Verify standards" — or — "@standards-agent review"

The agent will begin immediately without further prompting.

---

## Agent Task — Step-by-Step Execution

When this agent is invoked it must execute the following steps in order.

### Step 1 — Load source file inventory

Read `.github/analyze/analysis-instructions.md` to obtain the full list of files to analyse.
Then read every file in the list. Do not skip any file.

### Step 2 — Java Coding Standards check

For every `.java` file under `entity-api-service/src/`:

- Check naming conventions (PascalCase classes, camelCase methods/variables, UPPER_SNAKE_CASE constants)
- Check layer separation (no DTOs persisted, no documents returned from controllers)
- Check injection style (constructor injection preferred over field injection)
- Check exception handling (specific exceptions, no swallowed errors)
- Check for unused imports, dead code, magic literals
- Record each finding with: file path, line number, severity, description, recommendation

### Step 3 — Security Standards check

- Validate all controller `@RequestBody` parameters carry `@Valid`
- Check `application.yml` and `CouchbaseConfig.java` for hardcoded credentials
- Confirm `GlobalExceptionHandler` does not leak stack traces or internal messages
- Check request/response logging does not log PII fields (dob, address) at DEBUG level
- Review `pom.xml` dependency versions for known-vulnerable libraries
- Record each finding with: file, severity, description, recommendation

### Step 4 — OWASP Top 10 check

Assess each OWASP 2021 category against the codebase:

| # | Category |
|---|---|
| A01 | Broken Access Control |
| A02 | Cryptographic Failures |
| A03 | Injection (N1QL / query injection) |
| A04 | Insecure Design |
| A05 | Security Misconfiguration |
| A06 | Vulnerable & Outdated Components |
| A07 | Identification & Authentication Failures |
| A08 | Software & Data Integrity Failures |
| A09 | Security Logging & Monitoring Failures |
| A10 | Server-Side Request Forgery (SSRF) |

Record status (`PASS` / `FAIL` / `NEEDS REVIEW`), finding, and recommendation for each category.

### Step 5 — OpenAPI Spec Standards check

Review `entity-api.yaml` for:

- Completeness: every path, parameter, response code, and schema documented
- Schema quality: `$ref` reuse, `required` arrays, `readOnly` on server-set fields, format/pattern constraints
- Consistency: camelCase naming, consistent pagination parameters, reused `ErrorResponse` schema
- Security: `securitySchemes` present in `components`, `security` applied

Record each finding with: location (path/schema name), severity, description, recommendation.

### Step 6 — Write the report

Create (or overwrite) the report file at:

```
.github/analyze/standards-review-report.md
```

The report must use this exact structure:

```markdown
# Standards Review Report

**Date:** <current ISO 8601 date-time>
**Agent:** Standards Agent (`standards-agent.md`)
**Triggered by:** <invocation method or user>
**Scope:** Full Entity API repository

---

## Executive Summary

<2–5 sentence overall assessment. Call out the most critical issues first.>

---

## 1. Java Coding Standards

### Passed Checks
- <bullet list of checks with no issues>

### Issues Found

| Severity | File | Line | Issue | Recommendation |
|---|---|---|---|---|
| HIGH | `service/AccountService.java` | 42 | Field injection via `@Autowired` | Replace with constructor injection |

---

## 2. Security Standards

### Passed Checks
- <bullet list>

### Issues Found

| Severity | File | Issue | Recommendation |
|---|---|---|---|

---

## 3. OWASP Top 10 (2021)

| # | Category | Status | Finding | Recommendation |
|---|---|---|---|---|
| A01 | Broken Access Control | NEEDS REVIEW | No Spring Security configured | Document intentional open access or add auth |

---

## 4. OpenAPI Spec Standards

### Passed Checks
- <bullet list>

### Issues Found

| Severity | Location | Issue | Recommendation |
|---|---|---|---|

---

## Priority Actions

### Critical
1. <item>

### High
1. <item>

### Medium / Low
1. <item>

---

*Report generated by Standards Agent. Re-run after remediation to verify fixes.*
```

---

## Severity Definitions

| Level | Meaning |
|---|---|
| `CRITICAL` | Security vulnerability or data integrity risk requiring immediate fix |
| `HIGH` | Significant deviation from standards; fix before next release |
| `MEDIUM` | Should be fixed; low immediate risk |
| `LOW` | Minor style or convention issue |
| `INFO` | Observation or improvement suggestion; no action required |

---

## Output Contract

- The agent **must always produce** `.github/analyze/standards-review-report.md`, even if no issues are found (report a clean bill of health)
- The agent **must not** modify any source file — it is read-only
- The agent **must complete all five check steps** before writing the report — partial reports are not acceptable
- If a file cannot be read, the agent must note it in the report under the relevant section and continue
