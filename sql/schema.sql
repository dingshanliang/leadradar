-- Initial schema draft for LeadRadar. SQLModel/Alembic should become source of truth after implementation.

CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    base_url TEXT,
    priority TEXT,
    crawl_mode TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    rate_limit_per_minute INTEGER DEFAULT 20,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS raw_documents (
    id UUID PRIMARY KEY,
    source_id UUID REFERENCES sources(id),
    url TEXT NOT NULL,
    title TEXT,
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT now(),
    raw_html TEXT,
    extracted_text TEXT,
    content_hash TEXT,
    document_type TEXT,
    parse_status TEXT DEFAULT 'pending',
    UNIQUE(url, content_hash)
);

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    normalized_name TEXT,
    organization_type TEXT,
    province TEXT,
    city TEXT,
    county TEXT,
    industry TEXT,
    official_website TEXT,
    public_phone TEXT,
    public_email TEXT,
    credit_code TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY,
    raw_document_id UUID REFERENCES raw_documents(id),
    organization_id UUID REFERENCES organizations(id),
    signal_type TEXT NOT NULL,
    title TEXT,
    summary TEXT,
    budget_amount NUMERIC,
    expected_time TEXT,
    published_at TIMESTAMPTZ,
    matched_keywords JSONB,
    source_url TEXT,
    evidence_text TEXT,
    confidence NUMERIC,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    primary_signal_id UUID REFERENCES signals(id),
    customer_type TEXT,
    recommended_package TEXT,
    budget_bucket TEXT,
    lead_status TEXT DEFAULT 'new',
    owner TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
