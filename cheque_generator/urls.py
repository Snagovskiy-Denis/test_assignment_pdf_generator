from django.urls.conf import path

from . import views


urlpatterns = [
        path('create_checks/', views.CreateChecksView.as_view()),
        path('new_checks/', views.NewChecksView.as_view()),
        path('check/', views.CheckView.as_view()),
]
