"""
CDE SaaS - Multi-Tenancy and User Management Models
Python 3.7 Compatible Version
"""

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, DateTime, 
    Enum, JSON, ForeignKey, Index, TIMESTAMP, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

# Import Base from models.py
try:
    from models import Base
except ImportError:
    Base = declarative_base()

# For password hashing - compatible with Python 3.7
try:
    from passlib.hash import bcrypt
except ImportError:
    import bcrypt as bcrypt_lib
    
    class bcrypt:
        @staticmethod
        def hash(password):
            return bcrypt_lib.hashpw(password.encode(), bcrypt_lib.gensalt()).decode()
        
        @staticmethod
        def verify(password, hashed):
            return bcrypt_lib.checkpw(password.encode(), hashed.encode())


# ============================================================================
# Enums
# ============================================================================

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORG_ADMIN = "org_admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"

class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(str, enum.Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"

class AuditAction(str, enum.Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    IMPORT = "import"


# ============================================================================
# Organization Management
# ============================================================================

class Organization(Base):
    __tablename__ = 'organization'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    
    # Contact info
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    subscription_status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIAL)
    trial_ends_at = Column(DateTime)
    subscription_ends_at = Column(DateTime)
    
    # Limits
    max_users = Column(Integer, default=5)
    max_products = Column(Integer, default=100)
    max_storage_gb = Column(Integer, default=5)
    
    # Settings
    settings = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization")


class OrganizationInvitation(Base):
    __tablename__ = 'organization_invitation'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    token = Column(String(255), nullable=False, unique=True, index=True)
    
    invited_by_id = Column(BigInteger, ForeignKey('user.id'))
    accepted_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id])


# ============================================================================
# User Management
# ============================================================================

class User(Base):
    __tablename__ = 'user'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(50))
    avatar_url = Column(String(500))
    
    # Authorization
    role = Column(Enum(UserRole), default=UserRole.USER)
    permissions = Column(JSON)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    password_changed_at = Column(DateTime)
    
    # Preferences
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    preferences = Column(JSON)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("UserSession", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hash(password)
        self.password_changed_at = datetime.utcnow()
    
    def verify_password(self, password):
        """Verify password"""
        return bcrypt.verify(password, self.password_hash)
    
    @property
    def full_name(self):
        """Return full name"""
        return "{} {}".format(self.first_name, self.last_name)


class UserSession(Base):
    __tablename__ = 'user_session'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    
    token = Column(String(500), nullable=False, unique=True, index=True)
    refresh_token = Column(String(500), unique=True, index=True)
    
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    expires_at = Column(DateTime, nullable=False)
    refresh_expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_activity_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class ApiKey(Base):
    __tablename__ = 'api_key'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    prefix = Column(String(20), nullable=False)
    
    scopes = Column(JSON)
    
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    revoked_at = Column(DateTime)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")


# ============================================================================
# Audit & Compliance
# ============================================================================

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('user.id'))
    
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(BigInteger)
    
    changes = Column(JSON)
    audit_metadata = Column(JSON)
    
    ip_address = Column(String(50))
    user_agent = Column(Text)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_resource', 'organization_id', 'resource_type', 'resource_id'),
        Index('idx_audit_user_time', 'user_id', 'created_at'),
    )


# ============================================================================
# Notifications
# ============================================================================

class Notification(Base):
    __tablename__ = 'notification'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    data = Column(JSON)
    
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications")


# ============================================================================
# Webhooks
# ============================================================================

class Webhook(Base):
    __tablename__ = 'webhook'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)
    
    events = Column(JSON, nullable=False)
    
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime)
    failure_count = Column(Integer, default=0)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebhookDelivery(Base):
    __tablename__ = 'webhook_delivery'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    webhook_id = Column(BigInteger, ForeignKey('webhook.id'), nullable=False)
    
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)
    
    status_code = Column(Integer)
    response = Column(Text)
    error = Column(Text)
    
    delivered_at = Column(DateTime)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)


# ============================================================================
# File Attachments
# ============================================================================

class Attachment(Base):
    __tablename__ = 'attachment'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    uploaded_by_id = Column(BigInteger, ForeignKey('user.id'), nullable=False)
    
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(BigInteger, nullable=False)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    
    storage_path = Column(String(500), nullable=False)
    storage_provider = Column(String(50), default='local')
    
    description = Column(Text)
    attachment_metadata = Column(JSON)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_attachment_entity', 'entity_type', 'entity_id'),
    )


# ============================================================================
# Feature Flags & Settings
# ============================================================================

class FeatureFlag(Base):
    __tablename__ = 'feature_flag'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    key = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Integer, default=0)
    
    allowed_organizations = Column(JSON)
    allowed_users = Column(JSON)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Rate Limiting
# ============================================================================

