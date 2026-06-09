from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('materials/', views.materials_list, name='materials'),
    path('materials/delete/<int:pk>/', views.delete_material, name='delete_material'),
    path('tasks/', views.tasks_list, name='tasks'),
    path('tasks/update/<int:pk>/', views.update_task_status, name='update_task_status'),
    path('team/', views.team_list, name='team'),
    path('api/chat/', views.ai_chat, name='ai_chat'),
]
