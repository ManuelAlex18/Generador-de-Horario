from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.decorators import login_required

from .logic.logicaHorario import generar_horario

from .form_horario import HorarioForm, PeriodoForm, AsignaturaForm

from .models import Horario_Asignatura, Horario, Semana, Dia, Actividad, Asignatura, Periodo, Balance_de_carga

from django.core.exceptions import ValidationError

import json
# Create your views here.


def home(request):
    
    
    return render(request, 'home.html', {'pagina_activa': 'inicio'})

def registro(request):
    if request.method == 'GET':
        return render(request, 'registro.html', {'form': UserCreationForm})
    else: 
        if request.POST['password1'] == request.POST['password2']:
            try:
                user=User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('home')
            except:
                return render(request, 'registro.html', {'form': UserCreationForm, 'error': 'El usuario ya existe'})
        
        return render(request, 'registro.html', {'form': UserCreationForm, 'error': 'Las contraseñas no coinciden'})

def iniciar_sesion(request):
    if request.method == 'GET':
        return render(request, 'iniciar_sesion.html', {'form': AuthenticationForm})
    else:
        user=authenticate(request, username=request.POST['username'], password=request.POST['password'])
        if user is None:
            return render(request, 'iniciar_sesion.html', {'form': AuthenticationForm, 'error': 'Usuario o contrasena son incorrectos'})
        else:
            login(request, user)
            return redirect('home')

def cerrar_sesion(request):
    logout(request)
    return redirect('home')

@login_required
def index(request, id):
    horario = get_object_or_404(Horario, id=id)
    semanas= Semana.objects.filter(horario=horario)
    asignaturas = Asignatura.objects.filter(
        id__in=Horario_Asignatura.objects.filter(horario=horario).values_list('asignatura_id', flat=True)
    )
    balance_de_carga=get_object_or_404(Balance_de_carga, Horario=horario)
    balance=balance_de_carga.balance
    totales=[]
    for ele in balance:
        suma=sum(ele)*2
        totales.append(suma)
    balance_combinado=zip(balance,totales)

    return render(request, 'index.html', {'semanas': semanas, 'horario':horario, 'asignaturas':asignaturas, 'pagina_activa': 'horarios', 'balance_combinado':balance_combinado})

    

@login_required
def crearHorario(request):
    if request.method == 'GET':
        form = HorarioForm()
        return render(request, 'crear_horario.html', {'form': form, 'pagina_activa': 'crear_horario'})
    
    else:
        form = HorarioForm(request.POST)
        if form.is_valid():
            try:
                # Utiliza el método save sobrescrito para obtener todos los valores necesarios
                horario, asignaturas, fondo_de_horas, numero_de_semanas, dicc = form.save()

                generar_horario(asignaturas, fondo_de_horas, numero_de_semanas, horario.id, dicc)
                
                # Crea las relaciones Horario_Asignatura con los objetos asignatura seleccionados
                for asignatura in form.cleaned_data['asignaturas']:
                    Horario_Asignatura.objects.create(horario=horario, asignatura=asignatura)
                
                # Redirige a la página 'index' después de guardar los datos
                return redirect(f'index/{horario.id}/')
            
            except Exception as e:
                # Captura cualquier tipo de excepción y agrega un mensaje de error al formulario
                form.add_error(None, 'Ocurrió un error al guardar el horario: {}'.format(e))
        
        # Si el formulario no es válido o hubo un error, renderiza el formulario con los errores
        return render(request, 'crear_horario.html', {'form': form, 'pagina_activa': 'crear_horario'})


@login_required
def mostrar_horarios(request):
    horarios=Horario.objects.all()
    return render(request, 'mostrar_horarios.html', {'horarios': horarios, 'pagina_activa': 'horarios'})


def eliminar_horario(request, id):
    horario=get_object_or_404(Horario, pk=id)
    if request.method =='POST':
        horario.delete()
        return redirect('horarios')

@login_required
def crear_asignatura(request):    
    try:
        if request.method == 'GET':
            form=AsignaturaForm()
            return render(request, 'crear_asignatura.html', {'form':form, 'pagina_activa': 'crear_asignatura'})

        else:
            form=AsignaturaForm(request.POST)
            if form.is_valid():
                asignatura=form.save(commit=False)
                asignatura.save()
                return redirect('crear_horario')

    except Exception as e:
        # Captura cualquier tipo de excepción y agrega un mensaje de error al formulario
        form.add_error(None, 'Ocurrió un error al guardar el horario: {}'.format(e))

    return render(request, 'crear_asignatura.html', {'form':form, 'error':'Los datos no son validos', 'pagina_activa': 'crear_asignatura'})


@login_required
def editar_asignatura(request, id):
    if request.method=='GET':
        asignatura=get_object_or_404(Asignatura,pk=id)
        form=AsignaturaForm(instance=asignatura)
        return render(request, 'editar_asignatura.html', {'asignatura':asignatura, 'form':form})

    else:
        try:
            asignatura=get_object_or_404(Asignatura,pk=id)
            form=AsignaturaForm(request.POST, instance=asignatura)
            form.save()
            return redirect('crear_horario')
        except ValueError:
            return render(request, 'editar_asignatura.html', {'asignatura':asignatura, 'form':form, 'error':'Error al editar asignatura'})


def eliminar_asignatura(request, id):
    asignatura=get_object_or_404(Asignatura, pk=id)
    if request.method =='POST':
        asignatura.delete()
        return redirect('crear_horario')


