from django.urls.conf import path

from . import views


urlpatterns = [
        path('create_checks/', lambda request: None),
        path('new_checks/', views.NewChekcs.as_view()),
        path('check/', lambda request: None),
]
