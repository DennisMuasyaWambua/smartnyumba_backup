# How to Restart Django Server with Pesapal Changes

## Issue
The Django server was running the old M-Pesa code and needed to be restarted to load the Pesapal changes.

## Solution

### 1. Stop Existing Server

```bash
# Kill any running Django servers
pkill -f "python.*manage.py runserver"

# Or press Ctrl+C in the terminal where the server is running
```

### 2. Clear Python Cache

```bash
cd ~/Desktop/projects/smartnyumba_backup

# Clear all cached Python files
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete 2>/dev/null

echo "✓ Cache cleared"
```

### 3. Restart Server

```bash
cd ~/Desktop/projects/smartnyumba_backup

# Start Django development server
python3 manage.py runserver 0.0.0.0:8000
```

You should see:
```
Django version X.X.X, using settings 'smartnyumba_system.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

### 4. Test Activation Payment

Now try the activation payment again from your Flutter app. You should see:

**Instead of M-Pesa errors:**
```
Token request failed with status code: 400  ← OLD (WRONG)
Activation STK Push response: {...}         ← OLD (WRONG)
```

**You should see Pesapal responses:**
```
Pesapal payment initiated successfully      ← NEW (CORRECT)
redirect_url: https://cybqa.pesapal.com/... ← NEW (CORRECT)
```

---

## What Changed

The server now uses **Pesapal** instead of M-Pesa for activation payments:

### Old Flow (Before Restart):
- ❌ M-Pesa STK Push API
- ❌ Daraja token generation
- ❌ Only M-Pesa supported

### New Flow (After Restart):
- ✅ Pesapal Web Checkout
- ✅ OAuth2 token (Pesapal)
- ✅ M-Pesa + Cards supported
- ✅ WebView integration

---

## Troubleshooting

### Server Won't Start - Database Error

If you see:
```
django.db.utils.OperationalError: connection to server...
```

**Solution:**
1. Check your database is running
2. Verify `.env` file has correct `MY_DATABASE_URL`
3. Test database connection:
   ```bash
   python3 manage.py dbshell
   ```

### Still Getting M-Pesa Errors

If you still see "Token request failed" errors:

1. **Verify server restarted:**
   ```bash
   ps aux | grep "manage.py runserver"
   ```
   Should show the new process

2. **Check logs:**
   Look for "Pesapal" in server output, not "M-Pesa"

3. **Verify code changes:**
   ```bash
   grep -A 5 "INITIATE PESAPAL PAYMENT" authentication/api/views.py
   ```
   Should show Pesapal code

### Port Already in Use

If you see `Error: That port is already in use`:

```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
python3 manage.py runserver 0.0.0.0:8001
```

---

## Quick Start (All Steps)

```bash
# 1. Stop old server
pkill -f "python.*manage.py runserver"

# 2. Navigate to project
cd ~/Desktop/projects/smartnyumba_backup

# 3. Clear cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# 4. Start server
python3 manage.py runserver 0.0.0.0:8000
```

---

## Verification

### Test the Endpoint Manually

```bash
curl -X POST http://localhost:8000/apps/api/v1/auth/initiate-activation-payment/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "mobile_number": "254712345678",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Expected Response:**
```json
{
  "status": true,
  "message": "Please complete payment in the checkout page",
  "redirect_url": "https://cybqa.pesapal.com/iframe/PesapalIframe3/Index/?OrderTrackingId=...",
  "order_tracking_id": "...",
  "merchant_reference": "ACTIVATION-42-...",
  "amount": 500.0
}
```

**NOT this (old M-Pesa error):**
```json
{
  "status": false,
  "message": "Payment initiation failed",
  "error": {
    "errorCode": "404.001.03",
    "errorMessage": "Invalid Access Token"
  }
}
```

---

## Additional Notes

- The server must be restarted after code changes
- Python caches compiled bytecode (.pyc files)
- Clearing cache ensures new code is loaded
- The same applies to production deployments

---

**Status**: Ready to test
**Next Step**: Restart server and test activation payment
