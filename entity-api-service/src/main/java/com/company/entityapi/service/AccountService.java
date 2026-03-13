package com.company.entityapi.service;

import com.couchbase.client.core.error.DocumentNotFoundException;
import com.couchbase.client.java.Collection;
import com.couchbase.client.java.kv.ExistsOptions;
import com.couchbase.client.java.kv.GetOptions;
import com.couchbase.client.java.kv.GetResult;
import com.couchbase.client.java.kv.UpsertOptions;
import com.company.entityapi.document.AccountDocument;
import com.company.entityapi.exception.AccountNotFoundException;
import com.company.entityapi.exception.BadDataException;
import com.company.entityapi.model.AccountRecord;
import com.company.entityapi.model.Address;
import com.company.entityapi.model.Name;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * Reads and writes Account documents using the Couchbase Java SDK directly.
 *
 * Every operation is explicit:
 *   collection.get()    → KV GET  (port 11210, not N1QL)
 *   collection.exists() → KV EXISTS
 *   collection.upsert() → KV UPSERT  (insert or replace)
 *
 * Tuning notes per call:
 *   - timeout   : per-operation deadline independent of cluster default
 *   - durability: NONE is correct for single-node Docker dev.
 *                 Change to DurabilityLevel.MAJORITY on a multi-node cluster
 *                 to prevent data loss when a node fails mid-write.
 *
 * Partial-field updates (e.g. status only) should use collection.mutateIn()
 * rather than a full upsert — see the HTML reference doc for an example.
 * Updated comment
 */
@Service
public class AccountService {

    private final Collection collection;

    public AccountService(Collection collection) {
        this.collection = collection;
    }

    // ── Read ──────────────────────────────────────────────────────────────

    public AccountRecord getById(Long accountId) {
        try {
            GetResult result = collection.get(
                    String.valueOf(accountId),
                    GetOptions.getOptions()
                            .timeout(Duration.ofMillis(200))
            );
            return toRecord(result.contentAs(AccountDocument.class));

        } catch (DocumentNotFoundException e) {
            throw new AccountNotFoundException(accountId);
        }
    }

    // ── Write ─────────────────────────────────────────────────────────────

    public boolean exists(Long accountNumber) {
        return collection.exists(
                String.valueOf(accountNumber),
                ExistsOptions.existsOptions()
                        .timeout(Duration.ofMillis(100))
        ).exists();
    }

    public AccountRecord upsert(AccountRecord record) {
        // Reject null record early to avoid NPEs and produce a consistent bad-data error
        if (record == null) {
            throw new BadDataException("Account record must not be null");
        }
        // Validate required address state
        if (record != null && record.getAddress() != null) {
            String state = record.getAddress().getState();
            if (state == null || state.trim().isEmpty()) {
                throw new BadDataException("Missing required state code on address for account: " + record.getAccountNumber());
            }
        }
        AccountDocument doc = toDocument(record);
        String key = String.valueOf(doc.getAccountNumber());

        collection.upsert(
                key,
                doc,
                UpsertOptions.upsertOptions()
                        // durability omitted → SDK default (NONE)
                        // set to DurabilityLevel.MAJORITY for production
                        .timeout(Duration.ofMillis(500))
        );

        return toRecord(doc);
    }

    // ── Mapping: API model → Couchbase document ───────────────────────────

    private AccountDocument toDocument(AccountRecord r) {
        AccountDocument doc = new AccountDocument();
        doc.setDocType("Account");
        doc.setAccountNumber(r.getAccountNumber());
        doc.setDob(r.getDob());

        if (r.getStatus() != null) {
            doc.setStatus(r.getStatus().getValue());
        }

        if (r.getName() != null) {
            AccountDocument.NameDoc nameDoc = new AccountDocument.NameDoc();
            nameDoc.setLegalName(r.getName().getLegalName());
            nameDoc.setDbaName(r.getName().getDbaName());
            doc.setName(nameDoc);
        }

        if (r.getAddress() != null) {
            AccountDocument.AddressDoc addrDoc = new AccountDocument.AddressDoc();
            addrDoc.setLine1(r.getAddress().getLine1());
            addrDoc.setCity(r.getAddress().getCity());
            addrDoc.setState(r.getAddress().getState());
            addrDoc.setCountryCode(r.getAddress().getCountryCode());
            doc.setAddress(addrDoc);
        }

        // Server-set on every write — never accepted from the client
        doc.setLastUpdateDate(LocalDate.now().toString());
        doc.setLastUpdateTimestamp(Instant.now().toString());

        return doc;
    }

    // ── Mapping: Couchbase document → API model ───────────────────────────

    private AccountRecord toRecord(AccountDocument doc) {
        AccountRecord r = new AccountRecord();
        r.setDocType(AccountRecord.DocTypeEnum.ACCOUNT);
        r.setAccountNumber(doc.getAccountNumber());
        r.setDob(doc.getDob());

        if (doc.getStatus() != null) {
            r.setStatus(AccountRecord.StatusEnum.fromValue(doc.getStatus()));
        }

        if (doc.getName() != null) {
            Name name = new Name();
            name.setLegalName(doc.getName().getLegalName());
            name.setDbaName(doc.getName().getDbaName());
            r.setName(name);
        }

        if (doc.getAddress() != null) {
            Address addr = new Address();
            addr.setLine1(doc.getAddress().getLine1());
            addr.setCity(doc.getAddress().getCity());
            addr.setState(doc.getAddress().getState());
            addr.setCountryCode(doc.getAddress().getCountryCode());
            r.setAddress(addr);
        }

        if (doc.getLastUpdateDate() != null) {
            r.setLastUpdateDate(LocalDate.parse(doc.getLastUpdateDate()));
        }
        if (doc.getLastUpdateTimestamp() != null) {
            r.setLastUpdateTimestamp(OffsetDateTime.parse(doc.getLastUpdateTimestamp()));
        }

        return r;
    }
}
