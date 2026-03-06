---
name: Entity API Standards Review
description: Reviews Java coding standards, security standards (OWASP), and OpenAPI spec standards across the Entity API codebase, then produces a markdown report with findings.
mode: agent
---

# Standards Review Prompt

You are an expert code reviewer. When invoked, perform a comprehensive review of the Entity API codebase across the following four areas and produce a consolidated markdown report.

## Scope

Review all source files in:
- `entity-api-service/src/` — Java Spring Boot source
- `entity-api.yaml` — OpenAPI 3.0.3 specification
- `entity-api-service/pom.xml` — Maven dependencies
- `entity-api-service/src/main/resources/application.yml` — Spring configuration

---

## Review Area 1 — Java Coding Standards

Check all `.java` files against these standards:

### Naming & Structure
- [ ] Class names are `PascalCase`; method and variable names are `camelCase`; constants are `UPPER_SNAKE_CASE`
- [ ] Package names are all lowercase
- [ ] No abbreviations in public API names (e.g., `getAccountNumber` not `getAcctNum`)
- [ ] Single Responsibility Principle: each class has one clear purpose
- [ ] No unused imports, dead code, or commented-out blocks

### Code Quality
- [ ] Methods are concise (under 30 lines where possible); extract helpers when logic is complex
- [ ] No magic numbers or string literals — use named constants or enums
- [ ] Null safety: no unchecked dereferences; use `Optional` where appropriate
- [ ] Proper use of Java generics and collections (avoid raw types)
- [ ] Exception handling: specific exceptions caught, not `Exception` or `Throwable`
- [ ] Resources closed properly (try-with-resources for Closeable)

### Spring Boot Conventions
- [ ] Constructor injection used (not field injection via `@Autowired`)
- [ ] `@Service`, `@Repository`, `@RestController` annotations applied correctly
- [ ] No business logic in controller layer — only HTTP routing and delegation
- [ ] `application.yml` values bound via `@ConfigurationProperties` not raw `@Value` where grouping applies
- [ ] `@Transactional` not applied where it cannot be honoured (Couchbase KV is not transactional by default)

### Layer Separation
- [ ] API DTOs (`model/`) are never persisted directly to the database
- [ ] Couchbase documents (`document/`) are never returned directly from controllers
- [ ] Mapping between layers is done exclusively in the service layer

---

## Review Area 2 — Security Standards

Check all layers for the following:

### Input Validation
- [ ] All incoming request fields are validated at the API boundary (Jakarta Bean Validation annotations present and enforced)
- [ ] `@Valid` annotation used on all `@RequestBody` parameters in controllers
- [ ] Field length limits enforced (`name.legalName` and `name.dbaName` max 20 chars per spec)
- [ ] Pattern constraints enforced (`address.state: ^[A-Z]{2}$`, `address.countryCode: ^[A-Z]{3}$`)
- [ ] Enum values validated — no free-text `status` values accepted

### Authentication & Authorization
- [ ] No hardcoded credentials in source code (check `application.yml`, `CouchbaseConfig.java`)
- [ ] Credentials externalised via environment variables or a secrets manager
- [ ] API endpoints protected — confirm whether Spring Security is configured or intentionally absent; document the decision

### Data Exposure
- [ ] Server-set fields (`lastUpdateDate`, `lastUpdateTimestamp`) are `readOnly` in spec and never accepted from clients
- [ ] No stack traces or internal exception details leaked in HTTP responses (verify `GlobalExceptionHandler`)
- [ ] Sensitive fields (PII such as `dob`, `address`) are not logged at DEBUG level in request/response logs

### Dependency Security
- [ ] `pom.xml` — check for known-vulnerable dependency versions (Spring Boot, Couchbase SDK, Jackson)
- [ ] No snapshot/unstable dependencies used in production configuration
- [ ] `mvn dependency:tree` output should be reviewed for transitive vulnerabilities

