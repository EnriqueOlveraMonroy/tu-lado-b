from io import BytesIO
import pytest
from PIL import Image, ImageOps
from archetype_lore import LORE, avatar_path
from archetypes import ARCHETYPES
from wrapped import generate_card, FORMATS
from test_wrapped import sample


@pytest.mark.parametrize('name',list(LORE))
@pytest.mark.parametrize('format_name',list(FORMATS))
def test_avatar_is_embedded_in_download(name,format_name):
    metrics,_ = sample()
    assert name in ARCHETYPES
    assert len(ARCHETYPES[name]['descripcion']) > 500
    assert avatar_path(name).is_file()
    card=Image.open(BytesIO(generate_card(metrics,{'arquetipo':name},'01/01/2024 — 19/09/2026',format_name)))
    size=280 if format_name.startswith('LinkedIn') else 430
    y=255 if size==280 else 280
    with Image.open(avatar_path(name)) as source:
        expected=ImageOps.fit(source.convert('RGB'),(size,size),method=Image.Resampling.LANCZOS)
    assert card.getpixel((70+size//2,y+size//2)) == expected.getpixel((size//2,size//2))
    assert card.size == FORMATS[format_name]
