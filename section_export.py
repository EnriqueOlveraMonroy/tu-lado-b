"""Download a PNG of the current section locally in the browser."""
from pathlib import Path
from functools import lru_cache
import json
import streamlit.components.v1 as components


@lru_cache(maxsize=1)
def capture_library():
    return (Path(__file__).parent / 'assets' / 'vendor' / 'html2canvas.min.js').read_text(encoding='utf-8')


def download_section(title, slug, video=False):
    config = json.dumps(dict(title=title, slug=slug, video=video), ensure_ascii=True)
    document = '''<!doctype html><html lang="es-MX"><head><meta charset="utf-8">
<style>body{margin:0;font:14px Arial,sans-serif;color:#bed0c3;background:transparent}button,a{display:inline-block;background:#1ed760;color:#07150b;border:0;border-radius:24px;padding:12px 20px;font-weight:700;cursor:pointer;text-decoration:none}button:disabled{opacity:.6;cursor:wait}p{font-size:12px;margin:8px 0}a{margin-left:8px}</style></head><body>
<button id="download">Descargar imagen de esta sección</button><a id="save" style="display:none">Guardar PNG</a>
<p id="status" role="status">Incluye el año elegido y el contenido visible. Abre los detalles que quieras incluir.</p>
<script>LIBRARY</script><script>
const config = CONFIG;
const button = document.getElementById('download');
const status = document.getElementById('status');
const save = document.getElementById('save');
let previousUrl;
button.onclick = async () => {
  button.disabled = true;
  save.style.display = 'none';
  status.textContent = 'Preparando la imagen…';
  try {
    const host = window.frameElement;
    const doc = host.ownerDocument;
    const target = config.video ? doc.querySelector('.st-key-video_report') : host.closest('[role="tabpanel"]');
    if (!target) throw new Error('No se encontró la sección. Recarga la página e inténtalo de nuevo.');
    await doc.fonts.ready;
    await Promise.all(Array.from(target.querySelectorAll('img')).map(img => img.decode().catch(()=>{})));
    const width = Math.ceil(target.getBoundingClientRect().width);
    const height = Math.ceil(target.scrollHeight);
    // Keep very long reports within common browser canvas limits.
    const scale = Math.min(2, 15000/(height+120), Math.sqrt(24000000/(width*(height+120))));
    const canvas = await html2canvas(target, {
      backgroundColor: '#101412', scale, useCORS: true, logging:false,
      width, windowWidth:doc.defaultView.innerWidth,
      ignoreElements: el => el.tagName === 'IFRAME' || (el.getAttribute('data-testid') === 'stElementContainer' && el.querySelector('iframe')) || el.getAttribute('data-testid') === 'stDownloadButton',
      onclone: async cloned => {
        const style=cloned.createElement('style');
        style.textContent='[role=tabpanel] *,.st-key-video_report *{font-family:Arial,sans-serif !important;letter-spacing:normal !important} details:not([open]) > :not(summary){display:none !important} [data-testid="stIconMaterial"]{visibility:hidden !important}';
        cloned.head.appendChild(style);
        await cloned.fonts.ready;
        cloned.querySelectorAll('[data-testid="stElementToolbar"]').forEach(el=>el.style.display='none');
      }
    });
    const output = document.createElement('canvas');
    const header = Math.ceil(110*scale);
    output.width = canvas.width; output.height = canvas.height+header;
    const ctx = output.getContext('2d');
    ctx.fillStyle='#101412';ctx.fillRect(0,0,output.width,output.height);
    ctx.fillStyle='#1ed760';ctx.font=`bold ${26*scale}px Arial`;
    ctx.fillText('TU LADO B',24*scale,36*scale);
    ctx.fillStyle='#f5f7f5';ctx.font=`${20*scale}px Arial`;
    ctx.fillText(config.title,24*scale,70*scale);
    ctx.drawImage(canvas,0,header);
    const blob = await new Promise(resolve=>output.toBlob(resolve,'image/png'));
    if (!blob) throw new Error('La imagen es demasiado grande. Cierra algunos detalles e inténtalo de nuevo.');
    if (previousUrl) URL.revokeObjectURL(previousUrl);
    previousUrl=URL.createObjectURL(blob);
    save.href=previousUrl;save.download=`tu-lado-b-${config.slug}.png`;save.style.display='inline-block';
    save.click();
    status.textContent='Imagen lista. Si la descarga no comenzó, pulsa Guardar PNG. Las tablas incluyen las filas visibles.';
  } catch(error) {
    status.textContent='No se pudo crear la imagen. '+error.message;
  } finally { button.disabled=false; }
};
</script></body></html>'''
    document = document.replace('LIBRARY', capture_library().replace('</script', '<\\/script')).replace('CONFIG', config)
    components.html(document, height=105, scrolling=False)
