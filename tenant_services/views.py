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

import stripe

from utils.genRef import generate_B2c_account_reference

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
                    return Response({
                        'status': False,
                        'message': 'Configuration error!'
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
                    return Response({
                        'status': False,
                        'message': 'Payment initiation failed',
                        'error': json_response
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
