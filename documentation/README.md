# CDE SaaS Platform - Common Data Environment

An enterprise-grade Supply Chain Intelligence Platform with PLM (Product Lifecycle Management), Logistics Management, and Advanced Analytics.

## 🎯 What You Get

**Product Lifecycle Management (PLM)**
- Product master data management
- Engineering revisions with version control
- Bill of Materials (BOM) management
- Revision lifecycle (Draft → Released)

**Logistics Management**
- Real-time inventory tracking
- Inventory transaction history
- Shipment lifecycle management
- Multi-status shipment processing (Draft → Confirmed → Picked → Packed → Shipped)

**Advanced Analytics & AI**
- 8 advanced analytics functions
- Machine learning algorithms (scikit-learn)
- Trend analysis & forecasting
- Anomaly detection
- Performance KPIs (A+ to D grading)
- AI-driven optimization recommendations
- Interactive analytics dashboard

**Enterprise Features**
- Multi-tenant architecture (isolated by organization)
- Role-based access control (org_admin, manager, user, viewer)
- Comprehensive audit logging
- Transaction safety with event sourcing
- RESTful API-first design

## 🚀 Quick Start

```bash
cd c:\Users\prajw\Desktop\CDE-MVP
python startup.py
```

**What this does:**
- ✅ Checks prerequisites (Python 3.11+, MariaDB)
- ✅ Creates/resets database schema
- ✅ Starts FastAPI server on port 8000
- ✅ Displays access URLs

**Then open in browser:**
- API Dashboard: http://localhost:8000/docs
- Analytics: http://localhost:8000/analytics
- Main Dashboard: http://localhost:8000/

## 📋 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | Python 3.11+ with FastAPI |
| **Database** | MariaDB 10.11+ |
| **ORM** | SQLAlchemy with PyMySQL |
| **Frontend** | HTML5 + Tailwind CSS |
| **Analytics** | Pandas, NumPy, Scikit-learn, SciPy |
| **Visualization** | Plotly.js |
| **API** | REST with JWT authentication |

## 📁 Project Structure

```
CDE-MVP/
├── main_saas.py                    # FastAPI application (50+ endpoints)
├── backend/
│   ├── auth_service.py             # Authentication & authorization
│   ├── plm_service.py              # Product management logic
│   ├── logistics_service.py        # Inventory & shipment logic
│   ├── analytics_service.py        # ML & analytics engine
│   └── database.py                 # Database connection
├── database/
│   ├── schemas.py                  # Pydantic models
│   ├── saas_models_py37.py         # SQLAlchemy models
│   └── schema_saas.sql             # Database DDL
├── frontend/
│   ├── index.html                  # Main dashboard
│   ├── analytics_dashboard.html    # Analytics visualization
│   ├── saas_dashboard.html         # Business dashboard
│   └── research_demo.html          # Research interface
├── documentation/
│   ├── README.md                   # This file
│   ├── QUICKSTART.md               # 5-min setup
│   ├── STARTUP_GUIDE.md            # Detailed setup
│   ├── ARCHITECTURE.md             # System design
│   ├── REFERENCE.md                # API endpoints
│   └── INSTALL.md                  # Installation help
└── requirements.txt                # Python dependencies
```

## 🔑 Key Features

### PLM Module
- Create and manage products
- Track product revisions
- Design and modify BOMs
- Release engineering changes

### Logistics Module
- Record inventory transactions
- Track stock balances by location
- Create and manage shipments
- Process shipments through workflow

### Analytics Module
- **Inventory Trends**: 90-day history + 7-day forecast
- **Anomaly Detection**: Statistical pattern recognition
- **Lifecycle Analysis**: Product stage classification
- **Demand-Supply**: Risk-based forecasting
- **Performance Grading**: A+ to D KPI scores
- **Recommendations**: AI-driven optimization
- **BOM Complexity**: Component analysis
- **ABC Analysis**: Pareto classification

### Interactive Dashboard
- Real-time charts (Plotly)
- 7 visualization types
- Responsive design
- Works with mock data (no auth required)

