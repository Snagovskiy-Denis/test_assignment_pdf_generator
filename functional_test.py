from unittest.mock import patch
from hashlib import sha256
from time import sleep
from pathlib import Path

from rest_framework.test import APITestCase


class FunctionalTest(APITestCase):
    fixtures = ['printers', 'checks_for_non_testing_printers']

    kitchen_printer_api_key: str = sha256(b'kitchen_printer').hexdigest()
    client_printer_api_key: str = sha256(b'client_printer').hexdigest()

    def assertIsPdfFile(self, response) -> None:
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('.pdf', response['Content-Disposition'])

    def assertNoNewChecksForPrinter(self, api_key: str) -> None:
        printer_checks = self.get_new_checks_for_printer(api_key)
        num_of_checks = len(printer_checks)
        self.assertEqual(num_of_checks, 0)

    def get_new_checks_for_printer(self, api_key: str) -> dict:
        path = '/new_checks/'
        data = {'api_key': api_key}
        return self.client.get(path=path, data=data).json().get('checks')


@patch('cheque_generator.tasks.save_pdf_file')
class TestAssignment(FunctionalTest):

    def test_create_and_print_new_checks_for_point_with_2_printers(
            self, mock_save_pdf_file):

        directory = 'cheque_generator/templates/'
        filenames = ('kitchen_check.html', 'client_check.html')
        fake_files = [directory + file for file in filenames]
        mock_save_pdf_file.side_effect = fake_files

        self.assertNoNewChecksForPrinter(self.kitchen_printer_api_key)
        self.assertNoNewChecksForPrinter(self.client_printer_api_key)

        new_order_data = {
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
            'point_id': '1'
        }
        check_oder_id = new_order_data['id']
        self.client.post(path='/create_checks/', data=new_order_data, format='json')

        for api_key in self.kitchen_printer_api_key, self.client_printer_api_key:
            new_checks = self.get_new_checks_for_printer(api_key)
            self.assertEqual(len(new_checks), 1)
            check = new_checks[0]
            self.assertEqual(check['order']['id'], check_oder_id)

            check_data = { 'api_key': api_key, 'check_id': check['id'] }
            response = self.client.get(path='/check/', data=check_data)
            self.assertIsPdfFile(response)

            self.assertNoNewChecksForPrinter(api_key)
