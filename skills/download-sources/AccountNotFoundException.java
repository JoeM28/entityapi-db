package com.company.entityapi.exception;

public class AccountNotFoundException extends RuntimeException {

    public AccountNotFoundException(Long accountId) {
        super("No Account found with accountNumber " + accountId);
    }
}
