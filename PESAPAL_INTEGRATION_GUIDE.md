# Pesapal V3 Integration - Backend Implementation Complete

## Summary

The Pesapal V3 payment gateway has been successfully integrated into the Smart Nyumba backend. This integration supports both M-Pesa and Card payments through a unified Pesapal checkout flow while preserving the existing M-Pesa STK Push and Stripe implementations.

## Files Modified/Created

### 1. Created Files
- **`utils/pesapal_service.py`** - Complete Pesapal V3 service layer with:
  - OAuth2 token management with caching
  - IPN registration
  - Order submission
  - Transaction status querying
  - Error handling and logging

### 2. Modified Files
- **`smartnyumba_system/settings.py`** - Added Pesapal configuration:
  ```python
  PESAPAL_CONSUMER_KEY = 'FHzwQRiIVVhTs4ZU9QM2V6Bem44KuBRa'
  PESAPAL_CONSUMER_SECRET = 'JwpABThwdS13EsCK0gnMwGLpmog='
  PESAPAL_BASE_URL = 'https://cybqa.pesapal.com/pesapalv3'  # Sandbox
  ```

- **`tenant_services/models.py`** - Added Pesapal fields to both models:
  - `serviceTransactions` model:
    - `payment_method` - CharField (20)
    - `confirmation_code` - CharField (100)
    - `pesapal_response` - TextField

  - `RentTransaction` model:
    - `payment_method` - CharField (20)
    - `confirmation_code` - CharField (100)
    - `pesapal_response` - TextField

- **`tenant_services/views.py`** - Added/Updated views:
  - Updated `PayServiceAPIView` - Added Pesapal payment flow
  - Updated `PayRentAPIView` - Added Pesapal payment flow
  - Created `PesapalIPNView` - IPN callback handler
  - Created `CheckPaymentStatusAPIView` - Payment status checker

- **`tenant_services/urls.py`** - Added new endpoints:
  - `/api/v1/tenant-services/pesapal/ipn/` - IPN callback
  - `/api/v1/tenant-services/check-payment-status/` - Status check

## How It Works

### Payment Flow

1. **Payment Initiation**:
   - User selects `pay_via: 'pesapal'` in payment request
   - Backend creates pending transaction record
   - Submits order to Pesapal with billing details
   - Returns `redirect_url` and `order_tracking_id` to mobile app
   - User completes payment in Pesapal checkout (M-Pesa or Card)

2. **IPN Callback**:
   - Pesapal sends IPN notification to `/pesapal/ipn/`
   - Backend queries Pesapal for authoritative status
   - Updates transaction status (0=pending, 1=completed, 2=failed)
   - Calculates 5% commission using existing `utils.commission`
   - Marks parent payment record as completed

3. **Status Checking**:
   - Mobile app can poll `/check-payment-status/`
   - Backend returns current status or queries Pesapal if pending
   - Automatically updates transaction if status changed

### Commission Handling

The existing 5% commission logic is preserved:
- Platform retains 5% commission
- Landlord receives 95% payout
- Commission stored in transaction fields:
  - `commission_amount`
  - `landlord_payout_amount`
  - `platform_earnings`

## Database Migration Required

Run the following commands to apply model changes:

```bash
cd ~/Desktop/projects/smartnyumba_backup
python manage.py makemigrations tenant_services
python manage.py migrate tenant_services
```

Expected migration will add:
- `payment_method` VARCHAR(20) NULL
- `confirmation_code` VARCHAR(100) NULL
- `pesapal_response` TEXT NULL

## API Endpoints

### 1. Pay Service (Updated)
**POST** `/apps/api/v1/tenant-services/pay-service/`

**Request:**
```json
{
  "email": "tenant@example.com",
  "mobile_number": "254712345678",
  "service_name": "Annual Service Charge",
  "pay_via": "pesapal"
}
```

**Response (Pesapal):**
```json
{
  "status": true,
  "message": "Please complete payment in the checkout page",
  "redirect_url": "https://cybqa.pesapal.com/iframe/PesapalIframe3/Index/?OrderTrackingId=abc123",
  "order_tracking_id": "abc123-def456-ghi789",
  "transaction_id": 42
}
```

### 2. Pay Rent (Updated)
**POST** `/apps/api/v1/tenant-services/pay-rent/`

**Request:**
```json
{
  "email": "tenant@example.com",
  "mobile_number": "254712345678",
  "month": 5,
  "year": 2026,
  "pay_via": "pesapal"
}
```

**Response (Pesapal):**
```json
{
  "status": true,
  "message": "Please complete payment in the checkout page",
  "redirect_url": "https://cybqa.pesapal.com/iframe/PesapalIframe3/Index/?OrderTrackingId=xyz789",
  "order_tracking_id": "xyz789-abc123-def456",
  "transaction_id": 85,
  "MerchantRequestID": "xyz789-abc123-def456"
}
```

### 3. Pesapal IPN Callback (New)
**GET/POST** `/apps/api/v1/tenant-services/pesapal/ipn/`

**Receives:**
- `OrderTrackingId` - from query params or POST body

**Returns:**
```json
{
  "status": "ok",
  "message": "IPN processed successfully"
}
```

### 4. Check Payment Status (New)
**POST** `/apps/api/v1/tenant-services/check-payment-status/`

**Request:**
```json
{
  "transaction_id": 42,
  "transaction_type": "rent"
}
```

