package com.company.entityapi.controller;

import com.company.entityapi.model.AccountRecord;
import com.company.entityapi.service.AccountService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/entity")
public class AccountController {

    private final AccountService accountService;

    public AccountController(AccountService accountService) {
        this.accountService = accountService;
    }

    /**
     * GET /entity/account/{accountId}
     * Returns 200 with the account, or 404 if not found.
     */
    @GetMapping("/account/{accountId}")
    public ResponseEntity<AccountRecord> getAccountById(@PathVariable Long accountId) {
        return ResponseEntity.ok(accountService.getById(accountId));
    }

    /**
     * POST /entity/account
     * Upserts an account.
     * Returns 201 (Created) for new records, 200 (OK) for updates.
     */
    @PostMapping("/account")
    public ResponseEntity<AccountRecord> upsertAccount(@Valid @RequestBody AccountRecord accountRecord) {
        boolean alreadyExists = accountService.exists(accountRecord.getAccountNumber());
        AccountRecord saved = accountService.upsert(accountRecord);
        HttpStatus status = alreadyExists ? HttpStatus.OK : HttpStatus.CREATED;
        return ResponseEntity.status(status).body(saved);
    }
}
