/**
 * PROXY DE IA PARA "CONTEXTO DEL CLIENTE" — SOLART
 * ------------------------------------------------
 * Recibe el historial de una negociación desde app.solart.mx y le pide a
 * Claude (Anthropic) un resumen ejecutivo. La llave del API vive AQUÍ
 * (Propiedades del script), nunca en el HTML público.
 *
 * CÓMO DESPLEGARLO (5 min):
 * 1. script.google.com → Nuevo proyecto → pega este archivo completo.
 * 2. ⚙️ Configuración del proyecto → Propiedades del script → Agregar:
 *      Propiedad: ANTHROPIC_API_KEY   Valor: (tu llave sk-ant-...)
 * 3. Implementar → Nueva implementación → Aplicación web:
 *      Ejecutar como: Yo · Acceso: Cualquier persona
 * 4. Copia la URL (termina en /exec) y pásasela a Claude para ponerla
 *    en IA_PROXY_URL de front-dashboard.html.
 */

function doPost(e) {
  try {
    var datos = JSON.parse(e.postData.contents || '{}');
    var contexto = (datos.contexto || '').slice(0, 24000);
    if (!contexto) return _json({ error: 'Sin contexto' });

    var apiKey = PropertiesService.getScriptProperties().getProperty('ANTHROPIC_API_KEY');
    if (!apiKey) return _json({ error: 'Falta ANTHROPIC_API_KEY en Propiedades del script' });

    var prompt = 'Eres el asistente comercial de SOLART, empresa mexicana de energía solar. ' +
      'Te paso el historial completo de una negociación del CRM. Redacta un resumen ejecutivo ' +
      'en español, máximo 150 palabras, dirigido al vendedor o a un director que la abre por primera vez. ' +
      'Estructura: 1) Quién es el cliente y qué se le propone (monto, sistema). ' +
      '2) En qué va y cuánto lleva. 3) Objeciones o riesgos detectados en las conversaciones ' +
      '(precio, competencia, tiempos). 4) Siguiente paso recomendado. ' +
      'Sé directo y concreto, sin rodeos ni tecnicismos.\n\n' + contexto;

    var resp = UrlFetchApp.fetch('https://api.anthropic.com/v1/messages', {
      method: 'post',
      contentType: 'application/json',
      headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01' },
      payload: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 600,
        messages: [{ role: 'user', content: prompt }]
      }),
      muteHttpExceptions: true
    });

    var cuerpo = JSON.parse(resp.getContentText());
    if (resp.getResponseCode() !== 200) {
      return _json({ error: (cuerpo.error && cuerpo.error.message) || 'Error del API (' + resp.getResponseCode() + ')' });
    }
    var texto = (cuerpo.content && cuerpo.content[0] && cuerpo.content[0].text) || '';
    return _json({ resumen: texto });
  } catch (err) {
    return _json({ error: String(err) });
  }
}

function _json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
