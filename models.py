from pony.orm import Database, Required, Json
from settings import DB_CONFIG

db = Database()
db.bind(**DB_CONFIG)


class UserState(db.Entity):
    """User state in scenario"""
    user_id = Required(str, unique=True)
    scenario_name = Required(str)
    step_name = Required(str)
    context = Required(Json)


class Registration(db.Entity):
    """Request on registration"""
    city_from = Required(str)
    city_to = Required(str)
    date = Required(str)
    flight_number = Required(str)
    seats = Required(str)
    comment = Required(str)
    fio = Required(str)
    phone = Required(str)


db.generate_mapping(create_tables=True)
