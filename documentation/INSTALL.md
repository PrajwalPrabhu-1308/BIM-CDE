# 📖 CDE SaaS Platform - Complete Setup Guide

## 🎯 What You're Getting

A **production-ready** multi-tenant SaaS platform with:
- ✅ FastAPI backend (Python 3.7+)
- ✅ MySQL database
- ✅ JWT authentication
- ✅ Role-based permissions
- ✅ Multi-tenancy (org isolation)
- ✅ PLM (Product Lifecycle Management)
- ✅ Inventory & Shipment tracking
- ✅ Analytics dashboards

---

## 🚀 Quick Start (3 Steps)

### Step 1: Ensure MySQL is Running
```bash
# Windows - Start MySQL service
net start MySQL80

# Or from Services: MySQL80 → Start
```

### Step 2: Run Startup Script
```bash
cd c:\Users\prajw\Desktop\CDE-MVP
python startup.py
```

**What it does:**
- ✓ Checks Python version
- ✓ Checks MySQL connection
- ✓ Checks required packages
- ✓ Creates/resets database
- ✓ Starts the API server

### Step 3: Test Everything
```bash
# In a new terminal
cd c:\Users\prajw\Desktop\CDE-MVP
python debug_test.py
```

**What it shows:**
- ✓ Registration: 201 Created
- ✓ User info retrieval: 200 OK
- ✓ Permission checks: true
- ✓ Analytics access: 200 OK
- ✓ Products access: 200 OK

---

## 📍 Server Locations

| Component | URL |
|-----------|-----|
| **API Base** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Health Check** | http://localhost:8000/health |
| **Dashboard** | http://localhost:8000/ |
| **PLM Module** | http://localhost:8000/plm |

---

## 🔐 Getting Your First Token

### Method 1: Using debug_test.py
```bash
python debug_test.py
# Shows token in output
```

### Method 2: Using curl
```bash
curl -X POST "http://localhost:8000/api/auth/register?slug=myorg&name=MyOrg&admin_email=admin@test.com&admin_password=Test@123456&admin_first_name=Admin&admin_last_name=User"
```

### Method 3: Using PowerShell
```powershell
$params = @{
    slug = "testorg"
    name = "Test Org"
    admin_email = "admin@test.com"
    admin_password = "Test@123456"
    admin_first_name = "Admin"
    admin_last_name = "User"
}
$response = Invoke-WebRequest -Uri "http://localhost:8000/api/auth/register" -Method POST -Body $params
$token = ($response.Content | ConvertFrom-Json).access_token
Write-Host "Token: $token"
```

**Save your token:**
```powershell
$token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## 🧪 Testing Endpoints

### Test with Debug Endpoint
```bash
curl -H "Authorization: Bearer $token" \
  "http://localhost:8000/api/debug/current-user"
```

**Expected response:**
```json
{
  "email": "admin@test.com",
  "id": 1,
  "role": "org_admin",
  "organization_id": 1,
  "is_active": true,
  "permissions": "No custom permissions"
}
```

### Test with Real Endpoint
```bash
curl -H "Authorization: Bearer $token" \
  "http://localhost:8000/api/plm/products"
```

**Expected:** 200 OK with product list

### Test Analytics
```bash
curl -H "Authorization: Bearer $token" \
  "http://localhost:8000/api/analytics/product-inventory"
```

**Expected:** 200 OK with analytics data

---

## 📚 Documentation Files

### Quick References
- **`REFERENCE.md`** - One-page API reference (start here for cheat sheet)
- **`QUICKSTART.md`** - 5-minute startup guide
- **`SYSTEM_STATUS.md`** - What was fixed and verified

### Detailed Guides
- **`STARTUP_GUIDE.md`** - Complete setup instructions
- **`ARCHITECTURE.md`** - System design and architecture
- **`README.md`** - General information

### Executable Scripts
- **`startup.py`** - Interactive startup with checks
- **`start.ps1`** - PowerShell startup script
- **`debug_test.py`** - Automated test suite
- **`test_api.py`** - Manual API tests
- **`test_integration.py`** - Integration tests

---

## 🎮 Common Workflows

### Workflow 1: Get Started
```bash
# Terminal 1
python startup.py

# Terminal 2 (wait 3 seconds)
python debug_test.py

# See ✅ for all tests
```

### Workflow 2: Manual Testing
```bash
# Start server
python main_saas.py

# Register user
curl -X POST "http://localhost:8000/api/auth/register?..."

# Copy token

# Test endpoint
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/plm/products
```

### Workflow 3: Development
```bash
# Terminal 1 - Always Running
python main_saas.py

# Terminal 2 - Development
# Make changes to code
# Changes auto-reload (Uvicorn watch mode)

