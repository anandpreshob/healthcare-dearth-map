-- US Healthcare Dearth Map - Database Schema
-- PostgreSQL 16 + PostGIS 3.4

CREATE EXTENSION IF NOT EXISTS postgis;

-- Specialty categories (lookup table)
CREATE TABLE specialties (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    taxonomy_codes TEXT[]
);

-- Geographic units: Counties
CREATE TABLE counties (
    fips VARCHAR(5) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    state_fips VARCHAR(2) NOT NULL,
    state_abbr VARCHAR(2) NOT NULL,
    state_name VARCHAR(50) NOT NULL,
    population INTEGER,
    land_area_sqmi FLOAT,
    centroid GEOMETRY(Point, 4326),
    boundary GEOMETRY(MultiPolygon, 4326)
);

CREATE INDEX idx_counties_geom ON counties USING GIST(boundary);
CREATE INDEX idx_counties_state ON counties(state_abbr);

-- Geographic units: Zip codes (ZCTAs)
CREATE TABLE zipcodes (
    zcta VARCHAR(5) PRIMARY KEY,
    county_fips VARCHAR(5) REFERENCES counties(fips),
    state_abbr VARCHAR(2) NOT NULL,
    population INTEGER,
    land_area_sqmi FLOAT,
    centroid GEOMETRY(Point, 4326)
);

CREATE INDEX idx_zipcodes_geom ON zipcodes USING GIST(centroid);
CREATE INDEX idx_zipcodes_county ON zipcodes(county_fips);

