from django import forms
from .models import Horario, Asignatura, Periodo
from django.utils.html import format_html
from django.urls import reverse
import datetime
from datetime import date
from django.core.exceptions import ValidationError
class AsignaturaForm(forms.ModelForm):
    class Meta:
        model = Asignatura
        fields = ['nombre', 'abreviatura', 'horas_clase']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6', 'placeholder': 'Nombre de la Asignatura'}),
            'abreviatura': forms.TextInput(attrs={'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6', 'placeholder': 'Abreviatura'}),
            'horas_clase': forms.NumberInput(attrs={'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6', 'placeholder': 'Horas de Clase'}),
        }
    def clean_nombre(self):
        print("hola")
        nombre = self.cleaned_data.get('nombre')
        # Si la instancia ya existe (es una edición), verifica el nombre
        if self.instance and self.instance.pk:
            # Comprobar si el nombre ha cambiado
            if Asignatura.objects.filter(nombre=nombre).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe una asignatura con ese nombre.")
        else:
            # Para nuevos registros
            if Asignatura.objects.filter(nombre=nombre).exists():
                raise forms.ValidationError("Ya existe una asignatura con ese nombre.")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        horas_clases=cleaned_data.get('horas_clase')

        if horas_clases % 2 != 0:
            raise forms.ValidationError("Las horas de clase deben ser pares")
        return cleaned_data
        
    def __init__(self, *args, **kwargs):
        super(AsignaturaForm, self).__init__(*args, **kwargs)
        # No se requiere lógica adicional para la validación en este caso.

    

class CustomCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []

        output = []

        # Genera el HTML para cada asignatura con su checkbox y botón "Editar"
        for asignatura in self.choices.queryset:
            asignatura_id = asignatura.id
            asignatura_nombre = f"{asignatura.nombre} - {asignatura.horas_clase}"
            checked_html = 'checked' if asignatura_id in value else ''
            url = reverse('editar_asignatura', args=[asignatura_id])

            # Checkbox HTML con clases de Tailwind
            checkbox_html = format_html(
                '<input type="checkbox" name="{}" value="{}" {} class="form-checkbox text-blue-500 mr-2">',
                name,
                asignatura_id,
                checked_html
            )

            # Nombre de la asignatura
            nombre_asignatura_html = format_html(
                '<span class="text-gray-800">{}</span>',
                asignatura_nombre
            )

            # Botón "Editar" alineado a la derecha
            editar_html = format_html(
                '<a href="{}" class="text-blue-500 hover:underline ml-auto">Editar</a>',  # 'ml-auto' para mover el enlace al final
                url
            )

            # Estructura con flexbox, checkbox y nombre al principio, y "Editar" al final
            output.append(format_html(
                '<div class="flex justify-between items-center mb-4 w-full">{}</div>',
                format_html('{}{}{}', checkbox_html, nombre_asignatura_html, editar_html)
            ))

        return format_html(''.join(output))




