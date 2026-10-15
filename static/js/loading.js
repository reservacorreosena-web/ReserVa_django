/**
 * ReserVa - Módulo de Animaciones y Estados de Carga
 * Intercepta peticiones, formularios y acciones pesadas para dar feedback visual al usuario.
 */

(function () {
    'use strict';

    // 1. Estructura del Overlay Global en el DOM
    function ensureOverlay() {
        let overlay = document.getElementById('rvGlobalLoadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'rvGlobalLoadingOverlay';
            overlay.className = 'rv-loading-overlay';
            overlay.innerHTML = `
                <div class="rv-loading-card">
                    <div class="rv-spinner-ring">
                        <div></div><div></div><div></div><div></div>
                    </div>
                    <div class="rv-loading-brand">Reser<span>Va</span></div>
                    <p class="rv-loading-text" id="rvGlobalLoadingMsg">Procesando tu solicitud...</p>
                    <div class="rv-loading-bar"></div>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        return overlay;
    }

    // 2. Objeto Global ReserVaLoading
    window.ReserVaLoading = {
        show: function (mensaje) {
            const overlay = ensureOverlay();
            const msgEl = document.getElementById('rvGlobalLoadingMsg');
            if (msgEl && mensaje) {
                msgEl.innerText = mensaje;
            } else if (msgEl) {
                msgEl.innerText = 'Procesando tu solicitud...';
            }
            overlay.classList.add('active');
        },
        hide: function () {
            const overlay = document.getElementById('rvGlobalLoadingOverlay');
            if (overlay) {
                overlay.classList.remove('active');
            }
        }
    };

    // 3. Inicializar al cargar el DOM
    document.addEventListener('DOMContentLoaded', function () {
        ensureOverlay();

        // Interceptar envíos de formularios en la aplicación
        document.querySelectorAll('form').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                // Si el formulario no es válido según HTML5, no mostrar carga
                if (!form.checkValidity()) {
                    return;
                }

                const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
                const action = (form.getAttribute('action') || window.location.pathname).toLowerCase();
                const explicitMsg = form.getAttribute('data-loading-text');

                // Determinar el mensaje según el tipo de formulario
                let mensajeCarga = explicitMsg || null;

                if (!mensajeCarga) {
                    if (action.includes('reset') || form.id === 'formPasswordReset') {
                        mensajeCarga = 'Conectando con el servidor de correo y enviando enlace...';
                    } else if (action.includes('mapa') || form.id === 'formMapaMesas') {
                        mensajeCarga = 'Confirmando tu mesa y enviando correo de confirmación...';
                    } else if (action.includes('crear_reserva')) {
                        mensajeCarga = 'Comprobando disponibilidad de mesas...';
                    } else if (action.includes('iniciar_sesion') || action.includes('login')) {
                        mensajeCarga = 'Verificando credenciales...';
                    } else if (action.includes('registrar') || action.includes('crear_usuario')) {
                        mensajeCarga = 'Creando tu cuenta en ReserVa...';
                    } else if (action.includes('resena') || action.includes('comentarios')) {
                        mensajeCarga = 'Publicando tu reseña...';
                    } else if (action.includes('plato') || form.querySelector('input[type="file"]')) {
                        mensajeCarga = 'Subiendo archivos y actualizando carta...';
                    } else if (form.method && form.method.toUpperCase() === 'POST') {
                        mensajeCarga = 'Guardando cambios en el sistema...';
                    }
                }

                // Deshabilitar botón y añadir micro-spinner
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.disabled = true;
                    if (submitBtn.tagName === 'BUTTON') {
                        submitBtn.innerHTML = `<span class="rv-btn-spinner"></span>` + submitBtn.innerText;
                    }
                }

                // Si es una acción que toma tiempo (POST, email, archivo), desplegar el overlay elegante
                if (mensajeCarga) {
                    window.ReserVaLoading.show(mensajeCarga);
                }
            });
        });

        // Interceptar enlaces con clase o confirmación que desencadenan operaciones de cobro o cierre
        document.querySelectorAll('a.btn-cerrar-cuenta, a.btn-confirmar-accion').forEach(function (link) {
            link.addEventListener('click', function (e) {
                // Dar tiempo al confirm() nativo si lo tiene
                setTimeout(function () {
                    window.ReserVaLoading.show('Procesando cobro y actualizando caja...');
                }, 50);
            });
        });
    });

    // Ocultar overlay al navegar hacia atrás o restaurar desde caché del navegador (BFCache)
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            window.ReserVaLoading.hide();
            // Restaurar botones si se regresa
            document.querySelectorAll('button[type="submit"]:disabled').forEach(function (btn) {
                btn.disabled = false;
                const spinner = btn.querySelector('.rv-btn-spinner');
                if (spinner) spinner.remove();
            });
        }
    });

})();
