package com.company.entityapi.service;

import com.company.entityapi.document.AccountDocument;
import com.company.entityapi.exception.AccountNotFoundException;
import com.company.entityapi.model.AccountRecord;
import com.company.entityapi.model.Address;
import com.company.entityapi.model.Name;
import com.company.entityapi.repository.AccountRepository;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.time.LocalDate;
import java.time.OffsetDateTime;

/**
 * Business logic for Account operations.
 *
 * Mapping responsibility:
 *   API model  (camelCase, generated from entity-api.yaml)
 *   ↕
 *   Couchbase document (snake_case, stored in customer_bucket)
 */
@Service
public class AccountService {

    private final AccountRepository repository;

    public AccountService(AccountRepository repository) {
        this.repository = repository;
    }

    // ── Read ──────────────────────────────────────────────────────────────

    public AccountRecord getById(Long accountId) {
        return repository.findById(String.valueOf(accountId))
                .map(this::toRecord)
                .orElseThrow(() -> new AccountNotFoundException(accountId));
    }

    // ── Write ─────────────────────────────────────────────────────────────

    /**
     * Returns true when the account already exists (caller uses this to decide
     * whether to return 200 or 201).
     */
    public boolean exists(Long accountNumber) {
        return repository.existsById(String.valueOf(accountNumber));
    }

    /**
     * Upserts the account and returns the persisted record with server-set
     * timestamps populated.
     */
    public AccountRecord upsert(AccountRecord record) {
        AccountDocument saved = repository.save(toDocument(record));
        return toRecord(saved);
    }

    // ── Mapping helpers ───────────────────────────────────────────────────

    private AccountDocument toDocument(AccountRecord r) {
        AccountDocument doc = new AccountDocument();
        doc.setId(String.valueOf(r.getAccountNumber()));
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

        // Server-set timestamps — always overwritten on every write
        doc.setLastUpdateDate(LocalDate.now().toString());
        doc.setLastUpdateTimestamp(Instant.now().toString());

        return doc;
    }

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
