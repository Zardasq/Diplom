import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- ПАРАМЕТРЫ МОДЕЛИ ---
mu = 0.01
beta = 1.0
k = 0.7
b = 0.1

def G_slow(x, y, k, b):
    # Медленная нелинейность (из статьи)
    if -2.0 < y < 2.0: return -x + (k * y + b)
    elif y >= 2.0 and (-x + k * y + b < -y - 2.0): return -y - 2.0
    elif y <= -2.0 and (-x + k * y + b > -y + 2.0): return -y + 2.0
    else: return -x + k * y + b

# =====================================================================
# 2. ПОСТРОЕНИЕ 4D СИСТЕМЫ (ДВА СВЯЗАННЫХ НЕЙРОНА)
# =====================================================================
def coupled_4d_system(t, state, mu, beta, k, b, gamma):
    x1, y1, x2, y2 = state
    
    # Ток связи (gap junction). Делится на mu, так как связь мгновенная по быстрой переменной
    coupling_1 = gamma * (x2 - x1)
    coupling_2 = gamma * (x1 - x2)
    
    # Осциллятор 1
    dx1 = (-2.0 * beta * x1 / (1.0 + beta * x1**2) + y1 + coupling_1) / mu
    dy1 = G_slow(x1, y1, k, b)
    
    # Осциллятор 2
    dx2 = (-2.0 * beta * x2 / (1.0 + beta * x2**2) + y2 + coupling_2) / mu
    dy2 = G_slow(x2, y2, k, b)
    
    return [dx1, dy1, dx2, dy2]

# Разные начальные условия, чтобы показать рассинхронизацию изначально
init_state = [0.0, -1.0, 1.5, -0.5] 
t_span = (0, 150)
t_eval = np.linspace(t_span[0], t_span[1], 5000)

# 1. Запуск без связи (Асинхронный режим)
gamma_zero = 0.0
sol_async = solve_ivp(coupled_4d_system, t_span, init_state, t_eval=t_eval, 
                      args=(mu, beta, k, b, gamma_zero), method='RK45')

# 2. Запуск со связью (Режим синхронизации)
gamma_sync = 0.15
sol_sync = solve_ivp(coupled_4d_system, t_span, init_state, t_eval=t_eval, 
                     args=(mu, beta, k, b, gamma_sync), method='RK45')

# --- ВИЗУАЛИЗАЦИЯ СИНХРОНИЗАЦИИ ---
plt.figure(figsize=(12, 8))

# График 1: Нет связи
plt.subplot(2, 1, 1)
plt.plot(sol_async.t, sol_async.y[0], 'b-', linewidth=1.5, label='Нейрон 1')
plt.plot(sol_async.t, sol_async.y[2], 'r--', linewidth=1.5, label='Нейрон 2')
plt.title(f'Асинхронный режим (Связь $\gamma = 0$)')
plt.ylabel('Мембранный потенциал $x$')
plt.legend(loc='upper right')
plt.grid(True)

# График 2: Есть диффузионная связь
plt.subplot(2, 1, 2)
plt.plot(sol_sync.t, sol_sync.y[0], 'b-', linewidth=1.5, label='Нейрон 1')
plt.plot(sol_sync.t, sol_sync.y[2], 'r--', linewidth=1.5, label='Нейрон 2')
plt.title(f'Фазовая синхронизация (Связь $\gamma = {gamma_sync}$)')
plt.xlabel('Время $t$')
plt.ylabel('Мембранный потенциал $x$')
plt.legend(loc='upper right')
plt.grid(True)

plt.tight_layout()
plt.show()