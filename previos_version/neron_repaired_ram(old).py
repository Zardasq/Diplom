import sys, warnings
import traceback

def custom_excepthook(exc_type, exc_val, exc_tb):
    print("\n--- КРИТИЧЕСКАЯ ОШИБКА PYTHON --")
    traceback.print_exception(exc_type, exc_val, exc_tb)
    print("----------------------------------\n")
    sys.exit(1)

sys.excepthook = custom_excepthook
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel,
                             QPushButton, QListWidget, QListWidgetItem, QMenu, QMessageBox, QComboBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QGroupBox, QScrollArea,
                             QDialog, QCheckBox, QDialogButtonBox, QFileDialog, QGridLayout, QStyleFactory)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from scipy.integrate import solve_ivp
from numba import njit

plt.rcParams.update({
    'font.size': 21,
    'axes.titlesize': 23,
    'axes.labelsize': 22,
    'legend.fontsize': 29,
    'xtick.labelsize': 20,
    'ytick.labelsize': 20,
    'savefig.dpi': 300,
})



def get_available_memory_bytes():
    """Возвращает приблизительный объём доступной физической памяти в байтах."""
    try:
        import psutil
        return int(psutil.virtual_memory().available)
    except Exception:
        pass

    if sys.platform == "win32":
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullAvailPhys)
        except Exception:
            pass

    try:
        return int(os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except Exception:
        # Консервативный запасной вариант, если ОС не позволяет узнать RAM.
        return 4 * 1024 ** 3


APP_STYLESHEET = """
QMainWindow, QWidget#AppRoot {
    background: #f5f7fb;
    color: #1f2937;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #d8dee9;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 10px 10px 10px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 6px;
    color: #4b5563;
    font-weight: 600;
}
QLabel {
    color: #374151;
}
QLabel#StatusLabel {
    background: #eef2ff;
    border: 1px solid #dbe3ff;
    border-radius: 6px;
    color: #3730a3;
    font-weight: 600;
    padding: 7px 10px;
}
QLabel#StatusLabel[state="ready"] {
    background: #ecfdf5;
    border-color: #bbf7d0;
    color: #166534;
}
QLabel#StatusLabel[state="working"] {
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
}
QLabel#StatusLabel[state="accent"] {
    background: #faf5ff;
    border-color: #e9d5ff;
    color: #7e22ce;
}
QLabel#StatusLabel[state="warning"] {
    background: #fff7ed;
    border-color: #fed7aa;
    color: #c2410c;
}
QLabel#StatusLabel[state="error"] {
    background: #fff1f2;
    border-color: #fecdd3;
    color: #be123c;
}
QLineEdit, QComboBox {
    color: #1f2937;
    background: #ffffff;
    border: 1px solid #cfd7e3;
    border-radius: 6px;
    min-height: 26px;
    padding: 3px 8px;
    selection-background-color: #2563eb;
}
QLineEdit:focus, QComboBox:focus {
    border: 1px solid #2563eb;
}
QCheckBox {
    color: #1f2937;
    spacing: 7px;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #cfd7e3;
    border-radius: 6px;
    color: #1f2937;
    font-weight: 600;
    min-height: 28px;
    padding: 5px 12px;
}
QPushButton:hover {
    background: #f8fafc;
    border-color: #94a3b8;
}
QPushButton:pressed {
    background: #edf2f7;
}
QPushButton:disabled {
    background: #eef1f5;
    color: #9aa4b2;
    border-color: #dde3ec;
}
QPushButton[role="primary"] {
    background: #2563eb;
    border-color: #1d4ed8;
    color: #ffffff;
}
QPushButton[role="primary"]:hover {
    background: #1d4ed8;
}
QPushButton[role="secondary"] {
    background: #eff6ff;
    border-color: #bfdbfe;
    color: #1d4ed8;
}
QPushButton[role="secondary"]:hover {
    background: #dbeafe;
}
QPushButton[role="accent"] {
    background: #f59e0b;
    border-color: #d97706;
    color: #111827;
}
QPushButton[role="accent"]:hover {
    background: #fbbf24;
}
QPushButton[role="danger"] {
    background: #fff1f2;
    border-color: #fecdd3;
    color: #be123c;
}
QPushButton[role="danger"]:hover {
    background: #ffe4e6;
}
QTabWidget::pane {
    background: #ffffff;
    border: 1px solid #d8dee9;
    border-radius: 8px;
    top: -1px;
}
QTabBar::tab {
    background: #e8edf5;
    border: 1px solid #d8dee9;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #4b5563;
    font-weight: 600;
    padding: 8px 14px;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #111827;
}
QTableWidget, QListWidget {
    background: #ffffff;
    alternate-background-color: #f8fafc;
    border: 1px solid #d8dee9;
    border-radius: 6px;
    gridline-color: #e5e7eb;
}
QHeaderView::section {
    background: #eef2f7;
    border: none;
    border-right: 1px solid #d8dee9;
    color: #374151;
    font-weight: 700;
    padding: 7px;
}
QProgressBar {
    background: #e8edf5;
    border: 1px solid #d8dee9;
    border-radius: 6px;
    color: #374151;
    min-height: 16px;
    text-align: center;
}
QProgressBar::chunk {
    background: #2563eb;
    border-radius: 5px;
}
QScrollArea, QToolBar {
    background: transparent;
    border: none;
}
"""

PLOT_BACKGROUND = "#ffffff"
PLOT_GRID = "#e3e8ef"
MAX_ISI_PLOT_POINTS = 50000
MAX_BIFURCATION_PLOT_POINTS = 300000
MAX_BIFURCATION_POINTS_PER_STEP = 1500


def clean_isi_values(values):
    try:
        arr = np.asarray(values, dtype=np.float64).ravel()
    except (TypeError, ValueError):
        return np.array([], dtype=np.float64)

    if arr.size == 0:
        return arr

    arr = arr[np.isfinite(arr)]
    return arr[arr > 0.0]


def clean_xy_values(x_values, y_values, positive_y=False):
    try:
        x = np.asarray(x_values, dtype=np.float64).ravel()
        y = np.asarray(y_values, dtype=np.float64).ravel()
    except (TypeError, ValueError):
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    n = min(x.size, y.size)
    if n == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    x, y = x[:n], y[:n]
    mask = np.isfinite(x) & np.isfinite(y)
    if positive_y:
        mask &= y > 0.0
    return x[mask], y[mask]


def downsample_indices(size, limit):
    if size <= limit:
        return slice(None)
    return np.linspace(0, size - 1, limit, dtype=np.int64)



@njit(fastmath=True, cache=True)
def equations_scalar(x, y, z, A, x_eq, k, b, mu, ep):
    dx = -2.0 * x / (1.0 + x * x) + y - z
    f = -x + k * y + b
    upper = -y + 2.0
    lower = -y - 2.0
    if f >= upper:
        dy = upper
    elif f <= lower:
        dy = lower
    else:
        dy = f
    return dx, mu * dy, ep * (A * (x - x_eq) - z)


@njit(fastmath=True, cache=True)
def equations_njit(t, s, A, x_eq, k, b, mu, ep):
    dx, dy, dz = equations_scalar(s[0], s[1], s[2], A, x_eq, k, b, mu, ep)
    return np.array([dx, dy, dz])


@njit(fastmath=True, cache=True)
def jacobian_njit(s, A, k, b, mu, ep):
    x, y, z = s[0], s[1], s[2]
    J = np.zeros((3, 3))

    # Производные dx/dt
    J[0, 0] = 2.0 * (x ** 2 - 1.0) / ((1.0 + x ** 2) ** 2)
    J[0, 1] = 1.0
    J[0, 2] = -1.0

    f = -x + k * y + b
    if f <= -y - 2.0:
        J[1, 0] = 0.0
        J[1, 1] = -mu
    elif f >= -y + 2.0:
        J[1, 0] = 0.0
        J[1, 1] = -mu
    else:
        J[1, 0] = -mu
        J[1, 1] = mu * k

    J[2, 0] = ep * A
    J[2, 2] = -ep

    return J

@njit(fastmath=True, cache=True)
def get_xmax_on_the_fly(s_start, A, x_eq, k, b, mu, ep, dt, t_trans, t_meas):
    x, y, z = s_start[0], s_start[1], s_start[2]

    for _ in range(int(t_trans / dt)):
        x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)

    steps_meas = int(t_meas / dt)
    max_peaks = 50000
    peaks_arr = np.empty(max_peaks, dtype=np.float64)
    count = 0

    x_prev2 = x
    x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)
    x_prev1 = x

    for _ in range(steps_meas):
        x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)
        if x_prev1 > x_prev2 and x_prev1 > x:
            denom = x_prev2 - 2.0 * x_prev1 + x
            peak = x_prev1 - 0.125 * ((x_prev2 - x) ** 2) / denom if denom != 0.0 else x_prev1
            if count < max_peaks:
                peaks_arr[count] = peak
                count += 1
        x_prev2 = x_prev1
        x_prev1 = x

    return peaks_arr[:count].copy(), np.array([x, y, z])

@njit(fastmath=True, cache=True)
def var_equations_njit(t, state_vars, A, x_eq, k, b, mu, ep):
    s = state_vars[:3]
    V = state_vars[3:].reshape((3, 3))

    ds = equations_njit(t, s, A, x_eq, k, b, mu, ep)
    J = jacobian_njit(s, A, k, b, mu, ep)
    dV = J @ V

    res = np.empty(12)
    res[:3] = ds
    res[3:] = dV.flatten()
    return res


@njit(fastmath=True, cache=False, nogil=True)
def calc_lyapunov_numba(s_start, A, x_eq, k, b, mu, ep, dt, t_trans, t_calc, t_ortho, cancel_flag):
    s = s_start.copy()
    t = 0.0

    steps_trans = int(t_trans / dt)
    for _ in range(steps_trans):
        if cancel_flag[0] != 0:
            return np.zeros(3), True
        s = rk4_step(t, s, A, x_eq, k, b, mu, ep, dt)
        t += dt

    state_vars = np.zeros(12)
    state_vars[:3] = s
    state_vars[3:] = np.eye(3).flatten()

    steps_calc = int(t_calc / dt)
    steps_ortho = int(t_ortho / dt)
    if steps_ortho < 1: steps_ortho = 1

    LE = np.zeros(3)
    accumulated_time = 0.0
    interval_steps = 0

    for i in range(steps_calc):
        if cancel_flag[0] != 0:
            return np.zeros(3), True
        k1 = var_equations_njit(t, state_vars, A, x_eq, k, b, mu, ep)
        k2 = var_equations_njit(t + dt / 2.0, state_vars + dt / 2.0 * k1, A, x_eq, k, b, mu, ep)
        k3 = var_equations_njit(t + dt / 2.0, state_vars + dt / 2.0 * k2, A, x_eq, k, b, mu, ep)
        k4 = var_equations_njit(t + dt, state_vars + dt * k3, A, x_eq, k, b, mu, ep)

        state_vars = state_vars + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t += dt
        interval_steps += 1

        if interval_steps >= steps_ortho:
            V = state_vars[3:].reshape((3, 3))
            Q, R = np.linalg.qr(V)
            state_vars[3:] = Q.flatten()
            LE += np.log(np.maximum(np.abs(np.diag(R)), 1e-300))
            accumulated_time += interval_steps * dt
            interval_steps = 0

    # Include the final incomplete QR interval and normalize by elapsed time.
    if interval_steps > 0:
        V = state_vars[3:].reshape((3, 3))
        Q, R = np.linalg.qr(V)
        state_vars[3:] = Q.flatten()
        LE += np.log(np.maximum(np.abs(np.diag(R)), 1e-300))
        accumulated_time += interval_steps * dt

    if accumulated_time > 0.0:
        LE = LE / accumulated_time

    return LE, False

@njit(fastmath=True, cache=True)
def rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt):
    k1x, k1y, k1z = equations_scalar(x, y, z, A, x_eq, k, b, mu, ep)
    h = 0.5 * dt
    k2x, k2y, k2z = equations_scalar(x + h * k1x, y + h * k1y, z + h * k1z, A, x_eq, k, b, mu, ep)
    k3x, k3y, k3z = equations_scalar(x + h * k2x, y + h * k2y, z + h * k2z, A, x_eq, k, b, mu, ep)
    k4x, k4y, k4z = equations_scalar(x + dt * k3x, y + dt * k3y, z + dt * k3z, A, x_eq, k, b, mu, ep)
    c = dt / 6.0
    return (
        x + c * (k1x + 2.0 * k2x + 2.0 * k3x + k4x),
        y + c * (k1y + 2.0 * k2y + 2.0 * k3y + k4y),
        z + c * (k1z + 2.0 * k2z + 2.0 * k3z + k4z),
    )

@njit(fastmath=True, cache=True)
def rk4_step(t, s, A, x_eq, k, b, mu, ep, dt):
    xn, yn, zn = rk4_step_scalar(s[0], s[1], s[2], A, x_eq, k, b, mu, ep, dt)
    return np.array([xn, yn, zn])


@njit(fastmath=True, cache=True, nogil=True)
def integrate_rk4_numba(t_end, dt, s_start, A, x_eq, k, b, mu, ep, dt_out, is_backward, cancel_flag):
    steps = int(t_end / dt)
    sample_rate = max(1, int(dt_out / dt))
    out_len = steps // sample_rate + 2
    t_out_arr = np.empty(out_len)
    s_out_arr = np.empty((out_len, 3))
    t = 0.0
    x, y, z = s_start[0], s_start[1], s_start[2]
    step_dt = -dt if is_backward else dt
    out_idx = 0
    t_out_arr[0] = t
    s_out_arr[0, 0], s_out_arr[0, 1], s_out_arr[0, 2] = x, y, z
    out_idx = 1
    cancelled = False
    for i in range(1, steps + 1):
        if cancel_flag[0] != 0:
            cancelled = True
            break
        x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, step_dt)
        t += step_dt
        if i % sample_rate == 0:
            t_out_arr[out_idx] = t
            s_out_arr[out_idx, 0] = x
            s_out_arr[out_idx, 1] = y
            s_out_arr[out_idx, 2] = z
            out_idx += 1
    if t_out_arr[out_idx - 1] != t:
        t_out_arr[out_idx] = t
        s_out_arr[out_idx, 0], s_out_arr[out_idx, 1], s_out_arr[out_idx, 2] = x, y, z
        out_idx += 1
    return t_out_arr[:out_idx], s_out_arr[:out_idx], cancelled

@njit(fastmath=True, cache=True)
def rk4_step_back(t, s, A, x_eq, k, b, mu, ep, dt):
    k1 = -equations_njit(t, s, A, x_eq, k, b, mu, ep)
    k2 = -equations_njit(t + dt / 2.0, s + dt / 2.0 * k1, A, x_eq, k, b, mu, ep)
    k3 = -equations_njit(t + dt / 2.0, s + dt / 2.0 * k2, A, x_eq, k, b, mu, ep)
    k4 = -equations_njit(t + dt, s + dt * k3, A, x_eq, k, b, mu, ep)
    return s + dt / 6.0 * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


@njit(fastmath=True, cache=True)
def equations_network_njit(t, s, N, A_arr, x_eq_arr, k, b_arr, mu, ep,
                           g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn):
    ds = np.empty(3 * N, dtype=np.float64)
    for i in range(N):
        x_i = s[i]
        y_i = s[N + i]
        z_i = s[2 * N + i]

        I_el = 0.0
        I_syn = 0.0
        if g_el > 0.0:
            for j in range(N):
                if A_el[i, j] > 0.0:
                    I_el += A_el[i, j] * (s[j] - x_i)
            I_el *= g_el

        if g_syn > 0.0:
            syn_sum = 0.0
            for j in range(N):
                if A_syn[i, j] > 0.0:
                    sigmoid_j = 1.0 / (1.0 + np.exp(-lambda_syn * (s[j] - theta_syn)))
                    syn_sum += A_syn[i, j] * sigmoid_j
            I_syn = -g_syn * (x_i - V_rev) * syn_sum

        dx = -2.0 * x_i / (1.0 + x_i ** 2) + y_i - z_i + I_el + I_syn

        # Keep the intrinsic neuron equations identical to equations_scalar.
        f = -x_i + k * y_i + b_arr[i]
        upper = -y_i + 2.0
        lower = -y_i - 2.0
        if f >= upper:
            dy = upper
        elif f <= lower:
            dy = lower
        else:
            dy = f

        dz = ep * (A_arr[i] * (x_i - x_eq_arr[i]) - z_i)

        ds[i] = dx
        ds[N + i] = mu * dy
        ds[2 * N + i] = dz

    return ds
@njit(fastmath=True, cache=True)
def rk4_step_network(t, s, N, A_arr, x_eq_arr, k, b_arr, mu, ep,
                     g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn, dt):
    k1 = equations_network_njit(t, s, N, A_arr, x_eq_arr, k, b_arr, mu, ep, g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn)
    k2 = equations_network_njit(t + dt / 2.0, s + dt / 2.0 * k1, N, A_arr, x_eq_arr, k, b_arr, mu, ep, g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn)
    k3 = equations_network_njit(t + dt / 2.0, s + dt / 2.0 * k2, N, A_arr, x_eq_arr, k, b_arr, mu, ep, g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn)
    k4 = equations_network_njit(t + dt, s + dt * k3, N, A_arr, x_eq_arr, k, b_arr, mu, ep, g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn)
    return s + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

@njit(fastmath=True, cache=True, nogil=True)
def integrate_network_numba(t_end, dt, s_start, N, A_arr, x_eq_arr, k, b_arr, mu, ep,
                            g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn, dt_out, cancel_flag):
    steps = int(t_end / dt)
    sample_rate = max(1, int(dt_out / dt))
    out_len = steps // sample_rate + 2
    t_out_arr = np.empty(out_len, dtype=np.float64)
    s_out_arr = np.empty((out_len, 3 * N), dtype=np.float64)
    t = 0.0
    s = s_start.copy()
    out_idx = 0
    t_out_arr[out_idx] = t
    s_out_arr[out_idx] = s
    out_idx += 1
    cancelled = False
    for i in range(1, steps + 1):
        if cancel_flag[0] != 0:
            cancelled = True
            break
        s = rk4_step_network(t, s, N, A_arr, x_eq_arr, k, b_arr, mu, ep, g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn, dt)
        t += dt
        if i % sample_rate == 0:
            t_out_arr[out_idx] = t
            s_out_arr[out_idx] = s
            out_idx += 1
    # Always retain the last computed state, including a partial final interval.
    if t_out_arr[out_idx - 1] != t:
        t_out_arr[out_idx] = t
        s_out_arr[out_idx] = s
        out_idx += 1
    return t_out_arr[:out_idx], s_out_arr[:out_idx], cancelled

@njit(fastmath=True, cache=True)
def integrate_separatrix_numba(t_end, dt, s_start, A, x_eq, k, b, mu, ep, is_forward):
    steps = int(t_end / dt)
    s_out_arr = np.empty((steps + 1, 3), dtype=np.float64)
    t = 0.0
    s = s_start.copy()
    s_out_arr[0] = s
    valid_steps = 1

    for i in range(1, steps + 1):
        if is_forward:
            s = rk4_step(t, s, A, x_eq, k, b, mu, ep, dt)
        else:
            s = rk4_step_back(t, s, A, x_eq, k, b, mu, ep, dt)

        t += dt
        s_out_arr[i] = s
        valid_steps += 1

        if abs(s[0]) > 95.0 or abs(s[1]) > 95.0 or abs(s[2]) > 95.0:
            break

    return s_out_arr[:valid_steps]


@njit(fastmath=True, cache=True)
def sde_step_euler_maruyama(t, s, eta, A, x_eq, k, b, mu, ep, D, tau, dt):
    ds = equations_njit(t, s, A, x_eq, k, b, mu, ep)

    dx = ds[0] + eta
    dy = ds[1]
    dz = ds[2]

    s_new = s + np.array([dx, dy, dz]) * dt

    dW = np.random.normal(0.0, 1.0) * np.sqrt(dt)
    d_eta = -(1.0 / tau) * eta * dt + np.sqrt(2.0 * D / tau) * dW

    eta_new = eta + d_eta
    return s_new, eta_new


