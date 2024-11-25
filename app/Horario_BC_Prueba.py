import numpy as np
from pulp import *
import csv
import random

from app.models import Asignatura


# Datos iniciales
# asignaturas = ["A", "B", "C", "D", "E", "F", "G", "H"]
# fondo_horas = [96, 80, 48, 32, 80, 48, 32, 16]
# turnos_por_semana = [0, 12, 15, 15, 15, 15, 15, 15, 12, 15, 15, 15, 15, 15, 15, 15, 15, 15, 15]
# num_semanas = 18
# turnos_por_dia = 3
# dias_por_semana = 5
# horas_por_turno = 2
# Datos iniciales

asignaturas=Asignatura.abreviatura.objects.all
fondo_horas = [52, 32, 40, 40, 54]
turnos_por_semana = [9, 15, 15, 15, 15, 15, 15, 15]
num_semanas = 8
turnos_por_dia = 3
dias_por_semana = 5
horas_por_turno = 2


# Primer Código: Generar solución inicial y evaluación
def generar_solucion_inicial():
    solucion = np.zeros((len(asignaturas), num_semanas))
    turnos_restantes = turnos_por_semana.copy()
    
    for i in range(len(asignaturas)):
        horas_necesarias = fondo_horas[i] // horas_por_turno
        semana = 0
        while horas_necesarias > 0 and semana < num_semanas:
            if turnos_restantes[semana] > 0:
                turnos_a_asignar = min(horas_necesarias, turnos_restantes[semana])
                solucion[i, semana] = float(turnos_a_asignar)
                horas_necesarias -= turnos_a_asignar
                turnos_restantes[semana] -= turnos_a_asignar
            semana += 1

    return solucion

def eval_function(horario):
    penalizacion = 0
    for i in range(len(asignaturas)):
        horas_asignadas = np.sum(horario[i]) * horas_por_turno
        penalizacion += abs(horas_asignadas - fondo_horas[i])
    return penalizacion

def generar_vecindario(solucion_actual):
    vecinos = []
    for i in range(len(asignaturas)):
        for semana in range(num_semanas):
            vecino = solucion_actual.copy()
            if vecino[i, semana] > 0:
                vecino[i, semana] -= 1
                vecinos.append(vecino)
            vecino = solucion_actual.copy()
            vecino[i, semana] += 1
            vecinos.append(vecino)
    return vecinos

def busqueda_tabu(solucion_inicial, iteraciones=100, tabu_tenure=5):
    mejor_solucion = solucion_inicial
    mejor_valor = eval_function(mejor_solucion)
    
    solucion_actual = solucion_inicial
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
            solucion_actual = mejor_vecino
            lista_tabu.append(solucion_actual.tolist())
            if len(lista_tabu) > tabu_tenure:
                lista_tabu.pop(0)
            
            if mejor_vecino_valor < mejor_valor:
                mejor_solucion = mejor_vecino
                mejor_valor = mejor_vecino_valor
    
    return mejor_solucion, mejor_valor

solucion_inicial = generar_solucion_inicial()
horario_optimo, valor_optimo = busqueda_tabu(solucion_inicial, iteraciones=100, tabu_tenure=50)

# Segundo Código: Balance de carga
def TotalEncuentros(var, index):
    return sum(var[index])

def CargaSemanal(var, sem):
    carga = 0
    for i in range(n):
        carga += 2 * var[i][sem]
    return carga

def CargaTotal(var):
    return sum(CargaSemanal(var, j) for j in range(m))

def IncTotal(var):
    return sum(sum(var[i][j] for i in range(m)) for j in range(n))

def IncAsig(var, index):
    return sum(var[index][j] for j in range(m))

def BalancearEncuentros(var1, var2):
    return sum(sum(var1[x]) for x in range(len(var1))) + sum(sum(var2[x]) for x in range(len(var2)))

# Definir el problema de optimización
prob = LpProblem("Balance_de_Carga", LpMinimize)

n = len(asignaturas)
m = num_semanas
t = turnos_por_semana
b = fondo_horas
c = horario_optimo  # Usar el horario óptimo generado por el primer código

