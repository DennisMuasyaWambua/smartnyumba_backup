# OTP and Activation Payment Fix Summary

## Issues Fixed

### 1. OTP "Account Already Activated" Error

**Root Cause:**
- User accounts from previous testing attempts remain in the database
- When landlord registers with an existing email, the old user record (which may have been activated) causes the "already activated" error

**Fix Applied:**
- Line 607 in `authentication/api/views.py`: Explicitly set `user.is_active = False` when creating landlord users
- This ensures new landlord registrations start with inactive status

**Testing Instructions:**
1. **Delete existing test users first** before registering a new landlord
2. Use Django admin or the delete_users_v2.py script to remove test accounts
3. Register with a fresh email address
4. The OTP flow should now work correctly:
   - Register landlord → OTP sent
   - Enter OTP → Success with "requires_payment: true"
   - User remains inactive until payment

### 2. STK Push Not Triggered

**Status:** The backend code is correct and functional

**How It Works:**
1. After OTP verification, Flutter app redirects to `ActivationPaymentScreen`
2. User enters M-Pesa phone number (format: 254XXXXXXXXX)
3. Click "Pay Activation Fee"
4. App calls `initiateActivationPayment(email, phone)`
5. Backend sends STK push via `InitiateActivationPaymentAPIView` (line 1410)
6. User completes payment on phone
7. M-Pesa calls `ActivationMpesaCallBackAPIView` (line 1564)
8. User and landlord profile get activated (line 1625-1635)

**Why STK Push Might Not Work:**
- **Account already activated:** If user.status == 1, API returns error (line 1446)
- **Invalid phone format:** Phone must be 254XXXXXXXXX (12 digits total)
- **M-Pesa sandbox issues:** Ensure correct M-Pesa credentials in settings
- **Network/firewall:** Callback URL must be accessible to Safaricom

### 3. Changes Made

**File:** `authentication/api/views.py`

**Line 607-609:** Set user as inactive for landlords
```python
user.is_active = False  # User inactive until OTP verified (and payment for landlords)
user.status = 0
user.save()
```

**Line 658-669:** Generate and send OTP to landlord email
```python
# Generate OTP for landlord verification (just like tenants)
otp = random.randint(1111, 9999)
email_response = send_otp_message(email=email, otp=otp)

if not email_response:
    return Response({
        'status': False,
        'message': 'Error sending OTP'
    }, status=status.HTTP_400_BAD_REQUEST)

# Store OTP for verification
LoginOTP.objects.create(mobile_number=mobile_number, otp=otp)

# Also send credentials email
send_creation_email(email=email, password=password)
```

**Line 820-900:** Handle landlord OTP verification differently from tenants
```python
# Get user's role
user_role = user.role.short_name if user.role else None

# Check if already activated
if user.is_active:
    return Response({
        'status': False,
        'message':'Account has already been activated'
    }, status=status.HTTP_403_FORBIDDEN)

# ... OTP verification ...

# Handle verification based on role
if user_role == 'tenant':
    # TENANT: Activate immediately after OTP verification
    # ... tenant activation code ...

elif user_role == 'landlord':
    # LANDLORD: OTP verified but NOT activated yet (needs payment)
    login_otp.delete()

    return Response({
        'status': True,
        'message': 'OTP verified. Please complete payment to activate your account.',
        'requires_payment': True
    }, status=status.HTTP_200_OK)
```

## Testing Workflow

### Complete Landlord Registration Flow:

1. **Register Landlord**
   ```
   POST /apps/api/v1/auth/user-register/
   {
     "email": "landlord@test.com",
     "first_name": "Test",
     "last_name": "Landlord",
     "mobile_number": "0712345678",
     "id_number": "12345678",
     "role": "landlord",
     "phone_number": "0712345678",
     "location": "Nairobi",
     "block_number": "Test Estate",
     "approver": "admin@smartnyumba.com"
   }
   ```
   **Expected:** OTP sent to email, user created with is_active=False

2. **Verify OTP**
   ```
   POST /apps/api/v1/auth/user-register-verification/
   {
     "email": "landlord@test.com",
     "otp": "1234"
   }
   ```
   **Expected:** `{"status": true, "requires_payment": true}`
   **User Status:** is_active=False, status=0

3. **Initiate Payment**
   ```
   POST /apps/api/v1/auth/initiate-activation-payment/
   {
     "email": "landlord@test.com",
     "mobile_number": "254712345678"
   }
   ```
   **Expected:** STK push sent to phone, transaction record created
   **Check Phone:** M-Pesa payment prompt for KES 500

4. **Complete Payment**
   - User enters M-Pesa PIN on phone
   - M-Pesa calls activation-mpesa-callback/
   - Backend activates user and landlord profile

5. **Check Status**
   ```
   POST /apps/api/v1/auth/check-activation-status/
   {
     "email": "landlord@test.com"
   }
   ```
   **Expected:** `{"activation_status": 1}` after payment

## Troubleshooting

### "Account already activated" Error
- **Solution:** Delete the user from database and register with fresh email
- **Command:** Use delete_users_v2.py or Django admin to remove user

### STK Push Not Received
1. Check phone number format: 254XXXXXXXXX (12 digits)
2. Verify M-Pesa sandbox credentials in Django settings
3. Check user.status != 1 (not already activated)
4. Review M-Pesa API logs for errors
5. Ensure callback URL is accessible

### Payment Completed But User Not Activated
1. Check activation-mpesa-callback/ logs
2. Verify transaction record exists in ActivationTransaction table
3. Check ActivationPayment.status == 1
4. Manually activate if needed:
   ```python
   user.status = 1
   user.is_active = True
   user.save()
   ```

## Database Cleanup Commands

### Delete Test Landlord
```python
from authentication.models import User
from block_landlord.models import BlockLandlord

email = "landlord@test.com"
user = User.objects.filter(email=email).first()
if user:
    user.delete()  # Cascades to landlord profile
```

### Check Landlord Status
```python
from authentication.models import User
from block_landlord.models import BlockLandlord

user = User.objects.filter(email="landlord@test.com").first()
print(f"User Active: {user.is_active}, Status: {user.status}")

landlord = BlockLandlord.objects.filter(user=user).first()
print(f"Landlord Active: {landlord.is_active}")
```

---

**Status:** Backend fixes complete ✅
**Next Steps:** Test with fresh email addresses after clearing old test data
