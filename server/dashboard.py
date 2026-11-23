"""Interfaz Web y App Móvil Instalable (PWA) de Creditech by indatech.

Optimizada para usarla tanto desde el Teléfono Celular (Android / iPhone como App instalada
sin barras de navegador, con navegación inferior táctil, tarjetas móviles, envío directo
de avisos y PINs por WhatsApp y descarga de Excel de Deudores) como desde PC.
"""

from __future__ import annotations

from shared.branding import INDATECH_ICON_SVG, INDATECH_LOGO_SVG

DASHBOARD_HTML = (
    r"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
  <meta name="theme-color" content="#071D20" />
  <meta name="apple-mobile-web-app-capable" content="yes" />
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
  <meta name="apple-mobile-web-app-title" content="Creditech" />
  <link rel="manifest" href="/manifest.json" />
  <link rel="icon" type="image/svg+xml" href="/icon.svg" />
  <link rel="apple-touch-icon" href="/icon.svg" />
  <title>Creditech by indatech. — App de Control de Equipos</title>
  <style>
    :root {
      --brand: #00D094;
      --brand-hover: #00B580;
      --brand-deep: #008F64;
      --brand-soft: #E6FBF4;
      --dark: #071D20;
      --dark-2: #0D2C30;
      --text: #0F2327;
      --text-2: #526B70;
      --text-3: #879EA2;
      --bg: #F3F8F7;
      --surface: #FFFFFF;
      --surface-2: #F8FBFA;
      --border: #D9E8E5;
      --success: #00B580;
      --success-soft: #E6FBF4;
      --warning: #D97706;
      --warning-soft: #FFFBEB;
      --danger: #E03131;
      --danger-soft: #FFF5F5;
      --whatsapp: #25D366;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
    body {
      font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text);
      font-size: 14px;
      line-height: 1.48;
      padding-bottom: 84px; /* Espacio para la barra inferior en móvil */
    }

    /* Topbar */
    .topbar {
      background: linear-gradient(135deg, var(--dark) 0%, var(--dark-2) 100%);
      color: #fff;
      padding: 14px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 3px solid var(--brand);
      box-shadow: 0 8px 24px rgba(7, 29, 32, 0.14);
      position: sticky;
      top: 0;
      z-index: 100;
      flex-wrap: wrap;
      gap: 12px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .brand-logo-box {
      width: 50px;
      height: 50px;
      border-radius: 13px;
      background: #FFFFFF;
      padding: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 16px rgba(0, 208, 148, 0.32);
      border: 2px solid var(--brand);
      flex-shrink: 0;
    }
    .brand-title-row {
      display: flex;
      align-items: baseline;
      gap: 8px;
      flex-wrap: wrap;
    }
    .brand-title {
      font-size: 21px;
      font-weight: 900;
      letter-spacing: 0.3px;
      color: #FFFFFF;
    }
    .brand-pill {
      background: rgba(0, 208, 148, 0.18);
      color: var(--brand);
      border: 1px solid rgba(0, 208, 148, 0.45);
      padding: 2px 9px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 800;
    }
    .brand-sub {
      font-size: 12px;
      color: #A3C2C6;
      margin-top: 2px;
    }
    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }

    /* Botones */
    .btn {
      border: none;
      border-radius: 10px;
      padding: 10px 16px;
      font-size: 13.5px;
      font-weight: 700;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      transition: all 0.16s ease;
      text-decoration: none;
    }
    .btn-primary {
      background: var(--brand);
      color: #04221B;
      box-shadow: 0 4px 14px rgba(0, 208, 148, 0.3);
    }
    .btn-primary:hover { background: var(--brand-hover); color: #FFFFFF; }
    .btn-secondary {
      background: rgba(255, 255, 255, 0.1);
      color: #FFFFFF;
      border: 1px solid rgba(255, 255, 255, 0.22);
    }
    .btn-light {
      background: var(--surface);
      color: var(--text);
      border: 1px solid var(--border);
    }
    .btn-danger {
      background: var(--danger);
      color: #fff;
    }
    .btn-success {
      background: var(--brand-deep);
      color: #fff;
    }
    .btn-whatsapp {
      background: #E8FBF0;
      color: #0E7A38;
      border: 1px solid #96E6B3;
    }
    .btn-accent {
      background: var(--dark);
      color: var(--brand);
      border: 1px solid var(--brand);
    }
    .btn-sm { padding: 8px 12px; font-size: 12.5px; border-radius: 9px; }

    /* Contenedor */
    .container {
      max-width: 1400px;
      margin: 20px auto;
      padding: 0 18px;
    }

    /* Banner Instalar App en el Teléfono */
    .install-app-banner {
      background: linear-gradient(135deg, #071D20, #0B3832);
      border: 1.5px solid var(--brand);
      border-radius: 14px;
      padding: 14px 18px;
      color: #FFFFFF;
      display: none;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 18px;
      flex-wrap: wrap;
    }
    .install-app-banner.visible { display: flex; }

    /* KPIs */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 14px;
      margin-bottom: 20px;
    }
    .stat-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 15px;
      padding: 16px 18px;
      box-shadow: 0 4px 14px rgba(7, 29, 32, 0.04);
      position: relative;
      overflow: hidden;
    }
    .stat-card::before {
      content: "";
      position: absolute;
      top: 0;
      left: 0;
      width: 5px;
      height: 100%;
      background: var(--brand);
    }
    .stat-card.warn::before { background: var(--warning); }
    .stat-card.err::before { background: var(--danger); }
    .stat-label {
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-2);
    }
    .stat-value {
      font-size: 27px;
      font-weight: 900;
      margin-top: 4px;
      color: var(--dark);
    }
    .stat-note {
      font-size: 12px;
      color: var(--text-2);
      margin-top: 2px;
    }

    /* Filtros rápidos táctiles */
    .filter-pills {
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding-bottom: 6px;
      margin-bottom: 14px;
    }
    .filter-pill {
      padding: 7px 14px;
      border-radius: 999px;
      font-size: 12.5px;
      font-weight: 800;
      border: 1.5px solid var(--border);
      background: var(--surface);
      color: var(--text-2);
      cursor: pointer;
      white-space: nowrap;
    }
    .filter-pill.active {
      background: var(--dark);
      color: var(--brand);
      border-color: var(--brand);
    }

    /* Card principal */
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 20px;
      box-shadow: 0 6px 22px rgba(7, 29, 32, 0.04);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
      flex-wrap: wrap;
      gap: 12px;
    }
    .card-title {
      font-size: 17px;
      font-weight: 800;
      color: var(--dark);
    }
    .search-box {
      padding: 10px 14px;
      border: 1.5px solid var(--border);
      border-radius: 11px;
      min-width: 280px;
      flex: 1;
      max-width: 420px;
      font-size: 13.5px;
      background: var(--surface-2);
    }
    .search-box:focus {
      outline: none;
      border-color: var(--brand);
      background: #FFFFFF;
    }

    /* Tabla en escritorio */
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th {
      text-align: left;
      padding: 12px 13px;
      background: var(--surface-2);
      color: var(--text-2);
      font-size: 11px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 2px solid var(--border);
    }
    td {
      padding: 14px 13px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    tr:hover td { background: #F4FBF9; }

    /* Tarjetas móviles para el teléfono */
    .mobile-cards {
      display: none;
      flex-direction: column;
      gap: 14px;
    }
    .m-card {
      background: var(--surface);
      border: 1.5px solid var(--border);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 3px 12px rgba(7, 29, 32, 0.04);
    }
    .m-card-top {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px;
      margin-bottom: 10px;
    }
    .m-card-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      background: var(--surface-2);
      padding: 12px;
      border-radius: 12px;
      border: 1px solid var(--border);
      margin-bottom: 12px;
    }
    .m-card-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 5px 11px;
      border-radius: 999px;
      font-size: 11.5px;
      font-weight: 800;
    }
    .badge-ok { background: var(--success-soft); color: var(--brand-deep); border: 1px solid #99F3D6; }
    .badge-warn { background: var(--warning-soft); color: var(--warning); border: 1px solid #FDE68A; }
    .badge-err { background: var(--danger-soft); color: var(--danger); border: 1px solid #FECACA; }

    .client-name { font-weight: 800; color: var(--dark); font-size: 15px; }
    .client-meta { font-size: 12.5px; color: var(--text-2); margin-top: 2px; }
    .code-pill {
      font-family: 'Cascadia Code', Consolas, monospace;
      font-weight: 800;
      background: var(--brand-soft);
      padding: 4px 9px;
      border-radius: 8px;
      color: var(--dark);
      font-size: 12.5px;
      border: 1px solid #99F3D6;
      display: inline-block;
    }

    /* Barra de navegación inferior fija para Celular */
    .bottom-nav {
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--dark);
      border-top: 2px solid var(--brand);
      display: none;
      justify-content: space-around;
      align-items: center;
      padding: 8px 10px calc(8px + env(safe-area-inset-bottom));
      z-index: 900;
      box-shadow: 0 -6px 20px rgba(7, 29, 32, 0.25);
    }
    .nav-item {
      background: none;
      border: none;
      color: #A3C2C6;
      font-size: 11px;
      font-weight: 700;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 3px;
      cursor: pointer;
      text-decoration: none;
      padding: 4px 10px;
      border-radius: 10px;
    }
    .nav-item.primary-fab {
      background: var(--brand);
      color: #04221B;
      padding: 8px 16px;
      font-weight: 900;
    }
    .nav-icon { font-size: 17px; }

    /* Modales */
    .modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(7, 29, 32, 0.68);
      backdrop-filter: blur(3px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 1000;
      padding: 14px;
    }
    .modal-backdrop.active { display: flex; }
    .modal {
      background: var(--surface);
      border-radius: 18px;
      max-width: 780px;
      width: 100%;
      max-height: 92vh;
      overflow-y: auto;
      padding: 22px;
      box-shadow: 0 24px 60px rgba(7, 29, 32, 0.35);
      border: 1px solid var(--border);
    }
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 14px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 16px;
    }
    .modal-title { font-size: 18px; font-weight: 900; color: var(--dark); }
    .form-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 14px;
    }
    .form-group { display: flex; flex-direction: column; gap: 5px; }
    .form-group.full { grid-column: 1 / -1; }
    label { font-size: 12px; font-weight: 700; color: var(--text-2); }
    input, select {
      padding: 11px 13px;
      border: 1.5px solid var(--border);
      border-radius: 10px;
      font-size: 14px;
    }
    input:focus, select:focus {
      outline: none;
      border-color: var(--brand);
    }
    .modal-footer {
      margin-top: 18px;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
    }
    .pin-display {
      background: var(--brand-soft);
      border: 2px dashed var(--brand-deep);
      border-radius: 14px;
      padding: 16px;
      text-align: center;
      margin: 14px 0;
    }
    .pin-number {
      font-family: 'Cascadia Code', Consolas, monospace;
      font-size: 30px;
      font-weight: 900;
      color: var(--dark);
      letter-spacing: 3px;
      margin: 4px 0;
    }
    .action-group {
      display: flex;
      gap: 7px;
      flex-wrap: wrap;
    }

    /* Responsive para Teléfonos Celulares */
    @media (max-width: 820px) {
      .topbar { padding: 12px 16px; }
      .topbar-actions { display: none; }
      .bottom-nav { display: flex; }
      .desktop-table-wrap { display: none; }
      .mobile-cards { display: flex; }
      .stats-grid { grid-template-columns: 1fr 1fr; gap: 10px; }
      .stat-value { font-size: 22px; }
      .form-grid { grid-template-columns: 1fr; }
      .search-box { min-width: 100%; }
      .card { padding: 14px; }
    }
  </style>
