from django.urls.conf import path

from . import views


urlpatterns = [
        path('create_checks/', lambda request: None),
        path('new_checks/', views.new_checks),
        path('check/', lambda request: None),
]
