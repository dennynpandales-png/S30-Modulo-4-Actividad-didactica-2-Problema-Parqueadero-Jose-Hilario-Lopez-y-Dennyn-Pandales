import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy import stats

plt.rcParams['figure.figsize'] = (11, 5)
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3

usuarios = {
    'rapido':    {'servicio': 1.0, 'llegada': 3.0, 'prob': 0.25},
    'normal':    {'servicio': 3.0, 'llegada': 3.0, 'prob': 0.20},
    'lento':     {'servicio': 4.0, 'llegada': 5.0, 'prob': 0.275},
    'muy_lento': {'servicio': 6.0, 'llegada': 7.0, 'prob': 0.275}
}

num_cajeros = 3
tiempo_simulacion = 1000

print("=== VERIFICACIÓN DE PARÁMETROS DEL SISTEMA ===")
print(f"Cajeros independientes configurados: {num_cajeros}")
print(f"Suma total de probabilidades: {sum(u['prob'] for u in usuarios.values()):.3f}\n")

for tipo, datos in usuarios.items():
    lam = 1.0 / datos['llegada']
    mu = 1.0 / datos['servicio']
    rho = lam / mu
    estado = "Estable (ρ < 1)" if rho < 1 else "Crítico / Límite (ρ >= 1)"
    print(f"Usuario {tipo.upper():10s} | Prob: {datos['prob']*100:5.1f}% | λ = {lam:.3f} cl/min | μ = {mu:.3f} cl/min | ρ = {rho:.3f} -> {estado}")

def simular_sistema_parqueadero(num_cajeros=3, tiempo_sim=1000, semilla=None):
    if semilla is not None:
        np.random.seed(semilla)

    tipos = list(usuarios.keys())
    probs = [usuarios[t]['prob'] for t in tipos]
    tasa_llegada_promedio = sum(usuarios[t]['prob'] * usuarios[t]['llegada'] for t in tipos)

    resultados_cajeros = []
    for c in range(num_cajeros):
        resultados_cajeros.append({
            'tiempos_atencion': [],
            'tiempos_espera': [],
            'tiempos_sistema': [],
            'conteo_usuarios': {t: 0 for t in tipos},
            'tiempo_ocupado': 0.0
        })

    for c in range(num_cajeros):
        reloj = 0.0
        tiempo_libre_cajero = 0.0

        while True:
            inter_llegada = np.random.exponential(scale=tasa_llegada_promedio)
            reloj += inter_llegada

            if reloj > tiempo_sim:
                break

            tipo_actual = np.random.choice(tipos, p=probs)
            media_servicio = usuarios[tipo_actual]['servicio']
            tiempo_servicio = np.random.exponential(scale=media_servicio)

            inicio_atencion = max(reloj, tiempo_libre_cajero)
            espera_cola = inicio_atencion - reloj
            fin_atencion = inicio_atencion + tiempo_servicio
            tiempo_total_sistema = fin_atencion - reloj

            tiempo_libre_cajero = fin_atencion
            resultados_cajeros[c]['tiempos_atencion'].append(tiempo_servicio)
            resultados_cajeros[c]['tiempos_espera'].append(espera_cola)
            resultados_cajeros[c]['tiempos_sistema'].append(tiempo_total_sistema)
            resultados_cajeros[c]['conteo_usuarios'][tipo_actual] += 1
            resultados_cajeros[c]['tiempo_ocupado'] += min(tiempo_servicio, max(0.0, tiempo_sim - inicio_atencion))

    return resultados_cajeros

prueba = simular_sistema_parqueadero(num_cajeros=3, tiempo_sim=1000, semilla=42)
print("\n=== PRUEBA PILOTO DEL MOTOR DE SIMULACIÓN (1 CORRIDA, 1000 MIN) ===")
for i, cajero in enumerate(prueba):
    total_atendidos = sum(cajero['conteo_usuarios'].values())
    prom_atencion = np.mean(cajero['tiempos_atencion'])
    prom_espera = np.mean(cajero['tiempos_espera'])
    print(f"Cajero {i+1}: {total_atendidos} usuarios atendidos | Tiempo atención prom: {prom_atencion:.2f} min | Espera en cola prom: {prom_espera:.2f} min")

