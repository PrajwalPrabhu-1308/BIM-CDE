-- Common Data Environment (CDE) SaaS Schema
-- Complete schema with Multi-Tenancy, Authentication, and all features
-- Database: cde_saas

CREATE DATABASE IF NOT EXISTS cde_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE cde_saas;

-- ============================================================================
-- SAAS INFRASTRUCTURE - Organizations & Users
-- ============================================================================

-- Organization (Multi-tenant root)
CREATE TABLE organization (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    
    -- Contact
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(255),
    
    -- Address
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Subscription
    subscription_tier ENUM('FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE') DEFAULT 'FREE',
    subscription_status ENUM('TRIAL', 'ACTIVE', 'PAST_DUE', 'CANCELLED', 'SUSPENDED') DEFAULT 'TRIAL',
    trial_ends_at TIMESTAMP NULL,
    subscription_ends_at TIMESTAMP NULL,
    
    -- Limits
    max_users INT DEFAULT 5,
    max_products INT DEFAULT 100,
    max_storage_gb INT DEFAULT 5,
    
    -- Settings
    settings JSON DEFAULT (JSON_OBJECT()),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_slug (slug),
    INDEX idx_subscription_status (subscription_status)
) ENGINE=InnoDB;

-- User accounts
CREATE TABLE user (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    
    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Profile
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    
    -- Authorization
    role ENUM('SUPER_ADMIN', 'ORG_ADMIN', 'MANAGER', 'USER', 'VIEWER') DEFAULT 'USER',
    permissions JSON DEFAULT (JSON_OBJECT()),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP NULL,
    
    -- Security
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP NULL,
    password_changed_at TIMESTAMP NULL,
    
    -- Preferences
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    preferences JSON DEFAULT (JSON_OBJECT()),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    INDEX idx_organization (organization_id),
    INDEX idx_email (email),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

-- User sessions (JWT tokens)
CREATE TABLE user_session (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    
    token VARCHAR(500) NOT NULL UNIQUE,
    refresh_token VARCHAR(500) UNIQUE,
    
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    expires_at TIMESTAMP NOT NULL,
    refresh_expires_at TIMESTAMP NULL,
    revoked_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_token (token),
    INDEX idx_expires (expires_at)
) ENGINE=InnoDB;

-- API keys for programmatic access
CREATE TABLE api_key (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    organization_id BIGINT UNSIGNED NOT NULL,
    
    name VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    prefix VARCHAR(20) NOT NULL,
    
    scopes JSON DEFAULT (JSON_ARRAY()),
    
    last_used_at TIMESTAMP NULL,
    expires_at TIMESTAMP NULL,
    revoked_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    INDEX idx_key_hash (key_hash),
    INDEX idx_organization (organization_id)
) ENGINE=InnoDB;

-- Organization invitations
CREATE TABLE organization_invitation (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    email VARCHAR(255) NOT NULL,
    role ENUM('ORG_ADMIN', 'MANAGER', 'USER', 'VIEWER') DEFAULT 'USER',
    token VARCHAR(255) NOT NULL UNIQUE,
    
    invited_by_id BIGINT UNSIGNED,
    accepted_at TIMESTAMP NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (invited_by_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_token (token),
    INDEX idx_organization (organization_id)
) ENGINE=InnoDB;

-- ============================================================================
-- PLM DOMAIN (Multi-tenant enabled)
-- ============================================================================

-- Product state table
CREATE TABLE product (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    product_code VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    current_revision_id BIGINT UNSIGNED,
    status ENUM('ACTIVE', 'OBSOLETE', 'DEVELOPMENT') DEFAULT 'DEVELOPMENT',
    
    -- Audit
    created_by_id BIGINT UNSIGNED,
    updated_by_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES user(id) ON DELETE SET NULL,
    UNIQUE KEY unique_org_product_code (organization_id, product_code),
    INDEX idx_organization (organization_id),
    INDEX idx_status (status),
    INDEX idx_product_code (product_code)
) ENGINE=InnoDB;

-- Product revision state table
CREATE TABLE product_revision (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    revision_number VARCHAR(50) NOT NULL,
    description TEXT,
    status ENUM('DRAFT', 'RELEASED', 'OBSOLETE') DEFAULT 'DRAFT',
    released_at TIMESTAMP NULL,
    released_by_id BIGINT UNSIGNED,
    
    created_by_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (released_by_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    UNIQUE KEY unique_org_product_revision (organization_id, product_id, revision_number),
    INDEX idx_organization (organization_id),
    INDEX idx_status (status),
    INDEX idx_product_id (product_id)
) ENGINE=InnoDB;

-- Product change event table
CREATE TABLE product_change_event (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED,
    event_type ENUM('CREATED', 'UPDATED', 'STATUS_CHANGED', 'REVISION_CREATED', 'REVISION_RELEASED') NOT NULL,
    event_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_product_event (product_id, created_at),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB;

-- BOM (Bill of Materials) current state table
CREATE TABLE bom_current (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    parent_product_id BIGINT UNSIGNED NOT NULL,
    parent_revision_id BIGINT UNSIGNED NOT NULL,
    child_product_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(15,4) NOT NULL DEFAULT 1.0,
    unit VARCHAR(50) DEFAULT 'EA',
    position_number INT,
    reference_designator VARCHAR(100),
    notes TEXT,
    
    created_by_id BIGINT UNSIGNED,
    updated_by_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_revision_id) REFERENCES product_revision(id) ON DELETE CASCADE,
    FOREIGN KEY (child_product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES user(id) ON DELETE SET NULL,
    UNIQUE KEY unique_bom_item (organization_id, parent_revision_id, child_product_id, position_number),
    INDEX idx_organization (organization_id),
    INDEX idx_parent (parent_revision_id),
    INDEX idx_child (child_product_id)
) ENGINE=InnoDB;

-- BOM change event table
CREATE TABLE bom_change_event (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    parent_revision_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED,
    event_type ENUM('ITEM_ADDED', 'ITEM_UPDATED', 'ITEM_REMOVED') NOT NULL,
    bom_item_id BIGINT UNSIGNED,
    event_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_revision_id) REFERENCES product_revision(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_parent_event (parent_revision_id, created_at),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB;

-- ============================================================================
-- LOGISTICS DOMAIN (Multi-tenant enabled)
-- ============================================================================

-- Inventory balance state table
CREATE TABLE inventory_balance (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    location_code VARCHAR(100) NOT NULL,
    quantity_on_hand DECIMAL(15,4) NOT NULL DEFAULT 0,
    quantity_reserved DECIMAL(15,4) NOT NULL DEFAULT 0,
    quantity_available DECIMAL(15,4) GENERATED ALWAYS AS (quantity_on_hand - quantity_reserved) STORED,
    unit VARCHAR(50) DEFAULT 'EA',
    last_transaction_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    UNIQUE KEY unique_org_product_location (organization_id, product_id, location_code),
    INDEX idx_organization (organization_id),
    INDEX idx_product (product_id),
    INDEX idx_location (location_code),
    INDEX idx_available (quantity_available)
) ENGINE=InnoDB;

-- Inventory transaction event table
CREATE TABLE inventory_transaction (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    location_code VARCHAR(100) NOT NULL,
    transaction_type ENUM('RECEIPT', 'ISSUE', 'ADJUSTMENT', 'TRANSFER_OUT', 'TRANSFER_IN', 'RESERVATION', 'RELEASE_RESERVATION') NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    unit VARCHAR(50) DEFAULT 'EA',
    reference_type VARCHAR(50),
    reference_id BIGINT UNSIGNED,
    notes TEXT,
    balance_after DECIMAL(15,4),
    
    created_by_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_product_location (product_id, location_code, created_at),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_reference (reference_type, reference_id)
) ENGINE=InnoDB;

-- Shipment state table
CREATE TABLE shipment (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    shipment_number VARCHAR(100) NOT NULL,
    status ENUM('DRAFT', 'CONFIRMED', 'PICKED', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED') DEFAULT 'DRAFT',
    from_location VARCHAR(100) NOT NULL,
    to_location VARCHAR(100) NOT NULL,
    destination_address TEXT,
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    planned_ship_date DATE,
    actual_ship_date DATE,
    estimated_delivery_date DATE,
    actual_delivery_date DATE,
    notes TEXT,
    
    created_by_id BIGINT UNSIGNED,
    updated_by_id BIGINT UNSIGNED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE SET NULL,
    FOREIGN KEY (updated_by_id) REFERENCES user(id) ON DELETE SET NULL,
    UNIQUE KEY unique_org_shipment_number (organization_id, shipment_number),
    INDEX idx_organization (organization_id),
    INDEX idx_status (status),
    INDEX idx_shipment_number (shipment_number)
) ENGINE=InnoDB;

-- Shipment line items (state)
CREATE TABLE shipment_line (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    shipment_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity_planned DECIMAL(15,4) NOT NULL,
    quantity_picked DECIMAL(15,4) DEFAULT 0,
    quantity_packed DECIMAL(15,4) DEFAULT 0,
    unit VARCHAR(50) DEFAULT 'EA',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (shipment_id) REFERENCES shipment(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES product(id) ON DELETE CASCADE,
    INDEX idx_organization (organization_id),
    INDEX idx_shipment (shipment_id),
    INDEX idx_product (product_id)
) ENGINE=InnoDB;

-- Shipment event table
CREATE TABLE shipment_event (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    shipment_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED,
    event_type ENUM('CREATED', 'CONFIRMED', 'PICKED', 'PACKED', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'UPDATED') NOT NULL,
    event_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (shipment_id) REFERENCES shipment(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_shipment_event (shipment_id, created_at),
    INDEX idx_event_type (event_type)
) ENGINE=InnoDB;

-- ============================================================================
-- AUDIT & COMPLIANCE
-- ============================================================================

-- Audit log for all actions
CREATE TABLE audit_log (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED,
    
    action ENUM('CREATE', 'READ', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'EXPORT', 'IMPORT') NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id BIGINT UNSIGNED,
    
    changes JSON,
    metadata JSON,
    
    ip_address VARCHAR(50),
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL,
    INDEX idx_organization (organization_id),
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_action (action)
) ENGINE=InnoDB;

-- Notifications
CREATE TABLE notification (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    organization_id BIGINT UNSIGNED NOT NULL,
    
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    data JSON,
    
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_unread (user_id, is_read, created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- WEBHOOKS
-- ============================================================================

CREATE TABLE webhook (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    
    url VARCHAR(500) NOT NULL,
    secret VARCHAR(255) NOT NULL,
    
    events JSON NOT NULL,
    
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP NULL,
    failure_count INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    INDEX idx_organization (organization_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB;

CREATE TABLE webhook_delivery (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    webhook_id BIGINT UNSIGNED NOT NULL,
    
    event_type VARCHAR(100) NOT NULL,
    payload JSON NOT NULL,
    
    status_code INT,
    response TEXT,
    error TEXT,
    
    delivered_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (webhook_id) REFERENCES webhook(id) ON DELETE CASCADE,
    INDEX idx_webhook (webhook_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB;

-- ============================================================================
-- FILE ATTACHMENTS
-- ============================================================================

CREATE TABLE attachment (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    organization_id BIGINT UNSIGNED NOT NULL,
    uploaded_by_id BIGINT UNSIGNED NOT NULL,
    
    entity_type VARCHAR(100) NOT NULL,
    entity_id BIGINT UNSIGNED NOT NULL,
    
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes BIGINT NOT NULL,
    
    storage_path VARCHAR(500) NOT NULL,
    storage_provider VARCHAR(50) DEFAULT 'local',
    
    description TEXT,
    metadata JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (organization_id) REFERENCES organization(id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by_id) REFERENCES user(id) ON DELETE CASCADE,
    INDEX idx_organization (organization_id),
    INDEX idx_entity (entity_type, entity_id),
    INDEX idx_uploaded_by (uploaded_by_id)
) ENGINE=InnoDB;

-- ============================================================================
-- FEATURE FLAGS
-- ============================================================================

CREATE TABLE feature_flag (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    flag_key VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    is_enabled BOOLEAN DEFAULT FALSE,
    rollout_percentage INT DEFAULT 0,
    
    allowed_organizations JSON,
    allowed_users JSON,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_key (flag_key),
    INDEX idx_enabled (is_enabled)
) ENGINE=InnoDB;

-- ============================================================================
-- RATE LIMITING
-- ============================================================================

CREATE TABLE rate_limit_counter (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    
    limit_key VARCHAR(255) NOT NULL,
    count INT DEFAULT 0,
    
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_key_window (limit_key, window_start),
    INDEX idx_key (limit_key),
    INDEX idx_window (window_start, window_end)
) ENGINE=InnoDB;

-- ============================================================================
-- ANALYTICS VIEWS (Organization-scoped)
-- ============================================================================

-- Product inventory summary (organization-scoped)
CREATE OR REPLACE VIEW v_product_inventory_summary AS
SELECT 
    p.organization_id,
    p.id AS product_id,
    p.product_code,
    p.name AS product_name,
    p.status AS product_status,
    COALESCE(SUM(ib.quantity_on_hand), 0) AS total_on_hand,
    COALESCE(SUM(ib.quantity_reserved), 0) AS total_reserved,
    COALESCE(SUM(ib.quantity_available), 0) AS total_available,
    COUNT(DISTINCT ib.location_code) AS location_count
FROM product p
LEFT JOIN inventory_balance ib ON p.id = ib.product_id
GROUP BY p.organization_id, p.id, p.product_code, p.name, p.status;

-- BOM explosion view (organization-scoped)
CREATE OR REPLACE VIEW v_bom_explosion AS
SELECT 
    pr.organization_id,
    pr.id AS revision_id,
    pp.product_code AS parent_code,
    pp.name AS parent_name,
    pr.revision_number,
    cp.product_code AS child_code,
    cp.name AS child_name,
    bc.quantity,
    bc.unit,
    bc.position_number,
    bc.reference_designator
FROM bom_current bc
INNER JOIN product_revision pr ON bc.parent_revision_id = pr.id
INNER JOIN product pp ON bc.parent_product_id = pp.id
INNER JOIN product cp ON bc.child_product_id = cp.id
ORDER BY pr.organization_id, pr.id, bc.position_number;

-- Shipment status overview (organization-scoped)
CREATE OR REPLACE VIEW v_shipment_overview AS
SELECT 
    s.organization_id,
    s.id AS shipment_id,
    s.shipment_number,
    s.status,
    s.from_location,
    s.to_location,
    s.carrier,
    s.tracking_number,
    s.planned_ship_date,
    s.actual_ship_date,
    COUNT(sl.id) AS line_count,
    SUM(sl.quantity_planned) AS total_quantity_planned,
    SUM(sl.quantity_picked) AS total_quantity_picked,
    SUM(sl.quantity_packed) AS total_quantity_packed,
    s.created_at,
    s.updated_at
FROM shipment s
LEFT JOIN shipment_line sl ON s.id = sl.shipment_id
GROUP BY s.organization_id, s.id, s.shipment_number, s.status, s.from_location, s.to_location, 
         s.carrier, s.tracking_number, s.planned_ship_date, s.actual_ship_date,
         s.created_at, s.updated_at;

-- Recent inventory activity (organization-scoped)
CREATE OR REPLACE VIEW v_recent_inventory_activity AS
SELECT 
    it.organization_id,
    it.id,
    it.created_at,
    p.product_code,
    p.name AS product_name,
    it.location_code,
    it.transaction_type,
    it.quantity,
    it.unit,
    it.balance_after,
    it.reference_type,
    it.reference_id,
    it.notes,
    u.first_name,
    u.last_name
FROM inventory_transaction it
INNER JOIN product p ON it.product_id = p.id
LEFT JOIN user u ON it.created_by_id = u.id
ORDER BY it.created_at DESC
LIMIT 1000;

-- Product change history (organization-scoped)
CREATE OR REPLACE VIEW v_product_change_history AS
SELECT 
    pce.organization_id,
    pce.id,
    pce.created_at,
    p.product_code,
    p.name AS product_name,
    pce.event_type,
    pce.event_data,
    u.first_name,
    u.last_name
FROM product_change_event pce
INNER JOIN product p ON pce.product_id = p.id
LEFT JOIN user u ON pce.user_id = u.id
ORDER BY pce.created_at DESC
LIMIT 1000;

-- ============================================================================
-- SEED DATA - Default Organization & Admin User
-- ============================================================================

-- Insert default organization
INSERT INTO organization (slug, name, email, subscription_tier, subscription_status, trial_ends_at) VALUES
('demo-org', 'Demo Organization', 'admin@demo.com', 'PROFESSIONAL', 'TRIAL', DATE_ADD(NOW(), INTERVAL 14 DAY));

-- Insert default admin user (password: Admin123!)
-- Password hash for 'Admin123!' using bcrypt
INSERT INTO user (organization_id, email, password_hash, first_name, last_name, role, is_verified) VALUES
(1, 'admin@demo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU0WfRvKKG.i', 'Admin', 'User', 'ORG_ADMIN', TRUE);

-- Insert sample products for demo org
INSERT INTO product (organization_id, product_code, name, description, status, created_by_id) VALUES
(1, 'WIDGET-001', 'Standard Widget', 'Basic widget component', 'ACTIVE', 1),
(1, 'WIDGET-002', 'Premium Widget', 'Enhanced widget with extra features', 'ACTIVE', 1),
(1, 'SCREW-M4', 'M4 Screw', 'M4 x 20mm screw', 'ACTIVE', 1),
(1, 'WASHER-M4', 'M4 Washer', 'M4 flat washer', 'ACTIVE', 1),
(1, 'PCB-MAIN', 'Main Circuit Board', 'Primary PCB assembly', 'DEVELOPMENT', 1);

-- Insert sample revisions
INSERT INTO product_revision (organization_id, product_id, revision_number, description, status, released_at, created_by_id) VALUES
(1, 1, 'A', 'Initial release', 'RELEASED', NOW(), 1),
(1, 2, 'A', 'Initial release', 'RELEASED', NOW(), 1),
(1, 3, 'A', 'Standard specification', 'RELEASED', NOW(), 1),
(1, 4, 'A', 'Standard specification', 'RELEASED', NOW(), 1),
(1, 5, 'A', 'First prototype', 'DRAFT', NULL, 1);

-- Update current revision references
UPDATE product SET current_revision_id = 1 WHERE id = 1;
UPDATE product SET current_revision_id = 2 WHERE id = 2;
UPDATE product SET current_revision_id = 3 WHERE id = 3;
UPDATE product SET current_revision_id = 4 WHERE id = 4;
UPDATE product SET current_revision_id = 5 WHERE id = 5;

-- Insert BOM data
INSERT INTO bom_current (organization_id, parent_product_id, parent_revision_id, child_product_id, quantity, unit, position_number, created_by_id) VALUES
(1, 1, 1, 3, 4, 'EA', 1, 1),
(1, 1, 1, 4, 4, 'EA', 2, 1),
(1, 2, 2, 3, 6, 'EA', 1, 1),
(1, 2, 2, 4, 6, 'EA', 2, 1),
(1, 5, 5, 1, 1, 'EA', 1, 1);

-- Insert inventory balances
INSERT INTO inventory_balance (organization_id, product_id, location_code, quantity_on_hand, quantity_reserved) VALUES
(1, 1, 'WH-01', 100, 10),
(1, 2, 'WH-01', 50, 5),
(1, 3, 'WH-01', 1000, 50),
(1, 4, 'WH-01', 1000, 50),
(1, 1, 'WH-02', 75, 0),
(1, 2, 'WH-02', 25, 0);

-- Insert sample inventory transactions
INSERT INTO inventory_transaction (organization_id, product_id, location_code, transaction_type, quantity, balance_after, created_by_id) VALUES
(1, 1, 'WH-01', 'RECEIPT', 100, 100, 1),
(1, 2, 'WH-01', 'RECEIPT', 50, 50, 1),
(1, 3, 'WH-01', 'RECEIPT', 1000, 1000, 1),
(1, 4, 'WH-01', 'RECEIPT', 1000, 1000, 1);
