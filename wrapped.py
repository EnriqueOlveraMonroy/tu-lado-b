"""Tarjetas de datos generadas localmente con Pillow; sin servicios externos."""
from io import BytesIO
from pathlib import Path
import os
import math

from PIL import Image, ImageDraw, ImageFont, ImageOps
from archetype_lore import LORE, avatar_path

FORMATS = {"Historia · 9:16": (1080, 1920), "LinkedIn · 4:5": (1080, 1350)}


def playful_phrase(metrics):
    """Frase determinista basada en una señal observada, sin inventar datos."""
    if metrics['skip_rate'] >= 0.4:
        return f"Saltas el {metrics['skip_rate']:.0%} de las canciones. Tu dedo tiene más cardio que tú."
    if metrics['top_artist_concentration'] >= 0.4:
        return f"El {metrics['top_artist_concentration']:.0%} de tus reproducciones es del mismo artista. Eso ya es una relación estable."
    if metrics['time_slot_distribution'].get('madrugada', 0) >= 0.25:
        return f"El {metrics['time_slot_distribution']['madrugada']:.0%} de tus reproducciones cae en madrugada. Dormir no entró en la lista."
    if metrics['unique_artists'] >= 30:
        return f"{metrics['unique_artists']:,} artistas. Elegir uno nunca fue parte del plan."
    return f"{metrics['n_plays']:,} reproducciones. Tu vida sí tiene banda sonora."


def _font(size, bold=False):
    # Bundled fonts may be supplied for deployment; local OS fonts work on Windows/Linux/macOS.
    candidates = [Path(__file__).parent / 'assets' / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
                  Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / ('arialbd.ttf' if bold else 'arial.ttf'),
                  Path('/usr/share/fonts/truetype/dejavu') / ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
                  Path('/System/Library/Fonts/Supplemental') / ('Arial Bold.ttf' if bold else 'Arial.ttf')]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def _wrap(draw, text, font, width):
    lines, line = [], ''
    for word in str(text).split():
        candidate = f'{line} {word}'.strip()
        if draw.textlength(candidate, font=font) <= width:
            line = candidate
            continue
        if line:
            lines.append(line)
        line = ''
        # Break even an unusually long unspaced artist name.
        for char in word:
            if line and draw.textlength(line + char, font=font) > width:
                lines.append(line)
                line = ''
            line += char
    if line:
        lines.append(line)
    return lines


def _text_box(draw, text, box, size, color, bold=False):
    x, y, width, height = box
    for chosen in range(size, 15, -1):
        font = _font(chosen, bold)
        lines = _wrap(draw, text, font, width)
        step = int(chosen * 1.22)
        if len(lines) * step <= height:
            break
    else:
        lines = lines[:max(1, int(height // step))]
        last = lines[-1]
        while last and draw.textlength(last + '…', font=font) > width:
            last = last[:-1]
        lines[-1] = last + '…'
    for index, line in enumerate(lines):
        draw.text((x, y + index * step), line, font=font, fill=color, anchor='lt')


def generate_card(metrics, result, period, format_name='Historia · 9:16'):
    """Devuelve bytes PNG de la misma tarjeta que se muestra en la vista previa."""
    width, height = FORMATS[format_name]
    image = Image.new('RGB', (width, height), '#101413')
    draw = ImageDraw.Draw(image)
    lore = LORE[result['arquetipo']]
    green, white, muted = lore['color'], '#F4F5EE', '#A6B2AB'
    compact = height == 1350
    # Restrained record-like arcs and a custom waveform, no remote assets.
    for radius in [230, 295, 360]:
        draw.ellipse((1040-radius, 40-radius, 1040+radius, 40+radius), outline='#263E2C', width=3)
    draw.rounded_rectangle((70, 65, 325, 109), radius=22, fill=green)
    draw.text((91, 76), 'MI ADN MUSICAL', font=_font(24, True), fill='#101413', anchor='lt')
    draw.text((70, 137), 'TU LADO B / MI RESUMEN', font=_font(24), fill=muted, anchor='lt')
    _text_box(draw, period, (70, 182, 940, 42), 25, muted)

    avatar_size = 280 if compact else 430
    avatar_y = 255 if compact else 280
    with Image.open(avatar_path(result['arquetipo'])) as original:
        portrait = ImageOps.fit(original.convert('RGB'), (avatar_size, avatar_size), method=Image.Resampling.LANCZOS)
    mask = Image.new('L', (avatar_size, avatar_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, avatar_size-1, avatar_size-1), radius=36, fill=255)
    image.paste(portrait, (70, avatar_y), mask)
    text_x = 380 if compact else 540
    draw.text((text_x, avatar_y+10), 'MI ARQUETIPO', font=_font(24), fill=green, anchor='lt')
    _text_box(draw, result['arquetipo'], (text_x, avatar_y+60, 1010-text_x, avatar_size-60), 68, white, True)
    _text_box(draw, lore['essence'], (70, 555 if compact else 755, 940, 85), 30 if compact else 34, muted)
    quote_y = 655 if compact else 870
    draw.line((70, quote_y, 70, quote_y+90), fill=green, width=5)
    _text_box(draw, playful_phrase(metrics), (96, quote_y, 900, 95), 31 if compact else 36, green)

    artists_y = 785 if compact else 1040
    draw.text((70, artists_y), 'MIS ARTISTAS MÁS ESCUCHADOS', font=_font(24), fill=muted, anchor='lt')
    artists = list(metrics['top_artists'])[:3]
    row_height = 78 if compact else 120
    for index, artist in enumerate(artists):
        y = artists_y + 48 + index * row_height
        draw.line((70, y, 1010, y), fill='#344137', width=2)
        draw.text((70, y+21), f'0{index+1}', font=_font(30), fill=green, anchor='lt')
        _text_box(draw, artist, (155, y+18, 845, row_height-26), 41 if compact else 48, white, True)
    if not artists:
        draw.text((70, artists_y+60), 'Sin artistas identificados', font=_font(32), fill=white, anchor='lt')

    stats_y = 1110 if compact else 1510
    draw.rounded_rectangle((70, stats_y-20, 1010, stats_y+100), radius=24, fill='#1D2921')
    for x, value, label in [(95, f"{metrics['total_minutes']:,.0f}", 'MINUTOS'),
                            (560, f"{metrics['unique_artists']:,}", 'ARTISTAS')]:
        _text_box(draw, value, (x, stats_y, 400, 58), 48, white, True)
        draw.text((x, stats_y+63), label, font=_font(22), fill=muted, anchor='lt')
    if not compact:
        for i in range(70):
            x = 76+i*13.5
            amplitude = 12+abs(math.sin(i*0.43)*math.cos(i*0.13))*65
            draw.line((x, 1750-amplitude/2, x, 1750+amplitude/2), fill=green, width=5)
    _text_box(draw, 'Los hábitos y obsesiones que tu historial esconde.', (70, height-78, 940, 30), 22, muted, True)
    draw.text((70, height-43), 'Proyecto independiente · No afiliado a Spotify', font=_font(18), fill=muted, anchor='lt')
    output = BytesIO()
    image.save(output, format='PNG', optimize=True)
    return output.getvalue()
