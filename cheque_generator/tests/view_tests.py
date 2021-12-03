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
    data = {'api_key': sha256(b'test').hexdigest()}
    api_key = sha256(b'test').hexdigest()

    def test_get_returns_200_with_json_content_type(self):
        response = self.client.get(path=self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/json')

    def test_get_returns_list_of_checks(self):
        response = self.client.get(path=self.url, data=self.data)
        response_checks = response.json().get('checks')
        response_checks_ids = [check['id'] for check in response_checks]
        check1 = Check.objects.get(printer_id=self.api_key, type='kitchen')
        check2 = Check.objects.get(printer_id=self.api_key, type='client')
        self.assertIn(check1.id, response_checks_ids)
        self.assertIn(check2.id, response_checks_ids)

    def test_get_with_invalid_api_key_returns_401(self):
        invalid_data = {'api_key': '1' * 64}
        response = self.client.get(path=self.url, data=invalid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        expected = {'error': 'Не существует принтера с таким api_key'}
        self.assertEqual(expected, response.json())


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
