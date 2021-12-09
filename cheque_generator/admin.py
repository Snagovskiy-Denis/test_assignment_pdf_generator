from django.contrib import admin

from .models import *


class PrinterAdmin(admin.ModelAdmin):
    list_display = ('api_key', 'name', 'check_type', 'point_id')


class CheckAdmin(admin.ModelAdmin):
    list_display = ('id', 'status', 'type', 'printer_id')


admin.site.register(Printer, PrinterAdmin)
admin.site.register(Check, CheckAdmin)