# Variables de decisión
x = LpVariable.matrix("x", (range(n), range(m)), 0, 6, cat=LpInteger)
enc = LpVariable.matrix("enc", (range(n), range(m)), 0, cat=LpInteger)
ENC = LpVariable.matrix("ENC", (range(n), range(m)), 0, cat=LpInteger)
carga = LpVariable.matrix("carga", range(m), 0, 30, cat=LpInteger)
carga2 = LpVariable.matrix("carga2", range(m), 0, 30, cat=LpInteger)
sc = LpVariable.matrix("sc", range(m), 0, cat=LpInteger)
sc_ = LpVariable.matrix("sc_", range(m), 0, cat=LpInteger)
sc2 = LpVariable.matrix("sc2", range(m), 0, cat=LpInteger)
sc2_ = LpVariable.matrix("sc2_", range(m), 0, cat=LpInteger)

# Restricciones del problema
for i in range(n):
    prob += 2 * sum(x[i][j] for j in range(m)) == b[i]

for j in range(m):
    prob += sum(x[i][j] for i in range(n)) <= t[j]

for i in range(n):
    total = TotalEncuentros(x, i)
    for j in range(m):
        prob += m * x[i][j] - total + enc[i][j] - ENC[i][j] == 0

for j in range(m):
    prob += CargaSemanal(x, j) >= carga2[j]
    prob += CargaSemanal(x, j) <= carga[j]

for j in range(m):
    prob += (m - 1) * carga[j] - sum(carga) + sc_[j] - sc[j] == 0
    prob += (m - 1) * carga2[j] - sum(carga2) + sc2_[j] - sc2[j] == 0

prob += x[0][0] == 0

prob += sum(sc_) + sum(sc) + sum(sc2_) + sum(sc2) + BalancearEncuentros(enc, ENC)

prob.solve(PULP_CBC_CMD(msg=False))

resultados = [[x[i][j].value() for j in range(m)] for i in range(n)]
resultados_transpuestos = list(map(list, zip(*resultados)))

with open('balance.csv', 'w', newline='') as file:
    writer = csv.writer(file, delimiter=";")
    writer.writerows(resultados_transpuestos)

# Tercer Código: Generar horario final
balance_carga = resultados_transpuestos  # Usar el balance de carga generado por el segundo código

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
num_dias = len(dias_semana)
num_asignaturas = len(asignaturas)
num_semanas = len(balance_carga)
turnos_semanales = 15

horario = [[[] for _ in range(num_dias)] for _ in range(num_semanas)]

def asignatura_en_dia(horario_semana, dia, asignatura):
    return asignatura in horario_semana[dia]

for semana in range(num_semanas):
    turnos_asignados = {asignatura: balance_carga[semana][i] for i, asignatura in enumerate(asignaturas)}
    
    for dia in range(num_dias):
        while len(horario[semana][dia]) < 3 and sum(turnos_asignados.values()) > 0:
            asignaturas_posibles = [asignatura for asignatura, turnos in turnos_asignados.items() if turnos > 0 and not asignatura_en_dia(horario[semana], dia, asignatura)]
            
            if not asignaturas_posibles:
                asignaturas_posibles = [asignatura for asignatura, turnos in turnos_asignados.items() if turnos > 0]
            
            asignatura_seleccionada = random.choice(asignaturas_posibles)
            horario[semana][dia].append(asignatura_seleccionada)
            turnos_asignados[asignatura_seleccionada] -= 1

# for x in horario:
#     for y in x:
#         print(y)

def generarHorarioPrueba():
    h=Horario.objects.get(id=2)
    p=Periodo.objects.get(id=1)
    print(p.calcular_cantidad_semanas())
    print(h)
    relaciones=Horario_Asignatura.objects.filter(horario=2)
    fh=[relacion.asignatura.horas_clase for relacion in relaciones]
    asi=[relacion.asignatura.abreviatura for relacion in relaciones]
    print(asi, fh)
    return [num_semanas, dias_semana, horario, asi, fh]
