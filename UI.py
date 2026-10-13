import os
import subprocess
import threading
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# Configuración del tema de CustomTkinter
ctk.set_appearance_mode("Dark")  # Opciones: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")


# --- Utilidades de Windows para pausar/ocultar la ventana de scrcpy ---
def _get_windows_for_pid(pid):
    """Devuelve los HWND visibles de las ventanas de nivel superior del PID dado."""
    if os.name != 'nt':
        return []
    user32 = ctypes.windll.user32
    hwnds = []
    EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, lparam):
        wpid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(wpid))
        if wpid.value == pid and user32.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return hwnds


def _set_window_visibility(hwnd, visible):
    """Muestra u oculta una ventana (SW_SHOW / SW_HIDE)."""
    if os.name != 'nt':
        return
    SW_HIDE = 0
    SW_SHOW = 5
    ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW if visible else SW_HIDE)


def _suspend_process(pid):
    """Suspende todos los hilos del proceso (pausa real)."""
    if os.name != 'nt':
        return
    PROCESS_ALL_ACCESS = 0x1F0FFF
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if handle:
        ctypes.windll.ntdll.NtSuspendProcess(handle)
        ctypes.windll.kernel32.CloseHandle(handle)


def _resume_process(pid):
    """Reanuda todos los hilos del proceso previamente suspendido."""
    if os.name != 'nt':
        return
    PROCESS_ALL_ACCESS = 0x1F0FFF
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if handle:
        ctypes.windll.ntdll.NtResumeProcess(handle)
        ctypes.windll.kernel32.CloseHandle(handle)


