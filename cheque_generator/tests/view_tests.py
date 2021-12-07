from unittest import skip
from unittest.mock import patch
from hashlib import sha256

from rest_framework.test import APITestCase
from rest_framework import status

from cheque_generator.models import Check, Printer


@patch('cheque_generator.views.create_pdf_for_check')
class CreateChecksTest(APITestCase):
    fixtures = ['printers']

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
        'point_id': '1',
    }

    def post_json(self, data: dict):
        return self.client.post(path=self.url, data=data, format='json')

    def test_post_returns_200_json(self, _):
        response = self.post_json(data=self.request_body)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual({'ok': 'Чеки успешно созданы'}, response.json())

    def test_post_creates_check_for_each_printer_on_point(
            self, mock_create_pdf_for_check):
        cheks_before_post = Check.objects.count()

        self.post_json(data=self.request_body)

        self.assertEqual(cheks_before_post + 2, Check.objects.count())
        for printer in Printer.objects.filter(point_id=1):
            self.assertEqual(printer.check_set.count(), 1)
            created_check = printer.check_set.first()
            self.assertTrue(created_check.type == printer.check_type)
            self.assertTrue(created_check.status == 'new')
            self.assertTrue(created_check.order == self.request_body)
        mock_create_pdf_for_check.assert_called()

    def test_post_calls_task_that_generate_pdf_file(
            self, mock_create_pdf_for_check):
        self.post_json(data=self.request_body)
        self.assertEqual(mock_create_pdf_for_check.call_count, 2)
        created_checks = Check.objects.all()
        for check in created_checks:
            mock_create_pdf_for_check.assert_any_call(check)

    def test_post_returns_400_if_this_order_checks_are_already_exists(
            self, mock_create_pdf_for_check):
        self.post_json(data=self.request_body)
        self.assertEqual(Check.objects.count(), 2)
        mock_create_pdf_for_check.assert_called()
        mock_create_pdf_for_check.reset_mock()

        response = self.post_json(data=self.request_body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Check.objects.count(), 2)
        excpected_msg = {'order': 'Для данного заказа уже созданы чеки'}
        self.assertEqual(response.json(), excpected_msg)
        mock_create_pdf_for_check.assert_not_called()

    def test_post_returns_400_if_there_is_no_printers_in_given_point(
            self, mock_create_pdf_for_check):
        invalid_request_body = self.request_body.copy()
        invalid_request_body['point_id'] = 999
        self.assertEqual(Printer.objects.filter(point_id=999).count(), 0)

        response = self.post_json(data=invalid_request_body)

        self.assertEqual(Check.objects.count(), 0)
        expected_msg = {'error': 'Для данной точки не настроено ни одного принтера'}
        self.assertEqual(response.json(), expected_msg)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_create_pdf_for_check.assert_not_called()

    def test_post_returns_400_if_point_id_is_not_numeric(
            self, mock_create_pdf_for_check):
        invalid_request_body = self.request_body.copy()
        invalid_request_body['point_id'] = 'R-3PO'
        response = self.post_json(data=invalid_request_body)
        self.assertEqual(Check.objects.count(), 0)
        expected_msg = {'order': 'point_id должен быть целым числом'}
        self.assertEqual(response.json(), expected_msg)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_create_pdf_for_check.assert_not_called()


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

    def test_do_not_return_printed_checks(self):
        data = {'api_key': Check.objects.get(id=5).printer_id.api_key}
        response = self.client.get(path=self.url, data=data)
        checks = response.json()['checks']
        self.assertEqual(len(checks), 1)
        check = checks[0]
        self.assertNotEqual(check['id'], 5)
        self.assertNotEqual(check['status'], 'printed')


class CheckTestCase(APITestCase):
    fixtures = ['printers', 'checks']

    url = '/check/'

    data = {'api_key': sha256(b'test').hexdigest(), 'check_id': 1}

    @skip
    def test_get_200_return_pdf_file(self):
        response = self.client.get(path=self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['content-type'], 'application/pdf')
        filename = 'filename="pdf/1_kitchen.pdf"'
        self.assertEqual(response['content-disposition'], filename)

    def test_get_returns_400_if_requested_check_does_not_exist(self):
        invalid_data = self.data.copy()
        invalid_data['check_id'] = 999
        self.assertEqual(Check.objects.filter(id=999).count(), 0)
        response = self.client.get(path=self.url, data=invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_msg = {'error': 'Данного чека не существует'}
        self.assertEqual(expected_msg, response.json())

    @patch('cheque_generator.views.Check')
    def test_get_returns_400_if_there_is_not_pdf_file_for_requested_check(
            self, mock_Check):
        mock_Check.objects.get().pdf_file.name.__bool__.return_value = False
        response = self.client.get(path=self.url, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        expected_msg = {'error': 'Для данного чека не сгенерирован PDF-файл'}
        self.assertEqual(expected_msg, response.json())

    def test_get_with_invalid_api_key_returns_401(self):
        invalid_data = {'api_key': '1' * 64, 'check_id': 1}
        response = self.client.get(path=self.url, data=invalid_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        expected_msg = {'error': 'Не существует принтера с таким api_key'}
        self.assertEqual(expected_msg, response.json())

    def test_changes_status_of_check_after_download(self):
        check = Check.objects.get(id=4)
        check.pdf_file.name = 'functional_test.py'
        check.save()
        self.assertEqual(check.status, 'new')
        data = {'api_key': check.printer_id.api_key, 'check_id': 4}
        response = self.client.get(path=self.url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Check.objects.get(id=4).status, 'printed')
