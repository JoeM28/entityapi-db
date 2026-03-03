package com.company.entityapi.config;

import com.couchbase.client.java.Bucket;
import com.couchbase.client.java.Cluster;
import com.couchbase.client.java.Collection;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

/**
 * Exposes a ready Collection bean so AccountService can inject it directly.
 *
 * The Cluster bean is auto-configured by Spring Boot from application.yml:
 *   spring.couchbase.connection-string / username / password
 */
@Configuration
public class CouchbaseConfig {

    @Bean
    public Collection accountCollection(
            Cluster cluster,
            @Value("${spring.data.couchbase.bucket-name}") String bucketName) {

        Bucket bucket = cluster.bucket(bucketName);
        // Block until the bucket is ready (SDK 3.x async-first default)
        bucket.waitUntilReady(Duration.ofSeconds(10));
        return bucket.defaultCollection();
    }
}