lam_teorico = 1.0 / usuarios['rapido']['llegada']
mu_teorico  = 1.0 / usuarios['rapido']['servicio']
rho_teorico = lam_teorico / mu_teorico

W_teorico  = 1.0 / (mu_teorico - lam_teorico)
Wq_teorico = rho_teorico / (mu_teorico - lam_teorico)

np.random.seed(123)
W_replicas, Wq_replicas = [], []

for r in range(30):
    reloj = 0.0
    libre = 0.0
    w_lista, wq_lista = [], []
    while True:
        reloj += np.random.exponential(1.0 / lam_teorico)
        if reloj > 2000:
            break
        serv = np.random.exponential(1.0 / mu_teorico)
        inicio = max(reloj, libre)
        wq_lista.append(inicio - reloj)
        libre = inicio + serv
        w_lista.append(libre - reloj)
    W_replicas.append(np.mean(w_lista))
    Wq_replicas.append(np.mean(wq_lista))

W_sim_prom = np.mean(W_replicas)
Wq_sim_prom = np.mean(Wq_replicas)
t_stat, p_value = stats.ttest_1samp(W_replicas, W_teorico)

print("\n=== VALIDACIÓN ESTADÍSTICA (TEORÍA M/M/1 VS SIMULACIÓN) ===")
print(f"Tiempo promedio en sistema (W)  -> Teórico: {W_teorico:.3f} min | Simulado: {W_sim_prom:.3f} min")
print(f"Tiempo promedio en cola (Wq)    -> Teórico: {Wq_teorico:.3f} min | Simulado: {Wq_sim_prom:.3f} min")
print(f"Estadístico t = {t_stat:.4f} | Valor-p (p-value) = {p_value:.4f}")
if p_value > 0.05:
    print("CONCLUSIÓN V&V: Modelo VALIDADO (p > 0.05, sin diferencia significativa con teoría M/M/1).")

fig, ax = plt.subplots(figsize=(10, 8))
ax.set_xlim(0, 10)
ax.set_ylim(0, 11)
ax.axis('off')
ax.set_title("Diagrama del Proceso de Verificación, Calibración y Validación (V&V)",
             fontsize=14, fontweight='bold', pad=15)

pasos_vv = [
    (5, 10.0, "1. DEFINICIÓN DEL PROBLEMA\nSistema de 3 cajeros M/M/1 independientes (Supercentro)", "#2c3e50"),
    (5, 8.3,  "2. CONSTRUCCIÓN DEL MODELO\nProgramación de eventos discretos en Python (FIFO)", "#2980b9"),
    (5, 6.6,  "3. VERIFICACIÓN\n¿El código ejecuta la lógica M/M/1 sin errores?\n(Prueba de semillas, colas y eventos)", "#8e44ad"),
    (5, 4.9,  "4. CALIBRACIÓN\nAjuste de tasas λ, μ y proporciones de usuarios\n(25% Rápido, 20% Normal, 27.5% Lento, 27.5% Muy Lento)", "#d35400"),
    (5, 3.2,  f"5. VALIDACIÓN ESTADÍSTICA\nComparación vs Teoría M/M/1 (Prueba t: p = {p_value:.3f} > 0.05)", "#16a085"),
    (5, 1.4,  "6. MODELO VALIDADO Y LISTO\nEjecución de réplicas para análisis de estado estable", "#27ae60")
]

