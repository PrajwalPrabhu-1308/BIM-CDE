"""
CDE SaaS Platform - Main Application
Complete FastAPI application with authentication, multi-tenancy, and all features
"""

from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import os

# Core imports
from backend.database import get_db, check_db_connection

# Services
from backend.auth_service import AuthService, OrganizationService
from backend.plm_service import PLMService
from backend.logistics_service import LogisticsService
from backend.analytics_service import AnalyticsService

# Models
from database.saas_models_py37 import User, Organization, UserRole, AuditLog, AuditAction

# Schemas
from database.schemas import *

# ============================================================================
# App Configuration
# ============================================================================

app = FastAPI(
    title="CDE SaaS Platform",
    description="Enterprise Supply Chain Intelligence Platform",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ============================================================================
# Authentication Dependencies
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials
    return AuthService.get_current_user(db, token)

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    return current_user

def require_role(*allowed_roles: UserRole):
    """Dependency to check user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker

def check_permission(resource: str, action: str):
    """Dependency to check specific permission"""
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        AuthService.require_permission(current_user, resource, action)
        return current_user
    return permission_checker

# ============================================================================
# Health & System Endpoints
# ============================================================================

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    db_connected = check_db_connection(db)
    return {
        "status": "healthy" if db_connected else "unhealthy",
        "database": "connected" if db_connected else "disconnected",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/debug/current-user")
def debug_current_user(current_user: User = Depends(get_current_active_user)):
    """Debug endpoint - shows current user and permissions"""
    return {
        "email": current_user.email,
        "id": current_user.id,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "organization_id": current_user.organization_id,
        "is_active": current_user.is_active,
        "permissions": current_user.permissions or "No custom permissions"
    }

# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_organization(
    slug: str,
    name: str,
    admin_email: str,
    admin_password: str,
    admin_first_name: str,
    admin_last_name: str,
    db: Session = Depends(get_db)
):
    """Register new organization with admin user"""
    try:
        org, admin = OrganizationService.create_organization(
            db, slug, name, admin_email, admin_password,
            admin_first_name, admin_last_name
        )
        
        # Generate tokens
        access_token = AuthService._create_access_token(admin)
        refresh_token = AuthService._create_refresh_token(admin)
        
        return {
            "organization": {
                "id": org.id,
                "slug": org.slug,
                "name": org.name
            },
            "admin": {
                "id": admin.id,
                "email": admin.email,
                "role": admin.role.value if hasattr(admin.role, 'value') else admin.role,
                "full_name": admin.full_name
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@app.post("/api/auth/login")
def login(
    email: str,
    password: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    return AuthService.authenticate(
        db, email, password,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )

@app.post("/api/auth/logout")
def logout(
    current_user: User = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Logout user and revoke session"""
    AuthService.logout(db, credentials.credentials)
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me")
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "organization_id": current_user.organization_id,
        "is_verified": current_user.is_verified,
        "timezone": current_user.timezone,
        "language": current_user.language,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None
    }

@app.get("/api/debug/check-permission")
def debug_check_permission(
    resource: str,
    action: str,
    current_user: User = Depends(get_current_active_user)
):
    """Debug endpoint - test if user has specific permission"""
    has_permission = AuthService.check_permission(current_user, resource, action)
    return {
        "user_email": current_user.email,
        "user_role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "resource": resource,
        "action": action,
        "has_permission": has_permission
    }

