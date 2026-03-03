# Skill: Debug Analysis

**Description:**
Paste any error from the Entity API — HTTP response body, stack trace, Docker log line, or debug message — and this skill identifies the exact source file(s) causing the error and recommends the fix.

---

## Instructions

When the user pastes an error, follow these steps exactly.

### Step 1 — Extract the signal
Identify from the error:
- Exception class name (e.g. `TimeoutException`, `MethodArgumentNotValidException`)
- HTTP status code (400, 404, 405, 500)
- Field name if validation error (e.g. `address.state`)
- Component where it occurred — controller / service / config / Docker / Couchbase

### Step 2 — Map to source file
Use this table to find the exact file in `skills/download-sources/`:

| Error signal | Source file(s) to check |
|---|---|
| `No Account found` / HTTP 404 | `AccountNotFoundException.java` → `GlobalExceptionHandler.java` |
| `Validation failed` / HTTP 400 / field-level errors | `GlobalExceptionHandler.java` → `AccountController.java` → `entity-api.yaml` |
| `BadDataException` | `BadDataException.java` → `AccountService.java` |
| `TimeoutException` / `RequestCanceledException` / KV timeout | `AccountService.java` (timeout values) → `CouchbaseConfig.java` |
| `BucketNotFoundException` / startup timeout | `CouchbaseConfig.java` → `application.yml` |
| Couchbase `Access denied` / connection refused | `application.yml` (connection-string, credentials) |
| Jackson deserialization / `Unrecognized field` | `AccountDocument.java` (`@JsonProperty` snake_case mappings) |
| `docType` mismatch / enum error | `entity-api.yaml` → `AccountDocument.java` |
| `NullPointerException` in service | `AccountService.java` (toDocument / toRecord mapping) |
| HTTP 405 Method Not Allowed | `AccountController.java` (`@GetMapping` / `@PostMapping`) |
| HTTP 500 with no body | `GlobalExceptionHandler.java` (unhandled exception type) |
| Port 8080 already in use | `application.yml` → Docker container still running |
| `docker compose` build failure | `pom.xml` → `Dockerfile` |
| `couchbase-setup` container exit error | `couchbase/init.sh` |
| Logs missing or too verbose | `application.yml` (logging.level settings) |
| Request/response not logged | `ApiReqRespLogging.java` → `ApiRequestResponseLoggingFilter.java` |

### Step 3 — Read the mapped file
Open the file from `skills/download-sources/`. Read the relevant method and identify exactly what is wrong.

### Step 4 — Cross-check the API contract
Check `skills/download-sources/entity-api.yaml` for:
- Required fields: `name.legalName`, `address.line1`, `status`
- `address.state`: must match `^[A-Z]{2}$`
- `address.countryCode`: must match `^[A-Z]{3}$`
- `dob` format: `MM-DD-CCYY` (e.g. `01-15-1990`)
- `status` enum: `ACTIVE | INACTIVE | SUSPENDED | CLOSED | PENDING | CANCEL`
- `docType` must be `"Account"` for account endpoints
- `lastUpdateDate` and `lastUpdateTimestamp` are server-set — never sent by client

### Step 5 — Recommend the fix
Respond with:
1. **File** — exact filename
2. **Method / line** — where the problem is
3. **Root cause** — one sentence explanation
4. **Fix** — corrected code snippet

---

## Project Reference

```
Stack:     Spring Boot 3.2.5 | Java 17 | Couchbase SDK v3 (raw KV, no ORM)
Endpoints: GET  /entity/account/{accountId}  →  200 or 404
           POST /entity/account              →  201 (new) or 200 (update)
Couchbase: bucket=customer_bucket
           key=accountNumber as string (e.g. "123456")
           host=couchbase (Docker) | localhost (IntelliJ)
Naming:    API fields = camelCase | Couchbase document fields = snake_case
Port:      8080
```

### Layer map
| Class | Responsibility |
|---|---|
| `AccountController` | HTTP routing, determines 201 vs 200 |
| `AccountService` | Couchbase KV operations, `AccountRecord` ↔ `AccountDocument` mapping |
| `AccountDocument` | Couchbase POJO, all fields use `@JsonProperty` snake_case |
| `CouchbaseConfig` | Opens bucket, exposes `Collection` bean |
| `GlobalExceptionHandler` | Converts exceptions to `ErrorResponse` JSON |
| `BadDataException` | Thrown for invalid business data |
