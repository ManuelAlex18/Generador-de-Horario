from django.contrib import admin
from .models import Asignatura, Periodo, Profesor, Horario_Asignatura, Horario, Actividad, Dia, Semana, Balance_de_carga
# Register your models here.


admin.site.register(Asignatura)
admin.site.register(Periodo)
admin.site.register(Profesor)
admin.site.register(Horario)
admin.site.register(Horario_Asignatura)
admin.site.register(Actividad)
admin.site.register(Dia)
admin.site.register(Semana)
admin.site.register(Balance_de_carga)