</head>
<body>
  <header class="topbar">
    <div class="brand">
      <div class="brand-logo-box">
        """
    + INDATECH_LOGO_SVG
    + r"""
      </div>
      <div>
        <div class="brand-title-row">
          <span class="brand-title">CREDITECH</span>
          <span class="brand-pill">by indatech.</span>
        </div>
        <div class="brand-sub">App de Control, Avisos y Bloqueo de Laptops</div>
      </div>
    </div>
    <div class="topbar-actions">
      <button class="btn btn-secondary" onclick="loadDevices()">↻ Actualizar</button>
      <button class="btn btn-secondary" onclick="openQuickPinModal()" style="border-color: #FCD34D; color: #FCD34D;">🔑 PIN Rápido por Cédula</button>
      <a class="btn btn-secondary" href="/api/v1/reports/debtors.xlsx" onclick="downloadDebtorsExcel(event)" style="border-color: var(--brand); color: var(--brand);">📊 Excel de Deudores</a>
      <button class="btn btn-primary" onclick="openNewDeviceModal()">+ Nuevo Cliente</button>
    </div>
  </header>

  <main class="container">
    <!-- Banner para instalar como App en el Celular -->
    <div class="install-app-banner" id="installBanner">
      <div>
        <div style="font-weight: 800; font-size: 14.5px; color: var(--brand);">📱 Instalar Creditech en tu Teléfono</div>
        <div style="font-size: 12.5px; color: #D9E8E5;">Agrégala a tu pantalla de inicio para bloquear equipos, enviar PINs por WhatsApp y bajar el Excel desde tu celular.</div>
      </div>
      <button class="btn btn-primary btn-sm" id="installAppBtn">Instalar App</button>
    </div>

    <!-- KPIs -->
    <section class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Equipos</div>
        <div class="stat-value" id="statTotal">0</div>
        <div class="stat-note">Registrados</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Cobrado</div>
        <div class="stat-value" id="statPaidMoney" style="color: var(--brand-deep);">$0.00</div>
        <div class="stat-note" id="statUnlockedNote">0 activos</div>
      </div>
      <div class="stat-card err">
        <div class="stat-label">Falta por Cobrar</div>
        <div class="stat-value" id="statDebtMoney" style="color: var(--danger);">$0.00</div>
        <div class="stat-note" id="statDebtorsNote">0 personas deben</div>
      </div>
      <div class="stat-card warn">
        <div class="stat-label">Aviso / Bloqueados</div>
        <div class="stat-value"><span id="statWarning" style="color: var(--warning);">0</span> / <span id="statLocked" style="color: var(--danger);">0</span></div>
        <div class="stat-note">1d antes / En mora</div>
      </div>
    </section>

    <!-- Filtros rápidos -->
    <div class="filter-pills">
      <button class="filter-pill active" id="flt_all" onclick="setFilter('all')">Todos los Clientes</button>
      <button class="filter-pill" id="flt_debtors" onclick="setFilter('debtors')">💸 Personas que Deben</button>
      <button class="filter-pill" id="flt_warning" onclick="setFilter('warning')">⚠️ En Aviso (1 día antes)</button>
      <button class="filter-pill" id="flt_locked" onclick="setFilter('locked')">🔒 Equipos Bloqueados</button>
    </div>

    <!-- Lista de Equipos -->
    <section class="card">
      <div class="card-header">
        <div>
          <div class="card-title">Control de Clientes y Laptops</div>
          <div class="client-meta">Toque un cliente para bloquear, desbloquear, cobrar cuota o enviar PIN por WhatsApp</div>
        </div>
        <input
          type="text"
          id="searchInput"
          class="search-box"
          placeholder="🔍 Buscar nombre, cédula, serial o código..."
          oninput="renderTable()"
        />
      </div>

      <!-- Vista Escritorio -->
      <div class="desktop-table-wrap" style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th>Cliente / Cédula</th>
              <th>Laptop / Serial</th>
              <th>Código Instalación</th>
              <th>Pagado / Falta Pagar</th>
              <th>Próxima Cuota</th>
              <th>Estado del Equipo</th>
              <th>Acciones Rápidas</th>
            </tr>
          </thead>
          <tbody id="devicesTableBody">
            <tr><td colspan="7" style="text-align:center; padding: 32px;">Cargando equipos...</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Vista Tarjetas para Teléfono Celular -->
      <div class="mobile-cards" id="mobileCardsContainer"></div>
    </section>
  </main>

  <!-- Barra Inferior Fija para Teléfono Celular -->
  <nav class="bottom-nav">
    <button class="nav-item" onclick="setFilter('all'); window.scrollTo({top:0,behavior:'smooth'});">
      <span class="nav-icon">💻</span>
      <span>Equipos</span>
    </button>
    <button class="nav-item" onclick="setFilter('debtors')">
      <span class="nav-icon">💸</span>
      <span>Deudores</span>
    </button>
    <button class="nav-item primary-fab" onclick="openNewDeviceModal()">
      <span class="nav-icon">＋</span>
      <span>Nuevo</span>
    </button>
    <button class="nav-item" onclick="openQuickPinModal()">
      <span class="nav-icon">🔑</span>
      <span>PIN Cédula</span>
    </button>
    <a class="nav-item" href="/api/v1/reports/debtors.xlsx" onclick="downloadDebtorsExcel(event)">
      <span class="nav-icon">📊</span>
      <span>Excel</span>
    </a>
  </nav>

  <!-- Modal: Generador de PIN Rápido por Cédula (Funciona 100% sin Wi-Fi ni Servidor) -->
  <div class="modal-backdrop" id="quickPinModal">
    <div class="modal" style="max-width: 520px;">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="width:40px; height:40px;">"""
    + INDATECH_ICON_SVG
    + r"""</div>
          <div>
            <div class="modal-title">🔑 Generar PIN por Cédula</div>
            <div class="client-meta">Desbloquea cualquier laptop desde tu teléfono sin estar en el mismo Wi-Fi</div>
          </div>
        </div>
        <button class="btn btn-light btn-sm" onclick="closeModal('quickPinModal')">✕</button>
      </div>
      <div class="form-grid">
        <div class="form-group full">
          <label>Número de Cédula del Cliente *</label>
          <input type="text" id="qp_cedula" placeholder="Ej: V-18.452.910" />
        </div>
        <div class="form-group">
          <label>Días de Desbloqueo</label>
          <select id="qp_days">
            <option value="30">30 días (Pago de 1 cuota mensual)</option>
            <option value="15">15 días (Pago quincenal)</option>
            <option value="7">7 días (Prórroga semanal)</option>
            <option value="3">3 días (Gracia temporal)</option>
            <option value="99">Liberación Definitiva (Crédito 100% pagado)</option>
          </select>
        </div>
        <div class="form-group">
          <label>Teléfono WhatsApp (opcional)</label>
          <input type="text" id="qp_phone" placeholder="Ej: +58 412-5551234" />
        </div>
      </div>
      <div id="quickPinResultBox"></div>
      <div class="modal-footer">
        <button type="button" class="btn btn-light" onclick="closeModal('quickPinModal')">Cerrar</button>
        <button type="button" class="btn btn-primary" onclick="runQuickPinByCedula()">🔑 Calcular PIN de Desbloqueo</button>
      </div>
    </div>
  </div>

  <!-- Modal: Registrar Nuevo Cliente y Laptop -->
  <div class="modal-backdrop" id="newDeviceModal">
    <div class="modal">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="width:40px; height:40px;">"""
    + INDATECH_ICON_SVG
    + r"""</div>
          <div>
            <div class="modal-title">Registrar Cliente y Laptop</div>
            <div class="client-meta">Creditech by indatech.</div>
          </div>
        </div>
        <button class="btn btn-light btn-sm" onclick="closeModal('newDeviceModal')">✕</button>
      </div>
      <form id="newDeviceForm" onsubmit="submitNewDevice(event)">
        <div class="form-grid">
          <div class="form-group">
            <label>Nombre Completo del Cliente *</label>
            <input type="text" id="f_client_name" required placeholder="Ej: Carlos Eduardo Pérez" />
          </div>
          <div class="form-group">
            <label>Número de Cédula *</label>
            <input type="text" id="f_client_cedula" required placeholder="Ej: V-18.452.910" />
          </div>
          <div class="form-group">
            <label>Teléfono WhatsApp del Cliente</label>
            <input type="text" id="f_client_phone" placeholder="Ej: +58 412-5551234" />
          </div>
          <div class="form-group">
            <label>Marca y Modelo de la Laptop *</label>
            <input type="text" id="f_laptop_model" required placeholder="Ej: Lenovo ThinkPad T14" />
          </div>
          <div class="form-group">
            <label>Serial del Equipo</label>
            <input type="text" id="f_laptop_serial" placeholder="Ej: PF-39X81K" />
          </div>
          <div class="form-group">
            <label>Fecha de Vencimiento de 1ª Cuota *</label>
            <input type="date" id="f_first_due_date" required />
          </div>
          <div class="form-group">
            <label>Cantidad de Cuotas *</label>
            <input type="number" id="f_total_installments" min="1" max="48" value="6" required />
          </div>
          <div class="form-group">
            <label>Monto por Cuota (USD $) *</label>
            <input type="number" id="f_installment_amount" step="0.01" min="1" value="85.00" required />
          </div>
          <div class="form-group full">
            <label>Frecuencia de Pago</label>
            <select id="f_frequency_days">
              <option value="30">Mensual (cada 30 días)</option>
              <option value="15">Quincenal (cada 15 días)</option>
              <option value="7">Semanal (cada 7 días)</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-light" onclick="closeModal('newDeviceModal')">Cancelar</button>
          <button type="submit" class="btn btn-primary">Guardar Cliente y Generar Código</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Modal: Detalle de Cuotas, Bloqueo, WhatsApp y PIN Offline -->
  <div class="modal-backdrop" id="detailModal">
    <div class="modal">
      <div class="modal-header">
        <div style="display:flex; align-items:center; gap:12px;">
          <div style="width:40px; height:40px;">"""
    + INDATECH_ICON_SVG
    + r"""</div>
          <div>
            <div class="modal-title" id="detailTitle">Detalle del Equipo</div>
            <div class="client-meta" id="detailSubtitle"></div>
          </div>
        </div>
        <button class="btn btn-light btn-sm" onclick="closeModal('detailModal')">✕</button>
      </div>

      <div id="detailContent"></div>
    </div>
  </div>

  <script>
    let ALL_DEVICES = [];
    let CURRENT_FILTER = 'all';
    let deferredInstallPrompt = null;

    // Registro de Service Worker para instalar como App en Android/iPhone
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredInstallPrompt = e;
      document.getElementById('installBanner').classList.add('visible');
    });
    document.getElementById('installAppBtn')?.addEventListener('click', async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      document.getElementById('installBanner').classList.remove('visible');
    });

    window.addEventListener('DOMContentLoaded', () => {
      const tomorrow = new Date();
      tomorrow.setDate(tomorrow.getDate() + 1);
      const iso = tomorrow.toISOString().split('T')[0];
      const dateInput = document.getElementById('f_first_due_date');
      if (dateInput) dateInput.value = iso;
      loadDevices();
    });

    function setFilter(flt) {
      CURRENT_FILTER = flt;
      ['all', 'debtors', 'warning', 'locked'].forEach(k => {
        const el = document.getElementById('flt_' + k);
        if (el) el.classList.toggle('active', k === flt);
      });
      renderTable();
    }

        // Fallback a memoria local del teléfono (IndexedDB / localStorage) cuando no hay Wi-Fi o el servidor está apagado
        function getLocalPocketDevices() {
          try {
            return JSON.parse(localStorage.getItem('creditech_pocket_devices') || '[]');
          } catch (e) { return []; }
        }
        function saveLocalPocketDevices(list) {
          try {
            localStorage.setItem('creditech_pocket_devices', JSON.stringify(list));
          } catch (e) {}
        }

        // Generador criptográfico HMAC-SHA256 idéntico a shared/crypto.py en JavaScript puro (Web Crypto API)
        async function hmacSha256Hex(keyStr, msgStr) {
          const enc = new TextEncoder();
          const key = await crypto.subtle.importKey(
            'raw', enc.encode(keyStr), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
          );
          const sig = await crypto.subtle.sign('HMAC', key, enc.encode(msgStr));
          return Array.from(new Uint8Array(sig)).map(b => b.toString(16).padStart(2, '0')).join('');
        }

        function normalizeCedulaJs(cedula) {
          return String(cedula || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
        }

        async function generateOfflinePinInBrowser(cedula, unlockDays = 30, installmentNumber = 0) {
          const normId = normalizeCedulaJs(cedula);
          const masterKey = 'INDATECH-CREDITECH-MASTER-2026';
          const deviceSecret = (await hmacSha256Hex(masterKey, `DEVICE_SECRET|v1|${normId}`)).slice(0, 32);
          const todayIso = new Date().toISOString().slice(0, 10);
          const daysClamped = Math.max(1, Math.min(99, parseInt(unlockDays, 10) || 30));
          const prefix = String(daysClamped).padStart(2, '0');
          const payload = `CREDITECH|v1|${normId}|${todayIso}|${prefix}|${parseInt(installmentNumber, 10) || 0}`;
          const digest = await hmacSha256Hex(deviceSecret, payload);
          const numericCode = parseInt(digest.slice(0, 8), 16) % 1000000;
          return `${prefix}-${String(numericCode).padStart(6, '0')}`;
        }

        async function loadDevices() {
          try {
            const res = await fetch('/api/v1/devices');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            ALL_DEVICES = data.devices || [];
            saveLocalPocketDevices(ALL_DEVICES);
          } catch (err) {
            ALL_DEVICES = getLocalPocketDevices();
          }
          updateStats();
          renderTable();
        }

    function updateStats() {
      const total = ALL_DEVICES.length;
      const locked = ALL_DEVICES.filter(d => d.policy.locked).length;
      const warning = ALL_DEVICES.filter(d => !d.policy.locked && d.policy.warning_due_soon).length;
      const unlocked = total - locked;

      const totalPaid = ALL_DEVICES.reduce((acc, d) => acc + (d.paid_amount || 0), 0);
      const totalDebt = ALL_DEVICES.reduce((acc, d) => acc + (d.pending_amount || 0), 0);
      const debtorsCount = ALL_DEVICES.filter(d => (d.pending_amount || 0) > 0.001).length;

      document.getElementById('statTotal').textContent = total;
      document.getElementById('statPaidMoney').textContent = '$' + totalPaid.toFixed(2);
      document.getElementById('statUnlockedNote').textContent = `${unlocked} equipo(s) activo(s)`;
      document.getElementById('statDebtMoney').textContent = '$' + totalDebt.toFixed(2);
      document.getElementById('statDebtorsNote').textContent = `${debtorsCount} persona(s) deben`;
      document.getElementById('statWarning').textContent = warning;
      document.getElementById('statLocked').textContent = locked;
    }

    function buildWhatsAppUrl(phone, text) {
      const digits = String(phone || '').replace(/[^0-9]/g, '');
      const encoded = encodeURIComponent(text);
      return digits ? `https://wa.me/${digits}?text=${encoded}` : `https://wa.me/?text=${encoded}`;
    }

    function evaluatePolicyInBrowser(dev) {
      const todayIso = new Date().toISOString().slice(0, 10);
      const todayMs = new Date(todayIso + 'T00:00:00Z').getTime();
      const insts = (dev.installments || []).slice().sort((a, b) => a.number - b.number);
      const pending = insts.filter(i => i.status !== 'paid');
      const paid = insts.filter(i => i.status === 'paid');
      const overdue = pending.filter(i => i.due_date < todayIso);
      const nextInst = pending.length ? pending[0] : null;
      let daysUntilDue = null;
      if (nextInst) {
        const dueMs = new Date(nextInst.due_date + 'T00:00:00Z').getTime();
        daysUntilDue = Math.round((dueMs - todayMs) / 86400000);
      }

      const graceUntil = dev.manual_unlock_until || null;
      const hasGrace = graceUntil && graceUntil >= todayIso;
      const manualStatus = dev.manual_status || 'auto';

      let locked = false;
      let lockReason = '';
      if (manualStatus === 'locked' && !hasGrace) {
        locked = true;
        lockReason = dev.lock_reason_override || 'Equipo bloqueado remotamente por Creditech.';
      } else if (manualStatus === 'auto' && overdue.length > 0 && !hasGrace) {
        locked = true;
        lockReason = `Cuota #${overdue[0].number} vencida el ${overdue[0].due_date} ($${Number(overdue[0].amount).toFixed(2)}).`;
      }

      const warningDueSoon = !locked && nextInst !== null && daysUntilDue !== null && daysUntilDue >= 0 && daysUntilDue <= 1;

      const totalAmount = insts.reduce((s, i) => s + Number(i.amount || 0), 0);
      const paidAmount = paid.reduce((s, i) => s + Number(i.amount || 0), 0);
      const pendingAmount = Math.max(0, totalAmount - paidAmount);

      dev.total_amount = totalAmount;
      dev.paid_amount = paidAmount;
      dev.pending_amount = pendingAmount;
      dev.policy = {
        locked,
        lock_reason: lockReason,
        warning_due_soon: warningDueSoon,
        days_until_due: daysUntilDue,
        next_installment: nextInst,
        overdue_installments: overdue,
        pending_count: pending.length,
        paid_count: paid.length,
        total_count: insts.length,
      };
      return dev;
    }

    function downloadLocalExcelCsv() {
      const rows = [
        ['Nombre del Cliente', 'Numero de Cedula', 'Telefono', 'Laptop', 'Serial', 'Codigo Creditech', 'Total Credito ($)', 'Lo que ha Pagado ($)', 'Lo que Falta por Pagar ($)', 'Cuotas Pagadas', 'Cuotas Pendientes', 'Proximo Vencimiento', 'Estado']
      ];
      ALL_DEVICES.forEach(raw => {
        const d = evaluatePolicyInBrowser(raw);
        const p = d.policy;
        const stateStr = p.locked ? 'BLOQUEADO' : (p.warning_due_soon ? 'AVISO 1 DIA ANTES' : 'AL DIA');
        const nextDue = p.next_installment ? p.next_installment.due_date : 'PAGADO';
        rows.push([
          d.client_name,
          d.client_cedula,
          d.client_phone || 'N/A',
          d.laptop_model || 'Laptop',
          d.laptop_serial || 'N/A',
          d.enrollment_code || 'CRD-0000',
          (d.total_amount || 0).toFixed(2),
          (d.paid_amount || 0).toFixed(2),
          (d.pending_amount || 0).toFixed(2),
          `${p.paid_count}/${p.total_count}`,
          String(p.pending_count),
          nextDue,
          stateStr
        ]);
      });
      const csvContent = '\uFEFF' + rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(';')).join('\r\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `respaldo_deudores_creditech_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }

    async function downloadDebtorsExcel(e) {
      if (e) e.preventDefault();
      try {
        const res = await fetch('/api/v1/reports/debtors.xlsx');
        if (res.ok && (res.headers.get('content-type') || '').includes('spreadsheet')) {
          const blob = await res.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `respaldo_deudores_creditech_${new Date().toISOString().slice(0, 10)}.xlsx`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return;
        }
      } catch (err) {}
      downloadLocalExcelCsv();
    }

    function renderTable() {
      const q = (document.getElementById('searchInput').value || '').toLowerCase().trim();
      const tbody = document.getElementById('devicesTableBody');
      const mobileBox = document.getElementById('mobileCardsContainer');

      const filtered = ALL_DEVICES.filter(d => {
        if (CURRENT_FILTER === 'debtors' && (d.pending_amount || 0) <= 0.001) return false;
        if (CURRENT_FILTER === 'warning' && (!d.policy.warning_due_soon || d.policy.locked)) return false;
        if (CURRENT_FILTER === 'locked' && !d.policy.locked) return false;
        if (!q) return true;
        return (
          d.client_name.toLowerCase().includes(q) ||
          d.client_cedula.toLowerCase().includes(q) ||
          (d.laptop_model || '').toLowerCase().includes(q) ||
          (d.laptop_serial || '').toLowerCase().includes(q) ||
          (d.enrollment_code || '').toLowerCase().includes(q)
        );
      });

      if (filtered.length === 0) {
        const emptyMsg = 'No hay clientes en esta vista. Pulsa "+ Nuevo" para registrar una laptop.';
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 34px; color: var(--text-2);">${emptyMsg}</td></tr>`;
        mobileBox.innerHTML = `<div style="text-align:center; padding: 28px; color: var(--text-2);">${emptyMsg}</div>`;
        return;
      }

      tbody.innerHTML = filtered.map(d => {
        const p = d.policy;
        let statusBadge = '';
        if (p.locked) {
          statusBadge = `<span class="badge badge-err">🔒 BLOQUEADO</span><div class="client-meta">${escapeHtml(d.manual_status === 'locked' ? 'Bloqueo remoto' : 'Cuota vencida')}</div>`;
        } else if (p.warning_due_soon) {
          statusBadge = `<span class="badge badge-warn">⚠️ AVISO 1 DÍA ANTES</span><div class="client-meta">Vence ${p.days_until_due === 1 ? 'MAÑANA' : 'HOY'}</div>`;
        } else {
          statusBadge = `<span class="badge badge-ok">✓ AL DÍA</span>`;
        }

        let nextInstHtml = '<span class="badge badge-ok">Pagado</span>';
        let waReminderText = `Hola ${d.client_name} (${d.client_cedula}), le escribimos de Creditech by indatech. `;
        if (p.next_installment) {
          const ni = p.next_installment;
          waReminderText += `Le recordamos que su Cuota #${ni.number} por $${ni.amount.toFixed(2)} vence el ${ni.due_date}.`;
          const daysTxt = p.days_until_due < 0
            ? `<span style="color:var(--danger);font-weight:800;">Vencida (${Math.abs(p.days_until_due)}d)</span>`
            : (p.days_until_due === 1
                ? `<span style="color:var(--warning);font-weight:800;">Vence mañana</span>`
                : (p.days_until_due === 0
                    ? `<span style="color:var(--warning);font-weight:800;">Vence hoy</span>`
                    : `en ${p.days_until_due}d`));
          nextInstHtml = `
            <div><strong>Cuota #${ni.number}</strong> — $${ni.amount.toFixed(2)}</div>
            <div class="client-meta">${ni.due_date} (${daysTxt})</div>
          `;
        }
        const waUrl = buildWhatsAppUrl(d.client_phone, waReminderText);

        return `
          <tr>
            <td>
              <div class="client-name">${escapeHtml(d.client_name)}</div>
              <div class="client-meta">C.I: <strong>${escapeHtml(d.client_cedula)}</strong> ${d.client_phone ? '· ' + escapeHtml(d.client_phone) : ''}</div>
            </td>
            <td>
              <div style="font-weight:700;">${escapeHtml(d.laptop_model)}</div>
              <div class="client-meta">Serial: ${escapeHtml(d.laptop_serial || 'N/A')}</div>
            </td>
            <td><span class="code-pill">${escapeHtml(d.enrollment_code)}</span></td>
            <td>
              <div style="color:var(--brand-deep); font-weight:800;">Pagado: $${(d.paid_amount || 0).toFixed(2)}</div>
              <div style="color:${(d.pending_amount || 0) > 0 ? 'var(--danger)' : 'var(--brand-deep)'}; font-weight:800;">
                Falta: $${(d.pending_amount || 0).toFixed(2)}
              </div>
              <div class="client-meta">${p.paid_count}/${p.total_count} cuotas</div>
            </td>
            <td>${nextInstHtml}</td>
            <td>${statusBadge}</td>
            <td>
              <div class="action-group">
                ${p.locked
                  ? `<button class="btn btn-success btn-sm" onclick="quickUnlock('${d.id}')">🔓 Desbloquear</button>`
                  : `<button class="btn btn-danger btn-sm" onclick="quickLock('${d.id}')">🔒 Bloquear</button>`
                }
                <button class="btn btn-accent btn-sm" onclick="openDeviceDetail('${d.id}')">Cuotas / PIN</button>
                <a class="btn btn-whatsapp btn-sm" href="${waUrl}" target="_blank">💬 WhatsApp</a>
              </div>
            </td>
          </tr>
        `;
      }).join('');

      // Renderizar Tarjetas Táctiles para el Teléfono Celular
      mobileBox.innerHTML = filtered.map(d => {
        const p = d.policy;
        let statusBadge = p.locked
          ? `<span class="badge badge-err">🔒 BLOQUEADO</span>`
          : (p.warning_due_soon
              ? `<span class="badge badge-warn">⚠️ AVISO 1D</span>`
              : `<span class="badge badge-ok">✓ AL DÍA</span>`);

        let nextTxt = 'Crédito Pagado';
        let waReminderText = `Hola ${d.client_name} (${d.client_cedula}), le escribimos de Creditech by indatech.`;
        if (p.next_installment) {
          const ni = p.next_installment;
          nextTxt = `Cuota #${ni.number} ($${ni.amount.toFixed(2)}) · ${ni.due_date}`;
          waReminderText += ` Su Cuota #${ni.number} por $${ni.amount.toFixed(2)} tiene fecha ${ni.due_date}.`;
        }
        const waUrl = buildWhatsAppUrl(d.client_phone, waReminderText);

        return `
          <div class="m-card">
            <div class="m-card-top">
              <div>
                <div class="client-name">${escapeHtml(d.client_name)}</div>
                <div class="client-meta">Cédula: <strong>${escapeHtml(d.client_cedula)}</strong></div>
                <div class="client-meta">${escapeHtml(d.laptop_model)} · <span class="code-pill">${escapeHtml(d.enrollment_code)}</span></div>
              </div>
              ${statusBadge}
            </div>
            <div class="m-card-grid">
              <div>
                <div class="stat-label">Ha Pagado</div>
                <div style="font-size:16px; font-weight:900; color:var(--brand-deep);">$${(d.paid_amount || 0).toFixed(2)}</div>
                <div class="client-meta">${p.paid_count} de ${p.total_count} cuotas</div>
              </div>
              <div>
                <div class="stat-label">Falta por Pagar</div>
                <div style="font-size:16px; font-weight:900; color:var(--danger);">$${(d.pending_amount || 0).toFixed(2)}</div>
                <div class="client-meta">${escapeHtml(nextTxt)}</div>
              </div>
            </div>
            <div class="m-card-actions">
              ${p.locked
                ? `<button class="btn btn-success btn-sm" onclick="quickUnlock('${d.id}')">🔓 Desbloquear</button>`
                : `<button class="btn btn-danger btn-sm" onclick="quickLock('${d.id}')">🔒 Bloquear</button>`
              }
              <button class="btn btn-accent btn-sm" onclick="openDeviceDetail('${d.id}')">🔑 Cuotas / PIN</button>
              <a class="btn btn-whatsapp btn-sm" style="grid-column: 1 / -1;" href="${waUrl}" target="_blank">💬 Enviar Aviso de Cobro por WhatsApp</a>
            </div>
          </div>
        `;
      }).join('');
    }

    function openNewDeviceModal() {
      document.getElementById('newDeviceModal').classList.add('active');
    }

    function openQuickPinModal() {
      document.getElementById('quickPinModal').classList.add('active');
    }

    async function runQuickPinByCedula() {
      const cedula = document.getElementById('qp_cedula').value.trim();
      const days = parseInt(document.getElementById('qp_days').value, 10) || 30;
      const phone = document.getElementById('qp_phone').value.trim();
      if (!cedula) {
        alert('Ingresa el Número de Cédula del cliente.');
        return;
      }
      const pin = await generateOfflinePinInBrowser(cedula, days, 0);
      const waText = `Hola (Cédula ${cedula}), su pago ha sido verificado en Creditech by indatech. Ingrese este PIN en la pantalla de su laptop para desbloquearla: *${pin}*`;
      const waUrl = buildWhatsAppUrl(phone, waText);

      document.getElementById('quickPinResultBox').innerHTML = `
        <div class="pin-display">
          <div style="font-size:12px; font-weight:800; color:var(--brand-deep);">PIN PARA CÉDULA ${escapeHtml(cedula)} (${days === 99 ? 'DEFINITIVO' : days + ' DÍAS'})</div>
          <div class="pin-number">${pin}</div>
          <div class="client-meta">Este PIN funciona sin internet directamente en la laptop registrada con esa cédula.</div>
          <div style="margin-top:10px;">
            <a class="btn btn-whatsapp btn-sm" href="${waUrl}" target="_blank">💬 Enviar PIN por WhatsApp</a>
          </div>
        </div>
      `;
    }

    function closeModal(id) {
      document.getElementById(id).classList.remove('active');
    }

    async function submitNewDevice(e) {
      e.preventDefault();
      const payload = {
        client_name: document.getElementById('f_client_name').value.trim(),
        client_cedula: document.getElementById('f_client_cedula').value.trim(),
        client_phone: document.getElementById('f_client_phone').value.trim(),
        laptop_model: document.getElementById('f_laptop_model').value.trim(),
        laptop_serial: document.getElementById('f_laptop_serial').value.trim(),
        first_due_date: document.getElementById('f_first_due_date').value,
        total_installments: parseInt(document.getElementById('f_total_installments').value, 10),
        installment_amount: parseFloat(document.getElementById('f_installment_amount').value),
        frequency_days: parseInt(document.getElementById('f_frequency_days').value, 10),
      };

      try {
        const res = await fetch('/api/v1/devices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          closeModal('newDeviceModal');
          document.getElementById('newDeviceForm').reset();
          await loadDevices();
          return;
        }
      } catch (err) {}

      // Modo autónomo en el teléfono (GitHub Pages / Offline)
      const firstDate = new Date(payload.first_due_date + 'T00:00:00Z');
      const installments = [];
      for (let i = 1; i <= payload.total_installments; i++) {
        const d = new Date(firstDate.getTime() + (i - 1) * payload.frequency_days * 86400000);
        installments.push({
          id: 'inst_' + Date.now() + '_' + i,
          number: i,
          due_date: d.toISOString().slice(0, 10),
          amount: payload.installment_amount,
          status: 'pending',
          paid_at: null
        });
      }
      const p1 = Math.floor(1000 + Math.random() * 9000);
      const p2 = Math.floor(1000 + Math.random() * 9000);
      const newDev = evaluatePolicyInBrowser({
        id: 'dev_' + Date.now(),
        client_name: payload.client_name,
        client_cedula: payload.client_cedula,
        client_phone: payload.client_phone,
        laptop_model: payload.laptop_model,
        laptop_serial: payload.laptop_serial,
        enrollment_code: `CRD-${p1}-${p2}`,
        manual_status: 'auto',
        manual_unlock_until: null,
        lock_reason_override: '',
        installments
      });
      ALL_DEVICES.unshift(newDev);
      saveLocalPocketDevices(ALL_DEVICES);
      closeModal('newDeviceModal');
      document.getElementById('newDeviceForm').reset();
      updateStats();
      renderTable();
    }

    async function quickLock(deviceId) {
      const reason = prompt(
        'Motivo del bloqueo que verá el cliente en la pantalla de su laptop:',
        'Cuota vencida pendiente de pago. Comuníquese con Indatech / Creditech para desbloquear su equipo.'
      );
      if (reason === null) return;
      try {
        const res = await fetch(`/api/v1/devices/${deviceId}/lock`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason }),
        });
        if (res.ok) {
          await loadDevices();
          return;
        }
      } catch (e) {}
      const dev = ALL_DEVICES.find(x => x.id === deviceId);
      if (dev) {
        dev.manual_status = 'locked';
        dev.lock_reason_override = reason;
        evaluatePolicyInBrowser(dev);
        saveLocalPocketDevices(ALL_DEVICES);
        updateStats();
        renderTable();
      }
    }

    async function quickUnlock(deviceId) {
      try {
        const res = await fetch(`/api/v1/devices/${deviceId}/unlock`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'auto', grace_days: 3 }),
        });
        if (res.ok) {
          await loadDevices();
          return;
        }
      } catch (e) {}
      const dev = ALL_DEVICES.find(x => x.id === deviceId);
      if (dev) {
        dev.manual_status = 'auto';
        const grace = new Date(Date.now() + 3 * 86400000).toISOString().slice(0, 10);
        dev.manual_unlock_until = grace;
        evaluatePolicyInBrowser(dev);
        saveLocalPocketDevices(ALL_DEVICES);
        updateStats();
        renderTable();
      }
    }

    async function openDeviceDetail(deviceId) {
      let d = null;
      try {
        const res = await fetch(`/api/v1/devices/${deviceId}`);
        if (res.ok) d = await res.json();
      } catch (e) {}
      if (!d) {
        d = ALL_DEVICES.find(x => x.id === deviceId);
        if (d) evaluatePolicyInBrowser(d);
      }
      if (!d) return;

      document.getElementById('detailTitle').textContent = `${d.client_name} (${d.client_cedula})`;
      document.getElementById('detailSubtitle').textContent =
        `Laptop: ${d.laptop_model} · Pagado: $${(d.paid_amount || 0).toFixed(2)} · Falta: $${(d.pending_amount || 0).toFixed(2)}`;

      const rows = (d.installments || []).map(inst => {
        const isPaid = inst.status === 'paid';
        return `
          <tr>
            <td><strong>#${inst.number}</strong></td>
            <td>${inst.due_date}</td>
            <td>$${inst.amount.toFixed(2)}</td>
            <td>
              ${isPaid
                ? `<span class="badge badge-ok">✓ PAGADA</span>`
                : `<span class="badge badge-warn">PENDIENTE</span>`
              }
            </td>
            <td>
              ${!isPaid
                ? `<button class="btn btn-success btn-sm" onclick="markInstallmentPaid('${d.id}', '${inst.id}')">✓ Cobrar</button>`
                : `<span class="client-meta">${inst.paid_at ? inst.paid_at.slice(0, 10) : 'OK'}</span>`
              }
            </td>
          </tr>
        `;
      }).join('');

      document.getElementById('detailContent').innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:14px; background:var(--surface-2); padding:14px; border-radius:12px; border:1px solid var(--border);">
          <div>
            <div style="font-size:11px; color:var(--text-2); font-weight:800;">CÓDIGO DE INSTALACIÓN DE LA LAPTOP</div>
            <div style="font-size:19px; font-weight:900; font-family:Consolas,monospace; color:var(--dark);">${escapeHtml(d.enrollment_code)}</div>
          </div>
          <div class="action-group">
            <button class="btn btn-danger btn-sm" onclick="quickLock('${d.id}'); closeModal('detailModal');">🔒 Bloquear</button>
            <button class="btn btn-success btn-sm" onclick="quickUnlock('${d.id}'); closeModal('detailModal');">🔓 Desbloquear</button>
            <button class="btn btn-primary btn-sm" onclick="generatePinForDevice('${d.id}', '${escapeHtml(d.client_phone || '')}')">🔑 Generar PIN</button>
          </div>
        </div>

        <div id="pinBoxContainer"></div>

        <h4 style="margin: 12px 0 8px; color: var(--dark); font-weight:800;">Cronograma de Cuotas</h4>
        <div style="overflow-x:auto;">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Vencimiento</th>
                <th>Monto</th>
                <th>Estado</th>
                <th>Acción</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;

      document.getElementById('detailModal').classList.add('active');
    }

    async function markInstallmentPaid(deviceId, installmentId) {
      try {
        const res = await fetch(`/api/v1/devices/${deviceId}/installments/${installmentId}/pay`, {
          method: 'POST',
        });
        if (res.ok) {
          await openDeviceDetail(deviceId);
          await loadDevices();
          return;
        }
      } catch (e) {}
      const dev = ALL_DEVICES.find(x => x.id === deviceId);
      if (dev) {
        const inst = (dev.installments || []).find(i => i.id === installmentId);
        if (inst) {
          inst.status = 'paid';
          inst.paid_at = new Date().toISOString();
        }
        if (dev.manual_status === 'locked') dev.manual_status = 'auto';
        evaluatePolicyInBrowser(dev);
        saveLocalPocketDevices(ALL_DEVICES);
        updateStats();
        renderTable();
        await openDeviceDetail(deviceId);
      }
    }

    async function generatePinForDevice(deviceId, phone) {
      let data = null;
      try {
        const res = await fetch(`/api/v1/devices/${deviceId}/offline-pin`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ unlock_days: 30 }),
        });
        if (res.ok) data = await res.json();
      } catch (e) {}
      if (!data) {
        const dev = ALL_DEVICES.find(x => x.id === deviceId);
        if (!dev) return;
        const pin = await generateOfflinePinInBrowser(dev.client_cedula, 30, 0);
        data = {
          client_name: dev.client_name,
          client_cedula: dev.client_cedula,
          unlock_days: 30,
          pin
        };
      }
      const waText = `Hola ${data.client_name} (${data.client_cedula}), su pago ha sido registrado en Creditech by indatech. Su PIN de desbloqueo es: *${data.pin}*`;
      const waUrl = buildWhatsAppUrl(phone, waText);

      const box = document.getElementById('pinBoxContainer');
      box.innerHTML = `
        <div class="pin-display">
          <div style="font-size:12px; font-weight:800; color:var(--brand-deep);">PIN DE DESBLOQUEO GENERADO (${data.unlock_days} DÍAS)</div>
          <div class="pin-number">${data.pin}</div>
          <div style="margin-top:8px;">
            <a class="btn btn-whatsapp btn-sm" href="${waUrl}" target="_blank">💬 Enviar PIN al Cliente por WhatsApp</a>
          </div>
        </div>
      `;
    }

    function escapeHtml(str) {
      return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
    }
  </script>
</body>
</html>
"""
)
