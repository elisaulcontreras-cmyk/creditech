# Creditech — Sistema de Control y Bloqueo de Laptops a Crédito

**Creditech** es un sistema cliente-servidor en español diseñado para tiendas y vendedores de laptops financiadas a crédito. Permite instalar un agente en múltiples equipos, identificar cada equipo con el **Nombre y Número de Cédula del cliente**, mostrar un **aviso de pago automático 1 día antes del vencimiento de cada cuota**, y **bloquear o desbloquear el equipo** tanto automáticamente por mora como remotamente desde el servidor (o mediante PIN sin internet).

---

## Características Principales

1. **Identificación del Cliente en Cada Equipo**
   - Almacena y muestra en todo momento el **Nombre completo** y **Número de Cédula** del titular del crédito, junto con el modelo de la laptop, serial y código único de instalación (`CRD-XXXX-XXXX`).
2. **Instalación en Múltiples Laptops**
   - Puedes registrar todas las laptops que vendas desde el Panel Web del Servidor o directamente desde el instalador en cada laptop.
   - Se configura automáticamente en el inicio de Windows (`HKCU\...\Run`) para ejecutarse apenas el cliente encienda el equipo.
3. **Aviso de Pago Automático (1 Día Antes del Vencimiento)**
   - Exactamente **1 día antes de la fecha de vencimiento** de la próxima cuota (y el día de vencimiento), el programa despliega una alerta preventiva en pantalla y un banner destacado indicando el número de cuota, monto en dólares y fecha límite para evitar el bloqueo.
4. **Bloqueo Total del Equipo por Falta de Pago**
   - Si llega el día siguiente al vencimiento y la cuota sigue pendiente, o si decides bloquear el equipo desde el servidor, la laptop muestra una **pantalla de bloqueo a pantalla completa** siempre encima (`Frameless` + `StaysOnTop`) que bloquea el uso normal de Windows.
5. **Control Remoto desde el Servidor + PIN Offline (Sin Internet)**
   - **Con Internet (Online)**: Desde el Panel Web del Servidor puedes pulsar **🔒 Bloquear**, **🔓 Desbloquear** o **✓ Registrar Pago** en cualquier laptop y el equipo se actualizará en segundos.
   - **Sin Internet (Offline)**: Si la laptop quedó bloqueada y el cliente no tiene Wi-Fi al momento de pagar, en el Panel Web pulsas **🔑 Generar PIN Offline** y le entregas un código firmado de 8 dígitos (`DD-XXXXXX`, vinculado criptográficamente con HMAC-SHA256 a su número de cédula y a esa laptop).

---

## Estructura del Proyecto

```text
creditech/
├── iniciar_servidor.bat          # Inicia el Servidor Central y Panel Web (puerto 8085)
├── instalar_agente_laptop.bat    # Inicia/instala el Agente Creditech en la laptop del cliente
├── run_server.py                 # Lanzador Python del servidor
├── run_agent.py                  # Lanzador Python del agente de escritorio (PyQt6)
├── requirements.txt              # Dependencias (FastAPI, Uvicorn, SQLAlchemy, PyQt6, HTTPX)
├── shared/
│   ├── crypto.py                 # Firma y verificación HMAC-SHA256 de PINs offline por cédula
│   └── policy.py                 # Motor de reglas: aviso 1 día antes y bloqueo por cuota vencida
├── server/
│   ├── models.py                 # Base de datos SQLAlchemy (Device, Installment, DeviceEvent)
│   ├── dashboard.py              # Panel Web de Administración en español
│   ├── app.py                    # API REST (/api/v1/devices y /api/v1/agent)
│   └── main.py                   # Servidor Uvicorn
├── agent/
│   ├── state.py                  # Caché local a prueba de desconexión y cliente HTTP
│   ├── startup.py                # Registro en el arranque automático de Windows
│   └── ui.py                     # Interfaz PyQt6: Instalador, Portal, Aviso 1 día antes y Bloqueo
└── tests/
    ├── test_creditech.py         # Pruebas de reglas, servidor, bloqueo remoto y PIN offline
    └── test_ui.py                # Pruebas de interfaz gráfica con Nombre y Cédula
```

---

## Cómo Usarlo Paso a Paso

### 1. Iniciar Tu Servidor Central
Haz doble clic en `iniciar_servidor.bat` o ejecuta en la terminal:

```powershell
python run_server.py
```

Abre tu navegador en: **`http://localhost:8085`** (o la IP de tu servidor si conectas las laptops por red local o VPS en la nube).

Desde el Panel Web podrás:
- Hacer clic en **"+ Registrar Cliente y Laptop"** para ingresar el **Nombre**, **Número de Cédula**, teléfono, modelo/serial de la laptop, fecha de la 1ª cuota, cantidad de cuotas y monto.
- Obtener el **Código de Instalación** (`CRD-XXXX-XXXX`) para esa laptop.
- Ver cuáles equipos están **Al Día**, cuáles están en **Aviso de Pago (1 día antes)** y cuáles están **Bloqueados**.
- Bloquear o desbloquear cualquier equipo con un clic, marcar cuotas como pagadas o generar un **PIN de Desbloqueo Offline**.

### 2. Instalar el Programa en Cada Laptop Vendida
En la laptop que vas a entregar al cliente, copia la carpeta del proyecto (o compílala en un `.exe` con PyInstaller) y ejecuta `instalar_agente_laptop.bat` o:

```powershell
python run_agent.py
```

Al abrirse por primera vez aparecerá el **Asistente de Instalación de Creditech**:
- Coloca la URL de tu servidor (por ejemplo `http://localhost:8085` o la IP/dominio de tu servidor).
- Puedes registrar directamente el **Nombre del Cliente** y su **Número de Cédula** allí mismo, o pegar el **Código de Instalación (`CRD-XXXX-XXXX`)** generado en el servidor.
- Deja marcada la casilla **"Iniciar Creditech automáticamente al encender Windows"** y pulsa **Activar Protección Creditech**.
