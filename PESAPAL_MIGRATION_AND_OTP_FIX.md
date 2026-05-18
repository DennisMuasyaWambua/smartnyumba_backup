# Pesapal Migration and OTP Fix - Complete Implementation Guide

## Summary of Changes

This document outlines all changes made to migrate from M-Pesa to Pesapal for ALL payment functionalities and fix the double OTP email issue.

## Issues Fixed

### 1. Double OTP Email Issue ✅

**Problem**: Landlords received TWO emails during registration:
1. OTP verification email
2. Credentials email with password

**Solution**: Removed the credentials email from landlord registration flow.

**File Modified**: `authentication/api/views.py` (Line 679-680)
- Removed `send_creation_email(email=email, password=password)` call
- Added comment explaining that password can be reset via forgot password flow
- Only OTP verification email is now sent

**Note**: Tenant registration was already correct - only sends OTP email.

### 2. Activation Payment Migrated to Pesapal ✅

**Changed**: Activation payment for landlords now uses Pesapal instead of M-Pesa STK Push.

**Benefits**:
- Supports both M-Pesa AND Card payments
- Better user experience with web checkout
- No M-Pesa API token expiration issues
- Unified payment gateway for entire system

## Backend Changes

### Files Modified

#### 1. `authentication/api/views.py`

**Line 676-680**: Removed duplicate credentials email from landlord registration
```python
# Note: Credentials email removed - only OTP email is sent
# Password can be reset if needed via forgot password flow
```

**Line 1424-1580**: Updated `InitiateActivationPaymentAPIView`
- Changed from M-Pesa STK Push to Pesapal checkout
- Now accepts `first_name` and `last_name` for billing
- Returns `redirect_url` and `order_tracking_id`
- User redirected to Pesapal checkout page

**Line 1687-1846**: Added `ActivationPesapalCallBackAPIView`
- Handles Pesapal IPN callbacks
- Queries Pesapal for authoritative payment status
- Activates user and landlord profile on successful payment
- Supports GET and POST IPN notifications

#### 2. `authentication/api/urls.py`

**Line 28**: Added new URL route
```python
path('activation-pesapal-callback/', views.ActivationPesapalCallBackAPIView.as_view(), name='activation-pesapal-callback'),
```

#### 3. `smartnyumba_system/settings.py`

**Line 258-259**: Added SITE_URL configuration
```python
# Site Configuration
SITE_URL = config('SITE_URL', default='http://localhost:8000')
```

#### 4. `.env`

**Line 95**: Updated Pesapal URL to sandbox
```env
PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
```

**Line 98-100**: Added SITE_URL configuration
```env
# Site Configuration
SITE_URL=https://api.smartnyumba.com
# For local development use: http://localhost:8000
```

### Existing Pesapal Integration

The system already has a complete Pesapal V3 integration:
- **File**: `utils/pesapal_service.py`
- **Features**:
  - OAuth2 token management with caching
  - IPN registration
  - Order submission
  - Transaction status queries
  - Error handling and logging

**Already Integrated For**:
- Rent payments (`tenant_services/views.py`)
- Service charge payments (`tenant_services/views.py`)

**Now Added**:
- Landlord activation payments ✅

## API Endpoint Changes

### Initiate Activation Payment

**Endpoint**: `POST /apps/api/v1/auth/initiate-activation-payment/`

**Request Body** (Updated):
```json
{
  "email": "landlord@example.com",
  "mobile_number": "254712345678",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response** (Updated):
```json
{
  "status": true,
  "message": "Please complete payment in the checkout page",
  "redirect_url": "https://cybqa.pesapal.com/iframe/PesapalIframe3/Index/?OrderTrackingId=abc123",
  "order_tracking_id": "abc123-def456-ghi789",
  "merchant_reference": "ACTIVATION-42-abc12345",
  "amount": 500.0
}
```

### New Callback Endpoint

**Endpoint**: `GET/POST /apps/api/v1/auth/activation-pesapal-callback/`

**Receives**: `OrderTrackingId` from Pesapal IPN

**Returns**:
```json
{
  "status": "ok",
  "message": "Activation payment successful. Account activated."
}
```

### Check Activation Status (Unchanged)

**Endpoint**: `POST /apps/api/v1/auth/check-activation-status/`

Works the same as before - checks if landlord account is activated.

## Flutter Frontend Integration

### Required Changes

Since the Flutter app files were not accessible in the current directory, here are the changes needed:

#### 1. Update Activation Payment Screen

Create/Update: `lib/screens/authentication/activation_payment_screen.dart`

```dart
import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:provider/provider.dart';

