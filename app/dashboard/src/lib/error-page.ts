/**
 * Página de último recurso, servida cuando el renderizado del servidor falla
 * antes de que React pueda montar sus propias pantallas de error.
 *
 * No puede depender de la hoja de estilos ni de las fuentes del tablero,
 * porque el fallo puede ocurrir antes de que existan. Por eso los colores van
 * en hexadecimal en vez de los tokens en oklch, y la familia tipográfica cae
 * en la del sistema. Los valores replican los del tema oscuro del tablero.
 */
export function renderErrorPage(): string {
  return `<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <title>El tablero no pudo responder</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
      body {
        font: 15px/1.6 "IBM Plex Sans", system-ui, -apple-system, sans-serif;
        background: #191815;
        color: #e8e6e1;
        display: grid;
        place-items: center;
        min-height: 100vh;
        margin: 0;
        padding: 1.5rem;
      }
      .tarjeta {
        max-width: 28rem;
        width: 100%;
        background: #211f1d;
        border: 1px solid #3f3d39;
        padding: 2rem;
      }
      .rotulo {
        font-family: "IBM Plex Mono", ui-monospace, monospace;
        font-size: 0.6875rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #9b968d;
        margin: 0;
      }
      h1 { font-size: 1.25rem; font-weight: 600; margin: 0.75rem 0 0; }
      p.detalle { color: #9b968d; font-size: 0.875rem; margin: 0.5rem 0 0; }
      .acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 1.5rem; }
      a, button {
        display: inline-flex;
        align-items: center;
        min-height: 2.75rem;
        padding: 0 1rem;
        border: 1px solid #58544e;
        border-radius: 2px;
        background: transparent;
        color: inherit;
        font: inherit;
        font-size: 0.875rem;
        font-weight: 500;
        text-decoration: none;
        cursor: pointer;
      }
      a:hover, button:hover { background: #2b2926; }
    </style>
  </head>
  <body>
    <main class="tarjeta">
      <p class="rotulo">Error del servidor</p>
      <h1>El tablero no pudo responder</h1>
      <p class="detalle">
        La solicitud falló antes de poder construir la página. Los resultados publicados no se
        alteran por esto: reintentar vuelve a pedirlos.
      </p>
      <div class="acciones">
        <button onclick="location.reload()">Reintentar</button>
        <a href="/">Ir al tablero</a>
      </div>
    </main>
  </body>
</html>`;
}
