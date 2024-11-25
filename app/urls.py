from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path("iniciar/", views.iniciar_sesion, name='iniciar'),
    path("registro/", views.registro, name='registro'),
    path("cerrar/", views.cerrar_sesion, name='cerrar'),
    path("horarios/", views.mostrar_horarios, name='horarios'),
    path("crear_horario/", views.crearHorario, name='crear_horario'),
    path("crear_horario/index/<int:id>/", views.index, name='index'),
    path("crear_horario/index/<int:id>/eliminar", views.eliminar_horario, name='eliminar_horario'),
    path("crear_asignatura/", views.crear_asignatura, name='crear_asignatura'),
    path("editar_asignatura/<int:id>/", views.editar_asignatura, name='editar_asignatura'),
    path("editar_asignatura/<int:id>/eliminar", views.eliminar_asignatura, name='eliminar_asignatura'),
    path("periodos/", views.mostrar_periodos, name='periodos'),
    path("crear_periodo/", views.crear_periodo, name='crear_periodo'),
    path("editar_periodo/<int:id>/", views.editar_periodo, name='editar_periodo'),
    path("editar_periodo/<int:id>/eliminar", views.eliminar_periodo, name='eliminar_periodo'),
    
]
