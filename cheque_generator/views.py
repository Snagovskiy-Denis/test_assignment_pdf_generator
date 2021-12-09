from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from drf_pdf.response import PDFFileResponse
from drf_pdf.renderer import PDFRenderer
from cheque_generator.exceptions import CheckDoesNotExist, CheckPdfFileDoesNotExist

from cheque_generator.models import Check, Printer
from cheque_generator.serializers import CheckSerializer
from cheque_generator.tasks import create_pdf_for_check
from cheque_generator.exceptions import *


class ValidatePrinterMixin:
    '''Checks if printer with given api_key exist and raise error if not

    Printer' api_key for validation is gotten from HTTP-request GET parameters
    '''

    def get(self, *args, **kwargs):
        api_key = self.request.query_params.get('api_key')
        try:
            Printer.objects.get(api_key=api_key)
        except Printer.DoesNotExist:
            raise PrinterDoesNotExist()
        return super().get(args, kwargs)


class NewChecksView(ValidatePrinterMixin, generics.ListAPIView):
    '''List checks available for printing'''
    queryset = Check.objects.all()
    serializer_class = CheckSerializer

    def filter_queryset(self, queryset):
        api_key = self.request.query_params.get('api_key')
        return queryset.filter(printer_id__api_key=api_key, status='new')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data = {'checks': response.data}
        return response


class CreateChecksView(APIView):
    '''Creates checks for orders and generates pdf-documents for them'''

    def get_all_printers_on_point(self):
        point_id = self.request.data.get('point_id', '')
        if not type(point_id) == int and not point_id.isnumeric():
            msg = {'order': 'point_id должен быть целым числом'}
            raise PointException(msg)

        point_printers = Printer.objects.filter(point_id=point_id)
        if not point_printers:
            msg = {'error': 'Для данной точки не настроено ни одного принтера'}
            raise PointException(msg)
        return point_printers

    def post(self, request, format=None):
        checks = []
        for printer in self.get_all_printers_on_point():
            checks.append({
                'printer_id': printer.api_key,
                'type': printer.check_type,
                'status': 'new',
                'order': request.data,
            })

        serializer = CheckSerializer(data=checks, many=True)

        if not serializer.is_valid():
            msg = serializer.errors
            for check in serializer.errors:
                for error in check.get('non_field_errors'):
                    if error and error.code == 'unique':
                        msg = {'order': 'Для данного заказа уже созданы чеки'}
            raise CheckError(msg)

        for created_check in serializer.save():
            create_pdf_for_check(created_check)

        return Response({'ok': 'Чеки успешно созданы'}, status.HTTP_200_OK)


class CheckView(ValidatePrinterMixin, generics.RetrieveAPIView):
    '''Return pdf-file of requested Check object'''

    render_classes = (PDFRenderer, )

    def get_object(self):
        check_id = self.request.query_params.get('check_id')
        try:
            return Check.objects.get(id=check_id)
        except Check.DoesNotExist:
            raise CheckDoesNotExist()

    def retrieve(self, request, *args, **kwargs):
        check = self.get_object()

        if not check.pdf_file.name: raise CheckPdfFileDoesNotExist()

        check.status = Check.CheckStatus.PRINTED
        check.save()

        return PDFFileResponse(
            file_path=check.pdf_file.name,
            status=status.HTTP_200_OK
        )