# Terminal 3 - Testing
curl ... # your tests
```

---

## 📊 API Endpoints Summary

### Authentication (Public)
```
POST   /api/auth/register              → 201 Created + tokens
POST   /api/auth/login                 → 200 OK + tokens
POST   /api/auth/logout                → 200 OK (requires token)
GET    /api/auth/me                    → User info (requires token)
```

### Products (Requires: product:read)
```
GET    /api/plm/products               → List all products
POST   /api/plm/products               → Create product
GET    /api/plm/products/{id}          → Get specific product
PUT    /api/plm/products/{id}          → Update product
DELETE /api/plm/products/{id}          → Delete product
```

### Analytics (Requires: analytics:read)
```
GET    /api/analytics/product-inventory        → Stock data
GET    /api/analytics/shipment-overview        → Shipment stats
GET    /api/analytics/recent-inventory-activity → Activity log
```

### Debug (Development Only)
```
GET    /api/debug/current-user         → Show your user info
GET    /api/debug/check-permission     → Test permissions
GET    /health                         → Server status
```

---

## 🔑 User Roles

### org_admin (Organization Admin)
**Can do:** Create/edit/delete everything, manage users, view analytics
**Best for:** Organization owners

### manager (Manager)
**Can do:** Create/edit products, manage inventory, view analytics
**Best for:** Department managers

### user (User)
**Can do:** View products, manage shipments, view analytics
**Best for:** Regular employees

### viewer (Viewer)
**Can do:** View-only access to all data
**Best for:** Auditors, stakeholders

---

## ⚙️ Configuration

### Database Connection
File: `database.py`
```python
DATABASE_URL = "mysql+pymysql://root:@localhost:3306/cde_saas"
```

**Change if:**
- Using different MySQL host/port
- Using different username/password
- Using different database name

### API Settings
File: `main_saas.py`
```python
app = FastAPI(title="CDE SaaS API", version="2.0.0")
```

---

## 🐛 Troubleshooting

### "Connection refused" on port 8000
```bash
# Port already in use
Get-Process python | Stop-Process -Force
python startup.py
```

### "Unknown database 'cde_saas'"
```bash
# Database not created
mysql -u root -p cde_saas < schema_saas.sql
```

### "403 Forbidden" on analytics
```bash
# Old token before fixes
# Get new token:
python debug_test.py
```

### "Invalid credentials" in MySQL
Check `database.py` line 1:
```python
DATABASE_URL = "mysql+pymysql://USERNAME:PASSWORD@localhost:3306/cde_saas"
```

### "ModuleNotFoundError" on import
```bash
pip install -r requirements.txt
```

---

## 📈 Performance Tips

### Development (Single User Testing)
```bash
python main_saas.py
# Default settings perfect for dev
```

### Production (Multiple Users)
```bash
# Use production ASGI server
pip install gunicorn
gunicorn main_saas:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

---

## 🔄 Maintenance

### Daily
- Check server logs for errors
- Monitor database size
- Review failed login attempts

### Weekly
- Backup database
- Review user activity logs
- Check for unused organizations

### Monthly
- Analyze analytics
- Update dependencies
- Review permissions

---

## 📝 What's Included

```
CDE-MVP/
├── Core Files
│   ├── main_saas.py                 FastAPI app (30KB)
│   ├── auth_service.py              Authentication (15KB)
│   ├── database.py                  DB connection
│   ├── models.py                    ORM models
│   └── saas_models_py37.py         Python 3.7 models
│
├── Services
│   ├── plm_service.py               Product management
│   ├── analytics_service.py         Analytics data
│   └── logistics_service.py         Shipment tracking
│
├── Scripts
│   ├── startup.py                   Smart startup
│   ├── start.ps1                    PowerShell startup
│   ├── debug_test.py                Automated tests
│   └── test_api.py                  Manual tests
│
├── Documentation
│   ├── QUICKSTART.md                5-min guide ← START HERE
│   ├── REFERENCE.md                 Cheat sheet
│   ├── STARTUP_GUIDE.md             Full setup
│   ├── SYSTEM_STATUS.md             What's fixed
│   └── ARCHITECTURE.md              System design
│
└── Database
    ├── schema_saas.sql              Tables & schema
    └── requirements.txt             Dependencies
```

---

## 🎓 Learning Path

1. **Read:** `QUICKSTART.md` (5 min)
2. **Run:** `python startup.py` (3 min)
3. **Test:** `python debug_test.py` (1 min)
4. **Explore:** API at http://localhost:8000/docs
5. **Build:** Use the APIs for your app

---

## ✅ Verification Checklist

After startup, verify:
- [ ] Server running on http://localhost:8000
- [ ] Database has tables
- [ ] Registration endpoint returns 201
- [ ] Can retrieve token
- [ ] Analytics endpoint returns 200 OK
- [ ] Products endpoint returns 200 OK
- [ ] Debug endpoints working
- [ ] Health check passing

---

## 🆘 Need Help?

1. Check `REFERENCE.md` for quick answers
2. Review `STARTUP_GUIDE.md` for setup issues
3. Look at debug endpoints:
   - `/api/debug/current-user` - Check your user
   - `/api/debug/check-permission?resource=X&action=Y` - Test permissions
4. Check server logs for errors
5. Check database connection in `database.py`

---

## 🎉 You're Ready!

Everything is set up and working. 

**Next step:** `python startup.py`

Have fun! 🚀

---

Created: 2026-01-18
Version: 2.0 (Production Ready)
Status: ✅ All systems operational
