import time, datetime
from util import InstanceSheetNames, DepartsColumnNames, ArriveesColumnNames, CorrespondancesColumnNames
from lecture_donnees import (DATA_DICT, DEPARTS, ARRIVEES, get_first_day,
                             composition_train_arrivee, composition_train_depart)


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
    next_day_date = first_day + datetime.timedelta(days=1)
    next_day = datetime.datetime.strftime(next_day_date, '%d/%m/%Y')
    while next_day in DEPARTS[DepartsColumnNames.DEP_DATE]:
        all_days.append(next_day)
    return all_days

def get_data_for_given_period(start_day):
    sub_data_departs = set(DEPARTS[DEPARTS[DepartsColumnNames.DEP_DATE] == start_day].index)
    sub_data_arrivees = set(ARRIVEES[ARRIVEES[ArriveesColumnNames.ARR_DATE] == start_day].index)
    for index in sub_data_departs:
        dep_date = DEPARTS_DATE[index]
        dep_nb = DEPARTS_TR_NB[index]
        trains_arrivee_necessaires = composition_train_depart(DATA_DICT, (dep_date, dep_nb))
        for (arr_date, arr_nb) in trains_arrivee_necessaires:
            new_index = ARRIVEES[ARRIVEES[ArriveesColumnNames.ARR_DATE] == arr_date,
                                 ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER] == arr_nb].index[0]
            sub_data_arrivees.add(new_index)
    for index in sub_data_arrivees:
        arr_date = ARRIVEES_DATE[index]
        arr_nb = ARRIVEES_TR_NB[index]
        trains_depart_necessaires = composition_train_arrivee(DATA_DICT, (arr_date, arr_nb))
        for (dep_date, dep_nb) in trains_depart_necessaires:
            new_index = DEPARTS[DEPARTS[DepartsColumnNames.DEP_DATE, DepartsColumnNames.DEP_TRAIN_NUMBER] == (dep_date, dep_nb)].index[0]
            sub_data_arrivees.add(new_index)
    CORRESPONDANCES = DATA_DICT[InstanceSheetNames.SHEET_CORRESPONDANCES]
    sub_data_arrivees = list(sub_data_arrivees)
    sub_data_departs = list(sub_data_departs)
    sub_data_corresp = set(CORRESPONDANCES[(CORRESPONDANCES[CorrespondancesColumnNames.CORR_DEP_DATE] in DEPARTS_DATE[sub_data_departs]
                                        and CORRESPONDANCES[CorrespondancesColumnNames.CORR_DEP_TRAIN_NUMBER] in DEPARTS_TR_NB[sub_data_departs])
                                        or (CORRESPONDANCES[CorrespondancesColumnNames.CORR_ARR_DATE] in ARRIVEES_DATE[sub_data_arrivees]
                                        and CORRESPONDANCES[CorrespondancesColumnNames.CORR_ARR_TRAIN_NUMBER] in ARRIVEES_TR_NB[sub_data_arrivees])
                                        ].index)
    new_data = dict(DATA_DICT)
    new_data[InstanceSheetNames.SHEET_ARRIVEES] = ARRIVEES[sub_data_arrivees]
    new_data[InstanceSheetNames.SHEET_DEPARTS] = DEPARTS[sub_data_departs]
    new_data[InstanceSheetNames.SHEET_CORRESPONDANCES] = CORRESPONDANCES[sub_data_corresp]
    return new_data

days_list = get_all_days(DATA_DICT)
first_day = days_list[0]
first_day_data = get_data_for_given_period(first_day)
print(first_day_data)
# for new_day in days_list:
#     data = get_data_for_given_period(DATA_DICT, new_day)