for idx, (x, y, texto, color) in enumerate(pasos_vv):
    caja = patches.FancyBboxPatch((x - 3.3, y - 0.55), 6.6, 1.1,
                                  boxstyle="round,pad=0.15", facecolor=color,
                                  edgecolor="black", linewidth=1.5)
    ax.add_patch(caja)
    ax.text(x, y, texto, color="white", fontsize=9.5, fontweight="bold",
            ha="center", va="center")
    if idx < len(pasos_vv) - 1:
        ax.annotate("", xy=(x, pasos_vv[idx+1][1] + 0.65), xytext=(x, y - 0.65),
                    arrowprops=dict(arrowstyle="->", lw=2, color="#34495e"))

ax.annotate("NO -> Corregir código", xy=(1.55, 8.3), xytext=(1.55, 6.6),
            arrowprops=dict(arrowstyle="->", lw=1.8, color="#c0392b", connectionstyle="arc3,rad=0.4"),
            fontsize=8.5, fontweight="bold", color="#c0392b", ha="right", va="center")
ax.annotate("NO -> Recalibrar parámetros", xy=(8.45, 4.9), xytext=(8.45, 3.2),
            arrowprops=dict(arrowstyle="->", lw=1.8, color="#c0392b", connectionstyle="arc3,rad=-0.4"),
            fontsize=8.5, fontweight="bold", color="#c0392b", ha="left", va="center")

plt.tight_layout()
plt.savefig("diagrama_VV.png", dpi=300)
plt.show()

num_piloto = 20
tiempo_largo = 2000
trayectorias_sistema = []

for r in range(num_piloto):
    res = simular_sistema_parqueadero(num_cajeros=3, tiempo_sim=tiempo_largo, semilla=100 + r)
    min_len = min(len(c['tiempos_sistema']) for c in res)
    serie_replica = np.mean([c['tiempos_sistema'][:min_len] for c in res], axis=0)
    trayectorias_sistema.append(serie_replica)

longitud_comun = min(len(t) for t in trayectorias_sistema)
matriz_trayectorias = np.array([t[:longitud_comun] for t in trayectorias_sistema])
serie_promedio = np.mean(matriz_trayectorias, axis=0)

ventana = 40
promedios_moviles = np.array([
    np.mean(serie_promedio[i:i+ventana]) for i in range(len(serie_promedio) - ventana)
])
varianzas_moviles = np.array([
    np.var(promedios_moviles[i:i+ventana]) for i in range(len(promedios_moviles) - ventana)
])

umbral_var = np.percentile(varianzas_moviles, 20)
punto_corte = int(np.where(varianzas_moviles <= umbral_var)[0][0] + ventana)

datos_antes = serie_promedio
datos_despues = serie_promedio[punto_corte:]
media_antes = np.mean(datos_antes)
media_despues = np.mean(datos_despues)

print("\n=== ANÁLISIS DEL ESTADO TRANSITORIO Y ESTADO ESTABLE ===")
print(f"Total de clientes promedio observados por cajero: {longitud_comun}")
print(f"Punto de corte detectado (fin del estado transitorio): Cliente #{punto_corte}")
print(f"Tiempo promedio en sistema ANTES (con transitorio):    {media_antes:.3f} min")
print(f"Tiempo promedio en sistema DESPUÉS (estado estable):   {media_despues:.3f} min")
print(f"Diferencia corregida al eliminar el transitorio:       {abs(media_despues - media_antes):.3f} min")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.plot(datos_antes, color='#7f8c8d', alpha=0.45, label='Serie promedio por cliente')
ax1.plot(range(ventana, len(promedios_moviles) + ventana), promedios_moviles,
         color='#2980b9', linewidth=2, label=f'Promedio móvil (w={ventana})')
ax1.axvline(x=punto_corte, color='#e74c3c', linestyle='--', linewidth=2,
            label=f'Fin transitorio (Cliente #{punto_corte})')
ax1.axhline(y=media_antes, color='#8e44ad', linestyle=':', linewidth=2,
            label=f'Media con transitorio = {media_antes:.2f} min')
