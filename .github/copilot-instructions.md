# Entity API — Copilot Error Diagnosis Skill

## How to use this skill
Paste any error — HTTP response, stack trace, Docker log line, or debug message — and I will:
1. Extract the key signal (exception class, error code, message, field name)
2. Map it to the exact source file(s) in `skills/download-sources/`
3. Show the relevant code and recommend the fix

---

## Source file map

All source files are in `skills/download-sources/`. Use this map to find the right file fast.

| Error signal | File to check |
|---|---|
| `No Account found` / HTTP 404 | `AccountNotFoundException.java` → `GlobalExceptionHandler.java` |
| `Validation failed` / HTTP 400 / field-level errors | `GlobalExceptionHandler.java` → `AccountController.java` → `entity-api.yaml` |
| `BadDataException` | `BadDataException.java` → `AccountService.java` |
| `TimeoutException` / `RequestCanceledException` / KV timeout | `AccountService.java` (check timeout values) → `CouchbaseConfig.java` |
| `BucketNotFoundException` / `UnambiguousTimeoutException` on startup | `CouchbaseConfig.java` → `application.yml` |
| `Access denied` / `unable to connect` to Couchbase | `application.yml` (connection-string, username, password) |
| `com.fasterxml.jackson` / deserialization error / `Unrecognized field` | `AccountDocument.java` (check `@JsonProperty` snake_case mappings) |
| `docType` mismatch / enum error | `entity-api.yaml` (enum values) → `AccountDocument.java` |
| `NullPointerException` in service | `AccountService.java` (toDocument/toRecord mapping) |
| HTTP 405 Method Not Allowed | `AccountController.java` (check `@GetMapping`/`@PostMapping`) |
| HTTP 500 with no body | `GlobalExceptionHandler.java` (unhandled exception type) |
| Port 8080 already in use | `application.yml` → Docker container already running |
| `docker compose` build failure | `pom.xml` (dependency issue) → `Dockerfile` |
| `couchbase-setup` exit error | `couchbase/init.sh` |
| Logging not appearing / too verbose | `application.yml` (logging.level settings) |
| Request/response not logged | `ApiReqRespLogging.java` → `ApiRequestResponseLoggingFilter.java` |

---

## Diagnosis steps — follow these every time

### Step 1 — Extract the signal
From the error, identify:
- **Exception class** (e.g., `TimeoutException`, `MethodArgumentNotValidException`)
- **HTTP status code** (400, 404, 405, 500)
- **Field name** if validation error (e.g., `address.state`)
- **Component** where it occurred (controller / service / config / Docker)

### Step 2 — Open the mapped source file
Use the table above to identify the file. Read the full method where the error originates.

### Step 3 — Check against the API contract
Cross-reference `entity-api.yaml` for:
- Required fields (`name.legalName`, `address.line1`, `status`)
- Field formats (`address.state: ^[A-Z]{2}$`, `dob: MM-DD-CCYY`)
- Enum values (`ACTIVE | INACTIVE | SUSPENDED | CLOSED | PENDING | CANCEL`)
- `docType` must be `"Account"` for account endpoints

### Step 4 — Recommend the fix
State:
- The exact file and line/method to change
- What the code currently does vs what it should do
- The corrected code snippet

---

## Project quick reference

```
Stack:        Spring Boot 3.2.5 | Java 17 | Couchbase SDK v3 (raw KV)
API base:     /entity/account
Endpoints:    GET /entity/account/{accountId}   → 200 or 404
              POST /entity/account              → 201 (new) or 200 (update)
Couchbase:    host=couchbase (Docker) or localhost (IntelliJ)
              bucket=customer_bucket
              key=accountNumber as string (e.g. "123456")
Field naming: API → camelCase  |  Couchbase document → snake_case
Server port:  8080
```

## Layer map
```
AccountController     → validates HTTP, delegates to service, returns 201 vs 200
AccountService        → maps AccountRecord ↔ AccountDocument, calls Couchbase KV
AccountDocument       → Couchbase POJO, snake_case @JsonProperty fields
AccountRecord         → generated API DTO from entity-api.yaml (camelCase)
CouchbaseConfig       → opens bucket, exposes Collection bean
GlobalExceptionHandler→ converts exceptions to ErrorResponse JSON
```
