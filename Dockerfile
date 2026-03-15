# ─── Stage 1: Build ───────────────────────────────────────────────────────────
FROM maven:3.9-eclipse-temurin-17-alpine AS build

WORKDIR /workspace

# 1. Copy the OpenAPI spec to the root
# This ensures the maven-plugin can find it via relative paths (../entity-api.yaml)
COPY entity-api.yaml ./

# 2. Build and install entity-dob-validation (private lib, not in Maven Central)
COPY sibling-repo/entity-dob-validation /workspace/entity-dob-validation
WORKDIR /workspace/entity-dob-validation
RUN mvn install -DskipTests -B

# 3. Switch to the service directory for Maven commands
WORKDIR /workspace/entity-api-service

# 4. Copy pom first to cache dependencies independently of code changes
COPY entity-api-service/pom.xml ./
RUN mvn dependency:go-offline -B

# 4. Copy source and build the "Fat JAR"
COPY entity-api-service/src ./src
RUN mvn package -DskipTests -B


# ─── Stage 2: Runtime ─────────────────────────────────────────────────────────
FROM eclipse-temurin:17-jre-alpine

# Security: Run as a non-privileged user
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

WORKDIR /app

# 5. THE WILDCARD TRICK:
# This picks up the JAR regardless of if the version is 1.0.0 or 1.0.1-SNAPSHOT
COPY --from=build /workspace/entity-api-service/target/*.jar app.jar

EXPOSE 8080

# 6. Optimized for Docker memory management
ENTRYPOINT ["java", "-XX:+UseContainerSupport", "-XX:MaxRAMPercentage=75.0", "-jar", "app.jar"]
