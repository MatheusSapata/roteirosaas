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

-- Running upgrade 0003_add_pixels -> 0006_add_user_created_at

ALTER TABLE users ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;

UPDATE alembic_version SET version_num='0006_add_user_created_at' WHERE alembic_version.version_num = '0003_add_pixels';

-- Running upgrade 0006_add_user_created_at -> 0007_add_user_cpf_whatsapp

ALTER TABLE users ADD COLUMN cpf VARCHAR(14);

ALTER TABLE users ADD COLUMN whatsapp VARCHAR(20);

ALTER TABLE users ADD CONSTRAINT uq_users_cpf UNIQUE (cpf);

UPDATE alembic_version SET version_num='0007_add_user_cpf_whatsapp' WHERE alembic_version.version_num = '0006_add_user_created_at';

-- Running upgrade 0007_add_user_cpf_whatsapp -> 0008_add_user_trial_fields

ALTER TABLE users ADD COLUMN trial_plan VARCHAR(50);

ALTER TABLE users ADD COLUMN trial_original_plan VARCHAR(50);

ALTER TABLE users ADD COLUMN trial_started_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN trial_ends_at TIMESTAMP WITH TIME ZONE;

ALTER TABLE users ADD COLUMN trial_ack_start BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE users ADD COLUMN trial_ack_end BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE users ALTER COLUMN trial_ack_start DROP DEFAULT;

ALTER TABLE users ALTER COLUMN trial_ack_end DROP DEFAULT;

UPDATE alembic_version SET version_num='0008_add_user_trial_fields' WHERE alembic_version.version_num = '0007_add_user_cpf_whatsapp';

-- Running upgrade 0008_add_user_trial_fields -> 0009_add_agency_default_page

ALTER TABLE agencies ADD COLUMN default_page_id INTEGER;

ALTER TABLE agencies ADD CONSTRAINT agencies_default_page_id_fkey FOREIGN KEY(default_page_id) REFERENCES pages (id) ON DELETE SET NULL;

UPDATE alembic_version SET version_num='0009_add_agency_default_page' WHERE alembic_version.version_num = '0008_add_user_trial_fields';

-- Running upgrade 0009_add_agency_default_page -> 0010_add_finance_tables

ALTER TABLE users ADD COLUMN stripe_account_id VARCHAR(120);

ALTER TABLE users ADD COLUMN stripe_onboarding_completed BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE users ADD COLUMN stripe_charges_enabled BOOLEAN DEFAULT false NOT NULL;

ALTER TABLE users ADD COLUMN stripe_payouts_enabled BOOLEAN DEFAULT false NOT NULL;

CREATE INDEX ix_users_stripe_account_id ON users (stripe_account_id);

CREATE TABLE stripe_accounts (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    stripe_account_id VARCHAR(120) NOT NULL, 
    email VARCHAR(255), 
    country VARCHAR(2), 
    default_currency VARCHAR(3), 
    charges_enabled BOOLEAN DEFAULT false NOT NULL, 
    payouts_enabled BOOLEAN DEFAULT false NOT NULL, 
    onboarding_completed BOOLEAN DEFAULT false NOT NULL, 
    details_submitted BOOLEAN DEFAULT false NOT NULL, 
    requirements JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (user_id), 
    UNIQUE (stripe_account_id)
);

CREATE UNIQUE INDEX ix_stripe_accounts_stripe_account_id ON stripe_accounts (stripe_account_id);

