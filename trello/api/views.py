from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from django.db.models import Q
from django.http import Http404
from rest_auth.registration.views import SocialLoginView
from trello.api.serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
from trello.api.permissions import IsDeskOwnerOrMember, IsDeskOwner
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model

from rest_framework import generics, status, views, permissions
from .serializers import RegisterSerializer, SetNewPasswordSerializer, ResetPasswordEmailRequestSerializer, \
	EmailVerificationSerializer, LoginSerializer, LogoutSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from trello.models import User
from .utils import Util
from django.contrib.sites.shortcuts import get_current_site
import jwt
from django.conf import settings
from drf_yasg import openapi
from .renderers import UserRenderer
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.http import HttpResponsePermanentRedirect
import os

from rest_framework.generics import GenericAPIView
from .serializers import GoogleSocialAuthSerializer


class CustomRedirect(HttpResponsePermanentRedirect):
	allowed_schemes = [os.environ.get('APP_SCHEME'), 'http', 'https']


class RegisterView(generics.GenericAPIView):
	serializer_class = RegisterSerializer
	renderer_classes = (UserRenderer,)

	def post(self, request):
		user = request.data
		serializer = self.serializer_class(data=user)
		serializer.is_valid(raise_exception=True)
		serializer.save()
		user_data = serializer.data
		user = User.objects.get(email=user_data['email'])
		token = RefreshToken.for_user(user).access_token
		current_site = get_current_site(request).domain
		relativeLink = reverse('email-verify')
		absurl = 'http://' + current_site + relativeLink + "?token=" + str(token)
		email_body = 'Hi ' + user.username + \
		             ' Use the link below to verify your email \n' + absurl
		data = {'email_body': email_body, 'to_email': user.email,
		        'email_subject': 'Verify your email'}

		Util.send_email(data)
		return Response(user_data, status=status.HTTP_201_CREATED)


class VerifyEmail(views.APIView):
	serializer_class = EmailVerificationSerializer

	token_param_config = openapi.Parameter(
		'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

	@swagger_auto_schema(manual_parameters=[token_param_config])
	def get(self, request):
		token = request.GET.get('token')
		try:
			payload = jwt.decode(token, settings.SECRET_KEY)
			user = User.objects.get(id=payload['user_id'])
			if not user.is_verified:
				user.is_verified = True
				user.save()
			return Response({'email': 'Successfully activated'}, status=status.HTTP_200_OK)
		except jwt.ExpiredSignatureError as identifier:
			return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
		except jwt.exceptions.DecodeError as identifier:
			return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(generics.GenericAPIView):
	serializer_class = LoginSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response(serializer.data, status=status.HTTP_200_OK)


class RequestPasswordResetEmail(generics.GenericAPIView):
	serializer_class = ResetPasswordEmailRequestSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data)

		email = request.data.get('email', '')

		if User.objects.filter(email=email).exists():
			user = User.objects.get(email=email)
			uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
			token = PasswordResetTokenGenerator().make_token(user)
			current_site = get_current_site(
				request=request).domain
			relativeLink = reverse(
				'password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

			redirect_url = request.data.get('redirect_url', '')
			absurl = 'http://' + current_site + relativeLink
			email_body = 'Hello, \n Use link below to reset your password  \n' + \
			             absurl + "?redirect_url=" + redirect_url
			data = {'email_body': email_body, 'to_email': user.email,
			        'email_subject': 'Reset your passsword'}
			Util.send_email(data)
		return Response({'success': 'We have sent you a link to reset your password'}, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):
	serializer_class = SetNewPasswordSerializer

	def get(self, request, uidb64, token):
		redirect_url = request.GET.get('redirect_url')
		try:
			id = smart_str(urlsafe_base64_decode(uidb64))
			user = User.objects.get(id=id)

			if not PasswordResetTokenGenerator().check_token(user, token):
				if len(redirect_url) > 3:
					return CustomRedirect(redirect_url + '?token_valid=False')
				else:
					return CustomRedirect(os.environ.get('FRONTEND_URL', '') + '?token_valid=False')

			if redirect_url and len(redirect_url) > 3:
				return CustomRedirect(
					redirect_url + '?token_valid=True&message=Credentials Valid&uidb64=' + uidb64 + '&token=' + token)
			else:
				return CustomRedirect(os.environ.get('FRONTEND_URL', '') + '?token_valid=False')

		except DjangoUnicodeDecodeError as identifier:
			try:
				if not PasswordResetTokenGenerator().check_token(user):
					return CustomRedirect(redirect_url + '?token_valid=False')

			except UnboundLocalError as e:
				return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)


