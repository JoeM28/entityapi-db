package com.company.entityapi.client;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/**
 * HTTP client for entity-name-api (separate repo / container).
 *
 * Calls POST /name/capitalize to return the legalName in uppercase.
 * If the call fails for any reason the original value is returned so that
 * the main upsert flow is never blocked by the downstream service.
 *
 * Base URL is configured via entity.name-api.url in application.yml.
 * When running in Docker Compose the URL resolves to the entity-name-api container.
 */
@Component
public class NameApiClient {

    private static final Logger log = LoggerFactory.getLogger(NameApiClient.class);

    private final RestClient restClient;

    public NameApiClient(@Value("${entity.name-api.url}") String baseUrl) {
        this.restClient = RestClient.builder()
                .baseUrl(baseUrl)
                .build();
    }

    /**
     * Returns the legalName in uppercase as decided by entity-name-api.
     * Falls back to the original value if the downstream call fails.
     */
    public String capitalize(String legalName) {
        try {
            NameResponse response = restClient.post()
                    .uri("/name/capitalize")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(new NameRequest(legalName))
                    .retrieve()
                    .body(NameResponse.class);

            if (response != null && response.legalName() != null) {
                log.debug("entity-name-api capitalized '{}' -> '{}'", legalName, response.legalName());
                return response.legalName();
            }
        } catch (Exception e) {
            log.warn("entity-name-api call failed for legalName='{}', using original. Error: {}", legalName, e.getMessage());
        }
        return legalName;
    }

    // Internal records — not part of the public API surface
    private record NameRequest(String legalName) {}
    private record NameResponse(String legalName) {}
}
