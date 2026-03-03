package com.company.entityapi.config;

import jakarta.servlet.http.HttpServletRequest;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.filter.CommonsRequestLoggingFilter;

import java.time.OffsetDateTime;
import java.time.ZoneOffset;

@Configuration
public class ApiReqRespLogging {

    private static final Logger log = LoggerFactory.getLogger(ApiReqRespLogging.class);
    private static final String START_TIME_ATTR = "apiStartTime";

    @Bean
    public CommonsRequestLoggingFilter logFilter() {

        CommonsRequestLoggingFilter filter = new CommonsRequestLoggingFilter() {

            @Override
            protected void beforeRequest(HttpServletRequest request, String message) {
                request.setAttribute(START_TIME_ATTR, System.nanoTime());
                log.debug("API START | ts={} | {}", OffsetDateTime.now(ZoneOffset.UTC), message);
            }

            @Override
            protected void afterRequest(HttpServletRequest request, String message) {
                Long startNano = (Long) request.getAttribute(START_TIME_ATTR);
                long durationMicros = (startNano == null) ? 0 : (System.nanoTime() - startNano) / 1_000;
                log.debug("API END   | ts={} | duration={} μs | {}",
                        OffsetDateTime.now(ZoneOffset.UTC), durationMicros, message);
            }
        };

        // ✅ THESE are what make payload/headers show up inside `message`
        filter.setIncludeQueryString(true);
        filter.setIncludePayload(true);
        filter.setMaxPayloadLength(10000);

        filter.setIncludeHeaders(true);      // <-- you said you want headers
        filter.setIncludeClientInfo(true);   // optional but helpful
        filter.setAfterMessagePrefix("");    // optional formatting
        filter.setBeforeMessagePrefix("");   // optional formatting

        return filter;
    }
}