class ScrcpyProLauncher(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuración de la ventana principal
        self.title("scrcpy Pro Controller")
        self.geometry("520x680")
        self.resizable(False, False)

        # Rutas de los ejecutables locales
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.scrcpy_path = os.path.join(self.base_dir, "scrcpy.exe")
        self.adb_path = os.path.join(self.base_dir, "adb.exe")

        # Diccionario de mapeo de Resoluciones (Etiqueta -> Píxeles en lado máximo)
        self.resolution_map = {
            "Original (Pantalla completa)": "Original",
            "SD (480p)": "800",
            "HD (720p)": "1280",
            "Full HD (1080p)": "1920",
            "QHD (1440p)": "2560",
            "4K (2160p)": "3840"
        }

        # Estado del proceso scrcpy (para pausa/reanudar)
        self.scrcpy_process = None
        self.is_paused = False
        self._paused_hwnds = []

        self.create_ui()
        self.refresh_devices()

    def create_ui(self):
        # Título y Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title_label = ctk.CTkLabel(
            header_frame, 
            text="scrcpy Control Panel", 
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(side="left")

        # Pestañas de conexión (Cable USB vs Wi-Fi)
        self.tabview = ctk.CTkTabview(self, height=140)
        self.tabview.pack(fill="x", padx=20, pady=10)
        
        tab_usb = self.tabview.add("Cable USB")
        tab_wifi = self.tabview.add("Conexión Wi-Fi")

        # --- SECCIÓN USB ---
        usb_frame = ctk.CTkFrame(tab_usb, fg_color="transparent")
        usb_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(usb_frame, text="Dispositivo detectado:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w", pady=5)
        
        self.device_combo = ctk.CTkOptionMenu(usb_frame, values=["Buscando..."], width=260)
        self.device_combo.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        self.btn_refresh = ctk.CTkButton(usb_frame, text="🔄 Actualizar", width=100, command=self.refresh_devices)
        self.btn_refresh.grid(row=1, column=1)

        # --- SECCIÓN WI-FI ---
        wifi_frame = ctk.CTkFrame(tab_wifi, fg_color="transparent")
        wifi_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(wifi_frame, text="Dirección IP del Dispositivo:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(wifi_frame, text="Puerto:", font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.ip_entry = ctk.CTkEntry(wifi_frame, placeholder_text="192.168.1.50", width=220)
        self.ip_entry.grid(row=1, column=0, sticky="ew", pady=5)

        self.port_entry = ctk.CTkEntry(wifi_frame, placeholder_text="5555", width=80)
        self.port_entry.grid(row=1, column=1, padx=10, pady=5)
        self.port_entry.insert(0, "5555")

        self.btn_connect_wifi = ctk.CTkButton(wifi_frame, text="Conectar Wi-Fi", command=self.connect_wifi, width=120)
        self.btn_connect_wifi.grid(row=1, column=2, pady=5)

        # --- PARÁMETROS DE CONFIGURACIÓN ---
        config_frame = ctk.CTkFrame(self)
        config_frame.pack(fill="both", expand=True, padx=20, pady=10)

        ctk.CTkLabel(config_frame, text="Ajustes de Rendimiento y Pantalla", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(12, 8))

        grid_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        grid_frame.pack(fill="x", padx=15, pady=5)

        # 1. Resolución
        ctk.CTkLabel(grid_frame, text="Resolución máxima:").grid(row=0, column=0, sticky="w", pady=8)
        self.res_menu = ctk.CTkOptionMenu(grid_frame, values=list(self.resolution_map.keys()), width=180)
        self.res_menu.grid(row=0, column=1, sticky="e", padx=(20, 0), pady=8)
        self.res_menu.set("Original (Pantalla completa)")

        # 2. Bitrate (Calidad de vídeo)
        ctk.CTkLabel(grid_frame, text="Tasa de bits (Bitrate):").grid(row=1, column=0, sticky="w", pady=8)
        self.bitrate_menu = ctk.CTkOptionMenu(grid_frame, values=["2 M", "4 M", "8 M", "12 M", "16 M", "24 M"], width=180)
        self.bitrate_menu.grid(row=1, column=1, sticky="e", padx=(20, 0), pady=8)
        self.bitrate_menu.set("8 M")

        # 3. FPS máximos
        ctk.CTkLabel(grid_frame, text="Tasa de refresco (FPS):").grid(row=2, column=0, sticky="w", pady=8)
        self.fps_menu = ctk.CTkOptionMenu(grid_frame, values=["Sin límite", "30", "60", "90", "120"], width=180)
        self.fps_menu.grid(row=2, column=1, sticky="e", padx=(20, 0), pady=8)
        self.fps_menu.set("Sin límite")

        grid_frame.columnconfigure(0, weight=1)

        # --- OPCIONES ADICIONALES ---
        options_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=15, pady=10)

        self.sw_turn_off = ctk.CTkSwitch(options_frame, text="Apagar pantalla del móvil al conectar (-S)")
        self.sw_turn_off.pack(anchor="w", pady=5)

        self.sw_always_top = ctk.CTkSwitch(options_frame, text="Mantener ventana siempre visible (--always-on-top)")
        self.sw_always_top.pack(anchor="w", pady=5)

        self.sw_stay_awake = ctk.CTkSwitch(options_frame, text="Evitar que el móvil entre en reposo (--stay-awake)")
        self.sw_stay_awake.pack(anchor="w", pady=5)

        # --- BOTONES DE CONTROL (INICIAR + PAUSA) ---
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(10, 20))

        self.btn_launch = ctk.CTkButton(
            button_frame, 
            text="INICIAR TRANSMISIÓN", 
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#1f538d",
            hover_color="#14375e",
            command=self.launch_scrcpy
        )
        self.btn_launch.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_pause = ctk.CTkButton(
            button_frame,
            text="⏸ PAUSA",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            width=150,
            fg_color="#7a5900",
            hover_color="#5a4100",
            state="disabled",
            command=self.toggle_pause
        )
        self.btn_pause.pack(side="left", padx=(5, 0))

    # --- LÓGICA DE ADB Y SCRCPY ---

    def run_command(self, cmd):
        """Ejecuta un comando ocultando la consola en Windows."""
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        return subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)

    def refresh_devices(self):
        """Escanea dispositivos conectados mediante ADB."""
        def task():
            if not os.path.exists(self.adb_path):
                messagebox.showerror("Error", f"No se encontró adb.exe en:\n{self.adb_path}")
                return

            res = self.run_command([self.adb_path, "devices"])
            lines = res.stdout.strip().split("\n")[1:]
            devices = [line.split("\t")[0] for line in lines if "\tdevice" in line]

            if devices:
                self.device_combo.configure(values=devices)
                self.device_combo.set(devices[0])
            else:
                self.device_combo.configure(values=["Sin dispositivos conectados"])
                self.device_combo.set("Sin dispositivos conectados")

        threading.Thread(target=task, daemon=True).start()

    def connect_wifi(self):
        """Conecta un dispositivo por Wi-Fi usando la IP proporcionada."""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()

        if not ip:
            messagebox.showwarning("Atención", "Por favor ingresa la IP del dispositivo.")
            return

        def task():
            target = f"{ip}:{port}"
            res = self.run_command([self.adb_path, "connect", target])
            if "connected" in res.stdout:
                messagebox.showinfo("Éxito", f"Conectado exitosamente a {target}")
                self.refresh_devices()
            else:
                messagebox.showerror("Error de Conexión", f"No se pudo conectar a {target}.\n\nAsegúrate de tener la depuración por red activa en el teléfono.")

        threading.Thread(target=task, daemon=True).start()

    def launch_scrcpy(self):
        """Construcción y ejecución dinámica del comando final de scrcpy."""
        if not os.path.exists(self.scrcpy_path):
            messagebox.showerror("Error", f"No se encontró scrcpy.exe en:\n{self.scrcpy_path}")
            return

        device = self.device_combo.get()
        if not device or device == "Sin dispositivos conectados":
            messagebox.showwarning("Atención", "No hay ningún dispositivo seleccionado o detectado.")
            return

        # Si ya hay un proceso activo, lo cerramos antes de lanzar otro
        if self.scrcpy_process and self.scrcpy_process.poll() is None:
            try:
                if self.is_paused:
                    _resume_process(self.scrcpy_process.pid)
                self.scrcpy_process.terminate()
            except Exception:
                pass

        # Construcción básica del comando
        cmd = [self.scrcpy_path, "-s", device]

        # 1. Mapeo de Resolución
        selected_res_label = self.res_menu.get()
        res_value = self.resolution_map.get(selected_res_label, "Original")
        if res_value != "Original":
            cmd.extend(["--max-size", res_value])

        # 2. Bitrate (e.g. "8 M" -> "8M")
        bitrate = self.bitrate_menu.get().replace(" ", "")
        cmd.extend(["-b", bitrate])

        # 3. FPS
        fps = self.fps_menu.get()
        if fps != "Sin límite":
            cmd.extend(["--max-fps", fps])

        # Switches adicionales
        if self.sw_turn_off.get():
            cmd.append("-S")

        if self.sw_always_top.get():
            cmd.append("--always-on-top")

        if self.sw_stay_awake.get():
            cmd.append("--stay-awake")

        # Ejecución del proceso
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        try:
            self.scrcpy_process = subprocess.Popen(cmd, creationflags=creation_flags)
            self.is_paused = False
            self._paused_hwnds = []
            self.btn_pause.configure(
                state="normal",
                text="⏸ PAUSA",
                fg_color="#7a5900",
                hover_color="#5a4100"
            )
            # Iniciar monitor para deshabilitar la pausa si scrcpy se cierra
            self.after(1000, self._monitor_process)
        except Exception as e:
            messagebox.showerror("Error de ejecución", f"Ocurrió un problema al iniciar scrcpy:\n{e}")

    def toggle_pause(self):
        """Pausa o reanuda la ventana de scrcpy (oculta + suspende el proceso)."""
        if self.scrcpy_process is None or self.scrcpy_process.poll() is not None:
            messagebox.showinfo("Información", "No hay ninguna transmisión activa.")
            self.btn_pause.configure(state="disabled")
            return

        pid = self.scrcpy_process.pid

        if not self.is_paused:
            # --- PAUSAR: guardar HWNDs, ocultar ventanas y suspender el proceso ---
            self._paused_hwnds = _get_windows_for_pid(pid)
            for hwnd in self._paused_hwnds:
                _set_window_visibility(hwnd, False)
            _suspend_process(pid)

            self.is_paused = True
            self.btn_pause.configure(
                text="▶ REANUDAR",
                fg_color="#1f7a1f",
                hover_color="#155515"
            )
        else:
            # --- REANUDAR: reactivar proceso y volver a mostrar la ventana ---
            _resume_process(pid)

            hwnds = self._paused_hwnds or _get_windows_for_pid(pid)
            for hwnd in hwnds:
                _set_window_visibility(hwnd, True)
            self._paused_hwnds = []

            self.is_paused = False
            self.btn_pause.configure(
                text="⏸ PAUSA",
                fg_color="#7a5900",
                hover_color="#5a4100"
            )

    def _monitor_process(self):
        """Comprueba si scrcpy sigue vivo para habilitar/deshabilitar el botón de pausa."""
        if self.scrcpy_process is None:
            return
        if self.scrcpy_process.poll() is not None:
            # El proceso terminó: reiniciar estado del botón
            self.scrcpy_process = None
            self.is_paused = False
            self._paused_hwnds = []
            self.btn_pause.configure(
                state="disabled",
                text="⏸ PAUSA",
                fg_color="#7a5900",
                hover_color="#5a4100"
            )
        else:
            self.after(1000, self._monitor_process)


if __name__ == "__main__":
    app = ScrcpyProLauncher()
    app.mainloop()