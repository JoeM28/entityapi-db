# Skill: PR Analysis

**Description:**
Automatically runs on every pull request to `main`. Checks code quality,
OpenAPI standards, and application logic against Entity API conventions.
Results are posted as a markdown comment on the PR for the reviewer to check
before merging.

---

## Criteria

### 1. Code Quality
| Check | Rule |
|-------|------|
| `@Valid` on `@RequestBody` | Every `@PostMapping` controller method must annotate its `@RequestBody` parameter with `@Valid` to trigger Jakarta Bean Validation |
| Couchbase operation timeouts | All `collection.get()`, `collection.upsert()`, `collection.exists()` calls must use explicit `Options` with a timeout — never rely on cluster defaults |
| `@JsonProperty` snake_case | All `@JsonProperty` values in Document classes must be `snake_case` — never `camelCase` |
| Layer separation | Controllers must not import or reference `Document` classes directly — use the generated API model (`AccountRecord`) only |

### 2. OpenAPI Standards
| Check | Rule |
|-------|------|
| `operationId` present | Every path operation must define an `operationId` |
| `400` response defined | All mutating endpoints must document a `400 Bad Request` response |
| `404` response defined | All endpoints that retrieve by ID must document a `404 Not Found` response |
| `required` fields specified | Schemas must declare required fields explicitly |

### 3. Application Logic
| Check | Rule |
|-------|------|
| `lastUpdateDate` / `lastUpdateTimestamp` server-set | These fields must only be assigned server-side (via `LocalDate.now()` / `Instant.now()`) — never read from client input |
| `docType` set in service | Service layer must set `doc_type` on every document write — never trust client-supplied value |
| Test coverage | Every new or modified `*Service.java` file must have a corresponding `*ServiceTest.java` |

---

## Output

The analysis report is written to:
```
.github/skills/pr-analysis/PR_ANALYSIS_REPORT.md
```
This file is committed to the PR branch automatically so the reviewer can read it
directly in the repository before merging. It is also posted as a PR comment.

## How it works

1. GitHub Actions workflow (`.github/workflows/pr-analysis.yml`) triggers on PR open/update
2. `scripts/pr_analysis.py` reads this `SKILLS.md` as the criteria, diffs the PR against `main`
3. Sends both to GitHub Copilot (GitHub Models API) for analysis
4. Writes the markdown report to `.github/skills/pr-analysis/PR_ANALYSIS_REPORT.md`
5. Commits the report file to the PR branch and posts it as a PR comment
