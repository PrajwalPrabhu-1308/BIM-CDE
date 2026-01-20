# CDE MVP - Architecture Documentation

## System Overview

The Common Data Environment (CDE) is a modular monolithic application designed to support Product Lifecycle Management (PLM) and Logistics operations for MSMEs (Micro, Small & Medium Enterprises).

### Core Design Principles

1. **Event Sourcing Architecture**: State + Event pattern for audit trail and data integrity
2. **Domain-Driven Design**: Clear separation between PLM and Logistics domains
3. **Transaction Safety**: ACID guarantees for all write operations
4. **Modular Monolith**: Single deployable unit with clear domain boundaries
5. **API-First**: UI never accesses database directly

## Architecture Layers

```
┌─────────────────────────────────────────────────┐
│              Frontend (HTML/JS)                  │
│   Dashboard + Analytics Visualization           │
│         Read/Write via REST API only            │
└─────────────────────────────────────────────────┘
                      ↓ HTTP
┌─────────────────────────────────────────────────┐
│           FastAPI Application Layer              │
│  ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │PLM Router│ │Logistics │ │Analytics Router│  │
│  │          │ │Router    │ │ - Dashboards   │  │
│  └──────────┘ └──────────┘ │ - Trends       │  │
│                             │ - Forecasts    │  │
│                             │ - Recommendations
│                             └────────────────┘  │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│           Service Layer (Business Logic)         │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────┐ │
│  │ PLMService   │ │ Logistics    │ │Analytics│ │
│  │              │ │ Service      │ │Service  │ │
│  │ - Products   │ │ - Inventory  │ │ - ML    │ │
│  │ - Revisions  │ │ - Shipments  │ │ - Stats │ │
│  │ - BOM        │ │              │ │ - Viz   │ │
│  └──────────────┘ └──────────────┘ └─────────┘ │
│         NO CROSS-DOMAIN WRITES                   │
│     AnalyticsService: Read-Only Analytics       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│         Data Access Layer (SQLAlchemy ORM)       │
└─────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│              MariaDB Database                    │
│  ┌──────────────┐  ┌──────────────┐            │
│  │ State Tables │  │ Event Tables │            │
│  │              │  │              │            │
│  │ - product    │  │ - product_   │            │
│  │ - revision   │  │   change_    │            │
│  │ - bom_current│  │   event      │            │
│  │ - inventory_ │  │ - bom_change_│            │
│  │   balance    │  │   event      │            │
│  │ - shipment   │  │ - inventory_ │            │
│  │              │  │   transaction│            │
│  │              │  │ - shipment_  │            │
│  │              │  │   event      │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  ┌──────────────────────────────────┐           │
│  │      Analytics Views              │           │
│  │  (Read-Only, Cross-Domain)        │           │
│  │                                   │           │
│  │ - v_product_inventory_summary    │           │
│  │ - v_bom_explosion                │           │
│  │ - v_shipment_overview            │           │
│  │ - v_recent_inventory_activity    │           │
│  │ - v_product_change_history       │           │
│  └──────────────────────────────────┘           │
└─────────────────────────────────────────────────┘
```

## Data Architecture

### State + Event Pattern

Every domain entity follows this pattern:

**State Table**: Current state of the entity
- Updated via UPDATE/INSERT/DELETE operations
- Represents "what is" (current truth)
- Indexed for fast queries

**Event Table**: Historical record of all changes
- INSERT-only (append-only log)
- Represents "what happened" (audit trail)
- Contains full change context (who, what, when, why)

### Transaction Pattern

All write operations follow this atomic pattern:

```python
def write_operation(db, data):
    try:
        db.begin()
        
        # 1. Validate business rules
        validate(data)
        
        # 2. Update/Create state
        state_record = update_state(data)
        db.flush()  # Get ID if needed
        
        # 3. Create event
        event = create_event(state_record, action_type, data)
        db.add(event)
        
        # 4. Atomic commit
        db.commit()
        return state_record
        
    except Exception as e:
        db.rollback()
        raise
```

### Domain Boundaries

#### PLM Domain
**Owns**:
- Product master data
- Product revisions (version control)
- Bill of Materials (product structure)

**Responsibilities**:
- Product lifecycle management
- Version control
- Engineering change management
- BOM management

**Tables**:
- State: `product`, `product_revision`, `bom_current`
- Events: `product_change_event`, `bom_change_event`

#### Logistics Domain
**Owns**:
- Inventory balances
- Inventory transactions
- Shipment data

**Responsibilities**:
- Inventory tracking
- Warehouse management
- Shipment processing
- Stock movements

