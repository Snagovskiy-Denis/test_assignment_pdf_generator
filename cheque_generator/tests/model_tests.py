from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from cheque_generator.models import Printer, Check, CheckTypes


class CheckTest(TestCase):
    def test_cannot_assign_to_printer_with_different_check_type(self):
        printer = Printer.objects.create(
            name='1',
            api_key='1' * 64,
            check_type=CheckTypes.CLIENT,
            point_id=1,
        )

        with self.assertRaises(ValidationError) as e:
            Check(
                printer_id=printer,
                type=CheckTypes.KITCHEN,
                order={'test': 1},
                status=Check.CheckStatus.NEW,
            ).full_clean()
        self.assertIn(f'prints {CheckTypes.CLIENT} checks', str(e.exception))
