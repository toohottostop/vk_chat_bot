import requests
from pony.orm import db_session
from models import UserState, Registration
try:
    import settings
except ImportError:
    exit('Copy settings and set token')
import handlers
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from log_config import configure_logging, log


class VkBot:
    """
    Scenario for ordering tickets through vk.com
    Use Python 3.8.5

    Using API:
    - travelpayouts: https://support.travelpayouts.com/hc/ru/articles/360002322572-API
    - yandex: https://yandex.ru/dev/rasp/doc/reference/schedule-point-point.html

    Bot supports commands:
    '/t', '/ticket', 'заказ', 'регистрация', '1'  — start scenario;
    '/h', '/help', 'помощь', '2' — instruction about the work of the bot.

    Script structure:
    Step 1. Entering the city of departure. Checking a city using regular expression, suggest a city where we can fly
    Step 2. Entering the destination city. Checking a city using regular expression, suggest a city where we can fly
        * If there is no flight between the selected cities, we text about it and complete the scenario.
    Step 3. Entering the date: we ask the user for the departure date in the YYYY-mm-dd format.
    Step 4. Selecting a flight. With the help of the dispatcher, we offer 5 flights closest to the selected date,
        indicating their numbers and ask enter the number you like.
    Step 5. Specify the number of places (from 1 to 5).
    Step 6. Suggest writing a comment in any form.
    Step 7. Clarify the entered data.
    Step 8. Request a phone number.
    Step 9. Inform user that he will be contacted by the entered number.

    If a command (/ ticket or / help) is entered during a script, the script stops and the command is executed.
    """

    def __init__(self, token, group_id):
        """
        :param token: secret token from group vk
        :param group_id: group id from group vk
        """
        self.token = token
        self.group_id = group_id
        self.vk = vk_api.VkApi(token=self.token)
        self.longpoll = VkBotLongPoll(self.vk, self.group_id)
        self.api = self.vk.get_api()

    def run(self):
        """Launch VkBot"""

        for event in self.longpoll.listen():
            try:
                self.on_event(event=event)
            except Exception:
                log.exception('Error in event')

    @db_session
    def on_event(self, event):
        """
        Sends a message back if it is text
        :param event: VKBotMessageEvent
        :return: None
        """

        if event.type != VkBotEventType.MESSAGE_NEW:
            log.info('Can\'t handle this event %s', event.type)
            return
        else:
            user_id = event.object.message['peer_id']
            text = event.object.message['text']
            state = UserState.get(user_id=str(user_id))
            if state is not None:
                if any(token in text.lower() for token in settings.RESTART_TOKENS):
                    state.delete()
                    self.send_text(settings.RESTART_TEXT, user_id)
                else:
                    self.continue_scenario(text=text, state=state, user_id=user_id)
            else:
                for intent in settings.INTENTS:
                    log.debug(f'User gets {intent}')
                    if any(token in text.lower() for token in intent['tokens']):
                        if intent['answer']:
                            self.send_text(intent['answer'], user_id)
                        else:
                            self.start_scenario(user_id, intent['scenario'], text)
                        break
                else:
                    self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=get_random_id(),
            peer_id=user_id
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f'photo{owner_id}_{media_id}'
        self.api.messages.send(
            attachment=attachment,
            random_id=get_random_id(),
            peer_id=user_id
        )

    def send_step(self, step, user_id, text, context, state):
        if 'additional_function' in step:
            additional_function = getattr(handlers, step['additional_function'])
            if additional_function(context) is not True:
                state.delete()
                self.send_text(step['failure_additional_function'].format(**context), user_id)
                return False
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            image = handler(context)
            if image:
                self.send_image(image, user_id)
            else:
                self.send_text(step['failure_image'].format(**context), user_id)

    def start_scenario(self, user_id, scenario_name, text):
        scenario = settings.SCENARIO[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={}, state=None)
        UserState(user_id=str(user_id), scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIO[state.scenario_name]['steps']
        step = steps[state.step_name]

        handler = getattr(handlers, step['handler'])
        handler_answer = handler(text, state.context)
        if handler_answer is True:
            next_step = steps[step['next_step']]
            if self.send_step(next_step, user_id, text, state.context, state) is False:
                return
            if next_step['next_step']:
                state.step_name = step['next_step']
            else:
                log.info(f'Зарегестрирован рейс: {state.context["flight_number"]}; '
                         f'кол-во мест: {state.context["seats"]}; '
                         f'комментарий: {state.context["comment"]}; '
                         f'тел. пользователя: {state.context["phone"]};'
                         f'ФИО: {state.context["fio"]}')
                Registration(
                    city_from=state.context['city_from'],
                    city_to=state.context['city_to'],
                    date=state.context['date'],
                    flight_number=state.context['flight_number'],
                    seats=state.context['seats'],
                    comment=state.context['comment'],
                    fio=state.context['fio'],
                    phone=state.context['phone']
                )
                state.delete()
        elif handler_answer == 'failure_text_1':
            self.send_text(step['failure_text_1'].format(**state.context), user_id)
        elif handler_answer == 'failure_text_2':
            self.send_text(step['failure_text_2'].format(**state.context), user_id)


if __name__ == '__main__':
    configure_logging()
    vk_bot = VkBot(token=settings.TOKEN, group_id=settings.GROUP_ID)
    vk_bot.run()