CREATE TABLE sales (
    id SERIAL NOT NULL, 
    user_id INTEGER NOT NULL, 
    agency_id INTEGER, 
    page_id INTEGER, 
    page_slug VARCHAR(255), 
    section_id VARCHAR(64), 
    price_item_id VARCHAR(64), 
    product_title VARCHAR(255) NOT NULL, 
    product_description VARCHAR(500), 
    currency VARCHAR(3) DEFAULT 'brl' NOT NULL, 
    amount INTEGER NOT NULL, 
    commission_amount INTEGER NOT NULL, 
    stripe_application_fee_amount INTEGER NOT NULL, 
    net_amount INTEGER, 
    stripe_fee_amount INTEGER, 
    payment_method VARCHAR(50), 
    installments INTEGER DEFAULT '1' NOT NULL, 
    interest_mode VARCHAR(20) DEFAULT 'merchant' NOT NULL, 
    max_installments_no_interest INTEGER, 
    payment_status VARCHAR(50) DEFAULT 'requires_payment_method' NOT NULL, 
    financial_status VARCHAR(50) DEFAULT 'pending' NOT NULL, 
    payout_status VARCHAR(50) DEFAULT 'pending' NOT NULL, 
    passenger_status VARCHAR(50) DEFAULT 'not_started' NOT NULL, 
    passengers_required INTEGER DEFAULT '0' NOT NULL, 
    passenger_form_token VARCHAR(128) NOT NULL, 
    stripe_payment_intent_id VARCHAR(120) NOT NULL, 
    stripe_charge_id VARCHAR(120), 
    stripe_balance_transaction_id VARCHAR(120), 
    stripe_destination_account VARCHAR(120), 
    customer_name VARCHAR(255), 
    customer_email VARCHAR(255), 
    customer_phone VARCHAR(50), 
    metadata_json JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id) ON DELETE SET NULL, 
    FOREIGN KEY(page_id) REFERENCES pages (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (stripe_payment_intent_id), 
    UNIQUE (passenger_form_token)
);

CREATE INDEX ix_sales_user_id ON sales (user_id);

CREATE INDEX ix_sales_agency_id ON sales (agency_id);

CREATE UNIQUE INDEX ix_sales_stripe_payment_intent_id ON sales (stripe_payment_intent_id);

CREATE UNIQUE INDEX ix_sales_passenger_form_token ON sales (passenger_form_token);

CREATE TABLE passengers (
    id SERIAL NOT NULL, 
    sale_id INTEGER NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    cpf VARCHAR(20), 
    birthdate DATE, 
    phone VARCHAR(50), 
    whatsapp VARCHAR(50), 
    boarding_location VARCHAR(255), 
    extras VARCHAR(1000), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(sale_id) REFERENCES sales (id) ON DELETE CASCADE
);

CREATE INDEX ix_passengers_sale_id ON passengers (sale_id);

UPDATE alembic_version SET version_num='0010_add_finance_tables' WHERE alembic_version.version_num = '0009_add_agency_default_page';

-- Running upgrade 0010_add_finance_tables -> 0011_products_and_inventory

CREATE TABLE products (
    id SERIAL NOT NULL, 
    public_id VARCHAR(36) NOT NULL, 
    user_id INTEGER NOT NULL, 
    agency_id INTEGER, 
    name VARCHAR(255) NOT NULL, 
    description VARCHAR(2000), 
    status VARCHAR(20) DEFAULT 'draft' NOT NULL, 
    trip_date DATE, 
    date_is_flexible BOOLEAN DEFAULT false NOT NULL, 
    inventory_strategy VARCHAR(20) DEFAULT 'manual' NOT NULL, 
    total_slots INTEGER DEFAULT '0' NOT NULL, 
    available_slots INTEGER DEFAULT '0' NOT NULL, 
    reserved_slots INTEGER DEFAULT '0' NOT NULL, 
    sold_slots INTEGER DEFAULT '0' NOT NULL, 
    allow_oversell BOOLEAN DEFAULT false NOT NULL, 
    metadata_json JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(agency_id) REFERENCES agencies (id) ON DELETE SET NULL, 
    FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
    UNIQUE (public_id)
);

CREATE UNIQUE INDEX ix_products_public_id ON products (public_id);

CREATE INDEX ix_products_user_id ON products (user_id);

