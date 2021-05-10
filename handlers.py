from datetime import datetime
import re
import requests
import settings
from generate_ticket import generate_ticket

re_city = re.compile(r'^[а-яА-Я -]{3,30}$')
re_city_and_iata = re.compile(r'(\d+).\s([А-Яа-я- .()]+)\s([(A-Z)]+)')
re_date = re.compile(r'^(19|20)\d\d([- /.])(0[1-9]|1[012])\2(0[1-9]|[12][0-9]|3[01])$')
re_flight_number = re.compile(r'\w{2}\s[\d]{1,4}')
re_fio = re.compile(r'^[а-яА-Я ]{3,50}$')
re_phone = re.compile(r'^\+?\d{1,3}?[- .]?\(?(?:\d{2,3})\)?[- .]?\d\d\d[- .]?\d\d\d\d$')


def schedule(context):
    url = f'https://api.rasp.yandex.net/v3.0/search/?' \
          f'apikey={settings.YANDEX_KEY}&format=json&system=iata&' \
          f'from={context["iata_city_from"]}&to={context["iata_city_to"]}&lang=ru_RU&date={context["date"]}&' \
          f'transport_types=plane'
    response = requests.get(url).json()
    context['schedule'] = ''
    for data, i in zip(response['segments'], range(1, 6)):
        from_to = data['thread']['short_title']
        arrival = data['arrival']
        departure = data['departure']
        number = data['thread']['number']
        context['schedule'] += f'{i}. {from_to}\nПрибытие: {arrival}\nОтправление: {departure}\nНомер рейса: {number}\n'
    if context['schedule']:
        return True
    else:
        return 'failure_text_2'


def check_flight_between_cities(context):
    country_to_iata_url = f'https://api.rasp.yandex.net/v3.0/search/?' \
                          f'apikey={settings.YANDEX_KEY}&format=json&system=iata&' \
                          f'from={context["iata_city_from"]}&to={context["iata_city_to"]}&' \
                          f'lang=ru_RU&transport_types=plane'
    country_to_iata = requests.get(country_to_iata_url).json()
    if country_to_iata['segments']:
        return True
    else:
        return 'failure_additional_function'


def from_city_handler(text, context):
    match = re.match(re_city, text)
    if match:
        url = f'http://autocomplete.travelpayouts.com/places2?term={text}&locale=ru&types[]=city'
        response = requests.get(url).json()
        if len(response) == 0:
            return 'failure_text_1'
        elif len(response) == 1:
            for data in response:
                context['iata_city_from'] = data['code']
                context['city_from'] = data['name']
            return True
        else:
            context['city_from'] = ''
            for i, data in enumerate(response):
                context['city_from'] += f'{i + 1}. {data["name"]} ({data["code"]})\n'
            return 'failure_text_2'
    elif text.isdigit():
        find_city_and_iata = re.findall(re_city_and_iata, context['city_from'])
        if 0 <= int(text) - 1 < len(find_city_and_iata):
            city_and_iata = [city for city in find_city_and_iata if city[0] == text]
            context['city_from'] = city_and_iata[0][1]
            context['iata_city_from'] = city_and_iata[0][2][1:-1]
            return True
        else:
            return 'failure_text_2'
    else:
        return 'failure_text_1'


def city_to_handler(text, context):
    match = re.match(re_city, text)
    if match:
        url = f'http://autocomplete.travelpayouts.com/places2?term={text}&locale=ru&types[]=city'
        response = requests.get(url).json()
        if len(response) == 0:
            return 'failure_text_1'
        elif len(response) == 1:
            for data in response:
                context['iata_city_to'] = data['code']
                context['city_to'] = data['name']
            return True
        else:
            context['city_to'] = ''
            for i, data in enumerate(response):
                if i > 10:
                    break
                context['city_to'] += f'{i + 1}. {data["name"]} ({data["code"]})\n'
            return 'failure_text_2'
    elif text.isdigit():
        find_city_and_iata = re.findall(re_city_and_iata, context['city_to'])
        if 0 <= int(text) - 1 < len(find_city_and_iata):
            city_and_iata = [city for city in find_city_and_iata if city[0] == text]
            context['city_to'] = city_and_iata[0][1]
            context['iata_city_to'] = city_and_iata[0][2][1:-1]
            return True
        else:
            return 'failure_text_2'
    else:
        return 'failure_text_1'


def date_handler(text, context):
    match = re.match(re_date, text)
    try:
        if match and datetime.strptime(text, '%Y-%m-%d').date() >= datetime.today().date():
            context['date'] = text
            return True
        else:
            return 'failure_text_1'
    except ValueError:
        return 'failure_text_1'


def schedule_handler(text, context):
    if text in '12345':
        flight_number = re.findall(re_flight_number, context['schedule'])
        context['flight_number'] = flight_number[int(text) - 1]
        context.pop('schedule')
        return True
    else:
        return 'failure_text_1'


def seats_handler(text, context):
    if text in '12345':
        context['seats'] = text
        return True
    else:
        return 'failure_text_1'


def comment_handler(text, context):
    if 0 <= len(text) < 500:
        context['comment'] = text
        return True
    else:
        return 'failure_text_1'


def confirm_handler(text, context):
    if text.lower() in 'да, yes, ага, yeap, yep':
        return True
    elif text.lower() in 'нет, no, не, неа, nope':
        return 'failure_text_2'
    else:
        return 'failure_text_1'


def phone_handler(text, context):
    match = re.match(re_phone, text)
    if match:
        context['phone'] = text
        return True
    else:
        return 'failure_text_1'


def fio_handler(text, context):
    match = re.match(re_fio, text)
    if match:
        context['fio'] = text
        return True
    else:
        return 'failure_text_1'


def generate_ticket_handler(context):
    return generate_ticket(city_from=context['city_from'],
                           city_to=context['city_to'],
                           date=context['date'],
                           flight_number=context['flight_number'],
                           fio=context['fio'])
