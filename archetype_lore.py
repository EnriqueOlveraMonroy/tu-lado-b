"""Identidades visuales y relatos simbólicos; no alteran el scoring."""
from pathlib import Path

LORE = {
    'El Fiel de Culto': dict(asset='fiel.png', color='#B5F56B', symbol='El guardián del eco',
        essence='Custodias las voces que te marcaron. Cada regreso enciende una llama que el tiempo no apaga.',
        story='En tu santuario sonoro hay nombres grabados en piedra. No necesitas recorrer todo el firmamento para encontrar una estrella: vuelves a aquellas cuya luz reconoces. Cada canción de un artista querido abre otra puerta del mismo templo, y una sesión puede convertirse en una peregrinación por su universo. Tu magia está en la profundidad del vínculo, en descubrir pequeños detalles donde otros solo oyen una repetición.',
        gift='Memoria y devoción: convertir una discografía en un territorio familiar.',
        shadow='El refugio puede volverse frontera cuando ninguna voz nueva logra entrar.',
        ritual='Después de tu artista favorito, escucha una canción de alguien que nunca hayas elegido.',
        evidence='Concentración en un artista, rachas del mismo artista y menor diversidad relativa.'),
    'El Explorador Impaciente': dict(asset='explorador.png', color='#54D6CD', symbol='La brújula del relámpago',
        essence='Persigues el destello que aún no tiene nombre. Tu siguiente canción siempre parece esconder un portal.',
        story='Cruzas el mapa del sonido como quien persigue una tormenta: un fragmento basta para decidir si hay magia o si el viaje continúa. Tu brújula no apunta al norte, sino a la próxima sorpresa. Los saltos y las escuchas fugaces dibujan senderos veloces entre muchas voces. En este relato eres quien abre puertas, prueba umbrales y rara vez se queda inmóvil frente a un paisaje conocido.',
        gift='Curiosidad en movimiento: detectar conexiones y cambiar de rumbo sin solemnidad.',
        shadow='La búsqueda del próximo destello puede ocultar canciones que florecen lentamente.',
        ritual='Regala una escucha completa a una canción que normalmente saltarías.',
        evidence='Porcentaje de saltos, reproducciones fugaces y diversidad de artistas.'),
    'El Arquitecto de la Madrugada': dict(asset='arquitecto.png', color='#B7A6FF', symbol='El cartógrafo de la luna',
        essence='Cuando baja la luz, trazas constelaciones con canciones. La noche es el lienzo de tu universo sonoro.',
        story='Mientras el día recoge sus voces, tú levantas una ciudad invisible hecha de ritmos y ecos. Cada pista es una ventana iluminada; cada sesión nocturna, un puente entre estrellas. Tu historial sitúa una parte de la escucha bajo el cielo oscuro, y este arquetipo convierte ese horario en un paisaje: un taller lunar donde las canciones adquieren espacio y resonancia. El misterio pertenece al relato, no a una explicación de por qué estás despierto.',
        gift='Crear atmósferas: dar una identidad sonora a las horas menos transitadas.',
        shadow='Un mismo cielo puede esconder otros paisajes si toda la exploración sucede a la misma hora.',
        ritual='Lleva una canción de tu noche a una tarde y observa cómo cambia la experiencia.',
        evidence='Proporción de reproducciones en noche y madrugada según la zona horaria elegida.'),
    'El Coleccionista Ecléctico': dict(asset='coleccionista.png', color='#EC9FD8', symbol='El alquimista del prisma',
        essence='Reúnes voces como fragmentos de estrellas. Tu colección no busca un centro: inventa constelaciones.',
        story='Tu archivo es una cámara de cristales, y cada artista refracta una luz distinta. Ninguna voz reclama por mucho tiempo el trono: haces convivir universos y encuentras belleza en sus contrastes. La diversidad de nombres y una escucha repartida alimentan esta figura de alquimista, capaz de reunir piezas lejanas en una colección propia. No sabemos sus géneros por el historial; el prisma representa la variedad de artistas que sí aparece en tus datos.',
        gift='Amplitud: tender puentes entre muchas voces sin pedirles que se parezcan.',
        shadow='Acumular destellos puede dejar tesoros sin explorar en profundidad.',
        ritual='Elige un artista poco repetido de tu colección y escucha varias de sus canciones seguidas.',
        evidence='Entropía de artistas, baja concentración y proporción de artistas únicos.'),
    'El Ritualista Sereno': dict(asset='ritualista.png', color='#F5C77E', symbol='El custodio de la llama',
        essence='Dejas que cada sonido complete su círculo. Tu escucha es una llama que no necesita correr para iluminar.',
        story='En el centro de tu templo sonoro arde una luz constante. Las canciones reciben tiempo para desplegarse y los cambios bruscos aparecen con menos frecuencia. Pocos saltos, pocas escuchas fugaces y menor uso de reproducción aleatoria inspiran al custodio: alguien que, dentro de esta fábula, cuida la continuidad del viaje. Esa calma es una imagen poética de las señales de reproducción, no una afirmación sobre tu temperamento ni sobre quién eligió cada pista.',
        gift='Continuidad: permitir que una secuencia de canciones construya su propio espacio.',
        shadow='La costumbre puede conservar el fuego y, a la vez, repetir siempre el mismo paisaje.',
        ritual='Introduce una canción inesperada en tu próxima sesión y déjala llegar al final.',
        evidence='Pocos saltos, pocas reproducciones fugaces y menor uso de reproducción aleatoria.'),
}


def avatar_path(name):
    return Path(__file__).resolve().parent / 'assets' / 'archetypes' / LORE[name]['asset']


def description(name):
    item = LORE[name]
    return f"{item['story']}\n\nDon: {item['gift']}\n\nSombra: {item['shadow']}\n\nRitual: {item['ritual']}"