## 🔐 Authentication

**Default Test Account:**
```
Email: admin@example.com
Password: Admin123!
Organization: Test Org
```

**Or Register New:**
```
POST /api/auth/register
```

**All requests require JWT token:**
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## 📚 Documentation

| File | Purpose | Read Time |
|------|---------|-----------|
| `QUICKSTART.md` | Get running in 5 minutes | 5 min |
| `STARTUP_GUIDE.md` | Step-by-step setup | 10 min |
| `ARCHITECTURE.md` | System design & patterns | 15 min |
| `REFERENCE.md` | Complete API reference | 10 min |
| `INSTALL.md` | Troubleshooting | 5 min |

## 🧪 Testing

```bash
# Start server first
python startup.py

# In new terminal, run tests
python tests/test_api.py
python tests/test_integration.py
```

## 📊 API Endpoints (Sample)

**Authentication**
```
POST /api/auth/register  - Create account
POST /api/auth/login     - Get JWT token
POST /api/auth/logout    - Clear session
```

**PLM**
```
GET  /api/plm/products               - List all products
POST /api/plm/products               - Create product
GET  /api/plm/products/{id}          - Get product
PATCH /api/plm/products/{id}         - Update product
GET  /api/plm/products/{id}/revisions - Get revisions
POST /api/plm/revisions/{id}/release  - Release revision
GET  /api/plm/revisions/{id}/bom    - Get BOM
```

**Logistics**
```
GET  /api/logistics/inventory/balances       - Current stock
POST /api/logistics/inventory/transactions   - Record movement
GET  /api/logistics/shipments                - List shipments
POST /api/logistics/shipments                - Create shipment
POST /api/logistics/shipments/{id}/pick      - Pick items
POST /api/logistics/shipments/{id}/ship      - Ship order
```

**Analytics**
```
GET /api/analytics/dashboard                 - Full dashboard data
GET /api/analytics/trends/inventory          - Inventory trends
GET /api/analytics/recommendations           - ML recommendations
GET /api/analytics/performance-benchmark     - KPI grades
GET /api/analytics/anomalies                 - Pattern analysis
GET /api/analytics/abc-analysis              - Pareto analysis
```

See [REFERENCE.md](REFERENCE.md) for complete endpoint list.

## ⚙️ Configuration

**Database Connection** (`database.py`):
```python
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/cde_saas"
```

**Server Port** (`main_saas.py`):
```
localhost:8000 (configurable)
```

**Admin Credentials** (set during registration)

## 🛠️ Troubleshooting

**Database connection error?**
→ See [INSTALL.md](INSTALL.md)

**Port 8000 already in use?**
→ Kill: `Get-Process python | Stop-Process -Force`

**Permissions denied?**
→ Check user role in `/api/auth/me`

**Analytics showing mock data?**
→ Normal! Requires `analytics:read` permission

## 📈 What Makes This Production-Ready

✅ **Modular Architecture**: Clear separation of concerns
✅ **Transaction Safety**: ACID guarantees with event sourcing
✅ **Audit Trail**: Complete change history
✅ **Multi-tenant**: Org isolation built-in
✅ **Type Safety**: Pydantic validation + SQLAlchemy
✅ **Error Handling**: Comprehensive exception management
✅ **ML Integration**: Scikit-learn for real algorithms
✅ **Dashboard**: Interactive Plotly visualizations
✅ **REST API**: Full swagger documentation at /docs

## 🚀 Scaling Path

**Current**: Single server, all-in-one deployment
**Next**: Read replicas, caching layer
**Later**: Microservices, sharding, multiple regions

## 📞 Support

**For API issues**: Check `/api/debug/current-user` endpoint
**For database issues**: See `INSTALL.md`
**For feature requests**: Extend `analytics_service.py`

## 📄 License & Version

**Version**: 2.0.0
**Date**: January 2026
**Status**: ✅ Production Ready

---

**Ready to start?** → See [QUICKSTART.md](QUICKSTART.md)
