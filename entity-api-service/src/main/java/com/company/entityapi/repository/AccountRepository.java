package com.company.entityapi.repository;

import com.company.entityapi.document.AccountDocument;
import org.springframework.data.couchbase.repository.CouchbaseRepository;
import org.springframework.stereotype.Repository;

/**
 * Spring Data Couchbase repository for AccountDocument.
 *
 * findById / existsById / save all use the Couchbase Key-Value service
 * (port 11210) — no N1QL index required for these operations.
 */
@Repository
public interface AccountRepository extends CouchbaseRepository<AccountDocument, String> {
}