**Tables**:
- State: `inventory_balance`, `shipment`, `shipment_line`
- Events: `inventory_transaction`, `shipment_event`

#### Analytics Domain
**Owns**:
- Cross-domain data aggregation
- Statistical analysis and ML predictions
- Performance metrics and KPIs
- Recommendations engine

**Responsibilities**:
- Inventory trend analysis and forecasting
- Anomaly detection (statistical)
- Product lifecycle classification
- Demand-supply forecasting
- Performance benchmarking
- AI-driven optimization recommendations
- BOM complexity analysis
- ABC inventory classification

**Data Sources** (read-only):
- Product data (PLM)
- Inventory transactions (Logistics)
- Shipment data (Logistics)

**ML Algorithms**:
- Z-score statistical analysis (safety stock, anomaly detection)
- K-means clustering (demand pattern classification)
- Linear programming (optimization)
- Regression models (forecasting, trend analysis)
- Isolation Forest (anomaly detection)

**Technology Stack**:
- Scikit-learn (ML algorithms)
- Pandas (data manipulation)
- NumPy (numerical computing)
- SciPy (statistical functions)
- Statsmodels (time-series analysis)

## Key Business Flows

### 1. Product Creation Flow

```
User Request
    ↓
POST /api/plm/products
    ↓
PLMService.create_product()
    ↓
┌─────────────────────┐
│ BEGIN TRANSACTION   │
├─────────────────────┤
│ 1. Insert product   │ (state)
│ 2. Flush to get ID  │
│ 3. Insert event     │ (event)
│ 4. Commit           │
└─────────────────────┘
    ↓
Return product
```

### 2. BOM Management Flow

```
Create Product
    ↓
Create Revision (status: draft)
    ↓
Add BOM Items
    ↓  (only allowed on draft)
Update BOM Items
    ↓
Release Revision
    ↓  (sets current_revision_id)
    ├─ Change revision status to 'released'
    └─ BOM becomes read-only
```

### 3. Inventory Transaction Flow

```
POST /api/logistics/inventory/transactions
    ↓
LogisticsService.create_transaction()
    ↓
┌─────────────────────────────────┐
│ BEGIN TRANSACTION               │
├─────────────────────────────────┤
│ 1. Get/Create inventory_balance │ (state)
│ 2. Calculate new balance        │
│ 3. Validate (no negative qty)   │
│ 4. Update balance               │
│ 5. Insert transaction           │ (event)
│ 6. Commit                       │
└─────────────────────────────────┘
    ↓
Return transaction
```

### 4. Shipment Lifecycle Flow

```
Draft → Confirmed → Picked → Packed → Shipped
  ↓         ↓          ↓         ↓        ↓
Create   Reserve   Record    Record   Issue
         Inventory Picking   Packing  Inventory
                                      +Release
                                      Reservation
```

Each status transition:
1. Updates shipment state
2. Creates shipment_event
3. May create inventory_transaction
4. All within single transaction

## Database Design Details

### Indexing Strategy

**Primary Keys**: Auto-increment BIGINT for scalability

**Foreign Keys**: 
- All relationships have FK constraints
- CASCADE delete where appropriate
- ON DELETE RESTRICT for critical references

**Indexes**:
- All status fields (for filtering)
- All date fields (for sorting)
- Product codes (for lookups)
- Location codes (for filtering)
- Composite indexes for common queries

### Generated Columns

```sql
-- Computed available quantity
quantity_available = quantity_on_hand - quantity_reserved
```

Automatically updated by database, always consistent.

### JSON Event Data

Event tables store flexible JSON for:
- Change tracking (before/after values)
- Contextual information
- Extended attributes
- Future extensibility

Example:
```json
{
  "changes": {
    "status": {
      "old": "development",
      "new": "active"
    },
    "name": {
      "old": "Old Name",
      "new": "New Name"
    }
  },
  "user_id": 123,
  "reason": "Product ready for production"
}
```

## API Design

### REST Conventions

- **GET**: Retrieve resources (read-only)
- **POST**: Create new resources
- **PATCH**: Partial update of resources
- **DELETE**: Remove resources

### Endpoint Structure

```
/api/{domain}/{entity}/{action}

Examples:
/api/plm/products              - List products
/api/plm/products/{id}         - Get product
/api/plm/revisions/{id}/bom    - Get BOM
/api/logistics/shipments       - List shipments
/api/logistics/shipments/{id}/confirm - Action
/api/analytics/product-inventory - Analytics
```

### Request/Response Format

All requests and responses use JSON.

**Request Validation**: Pydantic schemas ensure:
- Required fields present
- Correct data types
- Business constraints (e.g., quantity > 0)

