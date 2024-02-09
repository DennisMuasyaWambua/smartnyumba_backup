import json
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
from properties.models import PropertyBlock
from tenant_services.models import services
from tenant_services.serializers import AllTRansactionsSerializer, PayServiceSerializer, ServiceFeeAmountSerializer, TransactionCheckSerializer, TransactionSerializer
from utils.api_auth import get_access_token

from django.contrib.auth import get_user_model
from django.conf import settings

import stripe

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

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            email = request.data.get('email')
            mobile_number = request.data.get('mobile_number')
            service_name = request.data.get('service_name')
            pay_via = request.data.get('pay_via')

            pay_via = pay_via.lower()

            email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            valid_email = re.fullmatch(email_regex, email)
            if not valid_email:
                return Response({
                    'status': False,
                    'message': 'Provide a valid email'
                }, status=status.HTTP_400_BAD_REQUEST)
            

            user = User.objects.filter(email=email)

            if not user.exists():
                return Response({
                    'status': False,
                    'message': 'tenant with this email does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            user = user.first()

            if mobile_number == None:
                mobile_number = user.mobile_number
                mobile_number = mobile_number[-9:]
                mobile_number = f'254{mobile_number}'
            

            
            if len(mobile_number) > 13 :
                return Response({
                    'status': False,
                    'message': 'number too long'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            mobile_number = mobile_number[-9:]
            mobile_number = f'254{mobile_number}'


            tenant = Tenant.objects.filter(email=email).first()
            service_charge = tenant.PropertyBlock.service_charge
            service_charge = int(service_charge)

            annual_charge = service_charge * 12

            mpesa = 'mpesa'
            card = 'card'

            
            if pay_via == mpesa:
                #-------------Connect to mpesa daraja push notification-----------
                print("Payment made through mpesa")

                access_token = get_access_token()
                headers = {
                    'Content-Type': 'application/json',
                    "Authorization": f'Bearer {access_token}'
                }
                endpoint = settings.SAFARICOM_STK_PUSH
                Business_short_code = settings.BUSINESS_SHORT_CODE

                timestamp = f"{datetime.datetime.now():%Y%m%d%H%M%S}"

                

                pass_key = settings.SAFARICOM_PASS_KEY

                message = str(Business_short_code)+ pass_key + timestamp
                message_bytes = message.encode('ascii')
                base64_bytes = base64.b64encode(message_bytes)
                password = base64_bytes.decode('ascii')
                CallBackURL = 'https://webhook.site/2ef99e8c-6df5-43e5-a43e-e19264215797'

                # CallBackURL = "https://y34b2e7j9d.execute-api.us-west-1.amazonaws.com/dev/apps/admin/api/v1/tenant-services/mpesa-callback/"

                payload = {
                    "BusinessShortCode": 174379,
                    "Password": password,
                    "Timestamp": timestamp,
                    "TransactionType": "CustomerPayBillOnline",
                    "Amount": service_charge,
                    "PartyA": mobile_number,
                    "PartyB": '174379',
                    "PhoneNumber": mobile_number,
                    "CallBackURL": CallBackURL,
                    "AccountReference": "SmartNyumbaLTD",
                    "TransactionDesc": "Payment of X" 
                }

                print(payload)
                
                response = requests.post(endpoint, json=payload, headers=headers)
                json_response = json.loads(response.text)
                print(json_response)
                if response.status_code == 200:
                    Service = services(
                        user=user,
                        service_name=service_name,
                        amount=service_charge,
                        annual_service_charge=annual_charge,
                        payment_mode=pay_via                    )
                    Service.save()
                    json_response = json.loads(response.text)
                    Service.MerchantRequestID = json_response['MerchantRequestID']
                    Service.CheckoutRequestID = json_response['CheckoutRequestID']

                    Service.save()

                    return Response({
                        'status': True,
                        'message': 'Payment initiated'
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': False,
                        'message': 'Configuration error!'
                    }, status=status.HTTP_400_BAD_REQUEST)

            elif pay_via == card:

                #-----------Connect to stripe card services-----------------------

                stripe.api_key = settings.STRIPE_SECRET_KEY

                amount = float(amount)
                amount = int(amount)

                checkout_session=stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[
                        {
                            'price_data': {
                                'currency': 'kes',
                                'unit_amount': amount,
                                'product_data': {
                                    'name': 'Waste'
                                },
                            },
                            'quantity': 1,
                        },
                    ],
                    mode='payment',
                    success_url = settings.SUCCESS_URL,
                    cancel_url= settings.CANCEL_URL
                )
                print("Payment made through card") 

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

        code = 0

        if ResponseCode == code:
            print("transaction is with status 0!")
            Service = services.objects.filter(MerchantRequestID=MerchantRequestID, CheckoutRequestID=CheckoutRequestID)
            print("service: ", Service)
        
            if not Service.exists():
                return Response({
                    'status': False,
                    'message': 'Transaction does not exist'
                }, status=status.HTTP_404_NOT_FOUND)
            
            Service = Service.first()
            Service.annual_service_charge -= Service.amount
            Service.status = 1
            Service.save()

            print("Service updated from db: ", Service)

            return Response({
                'status': True,
                'message': 'Transaction Completed successfully.'
            }, status=status.HTTP_200_OK)
        
        elif ResponseCode == "1032" or 1032:
            print("operation cancelled by user!")
            return Response({
                'status': False,
                'message': 'Operation Cancelled by user'
            }, status=status.HTTP_400_BAD_REQUEST)
        
class AllTransactionsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AllTRansactionsSerializer

    def get(self, request):
        try:
            current_user = request.user
            print(current_user)
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.filter(email=current_user).first()            
            all_services = services.objects.filter(user=user, status=1).order_by('-id')

            serializer = self.serializer_class(all_services, many=True)

            return Response({
                'status': True,
                'transactions': serializer.data
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
