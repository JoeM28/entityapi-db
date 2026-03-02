# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a **documentation-only repository** — no application code, build system, or tests. It contains:

- `entity-api.yaml` — OpenAPI 3.0.3 specification for the Entity API
- `entity-api-spec.html` — Rendered HTML visualization of the OpenAPI spec
- `datastore-reference-html.html` — Comprehensive datastore reference guide (6 datastores)

## API Design

The Entity API manages **Customer Account** entities under the `/entity` base path with two sub-resources:

| Resource | Key Field | DocType |
|---|---|---|
| `/entity/account` | `accountNumber` (int64) | `"Account"` |
| `/entity/customer` | `customerId` (int64) | `"Customer"` |

**Operations** (identical pattern for both resources):
- `GET /entity/{resource}` — retrieve all, paginated (`page`/`size`, 0-based), filterable by `?status=`
- `GET /entity/{resource}/{id}` — retrieve one by ID
- `POST /entity/{resource}` — upsert (insert or update based on key existence)

**Key field constraints:**
- `docType` is required and must match the endpoint (`"Account"` or `"Customer"`)
- `name.legalName`, `address.line1`, and `status` are required on all requests
- `lastUpdateDate` (YYYY-MM-DD) and `lastUpdateTimestamp` (ISO 8601) are server-set (`readOnly`) — never sent by clients
- `status` enum: `ACTIVE | INACTIVE | SUSPENDED | CLOSED | PENDING | CANCEL`
- `dob` format: `MM-DD-CCYY` (e.g. `01-15-1990`)
- `address.state`: 2-char uppercase (`^[A-Z]{2}$`)
- `address.countryCode`: 3-char uppercase (`^[A-Z]{3}$`)
- `name.legalName` and `name.dbaName`: max 20 characters

**Naming convention:** API fields use **camelCase**; all datastore fields use **snake_case**.

## Datastore Implementations

The reference guide documents how the same data model maps to 6 datastores. All stores use `snake_case` field names internally.

### Couchbase
- **Bucket:** `customer_bucket`; schemaless, no mapping file required
- **Document key:** raw `account_number` or `customer_id` (integer as string)
- Use `doc_type` field to distinguish Account from Customer in N1QL queries across the same bucket
- Query pattern: `SELECT * FROM customer_bucket WHERE doc_type = "Account" AND status = "ACTIVE"`

### Elasticsearch
- **Index:** `customer_account` (single index for both Account and Customer)
- Requires an explicit **mapping** defined before inserting data; changing field types later requires reindexing
- `legal_name` and `dba_name` use **multi-fields** — `text` (full-text, standard analyzer) + `.keyword` subfield (exact match/sort)
- `status`, `state`, `country_code`, `dob`, `doc_type` → `keyword` (exact match only)
- `last_update_date` → `date` format `yyyy-MM-dd`; `last_update_timestamp` → `date` format `yyyy-MM-dd'T'HH:mm:ssZ`
- **`full_text_srch`** — virtual `text` field fed via `copy_to` from `name.legal_name`, `name.dba_name`, `address.line1`, `address.city`; enables single-field cross-search, not stored in documents

### Firestore
- **Collections:** `accounts` (key: `account_number`) and `customers` (key: `customer_id`) — separate collections, not a single shared collection
- Nested objects stored as **Maps**; `last_update_timestamp` should use native Firestore `Timestamp` type for range queries

### DynamoDB
- **Table:** `CustomerAccount` — **Single Table Design**
- `pk` = `"ACCOUNT#123456789"` or `"CUSTOMER#987654321"` (prefixed string); `sk` = `"METADATA#<id>"`
- **GSIs:** `status-index` (PK=`status`) for status filtering; `customer_id-index` (PK=`customer_id`) for customer lookups
- `BillingMode: PAY_PER_REQUEST` (recommended for variable/high-volume traffic)
- `AttributeDefinitions` only declares key fields (`pk`, `sk` as String `S`); all other fields are schemaless

### AWS Keyspaces (Cassandra)
- **Keyspace:** `customer_ks`; tables: `customer_ks.account` and `customer_ks.customer`
- Requires strict CQL schema upfront; **does not support nested objects** — `name` and `address` are flattened into individual columns (`legal_name`, `address_line1`, `city`, etc.)
- Secondary index created on `status` column for filtering

### AWS Valkey (ElastiCache)
- Used as a **cache layer**, not a primary store
- Stored as Redis **Hash** with key pattern `ACCOUNT:123456789` or `CUSTOMER:987654321`
- Nested objects flattened using colon notation: `name:legal_name`, `address:line1`, etc.
- All values stored as strings; set TTL via `EXPIRE` for automatic cache eviction

## Spring Boot Service (`entity-api-service/`)

A Maven Spring Boot 3.2 application implementing the two Account endpoints.

**Build & run:**
```bash
cd entity-api-service
mvn compile          # generates model classes then compiles everything
mvn spring-boot:run  # starts on http://localhost:8080
mvn package          # produces target/entity-api-service-1.0.0.jar
java -jar target/entity-api-service-1.0.0.jar
```

**OpenAPI model generation** — the `openapi-generator-maven-plugin` reads `../entity-api.yaml` at compile time and generates `AccountRecord`, `Name`, `Address`, `ErrorResponse`, `ErrorResponseErrorsInner` into `target/generated-sources/openapi/…/model/`. These are API DTOs only — not Couchbase entities.

**Layer separation:**
- `model/` — generated from YAML (camelCase, Jackson + Jakarta Validation annotations)
- `document/AccountDocument` — Couchbase entity (snake_case `@Field` mappings, inner `NameDoc`/`AddressDoc` static classes)
- `repository/AccountRepository` — `CouchbaseRepository<AccountDocument, String>`; all operations are Key-Value (no N1QL/index required)
- `service/AccountService` — maps between `AccountRecord` ↔ `AccountDocument`; sets `lastUpdateDate`/`lastUpdateTimestamp` on every write
- `controller/AccountController` — `POST` checks `existsById` before upserting to return 201 vs 200

**Couchbase connection** (`application.yml`): `localhost`, bucket `customer_bucket`, default scope/collection.

## Error Response Schema

All errors return a consistent `ErrorResponse` body:
```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "Validation failed for one or more fields",
  "timestamp": "2026-03-01T10:30:00Z",
  "path": "/entity/account",
  "errors": [
    { "field": "address.state", "message": "State must be 2 uppercase letters" }
  ]
}
```
HTTP 404 is returned when a record with the given ID does not exist.
