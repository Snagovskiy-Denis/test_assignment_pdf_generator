import json
import requests
from base64 import b64encode

from celery import shared_task
from django.template.loader import get_template

from cheque_generator.models import Check
from asynchronous_workers.settings import CHECK_FILES_DIR, CONVERTER_URL, MEDIA_ROOT


def generate_html_check(check: Check) -> str:
    '''Get check basic template, populate it by data and return it'''
    template_name = check.type + '_check.html'
    template = get_template(template_name)
    return template.render(check.order)


def convert_check_html_file_to_pdf(html_file_content: str) -> bytes:
    '''Send POST request to wkhtmltopdf container and returns bytes response

    For explanations about base64 encoding-decong process, see issue № 9:
    https://github.com/openlabs/docker-wkhtmltopdf-aas/issues/9
    '''
    bynary_string = bytearray(html_file_content, 'utf-8')
    base64_bytes = b64encode(bynary_string)
    decoded_file_string = base64_bytes.decode('utf-8')

    data = {'contents': decoded_file_string}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(CONVERTER_URL,
                             data=json.dumps(data),
                             headers=headers)

    return response.content


def save_pdf_file(check: Check, content: bytes) -> str:
    '''Save given content into check directory'''
    output_directory = MEDIA_ROOT + CHECK_FILES_DIR + '/'
    output_file_name = f'{check.id}_{check.type}.pdf'
    output_path = output_directory + output_file_name

    with open(output_path, 'wb') as pdf_file:
        pdf_file.write(content)

    return output_path


@shared_task
def create_pdf_for_check(check: Check) -> None:
    '''Creates new pdf file and attach its path to given Check object'''
    # Is there a point to call task as django signal?

    check_html_file = generate_html_check(check)

    pdf_file_bytes = convert_check_html_file_to_pdf(check_html_file)

    file_path = save_pdf_file(check, pdf_file_bytes)

    check.pdf_file.name = file_path
    check.save()
