from rest_framework.exceptions import APIException


class PrinterDoesNotExist(APIException):
    status_code = 401
    default_detail = {'error': 'Не существует принтера с таким api_key'}
    default_code = 'no_such_printer'


class CheckError(APIException):
    status_code = 400
    default_code = 'bad_request'


class CheckDoesNotExist(CheckError):
    default_detail = {'error': 'Данного чека не существует'}


class CheckPdfFileDoesNotExist(CheckError):
    default_detail = {'error': 'Для данного чека не сгенерирован PDF-файл'}
