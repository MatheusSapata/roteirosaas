BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_full_initial

CREATE TABLE users (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    hashed_password VARCHAR(255) NOT NULL, 
    is_active BOOLEAN DEFAULT true, 
    is_superuser BOOLEAN DEFAULT false, 
    plan VARCHAR(50) DEFAULT 'free' NOT NULL, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_users_id ON users (id);

CREATE TABLE agencies (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    slug VARCHAR(255) NOT NULL, 
    logo_url VARCHAR(500), 
    primary_color VARCHAR(50), 
    secondary_color VARCHAR(50), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE INDEX ix_agencies_id ON agencies (id);

CREATE UNIQUE INDEX ix_agencies_slug ON agencies (slug);

CREATE TABLE page_templates (
    id SERIAL NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description TEXT, 
    slug VARCHAR(255) NOT NULL, 
    is_default BOOLEAN DEFAULT false, 
    config_json JSONB NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX ix_page_templates_id ON page_templates (id);

CREATE UNIQUE INDEX ix_page_templates_slug ON page_templates (slug);

CREATE TABLE agency_users (
    id SERIAL NOT NULL, 
    agency_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    role VARCHAR(50) DEFAULT 'editor' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id) ON DELETE CASCADE, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_agency_user UNIQUE (agency_id, user_id)
);

CREATE INDEX ix_agency_users_id ON agency_users (id);

CREATE TABLE pages (
    id SERIAL NOT NULL, 
    agency_id INTEGER NOT NULL, 
    template_id INTEGER, 
    title VARCHAR(255) NOT NULL, 
    slug VARCHAR(255) NOT NULL, 
    status VARCHAR(50) DEFAULT 'draft' NOT NULL, 
    published_at TIMESTAMP WITH TIME ZONE, 
    cover_image_url VARCHAR(500), 
    seo_title VARCHAR(255), 
    seo_description VARCHAR(500), 
    config_json JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id) ON DELETE CASCADE, 
    FOREIGN KEY(template_id) REFERENCES page_templates (id) ON DELETE SET NULL
);

CREATE INDEX ix_pages_id ON pages (id);

CREATE INDEX ix_pages_slug ON pages (slug);

CREATE TABLE media_assets (
    id SERIAL NOT NULL, 
    agency_id INTEGER NOT NULL, 
    url VARCHAR(500) NOT NULL, 
    type VARCHAR(50) DEFAULT 'image' NOT NULL, 
    original_file_name VARCHAR(255), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id) ON DELETE CASCADE
);

CREATE INDEX ix_media_assets_id ON media_assets (id);

CREATE TABLE page_visit_stats (
    id SERIAL NOT NULL, 
    page_id INTEGER NOT NULL, 
    date DATE NOT NULL, 
    visits INTEGER DEFAULT '0' NOT NULL, 
    clicks_whatsapp INTEGER DEFAULT '0' NOT NULL, 
    clicks_cta INTEGER DEFAULT '0' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(page_id) REFERENCES pages (id) ON DELETE CASCADE
);

CREATE INDEX ix_page_visit_stats_id ON page_visit_stats (id);

CREATE TABLE subscriptions (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    plan VARCHAR(50) DEFAULT 'free' NOT NULL, 
    preapproval_id VARCHAR(120), 
    failed_attempts INTEGER DEFAULT '0' NOT NULL, 
    status VARCHAR(50) DEFAULT 'active' NOT NULL, 
    valid_until TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    CONSTRAINT uq_subscription_user UNIQUE (user_id)
);

CREATE INDEX ix_subscriptions_preapproval_id ON subscriptions (preapproval_id);

ALTER TABLE users ADD COLUMN subscription_id INTEGER;

ALTER TABLE users ADD CONSTRAINT fk_users_subscription_id FOREIGN KEY(subscription_id) REFERENCES subscriptions (id) ON DELETE SET NULL;

INSERT INTO alembic_version (version_num) VALUES ('0001_full_initial') RETURNING alembic_version.version_num;

-- Running upgrade 0001_full_initial -> 0002_add_stripe_fields

ALTER TABLE subscriptions ADD COLUMN provider VARCHAR(50) DEFAULT 'stripe' NOT NULL;

ALTER TABLE subscriptions ADD COLUMN stripe_customer_id VARCHAR(120);

ALTER TABLE subscriptions ADD COLUMN stripe_subscription_id VARCHAR(120);

ALTER TABLE subscriptions ADD COLUMN stripe_price_id VARCHAR(120);

CREATE INDEX ix_subscriptions_stripe_subscription_id ON subscriptions (stripe_subscription_id);

UPDATE alembic_version SET version_num='0002_add_stripe_fields' WHERE alembic_version.version_num = '0001_full_initial';

-- Running upgrade 0002_add_stripe_fields -> 0003_add_pixels

CREATE TABLE pixels (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    type VARCHAR(20) NOT NULL, 
    value VARCHAR(120) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_pixels_id ON pixels (id);

UPDATE alembic_version SET version_num='0003_add_pixels' WHERE alembic_version.version_num = '0002_add_stripe_fields';

-- Running upgrade 0003_add_pixels -> 0004_add_asaas_fields

ALTER TABLE subscriptions ADD COLUMN asaas_customer_id VARCHAR(120);

ALTER TABLE subscriptions ADD COLUMN asaas_subscription_id VARCHAR(120);

ALTER TABLE subscriptions ADD COLUMN asaas_payment_link_id VARCHAR(120);

ALTER TABLE subscriptions ADD COLUMN external_reference VARCHAR(160);

ALTER TABLE subscriptions ADD COLUMN billing_cycle VARCHAR(20) DEFAULT 'monthly' NOT NULL;

CREATE INDEX ix_subscriptions_asaas_subscription_id ON subscriptions (asaas_subscription_id);

UPDATE alembic_version SET version_num='0004_add_asaas_fields' WHERE alembic_version.version_num = '0003_add_pixels';

COMMIT;