**Response Format**:
```json
{
  "id": 1,
  "product_code": "WIDGET-001",
  "name": "Standard Widget",
  "status": "active",
  "created_at": "2024-01-18T10:30:00",
  "updated_at": "2024-01-18T10:30:00"
}
```

**Error Format**:
```json
{
  "detail": "Product WIDGET-001 already exists"
}
```

### Pagination

```
GET /api/plm/products?skip=0&limit=100
```

Default limit: 100
Max limit: 1000

## Service Layer Patterns

### Dependency Injection

```python
@app.get("/api/plm/products")
def list_products(db: Session = Depends(get_db)):
    return PLMService.list_products(db)
```

Database session injected per request, automatically closed.

### Error Handling

```python
try:
    # Business logic
    result = service.operation(db, data)
    return result
except ValueError as e:
    # Business rule violation
    raise HTTPException(status_code=400, detail=str(e))
except IntegrityError as e:
    # Database constraint violation
    raise HTTPException(status_code=409, detail="Conflict")
except Exception as e:
    # Unexpected error
    raise HTTPException(status_code=500, detail="Internal error")
```

### Transaction Management

```python
@contextmanager
def get_db_context():
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()
```

## Scalability Considerations

### Current MVP Limitations

1. **Single Database**: All data in one MariaDB instance
2. **No Caching**: Direct database queries
3. **Synchronous**: No background jobs
4. **No Sharding**: Single organization only

### Future Scaling Path

1. **Read Replicas**: Separate read/write databases
2. **Redis Caching**: Cache frequently accessed data
3. **Message Queue**: Async processing (RabbitMQ/Celery)
4. **Microservices**: Split PLM and Logistics if needed
5. **Database Sharding**: Multi-tenant by organization

### Performance Optimization

**Already Implemented**:
- Database connection pooling
- Indexed queries
- Efficient ORM queries
- SQL views for complex queries

**Future Optimizations**:
- Query result caching
- Batch operations
- Materialized views
- Full-text search (Elasticsearch)

## Security Model (Future)

Current MVP: No authentication

Production Requirements:
1. **Authentication**: JWT tokens, OAuth2
2. **Authorization**: Role-based access control (RBAC)
3. **Audit Logging**: Track all user actions
4. **Data Encryption**: Encrypt sensitive fields
5. **API Rate Limiting**: Prevent abuse
6. **SQL Injection Protection**: Already handled by ORM

## Testing Strategy

### Unit Tests
- Service layer business logic
- Validation rules
- Transaction rollback scenarios

### Integration Tests
- End-to-end workflows
- API endpoint testing
- Database interaction

### Test Script Usage
```bash
python test_integration.py
```

Validates:
- Product creation with BOM
- Inventory transactions
- Shipment lifecycle
- Analytics views

## Deployment Architecture

### Development
```
Developer Machine
├── XAMPP MariaDB (localhost:3306)
├── FastAPI (localhost:8000)
└── Frontend (file:// or localhost:8080)
```

### Production (Recommended)
```
Load Balancer
    ↓
Application Servers (FastAPI + Uvicorn)
    ↓
Database Server (MariaDB with replication)
    ↓
Backup Storage
```

### Docker Deployment (Future)
```yaml
services:
  db:
    image: mariadb:10.11
  api:
    build: .
    depends_on: [db]
  nginx:
    image: nginx
    depends_on: [api]
```

## Monitoring & Observability

### Logging
- Application logs: Python logging module
- Database logs: MariaDB slow query log
- Access logs: Uvicorn access logs

### Metrics (Future)
- Request latency
- Error rates
- Database query performance
- Cache hit rates

### Health Checks
```
GET /health
Returns: {"status": "healthy", "database": "connected"}
```

## Extension Points

### Adding New Domains

1. Create `{domain}_service.py`
2. Add models to `models.py`
3. Add schemas to `schemas.py`
4. Add router to `main.py`
5. Create state + event tables
6. Maintain domain isolation

### Adding New Features

1. Add business logic to service layer
2. Add API endpoint to main.py
3. Update frontend if needed
4. Create/update database views for analytics

### Custom Business Rules

Implement in service layer:
```python
def custom_validation(data):
    if not meets_criteria(data):
        raise ValueError("Business rule violation")
```

## Conclusion

This architecture provides:

✓ **Data Integrity**: ACID transactions, event sourcing
✓ **Maintainability**: Clear domain separation
✓ **Auditability**: Complete change history
✓ **Scalability**: Foundation for growth
✓ **Flexibility**: Easy to extend and modify

The modular monolith approach allows rapid development while maintaining clear boundaries for future microservices migration if needed.