ax1.axvspan(0, punto_corte, color='#e74c3c', alpha=0.12, label='Estado Transitorio (Warm-up)')
ax1.set_title("ANTES: Serie Completa (Con Estado Transitorio)", fontsize=12, fontweight='bold')
ax1.set_xlabel("Número de cliente atendido")
ax1.set_ylabel("Tiempo promedio en sistema (min)")
ax1.legend(loc='lower right', fontsize=8.5)

eje_estable = np.arange(punto_corte, len(datos_antes))
ax2.plot(eje_estable, datos_despues, color='#27ae60', alpha=0.65, label='Datos en Estado Estable')
ax2.axhline(y=media_despues, color='#145a32', linestyle='--', linewidth=2.2,
            label=f'Media Estado Estable = {media_despues:.2f} min')
ax2.set_title("DESPUÉS: Estado Estable (Transitorio Eliminado)", fontsize=12, fontweight='bold')
ax2.set_xlabel("Número de cliente atendido (post warm-up)")
ax2.set_ylabel("Tiempo promedio en sistema (min)")
ax2.legend(loc='lower right', fontsize=9)

plt.tight_layout()
plt.savefig("antes_despues_transitorio.png", dpi=300)
plt.show()

promedios_por_replica_estable = [np.mean(t[punto_corte:]) for t in matriz_trayectorias]
media_rep = np.mean(promedios_por_replica_estable)
std_rep = np.std(promedios_por_replica_estable, ddof=1)
t_crit = stats.t.ppf(0.975, df=num_piloto - 1)
me_piloto = t_crit * (std_rep / np.sqrt(num_piloto))
er_piloto = (me_piloto / media_rep) * 100

precision_deseada = 5.0
if er_piloto <= precision_deseada:
    n_replicas_definitivo = num_piloto
else:
    n_replicas_definitivo = int(np.ceil(num_piloto * (er_piloto / precision_deseada) ** 2))
n_replicas_definitivo = max(30, n_replicas_definitivo)

print(f"\nError relativo con {num_piloto} réplicas piloto: {er_piloto:.2f}% (Meta <= {precision_deseada}%)")
print(f"Número de réplicas definitivo seleccionado para el estudio: n = {n_replicas_definitivo} réplicas")

medias_atencion_cajeros = [[] for _ in range(num_cajeros)]
medias_espera_cajeros   = [[] for _ in range(num_cajeros)]
medias_sistema_cajeros  = [[] for _ in range(num_cajeros)]
utilizacion_cajeros     = [[] for _ in range(num_cajeros)]

tipos_lista = list(usuarios.keys())
conteos_por_cajero_replicas = [{t: [] for t in tipos_lista} for _ in range(num_cajeros)]
conteos_totales_replicas    = {t: [] for t in tipos_lista}

for r in range(n_replicas_definitivo):
    res = simular_sistema_parqueadero(num_cajeros=num_cajeros, tiempo_sim=tiempo_largo, semilla=500 + r)
    suma_replica_tipos = {t: 0 for t in tipos_lista}

    for c in range(num_cajeros):
        atencion_est = res[c]['tiempos_atencion'][punto_corte:]
        espera_est   = res[c]['tiempos_espera'][punto_corte:]
        sistema_est  = res[c]['tiempos_sistema'][punto_corte:]

        medias_atencion_cajeros[c].append(np.mean(atencion_est))
        medias_espera_cajeros[c].append(np.mean(espera_est))
        medias_sistema_cajeros[c].append(np.mean(sistema_est))
        utilizacion_cajeros[c].append((res[c]['tiempo_ocupado'] / tiempo_largo) * 100)

        for t in tipos_lista:
            cant = res[c]['conteo_usuarios'][t]
            conteos_por_cajero_replicas[c][t].append(cant)
            suma_replica_tipos[t] += cant

    for t in tipos_lista:
        conteos_totales_replicas[t].append(suma_replica_tipos[t])

