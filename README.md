# Vk chat bot
Bot follow scenario for ordering tickets through vk.com.  

**Bot supports commands:**
- '/t', '/ticket', 'заказ', 'регистрация', '1'  — start scenario;
- '/h', '/help', 'помощь', '2' — instruction about the work of the bot.

**Script steps:**  
1. Entering the city of departure. Checking a city using regular expression, suggest a city where we can fly
2. Entering the destination city. Checking a city using regular expression, suggest a city where we can fly  
        * If there is no flight between the selected cities, we text about it and complete the scenario.
3. Entering the date: we ask the user for the departure date in the YYYY-mm-dd format.
4. Selecting a flight. With the help of the dispatcher, we offer 5 flights closest to the selected date, 
        indicating their numbers and ask enter the number you like.
5. Specify the number of places (from 1 to 5).
6. Suggest writing a comment in any form.
7. Clarify the entered data.
8. Request a phone number.
9. Inform user that he will be contacted by the entered number.

If a command (/ ticket or / help) is entered during a script, the script stops and the command is executed.
## What used?
Pytnon:
[pytnon 3.8.5](https://www.python.org/downloads/release/python-385/)  

APIs:
- https://avatars.dicebear.com API for creating a unique user avatar
- Yandex API for getting flight schedules and checking for flights between cities
- Travelpayouts API for autocomplete city if the user made a mistake or did not enter it completely 

Libs:  
- vk_api (wrapper vk.com API)
- requests
- Pillow
- cairosvg
- re
- unittest
- logging
- coverage
- pony ORM
## Installation
1. Make dir and jump into it  
`$mkdir vk_chat_bot && cd vk_chat_bot`
3. Clone repository  
`git clone https://github.com/toohottostop/vk_chat_bot.git`
5. Install virtual environment package  
`$sudo apt install python3-virtualenv`    
Set your virtual environment package  
`$python3 -m virtualenv <name_of_virtualenv>`  
Activate virtual environment  
`$source <name_of_virtualenv>/bin/activate`
4. Install requirements  
`pip install -r requirements.txt`
6. Set your vk token - `TOKEN`, vk group id - `GROUP_ID`, yandex API token - `YANDEX_KEY` in `settings.py`
7. Set your data base in `settings.py`(in project I used Postgres, but you can choose [another one](http://docs.peewee-orm.com/en/latest/peewee/database.html#initializing-a-database))  
`DB_CONFIG = dict(provider='',
                 user='',
                 password='',
                 host='',
                 database=''
                 )`
7. Run tests `python -m unittest tests.py`
## How to use  
`python chat_bot.py`
## Tests coverage
`chat_bot.py`- 72%