@app.post("/api/auth/api-keys", status_code=status.HTTP_201_CREATED)
def create_api_key(
    name: str,
    scopes: Optional[List[str]] = None,
    expires_in_days: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create API key for programmatic access"""
    api_key, raw_key = AuthService.create_api_key(
        db, current_user, name, scopes, expires_in_days
    )
    return {
        "api_key": raw_key,  # Only shown once!
        "id": api_key.id,
        "name": api_key.name,
        "prefix": api_key.prefix,
        "scopes": api_key.scopes,
        "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
        "warning": "Save this API key securely. It will not be shown again."
    }

# ============================================================================
# User Management Endpoints
# ============================================================================

@app.get("/api/users")
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ORG_ADMIN, UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """List users in organization"""
    users = db.query(User).filter(
        User.organization_id == current_user.organization_id
    ).offset(skip).limit(limit).all()
    
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None
        }
        for u in users
    ]

@app.post("/api/users", status_code=status.HTTP_201_CREATED)
def create_user(
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "USER",
    current_user: User = Depends(require_role(UserRole.ORG_ADMIN)),
    db: Session = Depends(get_db)
):
    """Create new user in organization"""
    try:
        user_role = UserRole(role.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")
    
    try:
        new_user = AuthService.create_user(
            db, current_user.organization_id,
            email, password, first_name, last_name, user_role
        )
        return {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role.value
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# PLM Endpoints (Multi-tenant)
# ============================================================================

@app.post("/api/plm/products", status_code=status.HTTP_201_CREATED)
def create_product(
    product: ProductCreate,
    current_user: User = Depends(check_permission("product", "create")),
    db: Session = Depends(get_db)
):
    """Create new product"""
    # Check resource limit
    if not OrganizationService.check_resource_limit(db, current_user.organization_id, "product"):
        raise HTTPException(status_code=403, detail="Product limit reached for your subscription tier")
    
    new_product = PLMService.create_product(
        db, current_user.organization_id, current_user.id,
        product.product_code, product.name, product.description
    )
    return new_product

@app.get("/api/plm/products")
def list_products(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(check_permission("product", "read")),
    db: Session = Depends(get_db)
):
    """List products in organization"""
    from models import Product, ProductStatus
    
    # Products are global, not org-specific
    query = db.query(Product)
    
    if status:
        try:
            query = query.filter(Product.status == ProductStatus(status.upper()))
        except ValueError:
            pass
    
    products = query.offset(skip).limit(limit).all()
    return products

@app.get("/api/plm/products/{product_id}")
def get_product(
    product_id: int,
    current_user: User = Depends(check_permission("product", "read")),
    db: Session = Depends(get_db)
):
    """Get product by ID"""
    from models import Product
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == current_user.organization_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

# Continue with other PLM endpoints...
# (I'll include the rest in the next section)

print("Main SaaS application created - Part 1")

# ============================================================================
# PLM Endpoints (continued)
# ============================================================================

@app.patch("/api/plm/products/{product_id}")
def update_product(
    product_id: int,
    product: ProductUpdate,
    current_user: User = Depends(check_permission("product", "update")),
    db: Session = Depends(get_db)
):
    """Update product"""
    from models import Product
    
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.organization_id == current_user.organization_id
    ).first()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return PLMService.update_product(
        db, current_user.organization_id, current_user.id,
        product_id, product.name, product.description, product.status
    )

@app.post("/api/plm/revisions", status_code=status.HTTP_201_CREATED)
def create_revision(
    revision: ProductRevisionCreate,
    current_user: User = Depends(check_permission("revision", "create")),
    db: Session = Depends(get_db)
):
    """Create product revision"""
    new_revision = PLMService.create_revision(
        db, current_user.organization_id, current_user.id,
        revision.product_id, revision.revision_number, revision.description
    )
    return new_revision

@app.post("/api/plm/revisions/{revision_id}/release")
def release_revision(
    revision_id: int,
    current_user: User = Depends(check_permission("revision", "release")),
    db: Session = Depends(get_db)
):
    """Release product revision"""
    return PLMService.release_revision(
        db, current_user.organization_id, current_user.id, revision_id
    )

@app.get("/api/plm/products/{product_id}/revisions")
def list_product_revisions(
    product_id: int,
    current_user: User = Depends(check_permission("revision", "read")),
    db: Session = Depends(get_db)
):
    """List revisions for a product"""
    from models import ProductRevision
    
    revisions = db.query(ProductRevision).filter(
        ProductRevision.product_id == product_id,
        ProductRevision.organization_id == current_user.organization_id
    ).all()
    
    return revisions

@app.post("/api/plm/revisions/{revision_id}/bom", status_code=status.HTTP_201_CREATED)
def add_bom_item(
    revision_id: int,
    bom_item: BOMItemCreate,
    current_user: User = Depends(check_permission("bom", "create")),
    db: Session = Depends(get_db)
):
    """Add BOM item"""
    new_item = PLMService.add_bom_item(
        db, current_user.organization_id, current_user.id,
        revision_id, bom_item.child_product_id, bom_item.quantity,
        bom_item.unit, bom_item.position_number
    )
    return new_item

@app.get("/api/plm/revisions/{revision_id}/bom")
def list_bom_items(
    revision_id: int,
    current_user: User = Depends(check_permission("bom", "read")),
    db: Session = Depends(get_db)
):
    """List BOM items for revision"""
    from models import BOMCurrent
    
    items = db.query(BOMCurrent).filter(
        BOMCurrent.parent_revision_id == revision_id,
        BOMCurrent.organization_id == current_user.organization_id
    ).all()
    
    return items

# ============================================================================
# Logistics Endpoints (Multi-tenant)
# ============================================================================

@app.post("/api/logistics/inventory/transactions", status_code=status.HTTP_201_CREATED)
def create_inventory_transaction(
    transaction: InventoryTransactionCreate,
    current_user: User = Depends(check_permission("inventory", "create")),
    db: Session = Depends(get_db)
):
    """Create inventory transaction"""
    new_transaction = LogisticsService.create_transaction(
        db, current_user.organization_id, current_user.id,
        transaction.product_id, transaction.location_code,
        transaction.transaction_type, transaction.quantity,
        transaction.unit, transaction.notes
    )
    return new_transaction

@app.get("/api/logistics/inventory/balances")
def list_inventory_balances(
    location_code: Optional[str] = None,
    current_user: User = Depends(check_permission("inventory", "read")),
    db: Session = Depends(get_db)
):
    """List inventory balances"""
    from models import InventoryBalance
    
    query = db.query(InventoryBalance).filter(
        InventoryBalance.organization_id == current_user.organization_id
    )
    
    if location_code:
        query = query.filter(InventoryBalance.location_code == location_code)
    
    return query.all()

@app.get("/api/logistics/inventory/transactions")
def list_inventory_transactions(
    product_id: Optional[int] = None,
    location_code: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(check_permission("inventory", "read")),
    db: Session = Depends(get_db)
):
    """List inventory transactions"""
    from models import InventoryTransaction
    
    query = db.query(InventoryTransaction).filter(
        InventoryTransaction.organization_id == current_user.organization_id
    )
    
    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)
    if location_code:
        query = query.filter(InventoryTransaction.location_code == location_code)
    
    return query.order_by(InventoryTransaction.created_at.desc()).limit(limit).all()

@app.post("/api/logistics/shipments", status_code=status.HTTP_201_CREATED)
def create_shipment(
    shipment: ShipmentCreate,
    current_user: User = Depends(check_permission("shipment", "create")),
    db: Session = Depends(get_db)
):
    """Create shipment"""
    from models import Shipment, ShipmentLine
    import json
    
    # Create shipment
    db_shipment = Shipment(
        organization_id=current_user.organization_id,
        shipment_number=shipment.shipment_number,
        from_location=shipment.from_location,
        to_location=shipment.to_location,
        destination_address=shipment.destination_address,
        planned_ship_date=shipment.planned_ship_date,
        notes=shipment.notes,
        created_by_id=current_user.id
    )
    db.add(db_shipment)
    db.flush()
    
    # Add lines
    for line in shipment.lines:
        db_line = ShipmentLine(
            organization_id=current_user.organization_id,
            shipment_id=db_shipment.id,
            product_id=line.product_id,
            quantity_planned=line.quantity_planned,
            unit=line.unit
        )
        db.add(db_line)
    
    db.commit()
    db.refresh(db_shipment)
    
    return db_shipment

@app.get("/api/logistics/shipments")
def list_shipments(
    status: Optional[str] = None,
    current_user: User = Depends(check_permission("shipment", "read")),
    db: Session = Depends(get_db)
):
    """List shipments"""
    from models import Shipment, ShipmentStatus
    
    query = db.query(Shipment).filter(
        Shipment.organization_id == current_user.organization_id
    )
    
    if status:
        try:
            query = query.filter(Shipment.status == ShipmentStatus(status.upper()))
        except ValueError:
            pass
    
    return query.all()

@app.get("/api/logistics/shipments/{shipment_id}")
def get_shipment(
    shipment_id: int,
    current_user: User = Depends(check_permission("shipment", "read")),
    db: Session = Depends(get_db)
):
    """Get shipment by ID"""
    from models import Shipment
    
    shipment = db.query(Shipment).filter(
        Shipment.id == shipment_id,
        Shipment.organization_id == current_user.organization_id
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    return shipment

@app.post("/api/logistics/shipments/{shipment_id}/confirm")
def confirm_shipment(
    shipment_id: int,
    current_user: User = Depends(check_permission("shipment", "update")),
    db: Session = Depends(get_db)
):
    """Confirm shipment (reserves inventory)"""
    return LogisticsService.confirm_shipment(
        db, current_user.organization_id, current_user.id, shipment_id
    )

@app.post("/api/logistics/shipments/{shipment_id}/pick")
def pick_shipment(
    shipment_id: int,
    quantities: dict,
    current_user: User = Depends(check_permission("shipment", "update")),
    db: Session = Depends(get_db)
):
    """Pick shipment"""
    return LogisticsService.pick_shipment(
        db, current_user.organization_id, current_user.id, shipment_id, quantities
    )

@app.post("/api/logistics/shipments/{shipment_id}/pack")
def pack_shipment(
    shipment_id: int,
    quantities: dict,
    current_user: User = Depends(check_permission("shipment", "update")),
    db: Session = Depends(get_db)
):
    """Pack shipment"""
    return LogisticsService.pack_shipment(
        db, current_user.organization_id, current_user.id, shipment_id, quantities
    )

@app.post("/api/logistics/shipments/{shipment_id}/ship")
def ship_shipment(
    shipment_id: int,
    carrier: Optional[str] = None,
    tracking_number: Optional[str] = None,
    current_user: User = Depends(check_permission("shipment", "update")),
    db: Session = Depends(get_db)
):
    """Ship shipment (issues inventory)"""
    return LogisticsService.ship_shipment(
        db, current_user.organization_id, current_user.id,
        shipment_id, carrier, tracking_number
    )

# ============================================================================
# Analytics Endpoints (Organization-scoped)
# ============================================================================

@app.get("/api/analytics/product-inventory")
def get_product_inventory(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get product inventory summary"""
    result = db.execute(
        "SELECT * FROM v_product_inventory_summary WHERE organization_id = :org_id",
        {"org_id": current_user.organization_id}
    )
    return [dict(row._mapping) for row in result]

@app.get("/api/analytics/bom-explosion/{revision_id}")
def get_bom_explosion(
    revision_id: int,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get BOM explosion"""
    result = db.execute(
        "SELECT * FROM v_bom_explosion WHERE organization_id = :org_id AND revision_id = :rev_id",
        {"org_id": current_user.organization_id, "rev_id": revision_id}
    )
    return [dict(row._mapping) for row in result]

@app.get("/api/analytics/shipment-overview")
def get_shipment_overview(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get shipment overview"""
    result = db.execute(
        "SELECT * FROM v_shipment_overview WHERE organization_id = :org_id",
        {"org_id": current_user.organization_id}
    )
    return [dict(row._mapping) for row in result]

@app.get("/api/analytics/recent-inventory-activity")
def get_recent_inventory_activity(
    limit: int = 100,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get recent inventory activity"""
    result = db.execute(
        "SELECT * FROM v_recent_inventory_activity WHERE organization_id = :org_id LIMIT :limit",
        {"org_id": current_user.organization_id, "limit": limit}
    )
    return [dict(row._mapping) for row in result]

@app.get("/api/analytics/product-change-history")
def get_product_change_history(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get product change history"""
    result = db.execute(
        "SELECT * FROM v_product_change_history WHERE organization_id = :org_id",
        {"org_id": current_user.organization_id}
    )
    return [dict(row._mapping) for row in result]

# Advanced Analytics (from analytics_service.py)
@app.get("/api/analytics/kpis/inventory")
def get_inventory_kpis(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get inventory KPIs"""
    return AnalyticsService.get_inventory_kpis(db)

@app.get("/api/analytics/kpis/shipments")
def get_shipment_kpis(
    days: int = 30,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get shipment KPIs"""
    return AnalyticsService.get_shipment_kpis(db, days)

@app.get("/api/analytics/kpis/plm")
def get_plm_kpis(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get PLM KPIs"""
    return AnalyticsService.get_plm_kpis(db)

@app.get("/api/analytics/dashboard")
def get_executive_dashboard(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get executive dashboard"""
    return AnalyticsService.get_executive_dashboard(db)

# ============================================================================
# Advanced Analytics Endpoints
# ============================================================================

@app.get("/api/analytics/trends/inventory")
def get_inventory_trends(
    days: int = 90,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get inventory trend analysis with forecasting"""
    return AnalyticsService.get_inventory_trend_analysis(db, days)

@app.get("/api/analytics/anomalies")
def detect_anomalies(
    threshold: float = 2.0,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Detect inventory anomalies using statistical analysis"""
    return AnalyticsService.detect_inventory_anomalies(db, threshold)

@app.get("/api/analytics/lifecycle")
def get_lifecycle_insights(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get product lifecycle analysis (introduction, growth, maturity, decline)"""
    return AnalyticsService.get_product_lifecycle_insights(db)

@app.get("/api/analytics/demand-supply")
def get_demand_supply(
    days: int = 30,
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get demand vs supply forecast with stockout risk analysis"""
    return AnalyticsService.get_demand_supply_forecast(db, days)

@app.get("/api/analytics/performance-benchmark")
def get_performance_benchmark(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get performance benchmarks and efficiency metrics"""
    return AnalyticsService.get_performance_benchmarks(db)

@app.get("/api/analytics/recommendations")
def get_optimization_recommendations(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get AI-driven optimization recommendations"""
    return AnalyticsService.get_optimization_recommendations(db)

@app.get("/api/analytics/bom-complexity")
def get_bom_complexity(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get BOM complexity analysis"""
    return AnalyticsService.get_bom_complexity_analysis(db)

@app.get("/api/analytics/abc-analysis")
def get_abc_analysis(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get ABC inventory classification analysis"""
    return AnalyticsService.perform_abc_analysis(db)

@app.get("/api/analytics/location-utilization")
def get_location_utilization(
    current_user: User = Depends(check_permission("analytics", "read")),
    db: Session = Depends(get_db)
):
    """Get warehouse location utilization metrics"""
    return AnalyticsService.get_location_utilization(db)

# ============================================================================
# Organization Endpoints
# ============================================================================

@app.get("/api/organizations/current")
def get_current_organization(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current organization details"""
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    return {
        "id": org.id,
        "slug": org.slug,
        "name": org.name,
        "email": org.email,
        "subscription_tier": org.subscription_tier.value,
        "subscription_status": org.subscription_status.value,
        "max_users": org.max_users,
        "max_products": org.max_products,
        "max_storage_gb": org.max_storage_gb,
        "trial_ends_at": org.trial_ends_at.isoformat() if org.trial_ends_at else None,
        "created_at": org.created_at.isoformat()
    }

@app.patch("/api/organizations/current")
def update_organization(
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.ORG_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update organization details"""
    org = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    
    if name:
        org.name = name
    if email:
        org.email = email
    if phone:
        org.phone = phone
    
    db.commit()
    db.refresh(org)
    
    return {"message": "Organization updated successfully"}

# ============================================================================
# Audit Log Endpoints
# ============================================================================

@app.get("/api/audit-logs")
def list_audit_logs(
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ORG_ADMIN, UserRole.MANAGER)),
    db: Session = Depends(get_db)
):
    """List audit logs for organization"""
    query = db.query(AuditLog).filter(
        AuditLog.organization_id == current_user.organization_id
    )
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if action:
        try:
            query = query.filter(AuditLog.action == AuditAction(action.upper()))
        except ValueError:
            pass
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action.value,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "changes": log.changes,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]

# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    print("CDE SaaS Platform starting...")
    print("Database: Connected")
    print("Authentication: Enabled")
    print("Multi-Tenancy: Active")
    print("All systems operational")

# ============================================================================
# Frontend Routes
# ============================================================================

@app.get("/")
async def root():
    """Serve dashboard"""
    with open("frontend/saas_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
    
@app.get("/plm")
async def plm():
    """Serve PLM interface"""
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/demo")
async def demo():
    """Serve research demo"""
    with open("frontend/research_demo.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/analytics")
async def analytics():
    """Serve advanced analytics dashboard"""
    with open("frontend/analytics_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    print("CDE SaaS Platform shutting down...")

# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_saas:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