-- Healthcare providers
CREATE TABLE providers (
    npi VARCHAR(10) PRIMARY KEY,
    entity_type INTEGER,
    name VARCHAR(200),
    address_line1 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    location GEOMETRY(Point, 4326),
    taxonomy_codes TEXT[],
    specialties VARCHAR(50)[],
    enumeration_date DATE,
    last_updated DATE,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_providers_geom ON providers USING GIST(location);
CREATE INDEX idx_providers_state ON providers(state);
CREATE INDEX idx_providers_zip ON providers(zipcode);
CREATE INDEX idx_providers_specialties ON providers USING GIN(specialties);

-- Pre-computed dearth scores
CREATE TABLE dearth_scores (
    id SERIAL PRIMARY KEY,
    geo_type VARCHAR(10) NOT NULL,
    geo_id VARCHAR(10) NOT NULL,
    specialty_code VARCHAR(50) NOT NULL REFERENCES specialties(code),

    -- Component metrics
    provider_count INTEGER,
    provider_density FLOAT,
    nearest_distance_miles FLOAT,
    avg_distance_top3_miles FLOAT,
    drive_time_minutes FLOAT,
    wait_time_days FLOAT,

    -- Nearest provider info (for OSRM routing)
    nearest_provider_npi VARCHAR(10),
    nearest_provider_lon FLOAT,
    nearest_provider_lat FLOAT,
    drive_time_is_estimated BOOLEAN DEFAULT FALSE,

    -- Scores (0-100, higher = worse access)
    density_score FLOAT,
    distance_score FLOAT,
    drivetime_score FLOAT,
    waittime_score FLOAT,

    -- Composite
    dearth_score FLOAT,
    dearth_label VARCHAR(20),

    -- Metadata
    computed_at TIMESTAMP DEFAULT NOW(),
    data_version VARCHAR(20)
);

CREATE UNIQUE INDEX idx_dearth_unique ON dearth_scores(geo_type, geo_id, specialty_code);
CREATE INDEX idx_dearth_specialty ON dearth_scores(specialty_code);
CREATE INDEX idx_dearth_score ON dearth_scores(dearth_score DESC);
CREATE INDEX idx_dearth_geo ON dearth_scores(geo_type, geo_id);

-- Materialized view for fast county-level queries (no geometry — frontend uses us-atlas)
CREATE MATERIALIZED VIEW county_dearth_summary AS
SELECT
    c.fips,
    c.name,
    c.state_abbr,
    c.population,
    s.code AS specialty,
    ds.provider_count,
    ds.provider_density,
    ds.dearth_score,
    ds.dearth_label
FROM counties c
CROSS JOIN specialties s
LEFT JOIN dearth_scores ds
    ON ds.geo_type = 'county'
    AND ds.geo_id = c.fips
    AND ds.specialty_code = s.code;

CREATE INDEX idx_county_summary_spec ON county_dearth_summary(specialty);

-- CMS Care Compare: Medicare participation and new patient acceptance
CREATE TABLE cms_care_compare (
    npi VARCHAR(10) PRIMARY KEY,
    pac_id VARCHAR(10),
    last_name VARCHAR(100),
    first_name VARCHAR(100),
    credential VARCHAR(20),
    medical_school VARCHAR(200),
    graduation_year INTEGER,
    primary_specialty VARCHAR(200),
    organization_legal_name VARCHAR(200),
    org_pac_id VARCHAR(10),
    num_org_members INTEGER,
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    phone_number VARCHAR(20),
    accepts_medicare_assignment BOOLEAN,
    participates_in_ehr BOOLEAN,
    reported_quality_measures BOOLEAN
);

CREATE INDEX idx_cms_care_npi ON cms_care_compare(npi);
CREATE INDEX idx_cms_care_state ON cms_care_compare(state);
CREATE INDEX idx_cms_care_zip ON cms_care_compare(zipcode);

-- CMS Hospital: Timely and effective care measures (ED wait times)
CREATE TABLE cms_hospital_timely_care (
    facility_id VARCHAR(10),
    facility_name VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(2),
    zipcode VARCHAR(10),
    county_name VARCHAR(100),
    measure_id VARCHAR(30),
    measure_name VARCHAR(300),
    score VARCHAR(20),
    sample INTEGER,
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    PRIMARY KEY (facility_id, measure_id)
);

CREATE INDEX idx_hospital_timely_state ON cms_hospital_timely_care(state);
CREATE INDEX idx_hospital_timely_zip ON cms_hospital_timely_care(zipcode);
CREATE INDEX idx_hospital_timely_measure ON cms_hospital_timely_care(measure_id);

-- HRSA Health Center Service Delivery Sites
CREATE TABLE hrsa_health_centers (
    id SERIAL PRIMARY KEY,
    health_center_type VARCHAR(100),
    health_center_name VARCHAR(200),
    site_name VARCHAR(200),
    site_address VARCHAR(200),
    site_city VARCHAR(100),
    site_state VARCHAR(2),
    site_zipcode VARCHAR(10),
    site_phone VARCHAR(20),
    site_web_address VARCHAR(500),
    operating_hours TEXT,
    location GEOMETRY(Point, 4326)
);

CREATE INDEX idx_hrsa_hc_state ON hrsa_health_centers(site_state);
CREATE INDEX idx_hrsa_hc_zip ON hrsa_health_centers(site_zipcode);
CREATE INDEX idx_hrsa_hc_geom ON hrsa_health_centers USING GIST(location);

-- County-level aggregated enrichment metrics
CREATE TABLE county_enrichment (
    fips VARCHAR(5) PRIMARY KEY REFERENCES counties(fips),
    -- CMS Care Compare aggregates
    total_medicare_providers INTEGER DEFAULT 0,
    pct_accepting_medicare FLOAT,
    pct_ehr_participation FLOAT,
    pct_quality_reporting FLOAT,
    -- Hospital wait time aggregates (minutes)
    median_ed_wait_minutes FLOAT,
    avg_ed_wait_minutes FLOAT,
    num_hospitals_reporting INTEGER DEFAULT 0,
    -- HRSA health center aggregates
    health_center_sites INTEGER DEFAULT 0,
    health_center_sites_per_100k FLOAT
);

-- Seed specialties
INSERT INTO specialties (code, name, description, taxonomy_codes) VALUES
    ('primary_care', 'Primary Care', 'Family Medicine, Internal Medicine, General Practice', ARRAY['207Q00000X', '207R00000X', '208D00000X']),
    ('cardiology', 'Cardiology', 'Cardiovascular Disease, Interventional Cardiology', ARRAY['207RC0000X', '207RI0011X']),
    ('neurology', 'Neurology', 'Neurology, Neurological Surgery', ARRAY['2084N0400X', '207T00000X']),
    ('nephrology', 'Nephrology', 'Nephrology', ARRAY['207RN0300X']),
    ('oncology', 'Oncology', 'Medical Oncology, Radiation Oncology', ARRAY['207RX0202X', '2085R0001X']),
    ('psychiatry', 'Psychiatry', 'Psychiatry, Child & Adolescent Psychiatry', ARRAY['2084P0800X', '2084P0804X']),
    ('obgyn', 'OB/GYN', 'Obstetrics & Gynecology', ARRAY['207V00000X']),
    ('orthopedics', 'Orthopedics', 'Orthopaedic Surgery', ARRAY['207X00000X']),
    ('general_surgery', 'General Surgery', 'Surgery', ARRAY['208600000X']),
    ('emergency', 'Emergency Medicine', 'Emergency Medicine', ARRAY['207P00000X']),
    ('radiology', 'Radiology', 'Diagnostic Radiology, Interventional Radiology', ARRAY['2085R0202X', '2085R0205X']),
    ('pathology', 'Pathology', 'Anatomic Pathology, Clinical Pathology', ARRAY['207ZP0101X', '207ZP0102X']),
    ('dermatology', 'Dermatology', 'Dermatology', ARRAY['207N00000X']),
    ('ophthalmology', 'Ophthalmology', 'Ophthalmology', ARRAY['207W00000X']),
    ('pediatrics', 'Pediatrics', 'Pediatrics', ARRAY['208000000X']);
