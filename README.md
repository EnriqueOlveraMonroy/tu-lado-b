# Tu Lado B
Los hábitos y obsesiones que tu historial esconde.

Aplicación Streamlit para explorar historiales ampliados de Spotify, con cuatro usuarios de ejemplo autorizados para publicación. Incluye audio, video, filtros por año, arquetipos, hallazgos, gráficas y descargas PNG.

## Ejecutar
Requiere Python 3.12 o posterior.

    pip install -r requirements.txt
    python -m streamlit run app.py

## Desplegar en Streamlit Community Cloud
Seleccionar el repositorio, la rama main y app.py. Usar Python 3.12. Las dependencias están en requirements.txt y packages.txt.

## Ejemplos
Los archivos públicos están en data/Usuario 1 a Usuario 4 como JSON comprimidos con gzip. La app los lee directamente. Se conservaron todas las filas y solo los campos necesarios para el análisis: no se incluyen IP, país de conexión, datos de cuenta, ZIP originales ni documentos adicionales. Los nombres Usuario 1 a 4 son etiquetas, no una garantía de anonimato del historial.

example_manifest.json enumera los archivos y sus cantidades de registros. Solo se carga el usuario elegido. El perfil 4 tiene mayor costo de procesamiento.

## Archivos propios
Los archivos que carga cada visitante se procesan en el servidor, no se incorporan al repositorio ni a los ejemplos. La app no escribe esos archivos en disco. El procesamiento de audio utiliza una caché en memoria con vencimiento de 30 minutos y un máximo de 8 entradas; las sesiones activas también conservan información en memoria.

## Pruebas
    python -m pytest -q

Proyecto independiente, sin afiliación con Spotify. Las descripciones de los arquetipos son narrativas, no evaluaciones psicológicas.
