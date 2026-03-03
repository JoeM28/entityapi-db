package com.company.entityapi.document;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Couchbase document for Account entity.
 *
 * Spring Data annotations (@Document, @Field) are intentionally absent.
 * The Couchbase Java SDK serialises this POJO to/from JSON using Jackson,
 * so standard @JsonProperty handles the snake_case field name mapping.
 *
 * @JsonIgnoreProperties(ignoreUnknown = true) tolerates the "_class" field
 * that Spring Data may have written into previously stored documents.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public class AccountDocument {

    @JsonProperty("doc_type")
    private String docType;

    @JsonProperty("account_number")
    private Long accountNumber;

    @JsonProperty("name")
    private NameDoc name;

    @JsonProperty("address")
    private AddressDoc address;

    @JsonProperty("dob")
    private String dob;

    @JsonProperty("status")
    private String status;

    @JsonProperty("last_update_date")
    private String lastUpdateDate;

    @JsonProperty("last_update_timestamp")
    private String lastUpdateTimestamp;

    public String getDocType() { return docType; }
    public void setDocType(String docType) { this.docType = docType; }

    public Long getAccountNumber() { return accountNumber; }
    public void setAccountNumber(Long accountNumber) { this.accountNumber = accountNumber; }

    public NameDoc getName() { return name; }
    public void setName(NameDoc name) { this.name = name; }

    public AddressDoc getAddress() { return address; }
    public void setAddress(AddressDoc address) { this.address = address; }

    public String getDob() { return dob; }
    public void setDob(String dob) { this.dob = dob; }

    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }

    public String getLastUpdateDate() { return lastUpdateDate; }
    public void setLastUpdateDate(String lastUpdateDate) { this.lastUpdateDate = lastUpdateDate; }

    public String getLastUpdateTimestamp() { return lastUpdateTimestamp; }
    public void setLastUpdateTimestamp(String ts) { this.lastUpdateTimestamp = ts; }

    // ── Nested objects ────────────────────────────────────────────────────

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class NameDoc {

        @JsonProperty("legal_name")
        private String legalName;

        @JsonProperty("dba_name")
        private String dbaName;

        public String getLegalName() { return legalName; }
        public void setLegalName(String legalName) { this.legalName = legalName; }

        public String getDbaName() { return dbaName; }
        public void setDbaName(String dbaName) { this.dbaName = dbaName; }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AddressDoc {

        @JsonProperty("line1")
        private String line1;

        @JsonProperty("city")
        private String city;

        @JsonProperty("state")
        private String state;

        @JsonProperty("country_code")
        private String countryCode;

        public String getLine1() { return line1; }
        public void setLine1(String line1) { this.line1 = line1; }

        public String getCity() { return city; }
        public void setCity(String city) { this.city = city; }

        public String getState() { return state; }
        public void setState(String state) { this.state = state; }

        public String getCountryCode() { return countryCode; }
        public void setCountryCode(String countryCode) { this.countryCode = countryCode; }
    }
}
