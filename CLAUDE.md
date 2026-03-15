# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

| Path | Purpose |
|---|---|
| `entity-api.yaml` | OpenAPI 3.0.3 spec — source of truth for all models and endpoints |
| `entity-api-service/` | Spring Boot 3.2 Maven service implementing the Account endpoints |
| `couchbase/init.sh` | One-shot cluster/bucket initialiser used by Docker Compose |
| `tests/integration-tests.postman_collection.json` | Newman integration test collection |
| `PostManCollection/` | Manual Postman collection (baseurl-only variant) |
| `sync-sibling-repos.py` | Clones/pulls cross-repo `com.company` dependencies into `sibling-repo/` |
| `sibling-repo/` | Git-ignored; populated by the sync script above |
| `datastore-reference-html.html` | Reference for all 6 datastore implementations |

## Build & Run

Maven is not globally installed. Use the IntelliJ-bundled Maven or add it to PATH:
```bash
# IntelliJ bundled (Windows/Git Bash)
MVN="sh '/c/Program Files/JetBrains/IntelliJ IDEA Community Edition 2025.2.4/plugins/maven/lib/maven3/bin/mvn'"
export JAVA_HOME="/c/Program Files/Zulu/zulu-25"
```

```bash
cd entity-api-service
mvn compile          # generates OpenAPI models, then compiles
mvn spring-boot:run  # starts on http://localhost:8080
mvn package          # produces target/entity-api-service-1.0.0.jar
java -jar target/entity-api-service-1.0.0.jar
```

**Full stack via Docker (preferred for integration testing):**
```bash
docker compose up -d --build   # starts Couchbase, runs init.sh, then the Spring Boot app
docker compose down -v         # tear down + remove volumes
docker compose logs entity-api # inspect app logs
```

Health check: `GET http://localhost:8080/actuator/health`

## Testing

**Unit tests** (JUnit 5 + Mockito, no Couchbase required):
```bash
cd entity-api-service
mvn test                                      # run all tests
mvn test -Dtest=AccountServiceTest            # run a single test class
mvn test -Dtest=AccountServiceTest#upsert_throwsBadData_whenStateMissing  # single method
```

**Integration tests** (requires Docker stack to be running):
```bash
npm install -g newman
newman run tests/integration-tests.postman_collection.json \
  --env-var "baseUrl=http://localhost:8080" \
  --reporters cli,junit \
  --reporter-junit-export newman-results.xml
```

Integration tests also run automatically on push/PR to `main` via `.github/workflows/integration-test.yml`.

## Architecture

### Request flow
```
HTTP → AccountController → AccountService → Couchbase SDK (Collection bean)
                                ↓                    ↓
                    DobValidator            NameApiClient → entity-name-api
               (entity-dob-validation)      POST /name/capitalize (port 8081)
```

### Key design decisions

**OpenAPI-first model generation** — `openapi-generator-maven-plugin` reads `../entity-api.yaml` at `mvn compile` and generates `AccountRecord`, `Name`, `Address`, `ErrorResponse` into `target/generated-sources/openapi/.../model/`. Never edit these by hand; change the YAML instead.

**Two distinct model layers:**
- `model/` — Generated API DTOs (camelCase, Jackson + Jakarta Validation annotations). Used at the HTTP boundary.
- `document/AccountDocument` — Couchbase POJO (snake_case `@JsonProperty`). Inner static classes `NameDoc`/`AddressDoc` mirror the nested structure.

**Raw Couchbase SDK, not Spring Data** — `CouchbaseConfig` exposes a `Collection` bean; `AccountService` calls `collection.get()`, `collection.exists()`, `collection.upsert()` directly. All access is Key-Value only (no N1QL). The document key is the raw integer as a string (e.g. `"123456789"`).

**Upsert returns 201 vs 200** — `AccountController.upsertAccount()` calls `accountService.exists()` before the upsert to determine the response status. 201 = new record, 200 = existing record updated.

**Server-set fields** — `lastUpdateDate` and `lastUpdateTimestamp` are set in `AccountService.toDocument()` on every write and are never accepted from the client.

### Cross-repo dependencies

**`entity-dob-validation`** (`com.company:entity-dob-validation:1.0.0`) — Maven library providing `DobValidator.isValid(String)`, called in `AccountService.upsert()`. To work on it locally, run `sync-sibling-repos.py` to clone it into `sibling-repo/`, then `mvn install` inside that folder to publish to `~/.m2`.

**`entity-name-api`** — HTTP microservice called during every upsert to capitalise `legalName` (POST `/name/capitalize`). Configured via `entity.name-api.url` in `application.yml` (default `http://localhost:8081`); override with `ENTITY_NAME_API_URL` env var in Docker/CI. Failure is non-blocking — `NameApiClient` falls back to the original value if the downstream call fails. `sync-sibling-repos.py` clones it into `sibling-repo/` via `EXTRA_REPOS`.

### Exception handling
`GlobalExceptionHandler` (`@ControllerAdvice`) maps:
- `AccountNotFoundException` → 404
- `BadDataException` → 400
- Bean validation failures (`MethodArgumentNotValidException`) → 400

All errors use the `ErrorResponse` schema with a nested `errors[]` array for field-level detail.

## API Design

**Base path:** `/entity`; implemented resources: `account` only (`customer` is spec-only).

**Operations:**
- `GET /entity/account/{accountId}` — KV get by ID, 404 if missing
- `POST /entity/account` — upsert; 201 (new) or 200 (existing)

**Field constraints:**
- `docType` must be `"Account"` for account endpoints
- `name.legalName`, `address.line1`, `status` are required
- `status` enum: `ACTIVE | INACTIVE | SUSPENDED | CLOSED | PENDING | CANCEL`
- `dob` format: `MM-DD-YYYY` (4-digit year enforced by `DobValidator`)
- `address.state`: 2-char uppercase; `address.countryCode`: 3-char uppercase
- `name.legalName` / `name.dbaName`: max 20 chars
- `lastUpdateDate` / `lastUpdateTimestamp` are `readOnly` — server-set, never sent by clients

**Naming:** API fields camelCase; Couchbase document fields snake_case.

## Couchbase

- **Bucket:** `customer_bucket`; default scope and collection
- **Connection** (`application.yml`): `localhost`, user `Administrator`, password `password`
- `CouchbaseConfig` blocks on `bucket.waitUntilReady(10s)` at startup
- Couchbase Management UI: `http://localhost:8091` (when running via Docker)

## CI/CD

| Workflow | Trigger | What it does |
|---|---|---|
| `integration-test.yml` | push/PR to `main` | Docker Compose stack → Newman tests → JUnit report posted to PR |
| `deploy-local.yml` | manual | Local deployment helper |
| `pr-analysis.yml` | PR to `main` | GitHub Copilot PR analysis |
