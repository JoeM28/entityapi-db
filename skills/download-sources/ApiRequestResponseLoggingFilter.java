package com.company.entityapi.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.util.ContentCachingRequestWrapper;
import org.springframework.web.util.ContentCachingResponseWrapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.Collections;
import java.util.Enumeration;
import java.util.stream.Collectors;

@Component
public class ApiRequestResponseLoggingFilter extends OncePerRequestFilter {

    private static final Logger log =
            LoggerFactory.getLogger(ApiRequestResponseLoggingFilter.class);

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain)
            throws ServletException, IOException {

        ContentCachingRequestWrapper wrappedRequest =
                new ContentCachingRequestWrapper(request);

        ContentCachingResponseWrapper wrappedResponse =
                new ContentCachingResponseWrapper(response);

        long startNano = System.nanoTime();
        OffsetDateTime startTime = OffsetDateTime.now(ZoneOffset.UTC);

        log.debug("API START | ts={} | method={} | uri={}",
                startTime,
                request.getMethod(),
                request.getRequestURI());

        try {
            filterChain.doFilter(wrappedRequest, wrappedResponse);
        } finally {

            long durationMicros = (System.nanoTime() - startNano) / 1_000;
            OffsetDateTime endTime = OffsetDateTime.now(ZoneOffset.UTC);

            String requestBody = getContent(wrappedRequest.getContentAsByteArray());
            String responseBody = getContent(wrappedResponse.getContentAsByteArray());

            String requestHeaders = getHeaders(request);
            String responseHeaders = getHeaders(wrappedResponse);

            int status = wrappedResponse.getStatus();

            log.debug("""
                    
================ API CALL COMPLETE ================
START_TS       : {}
END_TS         : {}
DURATION       : {} μs
METHOD         : {}
URI            : {}
STATUS         : {}
---- REQUEST HEADERS ----
{}
---- REQUEST BODY ----
{}
---- RESPONSE HEADERS ----
{}
---- RESPONSE BODY ----
{}
===================================================
                    """,
                    startTime,
                    endTime,
                    durationMicros,
                    request.getMethod(),
                    request.getRequestURI(),
                    status,
                    requestHeaders,
                    truncate(requestBody),
                    responseHeaders,
                    truncate(responseBody)
            );

            wrappedResponse.copyBodyToResponse();
        }
    }

    private String getContent(byte[] buf) {
        if (buf == null || buf.length == 0) return "";
        return new String(buf, StandardCharsets.UTF_8);
    }

    private String getHeaders(HttpServletRequest request) {
        Enumeration<String> headerNames = request.getHeaderNames();
        return headerNames == null ? "" :
                Collections.list(headerNames).stream()
                        .map(name -> name + ": " + request.getHeader(name))
                        .collect(Collectors.joining("\n"));
    }

    private String getHeaders(HttpServletResponse response) {
        return response.getHeaderNames().stream()
                .map(name -> name + ": " + response.getHeader(name))
                .collect(Collectors.joining("\n"));
    }

    private String truncate(String body) {
        if (body == null) return "";
        int max = 5000;
        return body.length() > max ? body.substring(0, max) + "...(truncated)" : body;
    }
}