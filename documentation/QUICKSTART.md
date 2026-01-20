# CDE SaaS Platform - Quick Start Guide

## 🚀 Fastest Way to Start (Choose One)

### Option 1: One-Click Python Script (Easiest)
```bash
cd c:\Users\prajw\Desktop\CDE-MVP
python startup.py
```
✅ Checks prerequisites
✅ Sets up database
✅ Starts server
✅ Shows status

### Option 2: PowerShell Script
```powershell
cd c:\Users\prajw\Desktop\CDE-MVP

# Quick start (keeps existing data)
.\start.ps1

# Full reset (fresh database)
.\start.ps1 -Mode clean
```

### Option 3: Manual Step-by-Step

**Step 1: Create Database**
```bash
mysql -u root -p
DROP DATABASE IF EXISTS cde_saas;
CREATE DATABASE cde_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

mysql -u root -p cde_saas < schema_saas.sql
```

**Step 2: Start Server** (new terminal)
```bash
cd c:\Users\prajw\Desktop\CDE-MVP
python main_saas.py
```

**Step 3: Test System** (another terminal)
```bash
python debug_test.py
```

---

## 📋 What Happens on Startup

✅ Database connection verified
✅ All tables initialized
✅ Server running on http://localhost:8000
✅ Authentication system ready
✅ Role-based permissions active
✅ API endpoints responding

---

## 🔑 Quick Test

### Register (Get Token)
```bash
curl -X POST "http://localhost:8000/api/auth/register?slug=test&name=Test&admin_email=admin@test.com&admin_password=Pass123!&admin_first_name=Admin&admin_last_name=User"
```

Save the `access_token` from response.

### Test API
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/plm/products

curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/analytics/product-inventory
```

Both should return **200 OK** ✅

---

## 🐛 Debug Endpoints

### See Current User
```bash
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/debug/current-user
```

### Test Permissions
```bash
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/debug/check-permission?resource=analytics&action=read"
```

---

## ⚠️ Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| "Unknown database" | DB not created | Run `mysql -u root -p cde_saas < schema_saas.sql` |
| "403 Forbidden" | Old token | Register new account and use new token |
| "Port 8000 in use" | Process still running | `Get-Process python \| Stop-Process -Force` |
| "Invalid token" | Expired token | Generate new token via registration |
| Server won't start | Missing MySQL | Install MySQL 8.x and start service |

---

## 📁 Key Files

```
CDE-MVP/
├── main_saas.py          ← FastAPI application (START HERE)
├── startup.py            ← Startup helper script
├── start.ps1             ← PowerShell startup
├── debug_test.py         ← Test script
├── STARTUP_GUIDE.md      ← Detailed guide
├── QUICKSTART.md         ← This file
├── auth_service.py       ← Authentication logic
├── database.py           ← DB connection
├── models.py             ← Data models
├── saas_models_py37.py   ← ORM models
├── schema_saas.sql       ← Database schema
└── requirements.txt      ← Dependencies
```

---

## 🎯 System Ready When You See

**Server Terminal:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
CDE SaaS Platform starting...
Database: Connected
Authentication: Enabled
Multi-Tenancy: Active
All systems operational
INFO:     Application startup complete.
```

**Test Output:**
```
[1] REGISTERING NEW USER...
Registration Status: 201 ✅
[2] CHECKING CURRENT USER...
Status: 200 ✅
[3] CHECKING ANALYTICS PERMISSION...
has_permission: true ✅
[4] TESTING ANALYTICS ENDPOINT...
Status: 200 ✅
```

---

## 📊 Features

✅ **Multi-Tenancy** - Organizations isolated
✅ **Authentication** - JWT tokens with refresh
✅ **Permissions** - Role-based (org_admin, manager, user, viewer)
✅ **Products** - Full CRUD operations
✅ **Inventory** - Stock tracking
✅ **Shipments** - Logistics management
✅ **Analytics** - Dashboard data
✅ **Debug Tools** - Built-in troubleshooting

---

## 🔗 API Quick Reference

### Auth
- `POST /api/auth/register` - New organization
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Current user

### Products
- `GET /api/plm/products` - List
- `POST /api/plm/products` - Create
- `GET /api/plm/products/{id}` - Read
- `PUT /api/plm/products/{id}` - Update
- `DELETE /api/plm/products/{id}` - Delete

### Analytics  
- `GET /api/analytics/product-inventory`
- `GET /api/analytics/shipment-overview`
- `GET /api/analytics/recent-inventory-activity`

### Debug
- `GET /api/debug/current-user`
- `GET /api/debug/check-permission?resource=X&action=Y`
- `GET /health`