class ActivationPaymentScreen extends StatefulWidget {
  final String email;
  final String mobileNumber;
  final String firstName;
  final String lastName;

  const ActivationPaymentScreen({
    Key? key,
    required this.email,
    required this.mobileNumber,
    this.firstName = '',
    this.lastName = '',
  }) : super(key: key);

  @override
  State<ActivationPaymentScreen> createState() => _ActivationPaymentScreenState();
}

class _ActivationPaymentScreenState extends State<ActivationPaymentScreen> {
  bool isLoading = false;
  String? redirectUrl;
  String? orderTrackingId;

  @override
  void initState() {
    super.initState();
    initiatePayment();
  }

  Future<void> initiatePayment() async {
    setState(() {
      isLoading = true;
    });

    try {
      // Call your auth provider method
      final authProvider = Provider.of<AuthProvider>(context, listen: false);

      final response = await authProvider.initiateActivationPayment(
        email: widget.email,
        mobileNumber: widget.mobileNumber,
        firstName: widget.firstName,
        lastName: widget.lastName,
      );

      if (response['status'] == true) {
        setState(() {
          redirectUrl = response['redirect_url'];
          orderTrackingId = response['order_tracking_id'];
          isLoading = false;
        });
      } else {
        setState(() {
          isLoading = false;
        });
        showError(response['message'] ?? 'Payment initiation failed');
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });
      showError('An error occurred: $e');
    }
  }

  void showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return Scaffold(
        appBar: AppBar(title: Text('Activation Payment')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              CircularProgressIndicator(),
              SizedBox(height: 16),
              Text('Initiating payment...'),
            ],
          ),
        ),
      );
    }

    if (redirectUrl == null) {
      return Scaffold(
        appBar: AppBar(title: Text('Activation Payment')),
        body: Center(
          child: Text('Failed to load payment page'),
        ),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Complete Payment'),
        leading: IconButton(
          icon: Icon(Icons.close),
          onPressed: () {
            showDialog(
              context: context,
              builder: (context) => AlertDialog(
                title: Text('Cancel Payment?'),
                content: Text('Are you sure you want to cancel this payment?'),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text('No'),
                  ),
                  TextButton(
                    onPressed: () {
                      Navigator.pop(context);
                      Navigator.pop(context);
                    },
                    child: Text('Yes'),
                  ),
                ],
              ),
            );
          },
        ),
      ),
      body: WebView(
        initialUrl: redirectUrl!,
        javascriptMode: JavascriptMode.unrestricted,
        navigationDelegate: (NavigationRequest request) {
          // Check if payment is complete by monitoring URL changes
          if (request.url.contains('payment-complete') ||
              request.url.contains('success')) {
            // Poll activation status
            checkActivationStatus();
            return NavigationDecision.prevent;
          }
          return NavigationDecision.navigate;
        },
        onWebViewCreated: (WebViewController webViewController) {
          // Optional: Save controller for later use
        },
        onPageFinished: (String url) {
          // Optional: Handle page load completion
        },
      ),
    );
  }

  Future<void> checkActivationStatus() async {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Center(child: CircularProgressIndicator()),
    );

    try {
      final authProvider = Provider.of<AuthProvider>(context, listen: false);

      // Poll status for up to 30 seconds
      for (int i = 0; i < 10; i++) {
        await Future.delayed(Duration(seconds: 3));

        final statusResponse = await authProvider.checkActivationStatus(
          email: widget.email,
        );

        if (statusResponse['activation_status'] == 1) {
          Navigator.pop(context); // Close progress dialog
          Navigator.pop(context); // Close payment screen

          showDialog(
            context: context,
            builder: (context) => AlertDialog(
              title: Text('Success!'),
              content: Text('Your account has been activated. You can now log in.'),
              actions: [
                TextButton(
                  onPressed: () {
                    Navigator.pop(context);
                    Navigator.pushReplacementNamed(context, '/login');
                  },
                  child: Text('OK'),
                ),
              ],
            ),
          );
          return;
        }
      }

      // Timeout - payment not confirmed yet
      Navigator.pop(context);
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Payment Processing'),
          content: Text(
            'Your payment is being processed. You will be notified once it\'s confirmed. Please try logging in after a few minutes.',
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                Navigator.pop(context);
              },
              child: Text('OK'),
            ),
          ],
        ),
      );
    } catch (e) {
      Navigator.pop(context);
      showError('Failed to check activation status: $e');
    }
  }
}
```

#### 2. Update Auth Provider

Add to: `lib/utils/providers/auth_provider.dart`

```dart
Future<Map<String, dynamic>> initiateActivationPayment({
  required String email,
  required String mobileNumber,
  String firstName = '',
  String lastName = '',
}) async {
  try {
    final response = await http.post(
      Uri.parse('${Constants.baseUrl}/apps/api/v1/auth/initiate-activation-payment/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'mobile_number': mobileNumber,
        'first_name': firstName,
        'last_name': lastName,
      }),
    );

    return jsonDecode(response.body);
  } catch (e) {
    return {
      'status': false,
      'message': 'Network error: $e',
    };
  }
}