@njit(fastmath=True, cache=False, nogil=True)
def integrate_sde_numba(t_end, dt, s_start, A, x_eq, k, b, mu, ep, D, tau, dt_out, cancel_flag):
    steps = int(t_end / dt)
    sample_rate = max(1, int(dt_out / dt))
    out_len = steps // sample_rate + 2
    t_out_arr = np.empty(out_len)
    s_out_arr = np.empty((out_len, 3))
    t = 0.0
    s = s_start.copy()
    eta = 0.0
    out_idx = 0
    t_out_arr[out_idx] = t
    s_out_arr[out_idx] = s
    out_idx += 1
    cancelled = False
    for i in range(1, steps + 1):
        if cancel_flag[0] != 0:
            cancelled = True
            break
        s, eta = sde_step_euler_maruyama(t, s, eta, A, x_eq, k, b, mu, ep, D, tau, dt)
        t += dt
        if i % sample_rate == 0:
            t_out_arr[out_idx] = t
            s_out_arr[out_idx] = s
            out_idx += 1
    if t_out_arr[out_idx - 1] != t:
        t_out_arr[out_idx] = t
        s_out_arr[out_idx] = s
        out_idx += 1
    return t_out_arr[:out_idx], s_out_arr[:out_idx], cancelled


def get_isi_on_the_fly(s_start, A, x_eq, k, b, mu, ep, dt, t_trans, t_meas, thresh):
    x, y, z = s_start[0], s_start[1], s_start[2]
    t = 0.0

    for _ in range(int(t_trans / dt)):
        x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)
        t += dt

    steps_meas = int(t_meas / dt)
    max_spikes = 50000
    isi_arr = np.empty(max_spikes, dtype=np.float64)
    spike_count = 0
    last_spike_t = -1.0

    x_prev2 = x
    x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)
    t += dt
    x_prev1 = x

    for _ in range(steps_meas):
        x, y, z = rk4_step_scalar(x, y, z, A, x_eq, k, b, mu, ep, dt)
        t += dt
        if x_prev1 > x_prev2 and x_prev1 > x and x_prev1 > thresh:
            if last_spike_t > 0:
                isi = t - last_spike_t
                if isi > 2.0 and spike_count < max_spikes:
                    isi_arr[spike_count] = isi
                    spike_count += 1
            last_spike_t = t
        x_prev2 = x_prev1
        x_prev1 = x

    return isi_arr[:spike_count].copy(), np.array([x, y, z])

def get_jacobian(x, y, zone, A, k, mu, ep):
    df_dx = 2 * (x ** 2 - 1) / ((x ** 2 + 1) ** 2)
    if zone == "Lin": return np.array([[df_dx, 1, -1], [-mu, mu * k, 0], [ep * A, 0, -ep]])
    return np.array([[df_dx, 1, -1], [0, -mu, 0], [ep * A, 0, -ep]])


def classify_equilibrium(eigenvalues):
    reals, imags = np.real(eigenvalues), np.imag(eigenvalues)
    # Порог точности увеличен с 1e-6 до 1e-10 для ловли порядка эпсилон
    num_pos, num_neg = np.sum(reals > 1e-10), np.sum(reals < -1e-10)
    if np.sum(np.abs(reals) <= 1e-10) > 0: return "Негрубое (Re=0)"
    if np.any(np.abs(
            imags) > 1e-10): return "НФ (Неуст. фокус)" if num_pos == 3 else "УФ (Уст. фокус)" if num_neg == 3 else "С-Ф (Седло-фокус)"
    return "НУ (Неуст. узел)" if num_pos == 3 else "УУ (Уст. узел)" if num_neg == 3 else "Седло"


def generate_topology(N, topo_type="all-to-all", directed=False, p_rand=0.3):
    A = np.zeros((N, N), dtype=np.float64)
    if N < 2:
        return A

    if topo_type == "pair":
        if directed:
            A[1, 0] = 1.0
        else:
            A[0, 1] = 1.0
            A[1, 0] = 1.0

    elif topo_type == "ring":
        for i in range(N):
            A[i, (i - 1) % N] = 1.0
            if not directed:
                A[i, (i + 1) % N] = 1.0

    elif topo_type == "nonlocal-ring":
        R = max(2, int(0.3 * N))
        for i in range(N):
            for r in range(1, R + 1):
                A[i, (i - r) % N] = 1.0
                if not directed:
                    A[i, (i + r) % N] = 1.0

    elif topo_type == "all-to-all":
        A = np.ones((N, N), dtype=np.float64) - np.eye(N, dtype=np.float64)

    elif topo_type == "random":
        A = (np.random.rand(N, N) < p_rand).astype(np.float64)
        np.fill_diagonal(A, 0.0)
        if not directed:
            A = np.tril(A) + np.tril(A, -1).T

    for i in range(N):
        row_sum = np.sum(A[i, :])
        if row_sum > 0:
            A[i, :] = A[i, :] / row_sum

    return A

def find_equilibria_with_types(A, x_eq, k, b, mu, ep):
    pts = [];
    a1, b1 = 1 - k * A, k * A * x_eq - b
    for r in np.roots([a1, b1, a1 - 2 * k, b1]):
        if abs(r.imag) < 1e-10 and -2 < (r.real - b) / k < 2: pts.append(
            [r.real, (r.real - b) / k, A * (r.real - x_eq), "Lin"])
    for yf in [2, -2]:
        for r in np.roots([-A, A * x_eq + yf, -(A + 2), A * x_eq + yf]):
            if abs(r.imag) < 1e-10:
                force = -r.real + k * yf + b
                if (yf == 2 and force >= 0) or (yf == -2 and force <= 0): pts.append(
                    [r.real, yf, A * (r.real - x_eq), "Sat"])
    pts.sort(key=lambda p: p[0])
    return [(x, y, z, zone, classify_equilibrium(np.linalg.eigvals(get_jacobian(x, y, zone, A, k, mu, ep))),
             np.linalg.eigvals(get_jacobian(x, y, zone, A, k, mu, ep))) for x, y, z, zone in pts]


def get_eq_signature(eqs):
    if not eqs: return "Нет СР"
    return " + ".join([eq[4].split()[0] if " " in eq[4] else eq[4] for eq in eqs])


class LegendItem(QWidget):
    def __init__(self, color, text):
        super().__init__();
        layout = QHBoxLayout(self);
        layout.setContentsMargins(5, 5, 5, 5)
        self.color_box = QLabel();
        self.color_box.setFixedSize(20, 20);
        self.color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #94a3b8; border-radius: 4px;")
        self.label = QLabel(text);
        self.label.setStyleSheet("font-size: 13px; color: #1f2937;")
        layout.addWidget(self.color_box);
        layout.addWidget(self.label);
        layout.addStretch()

    def set_highlight(self, is_active, any_active):
        if is_active:
            self.setStyleSheet("background-color: #e0f2fe; border-radius: 6px;");
            self.label.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: #075985;")
        elif any_active:
            self.setStyleSheet("background-color: transparent;");
            self.label.setStyleSheet(
                "font-size: 13px; color: #94a3b8;")
        else:
            self.setStyleSheet("background-color: transparent;");
            self.label.setStyleSheet(
                "font-size: 13px; color: #1f2937;")


class NetworkSolverWorker(QThread):
    finished_signal = pyqtSignal(str, object, object, str)
    error_signal = pyqtSignal(str)

    def __init__(self, traj_id, N, A_arr, x_eq_arr, k, b_arr, mu, ep,
                 g_el, A_el, g_syn, A_syn, V_rev, theta_syn, lambda_syn,
                 start_pos, dt_rk4, t_end):
        super().__init__()
        self.traj_id = traj_id
        self.N = N
        self.A_arr = np.asarray(A_arr, dtype=np.float64)
        self.x_eq_arr = np.asarray(x_eq_arr, dtype=np.float64)
        self.k, self.mu, self.ep = k, mu, ep
        self.b_arr = np.asarray(b_arr, dtype=np.float64)
        self.g_el, self.A_el = float(g_el), np.asarray(A_el, dtype=np.float64)
        self.g_syn, self.A_syn = float(g_syn), np.asarray(A_syn, dtype=np.float64)
        self.V_rev, self.theta_syn, self.lambda_syn = float(V_rev), float(theta_syn), float(lambda_syn)
        self.start_pos, self.dt_rk4, self.t_end = np.asarray(start_pos, dtype=np.float64), float(dt_rk4), float(t_end)
        self.dt_out = 0.2
        self.cancel_flag = np.zeros(1, dtype=np.int32)

    def cancel(self):
        self.cancel_flag[0] = 1

    def run(self):
        try:
            t_out, s_out, cancelled = integrate_network_numba(
                self.t_end, self.dt_rk4, self.start_pos, self.N, self.A_arr, self.x_eq_arr,
                self.k, self.b_arr, self.mu, self.ep, self.g_el, self.A_el, self.g_syn,
                self.A_syn, self.V_rev, self.theta_syn, self.lambda_syn, self.dt_out, self.cancel_flag
            )
            if cancelled:
                self.error_signal.emit("Остановлено пользователем")
                return
            self.finished_signal.emit(self.traj_id, t_out, s_out, "Успешно (Network RK4)")
        except Exception as e:
            self.error_signal.emit(f"Ошибка в NetworkWorker: {str(e)}")

class SolverWorker(QThread):
    finished_signal = pyqtSignal(str, object, object, object, object, str)
    error_signal = pyqtSignal(str)

    def __init__(self, traj_id, A, x_eq, k, b, mu, ep, start_pos, method, rtol, atol, dt_rk4, t_end, is_backward=False, use_noise=False, D=0.0, tau=1.0):
        super().__init__()
        self.traj_id, self.A, self.x_eq, self.start_pos = traj_id, A, x_eq, start_pos
        self.k, self.b, self.mu, self.ep = k, b, mu, ep
        self.method, self.rtol, self.atol, self.dt_rk4, self.t_end = method, rtol, atol, dt_rk4, t_end
        self.dt_out = 0.2
        self.is_backward = is_backward
        self.use_noise = use_noise
        self.D = D
        self.tau = tau
        self.cancel_flag = np.zeros(1, dtype=np.int32)

    def cancel(self):
        self.cancel_flag[0] = 1

    def run(self):
        try:
            if self.use_noise:
                t_out, y_out, cancelled = integrate_sde_numba(
                    self.t_end, self.dt_rk4, np.array(self.start_pos, dtype=np.float64),
                    self.A, self.x_eq, self.k, self.b, self.mu, self.ep, self.D, self.tau, self.dt_out, self.cancel_flag
                )
                if cancelled:
                    raise InterruptedError("Остановлено")
                self.finished_signal.emit(self.traj_id, t_out, y_out[:, 0], y_out[:, 1], y_out[:, 2], "Успешно (SDE Euler)")
            elif self.method == 'RK4 (Numba)':
                t_out, y_out, cancelled = integrate_rk4_numba(
                    self.t_end, self.dt_rk4, np.array(self.start_pos, dtype=np.float64),
                    self.A, self.x_eq, self.k, self.b, self.mu, self.ep, self.dt_out, self.is_backward, self.cancel_flag
                )
                if cancelled:
                    raise InterruptedError("Остановлено")
                self.finished_signal.emit(self.traj_id, t_out, y_out[:, 0], y_out[:, 1], y_out[:, 2], "Успешно (RK4)")
            else:
                t_span = (0, -self.t_end) if self.is_backward else (0, self.t_end)
                def cancel_event(t, y):
                    return 0.0 if self.cancel_flag[0] != 0 else 1.0
                cancel_event.terminal = True
                cancel_event.direction = 0
                sol = solve_ivp(
                    fun=lambda t, y: equations_njit(t, y, self.A, self.x_eq, self.k, self.b, self.mu, self.ep),
                    t_span=t_span, y0=self.start_pos, method=self.method, rtol=self.rtol,
                    atol=self.atol, max_step=self.dt_rk4, events=cancel_event)
                if self.cancel_flag[0] != 0:
                    raise InterruptedError("Остановлено")
                if sol.success or len(sol.t) > 0:
                    self.finished_signal.emit(self.traj_id, sol.t, sol.y[0], sol.y[1], sol.y[2],
                                              "Успешно" if sol.success else f"Прервано на t={sol.t[-1]:.0f}")
                else:
                    self.error_signal.emit(f"Прервано: {sol.message}")
        except Exception as e:
            self.error_signal.emit(str(e))

class LyapunovWorker(QThread):
    finished_signal = pyqtSignal(object, bool)
    error_signal = pyqtSignal(str)

    def __init__(self, A, x_eq, k, b, mu, ep, start_pos, dt):
        super().__init__()
        self.A, self.x_eq, self.k, self.b = A, x_eq, k, b
        self.mu, self.ep, self.start_pos, self.dt = mu, ep, start_pos, dt
        self.t_trans = 200000.0
        self.t_calc = 1000000.0
        self.t_ortho = 0.5
        self.cancel_flag = np.zeros(1, dtype=np.int32)

    def cancel(self):
        self.cancel_flag[0] = 1

    def run(self):
        try:
            le_spectrum, cancelled = calc_lyapunov_numba(
                np.array(self.start_pos, dtype=np.float64),
                self.A, self.x_eq, self.k, self.b, self.mu, self.ep, self.dt,
                self.t_trans, self.t_calc, self.t_ortho, self.cancel_flag
            )
            self.finished_signal.emit(le_spectrum, cancelled)
        except Exception as e:
            self.error_signal.emit(str(e))

class MapWorker(QThread):
    progress_signal = pyqtSignal(int);
    finished_signal = pyqtSignal(object, object, object, object)

    def __init__(self, A_min, A_max, X_min, X_max, res, k, b, mu, ep):
        super().__init__();
        self.A_min, self.A_max, self.X_min, self.X_max, self.res = A_min, A_max, X_min, X_max, res
        self.k, self.b, self.mu, self.ep = k, b, mu, ep
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        A_arr, X_arr = np.linspace(self.A_min, self.A_max, self.res), np.linspace(self.X_min, self.X_max, self.res)
        Z, unique_sigs, sig_to_idx, total, count = np.zeros((self.res, self.res),
                                                            dtype=int), [], {}, self.res * self.res, 0
        for j, a_val in enumerate(A_arr):
            for i, x_val in enumerate(X_arr):
                if self.is_cancelled: return
                sig = get_eq_signature(find_equilibria_with_types(a_val, x_val, self.k, self.b, self.mu, self.ep))
                if sig not in sig_to_idx: sig_to_idx[sig] = len(unique_sigs); unique_sigs.append(sig)
                Z[j, i] = sig_to_idx[sig];
                count += 1
                if count % max(1, total // 100) == 0: self.progress_signal.emit(int(count / total * 100))
        self.progress_signal.emit(100);
        self.finished_signal.emit(X_arr, A_arr, Z, unique_sigs)


class ISIBifurcationWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object, object, str, float, float, bool, float)
    error_signal = pyqtSignal(str)

    def __init__(self, param_type, p_min, p_max, p_steps, fixed_val, k, b, mu, ep, start_pos, t_transient, t_measure,
                 dt_rk4, threshold, use_continuation):
        super().__init__()
        self.ptype, self.pmin, self.pmax, self.psteps = param_type, p_min, p_max, p_steps
        self.fval, self.k, self.b, self.mu, self.ep = fixed_val, k, b, mu, ep
        self.spos, self.ttrans, self.tmeas, self.dt = start_pos, t_transient, t_measure, dt_rk4
        self.thresh, self.use_cont, self.is_cancelled = threshold, use_continuation, False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            parr = np.linspace(self.pmin, self.pmax, self.psteps)
            ap, aisi = [], []
            curr = np.array(self.spos, dtype=np.float64)
            th = -1.0 if self.thresh == 'auto' else float(self.thresh)

            for i, p in enumerate(parr):
                if self.is_cancelled: return

                A_val = float(p) if self.ptype == 'A' else float(self.fval)
                X_val = float(self.fval) if self.ptype == 'A' else float(p)

                if not self.use_cont:
                    curr = np.array(self.spos, dtype=np.float64)

                isi_vals, curr = get_isi_on_the_fly(
                    curr, A_val, X_val, float(self.k), float(self.b), float(self.mu), float(self.ep),
                    float(self.dt), float(self.ttrans), float(self.tmeas), float(th)
                )

                isi_vals = clean_isi_values(isi_vals)
                if isi_vals.size > MAX_BIFURCATION_POINTS_PER_STEP:
                    isi_vals = isi_vals[downsample_indices(isi_vals.size, MAX_BIFURCATION_POINTS_PER_STEP)]

                remaining = MAX_BIFURCATION_PLOT_POINTS - len(aisi)
                if remaining > 0 and isi_vals.size > 0:
                    if isi_vals.size > remaining:
                        isi_vals = isi_vals[downsample_indices(isi_vals.size, remaining)]
                    ap.extend([float(p)] * int(isi_vals.size))
                    aisi.extend(isi_vals.tolist())

                self.progress_signal.emit(int((i + 1) / self.psteps * 100))

            self.finished_signal.emit(ap, aisi, self.ptype, self.pmin, self.pmax, self.use_cont, float(self.fval))
        except Exception as e:
            self.error_signal.emit(str(e))



def classify_eq_algebraic(x, y, zone_is_lin, A, k, mu, ep):
    S = 2.0 * (x ** 2 - 1.0) / ((1.0 + x ** 2) ** 2)

    if zone_is_lin:
        c1 = -S - mu * k + ep
        c2 = ep * (A - S - mu * k) + mu * (1.0 + k * S)
        c3 = mu * ep * (1.0 + k * (S - A))
    else:
        c1 = -S + mu + ep
        c2 = ep * (A - S + mu) - mu * S
        c3 = mu * ep * (A - S)

    coeffs = np.array([1.0, c1, c2, c3], dtype=np.float64)
    evs = np.roots(coeffs)

    pos_reals = 0
    has_complex = False
    for i in range(3):
        if evs[i].real > 1e-9: pos_reals += 1
        if abs(evs[i].imag) > 1e-9: has_complex = True

    if pos_reals == 0: return 1
    elif pos_reals == 3: return 4
    elif pos_reals in (1, 2): return 3 if has_complex else 2
    return 0


def find_folded_states(A, x_eq, k, b, mu, ep):
    folded_states = []
    denom = mu * k + ep

    if abs(denom) > 1e-12:
        y_plus = (mu * (1.0 - b) + ep * (A * (1.0 - x_eq) + 1.0)) / denom
        z_plus = y_plus - 1.0

        if -2.0 <= y_plus <= 2.0:
            J11 = -mu - ep * A
            J12 = mu * k + ep
            J21 = -mu * (-1.0 + k * y_plus + b)
            J22 = 0.0

            Tr = J11 + J22
            Det = J11 * J22 - J12 * J21

            if Det < 0:
                ftype = "Свернутое седло"
            elif Tr ** 2 - 4 * Det > 0:
                ftype = "Свернутый узел"
            else:
                ftype = "Свернутый фокус"

            folded_states.append((1.0, y_plus, z_plus, ftype))

        # Линия складки L- (x = -1)
        y_minus = (-mu * (1.0 + b) - ep * (A * (1.0 + x_eq) + 1.0)) / denom
        z_minus = y_minus + 1.0

        if -2.0 <= y_minus <= 2.0:
            J11 = -mu - ep * A
            J12 = mu * k + ep
            J21 = mu * (1.0 + k * y_minus + b)
            J22 = 0.0

            Tr = J11 + J22
            Det = J11 * J22 - J12 * J21

            if Det < 0:
                ftype = "Свернутое седло"
            elif Tr ** 2 - 4 * Det > 0:
                ftype = "Свернутый узел"
            else:
                ftype = "Свернутый фокус"

            folded_states.append((-1.0, y_minus, z_minus, ftype))

    return folded_states

class EquilibriaBranchesWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object, str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, param_type, var_type, p_min, p_max, res, base_params):
        super().__init__()
        self.param_type = param_type  # 'x_eq', 'A', 'k', 'b', 'mu', 'ep'
        self.var_type = var_type      # 'x', 'y', 'z'
        self.p_min, self.p_max, self.res = p_min, p_max, res
        self.bp = base_params.copy()
        self.is_cancelled = False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            p_vals = np.linspace(self.p_min, self.p_max, self.res)
            eq_data = {1: {'p': [], 'v': []}, 2: {'p': [], 'v': []}, 3: {'p': [], 'v': []}, 4: {'p': [], 'v': []}}

            for i, p in enumerate(p_vals):
                if self.is_cancelled: return

                cp = self.bp.copy()
                cp[self.param_type] = p
                A, x_eq, k, b, mu, ep = cp['A'], cp['x_eq'], cp['k'], cp['b'], cp['mu'], cp['ep']

                # 1. Линейная зона (|y| <= 2)
                a1 = 1.0 - k * A
                b1 = k * A * x_eq - b
                if abs(a1) > 1e-12:
                    for r in np.roots([a1, b1, a1 - 2.0 * k, b1]):
                        if abs(r.imag) < 1e-9:
                            x_val = float(r.real)
                            y_val = (x_val - b) / k
                            if abs(y_val) <= 2.0:
                                t = classify_eq_algebraic(x_val, y_val, True, A, k, mu, ep)
                                if t in eq_data:
                                    z_val = A * (x_val - x_eq)
                                    val = x_val if self.var_type == 'x' else (y_val if self.var_type == 'y' else z_val)
                                    eq_data[t]['p'].append(float(p))
                                    eq_data[t]['v'].append(float(val))

                # 2. Зона насыщения (y = 2)
                a2_pos, b2_pos = -A, A * x_eq + 2.0
                if abs(a2_pos) > 1e-12:
                    for r in np.roots([a2_pos, b2_pos, a2_pos - 2.0, b2_pos]):
                        if abs(r.imag) < 1e-9 and (-r.real + k * 2.0 + b >= 0):
                            x_val = float(r.real)
                            t = classify_eq_algebraic(x_val, 2.0, False, A, k, mu, ep)
                            if t in eq_data:
                                z_val = A * (x_val - x_eq)
                                val = x_val if self.var_type == 'x' else (2.0 if self.var_type == 'y' else z_val)
                                eq_data[t]['p'].append(float(p))
                                eq_data[t]['v'].append(float(val))

                # 3. Зона насыщения (y = -2)
                a2_neg, b2_neg = -A, A * x_eq - 2.0
                if abs(a2_neg) > 1e-12:
                    for r in np.roots([a2_neg, b2_neg, a2_neg - 2.0, b2_neg]):
                        if abs(r.imag) < 1e-9 and (-r.real - k * 2.0 + b <= 0):
                            x_val = float(r.real)
                            t = classify_eq_algebraic(x_val, -2.0, False, A, k, mu, ep)
                            if t in eq_data:
                                z_val = A * (x_val - x_eq)
                                val = x_val if self.var_type == 'x' else (-2.0 if self.var_type == 'y' else z_val)
                                eq_data[t]['p'].append(float(p))
                                eq_data[t]['v'].append(float(val))

                if i % max(1, self.res // 100) == 0:
                    self.progress_signal.emit(int((i + 1) / self.res * 100))

            self.finished_signal.emit(eq_data, self.param_type, self.var_type)
        except Exception as e:
            self.error_signal.emit(str(e))


class ExportDialog(QDialog):
    def __init__(self, app_ref, default_tmin, default_tmax, parent=None):
        super().__init__(parent)
        self.app = app_ref
        self.trajectories = app_ref.trajectories
        self.setWindowTitle("Настройка и предпросмотр экспорта")
        self.setMinimumSize(1600, 950)

        layout = QHBoxLayout(self)

        # --- ЛЕВАЯ ПАНЕЛЬ (Элементы управления) ---
        left_panel = QWidget()
        left_panel.setFixedWidth(520)
        left_layout = QVBoxLayout(left_panel)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        sw = QWidget()
        sl = QVBoxLayout(sw)

        # 1. Фазовые портреты
        g1 = QGroupBox("Фазовые портреты")
        l1 = QVBoxLayout()
        h1 = QHBoxLayout()
        self.cp = {p: QCheckBox(p) for p in ['3D', 'X-Y', 'X-Z', 'Y-Z']}
        for p, cb in self.cp.items():
            cb.setChecked(p == '3D')
            h1.addWidget(cb)
        l1.addLayout(h1)
        self.cb_sep_phase = QCheckBox("Раздельные портреты (сетка Nx2)")
        l1.addWidget(self.cb_sep_phase)
        g1.setLayout(l1)
        sl.addWidget(g1)

        # 2. Временные реализации
        g2 = QGroupBox("Временные реализации")
        l2 = QHBoxLayout()
        self.cv = {v: QCheckBox(v) for v in ['x(t)', 'y(t)', 'z(t)']}
        for v, cb in self.cv.items():
            cb.setChecked(v == 'x(t)')
            l2.addWidget(cb)
        g2.setLayout(l2)
        sl.addWidget(g2)

        # 3. Оформление (Шрифты и отступы)
        g3 = QGroupBox("Оформление (Шрифты и отступы)")
        l3 = QGridLayout()

        self.cb_bold_axes = QCheckBox("Жирный шрифт осей")
        self.cb_bold_axes.setChecked(True)
        l3.addWidget(self.cb_bold_axes, 0, 0, 1, 2)

        l3.addWidget(QLabel("Толщина линий:"), 1, 0)
        self.i_lw = QLineEdit("2.5")
        l3.addWidget(self.i_lw, 1, 1)

        l3.addWidget(QLabel("Шрифт осей:"), 2, 0)
        self.i_fs_ax = QLineEdit("28")
        l3.addWidget(self.i_fs_ax, 2, 1)

        l3.addWidget(QLabel("Шрифт цифр:"), 3, 0)
        self.i_fs_tick = QLineEdit("26")
        l3.addWidget(self.i_fs_tick, 3, 1)

        l3.addWidget(QLabel("Отступ H (hspace):"), 4, 0)
        self.i_hspace = QLineEdit("0.4")
        l3.addWidget(self.i_hspace, 4, 1)

        l3.addWidget(QLabel("Отступ W (wspace):"), 5, 0)
        self.i_wspace = QLineEdit("0.25")
        l3.addWidget(self.i_wspace, 5, 1)

        l3.addWidget(QLabel("Шрифт букв:"), 6, 0)
        self.i_fs_let = QLineEdit("32")
        l3.addWidget(self.i_fs_let, 6, 1)

        l3.addWidget(QLabel("Формат нумерации:"), 7, 0)
        self.i_let_fmt = QLineEdit("{letter}")
        l3.addWidget(self.i_let_fmt, 7, 1)

        l3.addWidget(QLabel("X, Y буквы:"), 8, 0)
        h_let_xy = QHBoxLayout()
        self.i_let_x = QLineEdit("-0.1")
        self.i_let_y = QLineEdit("1.05")
        h_let_xy.addWidget(self.i_let_x)
        h_let_xy.addWidget(self.i_let_y)
        l3.addLayout(h_let_xy, 8, 1)

        g3.setLayout(l3)
        sl.addWidget(g3)

        # --- НОВЫЙ БЛОК: УВЕЛИЧЕННЫЕ ФРАГМЕНТЫ (ZOOM INSET) ---
        g_zoom = QGroupBox("Увеличенные фрагменты (Zoom)")
        l_zoom = QVBoxLayout()

        # Zoom для фазового портрета
        self.cb_z_ph = QCheckBox("Врезка на Фазовом портрете (только 2D)")
        grid_zph = QGridLayout()
        self.i_zph_idx = QLineEdit("0")
        self.i_zph_roi = QLineEdit("0.0, 1.0, -0.5, 0.5")  # x1, x2, y1, y2
        self.i_zph_loc = QLineEdit("0.5, 0.5, 0.4, 0.4")  # x0, y0, w, h
        grid_zph.addWidget(QLabel("Индекс графика (0, 1...):"), 0, 0);
        grid_zph.addWidget(self.i_zph_idx, 0, 1)
        grid_zph.addWidget(QLabel("Лимиты данных (x1,x2, y1,y2):"), 1, 0);
        grid_zph.addWidget(self.i_zph_roi, 1, 1)
        grid_zph.addWidget(QLabel("Окно (x, y, w, h) от 0 до 1:"), 2, 0);
        grid_zph.addWidget(self.i_zph_loc, 2, 1)

        # Zoom для времени
        self.cb_z_t = QCheckBox("Врезка на Временном ряду")
        grid_zt = QGridLayout()
        self.i_zt_idx = QLineEdit("0")
        self.i_zt_roi = QLineEdit("1000, 2000, 0.0, 1.0")  # t1, t2, v1, v2
        self.i_zt_loc = QLineEdit("0.5, 0.5, 0.4, 0.4")
        grid_zt.addWidget(QLabel("Индекс графика (0, 1...):"), 0, 0);
        grid_zt.addWidget(self.i_zt_idx, 0, 1)
        grid_zt.addWidget(QLabel("Лимиты данных (t1,t2, v1,v2):"), 1, 0);
        grid_zt.addWidget(self.i_zt_roi, 1, 1)
        grid_zt.addWidget(QLabel("Окно (x, y, w, h) от 0 до 1:"), 2, 0);
        grid_zt.addWidget(self.i_zt_loc, 2, 1)

        l_zoom.addWidget(self.cb_z_ph)
        l_zoom.addLayout(grid_zph)
        l_zoom.addWidget(self.cb_z_t)
        l_zoom.addLayout(grid_zt)
        g_zoom.setLayout(l_zoom)
        sl.addWidget(g_zoom)

        # 4. Время
        g4 = QGroupBox("Время")
        l4 = QHBoxLayout()
        self.i1 = QLineEdit(str(default_tmin))
        self.i2 = QLineEdit(str(default_tmax))
        l4.addWidget(QLabel("От t ="))
        l4.addWidget(self.i1)
        l4.addWidget(QLabel("До t ="))
        l4.addWidget(self.i2)
        g4.setLayout(l4)
        sl.addWidget(g4)

        # 5. Динамические режимы
        g5 = QGroupBox("Динамический режим")
        l5 = QVBoxLayout()
        grid5 = QGridLayout()
        regimes_list = ['Покой', 'Регулярные спайки', 'Хаотические спайки', 'Регулярные берсты', 'Хаотические берсты',
                        'Регулярные ММО', 'Хаотические ММО']
        self.regimes = {}
        row, col = 0, 0
        for name in regimes_list:
            cb = QCheckBox(name)
            self.regimes[name] = cb
            grid5.addWidget(cb, row, col)
            col += 1
            if col > 1:
                col, row = 0, row + 1
        l5.addLayout(grid5)

        h5_2 = QHBoxLayout()
        h5_2.addWidget(QLabel('Период ММО (L^S):'))
        self.i_mmo_period = QLineEdit("")
        h5_2.addWidget(self.i_mmo_period)
        l5.addLayout(h5_2)
        g5.setLayout(l5)
        sl.addWidget(g5)

        # 6. Доп текст
        g6 = QGroupBox("Доп. текст к названию")
        l6 = QHBoxLayout()
        self.i_custom_text = QLineEdit("")
        l6.addWidget(self.i_custom_text)
        g6.setLayout(l6)
        sl.addWidget(g6)

        # 7. Траектории
        g7 = QGroupBox("Траектории")
        l7 = QVBoxLayout()
        self.ct = {t: QCheckBox(t.split(' | ')[0]) for t in self.trajectories.keys()}
        for cb in self.ct.values():
            cb.setChecked(True)
            l7.addWidget(cb)
        g7.setLayout(l7)
        sl.addWidget(g7)

        sl.addStretch()
        scroll.setWidget(sw)
        left_layout.addWidget(scroll)

        # Кнопки действия
        btn_layout = QHBoxLayout()
        self.btn_update = QPushButton("Обновить предпросмотр")
        self.app.set_button_role(self.btn_update, "primary")
        self.btn_update.clicked.connect(self.build_figure)

        self.btn_export = QPushButton("Экспорт...")
        self.app.set_button_role(self.btn_export, "accent")
        self.btn_export.clicked.connect(self.export_to_file)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.reject)

        btn_layout.addWidget(self.btn_update)
        btn_layout.addWidget(self.btn_export)
        btn_layout.addWidget(self.btn_close)
        left_layout.addLayout(btn_layout)

        layout.addWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        self.canvas = FigureCanvas(Figure(figsize=(12, 10), facecolor='#ffffff'))
        right_layout.addWidget(NavigationToolbar(self.canvas, self))
        right_layout.addWidget(self.canvas)
        layout.addWidget(right_panel, 1)

    def build_figure(self):
        import warnings
        warnings.filterwarnings("ignore", module="matplotlib")
        import matplotlib.gridspec as gridspec
        import string
        import re

        self.canvas.figure.clear()
        fig = self.canvas.figure

        try:
            etm, etM = float(self.i1.text()), float(self.i2.text())
        except:
            etm, etM = 0.0, float('inf')

        try:
            lw = float(self.i_lw.text())
            fs_ax = int(self.i_fs_ax.text())
            fs_tick = int(self.i_fs_tick.text())
            fs_let = int(self.i_fs_let.text())
            hs = float(self.i_hspace.text())
            ws = float(self.i_wspace.text())
            let_x = float(self.i_let_x.text())
            let_y = float(self.i_let_y.text())
        except ValueError:
            return QMessageBox.warning(self, "Ошибка", "Проверьте числовые значения в Оформлении.")

        let_fmt = self.i_let_fmt.text()
        sep_phase = self.cb_sep_phase.isChecked()
        ax_weight = 'bold' if self.cb_bold_axes.isChecked() else 'normal'

        ph = [p for p, c in self.cp.items() if c.isChecked()]
        vts = [v for v, c in self.cv.items() if c.isChecked()]
        tids = [t for t, c in self.ct.items() if c.isChecked()]

        if not tids or (not ph and not vts): return

        M, V, P = len(tids), len(vts), len(ph)
        step = max(1, int(self.app.istep.text())) if self.app.istep.text() else 1
        atids = list(self.trajectories.keys())

        def get_params_from_tid(tid_str):
            match = re.search(r"A=([-\d.]+),\s*xeq=([-\d.]+)", tid_str)
            if match: return float(match.group(1)), float(match.group(2))
            return float(self.app.iA.text()), float(self.app.ix.text())

        def plot_equilibria(ax, pj, eqs):
            for pt in eqs:
                x, y, z, zone, eqt, ev = pt
                c1, c2 = (x, y) if pj == 'X-Y' else ((x, z) if pj == 'X-Z' else ((y, z) if pj == 'Y-Z' else (x, y)))

                facec = 'black'
                size = 180
                lw_m = 2.5

                if "С-Ф" in eqt or "Седло-фокус" in eqt:
                    facec = 'white'
                elif "Седло" in eqt:
                    facec = 'black'
                elif "НУ" in eqt or "НФ" in eqt or "Неуст." in eqt:
                    facec = 'white'
                elif "УУ" in eqt or "УФ" in eqt or "Уст." in eqt:
                    facec = 'black'

                if pj == '3D':
                    ax.scatter([x], [y], [z], marker='o', s=size, facecolors=facec, edgecolors='black', linewidth=lw_m,
                               zorder=12)
                else:
                    ax.scatter([c1], [c2], marker='o', s=size, facecolors=facec, edgecolors='black', linewidth=lw_m,
                               zorder=12)

        def plot_manifolds(ax, pj, A_val, xeq_val):
            k_sys, b_sys, mu_sys, ep_sys = self.app.get_sys_params()

            if self.app.cbmanif.isChecked():
                xl, yl = ax.get_xlim(), ax.get_ylim()
                try:
                    x0, y0, z0 = [float(v.strip()) for v in self.app.istart.text().split(',')]
                except:
                    x0, y0, z0 = 0.0, 0.0, 0.0

                if xl == (0.0, 1.0): xl, yl = (-3.0, 3.0), (-3.0, 3.0)
                if pj == '3D':
                    x_min, x_max = min(-2.5, xl[0]), max(2.5, xl[1])
                    y_min, y_max = min(-1.0, yl[0]), max(3.0, yl[1])
                    Xg, Yg = np.meshgrid(np.linspace(x_min, x_max, 100), np.linspace(y_min, y_max, 100))
                    Zg = Yg - (2.0 * Xg) / (1.0 + Xg ** 2)
                    ax.plot_surface(Xg, Yg, Zg, cmap='coolwarm', alpha=0.3, edgecolor='none', zorder=1)
                    y_line = np.linspace(y_min, y_max, 150)
                    ax.plot(np.ones_like(y_line), y_line, y_line - 1.0, color='crimson', linestyle='-', linewidth=lw,
                            zorder=3)
                    ax.plot(-np.ones_like(y_line), y_line, y_line + 1.0, color='blue', linestyle='-', linewidth=lw,
                            zorder=3)
                    ax.set_xlim([x_min, x_max]);
                    ax.set_ylim([y_min, y_max])
                elif pj == 'X-Y':
                    x_arr = np.linspace(min(-2.5, xl[0]), max(2.5, xl[1]), 400)
                    z_min, z_max = z0 - 0.5, z0 + 0.5
                    if len(self.trajectories) > 0:
                        trj = list(self.trajectories.values())[0]
                        z_min, z_max = np.min(trj['z']), np.max(trj['z'])
                    ax.plot(x_arr, z_min + (2.0 * x_arr) / (1.0 + x_arr ** 2), color='orange', lw=1.5, linestyle='--')
                    ax.plot(x_arr, z_max + (2.0 * x_arr) / (1.0 + x_arr ** 2), color='crimson', lw=1.5, linestyle='--')
                    ax.axvline(1.0, color='crimson', linestyle='-.', lw=1.5, alpha=0.7)
                    ax.axvline(-1.0, color='blue', linestyle='-.', lw=1.5, alpha=0.7)
                    ax.set_xlim([min(-2.5, xl[0]), max(2.5, xl[1])])

            if hasattr(self.app, 'cbfs') and self.app.cbfs.isChecked():
                folded_states = find_folded_states(A_val, xeq_val, k_sys, b_sys, mu_sys, ep_sys)
                xlim_orig, ylim_orig = ax.get_xlim(), ax.get_ylim()
                for fx, fy, fz, ftype in folded_states:
                    lbl, c = ("FN", "darkmagenta") if "узел" in ftype else (
                        ("FS", "darkcyan") if "седло" in ftype else ("FF", "saddlebrown"))
                    c1, c2 = (fx, fy) if pj == 'X-Y' else (
                        (fx, fz) if pj == 'X-Z' else ((fy, fz) if pj == 'Y-Z' else (fx, fy)))
                    dx, dy = (xlim_orig[1] - xlim_orig[0]) * 0.02, (ylim_orig[1] - ylim_orig[0]) * 0.03
                    if pj == '3D':
                        ax.scatter([fx], [fy], [fz], marker='X', s=140, c=c, edgecolor='white', linewidth=1.5,
                                   zorder=15)
                        ax.text(fx + dx, fy, fz + dy, lbl, fontsize=fs_let - 4, color=c, weight='bold')
                    else:
                        ax.scatter([c1], [c2], marker='X', s=140, c=c, edgecolor='white', linewidth=1.5, zorder=15)
                        ax.text(c1 + dx, c2 + dy, lbl, fontsize=fs_let - 4, color=c, weight='bold',
                                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=c, lw=1, alpha=0.8), zorder=16)

        cols = len(ph) + (1 if V > 0 else 0)

        if sep_phase and cols > 0:
            gs = gridspec.GridSpec(M * max(1, V), cols, wspace=ws, hspace=hs)
            for i, tid in enumerate(tids):
                A_trj, xeq_trj = get_params_from_tid(tid)
                k_sys, b_sys, mu_sys, ep_sys = self.app.get_sys_params()
                eqs_to_plot = find_equilibria_with_types(A_trj, xeq_trj, k_sys, b_sys, mu_sys, ep_sys)

                d = self.trajectories[tid]
                c = self.app.c1.colors[atids.index(tid) % len(self.app.c1.colors)]
                m = (d['t'] >= etm) & (d['t'] <= etM) if len(d['t']) > 0 else np.ones_like(d['t'], dtype=bool)

                for j, pj in enumerate(ph):
                    ax = fig.add_subplot(gs[i * max(1, V): (i + 1) * max(1, V), j],
                                         projection='3d' if pj == '3D' else None)
                    self.app.c1._setup_ax(ax, [], pj, show_labels=False)
                    plot_equilibria(ax, pj, eqs_to_plot)

                    ax.set_xlabel('x' if pj != 'Y-Z' else 'y', color='black', weight=ax_weight, fontsize=fs_ax)
                    ax.set_ylabel('y' if pj in ['3D', 'X-Y'] else 'z', color='black', weight=ax_weight, fontsize=fs_ax)
                    if pj == '3D' and hasattr(ax, 'zaxis'): ax.set_zlabel('z', color='black', weight=ax_weight,
                                                                          fontsize=fs_ax)
                    ax.tick_params(axis='both', which='major', labelsize=fs_tick)

                    if pj == '3D':
                        ax.plot(d['x'][m][::step], d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                    elif pj == 'X-Y':
                        ax.plot(d['x'][m][::step], d['y'][m][::step], color=c, lw=lw, alpha=0.8)
                    elif pj == 'X-Z':
                        ax.plot(d['x'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                    elif pj == 'Y-Z':
                        ax.plot(d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                    plot_manifolds(ax, pj, A_trj, xeq_trj)

                    if i < M - 1: ax.set_xlabel('')

                    if self.cb_z_ph.isChecked() and pj != '3D':
                        try:
                            idx_zoom = int(self.i_zph_idx.text())
                            if i == idx_zoom:
                                z_x1, z_x2, z_y1, z_y2 = map(float, self.i_zph_roi.text().split(','))
                                l_x, l_y, l_w, l_h = map(float, self.i_zph_loc.text().split(','))
                                axins = ax.inset_axes([l_x, l_y, l_w, l_h])

                                if pj == 'X-Y':
                                    axins.plot(d['x'][m][::step], d['y'][m][::step], color=c, lw=lw, alpha=0.8)
                                elif pj == 'X-Z':
                                    axins.plot(d['x'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                                elif pj == 'Y-Z':
                                    axins.plot(d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)

                                plot_equilibria(axins, pj, eqs_to_plot)
                                axins.set_xlim(z_x1, z_x2);
                                axins.set_ylim(z_y1, z_y2)
                                axins.set_xticks([]);
                                axins.set_yticks([])
                                ax.indicate_inset_zoom(axins, edgecolor="black")
                        except Exception as e:
                            print(f"Ошибка врезки ФП: {e}")

                if V > 0:
                    for k, vt in enumerate(vts):
                        ax = fig.add_subplot(gs[i * max(1, V) + k, len(ph)])
                        vdata, vl = (d['x'], 'x') if vt == 'x(t)' else (
                            (d['y'], 'y') if vt == 'y(t)' else (d['z'], 'z'))
                        ax.plot(d['t'][m][::step], vdata[m][::step], color=c, lw=lw)

                        ax.set_ylabel(vl, color='black', weight=ax_weight, fontsize=fs_ax)
                        ax.tick_params(axis='both', which='major', labelsize=fs_tick)
                        ax.grid(True, alpha=0.3)

                        if i == M - 1 and k == V - 1:
                            ax.set_xlabel('t', color='black', weight=ax_weight, fontsize=fs_ax)
                        else:
                            ax.tick_params(labelbottom=False)

                        if self.cb_z_t.isChecked():
                            try:
                                idx_zoom = int(self.i_zt_idx.text())
                                if i == idx_zoom and k == 0:
                                    z_t1, z_t2, z_v1, z_v2 = map(float, self.i_zt_roi.text().split(','))
                                    l_tx, l_ty, l_tw, l_th = map(float, self.i_zt_loc.text().split(','))
                                    axins_t = ax.inset_axes([l_tx, l_ty, l_tw, l_th])
                                    axins_t.plot(d['t'][m][::step], vdata[m][::step], color=c, lw=lw)
                                    axins_t.set_xlim(z_t1, z_t2);
                                    axins_t.set_ylim(z_v1, z_v2)
                                    axins_t.set_xticks([]);
                                    axins_t.set_yticks([])  # Убираем значения осей на врезке
                                    ax.indicate_inset_zoom(axins_t, edgecolor="black")
                            except Exception as e:
                                print(f"Ошибка врезки времени: {e}")

        elif not sep_phase and cols > 0:
            gs = gridspec.GridSpec(1, cols, wspace=ws)

            unique_params = set(get_params_from_tid(tid) for tid in tids)
            k_sys, b_sys, mu_sys, ep_sys = self.app.get_sys_params()
            all_eqs_sets = [(A_val, xeq_val, find_equilibria_with_types(A_val, xeq_val, k_sys, b_sys, mu_sys, ep_sys))
                            for A_val, xeq_val in unique_params]

            if len(ph) > 0:
                gs_left = gridspec.GridSpecFromSubplotSpec(P, 1, subplot_spec=gs[0, 0:len(ph)], hspace=hs)
                for j, pj in enumerate(ph):
                    ax = fig.add_subplot(gs_left[j, 0], projection='3d' if pj == '3D' else None)
                    self.app.c1._setup_ax(ax, [], pj, show_labels=False)

                    for A_val, xeq_val, eqs_set in all_eqs_sets:
                        plot_equilibria(ax, pj, eqs_set)

                    ax.set_xlabel('x' if pj != 'Y-Z' else 'y', color='black', weight=ax_weight, fontsize=fs_ax)
                    ax.set_ylabel('y' if pj in ['3D', 'X-Y'] else 'z', color='black', weight=ax_weight, fontsize=fs_ax)
                    if pj == '3D' and hasattr(ax, 'zaxis'): ax.set_zlabel('z', color='black', weight=ax_weight,
                                                                          fontsize=fs_ax)
                    ax.tick_params(axis='both', which='major', labelsize=fs_tick)

                    for tid in tids:
                        d = self.trajectories[tid]
                        c = self.app.c1.colors[atids.index(tid) % len(self.app.c1.colors)]
                        m = (d['t'] >= etm) & (d['t'] <= etM) if len(d['t']) > 0 else np.ones_like(d['t'], dtype=bool)

                        if pj == '3D':
                            ax.plot(d['x'][m][::step], d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                        elif pj == 'X-Y':
                            ax.plot(d['x'][m][::step], d['y'][m][::step], color=c, lw=lw, alpha=0.8)
                        elif pj == 'X-Z':
                            ax.plot(d['x'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                        elif pj == 'Y-Z':
                            ax.plot(d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)

                    for A_val, xeq_val, _ in all_eqs_sets:
                        plot_manifolds(ax, pj, A_val, xeq_val)

                    if j < P - 1: ax.set_xlabel('')

                    if self.cb_z_ph.isChecked() and pj != '3D':
                        try:
                            idx_zoom = int(self.i_zph_idx.text())
                            if j == idx_zoom:
                                z_x1, z_x2, z_y1, z_y2 = map(float, self.i_zph_roi.text().split(','))
                                l_x, l_y, l_w, l_h = map(float, self.i_zph_loc.text().split(','))
                                axins = ax.inset_axes([l_x, l_y, l_w, l_h])

                                for tid in tids:
                                    d = self.trajectories[tid]
                                    c = self.app.c1.colors[atids.index(tid) % len(self.app.c1.colors)]
                                    m = (d['t'] >= etm) & (d['t'] <= etM) if len(d['t']) > 0 else np.ones_like(d['t'],
                                                                                                               dtype=bool)
                                    if pj == 'X-Y':
                                        axins.plot(d['x'][m][::step], d['y'][m][::step], color=c, lw=lw, alpha=0.8)
                                    elif pj == 'X-Z':
                                        axins.plot(d['x'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)
                                    elif pj == 'Y-Z':
                                        axins.plot(d['y'][m][::step], d['z'][m][::step], color=c, lw=lw, alpha=0.8)

                                for A_val, xeq_val, eqs_set in all_eqs_sets:
                                    plot_equilibria(axins, pj, eqs_set)

                                axins.set_xlim(z_x1, z_x2);
                                axins.set_ylim(z_y1, z_y2)
                                axins.set_xticks([]);
                                axins.set_yticks([])
                                ax.indicate_inset_zoom(axins, edgecolor="black")
                        except Exception as e:
                            print(f"Ошибка врезки ФП (общий): {e}")

            if V > 0:
                gs_right = gridspec.GridSpecFromSubplotSpec(V * M, 1, subplot_spec=gs[0, len(ph)], hspace=hs)
                idx = 0
                for vt in vts:
                    for tid in tids:
                        ax = fig.add_subplot(gs_right[idx, 0])
                        d = self.trajectories[tid]
                        c = self.app.c1.colors[atids.index(tid) % len(self.app.c1.colors)]
                        m = (d['t'] >= etm) & (d['t'] <= etM) if len(d['t']) > 0 else np.ones_like(d['t'], dtype=bool)
                        vdata, vl = (d['x'], 'x') if vt == 'x(t)' else (
                            (d['y'], 'y') if vt == 'y(t)' else (d['z'], 'z'))

                        ax.plot(d['t'][m][::step], vdata[m][::step], color=c, lw=lw)
                        ax.set_ylabel(vl, color='black', weight=ax_weight, fontsize=fs_ax)
                        ax.tick_params(axis='both', which='major', labelsize=fs_tick)
                        ax.grid(True, alpha=0.3)

                        if idx == V * M - 1:
                            ax.set_xlabel('t', color='black', weight=ax_weight, fontsize=fs_ax)
                        else:
                            ax.tick_params(labelbottom=False)

                        # ВРЕЗКА ДЛЯ ВРЕМЕННОГО РЯДА В ОБЩЕМ РЕЖИМЕ
                        if self.cb_z_t.isChecked():
                            try:
                                idx_zoom = int(self.i_zt_idx.text())
                                if idx == idx_zoom:
                                    z_t1, z_t2, z_v1, z_v2 = map(float, self.i_zt_roi.text().split(','))
                                    l_tx, l_ty, l_tw, l_th = map(float, self.i_zt_loc.text().split(','))
                                    axins_t = ax.inset_axes([l_tx, l_ty, l_tw, l_th])
                                    axins_t.plot(d['t'][m][::step], vdata[m][::step], color=c, lw=lw)
                                    axins_t.set_xlim(z_t1, z_t2);
                                    axins_t.set_ylim(z_v1, z_v2)
                                    axins_t.set_xticks([]);
                                    axins_t.set_yticks([])
                                    ax.indicate_inset_zoom(axins_t, edgecolor="black")
                            except Exception as e:
                                print(f"Ошибка врезки времени (общий): {e}")

                        idx += 1

        if let_fmt:
            letters = list(string.ascii_lowercase) + [l * 2 for l in string.ascii_lowercase]
            for ax_idx, ax in enumerate(fig.axes):
                if ax.get_label() == '<inset_axes>':
                    continue
                label = let_fmt.replace("{letter}", letters[ax_idx])
                if hasattr(ax, 'text2D'):
                    ax.text2D(let_x, let_y, label, transform=ax.transAxes, fontsize=fs_let, fontweight='bold',
                              va='bottom', ha='left')
                else:
                    ax.text(let_x, let_y, label, transform=ax.transAxes, fontsize=fs_let, fontweight='bold',
                            va='bottom', ha='left')

        fig.align_ylabels()
        self.canvas.draw()

    def export_to_file(self):
        if not self.canvas.figure.axes:
            return QMessageBox.warning(self, "Внимание", "Сначала нажмите 'Обновить предпросмотр'.")

        k_val, b_val = self.app.ik.text().strip(), self.app.ib.text().strip()
        A_val, xeq_val = self.app.iA.text().strip(), self.app.ix.text().strip()

        filename_parts = [f"k={k_val}", f"b={b_val}", f"A={A_val}", f"xeq={xeq_val}"]
        selected_regimes = [name for name, cb in self.regimes.items() if cb.isChecked()]
        mmo_period = self.i_mmo_period.text().strip()

        if mmo_period: selected_regimes.append(f"{mmo_period}")
        if selected_regimes: filename_parts.append("-".join([r.replace(" ", "_") for r in selected_regimes]))

        custom_text = self.i_custom_text.text().strip()
        if custom_text: filename_parts.append(custom_text)

        default_filename = "_".join(filename_parts) + ".png"
        target_dir = r"E:\Neuron_Article_Images\New\Small"
        import os
        os.makedirs(target_dir, exist_ok=True)
        default_path = os.path.join(target_dir, default_filename)

        fp, _ = QFileDialog.getSaveFileName(self, "Сохранить", default_path, "PNG Image (*.png);;PDF File (*.pdf)")
        if fp:
            self.canvas.figure.savefig(fp, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Успех", f"График успешно сохранен в:\n{fp}")

class XmaxBifurcationWorker(QThread):
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(object, object, str, float, float)
    error_signal = pyqtSignal(str)

    def __init__(self, param_type, p_min, p_max, p_steps, fixed_val, k, b, mu, ep, start_pos, t_trans, t_meas, dt, use_cont):
        super().__init__()
        self.ptype, self.pmin, self.pmax, self.psteps = param_type, p_min, p_max, p_steps
        self.fval, self.k, self.b, self.mu, self.ep = fixed_val, k, b, mu, ep
        self.spos, self.ttrans, self.tmeas, self.dt = start_pos, t_trans, t_meas, dt
        self.use_cont, self.is_cancelled = use_cont, False

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        try:
            parr = np.linspace(self.pmin, self.pmax, self.psteps)
            ap, axmax = [], []
            curr = np.array(self.spos, dtype=np.float64)

            for i, p in enumerate(parr):
                if self.is_cancelled:
                    return
                A_val = float(p) if self.ptype == 'A' else float(self.fval)
                X_val = float(self.fval) if self.ptype == 'A' else float(p)
                if not self.use_cont:
                    curr = np.array(self.spos, dtype=np.float64)

                peaks, curr = get_xmax_on_the_fly(
                    curr, A_val, X_val, float(self.k), float(self.b),
                    float(self.mu), float(self.ep), float(self.dt),
                    float(self.ttrans), float(self.tmeas)
                )
                if peaks.size > 0:
                    ap.extend([float(p)] * int(peaks.size))
                    axmax.extend(peaks.tolist())
                self.progress_signal.emit(int((i + 1) / self.psteps * 100))

            self.finished_signal.emit(np.array(ap), np.array(axmax), self.ptype, self.pmin, self.pmax)
        except Exception as e:
            self.error_signal.emit(str(e))

class MplCanvasBase(FigureCanvas):
    def __init__(self, parent=None, width=12, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor=PLOT_BACKGROUND);
        super().__init__(self.fig)
        self.setStyleSheet("background: #ffffff;")

    def draw(self, *args, **kwargs):
        self._polish_axes()
        super().draw(*args, **kwargs)

    def _polish_axes(self):
        for ax in self.fig.axes:
            ax.set_facecolor(PLOT_BACKGROUND)
            ax.tick_params(colors="#4b5563", labelsize=10)
            ax.title.set_color("#111827")
            ax.xaxis.label.set_color("#374151")
            ax.yaxis.label.set_color("#374151")
            if hasattr(ax, "zaxis"):
                ax.zaxis.label.set_color("#374151")
            for spine in getattr(ax, "spines", {}).values():
                spine.set_color("#cfd7e3")
            legend = ax.get_legend()
            if legend:
                legend.get_frame().set_facecolor("#ffffff")
                legend.get_frame().set_edgecolor("#d8dee9")


class MplCanvasTrajectory(MplCanvasBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = plt.cm.tab10.colors

    def update_layout(self, trj, eqs, Aval, xval, k, b, mu, ep, spos, tstart=0, step=1, proj='3D', tvar='x(t)',
                      sfield=False, snull=False, smanif=False, ssep=False, sfs=False):
        import warnings
        warnings.filterwarnings("ignore", module="matplotlib")

        self.fig.clear()
        N = len(trj)
        if N == 0:
            axP = self.fig.add_subplot(111, projection='3d') if proj == '3D' else self.fig.add_subplot(111)
        else:
            gs = self.fig.add_gridspec(N, 2, width_ratios=[1.5, 1], hspace=0.3)
            axP = self.fig.add_subplot(gs[:, 0], projection='3d') if proj == '3D' else self.fig.add_subplot(gs[:, 0])
        self._setup_ax(axP, eqs, proj)

        axT0 = None
        for i, (tid, d) in enumerate(trj.items()):
            c, t, x, y, z = self.colors[i % len(self.colors)], d['t'], d['x'], d['y'], d['z']

            # --- НОВАЯ ЛОГИКА ФИЛЬТРАЦИИ ВРЕМЕНИ ---
            if len(t) > 0 and t[-1] < 0:
                # Обратное время
                ts = -tstart
                m = t <= ts
            else:
                # Прямое время
                ts = max(0, t[-1] * 0.8) if len(t) > 0 and 0 < t[-1] < tstart else tstart
                m = t >= ts if len(t) > 0 else np.ones_like(t, dtype=bool)
            # ---------------------------------------

            if proj == '3D':
                axP.plot(x[m][::step], y[m][::step], z[m][::step], c=c, lw=0.8, alpha=0.8, zorder=2)
            elif proj == 'X-Y':
                axP.plot(x[m][::step], y[m][::step], c=c, lw=1.2, alpha=0.8, zorder=2)
            elif proj == 'X-Z':
                axP.plot(x[m][::step], z[m][::step], c=c, lw=1.2, alpha=0.8, zorder=2)
            elif proj == 'Y-Z':
                axP.plot(y[m][::step], z[m][::step], c=c, lw=1.2, alpha=0.8, zorder=2)

            vd, vl = (x, 'x') if tvar == 'x(t)' else ((y, 'y') if tvar == 'y(t)' else (z, 'z'))
            axT = self.fig.add_subplot(gs[i, 1], sharex=axT0)
            axT0 = axT0 or axT
            axT.plot(t[m][::step], vd[m][::step], c=c, lw=1.2)
            axT.set_ylabel(vl, c=c, weight='bold')
            axT.grid(True, alpha=0.3)

            if smanif:
                xl, yl = axP.get_xlim(), axP.get_ylim()
                if xl == (0.0, 1.0): xl, yl = (-3.0, 3.0), (-3.0, 3.0)
                try:
                    x0, y0, z0 = spos
                except:
                    x0, y0, z0 = 0.0, 0.0, 0.0

                if proj == '3D':
                    x_min, x_max = min(-2.5, xl[0]), max(2.5, xl[1])
                    y_min, y_max = min(-1.0, yl[0]), max(3.0, yl[1])

                    x_surf = np.linspace(x_min, x_max, 100)
                    y_surf = np.linspace(y_min, y_max, 100)
                    Xg, Yg = np.meshgrid(x_surf, y_surf)
                    Zg = Yg - (2.0 * Xg) / (1.0 + Xg ** 2)

                    axP.plot_surface(Xg, Yg, Zg, cmap='coolwarm', alpha=0.3, edgecolor='none', zorder=1)

                    # Линии сгиба L+ и L-
                    y_line = np.linspace(y_min, y_max, 100)
                    axP.plot(np.ones_like(y_line), y_line, y_line - 1.0, color='crimson', linestyle='-', lw=2.5,
                             zorder=3, label='L+')
                    axP.plot(-np.ones_like(y_line), y_line, y_line + 1.0, color='blue', linestyle='-', lw=2.5, zorder=3,
                             label='L-')

                    axP.set_xlim([x_min, x_max])
                    axP.set_ylim([y_min, y_max])
                    zl = axP.get_zlim()
                    axP.set_zlim([min(zl[0], np.min(Zg) * 0.8), max(zl[1], np.max(Zg) * 0.8)])

                    try:
                        axP.set_box_aspect((1.5, 1.2, 1))
                    except:
                        pass

                elif proj == 'X-Y':
                    x_arr = np.linspace(min(-2.5, xl[0]), max(2.5, xl[1]), 400)
                    if len(trj) > 0:
                        first_trj = list(trj.values())[0]
                        z_min, z_max = np.min(first_trj['z']), np.max(first_trj['z'])
                    else:
                        z_min, z_max = z0 - 0.5, z0 + 0.5

                    y_min_curve = z_min + (2.0 * x_arr) / (1.0 + x_arr ** 2)
                    y_max_curve = z_max + (2.0 * x_arr) / (1.0 + x_arr ** 2)

                    axP.plot(x_arr, y_min_curve, color='orange', lw=1.5, linestyle='--', label=f'S0 (z={z_min:.2f})')
                    axP.plot(x_arr, y_max_curve, color='crimson', lw=1.5, linestyle='--', label=f'S0 (z={z_max:.2f})')

                    axP.axvline(1.0, color='crimson', linestyle='-.', lw=1.5, alpha=0.7)
                    axP.axvline(-1.0, color='blue', linestyle='-.', lw=1.5, alpha=0.7)
                    axP.set_xlim([min(-2.5, xl[0]), max(2.5, xl[1])])
                    if not axP.get_legend(): axP.legend(fontsize=8, loc='upper left')

                elif proj == 'X-Z':
                    x_arr = np.linspace(min(-2.5, xl[0]), max(2.5, xl[1]), 400)
                    if len(trj) > 0:
                        first_trj = list(trj.values())[0]
                        y_min, y_max = np.min(first_trj['y']), np.max(first_trj['y'])
                    else:
                        y_min, y_max = y0 - 0.5, y0 + 0.5

                    z_min_curve = y_min - (2.0 * x_arr) / (1.0 + x_arr ** 2)
                    z_max_curve = y_max - (2.0 * x_arr) / (1.0 + x_arr ** 2)

                    axP.plot(x_arr, z_min_curve, color='orange', lw=1.5, linestyle='--', label=f'S0 (y={y_min:.2f})')
                    axP.plot(x_arr, z_max_curve, color='crimson', lw=1.5, linestyle='--', label=f'S0 (y={y_max:.2f})')

                    axP.axvline(1.0, color='crimson', linestyle='-.', lw=1.5, alpha=0.7)
                    axP.axvline(-1.0, color='blue', linestyle='-.', lw=1.5, alpha=0.7)
                    axP.set_xlim([min(-2.5, xl[0]), max(2.5, xl[1])])
                    if not axP.get_legend(): axP.legend(fontsize=8, loc='upper left')

                elif proj == 'Y-Z':
                    y_arr = np.linspace(min(-1.0, xl[0]), max(3.0, xl[1]), 400)
                    z_curve = y_arr - (2.0 * x0) / (1.0 + x0 ** 2)
                    axP.plot(y_arr, z_curve, color='steelblue', lw=2.0, alpha=0.5, label=f'S0 (x={x0:.2f})')
                    axP.plot(y_arr, y_arr - 1.0, color='crimson', linestyle='--', lw=1.5, alpha=0.7)
                    axP.plot(y_arr, y_arr + 1.0, color='blue', linestyle='--', lw=1.5, alpha=0.7)
                    axP.fill_between(y_arr, y_arr - 1.0, y_arr + 1.0, color='steelblue', alpha=0.1)
                    axP.set_xlim([min(-1.0, xl[0]), max(3.0, xl[1])])
                    if not axP.get_legend(): axP.legend(fontsize=8, loc='upper left')

        if proj != '3D' and (sfield or snull):
            xl, yl = axP.get_xlim(), axP.get_ylim()
            Xg, Yg = np.meshgrid(np.linspace(xl[0], xl[1], 60), np.linspace(yl[0], yl[1], 60))
            U, V, (x0, y0, z0) = np.zeros_like(Xg), np.zeros_like(Yg), spos
            for i in range(60):
                for j in range(60):
                    if proj == 'X-Y':
                        d = equations_njit(0, np.array([Xg[i, j], Yg[i, j], z0]), Aval, xval, k, b, mu, ep)
                        U[i, j], V[i, j] = d[0], d[1]
                    elif proj == 'X-Z':
                        d = equations_njit(0, np.array([Xg[i, j], y0, Yg[i, j]]), Aval, xval, k, b, mu, ep)
                        U[i, j], V[i, j] = d[0], d[2]
                    elif proj == 'Y-Z':
                        d = equations_njit(0, np.array([x0, Xg[i, j], Yg[i, j]]), Aval, xval, k, b, mu, ep)
                        U[i, j], V[i, j] = d[1], d[2]
            if sfield: axP.streamplot(Xg, Yg, U, V, color='#ccc', density=1.0, linewidth=0.8, zorder=0)
            if snull:
                axP.contour(Xg, Yg, U, levels=[0], colors='g', alpha=0.7, linewidths=2, zorder=0)
                axP.contour(Xg, Yg, V, levels=[0], colors='orange', alpha=0.7, linewidths=2, zorder=0)
            axP.set_xlim(xl);
            axP.set_ylim(yl)

        if ssep:
            self._draw_separatrices(axP, eqs, Aval, xval, k, b, mu, ep, proj)

            # --- ВЫЗОВ ОТРИСОВКИ СВЕРНУТЫХ ТОЧЕК ---
        if sfs:
            xlim_orig = axP.get_xlim()
            ylim_orig = axP.get_ylim()
            if proj == '3D':
                zlim_orig = axP.get_zlim()

            folded_states = find_folded_states(Aval, xval, k, b, mu, ep)
            for fx, fy, fz, ftype in folded_states:
                if "узел" in ftype:
                    lbl, c = "FN", "darkmagenta"
                elif "седло" in ftype:
                    lbl, c = "FS", "darkcyan"
                else:
                    lbl, c = "FF", "saddlebrown"

                c1, c2 = (fx, fy) if proj == 'X-Y' else (
                    (fx, fz) if proj == 'X-Z' else ((fy, fz) if proj == 'Y-Z' else (fx, fy)))

                if proj == '3D':
                    axP.scatter(fx, fy, fz, marker='X', s=120, c=c, edgecolor='white', linewidth=1.5, zorder=12)
                    txt = axP.text(fx, fy, fz + 0.001, lbl, fontsize=10, c=c, weight='bold', ha='center')
                    txt.set_clip_on(True)
                    txt.set_clip_box(axP.bbox)
                else:
                    axP.scatter(c1, c2, marker='X', s=120, c=c, edgecolor='white', linewidth=1.5, zorder=12)
                    txt = axP.text(c1, c2 + 0.01, lbl, fontsize=10, c=c, weight='bold', ha='center')
                    txt.set_clip_on(True)
                    txt.set_clip_box(axP.bbox)

            axP.set_xlim(xlim_orig)
            axP.set_ylim(ylim_orig)
            if proj == '3D':
                axP.set_zlim(zlim_orig)


        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fig.tight_layout()
        self.draw()

    def _draw_separatrices(self, ax, eqs, Aval, xval, k, b, mu, ep, proj):
        t_end, dt = 100000.0, 0.1
        offset = 1e-3

        xlim_orig = ax.get_xlim()
        ylim_orig = ax.get_ylim()
        if proj == '3D':
            zlim_orig = ax.get_zlim()

        for pt in eqs:
            x, y, z, zone, eqt, ev = pt
            J = get_jacobian(x, y, zone, Aval, k, mu, ep)
            vals, vecs = np.linalg.eig(J)

            for i, val in enumerate(vals):
                if abs(np.imag(val)) < 1e-10:
                    v = np.real(vecs[:, i])
                    v = v / np.linalg.norm(v)

                    is_forward = bool(np.real(val) > 0)
                    c = 'darkorange' if is_forward else 'forestgreen'

                    for sign in [1, -1]:
                        s_start = np.array([x, y, z]) + sign * offset * v
                        trj = integrate_separatrix_numba(t_end, dt, s_start, Aval, xval, k, b, mu, ep, is_forward)

                        X, Y, Z = trj[:, 0], trj[:, 1], trj[:, 2]
                        mask = np.isfinite(X) & np.isfinite(Y) & np.isfinite(Z)
                        X, Y, Z = X[mask], Y[mask], Z[mask]

                        if proj == '3D':
                            ax.plot(X, Y, Z, color=c, linestyle='--', lw=1.5, alpha=0.9, zorder=3)
                        elif proj == 'X-Y':
                            ax.plot(X, Y, color=c, linestyle='--', lw=1.5, alpha=0.9, zorder=3)
                        elif proj == 'X-Z':
                            ax.plot(X, Z, color=c, linestyle='--', lw=1.5, alpha=0.9, zorder=3)
                        elif proj == 'Y-Z':
                            ax.plot(Y, Z, color=c, linestyle='--', lw=1.5, alpha=0.9, zorder=3)

        ax.set_xlim(xlim_orig)
        ax.set_ylim(ylim_orig)
        if proj == '3D':
            ax.set_zlim(zlim_orig)

    def _setup_ax(self, ax, eqs, prj, show_labels=True):
        ax.set_xlabel('x' if prj != 'Y-Z' else 'y')
        ax.set_ylabel('y' if prj in ['3D', 'X-Y'] else 'z')
        if prj == '3D':
            ax.set_zlabel('z')
        else:
            ax.grid(True, alpha=0.3)

        for pt in eqs:
            x, y, z, zone, eqt, ev = pt
            c1, c2 = (x, y) if prj == 'X-Y' else ((x, z) if prj == 'X-Z' else ((y, z) if prj == 'Y-Z' else (x, y)))
            if prj == '3D':
                ax.scatter(x, y, z, marker='*', s=150, c='red', edgecolor='k', zorder=10)
                if show_labels:
                    txt = ax.text(x, y, z + 0.001, eqt, fontsize=9, c='darkred', weight='bold', ha='center')
                    txt.set_clip_on(True)
                    txt.set_clip_box(ax.bbox)
            else:
                ax.scatter(c1, c2, marker='*', s=150, c='red', edgecolor='k', zorder=10)
                if show_labels:
                    txt = ax.text(c1, c2 + 0.001, eqt, fontsize=9, c='darkred', weight='bold', ha='center')
                    txt.set_clip_on(True)
                    txt.set_clip_box(ax.bbox)


class MplCanvasMap(MplCanvasBase):
    hover_signal = pyqtSignal(int);
    double_click_signal = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent);
        self.Z, self.extent = None, None
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_hover);
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def plot_map(self, X_arr, A_arr, Z, cmap, n_colors):
        self.fig.clear();
        self.Z, self.extent = Z, [X_arr.min(), X_arr.max(), A_arr.min(), A_arr.max()];
        ax = self.fig.add_subplot(111)
        ax.imshow(Z, origin='lower', extent=self.extent, aspect='auto', cmap=cmap, vmin=-0.5, vmax=n_colors - 0.5);
        ax.set_title("Карта");
        ax.set_xlabel("x_eq");
        ax.set_ylabel("A")
        with warnings.catch_warnings(): warnings.simplefilter("ignore"); self.fig.tight_layout()
        self.draw()

    def on_hover(self, ev):
        if ev.inaxes and self.Z is not None:
            xi, yi = int((ev.xdata - self.extent[0]) / (self.extent[1] - self.extent[0]) * self.Z.shape[1]), int(
                (ev.ydata - self.extent[2]) / (self.extent[3] - self.extent[2]) * self.Z.shape[0])
            self.hover_signal.emit(
                int(self.Z[max(0, min(yi, self.Z.shape[0] - 1)), max(0, min(xi, self.Z.shape[1] - 1))]))

    def on_click(self, ev):
        if ev.dblclick and ev.inaxes and self.Z is not None: self.double_click_signal.emit(ev.xdata, ev.ydata)


class MplCanvasPoincare1D(MplCanvasBase):
    def plot_1d_map(self, t, data, title):
        self.fig.clear();
        ax = self.fig.add_subplot(111)
        pk = data[1:-1][(data[1:-1] > data[:-2]) & (data[1:-1] > data[2:])]
        if len(pk) < 2: ax.text(0.5, 0.5, "Мало данных", ha='center'); self.draw(); return
        xn, xnp1 = pk[:-1], pk[1:];
        ax.scatter(xn, xnp1, color='b', alpha=0.6, edgecolor='k', s=30)
        mv, Mv = min(np.min(xn), np.min(xnp1)), max(np.max(xn), np.max(xnp1));
        pad = (Mv - mv) * 0.1 or 0.1;
        lims = [mv - pad, Mv + pad]
        ax.plot(lims, lims, 'k--', alpha=0.5);
        ax.set_xlim(lims);
        ax.set_ylim(lims);
        ax.grid(True, alpha=0.3);
        ax.set_title(f"1D Карта\n{title}")
        with warnings.catch_warnings(): warnings.simplefilter("ignore"); self.fig.tight_layout()
        self.draw()


class MplCanvasPoincare2D(MplCanvasBase):
    def plot_2d_section(self, x, y, z, plane, cval, dir_sign, title):
        self.fig.clear();
        ax = self.fig.add_subplot(111)
        vs, c1, c2, l1, l2 = (y, x, z, 'x', 'z') if plane == 'Y = C' else (
            (x, y, z, 'y', 'z') if plane == 'X = C' else (z, x, y, 'x', 'y'))
        m = (vs[:-1] < cval) & (vs[1:] >= cval) if dir_sign == '+' else (vs[:-1] > cval) & (vs[1:] <= cval);
        idx = np.where(m)[0]
        if len(idx) == 0: ax.text(0.5, 0.5, "Нет пересечений", ha='center'); self.draw(); return
        fr = (cval - vs[idx]) / (vs[idx + 1] - vs[idx]);
        ax.scatter(c1[idx] + fr * (c1[idx + 1] - c1[idx]), c2[idx] + fr * (c2[idx + 1] - c2[idx]), c='r', edgecolor='k',
                   s=20)
        ax.set_title(f"2D Сечение\n{title}");
        ax.set_xlabel(l1);
        ax.set_ylabel(l2);
        ax.grid(True, alpha=0.3)
        with warnings.catch_warnings(): warnings.simplefilter("ignore"); self.fig.tight_layout()
        self.draw()


class MplCanvasISI(MplCanvasBase):
    def __init__(self, parent=None):
        super().__init__(parent);
        self.colors = plt.cm.tab10.colors

    def update_layout(self, isidict):
        self.fig.clear()
        if not isidict:
            self.fig.add_subplot(111).text(0.5, 0.5, "Нет данных", ha='center')
            self.draw()
            return

        valid_items = []
        for name, data in isidict.items():
            isi = clean_isi_values(data.get('isi', []))
            if isi.size >= 2:
                mean = float(np.mean(isi))
                cv = float(np.std(isi) / mean) if mean > 0 else 0.0
                valid_items.append((name, isi, mean, cv))

        if not valid_items:
            self.fig.add_subplot(111).text(0.5, 0.5, "Недостаточно корректных ISI", ha='center')
            self.draw()
            return

        gs = gridspec.GridSpec(1, 2, width_ratios=[1.2, 1]);
        a1, a2 = self.fig.add_subplot(gs[0]), self.fig.add_subplot(gs[1]);
        gm, gM = float('inf'), float('-inf')
        per_series_limit = max(1000, MAX_ISI_PLOT_POINTS // max(1, len(valid_items)))

        for i, (name, isi, mean, cv) in enumerate(valid_items):
            c = self.colors[i % len(self.colors)]
            plot_isi = isi[downsample_indices(isi.size, per_series_limit)]
            bins = min(100, max(10, int(np.sqrt(plot_isi.size))))
            a1.hist(plot_isi, bins=bins, color=c, alpha=0.5, label=f"{name} (CV={cv:.3f})")
            a1.axvline(mean, color=c, ls='--')

            if plot_isi.size > 1:
                a2.scatter(plot_isi[:-1], plot_isi[1:], c=c, alpha=0.6, s=12, edgecolor='none')
                gm = min(gm, float(np.min(plot_isi)))
                gM = max(gM, float(np.max(plot_isi)))

        a1.set_title("Гистограмма ISI");
        a1.set_xlabel("ISI")
        a1.set_ylabel("Количество")
        a1.legend(fontsize=8);
        a1.grid(True, alpha=0.3)
        if gm != float('inf'):
            p = (gM - gm) * 0.1 or 0.1
            a2.plot([gm - p, gM + p], [gm - p, gM + p], 'k--', alpha=0.3)
            a2.set_xlim([gm - p, gM + p])
            a2.set_ylim([gm - p, gM + p])
        a2.set_title("Отображение ISI");
        a2.set_xlabel("ISI(n)")
        a2.set_ylabel("ISI(n+1)")
        a2.grid(True, alpha=0.3)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore");
            self.fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        self.draw()


class MplCanvasBifurcation(MplCanvasBase):
    double_click_signal = pyqtSignal(str, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = plt.cm.tab10.colors
        self.plotted_data = []
        self.fig.canvas.mpl_connect('button_press_event', self.on_click)

    def update_layout(self, bdict):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        self.plotted_data.clear()

        if not bdict:
            ax.text(0.5, 0.5, "Нет данных", ha='center')
            self.draw()
            return

        plotted = 0
        for i, (k, d) in enumerate(bdict.items()):
            x, y = clean_xy_values(d.get('p_vals', []), d.get('isi_vals', []), positive_y=True)
            if y.size == 0:
                continue

            remaining = MAX_BIFURCATION_PLOT_POINTS - plotted
            if remaining <= 0:
                break

            idx = downsample_indices(y.size, remaining)

            self.plotted_data.append({
                'p': x[idx],
                'isi': y[idx],
                'param_name': d.get('param_name'),
                'fixed_val': d.get('fixed_val')
            })

            ax.scatter(x[idx], y[idx], color=self.colors[i % len(self.colors)],
                       s=2.0, alpha=0.45, marker='.', label=k)
            plotted += np.asarray(y[idx]).size

        if plotted == 0:
            ax.text(0.5, 0.5, "Нет положительных ISI для лог-шкалы", ha='center')
            self.draw()
            return

        ax.set_title("1D Бифуркационная диаграмма ISI")
        ax.set_xlabel("Параметр")
        ax.set_ylabel("Межспайковый интервал (ISI)")
        ax.set_yscale('log')
        ax.grid(True, which="major", linestyle='-', linewidth=0.8, alpha=0.6)
        ax.grid(True, which="minor", linestyle='--', linewidth=0.4, alpha=0.3)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            leg = ax.legend(fontsize=9, markerscale=5)
            for lh in leg.legend_handles:
                lh.set_alpha(1)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fig.tight_layout()
        self.draw()

    def on_click(self, ev):
        if ev.dblclick and ev.inaxes and self.plotted_data:
            x_click = float(ev.xdata)
            y_click = float(ev.ydata)

            if y_click <= 0: return

            best_dist = float('inf')
            best_pn, best_p, best_fv = None, None, None

            x_min, x_max = ev.inaxes.get_xlim()
            y_min, y_max = ev.inaxes.get_ylim()

            x_range = x_max - x_min if x_max != x_min else 1.0
            y_range = np.log10(y_max) - np.log10(y_min) if (y_max > 0 and y_min > 0) else 1.0
            if y_range == 0: y_range = 1.0

            for d in self.plotted_data:
                p_arr = d['p']
                isi_arr = d['isi']

                dx = (p_arr - x_click) / x_range
                dy = (np.log10(isi_arr) - np.log10(y_click)) / y_range

                dist = dx ** 2 + dy ** 2
                idx = np.argmin(dist)

                if dist[idx] < best_dist:
                    best_dist = dist[idx]
                    best_p = p_arr[idx]
                    best_pn = d['param_name']
                    best_fv = d['fixed_val']

            if best_pn is not None:
                self.double_click_signal.connect
                self.double_click_signal.emit(best_pn, float(best_p), float(best_fv))


class MplCanvasEquilibriaBranches(MplCanvasBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = {1: '#10b981', 2: '#ef4444', 3: '#f59e0b', 4: '#3b82f6'}
        self.labels = {1: 'Устойчивое', 2: 'Седло', 3: 'Седло-фокус', 4: 'Неустойчивое'}

    def _polish_axes(self):
        super()._polish_axes()

        for ax in self.fig.axes:
            ax.tick_params(labelsize=26)

    def update_layout(self, eq_data, param_name, var_name):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        has_data = False
        for t in [1, 2, 3, 4]:
            if len(eq_data[t]['p']) > 0:
                ax.scatter(eq_data[t]['p'], eq_data[t]['v'], s=4.0, color=self.colors[t], label=self.labels[t],
                           zorder=5 - t)
                has_data = True

        if not has_data:
            ax.text(0.5, 0.5, "Нет точек равновесия", ha='center')
            self.draw()
            return

        p_label = "x_{eq}" if param_name == "x_eq" else param_name
        v_label = f"{var_name}^*"

        ax.set_xlabel(f"${p_label}$", fontsize=25)
        ax.set_ylabel(f"${v_label}$", fontsize=25)

        ax.grid(True, which="major", linestyle='-', linewidth=0.8, alpha=0.6)


        handles, labels = ax.get_legend_handles_labels()
        if handles:
            leg = ax.legend(handles, labels, loc='best', fontsize=20)
            for lh in leg.legend_handles:
                lh.set_alpha(1)
                lh._sizes = [30]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fig.tight_layout()
        self.draw()


class MplCanvasNetwork(MplCanvasBase):
    def __init__(self, parent=None):
        super().__init__(parent, height=10)

    def plot_space_time(self, t, s_out, N):
        self.fig.clear()
        if len(t) == 0:
            self.fig.add_subplot(111).text(0.5, 0.5, "Нет данных", ha='center')
            self.draw()
            return

        x_data = s_out[:, :N].T
        gs = gridspec.GridSpec(2, 1, height_ratios=[1.5, 1], hspace=0.25)

        ax1 = self.fig.add_subplot(gs[0])
        im = ax1.imshow(x_data, aspect='auto', origin='lower',
                        extent=[t[0], t[-1], 0.5, N + 0.5],
                        cmap='magma', vmin=np.percentile(x_data, 5), vmax=np.percentile(x_data, 95))
        ax1.set_ylabel('Индекс нейрона (i)')
        ax1.set_title('Пространственно-временная диаграмма')
        self.fig.colorbar(im, ax=ax1, label='$x_i(t)$')

        ax2 = self.fig.add_subplot(gs[1], sharex=ax1)
        plot_limit = min(N, 20)
        for i in range(plot_limit):
            ax2.plot(t, x_data[i], alpha=0.6, lw=0.8, label=f"Нейрон {i + 1}" if plot_limit <= 5 else None)

        ax2.set_xlabel('Время (t)')
        ax2.set_ylabel('$x(t)$')
        ax2.grid(True, alpha=0.3)
        if plot_limit <= 5:
            ax2.legend(loc='upper right', fontsize=8)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fig.tight_layout()
        self.draw()

class NeuroApp(QMainWindow):
    def start_xmax_bifurcation(self):
        try:
            pt = self.xm_prm.currentText()
            pmin, pmax, psteps = float(self.xm_min.text()), float(self.xm_max.text()), int(self.xm_stp.text())
            fval = float(self.iA.text()) if pt == 'x_eq' else float(self.ix.text())
            spos = [float(v.strip()) for v in self.istart.text().split(',')]
            ttrans, tmeas, dt = float(self.xm_tr.text()), float(self.xm_me.text()), float(self.idt.text())
            k, b, mu, ep = self.get_sys_params()
        except ValueError:
            return QMessageBox.critical(self, "Ошибка", "Проверьте параметры.")

        self.xm_bld.setEnabled(False); self.xm_ccl.setEnabled(True); self.xm_prog.setValue(0)
        self.set_status("Строим диаграмму x_max...", "working")
        self.xm_worker = XmaxBifurcationWorker(pt, pmin, pmax, psteps, fval, k, b, mu, ep, spos, ttrans, tmeas, dt, self.xm_cont.isChecked())
        self.xm_worker.progress_signal.connect(self.xm_prog.setValue)
        self.xm_worker.finished_signal.connect(self.on_xmax_finished)
        self.xm_worker.error_signal.connect(self.on_xmax_error)
        self.xm_worker.start()

    def cancel_xmax_bifurcation(self):
        if hasattr(self, 'xm_worker') and self.xm_worker.isRunning():
            self.xm_worker.cancel()
            self.xm_bld.setEnabled(True); self.xm_ccl.setEnabled(False)
            self.set_status("Построение x_max отменено.", "warning")

    def on_xmax_finished(self, p_vals, xmax_vals, pn, pmin, pmax):
        self.c10.update_layout(p_vals, xmax_vals, pn, pmin, pmax)
        self.xm_bld.setEnabled(True); self.xm_ccl.setEnabled(False)
        self.set_status(f"Диаграмма x_max готова ({len(xmax_vals)} точек).", "ready")

    def on_xmax_error(self, err):
        self.xm_bld.setEnabled(True); self.xm_ccl.setEnabled(False)
        self.set_status("Ошибка при построении x_max.", "error")
        QMessageBox.warning(self, "Ошибка", err)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeuroDynamics V12.0 - Universal Parameter Explorer")
        self.setGeometry(50, 50, 1600, 950)
        self.setMinimumSize(1180, 760)
        self.setStyleSheet(APP_STYLESHEET)
        self.trajectories, self.isi_results, self.bifurcation_results, self.current_eqs, self.legend_items = {}, {}, {}, [], []

        self.solver_worker = None
        self.network_worker = None

        self.init_ui()
        self.update_equilibria()

    @staticmethod
    def set_button_role(button, role):
        button.setProperty("role", role)
        button.style().unpolish(button)
        button.style().polish(button)

    def set_status(self, text, state="ready"):
        self.lbl.setText(text)
        self.lbl.setProperty("state", state)
        self.lbl.style().unpolish(self.lbl)
        self.lbl.style().polish(self.lbl)

    def init_ui(self):
        cw = QWidget();
        cw.setObjectName("AppRoot")
        self.setCentralWidget(cw);
        ml = QVBoxLayout(cw);
        ml.setContentsMargins(14, 14, 14, 14)
        ml.setSpacing(12)
        cp = QGroupBox("Параметры модели и расчета")
        cp_layout = QVBoxLayout(cp)
        cp_layout.setSpacing(10)

        # --- НОВЫЙ БЛОК ПАРАМЕТРОВ СИСТЕМЫ ---
        r0 = QHBoxLayout()
        r0.setSpacing(8)
        self.ik = QLineEdit("-7.7");
        self.ik.setFixedWidth(50)
        self.ib = QLineEdit("8.1");
        self.ib.setFixedWidth(50)
        self.imu = QLineEdit("0.01");
        self.imu.setFixedWidth(60)
        self.iep = QLineEdit("0.0001");
        self.iep.setFixedWidth(70)
        for w in [QLabel("k:"), self.ik, QLabel("b:"), self.ib, QLabel("mu:"), self.imu, QLabel("ep:"),
                  self.iep]: r0.addWidget(w)
        r0.addStretch()

        # --- НОВЫЙ БЛОК ШУМА ---
        r0_noise = QHBoxLayout()
        r0_noise.setSpacing(8)
        self.cb_noise = QCheckBox("Цветной шум (OU)")
        self.cb_noise.toggled.connect(self.toggle_noise_inputs)

        self.iD = QLineEdit("0.1")
        self.iD.setFixedWidth(50)
        self.iD.setEnabled(False)

        self.itau = QLineEdit("1.0")
        self.itau.setFixedWidth(50)
        self.itau.setEnabled(False)

        r0_noise.addWidget(self.cb_noise)
        r0_noise.addWidget(QLabel("D:"))
        r0_noise.addWidget(self.iD)
        r0_noise.addWidget(QLabel("tau_corr:"))
        r0_noise.addWidget(self.itau)
        r0_noise.addStretch()

        # --- БЛОК АНСАМБЛЯ ---
        r_net = QHBoxLayout()
        r_net.setSpacing(8)
        self.cb_net_mode = QCheckBox("Режим ансамбля")
        self.cb_net_mode.setStyleSheet("font-weight: bold; color: #b91c1c;")

        self.iN = QLineEdit("3")
        self.iN.setFixedWidth(40)
        self.c_topo = QComboBox()
        self.c_topo.addItems(["ring", "pair", "all-to-all", "random"])

        self.ig_el = QLineEdit("0.0");
        self.ig_el.setFixedWidth(50)
        self.ig_syn = QLineEdit("0.0");
        self.ig_syn.setFixedWidth(50)

        self.c_het_param = QComboBox()
        self.c_het_param.addItems(['b', 'x_eq', 'A'])
        self.c_het_param.setToolTip("Параметр для внесения разброса")

        self.i_hetero = QLineEdit("0.0")
        self.i_hetero.setFixedWidth(50)

        # Все элементы управления ансамблем должны находиться в строке
        # параметров, иначе режим включается, но настроить сеть невозможно.
        for w in [self.cb_net_mode, QLabel("N:"), self.iN,
                  QLabel("Топология:"), self.c_topo,
                  QLabel("g_el:"), self.ig_el,
                  QLabel("g_syn:"), self.ig_syn,
                  QLabel("Параметр шума:"), self.c_het_param,
                  QLabel("Δ:"), self.i_hetero]:
            r_net.addWidget(w)
        r_net.addStretch()

        # Таблица ручного ввода (до 10 нейронов)
        self.net_table_grp = QGroupBox("Параметры нейронов (Ручной ввод до N=10)")
        ntl = QVBoxLayout(self.net_table_grp)
        self.net_table = QTableWidget()
        self.net_table.setColumnCount(6)
        self.net_table.setHorizontalHeaderLabels(['x_eq', 'A', 'b', 'x(0)', 'y(0)', 'z(0)'])
        self.net_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        ntl.addWidget(self.net_table)

        btns_net = QHBoxLayout()
        self.b_rand_prm = QPushButton("Случ. параметры")
        self.b_rand_ics = QPushButton("Случ. НУ")
        self.set_button_role(self.b_rand_prm, "secondary")
        self.set_button_role(self.b_rand_ics, "secondary")
        self.b_rand_prm.clicked.connect(self.randomize_net_params)
        self.b_rand_ics.clicked.connect(self.randomize_net_ics)
        btns_net.addWidget(self.b_rand_prm)
        btns_net.addWidget(self.b_rand_ics)
        btns_net.addStretch()
        ntl.addLayout(btns_net)
        self.net_table_grp.hide()

        self.cb_net_mode.toggled.connect(self.update_network_ui)
        self.iN.textChanged.connect(self.update_network_ui)

        r1 = QHBoxLayout()
        r1.setSpacing(8)
        r1.addWidget(QLabel("A:"));
        self.iA = QLineEdit("0.5");
        self.iA.setFixedWidth(60);
        r1.addWidget(self.iA)
        r1.addWidget(QLabel("x_eq:"));
        self.ix = QLineEdit("0.5");
        self.ix.setFixedWidth(60);
        r1.addWidget(self.ix)
        r1.addWidget(QLabel("Время (t):"));
        self.itend = QLineEdit("150000");
        self.itend.setFixedWidth(70);
        r1.addWidget(self.itend)
        self.bfq = QPushButton("Найти СР");
        self.set_button_role(self.bfq, "secondary")
        self.bfq.clicked.connect(self.update_equilibria);
        r1.addWidget(self.bfq)
        self.blyap = QPushButton("Ляпунов (LE)")
        self.set_button_role(self.blyap, "accent")
        self.blyap.clicked.connect(self.start_lyapunov_calc)
        r1.addWidget(self.blyap)
        self.blyap_cancel = QPushButton("Стоп LE")
        self.blyap_cancel.setEnabled(False)
        self.blyap_cancel.clicked.connect(self.cancel_lyapunov_calc)
        r1.addWidget(self.blyap_cancel)
        r1.addWidget(QLabel("Старт (x,y,z):"));
        self.istart = QLineEdit("0.0, 0.0, 0.0");
        self.istart.setFixedWidth(120);
        r1.addWidget(self.istart)

        r2 = QHBoxLayout()
        r2.setSpacing(8)
        r2.addWidget(QLabel("Метод:"));
        self.cmeth = QComboBox();
        self.cmeth.addItems(['RK4 (Numba)', 'Radau', 'BDF', 'LSODA', 'RK45']);
        r2.addWidget(self.cmeth)
        r2.addWidget(QLabel("dt:"));
        self.idt = QLineEdit("0.1");
        self.idt.setFixedWidth(50);
        r2.addWidget(self.idt)
        r2.addWidget(QLabel("rtol:"));
        self.irtol = QLineEdit("1e-4");
        self.irtol.setFixedWidth(50);
        r2.addWidget(self.irtol)
        r2.addWidget(QLabel("atol:"));
        self.iatol = QLineEdit("1e-6");
        self.iatol.setFixedWidth(50);
        r2.addWidget(self.iatol)
        r2.addWidget(QLabel("Рис с t="));
        self.idraw = QLineEdit("100000");
        self.idraw.setFixedWidth(60);
        r2.addWidget(self.idraw)

        self.cb_rev_time = QCheckBox("Вспять (t < 0)")
        r2.addWidget(self.cb_rev_time)

        r2.addWidget(QLabel("Шаг:"));
        r2.addWidget(QLabel("Шаг:"));
        self.istep = QLineEdit("1");
        self.istep.setFixedWidth(30);
        r2.addWidget(self.istep)

        r3 = QHBoxLayout()
        r3.setSpacing(8)
        r3.addWidget(QLabel("Проекция:"));
        self.cproj = QComboBox();
        self.cproj.addItems(['3D', 'X-Y', 'X-Z', 'Y-Z']);
        r3.addWidget(self.cproj)
        self.cbf = QCheckBox("Векторное поле");
        r3.addWidget(self.cbf);
        self.cbn = QCheckBox("Изоклины");
        r3.addWidget(self.cbn)
        self.cbmanif = QCheckBox("Многообразие S0");
        r3.addWidget(self.cbmanif)

        self.cbsep = QCheckBox("Сепаратрисы");
        r3.addWidget(self.cbsep)

        self.cbfs = QCheckBox("Свернутые особые точки");
        r3.addWidget(self.cbfs)

        r3.addSpacing(20);
        r3.addWidget(QLabel("Ось t:"));
        self.ctvar = QComboBox();
        self.ctvar.addItems(['x(t)', 'y(t)', 'z(t)']);
        r3.addWidget(self.ctvar)
        self.bupd = QPushButton("Обновить вид");
        self.set_button_role(self.bupd, "secondary")
        self.bupd.clicked.connect(self.refresh_view);
        r3.addWidget(self.bupd);
        r3.addStretch()

        rbtn = QHBoxLayout()
        rbtn.setSpacing(8)
        self.brun = QPushButton("Считать");
        self.set_button_role(self.brun, "primary")
        self.brun.clicked.connect(self.start_calculation);
        rbtn.addWidget(self.brun)
        self.bcanc = QPushButton("Отмена");
        self.set_button_role(self.bcanc, "danger")
        self.bcanc.setEnabled(False);
        self.bcanc.clicked.connect(self.cancel_calculation);
        rbtn.addWidget(self.bcanc)
        self.lbl = QLabel("Готов.");
        self.lbl.setObjectName("StatusLabel")
        self.lbl.setProperty("state", "ready")
        status_box = QGroupBox("Управление")
        sl = QVBoxLayout(status_box);
        sl.setSpacing(8)
        sl.addLayout(rbtn);
        sl.addWidget(self.lbl)

        cpl = QVBoxLayout();
        cpl.addLayout(r0)
        cpl.addLayout(r0_noise)
        cpl.addLayout(r_net)
        # Таблица параметров должна быть частью layout, чтобы show()/hide()
        # действительно отображали её при N <= 10.
        cpl.addWidget(self.net_table_grp)
        cpl.addLayout(r1);
        cpl.addLayout(r2);
        cpl.addLayout(r3)
        thl = QHBoxLayout();
        thl.setSpacing(12)
        thl.addLayout(cpl);
        thl.addStretch();
        thl.addWidget(status_box);
        cp_layout.addLayout(thl);
        ml.addWidget(cp)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # 1. Траектории
        t1 = QWidget();
        l1 = QHBoxLayout(t1);
        p1 = QVBoxLayout();
        self.c1 = MplCanvasTrajectory(self)
        p1.addWidget(NavigationToolbar(self.c1, self));
        p1.addWidget(self.c1);
        l1.addLayout(p1, 5)
        pr1 = QVBoxLayout();
        self.lw1 = QListWidget();
        self.lw1.setAlternatingRowColors(True)
        self.lw1.setContextMenuPolicy(Qt.CustomContextMenu);
        self.lw1.customContextMenuRequested.connect(self.show_context_menu)
        pr1.addWidget(QLabel("Траектории:"));
        pr1.addWidget(self.lw1);
        be = QPushButton("Экспорт");
        self.set_button_role(be, "secondary")
        be.clicked.connect(self.export_custom_figure);
        pr1.addWidget(be)
        bc = QPushButton("Очистить");
        self.set_button_role(bc, "danger")
        bc.clicked.connect(self.clear_all);
        pr1.addWidget(bc);
        l1.addLayout(pr1, 1);
        self.tabs.addTab(t1, "Траектории")

        # 2. Таблица
        t2 = QWidget();
        l2 = QVBoxLayout(t2);
        self.tabeq = QTableWidget();
        self.tabeq.setAlternatingRowColors(True)
        self.tabeq.verticalHeader().setVisible(False)
        self.tabeq.setColumnCount(7)
        self.tabeq.setHorizontalHeaderLabels(["№", "x", "y", "z", "Зона", "Соб. числа", "Тип"])
        self.tabeq.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch);
        self.tabeq.setEditTriggers(QTableWidget.NoEditTriggers);
        self.tabeq.itemDoubleClicked.connect(self.on_table_double_click)
        l2.addWidget(self.tabeq);
        self.tabs.addTab(t2, "Таблица СР")

        # 3. Карта
        t3 = QWidget();
        l3 = QVBoxLayout(t3);
        mc = QHBoxLayout()
        self.mxmin, self.mxmax, self.mamin, self.mamax, self.mres = QLineEdit("-2.0"), QLineEdit("2.0"), QLineEdit(
            "0.0"), QLineEdit("2.0"), QLineEdit("50")
        for w in [QLabel("Xmin"), self.mxmin, QLabel("Xmax"), self.mxmax, QLabel("Amin"), self.mamin, QLabel("Amax"),
                  self.mamax, QLabel("N"), self.mres]: mc.addWidget(w)
        self.bmap = QPushButton("Карта");
        self.set_button_role(self.bmap, "primary")
        self.bmap.clicked.connect(self.start_map_build);
        mc.addWidget(self.bmap)
        self.cmap = QPushButton("Отмена");
        self.set_button_role(self.cmap, "danger")
        self.cmap.setEnabled(False);
        self.cmap.clicked.connect(self.cancel_map_build);
        mc.addWidget(self.cmap)
        l3.addLayout(mc);
        self.mprog = QProgressBar();
        self.mprog.setValue(0);
        l3.addWidget(self.mprog)
        mvl = QHBoxLayout();
        cl = QVBoxLayout();
        self.c3 = MplCanvasMap(self);
        self.c3.hover_signal.connect(self.highlight_legend);
        self.c3.double_click_signal.connect(self.on_map_double_click)
        cl.addWidget(NavigationToolbar(self.c3, self));
        cl.addWidget(self.c3);
        mvl.addLayout(cl, 4)
        self.lgrp = QGroupBox("Комбинации");
        ll = QVBoxLayout();
        s = QScrollArea();
        s.setWidgetResizable(True);
        sw = QWidget();
        self.llay = QVBoxLayout(sw);
        self.llay.addStretch();
        s.setWidget(sw);
        ll.addWidget(s);
        self.lgrp.setLayout(ll);
        mvl.addWidget(self.lgrp, 1);
        l3.addLayout(mvl);
        self.tabs.addTab(t3, "Карта")

        # 4. 1D
        t4 = QWidget();
        l4 = QVBoxLayout(t4);
        p4 = QHBoxLayout()
        self.tr1d = QComboBox();
        self.vr1d = QComboBox();
        self.vr1d.addItems(['x', 'y', 'z']);
        self.bp1 = QPushButton("Построить 1D");
        self.set_button_role(self.bp1, "primary")
        self.bp1.clicked.connect(self.build_poincare_1d)
        p4.addWidget(QLabel("Траектория:"));
        p4.addWidget(self.tr1d);
        p4.addWidget(QLabel("Ось:"));
        p4.addWidget(self.vr1d);
        p4.addWidget(self.bp1);
        p4.addStretch();
        l4.addLayout(p4)
        self.c4 = MplCanvasPoincare1D(self);
        l4.addWidget(NavigationToolbar(self.c4, self));
        l4.addWidget(self.c4);
        self.tabs.addTab(t4, "1D Карта")

        # 5. 2D
        t5 = QWidget();
        l5 = QVBoxLayout(t5);
        p5 = QHBoxLayout()
        self.tr2d = QComboBox();
        self.pl2d = QComboBox();
        self.pl2d.addItems(['Y = C', 'X = C', 'Z = C']);
        self.c2d = QLineEdit("0.0");
        self.d2d = QComboBox();
        self.d2d.addItems(['+', '-']);
        self.bp2 = QPushButton("Построить 2D");
        self.set_button_role(self.bp2, "primary")
        self.bp2.clicked.connect(self.build_poincare_2d)
        for w in [QLabel("Траектория:"), self.tr2d, QLabel("Плоскость:"), self.pl2d, self.c2d, self.d2d,
                  self.bp2]: p5.addWidget(w)
        p5.addStretch();
        l5.addLayout(p5);
        self.c5 = MplCanvasPoincare2D(self);
        l5.addWidget(NavigationToolbar(self.c5, self));
        l5.addWidget(self.c5);
        self.tabs.addTab(t5, "2D Сечение")

        # 6. ISI
        t6 = QWidget();
        l6 = QHBoxLayout(t6);
        p6l = QVBoxLayout();
        self.c6 = MplCanvasISI(self)
        p6l.addWidget(NavigationToolbar(self.c6, self));
        p6l.addWidget(self.c6);
        l6.addLayout(p6l, 5)
        p6r = QVBoxLayout();
        self.trisi = QComboBox();
        self.vrisi = QComboBox();
        self.vrisi.addItems(['x', 'y', 'z']);
        self.tisi = QLineEdit("auto");
        self.bisi = QPushButton("Анализ");
        self.set_button_role(self.bisi, "primary")
        self.bisi.clicked.connect(self.build_isi_analysis)
        for w in [QLabel("Траектория:"), self.trisi, QLabel("Переменная:"), self.vrisi, QLabel("Порог:"), self.tisi,
                  self.bisi]: p6r.addWidget(w)
        self.lw6 = QListWidget();
        self.lw6.setAlternatingRowColors(True)
        self.lw6.setContextMenuPolicy(Qt.CustomContextMenu);
        self.lw6.customContextMenuRequested.connect(self.show_isi_context_menu)
        p6r.addWidget(self.lw6);
        bc6 = QPushButton("Очистить");
        self.set_button_role(bc6, "danger")
        bc6.clicked.connect(self.clear_isi_all);
        p6r.addWidget(bc6);
        l6.addLayout(p6r, 1);
        self.tabs.addTab(t6, "Анализ ISI")

        # 7. Bifurcations
        t7 = QWidget();
        l7 = QVBoxLayout(t7);
        bctrl = QHBoxLayout()
        self.bprm = QComboBox();
        self.bprm.addItems(['x_eq', 'A']);
        self.bmin = QLineEdit("-2.0");
        self.bmax = QLineEdit("2.0");
        self.bstp = QLineEdit("200");
        self.bcont = QCheckBox("Слежение");
        self.bcont.setChecked(True)
        self.btr = QLineEdit("20000");
        self.bme = QLineEdit("10000");
        self.bbld = QPushButton("Построить");
        self.set_button_role(self.bbld, "primary")
        self.bccl = QPushButton("Отмена");
        self.set_button_role(self.bccl, "danger")
        self.bccl.setEnabled(False)
        self.bbld.clicked.connect(self.start_bifurcation_build);
        self.bccl.clicked.connect(self.cancel_bifurcation_build)
        for w in [QLabel("Пар-р:"), self.bprm, self.bmin, self.bmax, self.bstp, self.bcont, QLabel("T_trans:"),
                  self.btr, QLabel("T_meas:"), self.bme, self.bbld, self.bccl]: bctrl.addWidget(w)
        l7.addLayout(bctrl);
        self.bprog = QProgressBar();
        self.bprog.setValue(0);
        l7.addWidget(self.bprog)
        bv = QHBoxLayout();
        bl = QVBoxLayout();
        self.c7 = MplCanvasBifurcation(self);
        self.c7.double_click_signal.connect(self.on_bifurcation_double_click)  # <-- Добавьте эту строку
        bl.addWidget(NavigationToolbar(self.c7, self));
        bl.addWidget(self.c7);
        bv.addLayout(bl, 5)
        br = QVBoxLayout();
        self.lw7 = QListWidget();
        self.lw7.setAlternatingRowColors(True)
        self.lw7.setContextMenuPolicy(Qt.CustomContextMenu);
        self.lw7.customContextMenuRequested.connect(self.show_bif_context_menu)
        bex = QPushButton("Экспорт CSV");
        self.set_button_role(bex, "secondary")
        bex.clicked.connect(self.export_bif_csv);
        bcl = QPushButton("Очистить");
        self.set_button_role(bcl, "danger")
        bcl.clicked.connect(self.clear_bif_all)
        br.addWidget(self.lw7);
        br.addWidget(bex);
        br.addWidget(bcl);
        bv.addLayout(br, 1);
        l7.addLayout(bv);
        self.tabs.addTab(t7, "Бифуркации ISI")
        # 8. Ветви равновесий (Универсальные)
        t8 = QWidget()
        l8 = QVBoxLayout(t8)
        eb_ctrl = QHBoxLayout()

        self.eb_prm = QComboBox()
        self.eb_prm.addItems(['x_eq', 'A', 'k', 'b', 'mu', 'ep'])

        self.eb_var = QComboBox()
        self.eb_var.addItems(['x', 'y', 'z'])

        self.eb_min = QLineEdit("1.0")
        self.eb_max = QLineEdit("5.0")
        self.eb_res = QLineEdit("2000")

        self.eb_bld = QPushButton("Построить")
        self.set_button_role(self.eb_bld, "primary")
        self.eb_bld.clicked.connect(self.start_equilibria_branches)

        self.eb_ccl = QPushButton("Отмена")
        self.set_button_role(self.eb_ccl, "danger")
        self.eb_ccl.setEnabled(False)
        self.eb_ccl.clicked.connect(self.cancel_equilibria_branches)

        for w in [QLabel("Ось X (пар):"), self.eb_prm, QLabel("Ось Y (пер):"), self.eb_var,
                  QLabel("Min:"), self.eb_min, QLabel("Max:"), self.eb_max,
                  QLabel("Точек:"), self.eb_res, self.eb_bld, self.eb_ccl]:
            eb_ctrl.addWidget(w)
        eb_ctrl.addStretch()

        l8.addLayout(eb_ctrl)

        self.eb_prog = QProgressBar()
        self.eb_prog.setValue(0)
        l8.addWidget(self.eb_prog)

        self.c8 = MplCanvasEquilibriaBranches(self)
        l8.addWidget(NavigationToolbar(self.c8, self))
        l8.addWidget(self.c8)

        self.tabs.addTab(t8, "Ветви равновесий")

        # 9. Ансамбль (Space-Time)
        t9 = QWidget()
        l9 = QVBoxLayout(t9)
        self.c9 = MplCanvasNetwork(self)
        l9.addWidget(NavigationToolbar(self.c9, self))
        l9.addWidget(self.c9)
        self.tabs.addTab(t9, "Ансамбль (Space-Time)")
        # 10. Бифуркации x_max (Рис. 8)
        t10 = QWidget()
        l10 = QVBoxLayout(t10)
        xm_ctrl = QHBoxLayout()
        self.xm_prm = QComboBox(); self.xm_prm.addItems(['x_eq', 'A'])
        self.xm_min = QLineEdit("0.740")
        self.xm_max = QLineEdit("0.780")
        self.xm_stp = QLineEdit("600")
        self.xm_cont = QCheckBox("Слежение"); self.xm_cont.setChecked(True)
        self.xm_tr = QLineEdit("10000")
        self.xm_me = QLineEdit("20000")
        self.xm_bld = QPushButton("Построить"); self.set_button_role(self.xm_bld, "primary")
        self.xm_ccl = QPushButton("Отмена"); self.set_button_role(self.xm_ccl, "danger"); self.xm_ccl.setEnabled(False)
        self.xm_bld.clicked.connect(self.start_xmax_bifurcation)
        self.xm_ccl.clicked.connect(self.cancel_xmax_bifurcation)

        for w in [QLabel("Пар-р:"), self.xm_prm, self.xm_min, self.xm_max, QLabel("Точек:"), self.xm_stp,
                  self.xm_cont, QLabel("T_trans:"), self.xm_tr, QLabel("T_meas:"), self.xm_me,
                  self.xm_bld, self.xm_ccl]:
            xm_ctrl.addWidget(w)
        l10.addLayout(xm_ctrl)
        self.xm_prog = QProgressBar(); self.xm_prog.setValue(0); l10.addWidget(self.xm_prog)
        self.c10 = MplCanvasXmaxBifurcation(self)
        l10.addWidget(NavigationToolbar(self.c10, self))
        l10.addWidget(self.c10)
        self.tabs.addTab(t10, "Бифуркации x_max")

        ml.addWidget(self.tabs)

    def update_network_ui(self):
        if not self.cb_net_mode.isChecked():
            self.net_table_grp.hide()
            return
        try:
            N = int(self.iN.text())
        except ValueError:
            return

        if 1 <= N <= 10:
            self.net_table_grp.show()
            current_rows = self.net_table.rowCount()
            self.net_table.setRowCount(N)

            if N > current_rows:
                A, xeq = self.iA.text(), self.ix.text()
                k, b, _, _ = self.get_sys_params()
                spos = [v.strip() for v in self.istart.text().split(',')]
                if len(spos) != 3: spos = ["0.0", "0.0", "0.0"]

                for i in range(current_rows, N):
                    self.net_table.setItem(i, 0, QTableWidgetItem(xeq))
                    self.net_table.setItem(i, 1, QTableWidgetItem(A))
                    self.net_table.setItem(i, 2, QTableWidgetItem(str(b)))
                    self.net_table.setItem(i, 3, QTableWidgetItem(spos[0]))
                    self.net_table.setItem(i, 4, QTableWidgetItem(spos[1]))
                    self.net_table.setItem(i, 5, QTableWidgetItem(spos[2]))
        else:
            self.net_table_grp.hide()

    def randomize_net_params(self):
        try:
            A_b, xeq_b = float(self.iA.text()), float(self.ix.text())
            _, b_b, _, _ = self.get_sys_params()
            delta = float(self.i_hetero.text())
            target = self.c_het_param.currentText()
            for i in range(self.net_table.rowCount()):
                self.net_table.setItem(i, 0, QTableWidgetItem(
                    f"{xeq_b + (np.random.uniform(-delta, delta) if target == 'x_eq' else 0):.4f}"))
                self.net_table.setItem(i, 1, QTableWidgetItem(
                    f"{A_b + (np.random.uniform(-delta, delta) if target == 'A' else 0):.4f}"))
                self.net_table.setItem(i, 2, QTableWidgetItem(
                    f"{b_b + (np.random.uniform(-delta, delta) if target == 'b' else 0):.4f}"))
        except:
            pass

    def randomize_net_ics(self):
        try:
            spos = [float(v.strip()) for v in self.istart.text().split(',')]
            if len(spos) != 3: spos = [0.0, 0.0, 0.0]
            for i in range(self.net_table.rowCount()):
                self.net_table.setItem(i, 3, QTableWidgetItem(f"{spos[0] + np.random.normal(0, 0.01):.4f}"))
                self.net_table.setItem(i, 4, QTableWidgetItem(f"{spos[1] + np.random.normal(0, 0.01):.4f}"))
                self.net_table.setItem(i, 5, QTableWidgetItem(f"{spos[2] + np.random.normal(0, 0.01):.4f}"))
        except:
            pass

    def toggle_noise_inputs(self, checked):
        self.iD.setEnabled(checked)
        self.itau.setEnabled(checked)

    def get_sys_params(self):
        values = tuple(float(w.text()) for w in (self.ik, self.ib, self.imu, self.iep))
        if not np.all(np.isfinite(values)):
            raise ValueError("Параметры k, b, mu и epsilon должны быть конечными числами.")
        k, b, mu, ep = values
        if abs(k) < 1e-12:
            raise ValueError("Параметр k не должен быть равен нулю: расчёт равновесий использует деление на k.")
        if mu <= 0.0 or ep <= 0.0:
            raise ValueError("Параметры mu и epsilon должны быть положительными.")
        return values

    def update_trajectory_dropdowns(self):
        self.tr1d.clear();
        self.tr2d.clear();
        self.trisi.clear()
        for t in self.trajectories.keys(): self.tr1d.addItem(t); self.tr2d.addItem(t); self.trisi.addItem(t)

    def start_lyapunov_calc(self):
        try:
            A, xeq = float(self.iA.text()), float(self.ix.text())
            k, b, mu, ep = self.get_sys_params()
            spos = [float(v.strip()) for v in self.istart.text().split(',')]
            dt = float(self.idt.text())
        except:
            return QMessageBox.critical(self, "Ошибка", "Проверьте введенные параметры.")

        self.blyap.setEnabled(False)
        self.blyap_cancel.setEnabled(True)
        self.set_status("Вычисляем спектр Ляпунова...", "accent")

        self.lyap_worker = LyapunovWorker(A, xeq, k, b, mu, ep, spos, dt)
        self.lyap_worker.finished_signal.connect(self.on_lyapunov_finished)
        self.lyap_worker.error_signal.connect(self.on_lyapunov_error)
        self.lyap_worker.start()

    def cancel_lyapunov_calc(self):
        if hasattr(self, "lyap_worker") and self.lyap_worker.isRunning():
            self.lyap_worker.cancel()
            self.blyap_cancel.setEnabled(False)
            self.set_status("Останавливаем расчёт Ляпунова...", "warning")

    def on_lyapunov_finished(self, le, cancelled=False):
        self.blyap.setEnabled(True)
        self.blyap_cancel.setEnabled(False)
        if cancelled:
            self.set_status("Расчёт Ляпунова отменён.", "warning")
            return
        self.set_status("Спектр Ляпунова вычислен.", "ready")

        # Сортируем по убыванию (L1 >= L2 >= L3)
        le_sorted = np.sort(le)[::-1]

        # Формируем вердикт
        if le_sorted[0] > 1e-4:
            verdict = "ДЕТЕРМИНИРОВАННЫЙ ХАОС (Странный аттрактор)"
        elif abs(le_sorted[0]) <= 1e-4 and le_sorted[1] < -1e-4:
            verdict = "ПРЕДЕЛЬНЫЙ ЦИКЛ (Регулярные осцилляции)"
        elif abs(le_sorted[0]) <= 1e-4 and abs(le_sorted[1]) <= 1e-4:
            verdict = "КВАЗИПЕРИОДИЧНОСТЬ (Инвариантный тор)"
        else:
            verdict = "СТАЦИОНАРНАЯ ТОЧКА (Покой)"

        msg = f"Спектр Ляпунова (L1, L2, L3):\n\n"
        msg += f"λ₁ = {le_sorted[0]:.6f}\n"
        msg += f"λ₂ = {le_sorted[1]:.6f}\n"
        msg += f"λ₃ = {le_sorted[2]:.6f}\n\n"
        msg += f"Размерность Каплана-Йорка: "

        if le_sorted[0] > 0 and le_sorted[0] + le_sorted[1] + le_sorted[2] < 0:
            if le_sorted[0] + le_sorted[1] > 0:
                dky = 2 + (le_sorted[0] + le_sorted[1]) / abs(le_sorted[2])
            else:
                dky = 1 + le_sorted[0] / abs(le_sorted[1])
            msg += f"{dky:.4f}\n\n"
        else:
            msg += "N/A\n\n"

        msg += f"Вердикт: {verdict}"

        QMessageBox.information(self, "Результаты", msg)

    def on_lyapunov_error(self, err):
        self.blyap.setEnabled(True)
        self.blyap_cancel.setEnabled(False)
        self.set_status("Ошибка при вычислении Ляпунова.", "error")
        QMessageBox.critical(self, "Ошибка", f"Сбой:\n{err}")

    def build_poincare_1d(self):
        if not self.tr1d.currentText() or self.tr1d.currentText() not in self.trajectories: return QMessageBox.warning(
            self, "!", "Выберите траекторию")
        d = self.trajectories[self.tr1d.currentText()];
        tst = float(self.idraw.text()) if self.idraw.text() else 0
        m = d['t'] >= tst if len(d['t']) > 0 else np.ones_like(d['t'], dtype=bool)
        self.c4.plot_1d_map(d['t'][m], d[self.vr1d.currentText()][m], self.tr1d.currentText().split('\n')[0])

    def build_poincare_2d(self):
        if not self.tr2d.currentText() or self.tr2d.currentText() not in self.trajectories: return QMessageBox.warning(
            self, "!", "Выберите траекторию")
        try:
            c = float(self.c2d.text())
        except:
            return QMessageBox.warning(self, "!", "Некорректное C")
        d = self.trajectories[self.tr2d.currentText()];
        tst = float(self.idraw.text()) if self.idraw.text() else 0
        m = d['t'] >= tst if len(d['t']) > 0 else np.ones_like(d['t'], dtype=bool)
        self.c5.plot_2d_section(d['x'][m], d['y'][m], d['z'][m], self.pl2d.currentText(), c, self.d2d.currentText()[0],
                                self.tr2d.currentText().split('\n')[0])

    def build_isi_analysis(self):
        if not self.trisi.currentText() or self.trisi.currentText() not in self.trajectories: return QMessageBox.warning(
            self, "!", "Выберите траекторию")
        try:
            d = self.trajectories[self.trisi.currentText()]
            tst = float(self.idraw.text()) if self.idraw.text() else 0.0
            t_all = np.asarray(d['t'], dtype=np.float64)
            v_all = np.asarray(d[self.vrisi.currentText()], dtype=np.float64)
        except (KeyError, TypeError, ValueError):
            return QMessageBox.warning(self, "!", "В траектории нет корректных данных для ISI")

        n = min(t_all.size, v_all.size)
        if n < 3:
            return QMessageBox.warning(self, "!", "Недостаточно точек в траектории")

        t_all, v_all = t_all[:n], v_all[:n]
        mask = (t_all >= tst) & np.isfinite(t_all) & np.isfinite(v_all)
        td, vd = t_all[mask], v_all[mask]
        if td.size < 3:
            return QMessageBox.warning(self, "!", "После выбранного t осталось слишком мало точек")

        try:
            threshold_text = self.tisi.text().strip().lower()
            th = float(np.mean(vd)) if threshold_text in ("", "auto") else float(threshold_text)
        except ValueError:
            return QMessageBox.warning(self, "!", "Порог должен быть числом или auto")

        if not np.isfinite(th):
            return QMessageBox.warning(self, "!", "Не удалось определить корректный порог")

        peak_mask = (vd[1:-1] > vd[:-2]) & (vd[1:-1] > vd[2:]) & (vd[1:-1] > th)
        peak_times = td[1:-1][peak_mask]
        isi = clean_isi_values(np.diff(peak_times))

        if isi.size < 2:
            return QMessageBox.warning(self, "!", "Мало спайков. Попробуйте уменьшить порог или время t начала рисунка.")

        mean = float(np.mean(isi))
        cv = float(np.std(isi) / mean) if mean > 0 else 0.0
        iid = f"{self.trisi.currentText().split()[0]} | {self.vrisi.currentText()} | {np.random.randint(100, 999)}"
        self.isi_results[iid] = {'isi': isi, 'mean': mean, 'cv': cv}
        self.lw6.addItem(QListWidgetItem(iid));
        self.c6.update_layout(self.isi_results)
        self.set_status(f"ISI построен: {isi.size} интервалов", "ready")

    def refresh_isi_view(self):
        self.c6.update_layout(self.isi_results)

    def show_isi_context_menu(self, p):
        i = self.lw6.itemAt(p)
        if i:
            m = QMenu();
            a = m.addAction("Удалить")
            if m.exec_(self.lw6.mapToGlobal(p)) == a: del self.isi_results[i.text()]; self.lw6.takeItem(
                self.lw6.row(i)); self.refresh_isi_view()

    def clear_isi_all(self):
        self.isi_results.clear();
        self.lw6.clear();
        self.refresh_isi_view()

    def start_bifurcation_build(self):
        try:
            pt, pm, pM, ps = self.bprm.currentText(), float(self.bmin.text()), float(self.bmax.text()), int(
                self.bstp.text())
            fv = float(self.iA.text()) if pt == 'x_eq' else float(self.ix.text())
            sp = [float(v.strip()) for v in self.istart.text().split(',')]
            tr, me, dt = float(self.btr.text()), float(self.bme.text()), float(self.idt.text())
            k, b, mu, ep = self.get_sys_params()
        except:
            return QMessageBox.critical(self, "Ошибка", "Проверьте параметры.")

        if ps < 2:
            return QMessageBox.warning(self, "Ошибка", "N должно быть не меньше 2.")
        if dt <= 0 or tr < 0 or me <= 0:
            return QMessageBox.warning(self, "Ошибка", "Проверьте dt, T_trans и T_meas.")
        if len(sp) != 3 or not np.all(np.isfinite(sp)):
            return QMessageBox.warning(self, "Ошибка", "Старт должен содержать три конечных числа.")

        self.bbld.setEnabled(False);
        self.bccl.setEnabled(True);
        self.bprog.setValue(0)
        self.set_status("Строим бифуркационный ISI...", "working")
        self.bif_worker = ISIBifurcationWorker(pt, pm, pM, ps, fv, k, b, mu, ep, sp, tr, me, dt, 'auto',
                                               self.bcont.isChecked())
        self.bif_worker.progress_signal.connect(self.bprog.setValue);
        self.bif_worker.finished_signal.connect(self.on_bifurcation_finished);
        self.bif_worker.error_signal.connect(self.on_bifurcation_error);
        self.bif_worker.start()

    def cancel_bifurcation_build(self):
        if self.bif_worker and self.bif_worker.isRunning(): self.bif_worker.cancel(); self.bbld.setEnabled(
            True); self.bccl.setEnabled(False)

    def on_bifurcation_finished(self, pv, iv, pn, pm, pM, uc, fv):
        bid = f"{pn} ({pm}->{pM}) [{'Cont' if uc else 'Rst'}] #{np.random.randint(100, 999)}"
        pv, iv = clean_xy_values(pv, iv, positive_y=True)
        if iv.size == 0:
            self.bbld.setEnabled(True);
            self.bccl.setEnabled(False)
            self.set_status("Бифуркационный ISI не дал положительных интервалов.", "warning")
            return QMessageBox.warning(self, "Нет данных",
                                       "Положительные ISI не найдены. Попробуйте изменить порог, время измерения или начальные условия.")

        self.bifurcation_results[bid] = {'p_vals': pv, 'isi_vals': iv, 'param_name': pn, 'fixed_val': fv}
        self.lw7.addItem(QListWidgetItem(bid));
        self.c7.update_layout(self.bifurcation_results)
        self.bbld.setEnabled(True);
        self.bccl.setEnabled(False)
        self.set_status(f"Бифуркационный ISI построен: {iv.size} точек", "ready")

    def on_bifurcation_double_click(self, param_name, param_val, fixed_val):
        if param_name == 'x_eq':
            self.ix.setText(f"{param_val:.4f}")
            self.iA.setText(f"{fixed_val:.4f}")
        elif param_name == 'A':
            self.iA.setText(f"{param_val:.4f}")
            self.ix.setText(f"{fixed_val:.4f}")

        self.set_status(f"Скопировано из бифуркации: {param_name}={param_val:.4f}", "ready")
        self.update_equilibria()

    def on_bifurcation_error(self, e):
        QMessageBox.warning(self, "Ошибка", e);
        self.bbld.setEnabled(True);
        self.bccl.setEnabled(False)
        self.set_status("Ошибка при построении бифуркационного ISI.", "error")

    def show_bif_context_menu(self, p):
        i = self.lw7.itemAt(p)
        if i:
            m = QMenu();
            a = m.addAction("Удалить")
            if m.exec_(self.lw7.mapToGlobal(p)) == a: del self.bifurcation_results[i.text()]; self.lw7.takeItem(
                self.lw7.row(i)); self.c7.update_layout(self.bifurcation_results)

    def clear_bif_all(self):
        self.bifurcation_results.clear();
        self.lw7.clear();
        self.c7.update_layout(self.bifurcation_results)

    def export_bif_csv(self):
        if not self.bifurcation_results: return QMessageBox.warning(self, "Ошибка", "Нет данных.")
        f, _ = QFileDialog.getSaveFileName(self, "Сохранить", "bifurcations.csv", "CSV Files (*.csv)")
        if f:
            with open(f, 'w') as fh:
                fh.write("ID,Param,ParamVal,ISI\n")
                for key, d in self.bifurcation_results.items():
                    for p, i in zip(d['p_vals'], d['isi_vals']): fh.write(f"{key},{d['param_name']},{p},{i}\n")
            QMessageBox.information(self, "Успех", "Сохранено.")

    def refresh_view(self):
        print("\n[ФЛАГ 1] refresh_view: Вызов обновления графиков...")
        try:
            k, b, mu, ep = self.get_sys_params()
            self.c1.update_layout(self.trajectories, self.current_eqs, float(self.iA.text()), float(self.ix.text()),
                                  k, b, mu, ep, [float(v.strip()) for v in self.istart.text().split(',')],
                                  float(self.idraw.text()) if self.idraw.text() else 0, max(1, int(self.istep.text())),
                                  self.cproj.currentText(), self.ctvar.currentText(), self.cbf.isChecked(),
                                  self.cbn.isChecked(), self.cbmanif.isChecked(), self.cbsep.isChecked(),
                                  self.cbfs.isChecked())  # <-- Передача состояния
            print("[ФЛАГ 2] refresh_view: Успешное завершение")
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА В refresh_view]: {e}")
            import traceback
            traceback.print_exc()

    def update_equilibria(self):
        try:
            k, b, mu, ep = self.get_sys_params()
            self.current_eqs = find_equilibria_with_types(float(self.iA.text()), float(self.ix.text()), k, b, mu, ep);
            self.refresh_view()
            self.tabeq.setRowCount(len(self.current_eqs))
            for i, pt in enumerate(self.current_eqs):
                x, y, z, zone, eqt, evs = pt
                self.tabeq.setItem(i, 0, QTableWidgetItem(f"СР {i + 1}"));
                self.tabeq.setItem(i, 1, QTableWidgetItem(f"{x:.4f}"));
                self.tabeq.setItem(i, 2, QTableWidgetItem(f"{y:.4f}"));
                self.tabeq.setItem(i, 3, QTableWidgetItem(f"{z:.4f}"));
                self.tabeq.setItem(i, 4, QTableWidgetItem("Линейная" if zone == "Lin" else "Насыщение"))

                def format_ev(ev):
                    if abs(ev.imag) > 1e-10: return f"{ev.real:+.5e}{ev.imag:+.5e}j"
                    return f"{ev.real:+.5e}"

                self.tabeq.setItem(i, 5, QTableWidgetItem(", ".join([format_ev(ev) for ev in evs])))
                ti = QTableWidgetItem(eqt);
                ti.setForeground(
                    Qt.darkGreen if "Уст." in eqt or eqt == "УУ" else Qt.red if "Неуст." in eqt or eqt == "НУ" else Qt.blue);
                self.tabeq.setItem(i, 6, ti)
        except:
            pass

    def on_table_double_click(self, item):
        row = item.row()
        if row >= len(self.current_eqs): return
        try:
            A = float(self.iA.text());
            k, b, mu, ep = self.get_sys_params()
        except:
            return
        x, y, z, zone = self.current_eqs[row][:4];
        vals, vecs = np.linalg.eig(get_jacobian(x, y, zone, A, k, mu, ep))
        menu, p0 = QMenu(self), np.array([x, y, z]);
        act_sh = menu.addAction("Сдвиг произвольно");
        acts = {act_sh: p0 + 1e-3};
        menu.addSeparator()
        for i, ev in enumerate(vals):
            if abs(np.real(ev)) > 1e-10:
                v = np.real(vecs[:, i]) / np.linalg.norm(np.real(vecs[:, i]))
                pr = "Неустойчивое" if np.real(ev) > 0 else "Устойчивое"
                acts[menu.addAction(f"{pr} (+)")], acts[menu.addAction(f"{pr} (-)")] = p0 + 1e-3 * v, p0 - 1e-3 * v
        a = menu.exec_(QCursor.pos())
        if a: self.istart.setText(f"{acts[a][0]:.4f}, {acts[a][1]:.4f}, {acts[a][2]:.4f}"); self.tabs.setCurrentIndex(
            0); self.start_calculation()

    def start_calculation(self):
        try:
            A, xeq = float(self.iA.text()), float(self.ix.text())
            dt, rtol, atol, tend = float(self.idt.text()), float(self.irtol.text()), float(self.iatol.text()), float(
                self.itend.text())
            meth = self.cmeth.currentText()
            k, b, mu, ep = self.get_sys_params()
            if not np.all(np.isfinite((A, xeq, dt, rtol, atol, tend))):
                raise ValueError("Все параметры должны быть конечными числами.")
            if dt <= 0.0 or tend <= 0.0 or dt > tend:
                raise ValueError("Требуется 0 < dt <= время расчёта.")
            estimated_steps = tend / dt
            if not np.isfinite(estimated_steps) or estimated_steps > 100_000_000:
                raise ValueError("Слишком много шагов интегрирования (более 100 млн). Увеличьте dt или уменьшите время расчёта.")
            if rtol <= 0.0 or atol <= 0.0:
                raise ValueError("rtol и atol должны быть положительными.")

            is_backward = self.cb_rev_time.isChecked()
            use_noise = self.cb_noise.isChecked()
            D_val = float(self.iD.text())
            tau_val = float(self.itau.text())
            if not np.isfinite(D_val) or D_val < 0.0:
                raise ValueError("Интенсивность шума D должна быть неотрицательной.")
            if not np.isfinite(tau_val) or tau_val <= 0.0:
                raise ValueError("Время корреляции tau должно быть положительным.")

            is_network = hasattr(self, 'cb_net_mode') and self.cb_net_mode.isChecked()

        except (ValueError, OverflowError) as exc:
            return QMessageBox.critical(self, "Ошибка параметров", str(exc) or "Проверьте введенные числовые параметры.")

        self.update_equilibria()
        self.brun.setEnabled(False)
        self.bcanc.setEnabled(True)

        if is_network:
            try:
                N = int(self.iN.text())
                g_el, g_syn = float(self.ig_el.text()), float(self.ig_syn.text())
                hetero = float(self.i_hetero.text())
                topo, param_het = self.c_topo.currentText(), self.c_het_param.currentText()
                if not 1 <= N <= 200:
                    raise ValueError("Число нейронов N должно быть от 1 до 200.")
                if not np.all(np.isfinite((g_el, g_syn, hetero))) or min(g_el, g_syn, hetero) < 0:
                    raise ValueError("Связи и неоднородность должны быть конечными и неотрицательными.")
                sample_rate = max(1, int(0.2 / dt))
                output_rows = int(estimated_steps) // sample_rate + 2
                # Учитываем массив времени, состояния всех нейронов и запас на
                # временные массивы NumPy/Numba и последующую обработку результатов.
                estimated_memory = int(output_rows * (3 * N + 1) * 8 * 2.5)
                available_memory = get_available_memory_bytes()
                # Не занимаем всю свободную RAM: оставляем ОС и другим программам
                # не менее 1 ГБ либо 25% доступной памяти (что больше).
                reserve_memory = max(1 * 1024 ** 3, int(available_memory * 0.25))
                memory_budget = max(0, available_memory - reserve_memory)
                if estimated_memory > memory_budget:
                    need_mb = estimated_memory / (1024 ** 2)
                    budget_mb = memory_budget / (1024 ** 2)
                    available_mb = available_memory / (1024 ** 2)
                    raise ValueError(
                        f"Для расчёта ансамбля ориентировочно потребуется {need_mb:.0f} МБ "
                        f"с учётом запаса. Сейчас доступно {available_mb:.0f} МБ, "
                        f"безопасный лимит расчёта — {budget_mb:.0f} МБ. "
                        "Освободите память, уменьшите время расчёта или увеличьте dt."
                    )
            except (ValueError, OverflowError) as exc:
                self.brun.setEnabled(True)
                self.bcanc.setEnabled(False)
                return QMessageBox.critical(self, "Ошибка", str(exc) or "Ошибки в параметрах сети.")

            self.set_status(f"Считаем сеть из {N} нейронов...", "working")
            A_el = generate_topology(N, topo_type=topo, directed=False)
            A_syn = generate_topology(N, topo_type=topo, directed=False)

            if N <= 10 and not self.net_table_grp.isHidden():
                x_eq_arr, A_arr, b_arr = np.zeros(N), np.zeros(N), np.zeros(N)
                start_pos = np.zeros(3 * N)

                for i in range(N):
                    try:
                        x_eq_arr[i] = float(self.net_table.item(i, 0).text())
                        A_arr[i] = float(self.net_table.item(i, 1).text())
                        b_arr[i] = float(self.net_table.item(i, 2).text())
                        start_pos[i] = float(self.net_table.item(i, 3).text())
                        start_pos[N + i] = float(self.net_table.item(i, 4).text())
                        start_pos[2 * N + i] = float(self.net_table.item(i, 5).text())
                        if not np.all(np.isfinite((x_eq_arr[i], A_arr[i], b_arr[i], start_pos[i],
                                                   start_pos[N + i], start_pos[2 * N + i]))):
                            raise ValueError("Параметры должны быть конечными числами.")
                    except Exception:
                        self.brun.setEnabled(True)
                        self.bcanc.setEnabled(False)
                        return QMessageBox.critical(self, "Ошибка", f"Некорректный ввод в строке {i + 1} таблицы.")
            else:
                x_eq_arr = np.full(N, xeq)
                A_arr = np.full(N, A)
                b_arr = np.full(N, b)
                if param_het == 'x_eq':
                    x_eq_arr += np.random.uniform(-hetero, hetero, N)
                elif param_het == 'A':
                    A_arr += np.random.uniform(-hetero, hetero, N)
                elif param_het == 'b':
                    b_arr += np.random.uniform(-hetero, hetero, N)

                start_pos = np.zeros(3 * N, dtype=np.float64)
                start_pos[0:N] = np.random.uniform(-1.5, 2.5, N)
                start_pos[N:2 * N] = np.random.uniform(0.5, 2.0, N)
                start_pos[2 * N:3 * N] = np.random.uniform(0.2, 1.0, N)

            V_rev_val = 8.0
            theta_syn_val = 2.5
            lambda_syn_val = 8.0

            tid = f"Net N={N} {topo} | gel={g_el}, gsyn={g_syn}"
            self.network_worker = NetworkSolverWorker(
                tid, N, A_arr, x_eq_arr, k, b_arr, mu, ep,
                g_el, A_el, g_syn, A_syn, V_rev_val, theta_syn_val, lambda_syn_val, start_pos, dt, tend
            )
            self.network_worker.finished_signal.connect(
                lambda tid, t, s_out, st, n=N: self.on_network_finished(tid, t, s_out, st, n)
            )
            self.network_worker.error_signal.connect(self.on_calculation_error)
            self.network_worker.start()

        else:
            # ---БЛОК РАСЧЕТА ОДИНОЧНОГО НЕЙРОНА ---
            try:
                spos = [float(v.strip()) for v in self.istart.text().split(',')]
                if len(spos) != 3 or not np.all(np.isfinite(spos)):
                    raise ValueError("Начальное состояние должно содержать три конечных числа.")
            except (ValueError, OverflowError) as exc:
                self.brun.setEnabled(True)
                self.bcanc.setEnabled(False)
                return QMessageBox.critical(self, "Ошибка начального состояния", str(exc))
            dir_str = "назад" if is_backward else "вперед"
            noise_str = "с шумом" if use_noise else "детерминированно"
            self.set_status(f"Считаем {dir_str} {noise_str}...", "working")

            tid_base = f"A={A}, xeq={xeq} | {'SDE' if use_noise else meth}"
            tid = f"{tid_base} {'(Rev)' if is_backward else ''}"

            self.solver_worker = SolverWorker(tid, A, xeq, k, b, mu, ep, spos, meth, rtol, atol,
                                              dt, tend, is_backward, use_noise, D_val, tau_val)
            self.solver_worker.finished_signal.connect(self.on_calculation_finished)
            self.solver_worker.error_signal.connect(self.on_calculation_error)
            self.solver_worker.start()

    def cancel_calculation(self):
        if self.solver_worker and self.solver_worker.isRunning():
            self.solver_worker.cancel()
            self.set_status("Отменяем расчет нейрона...", "warning")

        if self.network_worker and self.network_worker.isRunning():
            self.network_worker.cancel()
            self.set_status("Отменяем расчет ансамбля...", "warning")

        # Кнопки будут восстановлены обработчиком завершения/отмены потока.

    def on_calculation_finished(self, tid, t, x, y, z, st):
        uid = f"{tid} #{np.random.randint(100, 999)}"
        self.trajectories[uid] = {'t': t, 'x': x, 'y': y, 'z': z}
        self.lw1.addItem(QListWidgetItem(uid))
        self.update_trajectory_dropdowns()
        self.refresh_view()

        self.tabs.setCurrentIndex(0)

        self.brun.setEnabled(True)
        self.bcanc.setEnabled(False)
        if "Прервано" in st:
            self.set_status(st, "error")
        else:
            self.set_status("Готов.", "ready")

    def on_calculation_error(self, e):
        message = str(e)
        self.brun.setEnabled(True)
        self.bcanc.setEnabled(False)
        cancelled = "Остановлено" in message
        self.set_status(message, "warning" if cancelled else "error")
        if not cancelled:
            QMessageBox.critical(self, "Ошибка расчёта", message)

    def show_context_menu(self, p):
        i = self.lw1.itemAt(p)
        if i:
            m = QMenu();
            a = m.addAction("Удалить")
            if m.exec_(self.lw1.mapToGlobal(p)) == a: del self.trajectories[i.text()]; self.lw1.takeItem(
                self.lw1.row(i)); self.update_trajectory_dropdowns(); self.refresh_view()

    def clear_all(self):
        self.trajectories.clear();
        self.lw1.clear();
        self.update_trajectory_dropdowns();
        self.refresh_view()

    def export_custom_figure(self):
        if not self.trajectories:
            return QMessageBox.warning(self, "Ошибка", "Сначала рассчитайте хотя бы одну траекторию.")
        t_draw = float(self.idraw.text()) if self.idraw.text() else 0
        t_end = float(self.itend.text()) if self.itend.text() else 200000

        dlg = ExportDialog(self, t_draw, t_end, self)
        dlg.exec_()
    def on_map_double_click(self, x, a):
        self.iA.setText(f"{a:.4f}");
        self.ix.setText(f"{x:.4f}");
        self.set_status(f"Скопировано: x_eq={x:.3f}, A={a:.3f}", "ready")
        self.update_equilibria();
        self.tabs.setCurrentIndex(0)

    def start_map_build(self):
        try:
            am, aM, xm, xM, res = float(self.mamin.text()), float(self.mamax.text()), float(self.mxmin.text()), float(
                self.mxmax.text()), int(self.mres.text())
            k, b, mu, ep = self.get_sys_params()
        except:
            return QMessageBox.critical(self, "Ошибка", "Проверьте диапазоны.")
        self.bmap.setEnabled(False);
        self.cmap.setEnabled(True);
        self.mprog.setValue(0)
        self.map_worker = MapWorker(am, aM, xm, xM, res, k, b, mu, ep);
        self.map_worker.progress_signal.connect(self.mprog.setValue);
        self.map_worker.finished_signal.connect(self.on_map_finished);
        self.map_worker.start()

    def cancel_map_build(self):
        if self.map_worker and self.map_worker.isRunning(): self.map_worker.cancel(); self.bmap.setEnabled(
            True); self.cmap.setEnabled(False); self.mprog.setValue(0)

    def on_map_finished(self, xa, aa, z, us):
        cm = plt.get_cmap('tab20', len(us)) if hasattr(plt, 'get_cmap') else plt.cm.get_cmap('tab20', len(us))
        self.c3.plot_map(xa, aa, z, cm, len(us))
        while self.llay.count() > 1:
            i = self.llay.takeAt(0)
            if i.widget(): i.widget().deleteLater()
        self.legend_items = []
        for c, s in zip([mcolors.to_hex(cm(i)) for i in range(len(us))], us):
            i = LegendItem(c, s);
            self.legend_items.append(i);
            self.llay.insertWidget(self.llay.count() - 1, i)
        self.bmap.setEnabled(True);
        self.cmap.setEnabled(False)

    def highlight_legend(self, aidx):
        for i, item in enumerate(self.legend_items): item.set_highlight(i == aidx, aidx != -1)

    def start_equilibria_branches(self):
        try:
            pt = self.eb_prm.currentText()
            vt = self.eb_var.currentText()
            p_min, p_max = float(self.eb_min.text()), float(self.eb_max.text())
            res = int(self.eb_res.text())

            k, b, mu, ep = self.get_sys_params()
            A = float(self.iA.text())
            x_eq = float(self.ix.text())

            base_params = {'A': A, 'x_eq': x_eq, 'k': k, 'b': b, 'mu': mu, 'ep': ep}

        except Exception:
            return QMessageBox.critical(self, "Ошибка", "Проверьте введенные параметры.")

        if res < 10:
            return QMessageBox.warning(self, "Ошибка", "Недостаточно точек для разрешения.")

        self.eb_bld.setEnabled(False)
        self.eb_ccl.setEnabled(True)
        self.eb_prog.setValue(0)
        self.set_status(f"Вычисление ветвей {vt} от {pt}...", "working")

        self.eb_worker = EquilibriaBranchesWorker(pt, vt, p_min, p_max, res, base_params)
        self.eb_worker.progress_signal.connect(self.eb_prog.setValue)
        self.eb_worker.finished_signal.connect(self.on_equilibria_branches_finished)
        self.eb_worker.error_signal.connect(self.on_equilibria_branches_error)
        self.eb_worker.start()

    def cancel_equilibria_branches(self):
        if hasattr(self, 'eb_worker') and self.eb_worker.isRunning():
            self.eb_worker.cancel()
            self.eb_bld.setEnabled(True)
            self.eb_ccl.setEnabled(False)
            self.set_status("Построение ветвей отменено.", "warning")

    def on_equilibria_branches_finished(self, eq_data, param_name, var_name):
        self.c8.update_layout(eq_data, param_name, var_name)
        self.eb_bld.setEnabled(True)
        self.eb_ccl.setEnabled(False)
        pts_count = sum(len(v['p']) for v in eq_data.values())
        self.set_status(f"Ветви построены. Найдено точек: {pts_count}", "ready")

    def on_equilibria_branches_error(self, err):
        self.eb_bld.setEnabled(True)
        self.eb_ccl.setEnabled(False)
        self.set_status("Ошибка при расчете ветвей.", "error")
        QMessageBox.critical(self, "Ошибка", f"Сбой:\n{err}")

    def on_network_finished(self, tid, t, s_out, st, N=None):
        if N is None:
            N = getattr(self.network_worker, "N", 0)
        if N < 1 or s_out.ndim != 2 or s_out.shape[1] != 3 * N:
            self.on_calculation_error("Получен массив результатов сети с некорректной размерностью.")
            return

        uid = f"{tid} #{np.random.randint(100, 999)}"

        self.trajectories[uid] = {'t': t, 'x': s_out[:, 0], 'y': s_out[:, N], 'z': s_out[:, 2 * N]}
        self.lw1.addItem(QListWidgetItem(uid))
        self.update_trajectory_dropdowns()
        self.refresh_view()

        self.c9.plot_space_time(t, s_out, N)

        self.tabs.setCurrentIndex(8)

        self.brun.setEnabled(True)
        self.bcanc.setEnabled(False)
        self.set_status("Сеть просчитана успешно.", "ready")

class MplCanvasXmaxBifurcation(MplCanvasBase):
    def update_layout(self, p_vals, xmax_vals, param_name, p_min, p_max):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        if len(xmax_vals) == 0:
            ax.text(0.5, 0.5, "Нет данных", ha='center')
            self.draw()
            return

        ax.scatter(p_vals, xmax_vals, s=0.3, color='black', alpha=0.5, edgecolors='none')
        ax.set_xlim(p_min, p_max)
        ax.set_xlabel("$x_{eq}$" if param_name == "x_eq" else param_name, fontsize=14, weight='bold')
        ax.set_ylabel("$x_{max}$", fontsize=14, weight='bold')
        ax.set_title("Бифуркационная диаграмма $x_{max}$ (Рис. 8)")
        ax.grid(True, alpha=0.3)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.fig.tight_layout()
        self.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    window = NeuroApp()
    window.show()
    sys.exit(app.exec_())