class SetNewPasswordAPIView(generics.GenericAPIView):
	serializer_class = SetNewPasswordSerializer

	def patch(self, request):
		serializer = self.serializer_class(data=request.data)
		serializer.is_valid(raise_exception=True)
		return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    serializer_class = LogoutSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class GoogleSocialAuthView(GenericAPIView):

    serializer_class = GoogleSocialAuthSerializer

    def post(self, request):
        """
        POST with "auth_token"
        Send an idtoken as from google to get user information
        """

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = ((serializer.validated_data)['auth_token'])
        return Response(data, status=status.HTTP_200_OK)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = 'http://localhost:8000/accounts/google/login/callback/'
    client_class = OAuth2Client


class MainDeskDetail(APIView):
    queryset = MainDesk.objects.all()
    serializer_class = MainDeskSerializer
    permission_classes = (IsDeskOwner,)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk):
        desk_obj = MainDesk.objects.get(pk=pk, author=request.user)
        serializer = MainDeskSerializer(desk_obj)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=MainDeskSerializer)
    def put(self, request, pk):
        maindesk_obj = MainDesk.objects.get(pk=pk)
        serializer = MainDeskSerializer(data=request.data, instance=maindesk_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=MainDeskSerializer)
    def patch(self, request, pk):
        maindesk_obj = MainDesk.objects.get(pk=pk)
        serializer = MainDeskSerializer(data=request.data, instance=maindesk_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        object = MainDesk.objects.get(pk=pk)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MainDeskListCreateView(APIView):
    queryset = MainDesk.objects.all()
    serializer_class = MainDeskSerializer
    permission_classes = (IsDeskOwner,)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk=None):
        queryset = MainDesk.objects.filter(Q(author=request.user) | Q(members__user=request.user))
        if pk:
            maindesk_obj = queryset.get(pk=pk)
            serializer = MainDeskSerializer(maindesk_obj)
        else:
            is_favorite = request.GET.get('favorite', False)
            if is_favorite == 'True':
                favorites_id = request.user.favorites.all().values_list('desk', flat=True)
                queryset = queryset.filter(id__in=favorites_id)
            else:
                queryset = queryset.all()
            serializer = MainDeskSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=MainDeskSerializer)
    def post(self, request, format=None):
        serializer = MainDeskSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MainDeskArchiveList(APIView):
    permission_classes = (IsDeskOwner,)
    def get(self, request):
        archives_id = request.user.archives.all().values_list('desk', flat=True)
        queryset = MainDesk.objects.filter(id__in=archives_id)
        serializer = MainDeskSerializer(queryset, many=True)
        return Response(serializer.data)


