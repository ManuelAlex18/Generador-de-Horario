import numpy as np
from pulp import *
import csv
import random
from app.models import Asignatura, Periodo, Semana, Dia, Actividad, Horario, Balance_de_carga
# Datos iniciales


def generar_horario(a,f,s,id_horario,d):
    
    horario_obj = Horario.objects.get(id=id_horario)#Recibimos el id del horario creado
    asignaturas=a
    fondo_horas = f
    num_semanas = int(s)
    
    
    turnos_por_semana = [15] * num_semanas
    turnos_por_dia = 3
    dias_por_semana = 5
    horas_por_turno = 2

    # Ajustar turnos_por_semana según días sin clases
    for semana_info in d:
        semana_dic = semana_info['numero_semana']
        turnos_por_semana[semana_dic-1] -= 3

    print(turnos_por_semana)
    print(fondo_horas)

    # Primer Código: Generar solución inicial y evaluación
    def generar_solucion_inicial():
        solucion = np.zeros((len(asignaturas), num_semanas))
        turnos_restantes = turnos_por_semana.copy()
        
        for i, fondo in enumerate(fondo_horas):
            horas_necesarias = fondo // horas_por_turno
            for semana in range(num_semanas):
                if horas_necesarias <= 0:
                    break
                turnos_a_asignar = min(horas_necesarias, turnos_restantes[semana])
                if turnos_a_asignar > 0:
                    solucion[i, semana] = float(turnos_a_asignar)
                    horas_necesarias -= turnos_a_asignar
                    turnos_restantes[semana] -= turnos_a_asignar

        return solucion

    def eval_function(horario):
        horas_asignadas = np.sum(horario, axis=1) * horas_por_turno
        penalizacion = np.sum(np.abs(horas_asignadas - fondo_horas))
        return penalizacion

    def generar_vecindario(solucion_actual):
        vecinos = []
        for i in range(len(asignaturas)):
            for semana in range(num_semanas):
                if solucion_actual[i, semana] > 0:
                    vecino = solucion_actual.copy()
                    vecino[i, semana] -= 1
                    vecinos.append(vecino)
                vecino = solucion_actual.copy()
                vecino[i, semana] += 1
                vecinos.append(vecino)
        return vecinos

    def busqueda_tabu(solucion_inicial, iteraciones=100, tabu_tenure=5):
        mejor_solucion = solucion_inicial.copy()
        mejor_valor = eval_function(mejor_solucion)
        
        solucion_actual = solucion_inicial.copy()
        lista_tabu = []

        for _ in range(iteraciones):
            vecindario = generar_vecindario(solucion_actual)
            mejor_vecino = None
            mejor_vecino_valor = float('inf')
            
            for vecino in vecindario:
                valor_vecino = eval_function(vecino)
                if valor_vecino < mejor_vecino_valor and vecino.tolist() not in lista_tabu:
                    mejor_vecino = vecino
                    mejor_vecino_valor = valor_vecino
            
            if mejor_vecino is not None:
                solucion_actual = mejor_vecino.copy()
                lista_tabu.append(solucion_actual.tolist())
                if len(lista_tabu) > tabu_tenure:
                    lista_tabu.pop(0)
                
                if mejor_vecino_valor < mejor_valor:
                    mejor_solucion = mejor_vecino.copy()
                    mejor_valor = mejor_vecino_valor
        
        return mejor_solucion, mejor_valor

    solucion_inicial = generar_solucion_inicial()
    horario_optimo, valor_optimo = busqueda_tabu(solucion_inicial, iteraciones=100, tabu_tenure=50)

    # Segundo Código: Balance de carga
    prob = LpProblem("Balance_de_Carga", LpMinimize)
    n = len(asignaturas)
    m = num_semanas
    t = turnos_por_semana
    b = fondo_horas

    # Variables de decisión
    x = LpVariable.matrix("x", (range(n), range(m)), 0, 6, cat=LpInteger)
    enc = LpVariable.matrix("enc", (range(n), range(m)), 0, cat=LpInteger)
    ENC = LpVariable.matrix("ENC", (range(n), range(m)), 0, cat=LpInteger)
    carga = LpVariable.matrix("carga", range(m), 0, 60, cat=LpInteger)
    carga2 = LpVariable.matrix("carga2", range(m), 0, 60, cat=LpInteger)
    sc = LpVariable.matrix("sc", range(m), 0, cat=LpInteger)
    sc_ = LpVariable.matrix("sc_", range(m), 0, cat=LpInteger)
    sc2 = LpVariable.matrix("sc2", range(m), 0, cat=LpInteger)
    sc2_ = LpVariable.matrix("sc2_", range(m), 0, cat=LpInteger)

    # Restricciones del problema
    for i in range(n):
        prob += 2 * lpSum(x[i][j] for j in range(m)) == b[i]

    for j in range(m):
        prob += lpSum(x[i][j] for i in range(n)) <= t[j]

    for i in range(n):
        total = lpSum(x[i][j] for j in range(m))
        for j in range(m):
            prob += m * x[i][j] - total + enc[i][j] - ENC[i][j] == 0

    for j in range(m):
        prob += lpSum(x[i][j] for i in range(n)) * 2 >= carga2[j]
        prob += lpSum(x[i][j] for i in range(n)) * 2 <= carga[j]

    for j in range(m):
        prob += (m - 1) * carga[j] - lpSum(carga) + sc_[j] - sc[j] == 0
        prob += (m - 1) * carga2[j] - lpSum(carga2) + sc2_[j] - sc2[j] == 0

    # prob += x[0][0] == 0 Dejar un dia espesifico sin clase
    prob += lpSum(sc_) + lpSum(sc) + lpSum(sc2_) + lpSum(sc2) + lpSum(enc) + lpSum(ENC)

    prob.solve(PULP_CBC_CMD(msg=False))

    resultados = np.array([[x[i][j].value() for j in range(m)] for i in range(n)])
    resultados_transpuestos = resultados.T

    totals_filas = np.sum(resultados_transpuestos, axis=1)*2
    totals_columnas = np.sum(resultados_transpuestos, axis=0)*2
    total_semanal = np.sum(totals_columnas)

    # Añadir la columna de totales de semanas
    resultados_con_totales = np.hstack((resultados_transpuestos, totals_filas.reshape(-1, 1)))

    # Añadir la fila de totales por columna y el total general
    totales_filas_y_total = np.append(totals_columnas, total_semanal)
    resultados_con_totales = np.vstack((resultados_con_totales, totales_filas_y_total))
        
    

    # Guardar en CSV
    with open('balance.csv', 'w', newline='') as file:
        writer = csv.writer(file, delimiter=";")
    
        # Escribir los datos
        for row in resultados_con_totales:
            writer.writerow(row)


    # Tercer Código: Generar horario final
    balance_carga = resultados_transpuestos
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    num_dias = len(dias_semana)
    num_asignaturas = len(asignaturas)
    num_semanas = len(balance_carga)
    
    horario = [[[] for _ in range(num_dias)] for _ in range(num_semanas)]

    def asignatura_en_dia(horario_semana, dia, asignatura):
        return asignatura in horario_semana[dia]

    for semana in range(num_semanas):
        turnos_asignados = {asignatura: balance_carga[semana][i] for i, asignatura in enumerate(asignaturas)}
        
        for dia in range(num_dias):
            while len(horario[semana][dia]) < turnos_por_dia and sum(turnos_asignados.values()) > 0:
                asignaturas_posibles = [asignatura for asignatura, turnos in turnos_asignados.items() if turnos > 0 and not asignatura_en_dia(horario[semana], dia, asignatura)]
                
                if not asignaturas_posibles:
                    asignaturas_posibles = [asignatura for asignatura, turnos in turnos_asignados.items() if turnos > 0]
                
                asignatura_seleccionada = random.choice(asignaturas_posibles)
                horario[semana][dia].append(asignatura_seleccionada)
                turnos_asignados[asignatura_seleccionada] -= 1
        
        
        # Guardar en base de datos
        for semana_index in range(num_semanas):
            semana_nombre = f"Semana {semana_index + 1}"
            semana_obj, created = Semana.objects.get_or_create(nombre=semana_nombre, horario=horario_obj)
            
            dias_sin_clase = [semana_info['dia_semana'] for semana_info in d if semana_info['numero_semana'] == (semana_index + 1)]
            
            # Crear los objetos Día para la semana
            dias_objetos = []
            for dia_index in range(num_dias):
                dia_nombre = dias_semana[dia_index]
                dia_obj, created = Dia.objects.get_or_create(semana=semana_obj, nombre=dia_nombre)
                dias_objetos.append((dia_index, dia_obj))
            
            # Inicializar una lista de actividades a mover
            actividades_a_mover = []

            # Asignar actividades a los días con clase y acumular actividades de días sin clase
            for dia_index, dia_obj in dias_objetos:
                if dia_index in dias_sin_clase:
                    # Acumular las actividades para los días sin clase
                    actividades_a_mover.extend(horario[semana_index][dia_index])
                    continue
                
                # Asignar actividades para los días con clase
                turno_actual = 1
                for asignatura in horario[semana_index][dia_index]:
                    asignatura_obj = Asignatura.objects.get(abreviatura=asignatura)
                    Actividad.objects.get_or_create(dia=dia_obj, asignatura=asignatura_obj, turno=turno_actual)
                    turno_actual += 1
                
                # Mover las actividades acumuladas al siguiente día disponible
                while actividades_a_mover and turno_actual <= 3:
                    asignatura = actividades_a_mover.pop(0)
                    asignatura_obj = Asignatura.objects.get(abreviatura=asignatura)
                    Actividad.objects.get_or_create(dia=dia_obj, asignatura=asignatura_obj, turno=turno_actual)
                    turno_actual += 1


    balance_obj = Balance_de_carga.objects.create(
        nombre=horario_obj.nombre,  # El nombre será el mismo que el del horario
        Horario=horario_obj,  # Se referencia al horario como llave foránea
    )
    balance_obj.balance=resultados_transpuestos.tolist()
    balance_obj.save()