CREATE SCHEMA IF NOT EXISTS aexia;

CREATE TABLE IF NOT EXISTS aexia.organizations (
    org_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    country VARCHAR(3),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aexia.o_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES aexia.organizations(org_id) ON DELETE CASCADE,
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    score_f SMALLINT CHECK (score_f BETWEEN 0 AND 5),
    score_a SMALLINT CHECK (score_a BETWEEN 0 AND 5),
    score_g SMALLINT CHECK (score_g BETWEEN 0 AND 5),
    score_c SMALLINT CHECK (score_c BETWEEN 0 AND 5),
    score_o SMALLINT CHECK (score_o BETWEEN 0 AND 5),
    score_m SMALLINT CHECK (score_m BETWEEN 0 AND 5),
    notes JSONB
);

CREATE TABLE IF NOT EXISTS aexia.cards (
    card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES aexia.organizations(org_id) ON DELETE CASCADE,
    system_name VARCHAR(255) NOT NULL,
    classification_ai_act VARCHAR(20) CHECK (classification_ai_act IN ('minimal', 'limite', 'haut_risque', 'inacceptable')),
    level_s SMALLINT CHECK (level_s BETWEEN 0 AND 9),
    xai_method VARCHAR(50),
    data JSONB NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS aexia.audits (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES aexia.cards(card_id) ON DELETE CASCADE,
    auditor_id UUID,
    audit_date TIMESTAMPTZ DEFAULT NOW(),
    dcm_e_results JSONB,
    ecs_score NUMERIC(4,3),
    rad_value NUMERIC(6,3),
    status VARCHAR(20) CHECK (status IN ('draft', 'completed', 'certified')),
    certificate_hash VARCHAR(66)
);

CREATE TABLE IF NOT EXISTS aexia.certificates (
    cert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID REFERENCES aexia.cards(card_id) ON DELETE CASCADE,
    audit_id UUID REFERENCES aexia.audits(audit_id) ON DELETE CASCADE,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    blockchain_tx_hash VARCHAR(66),
    issuer_signature TEXT
);

INSERT INTO aexia.organizations (name, sector, country) VALUES
    ('AI BIAIS INITIATIVE', 'Tech', 'FRA'),
    ('Universite de Paris', 'Education', 'FRA')
ON CONFLICT DO NOTHING;