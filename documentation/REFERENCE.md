# Quick Reference Card

## 🚀 START HERE
```bash
cd c:\Users\prajw\Desktop\CDE-MVP
python startup.py
```

## 🧪 TEST HERE
```bash
python debug_test.py
```

---

## API Endpoints

### Register Org
```
POST /api/auth/register?slug=ORG&name=NAME&admin_email=EMAIL&admin_password=PASS&admin_first_name=FIRST&admin_last_name=LAST
→ Returns: {access_token, refresh_token, role, ...}
```

### Login
```
POST /api/auth/login?email=EMAIL&password=PASS
→ Returns: {access_token, refresh_token}
```

### Get User Info
```
GET /api/auth/me
Header: Authorization: Bearer TOKEN
```

### List Products
```
GET /api/plm/products
Header: Authorization: Bearer TOKEN
```

### Create Product
```
POST /api/plm/products
Header: Authorization: Bearer TOKEN
Body: {name, description, ...}
```

### Analytics Dashboard
```
GET /api/analytics/dashboard
Header: Authorization: Bearer TOKEN (optional)
→ Returns: Comprehensive dashboard data with charts
```

### Analytics Endpoints (All require analytics:read permission)
```
GET /api/analytics/product-inventory
→ Inventory by product with stock levels

GET /api/analytics/shipment-overview
→ Shipment status summary

GET /api/analytics/recent-inventory-activity?limit=20
→ Recent inventory transactions

GET /api/analytics/trends/inventory
→ 90-day inventory trends + 7-day forecast

GET /api/analytics/anomalies
→ Statistical anomaly detection

GET /api/analytics/lifecycle
→ Product lifecycle stage analysis

GET /api/analytics/demand-supply
→ Demand-supply risk analysis

GET /api/analytics/performance-benchmark
→ KPI performance grading (A+ to D)

GET /api/analytics/recommendations
→ AI-driven optimization recommendations

GET /api/analytics/bom-complexity
→ Bill of Materials complexity analysis

GET /api/analytics/abc-analysis
→ Pareto ABC inventory classification

GET /api/analytics/bom-explosion/{revision_id}
→ Detailed BOM explosion

GET /api/analytics/product-change-history
→ Product changes and revisions

GET /api/analytics/kpis/inventory
→ Inventory KPIs

GET /api/analytics/kpis/shipments
→ Shipment KPIs

GET /api/analytics/kpis/plm
→ PLM KPIs

GET /api/analytics/location-utilization
→ Warehouse location utilization

Header: Authorization: Bearer TOKEN
```

---

## Debug Endpoints

### See Current User
```
GET /api/debug/current-user
Header: Authorization: Bearer TOKEN
```

### Test Permission
```
GET /api/debug/check-permission?resource=analytics&action=read
Header: Authorization: Bearer TOKEN
```

### Health
```
GET /health
```

---

## User Roles & Permissions

### org_admin
✅ All CRUD operations
✅ User management
✅ Analytics
✅ Organization settings

### manager
✅ CRUD on products, inventory, shipments
✅ Analytics
❌ User management

### user
✅ View products, inventory, shipments
✅ Create/update shipments
✅ Analytics

### viewer
✅ View-only access
✅ Analytics

---

## Database

**Name:** cde_saas
**Host:** localhost:3306
**User:** root
**Password:** (empty/your password)

**Reset:**
```bash
mysql -u root -p cde_saas < schema_saas.sql
```

---

## Common Commands

| Command | Purpose |
|---------|---------|
| `python startup.py` | Start with setup |
| `python main_saas.py` | Start server only |
| `python debug_test.py` | Run tests |
| `Get-Process python \| Stop-Process -Force` | Kill server |
| `.\start.ps1 -Mode clean` | PowerShell startup with reset |

---

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized (no token) |
| 403 | Forbidden (permission denied) |
| 404 | Not Found |
| 500 | Server Error |

---

## Documentation Files

- `QUICKSTART.md` - 5 min start
- `STARTUP_GUIDE.md` - Full details  
- `SYSTEM_STATUS.md` - What's fixed
- `ARCHITECTURE.md` - System design

---

## Important Notes

⚠️ Always use **fresh tokens** - old ones won't work after updates
⚠️ Register new accounts for testing
⚠️ Each org is **completely isolated** (multi-tenant)
⚠️ Permissions checked on **every request**

---

## Server Logs Location

While server runs, you can see:
```
INFO:     127.0.0.1:PORT - "METHOD /PATH HTTP/1.1" STATUS
```

For example:
```
INFO:     127.0.0.1:52256 - "GET /api/plm/products HTTP/1.1" 200 OK
```

---

## How to Test Everything

1. **Start server:** `python startup.py`
2. **In new terminal:** `python debug_test.py`
3. **Watch output:** Should show ✅ for all tests
4. **Done!** System is working

---

Version: 2.0
Date: 2026-01-18
Status: ✅ Ready for Production
