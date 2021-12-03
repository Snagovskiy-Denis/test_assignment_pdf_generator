from django.shortcuts import render
from rest_framework.exceptions import AuthenticationFailed

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.serializers import ValidationError

from cheque_generator.models import Check, Printer
from cheque_generator.serializers import CheckSerializer
from cheque_generator.tasks import create_pdf_for_check


class NewChekcs(APIView):
    '''List checks available for printing'''

    def get(self, request, format=None):
        api_key = request.query_params.get('api_key')

        if not Printer.objects.filter(api_key=api_key):
            # AuthenticationFailed don't return 401 because of standards
            # raise AuthenticationFailed(code=status.HTTP_401_UNAUTHORIZED)
            msg = {'error': 'Не существует принтера с таким api_key'}
            return Response(msg, status.HTTP_401_UNAUTHORIZED)

        checks = Check.objects.filter(printer_id=api_key)
        serializer = CheckSerializer(checks, many=True)
        return Response({'checks': serializer.data}, status.HTTP_200_OK)


class CreateChecks(APIView):
    '''Creates checks for orders and generates pdf-documents for them'''

    def post(self, request, format=None):
        point_id = int(request.data.get('point_id', -1))
        point_printers = Printer.objects.filter(point_id=point_id)

        for printer in point_printers:
            data = {
                'printer_id': printer.api_key,
                'type': printer.check_type,
                'status': 'new',
                'order': request.data,
            }
            serializer = CheckSerializer(data=data)

            if not serializer.is_valid():
                raise Exception(serializer.error)

            serializer.save()
            create_pdf_for_check(serializer.data)

        return Response({'ok': 'Чеки успешно созданы'}, status.HTTP_200_OK)
