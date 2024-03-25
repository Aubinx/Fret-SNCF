import time, datetime
import model_jalon2
from util import DepartsColumnNames, ArriveesColumnNames
from lecture_donnees import DATA_DICT, DEPARTS, ARRIVEES, get_first_day

SEP_HORAIRE = ["5:00-13:00", "13:00-21:00","21:00-5:00"]

ARRIVEES_DATE = ARRIVEES[ArriveesColumnNames.ARR_DATE]
ARRIVEES_TIME = ARRIVEES[ArriveesColumnNames.ARR_HOUR]
ARRIVEES_TR_NB = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER]
ARRIVEES_CRENEAUX = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU]
DEPARTS_DATE = DEPARTS[DepartsColumnNames.DEP_DATE]
DEPARTS_TIME = DEPARTS[DepartsColumnNames.DEP_HOUR]
DEPARTS_TR_NB = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER]
DEPARTS_CRENEAUX = DEPARTS[DepartsColumnNames.DEP_CRENEAU]

def get_all_days(data):
    """Renvoie la liste de tous les jours présents dans les données sous forme de `str`"""
    first_day = get_first_day(data)
    all_days = [first_day]
    next_day_date = first_day + datetime.deltatime(days=1)
    next_day = datetime.datetime.strftime(next_day_date, '%d/%m/%Y')
    while next_day in DEPARTS[DepartsColumnNames.DEP_DATE]:
        all_days.append(next_day)
    return all_days

def get_post_bounds(day, post):
    """Renvoie les horaires de début et de fin de chaque quart sous forme de `datetime`"""
    assert post in SEP_HORAIRE
    day1 = day
    day2 = day
    if post == SEP_HORAIRE[2]: # Changement de jour pendant le poste
        day2 = day + datetime.deltatime(days=1)
    hour1, hour2 = post.split(sep="-")
    hour1 = datetime.strptime(hour1, '%H:%M')
    hour2 = datetime.strptime(hour2, '%H:%M')
    return (datetime.datetime(years=day1.year, month=day1.month, day=day1.day, hour=hour1.hour, minute=hour1.minute), 
           datetime.datetime(years=day2.year, month=day2.month, day=day2.day, hour=hour2.hour, minute=hour2.minute))

def get_data_for_given_period(start_day, post):
    start_time, end_time = get_post_bounds(start_day, post)
    keep_indexes = []
    for index in DEPARTS.index:
        dep_date = DEPARTS_DATE[index]
        dep_time = DEPARTS_TIME[index]


days_list = get_all_days(DATA_DICT)
for new_day in days_list:
    for new_post in SEP_HORAIRE:
        data = get_data_for_given_period(DATA_DICT, new_day, new_post)

