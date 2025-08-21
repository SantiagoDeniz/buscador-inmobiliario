// Animación para minimizar y restaurar los filtros
function minimizarFiltros() {
  const filtros = document.getElementById('filtros-busqueda');
  if (!filtros) return;
  filtros.style.transition = 'max-height 0.5s cubic-bezier(0.4,0,0.2,1), opacity 0.5s';
  filtros.style.maxHeight = '0px';
  filtros.style.opacity = '0.2';
  filtros.style.overflow = 'hidden';
}

function restaurarFiltros() {
  const filtros = document.getElementById('filtros-busqueda');
  if (!filtros) return;
  filtros.style.transition = 'max-height 0.5s cubic-bezier(0.4,0,0.2,1), opacity 0.5s';
  filtros.style.maxHeight = '1000px';
  filtros.style.opacity = '1';
  filtros.style.overflow = 'visible';
}

// Lógica para disparar animación al buscar y autocompletar filtros con IA
async function onBuscarClick(e) {
  if (e) e.preventDefault();
  minimizarFiltros();
  mostrarSpinner();
  const textoLibre = document.getElementById('keywords').value;
  if (!textoLibre) {
    ocultarSpinner();
    document.querySelector('form').submit();
    return;
  }
  // Llamada AJAX al backend para obtener filtros sugeridos
  try {
    const resp = await fetch('/core/ia_sugerir_filtros/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
      },
      body: JSON.stringify({ query: textoLibre })
    });
    if (!resp.ok) throw new Error('Error IA');
    const data = await resp.json();
    if (data.filters) {
      autocompletarFiltros(data.filters);
      if (data.remaining_text !== undefined) {
        document.getElementById('keywords').value = data.remaining_text;
      }
    }
    setTimeout(() => {
      ocultarSpinner();
      document.querySelector('form').submit();
    }, 400); // Espera breve para que el usuario vea el autocompletado
  } catch (err) {
    ocultarSpinner();
    document.querySelector('form').submit();
  }
}
// Spinner visual
function mostrarSpinner() {
  let spinner = document.getElementById('busqueda-spinner');
  if (!spinner) {
    spinner = document.createElement('div');
    spinner.id = 'busqueda-spinner';
    spinner.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;padding:12px;"><span class="spinner-border" role="status" aria-hidden="true"></span> <span style="margin-left:10px;">Procesando búsqueda inteligente...</span></div>';
    spinner.style.position = 'fixed';
    spinner.style.top = '30%';
    spinner.style.left = '50%';
    spinner.style.transform = 'translate(-50%, -50%)';
    spinner.style.zIndex = '9999';
    spinner.style.background = '#fff';
    spinner.style.borderRadius = '8px';
    spinner.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
    document.body.appendChild(spinner);
  }
  spinner.style.display = 'block';
}

function ocultarSpinner() {
  const spinner = document.getElementById('busqueda-spinner');
  if (spinner) spinner.style.display = 'none';
}

function autocompletarFiltros(filtros) {
  for (const [campo, valor] of Object.entries(filtros)) {
    const el = document.getElementById(campo);
    if (!el) continue;
    if (el.type === 'checkbox') {
      el.checked = !!valor;
    } else {
      el.value = valor;
    }
  }
}

function getCSRFToken() {
  const name = 'csrftoken';
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    cookie = cookie.trim();
    if (cookie.startsWith(name + '=')) {
      return cookie.substring(name.length + 1);
    }
  }
  // Alternativamente, buscar en el meta
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.content : '';
}

function onBusquedaFinalizada() {
  restaurarFiltros();
  // Ocultar spinner/mensaje
}

window.minimizarFiltros = minimizarFiltros;
window.restaurarFiltros = restaurarFiltros;
window.onBuscarClick = onBuscarClick;
window.onBusquedaFinalizada = onBusquedaFinalizada;
