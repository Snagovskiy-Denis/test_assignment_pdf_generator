from django.test import TestCase
from unittest.mock import patch

from cheque_generator.models import Check
from cheque_generator.tasks import convert_check_html_file_to_pdf, create_pdf_for_check, generate_html_check, save_pdf_file

from functional_test import FunctionalTest


@patch('cheque_generator.tasks.requests')
class CreatePdfTask(TestCase):
    fixtures = ['printers', 'checks_for_non_testing_printers']

    def setUp(self) -> None:
        self.check_kitchen: Check = Check.objects.get(id=1)
        self.check_client: Check = Check.objects.get(id=2)
        return super().setUp()

    def test_generate_html_check_for_kitchen(self, _):
        template = generate_html_check(check=self.check_kitchen)
        self.assertIn('Чек для кухни', template)
        for item in self.check_kitchen.order['items']:
            self.assertIn(item['name'], template)
        price = self.check_kitchen.order['price']
        self.assertIn(f'<td>{price}</td>', template)

    def test_generate_html_check_for_client(self, _):
        template = generate_html_check(check=self.check_client)
        self.assertIn('Чек для клиента', template)
        for item in self.check_kitchen.order['items']:
            self.assertIn(item['name'], template)
        price = self.check_kitchen.order['price']
        self.assertIn(f'<td>{price}</td>', template)
        self.assertIn('Спасибо за заказ :)', template)

    def test_makes_request_to_wkhtmltopdf(self, mock_requests):
        template = ' <!DOCTYPE html> <html lang="en"> <head> <meta charset="UTF-8"> <title>Чек для клиента</title> <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css" integrity="sha384-Gn5384xqQ1aoWXA+058RXPxPg6 fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm" crossorigin="anonymous"> <style> @page { size: A4; margin: 1cm; } body { width: 210mm; font-size: 14px; height: 297mm; } </style> </head> <body> <div class="container"> <div class="row"> <h2 class="col col-3">№ 2</h2> <h3 class="col col-6">г. Уфа, ул. Ленина, д. 42</h3> <div class="col col-3"> <ul class="list-unstyled"> <li class="font-weight-bold">Иван</li> <li>9173332222</li> </ul> </div> </div> <div class="row"> <table class="table" width="830px"> <thead> <tr> <th>Название</th> <th>Количество</th> <th>Цена за единицу</th> </tr> </thead> <tbody> <tr> <td>Вкусная пицца</td> <td>2</td> <td>250</td> </tr> <tr> <td>Не менее вкусные роллы</td> <td>1</td> <td>280</td> </tr> <tr> <td></td> <td>ИТОГО:</td> <td>780</td> </tr> </tbody> </table> </div> </div> <div class="jumbotron"> <h2>Спасибо за заказ :)</h2> </div> </body> </html> '
        convert_check_html_file_to_pdf(html_file_content=template)

        mock_requests.post.assert_called_once()
        mock_call = mock_requests.post.mock_calls[0]
        self.assertIn('http://localhost:80/', mock_call.args)

        headers = mock_call.kwargs['headers']
        self.assertEqual({'Content-Type': 'application/json'}, headers)

        data = mock_call.kwargs['data']
        self.assertIn('contents', data)

    @patch('builtins.open')
    def test_saves_(self, mock_open, _):
        save_pdf_file(self.check_kitchen, b'')
        mock_open.assert_called_once_with('/media/pdf/1_kitchen.pdf', 'wb')


class CreatePdfFileFunctionalTest(FunctionalTest):

    @patch.object(Check, 'save')
    @patch('cheque_generator.tasks.save_pdf_file', return_value='/media/pdf/1_kitchen.pdf')
    @patch('cheque_generator.tasks.requests')
    def test_assign_pdf_file_to_check(self, _, mock_file_path, mock_save):
        check = Check.objects.get(id=1)
        self.assertEqual('', check.pdf_file.name)

        create_pdf_for_check(check)

        self.assertEqual(mock_file_path.return_value, check.pdf_file.name)
        mock_save.assert_called_once_with()
