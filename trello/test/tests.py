from django.core.files import File
from rest_framework import status
from rest_framework.reverse import reverse_lazy
from rest_framework.test import APITestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.contrib.auth import get_user_model
from trello.models import MainDesk, Column, Card, Comment

User = get_user_model()


class TestMainDeskAPI(APITestCase):

    def test_anonymous_cannot_see_desks(self):
        response = self.client.get(reverse("desk"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


def test_swagger_accessible_by_admin(admin_client):
    url = reverse("api-docs")
    response = admin_client.get(url)
    assert response.status_code == 200


# @pytest.mark.django_db
def test_swagger_ui_not_accessible_by_normal_user(client):
    url = reverse("api-docs")
    response = client.get(url)
    assert response.status_code == 403


def test_api_schema_generated_successfully(admin_client):
    url = reverse("api-schema")
    response = admin_client.get(url)
    assert response.status_code == 200


class MainDeskTestView(APITestCase):

    def setUp(self):
        self.desk_url = reverse('desk')
        self.user1 = User(email="juliana@dev.io", password="some_pass")
        self.user1.save()

    def get_user(self, pk):
        return User.objects.get(pk=pk)

    def test_desk_GET_request(self):
        self.client.force_authenticate(user=self.user1)
        desk = MainDesk(title='Desk1', author=self.user1)
        desk.save()
        request = self.client.get(self.desk_url)
        self.assertEqual(desk.title, 'Desk1')
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_create_desk(self):
        self.client.force_authenticate(user=self.user1)
        file = File(open('media/images/naryn-03.jpeg', 'rb'))
        uploaded_file = SimpleUploadedFile('new_image.jpg', file.read(), content_type='multipart/form-data')
        url = reverse('desk')
        payload = {
            'title': 'testdesk',
            'author': self.user1,
            'created_date': '2016-06-21T03:02:00.776594Z',
            'image': uploaded_file,
        }
        response = self.client.post(url, payload)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_PUT_request(self):
        self.client.force_authenticate(user=self.user1)
        file = File(open('media/images/naryn-03.jpeg', 'rb'))
        uploaded_file = SimpleUploadedFile('new_image.jpg', file.read(), content_type='multipart/form-data')
        url = reverse('desk')
        payload = {
            'title': 'testdesk',
            'author': self.user1,
            'created_date': '2016-06-21T03:02:00.776594Z',
            'image': uploaded_file,
        }
        self.client.post(url, payload)
        desk = MainDesk.objects.first()
        request = self.client.put(reverse_lazy('update-api-desk', kwargs={'pk': desk.pk}),
                                    payload={'title': 'Changed'}, follow=True)
        changed = MainDesk.objects.first()
        self.assertEqual(MainDesk.objects.count(), 1)
        self.assertEqual(changed.title, 'testdesk')
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_DELETE_request(self):
        self.client.force_authenticate(user=self.user1)
        file = File(open('media/images/naryn-03.jpeg', 'rb'))
        uploaded_file = SimpleUploadedFile('new_image.jpg', file.read(), content_type='multipart/form-data')
        url = reverse('desk')
        payload = {
            'title': 'testdesk',
            'author': self.user1,
            'created_date': '2016-06-21T03:02:00.776594Z',
            'image': uploaded_file,
        }
        self.client.post(url, payload)
        desk = MainDesk.objects.first()
        request = self.client.delete(reverse_lazy('update-api-desk', kwargs={'pk': desk.pk}), follow=True)
        self.assertEqual(MainDesk.objects.count(), 0)
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)

def create_desk_instance(self):
    desk = MainDesk(title='some title', author=self.user1)
    desk.save()
    return desk


def create_column_instance(self, desk):
    column = Column(title='New Column Name', desk=self.desk)
    column.save()
    return column


def create_card_instance(self):
    card = Card(title='New Card Name', author=self.user1, column=self.column, content='card1', date_created='2022-06-21T03:02:00.776594Z', deadline='2022-12-21T03:02:00.776594Z', choice='red',)
    card.save()
    return card


class ColumnTest(APITestCase):
    def setUp(self):
        self.user1 = User(email="juliana@dev.io", password="some_pass")
        self.user1.save()
        self.desk = MainDesk.objects.create(title='desk1', author=self.user1,)
        self.column_url = reverse('api-column', kwargs={'desk_pk': self.desk.pk})
        self.data = {'desk': self.desk.id, 'title': 'column1'}

    def test_can_create_column(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.column_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_GET_request(self):
        self.client.force_authenticate(user=self.user1)
        desk = create_desk_instance(self)
        column = create_column_instance(self, desk)
        request = self.client.get(self.column_url)
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_PUT_request(self):

        self.client.force_authenticate(user=self.user1)
        desk = create_desk_instance(self)
        second = MainDesk(title='Second Board', author=self.user1)
        second.save()
        column = create_column_instance(self, desk)
        request = self.client.put(reverse_lazy('api-detail-column', kwargs={'desk_pk': self.desk.pk, 'column_pk': column.pk}),
                                  data={'title': 'PUT NAME', 'desk': desk.pk})
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_DELETE_request(self):
        self.client.force_authenticate(user=self.user1)
        desk = create_desk_instance(self)
        column = create_column_instance(self, desk)
        request = self.client.delete(reverse_lazy('api-detail-column', kwargs={'desk_pk': self.desk.pk, 'column_pk': column.pk}))
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)


class CardTest(APITestCase):
    def setUp(self):
        self.user1 = User(email="juliana@dev.io", password="some_pass")
        self.user1.save()
        file = File(open('media/documents/2022/12/11/base.txt', 'rb'))
        uploaded_file = SimpleUploadedFile('doc.txt', file.read(), content_type='multipart/form-data')
        self.desk = MainDesk.objects.create(title='desk1', author=self.user1,)
        self.column = Column.objects.create(title='col1', desk=self.desk,)
        self.card_url = reverse('api-card', kwargs={'column_pk': self.column.pk})
        self.data = {'column': self.column.id,
                     'author': self.user1,
                     'title': 'card1',
                     'content': 'card1',
                     'date_created': '2022-06-21T03:02:00.776594Z',
                     'deadline': '2022-12-21T03:02:00.776594Z',
                     'choice': 'red',
                     'docfile': uploaded_file,
                     }

        self.data.update({'title': 'Changed'})

    def test_can_create_card(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.card_url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_GET_request(self):
        self.client.force_authenticate(user=self.user1)
        request = self.client.get(self.card_url)
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_PUT_request(self):
        self.client.force_authenticate(user=self.user1)
        card = create_card_instance(self)
        request = self.client.put(reverse_lazy('api-detail-card', kwargs={'column_pk': self.column.pk, 'card_pk': card.pk}),
                                  data=self.data)
        self.assertEqual(request.status_code, status.HTTP_200_OK)

    def test_DELETE_request(self):
        self.client.force_authenticate(user=self.user1)
        card = create_card_instance(self)
        request = self.client.delete(reverse_lazy('api-detail-card', kwargs={'column_pk': self.column.pk, 'card_pk': card.pk}))
        self.assertEqual(request.status_code, status.HTTP_204_NO_CONTENT)


class CreateCommentTest(APITestCase):
    def setUp(self):
        self.user1 = User(email="juliana@dev.io", password="some_pass")
        self.user1.save()
        self.desk = MainDesk.objects.create(title='desk1', author=self.user1, )
        self.column = Column.objects.create(title='col1', desk=self.desk, )
        self.card = Card.objects.create(title='card1', author=self.user1, column=self.column)
        self.comment_url = reverse('api-comment')
        self.data = {'author': self.user1,
                     'body': 'comment1',
                     'entry': self.card.pk,
                     'created_on': '2022-06-21T03:02:00.776594Z',
                     }
        self.data.update({'body': 'Changed'})

    def test_can_create_comment(self):
        response = self.client.post(reverse('api-comment'), self.data)
        print(response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_can_read_comment_list(self):
        response = self.client.get(reverse('api-comment'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

