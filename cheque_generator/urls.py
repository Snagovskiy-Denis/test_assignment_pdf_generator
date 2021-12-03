from django.urls.conf import path

from . import views


urlpatterns = [
        path('create_checks/', views.CreateChecks.as_view()),
        path('new_checks/', views.NewChekcs.as_view()),
        path('check/', lambda request: None),
]