---

## 📝 Next Steps

1. ✅ Start the server
2. ✅ Register a test account
3. ✅ Get API token
4. ✅ Test endpoints
5. 👉 Build your frontend using the APIs

See `STARTUP_GUIDE.md` for detailed documentation.

---

Version: 2.0 (Production Ready)
Updated: 2026-01-18

```bash
# Create and activate virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Start API Server (30 seconds)

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Verify**: Open http://localhost:8000/health - should return `{"status":"healthy","database":"connected"}`

## Step 4: View API Documentation (30 seconds)

Open http://localhost:8000/docs

You'll see interactive Swagger UI with all endpoints documented.

## Step 5: Open Frontend (30 seconds)

### Option A: Direct file
Simply open `index.html` in your browser

### Option B: HTTP Server (recommended)
```bash
# In a new terminal
python -m http.server 8080
```
Then open http://localhost:8080/index.html

## Quick Test

### Via Frontend UI:
1. Click "PLM" tab
2. Click "Load Products" - you should see 5 sample products
3. Click "Logistics" tab
4. Click "Load Inventory" - you should see inventory balances
5. Click "Analytics" tab
6. Click "Load Summary" - you should see combined PLM+Logistics data

### Via API (using curl):

```bash
# List products
curl http://localhost:8000/api/plm/products

# Check inventory
curl http://localhost:8000/api/logistics/inventory/balances

# View analytics
curl http://localhost:8000/api/analytics/product-inventory
```

### Via Python Test Script:

```bash
python test_integration.py
```

This will run a complete workflow:
1. Create products and BOM
2. Receive inventory
3. Create and ship a shipment
4. View analytics

## Sample Workflow: Create a Product

```bash
# Create a new product
curl -X POST http://localhost:8000/api/plm/products \
  -H "Content-Type: application/json" \
  -d '{
    "product_code": "TEST-001",
    "name": "My Test Product",
    "description": "Testing the API",
    "status": "development"
  }'

# Create a revision
curl -X POST http://localhost:8000/api/plm/revisions \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 6,
    "revision_number": "A",
    "description": "First version"
  }'

# Add to inventory
curl -X POST http://localhost:8000/api/logistics/inventory/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 6,
    "location_code": "WH-01",
    "transaction_type": "receipt",
    "quantity": 100,
    "unit": "EA",
    "notes": "Initial stock"
  }'

# Check the balance
curl http://localhost:8000/api/logistics/inventory/balances/6/WH-01
```

## Troubleshooting

### "Database connection failed"
- Ensure XAMPP MariaDB is running
- Check that database `cde_mvp` exists
- Verify credentials in database.py or set DATABASE_URL environment variable

### "Address already in use"
- Port 8000 is taken. Change port in main.py or:
  ```bash
  uvicorn main:app --port 8001
  ```

### "ModuleNotFoundError"
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Frontend shows no data
- Ensure API is running on http://localhost:8000
- Check browser console (F12) for errors
- Verify CORS is not blocking requests

## Next Steps

1. **Explore the API**: Use http://localhost:8000/docs to try all endpoints
2. **View the Data**: Check phpMyAdmin to see state and event tables
3. **Run Tests**: Execute `python test_integration.py` for full workflow
4. **Read Documentation**: See README.md for detailed architecture info
5. **Build Features**: Add your own products, create BOMs, manage inventory!

## Key Endpoints to Try

### PLM
- List products: GET `/api/plm/products`
- Create product: POST `/api/plm/products`
- Create revision: POST `/api/plm/revisions`
- Add BOM item: POST `/api/plm/revisions/{id}/bom`

### Logistics
- Create inventory transaction: POST `/api/logistics/inventory/transactions`
- List balances: GET `/api/logistics/inventory/balances`
- Create shipment: POST `/api/logistics/shipments`
- Process shipment: POST `/api/logistics/shipments/{id}/confirm|pick|pack|ship`

### Analytics
- Product inventory: GET `/api/analytics/product-inventory`
- Recent activity: GET `/api/analytics/recent-inventory-activity`
- Shipment overview: GET `/api/analytics/shipment-overview`

## Architecture Highlights

✓ **State + Event Tables**: Every change is tracked
✓ **Atomic Transactions**: All operations are ACID compliant
✓ **Domain Separation**: PLM and Logistics never cross-write
✓ **Analytics Views**: SQL views for read-only cross-domain queries
✓ **REST API**: Clean, documented endpoints
✓ **No Auth**: Simplified for MVP (add authentication for production)

## Support

- API Docs: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc
- Database: http://localhost/phpmyadmin

Happy coding! 🚀