Future<Map<String, dynamic>> checkActivationStatus({
  required String email,
}) async {
  try {
    final response = await http.post(
      Uri.parse('${Constants.baseUrl}/apps/api/v1/auth/check-activation-status/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );

    return jsonDecode(response.body);
  } catch (e) {
    return {
      'activation_status': 0,
      'message': 'Network error: $e',
    };
  }
}
```

#### 3. Update pubspec.yaml

Add WebView dependency:
```yaml
dependencies:
  flutter:
    sdk: flutter
  webview_flutter: ^4.4.2  # Add this line
  # ... other dependencies
```

#### 4. Update OTP Verification Screen

After OTP verification success for landlords, redirect to activation payment:

```dart
// In OTP verification screen, after successful landlord OTP verification:
if (response['requires_payment'] == true) {
  Navigator.pushReplacement(
    context,
    MaterialPageRoute(
      builder: (context) => ActivationPaymentScreen(
        email: email,
        mobileNumber: mobileNumber,
        firstName: firstName,
        lastName: lastName,
      ),
    ),
  );
}
```

## Testing Instructions

### 1. Test Double OTP Fix

1. Register a new landlord account
2. Check email inbox
3. **Expected**: Only ONE email received (OTP verification email)
4. **Not Expected**: No credentials email

### 2. Test Activation Payment Flow

#### A. Complete Flow Test

1. **Register Landlord**:
   ```bash
   POST /apps/api/v1/auth/user-register/
   {
     "email": "test@example.com",
     "first_name": "John",
     "last_name": "Doe",
     "mobile_number": "0712345678",
     "id_number": "12345678",
     "role": "landlord",
     "phone_number": "0712345678",
     "location": "Nairobi",
     "block_number": "Test Estate",
     "approver": "admin@smartnyumba.com"
   }
   ```

2. **Verify OTP**:
   ```bash
   POST /apps/api/v1/auth/user-register-verification/
   {
     "email": "test@example.com",
     "otp": "1234"
   }
   ```
   **Expected**: `{"status": true, "requires_payment": true}`

3. **Initiate Payment**:
   ```bash
   POST /apps/api/v1/auth/initiate-activation-payment/
   {
     "email": "test@example.com",
     "mobile_number": "254712345678",
     "first_name": "John",
     "last_name": "Doe"
   }
   ```
   **Expected**: Returns `redirect_url` and `order_tracking_id`

4. **Complete Payment**:
   - Open the `redirect_url` in browser
   - Choose M-Pesa or Card payment
   - Use Pesapal test credentials:
     - Test Card: `4111 1111 1111 1111`, CVV: `123`, Any future date
     - Test M-Pesa: `254712345678`

5. **IPN Callback** (Automatic):
   - Pesapal will call: `/apps/api/v1/auth/activation-pesapal-callback/`
   - Backend will query Pesapal for status
   - If successful, user and landlord profile activated

6. **Verify Activation**:
   ```bash
   POST /apps/api/v1/auth/check-activation-status/
   {
     "email": "test@example.com"
   }
   ```
   **Expected**: `{"activation_status": 1}`

7. **Login**:
   ```bash
   POST /apps/api/v1/auth/landlord-login/
   {
     "email": "test@example.com",
     "password": "generated_password"
   }
   ```
   **Expected**: Login successful with landlord profile data

#### B. Database Verification

```sql
-- Check user activation
SELECT id, email, status, is_active FROM authentication_user WHERE email = 'test@example.com';
-- Expected: status=1, is_active=true

-- Check activation payment
SELECT id, user_id, amount, payment_mode, status, completed_at
FROM authentication_activationpayment WHERE user_id = X;
-- Expected: payment_mode='pesapal', status=1, completed_at=<timestamp>

-- Check transaction
SELECT id, MerchantRequestID, status, ResultCode, ResultDesc, MpesaReceiptNumber
FROM authentication_activationtransaction WHERE activation_payment_id = X;
-- Expected: status=1, ResultCode='0', MpesaReceiptNumber=<pesapal_confirmation>

-- Check landlord profile
SELECT id, user_id, email, is_active FROM block_landlord_blockllandlord WHERE user_id = X;
-- Expected: is_active=1
```

## Production Deployment

### 1. Environment Variables

Update production `.env`:
```env
# Change Pesapal to production
PESAPAL_CONSUMER_KEY=<your_production_key>
PESAPAL_CONSUMER_SECRET=<your_production_secret>
PESAPAL_BASE_URL=https://pay.pesapal.com/v3

# Update site URL
SITE_URL=https://api.smartnyumba.com
```

### 2. Register IPN on Pesapal Dashboard

1. Log in to Pesapal Dashboard: https://dashboard.pesapal.com
2. Go to IPN Settings
3. Register IPN URL: `https://api.smartnyumba.com/apps/api/v1/auth/activation-pesapal-callback/`
4. Set notification type: `GET`
5. Save and test

### 3. Deploy Backend

```bash
cd ~/Desktop/projects/smartnyumba_backup
git add .
git commit -m "Migrate activation payment to Pesapal and fix double OTP issue"
git push origin main

# Deploy to production (your deployment process)
```

### 4. Test in Production

Follow the testing instructions above using production environment.

## Migration from M-Pesa to Pesapal - Complete System

### Current Status

✅ **Rent Payments**: Already using Pesapal
✅ **Service Charge Payments**: Already using Pesapal
✅ **Activation Payments**: **NOW using Pesapal** (this update)

### Old M-Pesa Endpoints (Can be Deprecated)

The following M-Pesa endpoints are **NO LONGER USED** for activation:
- `ActivationMpesaCallBackAPIView` (Line 1584) - Keep for backwards compatibility
- M-Pesa STK Push code in old `InitiateActivationPaymentAPIView` - Replaced

**Recommendation**: Keep old M-Pesa callbacks for a transition period in case any payments are in-flight.

## Troubleshooting

### Issue: "Payment initiation failed"

**Check**:
1. Pesapal credentials in `.env` are correct
2. `PESAPAL_BASE_URL` is correct (sandbox vs production)
3. Backend logs for detailed error message
4. Test Pesapal token generation:
   ```python
   from utils.pesapal_service import get_oauth_token
   token = get_oauth_token()
   print(f"Token: {token}")
   ```

### Issue: "IPN not received"

**Check**:
1. IPN URL is registered on Pesapal dashboard
2. IPN URL is publicly accessible (test with `curl`)
3. No firewall blocking Pesapal IPs
4. Check Django logs for incoming IPN requests
5. Manually query transaction status:
   ```python
   from utils.pesapal_service import get_transaction_status
   status = get_transaction_status('order_tracking_id')
   print(status)
   ```

### Issue: "User not activated after payment"

**Check**:
1. IPN callback was received (check logs)
2. Transaction status in database
3. Activation payment status
4. Manually activate if needed:
   ```python
   from authentication.models import User
   from block_landlord.models import BlockLandlord

   user = User.objects.get(email='test@example.com')
   user.status = 1
   user.is_active = True
   user.save()

   landlord = BlockLandlord.objects.get(user=user)
   landlord.is_active = 1
   landlord.save()
   ```

### Issue: "Double OTP still received"

**Check**:
1. Changes to `authentication/api/views.py` were deployed
2. Correct view is being called (not cached version)
3. Check email logs to see which emails are sent
4. Verify `send_creation_email` is commented out at line 680

## Summary

### What Was Changed ✅

1. **Fixed double OTP email** - Only OTP verification email sent to landlords
2. **Migrated activation payment to Pesapal** - Supports M-Pesa and Card payments
3. **Added Pesapal callback handler** - Auto-activates accounts on payment success
4. **Added configuration** - SITE_URL for callback URLs
5. **Created Flutter integration guide** - Complete frontend implementation instructions

### What Needs to Be Done 🔲

1. **Implement Flutter changes** - Create/update activation payment screen
2. **Add WebView dependency** - Update pubspec.yaml
3. **Test complete flow** - Register → OTP → Payment → Activation → Login
4. **Update production .env** - Set production Pesapal credentials
5. **Register IPN** - Add callback URL to Pesapal dashboard
6. **Deploy** - Push changes to production

### Benefits 🎉

- **Unified payment gateway** - All payments now use Pesapal
- **Better UX** - Web checkout supports multiple payment methods
- **No token expiration** - No more M-Pesa token issues
- **Cleaner onboarding** - Only one email during registration
- **International ready** - Card payments work worldwide

---

**Implementation Date**: May 12, 2026
**Status**: Backend complete ✅ | Frontend pending 🔲
**Next Step**: Implement Flutter frontend changes
