package com.company.entityapi.service;

import com.couchbase.client.java.Collection;
import com.couchbase.client.java.kv.UpsertOptions;
import com.company.entityapi.document.AccountDocument;
import com.company.entityapi.exception.BadDataException;
import com.company.entityapi.model.AccountRecord;
import com.company.entityapi.model.Address;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class AccountServiceTest {

    @Mock
    Collection collection;

    @InjectMocks
    AccountService service;

    @Test
    void upsert_throwsBadData_whenStateMissing() {
        AccountRecord record = new AccountRecord();
        record.setAccountNumber(123L);
        Address addr = new Address();
        addr.setLine1("1 Main St");
        addr.setCity("Springfield");
        addr.setState(""); // blank state should trigger validation
        addr.setCountryCode("US");
        record.setAddress(addr);

        BadDataException ex = assertThrows(BadDataException.class, () -> service.upsert(record));
        assertTrue(ex.getMessage().contains("Missing required state code"));
        verifyNoInteractions(collection);
    }

    @Test
    void upsert_callsCollection_whenStatePresent() {
        AccountRecord record = new AccountRecord();
        record.setAccountNumber(456L);
        Address addr = new Address();
        addr.setLine1("1 Main St");
        addr.setCity("Springfield");
        addr.setState("CA");
        addr.setCountryCode("US");
        record.setAddress(addr);

        AccountRecord result = service.upsert(record);

        verify(collection, times(1)).upsert(eq("456"), any(AccountDocument.class), any(UpsertOptions.class));
        assertNotNull(result);
        assertNotNull(result.getAddress());
        assertEquals("CA", result.getAddress().getState());
    }
}

