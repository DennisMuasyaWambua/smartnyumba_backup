import json
import os
import re
import datetime
import requests
import base64
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from authentication.models import Tenant
from properties.models import Property, PropertyBlock, ServiceChargeCollection
from tenant_services.models import serviceTransactions, services, RentPayment, RentTransaction
from tenant_services.serializers import AllTRansactionsSerializer, PayServiceSerializer, ServiceFeeAmountSerializer, TransactionCheckSerializer, TransactionSerializer, PayRentSerializer, RentPaymentSerializer, RentTransactionSerializer
from utils.api_auth import encrypt_initiator_password_with_certificate_file, get_access_token, get_b2c_access_token

from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone

import stripe

from utils.genRef import generate_B2c_account_reference
from utils import pesapal_service

User = get_user_model()

class ServiceFeeAmountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user
            user = Tenant.objects.filter(email=current_user).first()
            amount = user.PropertyBlock.service_charge
            
            return Response({
                'status': True,
                'amount': amount
            })

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Cannot get the details!'
            }, status=status.HTTP_400_BAD_REQUEST)

class PayServiceAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PayServiceSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided!',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_roles = ['tenant']
            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')
            mobile_number = request.data.get('mobile_number')
            service_name = request.data.get('service_name')
            pay_via = request.data.get('pay_via').lower()

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.fullmatch(email_regex, email):
                return Response({
                    'status': False,
                    'message': 'Provide a valid email'
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({
                    'status': False,
                    'message': 'Tenant with this email does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

            if mobile_number:
                mobile_number = user.mobile_number[-9:]
                mobile_number = f'254{mobile_number}'

            if len(mobile_number) > 13:
                return Response({
                    'status': False,
                    'message': 'Number too long'
                }, status=status.HTTP_400_BAD_REQUEST)

            tenant = Tenant.objects.filter(email=email).first()
            service_charge = Decimal(tenant.PropertyBlock.service_charge)
            annual_service_charge = Decimal(tenant.PropertyBlock.annual_service_charge)


            # MPesa Payment Logic
            if pay_via == 'mpesa':
                access_token = get_access_token()
                headers = {
                    'Content-Type': 'application/json',
                    "Authorization": f'Bearer {access_token}'
                }
                endpoint = settings.SAFARICOM_STK_PUSH
                Business_short_code = settings.BUSINESS_SHORT_CODE
                partyB = settings.TILLNUMBER
                timestamp = f"{datetime.datetime.now():%Y%m%d%H%M%S}"
                pass_key = settings.SAFARICOM_PASS_KEY
                message = f'{Business_short_code}{pass_key}{timestamp}'
                password = base64.b64encode(message.encode('ascii')).decode('ascii')
                CallBackURL = 'https://api.smartnyumba.com/apps/api/v1/tenant-services/mpesa-callback/'


                payload = {
                    "BusinessShortCode": Business_short_code,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerBuyGoodsOnline",
                    "Amount": int(service_charge),
                    "PartyA": mobile_number,
                    "PartyB": partyB,
                    "PhoneNumber": mobile_number,
                    "CallBackURL": CallBackURL,
                    "AccountReference": "SmartNyumba",
                    "TransactionDesc": "Payment of Service"
                }


                response = requests.post(endpoint, json=payload, headers=headers)
                json_response = json.loads(response.text)

                print(json_response)


                if response.status_code == 200:
                    service_instance, created = services.objects.get_or_create(
                        user=user,
                        defaults={
                            'block': tenant.PropertyBlock.block,
                            'service_name': service_name,
                            'amount': service_charge,
                            'balance_service_charge': annual_service_charge-service_charge,
                            'payment_mode': pay_via
                        }
                    )

                    if not created:
                        # Service already exists, update balance
                        service_instance.balance_service_charge -= service_charge
                        service_instance.save()

                    if service_instance.balance_service_charge == 0:
                        serviceTransactionStatus = 1
                    else:
                        serviceTransactionStatus = 0

                    ServiceTrans = serviceTransactions(
                        service_instance=service_instance,
                        status=serviceTransactionStatus,
                        MerchantRequestID=json_response.get('MerchantRequestID'),
                        CheckoutRequestID=json_response.get('CheckoutRequestID')
                    )
                    ServiceTrans.save()

                    return Response({
                        'status': True,
                        'message': 'Payment initiated'
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = json_response.get('errorMessage', json_response.get('ResponseDescription', 'MPesa payment configuration error'))
                    print(f"MPesa STK Push failed: {error_msg}, Response: {json_response}")
                    return Response({
                        'status': False,
                        'message': f'Payment gateway error: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Card Payment Logic
            elif pay_via == 'card':
                stripe.api_key = settings.STRIPE_SECRET_KEY
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'kes',
                            'unit_amount': int(service_charge * 100),  # Convert to cents
                            'product_data': {'name': 'Service Payment'}
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=settings.SUCCESS_URL,
                    cancel_url=settings.CANCEL_URL
                )

                return Response({
                    'status': True,
                    'message': 'Transaction is being processed',
                    'id': checkout_session.id,
                    'url': checkout_session.url
                }, status=status.HTTP_200_OK)

            # Pesapal Payment Logic
            elif pay_via == 'pesapal':
                try:
                    # Create or get existing service instance
                    service_instance, created = services.objects.get_or_create(
                        user=user,
                        defaults={
                            'block': tenant.PropertyBlock.block,
                            'service_name': service_name,
                            'amount': service_charge,
                            'balance_service_charge': annual_service_charge - service_charge,
                            'payment_mode': pay_via
                        }
                    )

                    if not created:
                        service_instance.balance_service_charge -= service_charge
                        service_instance.save()

                    # Check for existing pending transaction to avoid duplicates
                    existing_transaction = serviceTransactions.objects.filter(
                        service_instance=service_instance,
                        status=0,
                        MerchantRequestID__isnull=True
                    ).first()

                    if existing_transaction:
                        service_transaction = existing_transaction
                    else:
                        # Create new transaction record
                        service_transaction = serviceTransactions.objects.create(
                            service_instance=service_instance,
                            status=0,  # Pending
                            payment_method='pesapal'
                        )

                    # Build merchant reference
                    merchant_reference = f"SERVICE-{service_transaction.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    # Redirect URL - where user is sent after payment (deep link to app)
                    callback_url = "smartnyumba://payment-complete?type=service"

                    # IPN URL - where Pesapal sends payment notifications (must be HTTPS backend URL)
                    ipn_url = "https://api.smartnyumba.tech/apps/api/v1/tenant-services/pesapal-callback/"

                    # Build billing address
                    billing_address = {
                        "phone_number": mobile_number or user.mobile_number,
                        "email_address": email,
                        "country_code": "KE",
                        "first_name": user.first_name or "Tenant",
                        "middle_name": "",
                        "last_name": user.last_name or "",
                        "line_1": "",
                        "line_2": "",
                        "city": "",
                        "state": "",
                        "postal_code": "",
                        "zip_code": ""
                    }

                    # Build description
                    payment_description = f"Service charge for {user.get_full_name() or user.email}"

                    # Submit order to Pesapal
                    pesapal_response = pesapal_service.submit_order(
                        merchant_reference=merchant_reference,
                        amount=service_charge,
                        description=payment_description,
                        callback_url=callback_url,
                        currency='KES',
                        billing_address=billing_address,
                        ipn_url=ipn_url
                    )

                    # Update transaction with order tracking ID
                    service_transaction.MerchantRequestID = pesapal_response['order_tracking_id']
                    service_transaction.pesapal_response = json.dumps(pesapal_response)
                    service_transaction.save()

                    return Response({
                        'status': True,
                        'message': 'Please complete payment in the checkout page',
                        'redirect_url': pesapal_response['redirect_url'],
                        'order_tracking_id': pesapal_response['order_tracking_id'],
                        'transaction_id': service_transaction.id
                    }, status=status.HTTP_200_OK)

                except pesapal_service.PesapalException as e:
                    return Response({
                        'status': False,
                        'message': f'Payment gateway error: {str(e)}'
                    }, status=status.HTTP_502_BAD_GATEWAY)

            else:
                return Response({
                    'status': False,
                    'message': f'Unsupported payment method: {pay_via}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(str(e))
            return Response({
                'status': False,
                'message': 'Payment failed!'
            }, status=status.HTTP_400_BAD_REQUEST)
        
class MpesaCallBackAPIView(APIView):
    
    def post(self, request):
        data = request.data

        print("Mpesa Callback started.....")
        print("Callback data: ", data)

        {
            "data": {
                "Body": {
                    "stkCallback": {
                        "MerchantRequestID": "44398-58044773-1",
                        "CheckoutRequestID": "ws_CO_20062023153944017795941990",
                        "ResultCode": 0,
                        "ResultDesc": "The service request is processed successfully.",
                        "CallbackMetadata": {
                        "Item": [
                            {
                            "Name": "Amount",
                            "Value": 1.0
                            },
                            {
                            "Name": "MpesaReceiptNumber",
                            "Value": "RFK9IRCXVD"
                            },
                            {
                            "Name": "TransactionDate",
                            "Value": 20230620153923
                            },
                            {
                            "Name": "PhoneNumber",
                            "Value": 254795941990
                            }
                        ]
                        }
                    }
                    }
                }
            }
        ResponseCode = data['Body']['stkCallback']['ResultCode']

        CheckoutRequestID = data['Body']['stkCallback']['CheckoutRequestID']
        MerchantRequestID = data['Body']['stkCallback']['MerchantRequestID']

        print("CheckoutRequestID: ", CheckoutRequestID)
        print("MerchantRequestID: ", MerchantRequestID)

        if ResponseCode == 0:
            Service = serviceTransactions.objects.filter(MerchantRequestID=MerchantRequestID, CheckoutRequestID=CheckoutRequestID)
        
            if not Service.exists():
                return Response({
                    'status': False,
                    'message': 'Transaction does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            Service = Service.first()
            if Service.isB2CCompleted == 1:
                return Response({
                    'status': False,
                    'message': 'Transaction already completed!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            Service.status = 1
            Service.service_instance.save()
            Service.save()

            print("Service updated from db: ", Service)

            # do a B2C mpesa transaction.

            # work backwards to find business number from tenant -> propertyBlock -> property
            user = Service.service_instance.user

            service_charge_paybill_number = Tenant.objects.filter(user=user).first().PropertyBlock.block.service_charge_business_number

            print("This is the service charge pay bill ", service_charge_paybill_number)


            # Usage Example
            initiator_password = settings.SAFARICOM_B2C_INITIATOR_PASSWORD

            certificate_path = os.path.join(settings.BASE_DIR, 'SandboxCertificate.cer')
    
            # Make sure the certificate file exists
            if os.path.exists(certificate_path):
                encrypted_message = encrypt_initiator_password_with_certificate_file(initiator_password, certificate_path)
                print(f"Encrypted and Base64 Encoded Message: {encrypted_message}")
            else:
                raise FileNotFoundError(f"Certificate file not found at {certificate_path}")

            generate_account_reference = generate_B2c_account_reference()

            print(generate_account_reference)

            # Calculate commission (5% deduction)
            from utils.commission import calculate_commission

            original_amount = Service.service_instance.amount
            commission_data = calculate_commission(original_amount)

            # Save commission details to transaction record
            Service.commission_amount = commission_data['commission_amount']
            Service.landlord_payout_amount = commission_data['landlord_payout']
            Service.platform_earnings = commission_data['platform_earnings']
            Service.save()

            print(f"Original amount: {original_amount}, Commission: {commission_data['commission_amount']}, Landlord payout: {commission_data['landlord_payout']}")

            payload = {
                "Initiator": settings.SAFARICOM_B2C_INITIATOR_NAME,
                "SecurityCredential": encrypted_message,
                "CommandID": "BusinessPayBill",
                "SenderIdentifierType": "4",
                "RecieverIdentifierType":"4",
                "Amount": int(commission_data['landlord_payout']),  # Send 95% to landlord
                "PartyA": settings.SAFARICOM_B2C_PARTYA,
                "PartyB": service_charge_paybill_number,
                "AccountReference": generate_account_reference,
                "Requester": 254795941990,
                "Remarks": "B2C CHECKOUT",
                "QueueTimeOutURL": settings.SAFARICOM_B2C_QUEUETIMEOUTURL,
                "ResultURL": settings.SAFARICOM_B2C_RESULTURL
            }

            print("This is the payload: ", payload)

            access_token = get_b2c_access_token()

            endpoint = settings.SAFARICOM_B2C_ENDPOINT

            headers = {
                'Content-Type': 'application/json',
                "Authorization": f'Bearer {access_token}'
            }

            print("This is the token: ", access_token)

            response = requests.post(endpoint, json=payload, headers=headers)
            json_response = json.loads(response.text)
            print(json_response)
            print(json_response['OriginatorConversationID'])
            print(json_response['ConversationID'])

            if json_response['ResponseCode'] == '0':   
                Service.isB2CCompleted = 1
                Service.save()             
                return Response({
                    'status': True,
                    'message': 'Transaction Completed successfully.'
                }, status=status.HTTP_200_OK)
            
            else :
                return Response({
                    'status': False,
                    'message': 'Operation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        else :
                return Response({
                    'status': False,
                    'message': 'Operation failed'
                }, status=status.HTTP_400_BAD_REQUEST)
        
class AllTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AllTRansactionsSerializer

    def get(self, request):
        try:
            current_user = request.user
            print(current_user)
            allowed_roles = ['tenant']

            print(current_user.role.short_name)
            

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            print("we are here...")
            user = User.objects.filter(email=current_user).first()  
            print(user)          
            tenant = Tenant.objects.filter(user=user).first()
            PropertyBlock = tenant.PropertyBlock
            house_number = tenant.PropertyBlock.house_number
            block = tenant.PropertyBlock.block.block_number
            print(house_number)
            print(block)
            all_services = services.objects.filter(user=user, status=1).order_by('-id')

            print(all_services)

            serializer = self.serializer_class(all_services, many=True)

            transactions_with_details = []
            for service_data, service in zip(serializer.data, all_services):
                block = block
                if block:
                    service_data['house_number'] = house_number
                    service_data['block_number'] = block
                transactions_with_details.append(service_data)

            return Response({
                'status': True,
                'transactions': transactions_with_details
            }, status=status.HTTP_200_OK)
        

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not fetch all transactions!'
            }, status=status.HTTP_400_BAD_REQUEST)

class CheckTransactionStatusAPIView(APIView):
    
    serializer_class = TransactionCheckSerializer

    def post(self, request):
        try:
            email = request.data.get('email')

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email to continue'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=email).first()
            
            subscription = services.objects.filter(user=user)

            if not subscription.exists():
                return Response({
                    'status': False,
                    'message': 'Subscription does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            subscription = subscription.last()

            
            serializer = TransactionSerializer(subscription)

            return Response({
                'status': True,
                'message': 'transaction sucessful',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'We could not complete payment process.',
                'ResponseCode': '400'
            }, status=status.HTTP_400_BAD_REQUEST)


# ============================================
# RENT PAYMENT VIEWS
# ============================================

class PayRentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PayRentSerializer

    def post(self, request):
        try:
            data = request.data
            current_user = request.user
            serializer = self.serializer_class(data=data)

            if not serializer.is_valid():
                return Response({
                    'status': False,
                    'message': 'Invalid data provided!',
                    'error': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            allowed_roles = ['tenant']
            if current_user.role.short_name not in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)

            email = request.data.get('email')
            mobile_number = request.data.get('mobile_number')
            pay_via = request.data.get('pay_via', '').lower()
            month = request.data.get('month')
            year = request.data.get('year')

            # Validate email
            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.fullmatch(email_regex, email):
                return Response({
                    'status': False,
                    'message': 'Provide a valid email'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({
                    'status': False,
                    'message': 'Tenant with this email does not exist'
                }, status=status.HTTP_404_NOT_FOUND)

            # Format mobile number
            if mobile_number:
                mobile_number = user.mobile_number[-9:]
                mobile_number = f'254{mobile_number}'

            if len(mobile_number) > 13:
                return Response({
                    'status': False,
                    'message': 'Number too long'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get tenant and rent amount
            tenant = Tenant.objects.filter(email=email).first()
            if not tenant:
                return Response({
                    'status': False,
                    'message': 'Tenant not found'
                }, status=status.HTTP_404_NOT_FOUND)

            rent_amount = Decimal(tenant.PropertyBlock.rent_charged)

            # Create or get rent payment record
            rent_payment, created = RentPayment.objects.get_or_create(
                user=user,
                property_block=tenant.PropertyBlock,
                month=month,
                year=year,
                defaults={
                    'rent_amount': rent_amount,
                    'payment_mode': pay_via,
                    'status': 0
                }
            )

            # Check if already paid
            if not created and rent_payment.status == 1:
                return Response({
                    'status': False,
                    'message': f'Rent for {month}/{year} already paid'
                }, status=status.HTTP_400_BAD_REQUEST)

            # MPesa Payment Logic
            if pay_via == 'mpesa':
                access_token = get_access_token()
                headers = {
                    'Content-Type': 'application/json',
                    "Authorization": f'Bearer {access_token}'
                }
                endpoint = settings.SAFARICOM_STK_PUSH
                Business_short_code = settings.BUSINESS_SHORT_CODE
                partyB = settings.TILLNUMBER
                timestamp = f"{datetime.datetime.now():%Y%m%d%H%M%S}"
                pass_key = settings.SAFARICOM_PASS_KEY
                message = f'{Business_short_code}{pass_key}{timestamp}'
                password = base64.b64encode(message.encode('ascii')).decode('ascii')
                CallBackURL = 'https://api.smartnyumba.com/apps/api/v1/tenant-services/rent-mpesa-callback/'

                payload = {
                    "BusinessShortCode": Business_short_code,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerBuyGoodsOnline",
                    "Amount": int(rent_amount),
                    "PartyA": mobile_number,
                    "PartyB": partyB,
                    "PhoneNumber": mobile_number,
                    "CallBackURL": CallBackURL,
                    "AccountReference": f"RENT-{month}-{year}",
                    "TransactionDesc": f"Rent Payment {month}/{year}"
                }

                response = requests.post(endpoint, json=payload, headers=headers)
                json_response = json.loads(response.text)

                print("Rent payment STK Push response:", json_response)

                if response.status_code == 200:
                    # Create transaction record
                    RentTransaction.objects.create(
                        rent_payment=rent_payment,
                        MerchantRequestID=json_response.get('MerchantRequestID'),
                        CheckoutRequestID=json_response.get('CheckoutRequestID'),
                        status=0
                    )

                    return Response({
                        'status': True,
                        'message': 'STK Push sent successfully',
                        'MerchantRequestID': json_response.get('MerchantRequestID')
                    }, status=status.HTTP_200_OK)
                else:
                    error_msg = json_response.get('errorMessage', json_response.get('ResponseDescription', 'MPesa payment configuration error'))
                    print(f"Rent MPesa STK Push failed: {error_msg}, Response: {json_response}")
                    return Response({
                        'status': False,
                        'message': f'Payment gateway error: {error_msg}'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Card Payment Logic
            elif pay_via == 'card':
                stripe.api_key = settings.STRIPE_SECRET_KEY
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price_data': {
                            'currency': 'kes',
                            'unit_amount': int(rent_amount * 100),
                            'product_data': {'name': f'Rent Payment {month}/{year}'}
                        },
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=settings.SUCCESS_URL,
                    cancel_url=settings.CANCEL_URL,
                    metadata={'rent_payment_id': rent_payment.id}
                )

                return Response({
                    'status': True,
                    'message': 'Stripe checkout session created',
                    'id': checkout_session.id,
                    'url': checkout_session.url
                }, status=status.HTTP_200_OK)

            # Pesapal Payment Logic
            elif pay_via == 'pesapal':
                try:
                    # Check for existing pending transaction to avoid duplicates
                    existing_transaction = RentTransaction.objects.filter(
                        rent_payment=rent_payment,
                        status=0,
                        MerchantRequestID__isnull=True
                    ).first()

                    if existing_transaction:
                        rent_transaction = existing_transaction
                    else:
                        # Create new transaction record
                        rent_transaction = RentTransaction.objects.create(
                            rent_payment=rent_payment,
                            status=0,  # Pending
                            payment_method='pesapal'
                        )

                    # Build merchant reference
                    merchant_reference = f"RENT-{rent_transaction.id}-{month}-{year}-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    # Redirect URL - where user is sent after payment (deep link to app)
                    callback_url = "smartnyumba://payment-complete?type=rent"

                    # IPN URL - where Pesapal sends payment notifications (must be HTTPS backend URL)
                    ipn_url = "https://api.smartnyumba.tech/apps/api/v1/tenant-services/pesapal-rent-callback/"

                    # Build billing address
                    billing_address = {
                        "phone_number": mobile_number or user.mobile_number,
                        "email_address": email,
                        "country_code": "KE",
                        "first_name": user.first_name or "Tenant",
                        "middle_name": "",
                        "last_name": user.last_name or "",
                        "line_1": "",
                        "line_2": "",
                        "city": "",
                        "state": "",
                        "postal_code": "",
                        "zip_code": ""
                    }

                    # Build description
                    payment_description = f"Rent payment for {user.get_full_name() or user.email}, {month}/{year}"

                    # Submit order to Pesapal
                    pesapal_response = pesapal_service.submit_order(
                        merchant_reference=merchant_reference,
                        amount=rent_amount,
                        description=payment_description,
                        callback_url=callback_url,
                        currency='KES',
                        billing_address=billing_address,
                        ipn_url=ipn_url
                    )

                    # Update transaction with order tracking ID
                    rent_transaction.MerchantRequestID = pesapal_response['order_tracking_id']
                    rent_transaction.pesapal_response = json.dumps(pesapal_response)
                    rent_transaction.save()

                    return Response({
                        'status': True,
                        'message': 'Please complete payment in the checkout page',
                        'redirect_url': pesapal_response['redirect_url'],
                        'order_tracking_id': pesapal_response['order_tracking_id'],
                        'transaction_id': rent_transaction.id,
                        'MerchantRequestID': pesapal_response['order_tracking_id']
                    }, status=status.HTTP_200_OK)

                except pesapal_service.PesapalException as e:
                    return Response({
                        'status': False,
                        'message': f'Payment gateway error: {str(e)}'
                    }, status=status.HTTP_502_BAD_GATEWAY)

            else:
                return Response({
                    'status': False,
                    'message': f'Unsupported payment method: {pay_via}'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"Rent payment error: {str(e)}")
            return Response({
                'status': False,
                'message': 'Rent payment failed!'
            }, status=status.HTTP_400_BAD_REQUEST)


class RentMpesaCallBackAPIView(APIView):

    def post(self, request):
        data = request.data
        print("Rent M-Pesa Callback Data:", data)

        try:
            result_code = data['Body']['stkCallback']['ResultCode']

            if result_code == 0:
                # Payment successful
                merchant_request_id = data['Body']['stkCallback']['MerchantRequestID']
                checkout_request_id = data['Body']['stkCallback']['CheckoutRequestID']

                print(f"Rent payment successful: {merchant_request_id}")

                # Update transaction status
                transaction = RentTransaction.objects.filter(
                    MerchantRequestID=merchant_request_id,
                    CheckoutRequestID=checkout_request_id
                ).first()

                if transaction and transaction.isB2CCompleted == 0:
                    transaction.status = 1
                    transaction.save()

                    # Update rent payment status
                    rent_payment = transaction.rent_payment
                    rent_payment.status = 1
                    rent_payment.save()

                    print(f"Rent payment updated: {rent_payment}")

                    # B2C Payout with 5% commission deduction
                    user = rent_payment.user
                    property_block = rent_payment.property_block

                    # Get landlord's rent paybill number
                    rent_paybill_number = property_block.rent_charge_business_number

                    print(f"Rent paybill number: {rent_paybill_number}")

                    # Calculate commission using utility
                    from utils.commission import calculate_commission
                    original_amount = rent_payment.rent_amount
                    commission_data = calculate_commission(original_amount)

                    # Save commission details
                    transaction.commission_amount = commission_data['commission_amount']
                    transaction.landlord_payout_amount = commission_data['landlord_payout']
                    transaction.platform_earnings = commission_data['platform_earnings']
                    transaction.save()

                    print(f"Rent commission: {commission_data['commission_amount']}, Landlord payout: {commission_data['landlord_payout']}")

                    # Encrypt initiator password
                    initiator_password = settings.SAFARICOM_B2C_INITIATOR_PASSWORD
                    certificate_path = os.path.join(settings.BASE_DIR, 'SandboxCertificate.cer')

                    if not os.path.exists(certificate_path):
                        raise FileNotFoundError(f"Certificate not found at {certificate_path}")

                    encrypted_message = encrypt_initiator_password_with_certificate_file(
                        initiator_password,
                        certificate_path
                    )

                    # Generate account reference
                    generate_account_reference = generate_B2c_account_reference()

                    # B2C Payload - send 95% to landlord
                    payload = {
                        "Initiator": settings.SAFARICOM_B2C_INITIATOR_NAME,
                        "SecurityCredential": encrypted_message,
                        "CommandID": "BusinessPayBill",
                        "SenderIdentifierType": "4",
                        "RecieverIdentifierType": "4",
                        "Amount": int(commission_data['landlord_payout']),  # 95% of original
                        "PartyA": settings.SAFARICOM_B2C_PARTYA,
                        "PartyB": rent_paybill_number,  # Landlord's rent paybill
                        "AccountReference": generate_account_reference,
                        "Requester": 254795941990,
                        "Remarks": "RENT B2C PAYOUT",
                        "QueueTimeOutURL": settings.SAFARICOM_B2C_QUEUETIMEOUTURL,
                        "ResultURL": settings.SAFARICOM_B2C_RESULTURL
                    }

                    print(f"Rent B2C payload: {payload}")

                    # Get access token and send B2C request
                    access_token = get_b2c_access_token()
                    endpoint = settings.SAFARICOM_B2C_ENDPOINT
                    headers = {
                        'Content-Type': 'application/json',
                        "Authorization": f'Bearer {access_token}'
                    }

                    response = requests.post(endpoint, json=payload, headers=headers)
                    json_response = response.json()
                    print(f"Rent B2C Response: {json_response}")

                    if json_response.get('ResponseCode') == '0':
                        transaction.isB2CCompleted = 1
                        transaction.save()
                        print("Rent B2C completed successfully")
                        return Response({'status': True, 'message': 'Rent B2C completed'}, status=status.HTTP_200_OK)
                    else:
                        print(f"Rent B2C failed: {json_response}")
                        return Response({'status': False, 'message': 'B2C payout failed'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                print(f"Rent payment failed with result code: {result_code}")
                return Response({'status': False, 'message': 'Payment failed'}, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Rent callback error: {str(e)}")
            return Response({'status': False, 'message': 'Callback processing error'}, status=status.HTTP_200_OK)


class AllRentTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user

            if current_user.role.short_name not in ['tenant', 'admin']:
                return Response({
                    'status': False,
                    'message': 'Not authorized'
                }, status=status.HTTP_403_FORBIDDEN)

            if current_user.role.short_name == 'tenant':
                rent_payments = RentPayment.objects.filter(user=current_user)
            else:
                rent_payments = RentPayment.objects.all()

            serializer = RentPaymentSerializer(rent_payments, many=True)
            return Response({
                'status': True,
                'data': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Rent transactions error: {str(e)}")
            return Response({
                'status': False,
                'message': 'Could not retrieve rent transactions'
            }, status=status.HTTP_400_BAD_REQUEST)


class PesapalIPNView(APIView):
    """
    Handle Pesapal IPN (Instant Payment Notification) callbacks.

    Pesapal sends IPN notifications when transaction status changes.
    This endpoint processes the notification and updates transaction status.

    Note: This endpoint should be publicly accessible (no authentication required)
    and must be HTTPS in production.
    """
    permission_classes = []  # No authentication for IPN callbacks

    def post(self, request):
        """Handle POST IPN callbacks from Pesapal"""
        return self._process_ipn(request)

    def get(self, request):
        """Handle GET IPN callbacks from Pesapal"""
        return self._process_ipn(request)

    def _process_ipn(self, request):
        """
        Process IPN notification from Pesapal.

        Pesapal may send order_tracking_id in:
        - POST body (JSON or form data)
        - GET query parameters
        - Headers
        """
        try:
            # Extract order_tracking_id from various possible sources
            order_tracking_id = None

            # Try POST JSON body
            if request.content_type == 'application/json' and request.body:
                try:
                    data = json.loads(request.body)
                    order_tracking_id = data.get('OrderTrackingId') or data.get('order_tracking_id')
                except json.JSONDecodeError:
                    pass

            # Try POST form data
            if not order_tracking_id:
                order_tracking_id = request.POST.get('OrderTrackingId') or request.POST.get('order_tracking_id')

            # Try GET query parameters
            if not order_tracking_id:
                order_tracking_id = request.GET.get('OrderTrackingId') or request.GET.get('order_tracking_id')

            if not order_tracking_id:
                print(f"IPN received without order_tracking_id. Data: {request.data}, Query: {request.GET}")
                return Response(
                    {"error": "Missing order_tracking_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            print(f"Processing Pesapal IPN for order_tracking_id: {order_tracking_id}")

            # Query Pesapal for authoritative transaction status
            transaction_status = pesapal_service.get_transaction_status(order_tracking_id)

            print(f"Transaction status from Pesapal: {transaction_status['status']}")

            # Find corresponding transaction in database
            # Try RentTransaction, serviceTransactions, and ActivationTransaction
            transaction = None
            transaction_type = None

            rent_transaction = RentTransaction.objects.filter(
                MerchantRequestID=order_tracking_id
            ).first()

            if rent_transaction:
                transaction = rent_transaction
                transaction_type = 'rent'
            else:
                service_transaction = serviceTransactions.objects.filter(
                    MerchantRequestID=order_tracking_id
                ).first()
                if service_transaction:
                    transaction = service_transaction
                    transaction_type = 'service'
                else:
                    # Check for activation payment
                    from authentication.models import ActivationTransaction
                    activation_transaction = ActivationTransaction.objects.filter(
                        MerchantRequestID=order_tracking_id
                    ).first()
                    if activation_transaction:
                        transaction = activation_transaction
                        transaction_type = 'activation'

            if not transaction:
                print(f"No transaction found for order_tracking_id: {order_tracking_id}")
                return Response(
                    {"error": "Transaction not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Update transaction based on status
            pesapal_status = transaction_status['status']

            # Idempotency check - if already processed, return success
            if transaction.status == 1 and pesapal_status == 'COMPLETED':
                print(f"Transaction {transaction.id} already marked as completed. Idempotent IPN.")
                return Response({"status": "ok", "message": "Already processed"}, status=status.HTTP_200_OK)

            if pesapal_status == 'COMPLETED':
                # Payment successful
                transaction.status = 1  # Completed/Paid
                transaction.confirmation_code = transaction_status.get('confirmation_code', '')
                transaction.pesapal_response = json.dumps(transaction_status['raw_response'])
                transaction.payment_method = transaction_status.get('payment_method', 'pesapal')
                transaction.save()

                print(f"{transaction_type.capitalize()} transaction {transaction.id} marked as COMPLETED. Confirmation: {transaction.confirmation_code}")

                # Update parent payment status
                if transaction_type == 'rent' and transaction.rent_payment:
                    transaction.rent_payment.status = 1
                    transaction.rent_payment.save()
                    print(f"Rent payment {transaction.rent_payment.id} marked as completed")
                elif transaction_type == 'service' and transaction.service_instance:
                    transaction.service_instance.status = 1
                    transaction.service_instance.save()
                    print(f"Service {transaction.service_instance.id} marked as completed")
                elif transaction_type == 'activation' and transaction.activation_payment:
                    # Handle activation payment completion
                    activation_payment = transaction.activation_payment
                    activation_payment.status = 1  # Completed
                    activation_payment.completed_at = timezone.now()
                    activation_payment.save()

                    # Activate the landlord user account
                    user = activation_payment.user
                    user.status = 1  # Active
                    user.save()

                    print(f"Activation payment {activation_payment.id} completed. User {user.email} activated.")

                # Calculate and save commission
                from utils.commission import calculate_commission
                if transaction_type == 'rent':
                    original_amount = transaction.rent_payment.rent_amount
                elif transaction_type == 'service':
                    original_amount = transaction.service_instance.amount
                elif transaction_type == 'activation':
                    # Activation fee goes 100% to platform (no commission split)
                    original_amount = transaction.activation_payment.amount
                    transaction.platform_earnings = original_amount
                    transaction.save()
                    print(f"Activation fee: {original_amount} (100% platform earnings)")
                else:
                    original_amount = Decimal('0')

                # Only calculate commission for rent and service payments
                if transaction_type in ['rent', 'service']:
                    commission_data = calculate_commission(original_amount)
                    transaction.commission_amount = commission_data['commission_amount']
                    transaction.landlord_payout_amount = commission_data['landlord_payout']
                    transaction.platform_earnings = commission_data['platform_earnings']
                    transaction.save()

                    print(f"Commission calculated: {commission_data['commission_amount']}, Landlord payout: {commission_data['landlord_payout']}")

            elif pesapal_status in ['FAILED', 'CANCELLED']:
                # Payment failed or cancelled
                transaction.status = 2  # Failed (or use appropriate status code)
                transaction.pesapal_response = json.dumps(transaction_status['raw_response'])
                transaction.save()

                print(f"Transaction {transaction.id} marked as {pesapal_status}")

            else:
                # Status still pending or unknown
                print(f"Transaction {transaction.id} status: {pesapal_status} (no update)")

            # Return 200 OK to Pesapal to acknowledge receipt
            return Response(
                {"status": "ok", "message": "IPN processed successfully"},
                status=status.HTTP_200_OK
            )

        except pesapal_service.PesapalException as e:
            print(f"Pesapal IPN processing error: {str(e)}")
            return Response(
                {"error": "Failed to process IPN"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            print(f"IPN processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to process IPN"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckPaymentStatusAPIView(APIView):
    """
    Check payment status for a transaction.

    Supports lookup by internal transaction_id or order_tracking_id.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Check payment status.

        Expected payload:
        {
            "transaction_id": int (optional),
            "order_tracking_id": string (optional),
            "transaction_type": "rent" | "service"
        }
        """
        try:
            transaction_id = request.data.get('transaction_id')
            order_tracking_id = request.data.get('order_tracking_id')
            transaction_type = request.data.get('transaction_type', 'rent')

            if not transaction_id and not order_tracking_id:
                return Response(
                    {"error": "Either transaction_id or order_tracking_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Find transaction
            transaction = None
            if transaction_type == 'rent':
                if transaction_id:
                    transaction = RentTransaction.objects.filter(id=transaction_id).first()
                elif order_tracking_id:
                    transaction = RentTransaction.objects.filter(MerchantRequestID=order_tracking_id).first()
            else:  # service
                if transaction_id:
                    transaction = serviceTransactions.objects.filter(id=transaction_id).first()
                elif order_tracking_id:
                    transaction = serviceTransactions.objects.filter(MerchantRequestID=order_tracking_id).first()

            if not transaction:
                return Response(
                    {"error": "Transaction not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # If transaction is pending and has order_tracking_id, query Pesapal
            if transaction.status == 0 and transaction.MerchantRequestID and transaction.payment_method == 'pesapal':
                try:
                    pesapal_status = pesapal_service.get_transaction_status(transaction.MerchantRequestID)

                    # Update transaction if status changed
                    if pesapal_status['status'] == 'COMPLETED' and transaction.status != 1:
                        transaction.status = 1
                        transaction.confirmation_code = pesapal_status.get('confirmation_code', '')
                        transaction.pesapal_response = json.dumps(pesapal_status['raw_response'])
                        transaction.save()

                        # Update parent payment status
                        if transaction_type == 'rent' and transaction.rent_payment:
                            transaction.rent_payment.status = 1
                            transaction.rent_payment.save()
                        elif transaction_type == 'service' and transaction.service_instance:
                            transaction.service_instance.status = 1
                            transaction.service_instance.save()

                        # Calculate commission
                        from utils.commission import calculate_commission
                        if transaction_type == 'rent':
                            original_amount = transaction.rent_payment.rent_amount
                        else:
                            original_amount = transaction.service_instance.amount

                        commission_data = calculate_commission(original_amount)
                        transaction.commission_amount = commission_data['commission_amount']
                        transaction.landlord_payout_amount = commission_data['landlord_payout']
                        transaction.platform_earnings = commission_data['platform_earnings']
                        transaction.save()

                        print(f"Transaction {transaction.id} updated to COMPLETED via status check")

                except pesapal_service.PesapalException as e:
                    print(f"Failed to check Pesapal status: {str(e)}")

            # Return current transaction status
            response_data = {
                "transaction_id": transaction.id,
                "status": transaction.status,
                "status_text": self._get_status_text(transaction.status),
                "payment_method": transaction.payment_method if hasattr(transaction, 'payment_method') else "unknown",
                "confirmation_code": transaction.confirmation_code if hasattr(transaction, 'confirmation_code') else ""
            }

            # Add type-specific data
            if transaction_type == 'rent' and transaction.rent_payment:
                response_data.update({
                    "amount": str(transaction.rent_payment.rent_amount),
                    "month": transaction.rent_payment.month,
                    "year": transaction.rent_payment.year
                })
            elif transaction_type == 'service' and transaction.service_instance:
                response_data.update({
                    "amount": str(transaction.service_instance.amount),
                    "service_name": transaction.service_instance.service_name
                })

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"CheckPaymentStatusAPIView error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": "Failed to check payment status"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_status_text(self, status_code):
        """Convert status code to human-readable text"""
        status_map = {
            0: "Pending",
            1: "Completed",
            2: "Failed"
        }
        return status_map.get(status_code, "Unknown")
