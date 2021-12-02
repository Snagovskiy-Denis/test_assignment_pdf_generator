from django.shortcuts import render

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.views import APIView
from rest_framework import status, generics
from rest_framework.serializers import ValidationError


@api_view(['GET'])
def new_checks(request):
    '''List checks available for printing'''
    return Response(data={'checks': []}, content_type='application/json')
