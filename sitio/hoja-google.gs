/**
 * Recibe los datos que dejan las clientas en la página de Isabella (el juego de premios,
 * el test de rutina y el club de cumpleaños) y los anota en una hoja de Google.
 * Gratis. La libreta de clientas los trae con:
 *   python3 clientas/libreta.py sincronizar "<enlace de la hoja>"
 *
 * Cómo se instala (una sola vez): ver sitio/README.md.
 */
const COLUMNAS = ['fecha', 'nombre', 'whatsapp', 'cumpleanos', 'piel', 'interes', 'mensaje',
                  'etiquetas', 'origen', 'premio', 'codigo'];

function doPost(e) {
  const hoja = SpreadsheetApp.getActiveSpreadsheet().getSheets()[0];
  if (hoja.getLastRow() === 0) hoja.appendRow(COLUMNAS);
  let d = {};
  try { d = JSON.parse(e.postData.contents); } catch (err) { d = e.parameter || {}; }
  // Solo texto corto, y nada que la hoja pueda tomar como fórmula.
  const limpio = v => String(v == null ? '' : v).replace(/^[=+\-@]/, "'$&").slice(0, 300);
  d.fecha = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
  hoja.appendRow(COLUMNAS.map(c => limpio(d[c])));
  return ContentService.createTextOutput('ok');
}