OR

```json
{
  "order_tracking_id": "abc123-def456",
  "transaction_type": "service"
}
```

**Response:**
```json
{
  "transaction_id": 42,
  "status": 1,
  "status_text": "Completed",
  "payment_method": "pesapal",
  "confirmation_code": "PESAPAL123456",
  "amount": "5000.00",
  "month": 5,
  "year": 2026
}
```

## Environment Variables

Add to `.env` file or set in production environment:

```bash
# Pesapal Sandbox
PESAPAL_CONSUMER_KEY=FHzwQRiIVVhTs4ZU9QM2V6Bem44KuBRa
PESAPAL_CONSUMER_SECRET=JwpABThwdS13EsCK0gnMwGLpmog=
PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3

# For Production (when ready)
# PESAPAL_BASE_URL=https://pay.pesapal.com/v3
```

## Testing Instructions

### 1. Local Development Testing

Use **ngrok** to expose your local server:

```bash
# Start Django server
python manage.py runserver 8000

# In another terminal, start ngrok
ngrok http 8000

# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

Update IPN URL in Pesapal dashboard:
- Go to: https://developer.pesapal.com
- Navigate to: IPN Settings
- Register IPN: `https://abc123.ngrok.io/apps/api/v1/tenant-services/pesapal/ipn/`

### 2. Test Payment Flow

**Step 1: Initiate Payment**
```bash
curl -X POST https://your-domain.com/apps/api/v1/tenant-services/pay-rent/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "email": "tenant@example.com",
    "mobile_number": "254712345678",
    "month": 5,
    "year": 2026,
    "pay_via": "pesapal"
  }'
```

**Step 2: Complete Checkout**
- Open the `redirect_url` in browser
- Choose M-Pesa or Card payment
- Use test credentials:
  - Test Card: `4111 1111 1111 1111`
  - Test M-Pesa: `254712345678`

**Step 3: Verify IPN Received**
```bash
# Check Django logs
tail -f /path/to/django.log

# Should see:
# Processing Pesapal IPN for order_tracking_id: abc123...
# Transaction status from Pesapal: COMPLETED
# Rent transaction 85 marked as COMPLETED
```

**Step 4: Check Status**
```bash
curl -X POST https://your-domain.com/apps/api/v1/tenant-services/check-payment-status/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "transaction_id": 85,
    "transaction_type": "rent"
  }'
```

### 3. Database Verification

```sql
-- Check transaction record
SELECT id, status, MerchantRequestID, payment_method, confirmation_code, commission_amount
FROM rent_transactions
WHERE id = 85;

-- Expected result:
-- status: 1 (completed)
-- payment_method: 'pesapal'
-- confirmation_code: 'PESAPAL123456'
-- commission_amount: 250.00 (5% of 5000)
```

## Production Deployment Checklist

- [ ] Run database migrations (`python manage.py migrate`)
- [ ] Update `.env` with production Pesapal credentials
- [ ] Change `PESAPAL_BASE_URL` to production: `https://pay.pesapal.com/v3`
- [ ] Register production IPN URL on Pesapal dashboard
- [ ] Ensure IPN endpoint is HTTPS and publicly accessible
- [ ] Test end-to-end payment flow in production
- [ ] Monitor IPN callback logs for any failures
- [ ] Set up alerts for payment processing errors

## Security Considerations

1. **HTTPS Required**: IPN endpoint MUST be HTTPS in production
2. **Signature Validation**: TODO - Implement IPN signature verification in `pesapal_service.validate_ipn_signature()`
3. **Rate Limiting**: Consider adding rate limiting to IPN endpoint
4. **IP Whitelisting**: Optionally restrict IPN endpoint to Pesapal IPs
5. **Token Security**: OAuth tokens are cached securely using Django cache
6. **Idempotency**: IPN handler checks for duplicate IPNs to prevent double-processing

## Troubleshooting

### IPN Not Received

1. Check IPN URL is registered on Pesapal dashboard
2. Verify URL is publicly accessible (use `curl` to test)
3. Check Django logs for errors in `PesapalIPNView`
4. Ensure no firewall blocking Pesapal IPs

### Payment Not Updating

1. Check if IPN was received (check logs)
2. Query Pesapal status manually:
   ```python
   from utils import pesapal_service
   status = pesapal_service.get_transaction_status('order_tracking_id')
   print(status)
   ```
3. Verify `MerchantRequestID` in database matches `order_tracking_id`

### Token Errors (401 Unauthorized)

1. Clear Django cache:
   ```python
   from django.core.cache import cache
   cache.delete('pesapal_oauth_token')
   ```
2. Verify credentials in settings
3. Check Pesapal API status: https://status.pesapal.com

## Support & Documentation

- **Pesapal Docs**: https://developer.pesapal.com/docs
- **Pesapal Support**: support@pesapal.com
- **Smart Nyumba Backend**: ~/Desktop/projects/smartnyumba_backup

## Next Steps

1. **Run migrations** to add new database fields
2. **Test locally** using ngrok
3. **Implement Flutter integration** (see Flutter implementation guide)
4. **Deploy to staging** and test end-to-end
5. **Register production IPN** on Pesapal dashboard
6. **Go live** and monitor transactions

---

**Implementation Date**: May 2026
**Pesapal Version**: V3
**API Environment**: Sandbox (switch to Production when ready)