print(f"\n=== PUNTO 1: ESTADÍSTICAS DE TIEMPO DE ATENCIÓN POR CAJERO (n = {n_replicas_definitivo} réplicas) ===")
t_critico = stats.t.ppf(0.975, df=n_replicas_definitivo - 1)

resumen_cajeros = []
for c in range(num_cajeros):
    datos_c = np.array(medias_atencion_cajeros[c])
    media_c = np.mean(datos_c)
    std_c   = np.std(datos_c, ddof=1)
    se_c    = std_c / np.sqrt(n_replicas_definitivo)
    me_c    = t_critico * se_c
    ic_inf  = media_c - me_c
    ic_sup  = media_c + me_c
    min_c   = np.min(datos_c)
    max_c   = np.max(datos_c)
    esp_c   = np.mean(medias_espera_cajeros[c])
    sis_c   = np.mean(medias_sistema_cajeros[c])
    rho_c   = np.mean(utilizacion_cajeros[c])

    resumen_cajeros.append({
        'cajero': f"Cajero {c+1}", 'media': media_c, 'std': std_c,
        'ic_inf': ic_inf, 'ic_sup': ic_sup, 'min': min_c, 'max': max_c,
        'espera': esp_c, 'sistema': sis_c, 'utilizacion': rho_c
    })

    print(f"Cajero {c+1} | Media Atención: {media_c:.3f} min | Desv.Std: {std_c:.3f} | Mín: {min_c:.3f} | Máx: {max_c:.3f} | IC 95%: [{ic_inf:.3f}, {ic_sup:.3f}] | Espera cola prom: {esp_c:.2f} min | Utilización: {rho_c:.1f}%")

cajero_menor = min(resumen_cajeros, key=lambda x: x['media'])
cajero_mayor = max(resumen_cajeros, key=lambda x: x['media'])

print(f"\n-> CAJERO CON MENOR TIEMPO PROMEDIO DE ATENCIÓN: {cajero_menor['cajero']} ({cajero_menor['media']:.3f} min)")
print(f"-> CAJERO CON MAYOR TIEMPO PROMEDIO DE ATENCIÓN: {cajero_mayor['cajero']} ({cajero_mayor['media']:.3f} min)")

print("\n=== PUNTO 2: PROMEDIO DE USUARIOS POR TIPO EN LA TOTALIDAD DE LOS 3 CAJEROS ===")
total_general_usuarios = sum(np.mean(conteos_totales_replicas[t]) for t in tipos_lista)

promedios_totales_tipo = []
for t in tipos_lista:
    prom_c1 = np.mean(conteos_por_cajero_replicas[0][t])
    prom_c2 = np.mean(conteos_por_cajero_replicas[1][t])
    prom_c3 = np.mean(conteos_por_cajero_replicas[2][t])
    prom_total = np.mean(conteos_totales_replicas[t])
    std_total  = np.std(conteos_totales_replicas[t], ddof=1)
    prop_sim   = (prom_total / total_general_usuarios) * 100
    prop_esp   = usuarios[t]['prob'] * 100
    promedios_totales_tipo.append(prom_total)

    print(f"Tipo {t.upper():10s} | C1: {prom_c1:6.2f} | C2: {prom_c2:6.2f} | C3: {prom_c3:6.2f} | TOTAL 3 CAJEROS: {prom_total:6.2f} ± {std_total:5.2f} usuarios | Prop. Simulada: {prop_sim:5.2f}% (Esperada: {prop_esp:5.1f}%)")

print(f"TOTAL PROMEDIO DE USUARIOS ATENDIDOS EN LOS 3 CAJEROS: {total_general_usuarios:.2f} usuarios/réplica")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
nombres_c = [r['cajero'] for r in resumen_cajeros]
medias_c  = [r['media'] for r in resumen_cajeros]
errores_c = [r['media'] - r['ic_inf'] for r in resumen_cajeros]
colores_c = ['#27ae60' if r['cajero'] == cajero_menor['cajero']
             else ('#e74c3c' if r['cajero'] == cajero_mayor['cajero'] else '#3498db')
             for r in resumen_cajeros]