### Transport & Configuration
- [ ] HTTPS enforced for production (flag if only HTTP is configured)
- [ ] CORS policy defined if the API is consumed by a browser client
- [ ] Actuator endpoints secured or disabled if present

---

## Review Area 3 — OWASP Top 10 (2021)

For each OWASP category, assess the codebase:

| # | Category | Check |
|---|---|---|
| A01 | Broken Access Control | Are all endpoints access-controlled? Can one customer access another's data? |
| A02 | Cryptographic Failures | Is sensitive data (PII, credentials) encrypted at rest and in transit? |
| A03 | Injection | Are Couchbase queries (N1QL) parameterised? No string concatenation into queries. |
| A04 | Insecure Design | Is the threat model documented? Are least-privilege principles followed? |
| A05 | Security Misconfiguration | Default credentials changed? Debug mode off in production? Error details hidden? |
| A06 | Vulnerable & Outdated Components | Are all Maven dependencies up to date? Check Spring Boot and Couchbase SDK versions. |
| A07 | Identification & Auth Failures | Is authentication implemented? Are sessions/tokens handled securely? |
| A08 | Software & Data Integrity Failures | Are dependencies verified (checksums/signatures)? CI pipeline tamper-resistant? |
| A09 | Security Logging & Monitoring | Are authentication failures, access denials, and errors logged with context? |
| A10 | Server-Side Request Forgery | Does any endpoint make outbound HTTP calls based on user-supplied URLs? |

---

## Review Area 4 — OpenAPI Spec Standards

Review `entity-api.yaml` against OpenAPI 3.0.3 best practices:

### Completeness
- [ ] Every path has `summary` and `description`
- [ ] All parameters documented with `description`, `required`, and `schema`
- [ ] Every response code documented (200, 201, 400, 404, 500 minimum)
- [ ] Request bodies include `required: true` and `content` with `application/json`
- [ ] `info` block has `title`, `version`, and `description`

### Schema Quality
- [ ] All schemas use `$ref` to avoid duplication
- [ ] Required fields listed under `required:` array on each schema
- [ ] `readOnly: true` on server-set fields (`lastUpdateDate`, `lastUpdateTimestamp`)
- [ ] String fields have `minLength`, `maxLength`, or `pattern` where applicable
- [ ] Enum values listed exhaustively; no open-ended string types for constrained fields
- [ ] `format` specified for typed fields (`int64`, `date`, `date-time`)

### Consistency
- [ ] Naming convention consistent: camelCase for all property names
- [ ] `docType` discriminator used consistently across Account and Customer schemas
- [ ] Pagination parameters (`page`, `size`) consistent across all list endpoints
- [ ] Error response schema (`ErrorResponse`) reused via `$ref` — not inlined per endpoint
- [ ] HTTP status codes semantically correct (201 for create, 200 for update/retrieve, 404 for not found)

### Security
- [ ] `securitySchemes` defined in `components` (even if currently open — document it)
- [ ] `security` applied at global or operation level

---

## Output Instructions

After completing the review, create a markdown report at:

```
.github/analyze/standards-review-report.md
```

The report must follow this structure:

```markdown
# Standards Review Report
**Date:** <ISO 8601 date>
**Reviewer:** GitHub Copilot / Claude Code Agent
**Scope:** Entity API codebase

## Executive Summary
<2–4 sentence overall assessment>

## 1. Java Coding Standards
### Passed
- <list of checks that passed>
### Issues Found
| Severity | File | Line | Issue | Recommendation |
|---|---|---|---|---|

## 2. Security Standards
### Passed
- <list>
### Issues Found
| Severity | File | Issue | Recommendation |

## 3. OWASP Top 10
| Category | Status | Finding | Recommendation |
|---|---|---|---|

## 4. OpenAPI Spec Standards
### Passed
- <list>
### Issues Found
| Severity | Location | Issue | Recommendation |

## Priority Actions
1. <Critical items first>
2. ...
```

Severity levels: `CRITICAL` | `HIGH` | `MEDIUM` | `LOW` | `INFO`
