import base64
import os
from io import BytesIO

import httpx
from PIL import Image, ImageDraw, ImageFont

from .. import static

fontpath = os.path.join(static, 'SourceHanSansSC-Bold.otf')


def draw_text(img_pil: Image.Image, text: str, offset_x: float):
    draw = ImageDraw.Draw(img_pil)
    font = ImageFont.truetype(fontpath, 48)
    width, height = draw.textsize(text, font)
    x = 5
    if width > 390:
        font = ImageFont.truetype(fontpath, int(390 * 48 / width))
        width, height = draw.textsize(text, font)
    else:
        x = int((400 - width) / 2)
    draw.rectangle((x + offset_x - 2, 360, x + 2 + width + offset_x, 360 + height * 1.2), fill=(0, 0, 0, 255))
    draw.text((x + offset_x, 360), text, font=font, fill=(255, 255, 255, 255))


def text_to_image(text: str) -> Image.Image:
    font = ImageFont.truetype(fontpath, 24)
    padding = 10
    margin = 4
    lines = text.strip().split('\n')
    max_width = 0
    for line in lines:
        l, t, r, b = font.getbbox(text)
        max_width = max(max_width, r)
    wa = max_width + padding * 2
    ha = b * len(lines) + margin * (len(lines) - 1) + padding * 2
    im = Image.new('RGB', (wa, ha), color=(255, 255, 255))
    draw = ImageDraw.Draw(im)
    for index, line in enumerate(lines):
        draw.text((padding, padding + index * (margin + b)), line, font=font, fill=(0, 0, 0))
    return im


def to_bytes_io(text: str) -> BytesIO:
    bio = BytesIO()
    text_to_image(text).save(bio, format='PNG')
    bio.seek(0)

    return bio


def image_to_base64(img: Image.Image, format='PNG') -> str:
    output_buffer = BytesIO()
    img.save(output_buffer, format)
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode()
    return 'base64://' + base64_str

def file_to_base64(path: str) -> str:
    with open(path, 'rb') as file:
        base64_str = base64.b64encode(file.read()).decode()
    return 'base64://' + base64_str

def image_to_bytesio(img: Image.Image, format_='PNG') -> BytesIO:
    bio = BytesIO()
    img.save(bio, format_)
    bio.seek(0)
    return bio


async def get_user_logo(qq: int) -> Image.Image:
    async with httpx.AsyncClient() as client:
        res = await client.get(f'http://q1.qlogo.cn/g?b=qq&nk={qq}&s=100')
        return Image.open(BytesIO(res.content))
