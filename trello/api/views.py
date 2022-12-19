from django.db.models import Q
from django.http import Http404
from rest_auth.registration.views import SocialLoginView
from trello.api.serializers import *
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from trello.api.permissions import IsDeskOwnerOrMember, IsDeskOwner
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser


# class GoogleLogin(SocialLoginView):
#     adapter_class = GoogleOAuth2Adapter
#     callback_url = 'http://localhost:8000/accounts/google/login/callback/'
#     client_class = OAuth2Client


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
    permission_classes = (IsDeskOwnerOrMember,)
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, column_pk, *args, **kwagrs):
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
    queryset = CustomUser.objects.all()

    def post(self, request, *args, **kwargs):
        invite_to_register = []
        invite_to_desk = []

        emails = request.data.get('emails')
        desk_id = request.data.get('desk_id')

        for email in emails:
            user = CustomUser.objects.filter(email=email).first()
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

    def get(self, request, *args, **kwagrs):
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

    def get(self, request, card_pk, *args, **kwagrs):

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