class ColumnDetail(APIView):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    # permission_classes = (IsDeskOwner,)
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, desk_pk, column_pk):
        try:
            return Column.objects.get(desk_id=desk_pk, pk=column_pk)
        except Column.DoesNotExist:
            raise Http404

    def get(self, request, desk_pk, column_pk):
        column_obj = self.get_object(desk_pk, column_pk)
        serializer = ColumnSerializer(column_obj)

        return Response(serializer.data)

    @swagger_auto_schema(request_body=ColumnSerializer)
    def put(self, request, desk_pk, column_pk):
        column_obj = self.get_object(desk_pk, column_pk)
        serializer = ColumnSerializer(data=request.data, instance=column_obj)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=ColumnSerializer)
    def patch(self, request, desk_pk, column_pk):
        column_obj = self.get_object(desk_pk, column_pk)
        serializer = ColumnSerializer(data=request.data, instance=column_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, desk_pk, column_pk, format=None):
        object = self.get_object(desk_pk, column_pk)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ColumnListCreateView(APIView):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = (IsDeskOwner,)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, desk_pk):
        column_obj = Column.objects.filter((Q(desk__author=request.user) | Q(desk__members__user=request.user)) & (Q(desk_id=desk_pk)))
        for column in column_obj:
            self.check_object_permissions(request, column.desk)

        serializer = ColumnSerializer(column_obj, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=ColumnSerializer)
    def post(self, request, desk_pk):
        desk = MainDesk.objects.get(pk=request.data['desk'])
        self.check_object_permissions(request, desk)
        serializer = ColumnSerializer(data=request.data, context={'request': request, 'desk_pk': desk_pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardDetail(APIView):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = (IsDeskOwnerOrMember,)
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, column_pk, card_pk):
        try:
            return Card.objects.get(column_id=column_pk, pk=card_pk)
        except Card.DoesNotExist:
            raise Http404

    def get(self, request, column_pk, card_pk):
        card_obj = self.get_object(column_pk, card_pk)
        serializer = CardSerializer(card_obj)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CardSerializer)
    def put(self, request, column_pk, card_pk):
        card_obj = self.get_object(column_pk, card_pk)
        serializer = CardSerializer(data=request.data, instance=card_obj)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CardSerializer)
    def patch(self, request, column_pk, card_pk):
        card_obj = self.get_object(column_pk, card_pk)
        serializer = CardSerializer(data=request.data, instance=card_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, column_pk, card_pk):
        object = self.get_object(column_pk, card_pk)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CardListCreateView(APIView):
    queryset = Card.objects.all()
    serializer_class = CardSerializer
    permission_classes = (IsDeskOwner,)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, column_pk, *args, **kwargs):
        card_obj = Card.objects.filter(
            (Q(column__desk__author=request.user) | Q(column__desk__members__user=request.user)) & (Q(column_id=column_pk)))
        for card in card_obj:
            self.check_object_permissions(request, card.column.desk)
        serializer = CardSerializer(card_obj, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CardSerializer)
    def post(self, request, column_pk, format=None):
        serializer = CardSerializer(data=request.data, context={'request': request, 'column_pk': column_pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FavouriteDetail(APIView):
    serializer_class = FavouriteSerializer

    def get(self, request):
        queryset = MainDeskFavorites.objects.all()
        serializer = FavouriteSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FavouriteSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateComment(APIView):
    serializer_class = CommentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        queryset = Comment.objects.all()
        serializer = CommentSerializer(queryset, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CommentSerializer)
    def post(self, request):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SendInvite(APIView):
    queryset = User.objects.all()

    def post(self, request, *args, **kwargs):
        invite_to_register = []
        invite_to_desk = []

        emails = request.data.get('emails')
        desk_id = request.data.get('desk_id')

        for email in emails:
            user = User.objects.filter(email=email).first()
            if user is None:
                invite_to_register.append(email)
            else:
                invite_to_desk.append(email)

        send_mail(
            'Subject',
            'register!!!.',
            'nuraika.obozkanova@gmail.com',
            invite_to_register,
            fail_silently=False,

        )
        send_mail(
            'Subject',
            f'Invite to desk!!! {desk_id}',
            'nuraika.obozkanova@gmail.com',
            invite_to_desk,
            fail_silently=False,
        )

        return Response({'status': 'good'})


class AcceptInvite(APIView):
    def post(self, request, desk_id):
        pass


class CheckListCreateView(APIView):
    queryset = CheckList.objects.all()
    serializer_class = CheckListSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, *args, **kwargs):
        checklist_obj = CheckList.objects.filter(
            Q(card__column__desk__author=request.user) | Q(card__column__desk__members__user=request.user))
        for checklist in checklist_obj:
            self.check_object_permissions(request, checklist.card.column.desk)
        serializer = CheckListSerializer(checklist_obj, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=CheckListSerializer)
    def post(self, request, format=None):
        checklist = Card.objects.get(pk=request.data['card']).column.desk
        self.check_object_permissions(request, checklist)
        serializer = CheckListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckListDetail(APIView):
    queryset = CheckList.objects.all()
    serializer_class = CheckListSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return CheckList.objects.get(pk=pk)
        except CheckList.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        checklist_obj = self.get_object(pk=pk)
        serializer = CheckListSerializer(checklist_obj)

        return Response(serializer.data)

    @swagger_auto_schema(request_body=CheckListSerializer)
    def put(self, request, pk):
        card_obj = self.get_object(pk=pk)
        serializer = CheckListSerializer(data=request.data, instance=card_obj)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=CheckListSerializer)
    def patch(self, request, pk):
        checklist_obj = self.get_object(pk=pk)
        serializer = CheckListSerializer(data=request.data, instance=checklist_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        object = self.get_object(pk)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MetkiCreateView(APIView):
    queryset = Metki.objects.all()
    serializer_class = MetkiSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, card_pk, *args, **kwargs):

        metki_obj = Metki.objects.filter(
            (Q(card__column__desk__author=request.user) | Q(card__column__desk__members__user=request.user)) & (Q(card_id=card_pk)))
        for metki in metki_obj:
            self.check_object_permissions(request, metki.card.column.desk)
        serializer = MetkiSerializer(metki_obj, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=MetkiSerializer)
    def post(self, request, card_pk, format=None):
        serializer = MetkiSerializer(data=request.data, context={'request': request, 'card_pk': card_pk})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MetkiDetail(APIView):
    queryset = Metki.objects.all()
    serializer_class = MetkiSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_object(self, pk):
        try:
            return Metki.objects.get(pk=pk)
        except Metki.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        metki_obj = self.get_object(pk=pk)
        serializer = MetkiSerializer(metki_obj)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=MetkiSerializer)
    def put(self, request, pk):
        metki_obj = self.get_object(pk=pk)
        serializer = MetkiSerializer(data=request.data, instance=metki_obj)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=MetkiSerializer)
    def patch(self, request, pk):
        metki_obj = self.get_object(pk=pk)
        serializer = MetkiSerializer(data=request.data, instance=metki_obj, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        object = self.get_object(pk)
        object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

