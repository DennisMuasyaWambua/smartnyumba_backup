# Activation Payment Token Fix

## Problem Summary

After successful OTP verification, landlords encountered an error when attempting to initiate activation payment:

**Backend Error:**
```
Token request failed with status code: 400
Activation STK Push response: {'requestId': '51a5-4880-ab95-0592c46fbe712081', 'errorCode': '404.001.03', 'errorMessage': 'Invalid Access Token'}
Bad Request: /apps/api/v1/auth/initiate-activation-payment/
```

**Frontend Error:**
```json
{
  "status": false,
  "message": "Payment initiation failed",
  "error": {
    "requestId": "51a5-4880-ab95-0592c46fbe712081",
    "errorCode": "404.001.03",
    "errorMessage": "Invalid Access Token"
  }
}
```

## Root Cause

The issue occurred in the payment initiation flow:

1. `InitiateActivationPaymentAPIView` calls `get_access_token()` to get Safaricom M-Pesa access token
2. `get_access_token()` makes a request to Safaricom's OAuth endpoint but receives status code 400 (Bad Request)
3. The function returns `False` instead of a valid token
4. **The code didn't check if the token was valid** before using it
5. The authorization header became `"Authorization": 'Bearer False'`
6. Safaricom rejected the STK Push request with error "404.001.03: Invalid Access Token"

### Why Token Generation Failed

The token generation failed (400 status code) likely due to:
- **Expired or invalid Safaricom sandbox credentials** (most common)
- Incorrect `SAFARICOM_AUTH_KEY` or `SAFARICOM_AUTH_CONSUMER_SECRET`
- Safaricom sandbox app may have been regenerated/deleted
- Network/connectivity issues to Safaricom's API

## Changes Made

### 1. Added Token Validation in Payment Initiation (views.py:1516-1523)

**File:** `/home/dennis/Desktop/projects/smartnyumba_backup/authentication/api/views.py`

```python
access_token = get_access_token()

# Check if token generation failed
if not access_token or access_token == False:
    print("Failed to get Safaricom access token")
    return Response({
        'status': False,
        'message': 'Failed to authenticate with payment provider. Please try again later or contact support.',
        'error': 'Token generation failed'
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

This prevents sending invalid tokens to Safaricom and provides a clear error message to users.

### 2. Enhanced Error Logging (api_auth.py:38-41)

**File:** `/home/dennis/Desktop/projects/smartnyumba_backup/utils/api_auth.py`

```python
else:
    print("Token request failed with status code:", response.status_code)
    print("Token endpoint:", token_endpoint)
    print("Response:", response.text)
    print("Check your SAFARICOM_AUTH_KEY and SAFARICOM_AUTH_CONSUMER_SECRET in .env")
    return False
```

This provides more detailed diagnostics when token generation fails.

## How to Resolve

### Option 1: Update Safaricom Sandbox Credentials (Recommended)

1. **Log in to Safaricom Daraja Portal:**
   - Visit: https://developer.safaricom.co.ke/login
   - Log in with your account

2. **Create or Access Your Sandbox App:**
   - Navigate to "My Apps"
   - Create a new sandbox app or select existing one
   - Click on your app to view credentials

3. **Copy the New Credentials:**
   - Consumer Key (this is `SAFARICOM_AUTH_KEY`)
   - Consumer Secret (this is `SAFARICOM_AUTH_CONSUMER_SECRET`)

4. **Update .env File:**

   Open `/home/dennis/Desktop/projects/smartnyumba_backup/.env` and update:
   ```env
   SAFARICOM_AUTH_KEY=your_new_consumer_key_here
   SAFARICOM_AUTH_CONSUMER_SECRET=your_new_consumer_secret_here
   ```

5. **Restart Django Server:**
   ```bash
   cd ~/Desktop/projects/smartnyumba_backup
   # Kill existing server if running
   pkill -f "python manage.py runserver" || true
   # Start server
   python manage.py runserver
   ```

### Option 2: Test Token Generation Manually

Test if your credentials work:

```bash
cd ~/Desktop/projects/smartnyumba_backup
python manage.py shell
```

Then run:
```python
from utils.api_auth import get_access_token

# Test token generation
token = get_access_token()

