from django.shortcuts import render
from rest_framework.exceptions import AuthenticationFailed

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.serializers import ValidationError
from drf_pdf.response import PDFFileResponse
from drf_pdf.renderer import PDFRenderer

from cheque_generator.models import Check, Printer
from cheque_generator.serializers import CheckSerializer
from cheque_generator.tasks import create_pdf_for_check


class NewChekcsView(APIView):
    '''List checks available for printing'''

    def get(self, request, format=None):
        api_key = request.query_params.get('api_key')

        if not Printer.objects.filter(api_key=api_key):
            # AuthenticationFailed don't return 401 because of standards
            # raise AuthenticationFailed(code=status.HTTP_401_UNAUTHORIZED)
            msg = {'error': 'Не существует принтера с таким api_key'}
            return Response(msg, status.HTTP_401_UNAUTHORIZED)

        checks = Check.objects.filter(printer_id=api_key, status='new')
        serializer = CheckSerializer(checks, many=True)
        return Response({'checks': serializer.data}, status.HTTP_200_OK)


class CreateChecksView(APIView):
    '''Creates checks for orders and generates pdf-documents for them'''

    def post(self, request, format=None):
        point_id = request.data.get('point_id', '')
        if not type(point_id) == int and not point_id.isnumeric():
            msg = {'order': 'point_id должен быть целым числом'}
            return Response(msg, status.HTTP_400_BAD_REQUEST)

        point_printers = Printer.objects.filter(point_id=point_id)

        if not point_printers:
            msg = {'error': 'Для данной точки не настроено ни одного принтера'}
            return Response(msg, status.HTTP_400_BAD_REQUEST)

        for printer in point_printers:
            data = {
                'printer_id': printer.api_key,
                'type': printer.check_type,
                'status': 'new',
                'order': request.data,
            }
            serializer = CheckSerializer(data=data)

            if not serializer.is_valid():
                msg = serializer.errors
                if serializer.errors.get('non_field_errors'):
                    msg = {'order': 'Для данного заказа уже созданы чеки'}
                return Response(msg, status.HTTP_400_BAD_REQUEST)

            check = serializer.save()
            create_pdf_for_check(check)

        msg = {'ok': 'Чеки успешно созданы'}
        return Response(msg, status.HTTP_200_OK)


class CheckView(APIView):
    '''Return pdf-file of requested Check object'''

    render_classes = (PDFRenderer, )

    def get(self, request, format=None):
        api_key = request.query_params.get('api_key')

        try:
            printer = Printer.objects.get(api_key=api_key)
        except Printer.DoesNotExist:
            # AuthenticationFailed don't return 401 because of standards
            # raise AuthenticationFailed(code=status.HTTP_401_UNAUTHORIZED)
            msg = {'error': 'Не существует принтера с таким api_key'}
            return Response(msg, status.HTTP_401_UNAUTHORIZED)

        check_id = request.query_params.get('check_id')

        try:
            check = Check.objects.get(printer_id=printer.api_key, id=check_id)
        except Check.DoesNotExist:
            msg = {'error': 'Данного чека не существует'}
            return Response(msg, status.HTTP_400_BAD_REQUEST)

        if not check.pdf_file.name:
            msg = {'error': 'Для данного чека не сгенерирован PDF-файл'}
            return Response(msg, status.HTTP_400_BAD_REQUEST)

        check.status = Check.CheckStatus.PRINTED
        check.save()

        return PDFFileResponse(
            file_path=check.pdf_file.name,
            status=status.HTTP_200_OK
        )
