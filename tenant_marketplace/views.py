import re
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth import get_user_model

from marketplace.models import MarketPlace
User = get_user_model()

from marketplace.api.serializers import AddGoodsSerializer, UploadGoodsToEstateSerializer, ViewAllUnpublishedGoodsSerializer

#add goods
class AddGoodsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddGoodsSerializer

    def post(self, request):
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
        
        goods_name = request.data.get('goods_name')
        goods_description = request.data.get('goods_description')
        goods_quantity = request.data.get('goods_quantity')
        any_offer = request.data.get('any_offer')
        

        user = User.objects.filter(email=current_user)

        if not user.exists():
            return Response({
                'status': False,
                'message': 'tenant with this email does not exist'
            }, status=status.HTTP_404_NOT_FOUND)
        
        user = user.first()
        if user.is_active == 0:
            return Response({
                'status': False,
                'message': 'tenant account is inactive'
            }, status=status.HTTP_400_BAD_REQUEST)
        if not MarketPlace.objects.create(goods_name=goods_name, goods_description=goods_description, goods_quantity=goods_quantity, any_offer=any_offer):
            return Response({
                'status': False,
                'message': 'error accessing db'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
                'status': True,
                'message': 'Goods added successfully'
            }, status=status.HTTP_200_OK)

class UploadGoodsToEstateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UploadGoodsToEstateSerializer

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
            
            goods_id = request.data.get('goods_id')

            market_goods = MarketPlace.objects.filter(id=goods_id)
            if not market_goods.exists():
                return Response({
                    'status': False,
                    'message': 'goods do not exist!'
                }, status=status.HTTP_404_NOT_FOUND)
            
            market_goods = market_goods.first()

            market_goods.status = 1
            market_goods.save()

            return Response({
                'status': True,
                'message': 'Goods Published to estate!'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not publish to estate!'
            }, status=status.HTTP_200_OK)


class ViewAllUnpublishedGoodsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ViewAllUnpublishedGoodsSerializer

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            unpublished_goods = MarketPlace.objects.filter(status=0).order_by('-id')

            serializer = self.serializer_class(unpublished_goods, many=True)

            return Response({
                'status': True,
                'goods': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not publish to estate!'
            }, status=status.HTTP_200_OK)


class ViewAllPublishedGoodsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ViewAllUnpublishedGoodsSerializer

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            unpublished_goods = MarketPlace.objects.filter(status=1).order_by('-id')

            serializer = self.serializer_class(unpublished_goods, many=True)

            return Response({
                'status': True,
                'goods': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not publish to estate!'
            }, status=status.HTTP_200_OK)

class ViewAllGoodsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ViewAllUnpublishedGoodsSerializer

    def get(self, request):
        try:
            current_user = request.user
            allowed_roles = ['tenant']

            if not current_user.role.short_name in allowed_roles:
                return Response({
                    'status': False,
                    'message': 'Role not allowed to access this portal!'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            unpublished_goods = MarketPlace.objects.order_by('-id')

            serializer = self.serializer_class(unpublished_goods, many=True)

            return Response({
                'status': True,
                'goods': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not publish to estate!'
            }, status=status.HTTP_200_OK)


class DeleteGoodsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UploadGoodsToEstateSerializer

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
            
            goods_id = request.data.get('goods_id')

            market_goods = MarketPlace.objects.filter(id=goods_id)
            if not market_goods.exists():
                return Response({
                    'status': False,
                    'message': 'goods do not exist!'
                }, status=status.HTTP_404_NOT_FOUND)
            
            market_goods = market_goods.first()

            market_goods.delete()

            return Response({
                'status': True,
                'message': 'Goods deleted!'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))

            return Response({
                'status': False,
                'message': 'Could not publish to estate!'
            }, status=status.HTTP_200_OK)