class HorarioForm(forms.ModelForm):
    asignaturas = forms.ModelMultipleChoiceField(
        queryset=Asignatura.objects.all(),
        widget=CustomCheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Horario
        fields = ('nombre', 'asignaturas', 'periodo')

    def __init__(self, *args, **kwargs):
        super(HorarioForm, self).__init__(*args, **kwargs)

        self.fields['nombre'].widget.attrs.update({
            'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6',
            'placeholder': 'Nombre del Horario'
        })

        self.fields['periodo'].widget.attrs.update({
            'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6'
        })

        self.fields['asignaturas'].widget.attrs.update({
            'class': 'form-checkbox text-blue-500 mr-2'
        })

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if Horario.objects.filter(nombre=nombre).exists():
            raise forms.ValidationError("Ya existe un horario para esa carrera")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        asignaturas_seleccionadas = cleaned_data.get('asignaturas')
        periodo = cleaned_data.get('periodo')

        if not asignaturas_seleccionadas or not periodo:
            return cleaned_data

        # Obtener número de semanas del periodo
        numero_de_semanas = periodo.calcular_cantidad_semanas()

        # Obtener cantidad de días sin clase
        dias_sin_clase_info = periodo.obtener_dias_sin_clase_info()
        cantidad_dias_sin_clase = len(dias_sin_clase_info)

        # Sumar las horas de clase de las asignaturas seleccionadas
        suma_horas_clase = sum(asignatura.horas_clase for asignatura in asignaturas_seleccionadas)
        numero_de_semanas = periodo.calcular_cantidad_semanas()*30
        numero_de_semanas-=cantidad_dias_sin_clase*6
        
        print(suma_horas_clase)
        print(numero_de_semanas)
        # Validar si la suma de horas por semana excede el límite semanal
        if numero_de_semanas / suma_horas_clase  < 1:
            raise forms.ValidationError("El total de horas de clase de las asignaturas supera las horas maximas de duracion del periodo")
        elif numero_de_semanas / suma_horas_clase  > 5:
            raise forms.ValidationError("La proporcion de horas clases entre asignaturas y periodo no permiten crear un horario")
        return cleaned_data

    def save(self, commit=True):
        horario = super().save(commit=False)
        periodo = self.cleaned_data['periodo']
        numero_de_semanas = periodo.calcular_cantidad_semanas()
        dicc = periodo.obtener_dias_sin_clase_info()
        asignaturas_seleccionadas = self.cleaned_data['asignaturas']
        asignaturas = [asignatura.abreviatura for asignatura in asignaturas_seleccionadas]
        fondo_de_horas = [asignatura.horas_clase for asignatura in asignaturas_seleccionadas]

        if commit:
            horario.save()
            self.save_m2m()

        return horario, asignaturas, fondo_de_horas, numero_de_semanas, dicc



class PeriodoForm(forms.ModelForm):
    class Meta:
        model = Periodo
        fields = ['name', 'start', 'end', 'dias_sin_clase', 'semanas_sin_clase']
        widgets = {
            'start': forms.DateInput(attrs={'type': 'date', 'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6'}),
            'end': forms.DateInput(attrs={'type': 'date', 'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6'}),
        }

    def __init__(self, *args, **kwargs):
        super(PeriodoForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({
            'class': 'appearance-none border border-black rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline mb-6',
            'placeholder': 'Nombre del Periodo'
        })
    def clean_name(self):
        nombre = self.cleaned_data.get('name')
        # Si la instancia ya existe (es una edición), verifica el nombre
        if self.instance and self.instance.pk:
            # Comprobar si el nombre ha cambiado
            if Periodo.objects.filter(name=nombre).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe un periodo con este nombre.")
        else:
            # Para nuevos registros
            if Periodo.objects.filter(name=nombre).exists():
                raise forms.ValidationError("Ya existe un periodo con este nombre.")
        return nombre


    def clean(self):
        
        cleaned_data = super().clean()
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        dias_sin_clase = cleaned_data.get('dias_sin_clase')
        semanas_sin_clase = cleaned_data.get('semanas_sin_clase')
        
        # Validación de que las fechas de inicio y fin no sean domingo (6 es domingo)
        if start and start.weekday() == 6:
            self.add_error('start', "La fecha de inicio no puede ser un domingo.")
        
        if end and end.weekday() == 6:
            self.add_error('end', "La fecha de finalización no puede ser un domingo.")
        
        # Validación de que los días sin clase estén dentro del rango
        if dias_sin_clase:
            
            
            for dia_str in dias_sin_clase:
                dia = date.fromisoformat(dia_str)
                if not (start <= dia <= end):
                    raise forms.ValidationError(f"El día {dia} no está en el rango del periodo.")
                    
        # Validación de que las semanas sin clase estén dentro del rango
        if semanas_sin_clase:
            for semana in semanas_sin_clase:
                semana_inicio = date.fromisoformat(semana['start'])
                semana_fin = date.fromisoformat(semana['end'])
                if not (start <= semana_inicio <= end and start <= semana_fin <= end):
                    raise forms.ValidationError(f"Las fechas de {semana_inicio} a {semana_fin} no está en el rango del periodo.")

        return cleaned_data