import time
import numpy as np
import matplotlib.pyplot as plt
from numba import njit

# --- 1. Параметры системы ---
K = -2.0
B = 4.0
MU = 0.01
EPS = 0.0001
A = 1.0

# Параметры бифуркационной диаграммы (Рис. 8)
X_EQ_MIN = 0.740
X_EQ_MAX = 0.780
NUM_POINTS = 600  # 600 точек для плавного графика

# --- 2. Скомпилированные функции системы (Numba) ---
@njit
def derivatives(x, y, z, x_eq):
    # Быстрая подсистема f(x) = 2x / (1 + x^2)
    fx = (2.0 * x) / (1.0 + x * x)
    dx = -fx + y - z

    # Кусочно-линейная функция G(x, y)
    term = -x + K * y + B
    upper = -y + 2.0
    lower = -y - 2.0
    if term >= upper:
        g = upper
    elif term <= lower:
        g = lower
    else:
        g = term

    dy = MU * g
    dz = EPS * (A * (x - x_eq) - z)
    return dx, dy, dz

@njit
def rk4_step(x, y, z, x_eq, dt):
    k1x, k1y, k1z = derivatives(x, y, z, x_eq)
    k2x, k2y, k2z = derivatives(x + 0.5*dt*k1x, y + 0.5*dt*k1y, z + 0.5*dt*k1z, x_eq)
    k3x, k3y, k3z = derivatives(x + 0.5*dt*k2x, y + 0.5*dt*k2y, z + 0.5*dt*k2z, x_eq)
    k4x, k4y, k4z = derivatives(x + dt*k3x, y + dt*k3y, z + dt*k3z, x_eq)

    xn = x + (dt / 6.0) * (k1x + 2.0*k2x + 2.0*k3x + k4x)
    yn = y + (dt / 6.0) * (k1y + 2.0*k2y + 2.0*k3y + k4y)
    zn = z + (dt / 6.0) * (k1z + 2.0*k2z + 2.0*k3z + k4z)
    return xn, yn, zn

@njit
def compute_diagram(x_eq_values, dt=0.1, t_init=20000.0, t_trans=10000.0, t_rec=20000.0):
    # Начальное состояние
    x, y, z = 1.0, 1.5, 0.5

    # Предварительный прогрев в первой точке, чтобы выйти на аттрактор
    init_steps = int(t_init / dt)
    for _ in range(init_steps):
        x, y, z = rk4_step(x, y, z, x_eq_values[0], dt)

    trans_steps = int(t_trans / dt)
    rec_steps = int(t_rec / dt)

    # Списки для сохранения результатов
    out_xeq = []
    out_xmax = []

    for i in range(len(x_eq_values)):
        x_eq = x_eq_values[i]

        # 1. Пропускаем переходный процесс
        for _ in range(trans_steps):
            x, y, z = rk4_step(x, y, z, x_eq, dt)

        # 2. Записываем локальные максимумы на установившемся режиме
        x_prev2 = x
        x, y, z = rk4_step(x, y, z, x_eq, dt)
        x_prev1 = x

        for _ in range(rec_steps):
            x, y, z = rk4_step(x, y, z, x_eq, dt)

            # Проверка условия локального максимума: x_prev2 < x_prev1 > x
            if x_prev1 > x_prev2 and x_prev1 > x:
                # Параболическая интерполяция для точного значения пика
                denom = x_prev2 - 2.0 * x_prev1 + x
                if denom != 0.0:
                    peak = x_prev1 - 0.125 * ((x_prev2 - x) ** 2) / denom
                else:
                    peak = x_prev1

                out_xeq.append(x_eq)
                out_xmax.append(peak)

            x_prev2 = x_prev1
            x_prev1 = x

    return np.array(out_xeq), np.array(out_xmax)

# --- 3. Запуск расчета ---
if __name__ == "__main__":
    start_time = time.time()
    x_eq_values = np.linspace(X_EQ_MIN, X_EQ_MAX, NUM_POINTS)

    print(f"Запуск расчета для {NUM_POINTS} точек (первый запуск включает компиляцию Numba)...")
    X_eq_plot, X_max_plot = compute_diagram(x_eq_values)
    
    elapsed = time.time() - start_time
    print(f"Готово! Найдено {len(X_max_plot)} экстремумов за {elapsed:.2f} сек.")

    # --- 4. Построение графика (Рис. 8) ---
    plt.figure(figsize=(10, 5), dpi=150)
    plt.scatter(X_eq_plot, X_max_plot, s=0.15, color='black', alpha=0.6, edgecolors='none')

    plt.xlim(X_EQ_MIN, X_EQ_MAX)
    plt.ylim(0.8, 7.2)

    plt.xlabel('$x_{eq}$', fontsize=14, fontweight='bold')
    plt.ylabel('$x_{max}$', fontsize=14, fontweight='bold')
    plt.title('Бифуркационная диаграмма $x_{max}(x_{eq})$ (Рис. 8)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()