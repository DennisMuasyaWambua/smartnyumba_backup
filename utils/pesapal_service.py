"""
Pesapal V3 Payment Gateway Integration Service

This module encapsulates all interactions with the Pesapal V3 API including:
- OAuth2 token management with caching
- IPN registration
- Order submission
- Transaction status queries

All API calls use proper error handling, logging, and timeout management.
"""

import logging
import requests
from typing import Dict, Optional, Any
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import APIException

logger = logging.getLogger(__name__)

# Pesapal API endpoints
# Note: All V3 endpoints require '/api' prefix
PESAPAL_TOKEN_ENDPOINT = '/api/Auth/RequestToken'
PESAPAL_IPN_REGISTER_ENDPOINT = '/api/URLSetup/RegisterIPN'
PESAPAL_SUBMIT_ORDER_ENDPOINT = '/api/Transactions/SubmitOrderRequest'
PESAPAL_TRANSACTION_STATUS_ENDPOINT = '/api/Transactions/GetTransactionStatus'

# Cache keys
PESAPAL_TOKEN_CACHE_KEY = 'pesapal_oauth_token'
PESAPAL_IPN_ID_CACHE_KEY = 'pesapal_ipn_id'

# Request timeout in seconds
REQUEST_TIMEOUT = 30


class PesapalException(APIException):
    """Custom exception for Pesapal API errors"""
    status_code = 500
    default_detail = 'Pesapal payment service error occurred.'
    default_code = 'pesapal_error'


def get_oauth_token() -> str:
    """
    Request an OAuth2 token from Pesapal and cache it.

    Tokens are cached with safe expiry (300 seconds or token_expires - 30 seconds).
    If a valid cached token exists, it is returned immediately.

    Returns:
        str: Valid OAuth2 bearer token

    Raises:
        PesapalException: If token request fails
    """
    # Check cache first
    cached_token = cache.get(PESAPAL_TOKEN_CACHE_KEY)
    if cached_token:
        logger.debug("Using cached Pesapal OAuth token")
        return cached_token

    # Request new token
    url = f"{settings.PESAPAL_BASE_URL}{PESAPAL_TOKEN_ENDPOINT}"
    print(f"Requesting new Pesapal OAuth token from: {url}")  # Debug print for endpoint URL
    logging.info(f"Requesting new Pesapal OAuth token from: {url}")
    payload = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }
    print(f"Pesapal OAuth payload: {payload}")  # Debug print for payload
    logging.info(f"Pesapal OAuth payload: {payload}")
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        logger.info(f"Requesting new Pesapal OAuth token from: {url}")
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )

        print(f"Pesapal OAuth response: {response}")  # Debug print for response
        logging.info(f"Pesapal OAuth response status: {response.status_code}")
        logger.debug(f"Pesapal OAuth response headers: {response.headers}")

        response.raise_for_status()

        # Log raw response text before parsing
        response_text = response.text
        logger.debug(f"Pesapal OAuth raw response: {response_text[:500]}")  # First 500 chars

        try:
            data = response.json()
            print(f"Pesapal OAuth response JSON: {data}")  # Debug print for parsed JSON
            logging.info(f"Pesapal OAuth response JSON: {data}")
        except requests.exceptions.JSONDecodeError as json_err:
            logger.error(f"Failed to parse Pesapal response as JSON. Status: {response.status_code}, Response: {response_text[:1000]}")
            raise PesapalException(f"Invalid JSON response from Pesapal (Status {response.status_code}). Check API endpoint and credentials.")

        token = data.get('token')
        expires_in = data.get('expiryDate')  # Pesapal returns expiryDate in seconds or ISO format

        if not token:
            logger.error(f"No token in Pesapal response: {data}")
            raise PesapalException("Failed to obtain OAuth token from Pesapal")

        # Cache token with safe expiry (default 300 seconds or parsed expiry minus 30 seconds)
        cache_timeout = 300
        if expires_in:
            try:
                # If expires_in is integer seconds
                if isinstance(expires_in, int):
                    cache_timeout = max(expires_in - 30, 60)
                # If expires_in is string, try parsing as seconds
                elif isinstance(expires_in, str) and expires_in.isdigit():
                    cache_timeout = max(int(expires_in) - 30, 60)
            except (ValueError, TypeError):
                pass

        cache.set(PESAPAL_TOKEN_CACHE_KEY, token, cache_timeout)
        logger.info(f"Pesapal OAuth token cached for {cache_timeout} seconds")

        return token

    except requests.exceptions.RequestException as e:
        logger.error(f"Pesapal OAuth token request failed: {str(e)}")
        # Log additional details if response is available
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}, Body: {e.response.text[:1000]}")
        raise PesapalException(f"Failed to connect to Pesapal: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Pesapal token response format: {str(e)}")
        raise PesapalException("Invalid response from Pesapal token service")