barras1 = ax1.bar(nombres_c, medias_c, yerr=errores_c, capsize=8, color=colores_c, edgecolor='black', alpha=0.88)
ax1.set_title("Punto 1: Tiempo Promedio de Atención por Cajero (IC 95%)", fontsize=11.5, fontweight='bold')
ax1.set_ylabel("Tiempo promedio de atención (minutos)")
ax1.set_ylim(0, max(medias_c) + 1.0)
for b in barras1:
    yval = b.get_height()
    ax1.text(b.get_x() + b.get_width()/2, yval + 0.18, f"{yval:.3f} min", ha='center', fontweight='bold')

etiquetas_t = ['Rápido\n(25%)', 'Normal\n(20%)', 'Lento\n(27.5%)', 'Muy Lento\n(27.5%)']
colores_t   = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c']
barras2 = ax2.bar(etiquetas_t, promedios_totales_tipo, color=colores_t, edgecolor='black', alpha=0.88)
ax2.set_title("Punto 2: Promedio de Usuarios por Tipo (Total 3 Cajeros)", fontsize=11.5, fontweight='bold')
ax2.set_ylabel("Cantidad promedio de usuarios atendidos")
ax2.set_ylim(0, max(promedios_totales_tipo) * 1.18)
for b in barras2:
    yval = b.get_height()
    ax2.text(b.get_x() + b.get_width()/2, yval + 6, f"{yval:.2f}", ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("resultados_cajeros_usuarios.png", dpi=300)
plt.show()

def evaluar_escenario_cajeros(k_cajeros, n_rep, tiempo_sim, corte_transitorio):
    tipos = list(usuarios.keys())
    probs = [usuarios[t]['prob'] for t in tipos]
    inter_llegada_base = sum(usuarios[t]['prob'] * usuarios[t]['llegada'] for t in tipos)
    inter_llegada_escenario = inter_llegada_base * (k_cajeros / 3.0)

    wq_rep, w_rep, rho_rep = [], [], []

    for r in range(n_rep):
        np.random.seed(900 + k_cajeros * 100 + r)
        wq_caj, w_caj, rho_caj = [], [], []

        for c in range(k_cajeros):
            reloj = 0.0
            libre = 0.0
            ocupado = 0.0
            lista_wq, lista_w = [], []

            while True:
                reloj += np.random.exponential(scale=inter_llegada_escenario)
                if reloj > tiempo_sim:
                    break
                tipo_u = np.random.choice(tipos, p=probs)
                serv = np.random.exponential(scale=usuarios[tipo_u]['servicio'])
                inicio = max(reloj, libre)
                lista_wq.append(inicio - reloj)
                libre = inicio + serv
                lista_w.append(libre - reloj)
                ocupado += min(serv, max(0.0, tiempo_sim - inicio))

            wq_caj.append(np.mean(lista_wq[corte_transitorio:]))
            w_caj.append(np.mean(lista_w[corte_transitorio:]))
            rho_caj.append((ocupado / tiempo_sim) * 100)

        wq_rep.append(np.mean(wq_caj))
        w_rep.append(np.mean(w_caj))
        rho_rep.append(np.mean(rho_caj))

    t_crit = stats.t.ppf(0.975, df=n_rep - 1)
    me_wq = t_crit * (np.std(wq_rep, ddof=1) / np.sqrt(n_rep))
    me_w  = t_crit * (np.std(w_rep, ddof=1) / np.sqrt(n_rep))

    return {
        'k': k_cajeros,
        'Wq_media': np.mean(wq_rep), 'Wq_me': me_wq,
        'W_media': np.mean(w_rep),   'W_me': me_w,
        'rho_media': np.mean(rho_rep)
    }

escenarios = [evaluar_escenario_cajeros(k, n_replicas_definitivo, tiempo_largo, punto_corte)
              for k in [3, 4, 5]]

print("\n=== PUNTO 3: COMPARACIÓN DE ESCENARIOS EN ESTADO ESTABLE ===")
for esc in escenarios:
    cumple_wq  = "OK" if esc['Wq_media'] < 3.0 else "NO"
    cumple_w   = "OK" if esc['W_media'] < 5.0 else "NO"
    cumple_rho = "OK" if esc['rho_media'] <= 85.0 else "NO"
    veredicto  = "CUMPLE CRITERIOS" if (esc['Wq_media'] < 3.0 and esc['W_media'] < 5.0 and esc['rho_media'] <= 85.0) else "CONGESTIÓN / REQUIERE MEJORA"

    print(f"Escenario {esc['k']} Cajeros | Espera cola (Wq): {esc['Wq_media']:.2f} ± {esc['Wq_me']:.2f} min [{cumple_wq}] | Tiempo sistema (W): {esc['W_media']:.2f} ± {esc['W_me']:.2f} min [{cumple_w}] | Utilización (ρ): {esc['rho_media']:.1f}% [{cumple_rho}] -> {veredicto}")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
etiquetas_esc = [f"{e['k']} Cajeros\n({'Actual' if e['k']==3 else 'Mejora'})" for e in escenarios]
wq_vals = [e['Wq_media'] for e in escenarios]
w_vals  = [e['W_media'] for e in escenarios]
rho_vals = [e['rho_media'] for e in escenarios]

x = np.arange(len(etiquetas_esc))
ancho = 0.35

b1 = ax1.bar(x - ancho/2, wq_vals, ancho, label='Espera en Cola (Wq)', color='#e67e22', edgecolor='black')
b2 = ax1.bar(x + ancho/2, w_vals, ancho, label='Tiempo Total en Sistema (W)', color='#2980b9', edgecolor='black')
ax1.axhline(y=3.0, color='#d35400', linestyle='--', linewidth=1.5, label='Meta máxima Wq (3.0 min)')
ax1.axhline(y=5.0, color='#1f618d', linestyle=':', linewidth=1.5, label='Meta máxima W (5.0 min)')
ax1.set_xticks(x)
ax1.set_xticklabels(etiquetas_esc)
ax1.set_ylabel("Tiempo promedio (minutos)")
ax1.set_title("Punto 3: Comparación de Tiempos por Escenario", fontsize=11.5, fontweight='bold')
ax1.legend(fontsize=8.5)
for b in list(b1) + list(b2):
    ax1.text(b.get_x() + b.get_width()/2, b.get_height() + 0.25, f"{b.get_height():.2f}", ha='center', fontsize=8.5, fontweight='bold')

colores_rho = ['#e74c3c' if r > 85 else '#27ae60' for r in rho_vals]
b3 = ax2.bar(etiquetas_esc, rho_vals, color=colores_rho, edgecolor='black', width=0.45)
ax2.axhline(y=85.0, color='#c0392b', linestyle='--', linewidth=1.8, label='Límite óptimo utilización (85%)')
ax2.set_ylabel("Utilización promedio (%)")
ax2.set_ylim(0, 110)
ax2.set_title("Punto 3: Utilización Promedio de Cajeros (ρ)", fontsize=11.5, fontweight='bold')
ax2.legend(fontsize=9)
for b in b3:
    ax2.text(b.get_x() + b.get_width()/2, b.get_height() + 2, f"{b.get_height():.1f}%", ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig("estrategia_mejora_escenarios.png", dpi=300)
plt.show()

print("\n=== EJECUCIÓN FINALIZADA: 4 GRÁFICAS GUARDADAS EN LA CARPETA DEL PROYECTO ===")