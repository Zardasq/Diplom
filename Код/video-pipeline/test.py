import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# --- ПАРАМЕТРЫ МОДЕЛИ ---
mu = 0.01
beta = 1.0
k = 0.7
b = 0.1

# =====================================================================
# 1.1 АНАЛИТИЧЕСКИЙ ПОИСК СОСТОЯНИЙ РАВНОВЕСИЯ (МЕТОД КАРДАНО)
# =====================================================================
def find_equilibria(b, k, beta=1.0):
    """Нахождение стационарных точек системы по формулам Кардано (ур. 5-9)"""
    P1 = 1 - 2*k - (b**2)/3
    Q1 = - (2 * b**3)/27 - (2 * b * (1 + k))/3
    
    # Дискриминант (ур. 6)
    Delta1 = (Q1 / 2)**2 + (P1 / 3)**3
    
    roots_x = []
    if Delta1 > 0:
        # Одно состояние равновесия (ур. 7)
        A = -Q1/2 + np.sqrt(Delta1)
        B = -Q1/2 - np.sqrt(Delta1)
        u1 = np.cbrt(A) if A >= 0 else -np.cbrt(-A)
        v1 = np.cbrt(B) if B >= 0 else -np.cbrt(-B)
        x1 = u1 + v1 + b/3
        roots_x.append(x1)
    else:
        # Три состояния равновесия (ур. 8, 9)
        R = 2 * np.sqrt(-P1 / 3)
        arg = np.clip((-Q1 / 2) / np.sqrt(-(P1 / 3)**3), -1.0, 1.0)
        theta = np.arccos(arg)
        for j in range(3):
            xj = b/3 + R * np.cos((theta + 2 * np.pi * j) / 3)
            roots_x.append(xj)
            
    # Вычисляем y_* через быструю изоклину
    equilibria = [(x, 2 * beta * x / (1 + beta * x**2)) for x in roots_x]
    return equilibria, Delta1

# Вывод результатов поиска равновесий
eq_points, delta = find_equilibria(b, k, beta)
print(f"Дискриминант Delta1 = {delta:.4f}")
print(f"Найдено стационарных точек: {len(eq_points)}")
for idx, (eq_x, eq_y) in enumerate(eq_points):
    print(f"  Точка {idx+1}: x* = {eq_x:.4f}, y* = {eq_y:.4f}")


# =====================================================================
# 1.2 ОПРЕДЕЛЕНИЕ ФУНКЦИЙ СИСТЕМЫ И ИЗОКЛИН (ПРЕДЕЛЬНЫЙ ЦИКЛ)
# =====================================================================
def G_slow(x, y, k, b):
    if -2.0 < y < 2.0:
        return -x + (k * y + b)
    elif y >= 2.0 and (-x + k * y + b < -y - 2.0):
        return -y - 2.0
    elif y <= -2.0 and (-x + k * y + b > -y + 2.0):
        return -y + 2.0
    else:
        return -x + k * y + b

def single_neuron(t, state, mu, beta, k, b):
    x, y = state
    # Обратите внимание: делим на mu, как в вашем коде (масштабирование времени)
    dx = (-2.0 * beta * x / (1.0 + beta * x**2) + y) / mu
    dy = G_slow(x, y, k, b)
    return [dx, dy]

# Численное интегрирование для визуализации предельного цикла
sol = solve_ivp(single_neuron, (0, 100), [0.1, -1.0], args=(mu, beta, k, b), max_step=0.01)

# --- ВИЗУАЛИЗАЦИЯ: ФАЗОВЫЙ ПОРТРЕТ И ИЗОКЛИНЫ ---
plt.figure(figsize=(12, 5))

# График 1: Фазовый портрет
plt.subplot(1, 2, 1)
plt.plot(sol.y[0], sol.y[1], 'b-', label='Траектория (Предельный цикл)')

# Строим быструю изоклину (dx/dt = 0)
x_iso = np.linspace(-10, 10, 400)
y_fast = 2 * beta * x_iso / (1 + beta * x_iso**2)
plt.plot(x_iso, y_fast, 'r--', label='Быстрая изоклина ($\dot{x}=0$)')

# Строим медленную изоклину (dy/dt = 0) с помощью contour
y_iso = np.linspace(-3, 3, 400)
X_grid, Y_grid = np.meshgrid(x_iso, y_iso)
Z_slow = np.zeros_like(X_grid)
for i in range(X_grid.shape[0]):
    for j in range(X_grid.shape[1]):
        Z_slow[i,j] = G_slow(X_grid[i,j], Y_grid[i,j], k, b)
plt.contour(X_grid, Y_grid, Z_slow, levels=[0], colors='green', linestyles='--', linewidths=2)

# Отмечаем стационарные точки
for eq_x, eq_y in eq_points:
    plt.plot(eq_x, eq_y, 'ko', markersize=8, label='Состояние равновесия' if eq_x == eq_points[0][0] else "")

plt.title(f'Фазовый портрет (b={b}, k={k})')
plt.xlabel('x (мембранный потенциал)')
plt.ylabel('y (медленная переменная)')
plt.legend()
plt.grid(True)

# График 2: Бифуркационная диаграмма (Уравнения 10 и 11 из методички)
plt.subplot(1, 2, 2)
b_vals = np.linspace(0, 12, 400)
k_vals = np.linspace(-10, 1, 400)
B, K = np.meshgrid(b_vals, k_vals)

# Уравнение кривой Седло-узла (ур. 10)
SN = 8*K**3 + (B**2 - 12)*K**2 + (6 - 10*B**2)*K - (B**2 + 1)**2
plt.contour(B, K, SN, levels=[0], colors='blue', linewidths=2)

# Уравнение кривой Андронова-Хопфа (ур. 11)
Hopf = (mu**3 * K**7 - 2*mu**2 * K**6 + 2*mu**2 * K**5 + 
        2*mu*(B**2 * mu - mu - 2)*K**4 + mu*(5 - B**2)*K**3 + 
        (6*B**2 * mu - 2*mu - 2)*K**2 + (B**4 * mu + 2*B**2 * mu + mu + 4)*K + 
        (2*B**2 - 2))

# Ограничение физической реализуемости |k| < 1/sqrt(mu)
valid_hopf = np.abs(K) < 1 / np.sqrt(mu)
Hopf_masked = np.ma.masked_where(~valid_hopf, Hopf)
plt.contour(B, K, Hopf_masked, levels=[0], colors='red', linewidths=2)

plt.plot(b, k, 'g*', markersize=12, label='Текущая точка параметров')
plt.title('Бифуркационная диаграмма (b, k)')
plt.xlabel('Параметр b')
plt.ylabel('Параметр k')
plt.grid(True)
# Ручные легенды для контуров
plt.plot([], [], 'b-', linewidth=2, label='SN (Седло-узел)')
plt.plot([], [], 'r-', linewidth=2, label='Hopf (Хопф)')
plt.legend()

plt.tight_layout()
plt.show()