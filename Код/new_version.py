import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

# ==========================================
# 1. ПАРАМЕТРЫ МОДЕЛИ
# ==========================================
# Временные масштабы: 0 < epsilon << mu << 1
mu = 0.01          # Медленный масштаб (переменная y)
epsilon = 0.001    # Сверхмедленный масштаб (переменная z)

# Параметры с листа преподавателя:
k = -7.7
b = 8.1

# Параметры сверхмедленной переменной z (уравнение 1):
A = 1.0            # Коэффициент связи по току
x_eq = 0.74      # Равновесный потенциал 2D-подсистемы при z = 0

# ==========================================
# 2. ПРАВЫЕ ЧАСТИ СИСТЕМЫ ОДУ (1)-(2)
# ==========================================
def neuron_3d_system(t, state, mu, epsilon, k, b, A, x_eq):
    x, y, z = state
    
    # 1. Быстрое уравнение мембранного потенциала
    dx = - (2 * x) / (1 + x**2) + y - z
    
    # 2. Кусочно-линейная функция G(x, y) для медленной переменной y (ур-ние 2)
    lin = -x + k * y + b
    if -2 < y < 2:
        G = lin
    elif lin <= -y - 2:
        G = -y - 2
    elif lin >= -y + 2:
        G = -y + 2
    else:
        G = lin
    dy = mu * G
    
    # 3. Сверхмедленное уравнение адаптации z
    dz = epsilon * (A * (x - x_eq) - z)
    
    return [dx, dy, dz]

# ==========================================
# 3. ПОИСК СОСТОЯНИЙ РАВНОВЕСИЯ И АНАЛИЗ УСТОЙЧИВОСТИ
# ==========================================
def find_3d_equilibria(k, b, A, x_eq, mu, epsilon):
    """
    При равновесии:
    z* = A * (x* - x_eq)
    y* = 2*x* / (1 + x*^2) + z*
    G(x*, y*) = 0  =>  -x* + k*y* + b = 0 (в центр. области)
    """
    # Подстановка дает уравнение относительно x*:
    # -x* + k*( 2*x*/(1+x*^2) + A*(x* - x_eq) ) + b = 0
    # При A = 0 или z* = 0 это сводится к базовому кубическому полиному.
    # Найдем корни уравнения численно в рабочей области:
    def eq_residual(x_val):
        z_val = A * (x_val - x_eq)
        y_val = (2 * x_val) / (1 + x_val**2) + z_val
        return -x_val + k * y_val + b

    # Сканируем диапазон для поиска нулей
    xs = np.linspace(-3, 8, 1000)
    res = eq_residual(xs)
    sign_changes = np.where(np.diff(np.sign(res)))[0]
    
    equilibria = []
    for idx in sign_changes:
        # Уточняем корень методом деления отрезка / секущих
        x0, x1 = xs[idx], xs[idx+1]
        for _ in range(30):
            xm = 0.5 * (x0 + x1)
            if eq_residual(x0) * eq_residual(xm) <= 0:
                x1 = xm
            else:
                x0 = xm
        x_star = 0.5 * (x0 + x1)
        z_star = A * (x_star - x_eq)
        y_star = (2 * x_star) / (1 + x_star**2) + z_star
        
        # Матрица Якоби 3x3 в точке (x*, y*, z*):
        df_dx = 2 * (x_star**2 - 1) / (1 + x_star**2)**2
        df_dy = 1.0
        df_dz = -1.0
        
        dg_dx = -mu
        dg_dy = mu * k
        dg_dz = 0.0
        
        dh_dx = epsilon * A
        dh_dy = 0.0
        dh_dz = -epsilon
        
        J = np.array([
            [df_dx, df_dy, df_dz],
            [dg_dx, dg_dy, dg_dz],
            [dh_dx, dh_dy, dh_dz]
        ])
        
        # Собственные значения матрицы Якоби
        eigvals = np.linalg.eigvals(J)
        real_parts = np.real(eigvals)
        
        # Классификация устойчивости по знакам вещественных частей
        if np.all(real_parts < 0):
            eq_type = "Устойчивое равновесие"
            color = "black"
        elif np.all(real_parts > 0):
            eq_type = "Неустойчивый репеллер"
            color = "red"
        else:
            eq_type = "Седловая особенность"
            color = "purple"
            
        equilibria.append({
            "x": x_star, "y": y_star, "z": z_star,
            "type": eq_type, "color": color, "eigvals": eigvals
        })
        
    return equilibria

# Вывод найденных точек в консоль
eq_points = find_3d_equilibria(k, b, A, x_eq, mu, epsilon)
print(f"--- Найденные равновесия для 3D системы (k={k}, b={b}) ---")
for i, pt in enumerate(eq_points, 1):
    print(f"{i}. (x={pt['x']:.4f}, y={pt['y']:.4f}, z={pt['z']:.4f}) | {pt['type']}")
    print(f"   Собственные числа: {pt['eigvals']}")

# ==========================================
# 4. ЧИСЛЕННОЕ ИНТЕГРИРОВАНИЕ (ОДНА ТОЧКА)
# ==========================================
# Интервал времени увеличен, так как epsilon = 0.001 требует долгой симуляции
t_span = (0, 4000)
t_eval = np.linspace(t_span[0], t_span[1], 40000)

# ОДНА начальная точка [x0, y0, z0] по требованию преподавателя:
initial_condition = [0.1, 0.1, 0.0]

sol = solve_ivp(
    neuron_3d_system, t_span, initial_condition,
    args=(mu, epsilon, k, b, A, x_eq),
    t_eval=t_eval, method='Radau', rtol=1e-6, atol=1e-8
)

# ==========================================
# 5. ВИЗУАЛИЗАЦИЯ
# ==========================================
fig = plt.figure(figsize=(15, 6))

# --- Левый график: 3D фазовый портрет (x, y, z) ---
ax1 = fig.add_subplot(1, 2, 1, projection='3d')

# Траектория
ax1.plot(sol.y[0], sol.y[1], sol.y[2], color='#1f77b4', linewidth=0.8, label='Фазовая траектория')

# Начальная точка
ax1.scatter([initial_condition[0]], [initial_condition[1]], [initial_condition[2]], 
            color='green', s=60, label='Старт')

# Точки равновесия
for pt in eq_points:
    ax1.scatter([pt['x']], [pt['y']], [pt['z']], color=pt['color'], s=70, marker='o', label=pt['type'])

ax1.set_xlabel('x (потенциал)', fontsize=10, labelpad=8)
ax1.set_ylabel('y (медленный ток)', fontsize=10, labelpad=8)
ax1.set_zlabel('z (адаптация)', fontsize=10, labelpad=8)
ax1.set_title(f'3D фазовый портрет (k={k}, b={b})', fontsize=12)
ax1.legend(loc='upper right', fontsize=8)
ax1.view_init(elev=25, azim=45)

# --- Правый график: Временная реализация x(t) (Бёрстинг / ММО) ---
ax2 = fig.add_subplot(1, 2, 2)
ax2.plot(sol.t, sol.y[0], color='#d62728', linewidth=0.8)
ax2.set_xlabel('Время t', fontsize=11)
ax2.set_ylabel('Мембранный потенциал x(t)', fontsize=11)
ax2.set_title('Временная реализация (пачечная активность / бёрстинг)', fontsize=12)
ax2.set_xlim([0, 4000])
ax2.grid(True, linestyle=':', alpha=0.6)

plt.tight_layout()
plt.show()