CREATE TABLE product_variations (
    id SERIAL NOT NULL, 
    public_id VARCHAR(36) NOT NULL, 
    product_id INTEGER NOT NULL, 
    name VARCHAR(255) NOT NULL, 
    description VARCHAR(1000), 
    price_cents INTEGER NOT NULL, 
    currency VARCHAR(3) DEFAULT 'BRL' NOT NULL, 
    people_included INTEGER DEFAULT '1' NOT NULL, 
    status VARCHAR(20) DEFAULT 'active' NOT NULL, 
    stock_mode VARCHAR(20) DEFAULT 'shared' NOT NULL, 
    total_slots INTEGER, 
    available_slots INTEGER, 
    reserved_slots INTEGER, 
    sold_slots INTEGER, 
    sort_order INTEGER DEFAULT '0' NOT NULL, 
    metadata_json JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
    UNIQUE (public_id)
);

CREATE INDEX ix_product_variations_product_id ON product_variations (product_id);

CREATE TABLE sale_items (
    id SERIAL NOT NULL, 
    sale_id INTEGER NOT NULL, 
    product_id INTEGER, 
    product_public_id VARCHAR(36), 
    variation_id INTEGER, 
    variation_public_id VARCHAR(36), 
    variation_name VARCHAR(255) NOT NULL, 
    variation_description VARCHAR(500), 
    currency VARCHAR(3) DEFAULT 'BRL' NOT NULL, 
    unit_price INTEGER NOT NULL, 
    quantity INTEGER DEFAULT '1' NOT NULL, 
    total_price INTEGER NOT NULL, 
    people_count INTEGER DEFAULT '1' NOT NULL, 
    stock_mode VARCHAR(20) DEFAULT 'shared' NOT NULL, 
    reserved_from_product INTEGER DEFAULT '0' NOT NULL, 
    reserved_from_variant INTEGER DEFAULT '0' NOT NULL, 
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL, 
    FOREIGN KEY(sale_id) REFERENCES sales (id) ON DELETE CASCADE, 
    FOREIGN KEY(variation_id) REFERENCES product_variations (id) ON DELETE SET NULL
);

CREATE INDEX ix_sale_items_sale_id ON sale_items (sale_id);

CREATE TABLE product_inventory_events (
    id SERIAL NOT NULL, 
    product_id INTEGER NOT NULL, 
    variation_id INTEGER, 
    sale_id INTEGER, 
    sale_item_id INTEGER, 
    action VARCHAR(32) NOT NULL, 
    quantity INTEGER NOT NULL, 
    available_before INTEGER, 
    available_after INTEGER, 
    context JSONB, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
    FOREIGN KEY(sale_id) REFERENCES sales (id) ON DELETE SET NULL, 
    FOREIGN KEY(sale_item_id) REFERENCES sale_items (id) ON DELETE SET NULL, 
    FOREIGN KEY(variation_id) REFERENCES product_variations (id) ON DELETE CASCADE
);

CREATE TABLE sale_payment_links (
    id SERIAL NOT NULL, 
    sale_id INTEGER NOT NULL, 
    token VARCHAR(64) NOT NULL, 
    status VARCHAR(20) DEFAULT 'open' NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE, 
    created_by_user_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by_user_id) REFERENCES users (id) ON DELETE SET NULL, 
    FOREIGN KEY(sale_id) REFERENCES sales (id) ON DELETE CASCADE, 
    UNIQUE (sale_id), 
    UNIQUE (token)
);

ALTER TABLE sales ADD COLUMN product_id INTEGER;

ALTER TABLE sales ADD COLUMN product_public_id VARCHAR(36);

ALTER TABLE sales ADD COLUMN channel VARCHAR(20) DEFAULT 'page' NOT NULL;

CREATE INDEX ix_sales_product_id ON sales (product_id);

CREATE INDEX ix_sales_product_public_id ON sales (product_public_id);

ALTER TABLE sales ADD CONSTRAINT fk_sales_product_id FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE SET NULL;

UPDATE alembic_version SET version_num='0011_products_and_inventory' WHERE alembic_version.version_num = '0010_add_finance_tables';

COMMIT;

