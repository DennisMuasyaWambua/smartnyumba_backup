# Pesapal Setup Guide - Get Valid Credentials

## Current Issue

The Pesapal credentials in your `.env` file are **invalid or expired**:

```
Error: invalid_consumer_key_or_secret_provided
Status: 500
```

You need to get **valid credentials** from the Pesapal Developer Dashboard.

---

## Solution: Get Valid Pesapal Credentials

### Option 1: Use Pesapal Sandbox (For Testing)

#### Step 1: Create Pesapal Developer Account

1. **Go to Pesapal Developer Portal:**
   - **URL**: https://developer.pesapal.com/
   - Click **"Sign Up"** or **"Get Started"**

2. **Fill Registration Form:**
   - Business Name: `Smart Nyumba`
   - Email: Your email
   - Phone: Your phone number
   - Password: Create strong password

3. **Verify Email:**
   - Check your email inbox
   - Click verification link

4. **Log in to Dashboard:**
   - https://developer.pesapal.com/login

#### Step 2: Create Sandbox App

1. **Navigate to Apps Section:**
   - Dashboard → **"My Apps"** or **"Applications"**
   - Click **"Create App"** or **"Add Application"**

2. **Select Environment:**
   - Choose **"Sandbox"** (for testing)
   - OR **"Production"** (if you're ready to go live)

3. **Fill App Details:**
   - **App Name**: `Smart Nyumba Activation Payments`
   - **Description**: `Property management system - landlord activation fees`
   - **Callback URL**: Leave blank for now (we'll add IPN later)

4. **Submit Application:**
   - Click **"Create"** or **"Submit"**
   - App will be created instantly

#### Step 3: Get Consumer Key and Secret

1. **View App Details:**
   - Click on your newly created app
   - You should see app credentials

2. **Copy Credentials:**
   - **Consumer Key**: Long alphanumeric string (e.g., `qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW`)
   - **Consumer Secret**: Encoded secret (e.g., `osGQ364R49cXKeOYSpaOnT++rHs=`)

   **Important**: These are just examples! Use YOUR actual credentials from the dashboard.

3. **Save Credentials Securely:**
   - Don't share these publicly
   - Store in password manager if needed

#### Step 4: Register IPN (Instant Payment Notification) URL

1. **Navigate to IPN Settings:**
   - Dashboard → **"IPN Settings"** or **"Webhooks"**
   - Click **"Register IPN"** or **"Add IPN URL"**

2. **Enter IPN Details:**
   - **IPN URL**: `https://api.smartnyumba.com/apps/api/v1/auth/activation-pesapal-callback/`
   - **Notification Type**: Select **"GET"** or **"POST"** (both work)
   - If you're testing locally with ngrok, use: `https://your-ngrok-url.ngrok.io/apps/api/v1/auth/activation-pesapal-callback/`

3. **Save IPN Configuration:**
   - Click **"Register"** or **"Save"**
   - IPN is now active

#### Step 5: Update .env File

1. **Open .env file:**
   ```bash
   nano ~/Desktop/projects/smartnyumba_backup/.env
   ```

2. **Update Pesapal credentials:**
   ```env
   # Pesapal Configuration
   PESAPAL_CONSUMER_KEY=YOUR_ACTUAL_CONSUMER_KEY_HERE
   PESAPAL_CONSUMER_SECRET=YOUR_ACTUAL_CONSUMER_SECRET_HERE
   PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
   ```

   **Example (use your real credentials):**
   ```env
   PESAPAL_CONSUMER_KEY=qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW
   PESAPAL_CONSUMER_SECRET=osGQ364R49cXKeOYSpaOnT++rHs=
   PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
   ```

3. **Save file:**
   - Press `Ctrl+X`, then `Y`, then `Enter`

#### Step 6: Restart Django Server

```bash
cd ~/Desktop/projects/smartnyumba_backup

# Stop old server
pkill -f "python.*manage.py runserver"

# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -name "*.pyc" -delete

# Start server with new credentials
python3 manage.py runserver 0.0.0.0:8000
```

#### Step 7: Test Payment

1. **Try activation payment again** from your Flutter app
2. **Should now work** and show Pesapal checkout page

---

### Option 2: Use Production Credentials (For Live Payments)

If you already have a Pesapal business account and want to accept real payments:

#### Step 1: Log in to Production Dashboard

- **URL**: https://www.pesapal.com/dashboard
- Use your business account credentials

#### Step 2: Get Production Credentials

1. Navigate to **"API Integration"** or **"Developer"** section
2. Create production app or view existing credentials
3. Copy **Consumer Key** and **Consumer Secret**

#### Step 3: Update .env for Production

```env
# Pesapal Configuration - PRODUCTION
PESAPAL_CONSUMER_KEY=your_production_consumer_key
PESAPAL_CONSUMER_SECRET=your_production_consumer_secret
PESAPAL_BASE_URL=https://pay.pesapal.com/v3

# Site Configuration - PRODUCTION
SITE_URL=https://api.smartnyumba.com
```

#### Step 4: Register Production IPN

- IPN URL: `https://api.smartnyumba.com/apps/api/v1/auth/activation-pesapal-callback/`
- This MUST be a publicly accessible HTTPS URL

---

## Testing Locally with ngrok (Optional)

If you want to test with real Pesapal sandbox but your server is running locally:

### Step 1: Install ngrok

```bash
# Download ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar -xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/
```

### Step 2: Get ngrok Auth Token

1. Sign up at https://ngrok.com
2. Copy your auth token from dashboard
3. Configure ngrok:
   ```bash
   ngrok config add-authtoken YOUR_NGROK_TOKEN
   ```

### Step 3: Expose Local Server

```bash
# Start Django server
python3 manage.py runserver 0.0.0.0:8000

# In another terminal, start ngrok
ngrok http 8000
```

You'll see output like:
```
Forwarding https://abc123.ngrok.io -> http://localhost:8000
```

### Step 4: Update .env with ngrok URL

```env
SITE_URL=https://abc123.ngrok.io
```

### Step 5: Register ngrok IPN URL in Pesapal

- IPN URL: `https://abc123.ngrok.io/apps/api/v1/auth/activation-pesapal-callback/`

Now Pesapal can send callbacks to your local server!

---

## Verification

### Test Token Generation

After updating credentials, test if they work:

```bash
cd ~/Desktop/projects/smartnyumba_backup
python3 manage.py shell
```

```python
from utils.pesapal_service import get_oauth_token

# Test token generation
token = get_oauth_token()

if token:
    print(f"✓ SUCCESS! Token: {token[:30]}...")
else:
    print("✗ FAILED! Check your credentials.")
```

**Expected Output:**
```
✓ SUCCESS! Token: eyJhbGciOiJIUzI1NiIsInR5cCI6...
```

**If it fails, you'll see:**
```
No token in Pesapal response: {'error': {...}}
✗ FAILED! Check your credentials.
```

### Test Complete Payment Flow

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

**Expected Response (Success):**
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

---

## Common Issues

### Issue 1: "invalid_consumer_key_or_secret_provided"

**Cause**: Wrong credentials in `.env`

**Solution**:
1. Double-check credentials from Pesapal dashboard
2. Make sure no extra spaces or quotes
3. Consumer Secret should end with `=` (base64 encoded)
4. Restart Django after updating

### Issue 2: "IPN not received"

**Cause**: IPN URL not registered or unreachable

**Solution**:
1. Register IPN URL in Pesapal dashboard
2. Make sure URL is publicly accessible (use ngrok for local testing)
3. Check Django logs for incoming requests
4. Verify no firewall blocking Pesapal IPs

### Issue 3: "Token expires quickly"

**Cause**: Normal behavior - Pesapal tokens expire

**Solution**:
- Token caching is already implemented in `utils/pesapal_service.py`
- Token is refreshed automatically when expired
- No action needed

### Issue 4: "Sandbox vs Production confusion"

**Solution**:
- **Sandbox**: `https://cybqa.pesapal.com/pesapalv3` - For testing, no real money
- **Production**: `https://pay.pesapal.com/v3` - Real payments, requires business verification

---

## Quick Fix Checklist

- [ ] Create Pesapal developer account
- [ ] Create sandbox app in dashboard
- [ ] Copy Consumer Key and Secret
- [ ] Update `.env` file with new credentials
- [ ] Register IPN URL in Pesapal dashboard
- [ ] Restart Django server
- [ ] Test token generation
- [ ] Test activation payment from app

---

## Sample Valid Credentials Format

```env
# These are EXAMPLES - use YOUR credentials from Pesapal dashboard
PESAPAL_CONSUMER_KEY=qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW
PESAPAL_CONSUMER_SECRET=osGQ364R49cXKeOYSpaOnT++rHs=
PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
```

**Invalid format (will fail):**
```env
# DON'T DO THIS:
PESAPAL_CONSUMER_KEY="qkio1BGGYAXTu2JOfm7XSXNruoZsrqEW"  # ✗ No quotes
PESAPAL_CONSUMER_SECRET='osGQ364R49cXKeOYSpaOnT++rHs='    # ✗ No quotes
PESAPAL_CONSUMER_KEY=                                      # ✗ Empty
```

---

## Support

- **Pesapal Docs**: https://developer.pesapal.com/how-to-integrate
- **Pesapal Support**: support@pesapal.com
- **Pesapal Dashboard**: https://developer.pesapal.com/login

---

**Next Step**: Get valid credentials from Pesapal dashboard and update your `.env` file!
