import datetime
from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch, Mock
from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent
from chat_bot import VkBot
import settings
from generate_ticket import generate_ticket


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session:
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_EVENT = {'type': 'message_new', 'object': {
        'message': {'date': 1606661188, 'from_id': 11159140, 'id': 2419, 'out': 0, 'peer_id': 11159140, 'text': '/t',
                    'conversation_message_id': 2262, 'fwd_messages': [], 'important': False, 'random_id': 0,
                    'attachments': [], 'is_hidden': False},
        'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'], 'keyboard': True,
                        'inline_keyboard': True, 'carousel': False, 'lang_id': 0}}, 'group_id': 197969572,
                 'event_id': 'db09dc03d6c147953ace5b1db5df5639fe9dfc77'}

    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('chat_bot.vk_api.VkApi'):
            with patch('chat_bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                vk_bot = VkBot(token='', group_id='')
                vk_bot.on_event = Mock()
                vk_bot.event_message = Mock()
                vk_bot.run()
        vk_bot.on_event.assert_called()
        vk_bot.on_event.assert_any_call(event=obj)
        self.assertEqual(vk_bot.on_event.call_count, count)

    INPUTS = [
        'чушь муть',
        'привет',
        '/h',
        '/t',
        'москва',
        'екатеринбург',
        '2020-10-22',
        datetime.datetime.now().strftime('%Y-%m-%d'),
        '2',
        '2',
        'какой то комментарий',
        'да',
        '+79127693560',
        'Иван Иванов',
    ]
    flights = '1. Москва — Екатеринбург\n' \
              'Прибытие: 2020-11-20T04:45:00+05:00\n' \
              'Отправление: 2020-11-20T00:15:00+03:00\n' \
              'Номер рейса: WZ 421\n' \
              '2. Москва — Екатеринбург\n' \
              'Прибытие: 2020-11-20T04:55:00+05:00\n' \
              'Отправление: 2020-11-20T00:25:00+03:00\n' \
              'Номер рейса: SU 1408\n' \
              '3. Москва — Екатеринбург\n' \
              'Прибытие: 2020-11-20T13:55:00+05:00\n' \
              'Отправление: 2020-11-20T09:20:00+03:00\n' \
              'Номер рейса: SU 1412\n' \
              '4. Москва — Екатеринбург\n' \
              'Прибытие: 2020-11-20T14:15:00+05:00\n' \
              'Отправление: 2020-11-20T10:00:00+03:00\n' \
              'Номер рейса: U6 261\n' \
              '5. Москва — Екатеринбург\n' \
              'Прибытие: 2020-11-20T17:25:00+05:00\n' \
              'Отправление: 2020-11-20T12:50:00+03:00\n' \
              'Номер рейса: SU 1402\n'

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIO['registration']['steps']['step1']['text'],
        settings.SCENARIO['registration']['steps']['step2']['text'].format(city_from='Москва'),
        settings.SCENARIO['registration']['steps']['step3']['text'].format(city_to='Екатеринбург'),
        settings.SCENARIO['registration']['steps']['step3']['failure_text_1'],
        settings.SCENARIO['registration']['steps']['step4']['text'].format(schedule=flights),
        settings.SCENARIO['registration']['steps']['step5']['text'].format(flight_number='SU 1408',
                                                                           city_from='Москва',
                                                                           city_to='Екатеринбург'),
        settings.SCENARIO['registration']['steps']['step6']['text'].format(seats='2'),
        settings.SCENARIO['registration']['steps']['step7']['text'],
        settings.SCENARIO['registration']['steps']['step8']['text'],
        settings.SCENARIO['registration']['steps']['step9']['text'],
        settings.SCENARIO['registration']['steps']['step10']['text'].format(phone='+79127693560'),
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock

        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))

        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        def schedule_mock(context):
            context['schedule'] = self.flights
            return True

        with patch('chat_bot.VkBotLongPoll', return_value=long_poller_mock):
            with patch('handlers.schedule', side_effect=schedule_mock):
                bot = VkBot('', '')
                bot.api = api_mock
                with patch('chat_bot.VkBot.send_image', return_value=None):
                    bot.run()

        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        self.assertEqual(real_outputs, self.EXPECTED_OUTPUTS)

    def test_image_generation(self):
        with open('files/avatar.svg', 'rb') as avatar_file:
            avatar_mock = Mock()
            avatar_mock.content = avatar_file.read()
        with patch('generate_ticket.requests.get', return_value=avatar_mock):
            avatar_mock.status_code = 200
            ticket_file = generate_ticket('Moscow', 'Yekaterinburg', '2020-11-30', 'SU 1408', 'Иван Иванов')
            ticket_bytes = ticket_file.read()
        with open('files/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        self.assertEqual(ticket_bytes, expected_bytes)
