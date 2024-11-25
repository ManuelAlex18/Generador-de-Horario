from django.db import models
import datetime
from datetime import timedelta, date
from django.core.validators import MinValueValidator, MaxValueValidator, ValidationError


    

# Create your models here.
class Asignatura(models.Model):
    nombre=models.CharField(max_length=30, unique=True)
    horas_clase=models.IntegerField()
    abreviatura=models.CharField(max_length=3)
    
    
    def __str__(self):
        return self.nombre



class Profesor(models.Model):
    nombre = models.CharField(max_length=40, unique=True)
    info = models.TextField()
    disponibilidad = models.BooleanField(default=False)
    asignaturas = models.ForeignKey(Asignatura, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre


class Periodo(models.Model):



    name = models.CharField(verbose_name=('nombre'),
                            max_length=50,
                            unique=True,
                            )

    start = models.DateField(verbose_name=('inicio'),)

    end = models.DateField(verbose_name=('fin'),)
    
    dias_sin_clase = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Días sin clase'
    )

    semanas_sin_clase = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Semanas sin clase'
    )

    class Meta:

        verbose_name = ("Periodo")
        verbose_name_plural = ("Periodo")
        ordering = ('start',)
        

    

    def __str__(self):
        return self.name

    def calcular_cantidad_semanas(self):
            # Asegurarse de que 'start' y 'end' son fechas válidas
            if not self.start or not self.end:
                return 0
            
            # Encuentra el primer lunes a partir de la fecha de inicio
            start_date = self.start
            while start_date.weekday() != 0:  # 0 es lunes
                start_date += timedelta(days=1)

            # Encuentra el último domingo antes de la fecha de fin
            end_date = self.end
            while end_date.weekday() != 0:  # 0 es lunes
                end_date += timedelta(days=1)

            # Calcula la cantidad de días totales entre start_date y end_date
            total_dias = (end_date - start_date).days + 1
            # Resta los días de las semanas sin clase
            if self.semanas_sin_clase:
                for semana in self.semanas_sin_clase:
                    semana_inicio = date.fromisoformat(semana['start'])
                    semana_fin = date.fromisoformat(semana['end'])
                    
                    # Calcula los días dentro del rango que deben restarse
                    if self.start <= semana_inicio <= self.end and self.start <= semana_fin <= self.end:
                        dias_semana = (semana_fin - semana_inicio).days + 1
                        total_dias -= dias_semana

            # Finalmente, convierte los días restantes a semanas completas
            total_semanas = total_dias // 7
            return total_semanas

    def obtener_dias_sin_clase_info(self):
        """ Devuelve una lista de diccionarios con información sobre días sin clase """
        if not self.dias_sin_clase:
            return []

        # Convertir semanas sin clase a un conjunto de tuplas (start, end)
        semanas_sin_clase_rango = []
        for semana in self.semanas_sin_clase:
            inicio = date.fromisoformat(semana['start'])
            fin = date.fromisoformat(semana['end'])
            semanas_sin_clase_rango.append((inicio, fin))

        resultado = []
        # Encuentra el primer lunes a partir de la fecha de inicio
        start_date = self.start
        while start_date.weekday() != 0:  # 0 es lunes
            start_date += timedelta(days=1)

        # Iterar sobre cada día sin clase
        for dia_str in self.dias_sin_clase:
            dia = date.fromisoformat(dia_str)
            if self.start <= dia <= self.end:
                # Verificar si el día está en una semana sin clase
                en_semana_sin_clase = any(inicio <= dia <= fin for inicio, fin in semanas_sin_clase_rango)

                if not en_semana_sin_clase:
                    # Calcula los días transcurridos desde el inicio del periodo
                    dias_transcurridos = (dia - start_date).days

                    # Caso 1: Verificar si el día sin clase está antes de la primera semana sin clases
                    semanas_antes = [inicio for inicio, _ in semanas_sin_clase_rango if dia < inicio]
                    
                    # Verificación y depuración
                    

                    if semanas_antes:
                        # Calcular las semanas transcurridas normalmente, ya que el día está antes de la primera semana sin clase
                        semanas_transcurridas = dias_transcurridos // 7
                    else:
                        # Caso 2: El día sin clase está después de la(s) semana(s) sin clases
                        dias_a_excluir = 0
                        for inicio, fin in semanas_sin_clase_rango:
                            if fin < dia:  # Solo restar si la semana sin clase está antes del día sin clase
                                dias_a_excluir += (fin - inicio).days + 1

                        # Restar los días excluidos y calcular las semanas transcurridas
                        dias_netos = dias_transcurridos - dias_a_excluir
                        semanas_transcurridas = dias_netos // 7
                    
                    # Determinar el número de la semana
                    numero_semana = semanas_transcurridas + 1  # Para comenzar la numeración desde la semana 1

                    # Determinar el día de la semana
                    dia_semana = dia.weekday()  # 0 es lunes, 6 es domingo

                    resultado.append({
                        'numero_semana': numero_semana,
                        'dia_semana': dia_semana
                    })

        return resultado




class Horario(models.Model):
    nombre=models.CharField(max_length=20, unique=True)
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre        
class Horario_Asignatura(models.Model):
    
    horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.horario.nombre}, {self.asignatura.nombre}"        





class Semana(models.Model):
    nombre = models.CharField(max_length=50)
    horario= models.ForeignKey(Horario, on_delete=models.CASCADE)
    def __str__(self):
        return f"{self.nombre}"

class Dia(models.Model):
    semana = models.ForeignKey(Semana, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=20)
    def __str__(self):
        return f"{self.nombre}"
class Actividad(models.Model):
    dia = models.ForeignKey(Dia, on_delete=models.CASCADE)
    asignatura = models.ForeignKey(Asignatura, on_delete=models.CASCADE)
    turno = models.IntegerField()
    def __str__(self):
        return f"{self.asignatura.abreviatura}"



class Balance_de_carga(models.Model):
    nombre = models.CharField(max_length=50)
    balance = models.JSONField(default=list,
        blank=True, verbose_name="Balamce")
    Horario = models.ForeignKey(Horario, on_delete=models.CASCADE)
    def __str__(self):
        return self.nombre