@login_required
def crear_periodo(request):
    if request.method == 'POST':
        form = PeriodoForm(request.POST)
        if form.is_valid():
            try:
                periodo = form.save(commit=False)
                
                dias_sin_clase = request.POST.get('dias_sin_clase', '[]')
                if dias_sin_clase: 
                    periodo.dias_sin_clase = json.loads(dias_sin_clase)
                else:
                    periodo.dias_sin_clase = []

                semanas_sin_clase = request.POST.get('semanas_sin_clase', '[]')
                if semanas_sin_clase:      
                    periodo.semanas_sin_clase = json.loads(semanas_sin_clase)
                else:
                    periodo.semanas_sin_clase = []

                periodo.save()
                return redirect('periodos')
        
            except Exception as e:
            # Captura cualquier tipo de excepción y agrega un mensaje de error al formulario
                form.add_error(None, 'Ocurrió un error al guardar el horario: {}'.format(e))
    
    else:
        form = PeriodoForm()
    return render(request, 'crear_periodo.html', {'form': form, 'pagina_activa': 'crear_periodo'})


@login_required
def editar_periodo(request, id):
    # Obtener el periodo que se va a editar
    
    periodo = get_object_or_404(Periodo, id=id)
    # Inicializar las variables `dias_sin_clase_json` y `semanas_sin_clase_json`
    dias_sin_clase_json = json.dumps(periodo.dias_sin_clase) if periodo.dias_sin_clase else '[]'
    semanas_sin_clase_json = json.dumps(periodo.semanas_sin_clase) if periodo.semanas_sin_clase else '[]'
    valor_semana=periodo.semanas_sin_clase
    valor_dia=periodo.dias_sin_clase
    
    if request.method == 'POST':
        
        form = PeriodoForm(request.POST, instance=periodo)
        if form.is_valid():
            
            try:
                
                periodo = get_object_or_404(Periodo, id=id)
                
                # Capturar y procesar días sin clases
                # Capturar los datos del formulario
                dias_sin_clase = request.POST.get('dias_sin_clase', None)  # Campo que podría haber sido modificado
                semanas_sin_clase = request.POST.get('semanas_sin_clase', None)  # Campo que podría haber sido modificado
                condicion_dias=dias_sin_clase
                condicion_semana=semanas_sin_clase
                
                valor_semanafinal=periodo.semanas_sin_clase
                # Verificar si se modificaron los días sin clase
                if dias_sin_clase is not None and dias_sin_clase.strip():
                    try:
                        
                        # Actualizar el valor de dias_sin_clase en el periodo
                        periodo.dias_sin_clase = json.loads(dias_sin_clase)
                    except json.JSONDecodeError:
                        # Manejo del error si no se puede decodificar el JSON
                        print("Error: No se pudo decodificar el JSON de los días sin clase")
                else:
                    
                    # Mantener el valor existente de dias_sin_clase si no se ha modificado
                    dias_sin_clase = periodo.dias_sin_clase
                
                # Verificar si se modificaron las semanas sin clase
                if semanas_sin_clase is not None and semanas_sin_clase.strip():
                    try:
                        
                        # Actualizar el valor de semanas_sin_clase en el periodo
                        periodo.semanas_sin_clase = json.loads(semanas_sin_clase)
                    except json.JSONDecodeError:
                        # Manejo del error si no se puede decodificar el JSON
                        print("Error: No se pudo decodificar el JSON de las semanas sin clase")
                
                
                elif condicion_dias != '':
                    
                    if condicion_semana == '':
            
                        semanas_sin_clase = periodo.semanas_sin_clase
                    else:
                        
                        periodo.semanas_sin_clase=[]
                
                elif condicion_dias == '':

                    periodo.semanas_sin_clase=[]
                          
                elif condicion_semana == '' and condicion_dia == '':
                    semanas_sin_clase = periodo.semanas_sin_clase
                else:
                    # Mantener el valor existente de semanas_sin_clase si no se ha modificado
                    semanas_sin_clase = periodo.semanas_sin_clase

                periodo_modificado = form.save(commit=False)
            
                # Asignar manualmente los campos que queremos actualizar
                periodo.start = periodo_modificado.start
                periodo.end = periodo_modificado.end
                periodo.name = periodo_modificado.name
                  
                periodo.save()
                return redirect('periodos')  # Redirigir a la lista de periodos
                
            except Exception as e:
                
            # Captura cualquier tipo de excepción y agrega un mensaje de error al formulario
                form.add_error(None, 'Ocurrió un error al guardar el periodo: {}'.format(e))
    else:
        # Cargar los días sin clase y semanas sin clase existentes en formato JSON
        dias_sin_clase_json = json.dumps(periodo.dias_sin_clase)
        semanas_sin_clase_json = json.dumps(periodo.semanas_sin_clase)

        form = PeriodoForm(instance=periodo)
    return render(request, 'editar_periodo.html', {
            'form': form,
            'dias_sin_clase': dias_sin_clase_json,
            'semanas_sin_clase': semanas_sin_clase_json,
            'periodo': periodo
        })


def eliminar_periodo(request, id):
    periodo=get_object_or_404(Periodo, pk=id)
    if request.method =='POST':
        periodo.delete()
        return redirect('periodos')


@login_required
def mostrar_periodos(request):
    
    periodos=Periodo.objects.all()
    return render(request, 'mostrar_periodos.html', {'periodos': periodos, 'pagina_activa': 'periodos'})