class RateLimitCounter(Base):
    __tablename__ = 'rate_limit_counter'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    key = Column(String(255), nullable=False, index=True)
    count = Column(Integer, default=0)
    
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('key', 'window_start', name='uq_rate_limit_key_window'),
    )


# ============================================================================
# Domain Models - PLM (Product Lifecycle Management)
# ============================================================================

class ProductStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    OBSOLETE = "obsolete"

class RevisionStatus(str, enum.Enum):
    DRAFT = "draft"
    RELEASED = "released"
    OBSOLETE = "obsolete"

class ProductEventType(str, enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    STATUS_CHANGED = "status_changed"
    RELEASED = "released"

class BOMEventType(str, enum.Enum):
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    ITEM_QUANTITY_CHANGED = "item_quantity_changed"
    RELEASED = "released"

class Product(Base):
    __tablename__ = 'product'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    product_code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(Enum(ProductStatus), default=ProductStatus.DRAFT)
    
    current_revision_id = Column(BigInteger, ForeignKey('product_revision.id'))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_product_org_code', 'organization_id', 'product_code'),
    )

class ProductRevision(Base):
    __tablename__ = 'product_revision'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    
    revision_number = Column(Integer, nullable=False)
    name = Column(String(255))
    description = Column(Text)
    status = Column(Enum(RevisionStatus), default=RevisionStatus.DRAFT)
    
    released_at = Column(DateTime)
    released_by_id = Column(BigInteger, ForeignKey('user.id'))
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_revision_product', 'product_id', 'revision_number'),
    )

class ProductChangeEvent(Base):
    __tablename__ = 'product_change_event'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    
    event_type = Column(Enum(ProductEventType), nullable=False)
    event_data = Column(JSON)
    
    created_by_id = Column(BigInteger, ForeignKey('user.id'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class BOMCurrent(Base):
    __tablename__ = 'bom_current'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_revision_id = Column(BigInteger, ForeignKey('product_revision.id'), nullable=False)
    
    component_product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit = Column(String(50))
    
    position = Column(String(100))
    notes = Column(Text)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class BOMChangeEvent(Base):
    __tablename__ = 'bom_change_event'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_revision_id = Column(BigInteger, ForeignKey('product_revision.id'), nullable=False)
    
    event_type = Column(Enum(BOMEventType), nullable=False)
    event_data = Column(JSON)
    
    created_by_id = Column(BigInteger, ForeignKey('user.id'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)


# ============================================================================
# Domain Models - Logistics (Inventory & Shipments)
# ============================================================================

class TransactionType(str, enum.Enum):
    RECEIPT = "receipt"
    CONSUMPTION = "consumption"
    ADJUSTMENT = "adjustment"
    RETURN = "return"
    TRANSFER = "transfer"

class ShipmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PICKED = "picked"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class ShipmentEventType(str, enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    PICKED = "picked"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

class InventoryBalance(Base):
    __tablename__ = 'inventory_balance'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    
    location_code = Column(String(100), nullable=False)
    quantity_on_hand = Column(BigInteger, default=0)
    quantity_reserved = Column(BigInteger, default=0)
    
    last_counted_at = Column(DateTime)
    last_transaction_at = Column(DateTime)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_inventory_product_location', 'product_id', 'location_code'),
    )

class InventoryTransaction(Base):
    __tablename__ = 'inventory_transaction'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    location_code = Column(String(100), nullable=False)
    quantity = Column(BigInteger, nullable=False)
    
    reference_type = Column(String(100))
    reference_id = Column(BigInteger)
    
    notes = Column(Text)
    transaction_data = Column(JSON)
    
    created_by_id = Column(BigInteger, ForeignKey('user.id'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

class Shipment(Base):
    __tablename__ = 'shipment'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, ForeignKey('organization.id'), nullable=False)
    
    shipment_code = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    
    scheduled_ship_date = Column(DateTime)
    actual_ship_date = Column(DateTime)
    delivery_date = Column(DateTime)
    
    carrier = Column(String(100))
    tracking_number = Column(String(100))
    
    notes = Column(Text)
    shipment_data = Column(JSON)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShipmentLine(Base):
    __tablename__ = 'shipment_line'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger, ForeignKey('shipment.id'), nullable=False)
    product_id = Column(BigInteger, ForeignKey('product.id'), nullable=False)
    
    quantity_ordered = Column(BigInteger, nullable=False)
    quantity_packed = Column(BigInteger, default=0)
    quantity_shipped = Column(BigInteger, default=0)
    
    line_number = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

class ShipmentEvent(Base):
    __tablename__ = 'shipment_event'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shipment_id = Column(BigInteger, ForeignKey('shipment.id'), nullable=False)
    
    event_type = Column(Enum(ShipmentEventType), nullable=False)
    event_data = Column(JSON)
    
    created_by_id = Column(BigInteger, ForeignKey('user.id'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
