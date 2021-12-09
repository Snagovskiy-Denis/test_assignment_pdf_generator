from django.db import models
from django.core.exceptions import ValidationError

from asynchronous_workers.settings import CHECK_FILES_DIR


class CheckTypes(models.TextChoices):
    KITCHEN = 'kitchen'
    CLIENT = 'client'


class Printer(models.Model):
    name = models.CharField(max_length=100)
    api_key = models.CharField(max_length=64, primary_key=True)
    check_type = models.CharField(max_length=7, choices=CheckTypes.choices)
    point_id = models.IntegerField()

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.api_key=})'


class Check(models.Model):
    class CheckStatus(models.TextChoices):
        NEW = 'new'
        RENDERED = 'rendered'
        PRINTED = 'printed'

    printer_id = models.ForeignKey(Printer, on_delete=models.CASCADE)
    type = models.CharField(max_length=7, choices=CheckTypes.choices)
    order = models.JSONField()
    status = models.CharField(max_length=8, choices=CheckStatus.choices)
    pdf_file = models.FileField(blank=True, upload_to=CHECK_FILES_DIR)

    def __str__(self) -> str:
        printer_api_key = self.printer_id.api_key
        return f'{self.__class__.__name__}({self.id=}, {printer_api_key=})'

    def clean(self) -> None:
        if self.printer_id.check_type != self.type:
            msg = 'Printer with api "{}" ' \
                  'prints {} checks, but {} check was passed'
            api = self.printer_id.api_key
            printer_type = self.printer_id.check_type
            raise ValidationError(msg.format(api, printer_type, self.type))

    class Meta:
        unique_together = ('order', 'printer_id')
