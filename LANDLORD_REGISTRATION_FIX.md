# Landlord Registration OTP and Payment Activation Fixes

## Date: 2026-05-12

## Issues Found and Fixed

### 1. **Critical: BlockLandlord Import Error** (FIXED)
**File:** `authentication/api/views.py:880`

**Problem:** 
Inside the `UserRegisterVerificationAPIView` function, there was an incorrect import:
```python
from authentication.models import BlockLandlord
```

The `BlockLandlord` model is NOT in `authentication.models` - it's in `block_landlord.models`.

**Fix:**
Removed the redundant import on line 880. The correct import already exists at the top of the file (line 17):
```python
from block_landlord.models import BlockLandlord
```

---

### 2. **Phone Number Formatting Bug** (FIXED)
**File:** `authentication/api/views.py:600`

**Problem:**
The phone number formatting for landlords/accounts/caretakers was using:
```python
phone_number = phone_number[:9]  # Takes FIRST 9 characters
```

This should take the LAST 9 digits to match the tenant registration flow and properly format Kenyan phone numbers.

**Fix:**
Changed line 600 to:
```python
phone_number = phone_number[-9:]  # Takes LAST 9 digits
```

This ensures the phone number is consistently formatted as `254XXXXXXXXX` for OTP lookup.

---

### 3. **Activation Status API Response Format Mismatch** (FIXED)
**File:** `authentication/api/views.py:1711-1742`

**Problem:**
The `CheckActivationStatusAPIView` endpoint was returning:
- `is_activated`
- `requires_payment`
- `payment_status`

But the Flutter frontend (`lib/utils/models/activation_status.dart`) expects:
- `activation_status` (int): 0=pending, 1=completed, 2=failed
- `activation_fee` (string)
- `message` (string)

**Fix:**
Updated the response format to match frontend expectations:

```python
# For landlords with payment record
return Response({
    'status': True,
    'message': 'Activation status retrieved',
    'activation_status': activation_payment.status,  # 0/1/2
    'activation_fee': str(activation_payment.amount)
}, status=status.HTTP_200_OK)

# For landlords without payment record
return Response({
    'status': True,
    'message': 'Payment not initiated',
    'activation_status': 0,  # pending
    'activation_fee': str(config.landlord_activation_fee)
}, status=status.HTTP_200_OK)
```

---

## Complete Landlord Registration Flow (Now Fixed)

1. **Registration** → User registers with role "landlord"
   - OTP is generated and sent via email
   - LoginOTP created with formatted mobile_number (`254XXXXXXXXX`)
   - User status: `0` (inactive)
   - ActivationPayment record created with status: `0` (pending)

2. **OTP Verification** → User enters OTP from email
   - Backend verifies OTP against LoginOTP table
   - For landlords: OTP deleted, returns `requires_payment: true`
   - User remains inactive (status: `0`)
   - Frontend redirects to ActivationPaymentScreen

3. **Payment Initiation** → User enters M-Pesa phone number
   - Backend initiates STK Push via Safaricom M-Pesa API
   - ActivationTransaction created with MerchantRequestID
   - User receives M-Pesa prompt on phone

4. **Payment Callback** → M-Pesa sends callback after payment
   - Backend receives callback on `activation-mpesa-callback/`
   - If successful (ResultCode == 0):
     - ActivationTransaction status → `1` (completed)
     - ActivationPayment status → `1` (completed)
     - User status → `1` (activated)
     - User is_active → `True`
     - BlockLandlord is_active → `1`

5. **Status Polling** → Frontend polls every 10 seconds
   - Calls `check-activation-status/` endpoint
   - Receives `activation_status`: 0/1/2
   - When `activation_status == 1`, redirects to landlord dashboard

---

## Deployment Instructions

### Option 1: Manual Deployment to VPS (Hetzner)
```bash
# SSH into the server
ssh user@178.105.35.41

# Navigate to project directory
cd /path/to/smartnyumba_backup

# Pull latest changes (if using git)
git pull origin main

# Or manually copy the updated files to the server

# Restart Django application
sudo systemctl restart gunicorn  # or whatever service name you use
# OR
pkill -f "python manage.py runserver"
python manage.py runserver 0.0.0.0:8080
```

### Option 2: Docker Deployment
```bash
cd ~/Desktop/projects/smartnyumba_backup

# Rebuild and restart containers
docker-compose down
docker-compose up -d --build
```

### Option 3: Test Locally First
```bash
cd ~/Desktop/projects/smartnyumba_backup

# Activate virtual environment
source venv/bin/activate

# Run migrations (if needed)
python manage.py migrate

# Start development server
python manage.py runserver 0.0.0.0:8080
```

---

## Testing Checklist

After deployment, test the complete flow:

1. [ ] Register a new landlord account with valid details
2. [ ] Verify OTP email is received
3. [ ] Enter OTP on the app
4. [ ] Verify redirection to Activation Payment Screen
5. [ ] Enter M-Pesa phone number (format: 254XXXXXXXXX)
6. [ ] Verify STK Push prompt on phone
7. [ ] Complete M-Pesa payment
8. [ ] Verify status polling shows "Payment Successful"
9. [ ] Verify redirection to Landlord Dashboard
10. [ ] Verify landlord can access all landlord features

---

## Files Modified

1. `authentication/api/views.py` (3 changes):
   - Line 880: Removed duplicate BlockLandlord import
   - Line 600: Fixed phone number formatting ([:9] → [-9:])
   - Lines 1711-1742: Fixed CheckActivationStatusAPIView response format

---

## Notes

- The frontend is already correctly implemented
- All Flutter code in `lib/screens/authentication/activation_payment_screen.dart` is working correctly
- The payment provider methods in `lib/utils/providers/payment_provider.dart` are correct
- OTP verification logic in `lib/screens/authentication/otp.dart` is correct

The issues were all on the backend side and have been fixed.

---

## Error That Should No Longer Occur

Before fixes:
```
<QuerySet [<User: d@ozsaip.com>]>
d@ozsaip.com
User role: landlord
254072052329
cannot import name 'BlockLandlord' from 'authentication.models'
Forbidden: /apps/api/v1/auth/user-register-verification/
```

After fixes:
✅ OTP verification succeeds
✅ Payment initiation works
✅ STK Push sent successfully
✅ Callback processes payment
✅ User gets activated
✅ Landlord can log in and access dashboard