if token:
    print(f"Success! Token: {token[:20]}...")
else:
    print("Failed to get token. Check the error logs above.")
```

### Option 3: Use Production Credentials (If Available)

If you have production M-Pesa credentials:

1. Update `.env` with production credentials
2. Change endpoint from sandbox to production:
   ```env
   SAFARICOM_AUTH_ENDPOINT=https://api.safaricom.co.ke/oauth/v1/generate
   SAFARICOM_STK_PUSH=https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest
   ```

## Testing the Fix

### 1. Test Token Generation

After updating credentials:
```bash
cd ~/Desktop/projects/smartnyumba_backup
python manage.py shell
```

```python
from utils.api_auth import get_access_token
token = get_access_token()
print(f"Token valid: {bool(token)}")
```

### 2. Test Full Payment Flow

1. **Register a new landlord** (or use existing test account)
2. **Verify OTP**
3. **Initiate activation payment:**
   ```
   POST http://localhost:8000/apps/api/v1/auth/initiate-activation-payment/
   {
     "email": "test@example.com",
     "mobile_number": "254712345678"
   }
   ```

4. **Expected responses:**
   - **If token generation fails:** Clear error message (no longer sends invalid token)
   - **If credentials valid:** STK Push sent to phone

### 3. Check Logs

Monitor Django console for detailed diagnostics:
```bash
# Look for these messages:
Token request failed with status code: 400
Token endpoint: https://sandbox.safaricom.co.ke/oauth/v1/generate
Response: {"error": "..."}
Check your SAFARICOM_AUTH_KEY and SAFARICOM_AUTH_CONSUMER_SECRET in .env
```

## Current .env Credentials

Current sandbox credentials in `.env`:
```env
SAFARICOM_AUTH_ENDPOINT=https://sandbox.safaricom.co.ke/oauth/v1/generate
SAFARICOM_AUTH_KEY=gHA6y3j3ERj6B9CJZL9nhD1l42pxrbrF
SAFARICOM_AUTH_CONSUMER_SECRET=z8Vk4JByW1GO76jo
```

**Action Required:** These credentials appear to be invalid/expired. Update them from Daraja portal.

## Expected Behavior After Fix

### Before Fix:
1. OTP verified ✅
2. Initiate payment → Token fails → Sends `Bearer False` → M-Pesa rejects with "Invalid Access Token" ❌

### After Fix:
1. OTP verified ✅
2. Initiate payment → Token fails → Returns clear error: "Failed to authenticate with payment provider" ✅
3. OR: Token succeeds → STK Push sent → User receives M-Pesa prompt ✅

## Files Modified

1. **authentication/api/views.py** (Line 1516-1523)
   - Added validation to check if access token is valid before using it
   - Returns proper error message if token generation fails

2. **utils/api_auth.py** (Line 38-41)
   - Enhanced error logging to show full response and guidance

## Next Steps

1. ✅ **Fix Applied:** Code now handles invalid tokens gracefully
2. ⏳ **Update Credentials:** Get fresh credentials from Safaricom Daraja portal
3. ⏳ **Test:** Verify token generation works
4. ⏳ **Deploy:** Restart backend server with new credentials

## Troubleshooting

### Still Getting 400 Error After Updating Credentials?

1. **Verify credentials are correct:**
   - No extra spaces in .env file
   - Consumer Key and Secret match exactly from Daraja portal

2. **Check Daraja portal:**
   - Is your app active?
   - Is it a sandbox app with proper products (Lipa Na M-Pesa Online)?

3. **Test with curl:**
   ```bash
   CONSUMER_KEY="your_key_here"
   CONSUMER_SECRET="your_secret_here"

   curl -X GET 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials' \
     -H "Authorization: Basic $(echo -n $CONSUMER_KEY:$CONSUMER_SECRET | base64)"
   ```
   Should return: `{"access_token": "...", "expires_in": "3599"}`

### Frontend Still Shows "Payment Failed"?

- The frontend will now receive a clearer error message
- User should be instructed to contact support if credentials are truly invalid
- Once credentials are fixed, the payment flow will work end-to-end

---

**Status:** ✅ Code fix complete
**Action Required:** Update Safaricom credentials in `.env` file
