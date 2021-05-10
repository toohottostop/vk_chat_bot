from io import BytesIO
import requests
from PIL import Image, ImageDraw, ImageFont
from cairosvg import svg2png


TEMPLATE_PATH = 'files/ticket-base.png'
FONT_PATH = 'files/Roboto-Regular.ttf'
FONT_SIZE = 20
BLACK_COLOR = (0, 0, 0)

AIRLINES_OFFSET = (262, 190)
CITY_FROM_OFFSET = (45, 189)
CITY_TO_OFFSET = (45, 255)
DATE_OFFSET = (262, 254)
FLIGHT_NUMBER_OFFSET = (45, 319)
FIO_OFFSET = (45, 118)

AVATAR_OFFSET = (350, 80)
AVATAR_SCALE = 4
AVATAR_BACKGROUND_COLOR = '#ffffff'


def generate_ticket(city_from, city_to, date, flight_number, fio):
    with open(TEMPLATE_PATH, 'rb') as image_file:
        image = Image.open(image_file).convert('RGB')
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

        draw = ImageDraw.Draw(image)
        draw.text(AIRLINES_OFFSET, 'ShitHappen Airlines', font=font, fill=BLACK_COLOR)
        draw.text(CITY_FROM_OFFSET, city_from, font=font, fill=BLACK_COLOR)
        draw.text(CITY_TO_OFFSET, city_to, font=font, fill=BLACK_COLOR)
        draw.text(DATE_OFFSET, date, font=font, fill=BLACK_COLOR)
        draw.text(FLIGHT_NUMBER_OFFSET, flight_number, font=font, fill=BLACK_COLOR)
        draw.text(FIO_OFFSET, fio, font=font, fill=BLACK_COLOR)

        response = requests.get(f'https://avatars.dicebear.com/api/male/{fio}.svg')
        if response.status_code == 200:
            avatar_file_like = BytesIO()
            svg2png(bytestring=response.content, write_to=avatar_file_like, scale=AVATAR_SCALE,
                    background_color=AVATAR_BACKGROUND_COLOR)
            avatar = Image.open(avatar_file_like)
            image.paste(avatar, AVATAR_OFFSET)
            # image.save('files/ticket_example.png')
            temp_file = BytesIO()

            image.save(temp_file, 'png')
            temp_file.seek(0)
            return temp_file
        else:
            return False
