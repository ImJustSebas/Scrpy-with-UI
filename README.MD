# scrcpy with Graphical User Interface (GUI)

## Descripción del Proyecto
Este proyecto proporciona una interfaz gráfica de usuario (GUI) desarrollada en Python para **scrcpy**, la herramienta de código abierto que permite reflejar y controlar dispositivos Android desde una computadora.

Por defecto, scrcpy requiere el uso de parámetros mediante la línea de comandos para ajustar configuraciones de video, rendimiento y conexión. Esta interfaz simplifica este proceso al permitir configurar la resolución, la tasa de bits (bitrate), los FPS y el modo de conexión (USB o Wi-Fi) de manera intuitiva antes de iniciar la transmisión.

---

## Características Principales
* **Selección de Resolución Preseteada:** Opciones claras como SD (480p), HD (720p), Full HD (1080p), QHD (1440p) y 4K (2160p).
* **Ajustes de Rendimiento:** Selección rápida de la tasa de bits (Bitrate) y límite de tasa de refresco (FPS).
* **Gestión de Conexión:** 
  * Detección automática de dispositivos conectados mediante cable USB.
  * Soporte para conexión inalámbrica vía Wi-Fi ingresando IP y puerto.
* **Opciones de Pantalla y Control:** Modos para apagar la pantalla del dispositivo al conectar, mantener la ventana siempre visible o evitar que el dispositivo entre en suspensión.

---

## Requisitos Previos

### En el Dispositivo Android
1. Activar las **Opciones para desarrolladores** (Ajustes > Información del teléfono > Presionar 7 veces en "Número de compilación").
2. Habilitar la **Depuración por USB** en las Opciones para desarrolladores.
3. Permitir la autorización de depuración USB en la pantalla del teléfono al conectarlo por primera vez.

### En la Computadora
* Sistema Operativo: Windows.
* Python 3.8 o superior (si se ejecuta el script fuente `UI.py`).
* Librería `customtkinter`:
  ```bash
  pip install customtkinter
Instalación y Configuración
Clonar o descargar el repositorio:

Bash
git clone [https://github.com/ImJustSebas/Scrpy-with-UI.git](https://github.com/ImJustSebas/Scrpy-with-UI.git)
Ubicación de archivos:
Asegúrese de que el archivo UI.py se encuentre en el mismo directorio que los ejecutables binarios de scrcpy (scrcpy.exe, adb.exe y las librerías .dll adjuntas).

Modo de Uso
1. Ejecución vía Cable USB
Conecte su dispositivo Android a la computadora mediante un cable USB.

Ejecute el script de la interfaz:

Bash
python UI.py
Seleccione el dispositivo detectado en el menú desplegable (presione el botón de actualizar si no aparece inmediatamente).

Configure los parámetros deseados (Resolución, Bitrate, FPS).

Presione el botón INICIAR TRANSMISIÓN.

2. Ejecución vía Wi-Fi
Asegúrese de que el dispositivo y la PC estén conectados a la misma red local.

Seleccione la pestaña Conexión Wi-Fi en la interfaz.

Ingrese la dirección IP del teléfono y el puerto correspondiente (por defecto 5555).

Haga clic en Conectar Wi-Fi.

Tras confirmarse la conexión, seleccione el dispositivo y presione INICIAR TRANSMISIÓN.

Estructura del Repositorio
UI.py: Script principal en Python que contiene la interfaz gráfica.

scrcpy.exe & adb.exe: Binarios de ejecución de scrcpy y Android Debug Bridge.

Archivos DLL (avcodec-61.dll, SDL2.dll, etc.): Librerías necesarias para el procesamiento de video y audio.

Créditos y Licencia
scrcpy es desarrollado por Genymobile y está distribuido bajo la licencia Apache 2.0.

Este proyecto actúa como una capa de interfaz (Wrapper GUI) no oficial para facilitar el acceso a sus parámetros.