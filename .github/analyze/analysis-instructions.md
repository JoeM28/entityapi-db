# Analysis Instructions

Use **all source files** in this repository for analysis. This includes every file across all directories and subdirectories.

## Source Files to Include

### OpenAPI Specification
- `entity-api.yaml` — primary API contract (OpenAPI 3.0.3)
- `entity-api-spec.html` — rendered HTML visualization of the spec
- `datastore-reference-html.html` — datastore reference guide

### Spring Boot Application (`entity-api-service/`)
- `pom.xml` — Maven build descriptor, dependencies, plugin configuration
- `src/main/resources/application.yml` — Spring Boot configuration
- `src/main/java/**/*.java` — all Java source files:
  - Controllers (`controller/`)
  - Services (`service/`)
  - Documents / Couchbase POJOs (`document/`)
  - Configuration (`config/`)
  - Exception handlers (`exception/`)
  - Logging filters (`logging/`)

### GitHub Configuration (`.github/`)
- `workflows/*.yml` — CI/CD pipeline definitions
- `prompts/*.prompt.md` — Copilot prompt files
- `agents/*.md` — custom agent definitions
- `skills/**/*` — skill scripts and outputs
- `copilot-instructions.md` — Copilot workspace instructions

### Documentation & Testing
- `PostManCollection/*.json` — Postman collection files
- `request.http` — HTTP test requests
- `CLAUDE.md` — codebase guidance document

## Analysis Scope

When performing any analysis task against this repository, the agent or tool must:

1. **Read every file listed above** before drawing conclusions — do not rely on partial reads or summaries.
2. **Cross-reference layers** — trace data from the API spec through the controller, service, and document layers to the datastore.
3. **Use the full file list** as the authoritative source of truth; do not assume file contents from filenames alone.
4. **Report findings per file** with file path and line number where applicable.

## Notes

- Generated files under `entity-api-service/target/` are excluded from analysis (they are build artefacts).
- The OpenAPI model classes generated under `target/generated-sources/` are derived from `entity-api.yaml`; analyse the spec directly rather than the generated output.
- All datastore field names use `snake_case`; all API field names use `camelCase` — this mapping is intentional and should not be flagged as an inconsistency.
