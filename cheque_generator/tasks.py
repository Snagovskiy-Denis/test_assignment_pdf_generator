# Create your tasks here

from celery import shared_task


@shared_task
def create_pdf_for_check(check):
    # file_name = '{raw_data.get("id")}_{printer.check_type}.pdf'
    pass
