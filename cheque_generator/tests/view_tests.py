from hashlib import sha256
from rest_framework.test import APITestCase
from rest_framework import status

from cheque_generator.models import Check


class CreateChecksTest(APITestCase):

    url = '/create_checks/'

    request_body = {
        'id':
        123456,
        'price':
        780,
        'items': [{
            'name': 'Вкусная пицца',
            'quantity': 2,
            'unit_price': 250
        }, {
            'name': 'Не менее вкусные роллы',
            'quantity': 1,
            'unit_price': 280
        }],
        'address':
        'г. Уфа, ул. Ленина, д. 42',
        'client': {
            'name': 'Иван',
            'phone': 9173332222
        },
        'point_id': 1
    }

    def test_post_creates_check_in_database(self):
        pass

    def test_post_creates_multiple_checks_in_database(self):
        pass

    def test_post_returns_400_if_this_order_checks_are_already_exists(self):
        pass

    def test_post_returns_400_if_there_is_no_printers_in_given_point(self):
        pass


class NewChecksTest(APITestCase):
    fixtures = ['printers', 'checks']

    url = '/new_checks/'
    data = {'api_key': sha256(b'test2').hexdigest()}

    def test_get_returns_200_with_json_content_type(self):
        response = self.client.get(path=self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_list_of_checks(self):
        response = self.client.get(path=self.url, data=self.data)
        expected = Check.objects.filter(printer_id=self.data['api_key'])
        actual = response.json().get('checks')
        self.assertEqual(expected, actual)

    def test_get_with_invalid_api_key_returns_401(self):
        pass


class CheckTestCase(APITestCase):
    fixtures = ['printers', 'checks']

    url = '/check/'

    def test_get_200_return_pdf_file(self):
        pass

    def test_get_returns_400_if_requested_check_does_not_exist(self):
        pass

    def test_get_returns_400_if_there_is_not_pdf_file_for_requested_check(self):
        pass

    def test_get_with_invalid_api_key_returns_401(self):
        pass