def register_ipn(ipn_url: str, ipn_notification_type: str = "GET") -> str:
    """
    Register an IPN (Instant Payment Notification) URL with Pesapal.

    This function is idempotent - if the IPN URL is already registered,
    it returns the existing ipn_id from cache or re-registers if necessary.

    Args:
        ipn_url: Publicly accessible HTTPS URL for IPN callbacks
        ipn_notification_type: HTTP method Pesapal will use (GET or POST)

    Returns:
        str: IPN ID returned by Pesapal

    Raises:
        PesapalException: If IPN registration fails
    """
    # Check cache for existing IPN ID
    cached_ipn_id = cache.get(PESAPAL_IPN_ID_CACHE_KEY)
    if cached_ipn_id:
        logger.debug(f"Using cached Pesapal IPN ID: {cached_ipn_id}")
        return cached_ipn_id

    token = get_oauth_token()
    url = f"{settings.PESAPAL_BASE_URL}{PESAPAL_IPN_REGISTER_ENDPOINT}"

    payload = {
        "url": ipn_url,
        "ipn_notification_type": ipn_notification_type
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        logger.info(f"Registering IPN URL with Pesapal: {ipn_url}")
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()
        ipn_id = data.get('ipn_id')

        if not ipn_id:
            # Check if error indicates IPN already exists
            error_message = data.get('error', {}).get('message', '')
            if 'already registered' in error_message.lower():
                logger.warning(f"IPN URL already registered: {error_message}")
                # Extract ipn_id from error message if available or return a placeholder
                # For now, we'll need to handle this case - Pesapal should return the existing ID
                ipn_id = data.get('error', {}).get('ipn_id')
                if ipn_id:
                    cache.set(PESAPAL_IPN_ID_CACHE_KEY, ipn_id, 86400)  # Cache for 24 hours
                    return ipn_id

            logger.error(f"No ipn_id in Pesapal response: {data}")
            raise PesapalException("Failed to register IPN with Pesapal")

        # Cache IPN ID for 24 hours
        cache.set(PESAPAL_IPN_ID_CACHE_KEY, ipn_id, 86400)
        logger.info(f"IPN registered successfully. IPN ID: {ipn_id}")

        return ipn_id

    except requests.exceptions.RequestException as e:
        logger.error(f"Pesapal IPN registration failed: {str(e)}")
        raise PesapalException(f"Failed to register IPN with Pesapal: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Pesapal IPN registration response: {str(e)}")
        raise PesapalException("Invalid response from Pesapal IPN service")


def submit_order(
    merchant_reference: str,
    amount: Decimal,
    description: str,
    callback_url: str,
    currency: str = 'KES',
    metadata: Optional[Dict[str, Any]] = None,
    billing_address: Optional[Dict[str, str]] = None,
    ipn_url: Optional[str] = None
) -> Dict[str, str]:
    """
    Submit an order to Pesapal for payment processing.

    Args:
        merchant_reference: Unique reference for this transaction (internal transaction ID)
        amount: Total amount to charge (including commission)
        description: Payment description (e.g., "Rent payment for Tenant X, Property Y")
        callback_url: URL where user is redirected after payment (can be deep link)
        currency: Currency code (default: KES)
        metadata: Optional metadata dictionary
        billing_address: Optional billing address details
        ipn_url: Optional HTTPS URL for IPN notifications (defaults to callback_url if not provided)

    Returns:
        dict: {
            'redirect_url': URL to redirect user for payment,
            'order_tracking_id': Pesapal order tracking ID,
            'merchant_reference': Echo of merchant reference,
            'status': Order submission status
        }

    Raises:
        PesapalException: If order submission fails
    """
    token = get_oauth_token()
    url = f"{settings.PESAPAL_BASE_URL}{PESAPAL_SUBMIT_ORDER_ENDPOINT}"

    # Ensure amount is properly formatted as string with 2 decimal places
    amount_str = f"{amount:.2f}"

    # Build billing address - Pesapal V3 requires at least some billing info
    if not billing_address:
        billing_address = {
            "phone_number": "",  # Should be populated from tenant data in view
            "email_address": "",  # Should be populated from tenant data in view
            "country_code": "KE",
            "first_name": "",
            "middle_name": "",
            "last_name": "",
            "line_1": "",
            "line_2": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "zip_code": ""
        }

    # Use ipn_url if provided, otherwise fall back to callback_url
    # IPN URL must be a publicly accessible HTTPS URL, not a deep link
    notification_url = ipn_url if ipn_url else callback_url

    payload = {
        "id": merchant_reference,  # Merchant reference / internal transaction ID
        "currency": currency,
        "amount": amount_str,
        "description": description,
        "callback_url": callback_url,
        "notification_id": register_ipn(notification_url),  # Register IPN and get ID
        "billing_address": billing_address
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        logger.info(f"Submitting order to Pesapal: merchant_ref={merchant_reference}, amount={amount_str}")
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        logging.info(f"Pesapal order submission response: {data}")
        # Pesapal V3 returns order_tracking_id and redirect_url
        order_tracking_id = data.get('order_tracking_id')
        redirect_url = data.get('redirect_url')

        if not order_tracking_id or not redirect_url:
            logger.error(f"Missing required fields in Pesapal response: {data}")
            raise PesapalException("Invalid order submission response from Pesapal")

        result = {
            'redirect_url': redirect_url,
            'order_tracking_id': order_tracking_id,
            'merchant_reference': data.get('merchant_reference', merchant_reference),
            'status': data.get('status', 'pending')
        }

        logger.info(f"Order submitted successfully: order_tracking_id={order_tracking_id}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Pesapal order submission failed: {str(e)}")
        raise PesapalException(f"Failed to submit order to Pesapal: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Pesapal order submission response: {str(e)}")
        raise PesapalException("Invalid response from Pesapal order service")


def get_transaction_status(order_tracking_id: str) -> Dict[str, Any]:
    """
    Query Pesapal for the current status of a transaction.

    Args:
        order_tracking_id: The order tracking ID returned by submit_order

    Returns:
        dict: {
            'status': Normalized status string ('COMPLETED', 'FAILED', 'PENDING', 'CANCELLED'),
            'payment_status_description': Human-readable status,
            'amount': Transaction amount,
            'currency': Currency code,
            'payment_method': Payment method used,
            'created_date': Transaction creation date,
            'confirmation_code': Pesapal confirmation code,
            'raw_response': Full response from Pesapal
        }

    Raises:
        PesapalException: If status query fails
    """
    token = get_oauth_token()
    url = f"{settings.PESAPAL_BASE_URL}{PESAPAL_TRANSACTION_STATUS_ENDPOINT}"

    params = {
        'orderTrackingId': order_tracking_id
    }

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }

    try:
        logger.info(f"Querying transaction status: order_tracking_id={order_tracking_id}")
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        data = response.json()

        # Extract and normalize status
        payment_status_code = data.get('payment_status_code', 0)
        payment_status_description = data.get('payment_status_description', 'Unknown')

        # Normalize status based on Pesapal status codes
        # Pesapal V3 status codes:
        # 0 = Invalid, 1 = Completed, 2 = Failed, 3 = Reversed
        status_mapping = {
            0: 'PENDING',
            1: 'COMPLETED',
            2: 'FAILED',
            3: 'CANCELLED'
        }

        normalized_status = status_mapping.get(payment_status_code, 'PENDING')

        result = {
            'status': normalized_status,
            'payment_status_description': payment_status_description,
            'payment_status_code': payment_status_code,
            'amount': data.get('amount'),
            'currency': data.get('currency'),
            'payment_method': data.get('payment_method'),
            'created_date': data.get('created_date'),
            'confirmation_code': data.get('confirmation_code'),
            'merchant_reference': data.get('merchant_reference'),
            'raw_response': data
        }

        logger.info(f"Transaction status retrieved: {normalized_status} ({payment_status_description})")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Pesapal status query failed: {str(e)}")
        raise PesapalException(f"Failed to query transaction status: {str(e)}")
    except (KeyError, ValueError) as e:
        logger.error(f"Invalid Pesapal status response: {str(e)}")
        raise PesapalException("Invalid response from Pesapal status service")


def validate_ipn_signature(payload: Dict[str, Any], signature: str) -> bool:
    """
    Validate IPN callback signature from Pesapal.

    TODO: Implement signature validation per Pesapal V3 documentation.
    Pesapal may provide HMAC signature in headers or payload.
    Use PESAPAL_CONSUMER_SECRET as signing key.

    Args:
        payload: IPN payload data
        signature: Signature from Pesapal headers

    Returns:
        bool: True if signature is valid, False otherwise
    """
    # Placeholder for signature validation
    # Consult Pesapal V3 docs for exact signature algorithm
    logger.warning("IPN signature validation not implemented - add per Pesapal V3 docs")
    return True  # TODO: Implement actual validation
