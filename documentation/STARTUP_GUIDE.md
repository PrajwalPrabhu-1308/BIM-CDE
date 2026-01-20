# CDE SaaS Platform - Startup Guide

## Prerequisites

### 1. Database Setup
Ensure MySQL 8.x is running:
```bash
# Check MySQL status
mysql -u root -p -e "SELECT VERSION();"
```

### 2. Python 3.7+ Installed
```bash
python --version
# Should show Python 3.7.x or higher
```

### 3. Dependencies Installed
```bash
cd c:\Users\prajw\Desktop\CDE-MVP
pip install -r requirements.txt
```

---

## Step 1: Initialize Database

### Option A: Fresh Start (Recommended)
Drop and recreate the database:

```bash
# Connect to MySQL
mysql -u root -p

# In MySQL console:
DROP DATABASE IF EXISTS cde_saas;
CREATE DATABASE cde_saas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;

# Load schema
mysql -u root -p cde_saas < schema_saas.sql
```

### Option B: Keep Existing Data
Just verify the database exists:
```bash
mysql -u root -p -e "USE cde_saas; SHOW TABLES;"
```

---

## Step 2: Start the API Server

### From PowerShell Terminal:
```powershell
cd "c:\Users\prajw\Desktop\CDE-MVP"
python main_saas.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
CDE SaaS Platform starting...
Database: Connected
Authentication: Enabled
Multi-Tenancy: Active
All systems operational
```

---

## Step 3: Test the System

### Option A: Quick Test (Python)
```bash
cd "c:\Users\prajw\Desktop\CDE-MVP"
python debug_test.py
```

This will:
- Register a new org and admin user
- Test authentication
- Verify analytics permissions
- Verify product access
- Display all results

### Option B: Manual Testing with cURL

**1. Register a new organization:**
```bash
curl -X POST "http://localhost:8000/api/auth/register?slug=myorg&name=MyOrg&admin_email=admin@myorg.com&admin_password=Password123!&admin_first_name=Admin&admin_last_name=User"
```

Response will include: `access_token`, `refresh_token`, `role`

**2. Save the token:**
```powershell
$token = "YOUR_TOKEN_HERE"
$headers = @{"Authorization" = "Bearer $token"}
```

**3. Test Analytics:**
```bash
curl -H "Authorization: Bearer $token" "http://localhost:8000/api/analytics/product-inventory"
```

**4. Test Products:**
```bash
curl -H "Authorization: Bearer $token" "http://localhost:8000/api/plm/products"
```

### Option C: Debug Endpoints

**Check your current user:**
```bash
curl -H "Authorization: Bearer $token" "http://localhost:8000/api/debug/current-user"
```

Response shows:
```json
{
  "email": "admin@myorg.com",
  "id": 1,
  "role": "org_admin",
  "organization_id": 1,
  "is_active": true,
  "permissions": "No custom permissions"
}
```

**Test a specific permission:**
```bash
curl -H "Authorization: Bearer $token" "http://localhost:8000/api/debug/check-permission?resource=analytics&action=read"
```

Response:
```json
{
  "user_email": "admin@myorg.com",
  "user_role": "org_admin",
  "resource": "analytics",
  "action": "read",
  "has_permission": true
}
```

---

## Step 4: Access the Frontend

### HTML Dashboard
Open browser and visit:
```
http://localhost:8000/
http://localhost:8000/plm
http://localhost:8000/demo
```

---

## Troubleshooting

### Issue: "Unknown database 'cde_saas'"
**Solution:** Run the database initialization steps above

### Issue: "Permission denied" (403 Forbidden)
**Solution:** 
1. Make sure you're using a fresh token from a NEW registration
2. Old tokens from before the fixes won't work
3. Use `/api/debug/current-user` to verify your role

### Issue: Server won't start
**Solution:** Check if port 8000 is in use:
```powershell
Get-NetTcpConnection -LocalPort 8000
# If it shows python.exe, kill it:
Get-Process python | Stop-Process -Force
```

### Issue: "Invalid token"
**Solution:** Token might be expired or from old session
- Register a new account
- Use the new token

---

## API Endpoints Overview

### Authentication
- `POST /api/auth/register` - Register new organization
- `POST /api/auth/login` - Login user
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user info

### PLM (Products, Revisions, BOMs)
- `GET /api/plm/products` - List products
- `POST /api/plm/products` - Create product
- `GET /api/plm/products/{id}` - Get product
- `PUT /api/plm/products/{id}` - Update product
- `DELETE /api/plm/products/{id}` - Delete product

### Analytics
- `GET /api/analytics/product-inventory` - Product inventory stats
- `GET /api/analytics/shipment-overview` - Shipment stats
- `GET /api/analytics/recent-inventory-activity?limit=20` - Activity log

### Debug (Development Only)
- `GET /api/debug/current-user` - Show current user info
- `GET /api/debug/check-permission?resource=X&action=Y` - Test permissions

---

## User Roles & Permissions

### org_admin (Organization Admin)
✅ Can:
- Create/edit/delete products, revisions, BOMs
- Create/edit/delete inventory, shipments
- Manage users
- View analytics
- Update organization settings

### manager (Manager)
✅ Can:
- Create/edit products and revisions
- Manage inventory and shipments
- View analytics
❌ Cannot:
- Manage users
- Delete resources
- Update organization settings

### user (User)
✅ Can:
- View products, revisions, BOMs
- Create/update shipments
- View inventory
- View analytics
❌ Cannot:
- Create/delete products
- Manage inventory
- Manage users

### viewer (Viewer)
✅ Can:
- View products, revisions, BOMs
- View inventory
- View shipments
- View analytics
❌ Cannot:
- Create or modify anything

---

## System Features

### ✅ Completed
- Multi-tenancy (organization isolation)
- JWT authentication with refresh tokens
- Role-based access control (RBAC)
- Product/Revision/BOM management
- Inventory tracking
- Shipment management
- Analytics dashboards
- Debug endpoints for troubleshooting

### 🔧 Configuration
Database connection: `mysql+pymysql://root:@localhost:3306/cde_saas`

Edit `database.py` if you need to change:
- Host
- Port
- Username
- Password
- Database name

---

## Quick Reference

### Start Fresh
```bash
# Kill old processes
Get-Process python | Stop-Process -Force

# Reset database
mysql -u root -p -e "DROP DATABASE cde_saas; CREATE DATABASE cde_saas;"
mysql -u root -p cde_saas < schema_saas.sql

# Start server
python main_saas.py

# In another terminal, test
python debug_test.py
```

### Common Workflow
```bash
# 1. Start server
python main_saas.py

# 2. Register (in another terminal)
python debug_test.py

# 3. Use the token from output for API calls
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/api/plm/products"
```

---

## Files Overview

| File | Purpose |
|------|---------|
| `main_saas.py` | Main FastAPI application |
| `auth_service.py` | Authentication & permissions |
| `database.py` | Database connection |
| `models.py` | Data models (Products, Users, etc.) |
| `saas_models_py37.py` | ORM models for SQLAlchemy |
| `schemas.py` | Pydantic validation schemas |
| `requirements.txt` | Python dependencies |
| `schema_saas.sql` | Database schema |
| `debug_test.py` | Test script |

---

## Need Help?

1. **Check `/api/debug/current-user`** - Verify your user and role
2. **Check `/api/debug/check-permission?resource=X&action=Y`** - Test specific permissions
3. **Check server logs** - Look for error messages when making requests
4. **Check database** - Verify tables and data exist
5. **Use fresh token** - Don't reuse old tokens

---

Generated: 2026-01-18
