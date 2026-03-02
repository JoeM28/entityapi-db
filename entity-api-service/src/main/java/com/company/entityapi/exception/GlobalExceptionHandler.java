package com.company.entityapi.exception;

import com.company.entityapi.model.ErrorResponse;
import com.company.entityapi.model.ErrorResponseErrorsInner;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.time.OffsetDateTime;
import java.util.List;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(AccountNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleNotFound(
            AccountNotFoundException ex, HttpServletRequest request) {
        ErrorResponse body = buildError(404, "Not Found", ex.getMessage(), request.getRequestURI());
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(body);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(
            MethodArgumentNotValidException ex, HttpServletRequest request) {

        List<ErrorResponseErrorsInner> fieldErrors = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(fe -> {
                    ErrorResponseErrorsInner err = new ErrorResponseErrorsInner();
                    err.setField(fe.getField());
                    err.setMessage(fe.getDefaultMessage());
                    return err;
                })
                .toList();

        ErrorResponse body = buildError(400, "Bad Request",
                "Validation failed for one or more fields", request.getRequestURI());
        body.setErrors(fieldErrors);

        return ResponseEntity.badRequest().body(body);
    }

    private ErrorResponse buildError(int status, String error, String message, String path) {
        ErrorResponse body = new ErrorResponse();
        body.setStatus(status);
        body.setError(error);
        body.setMessage(message);
        body.setTimestamp(OffsetDateTime.now());
        body.setPath(path);
        return body;
    }
}
