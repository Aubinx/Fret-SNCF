from datetime import datetime, timedelta
import numpy as np
from util import ArriveesColumnNames, DepartsColumnNames

from display_tools.display_track_occupation import displays_track_occupation

def generate_worksites(extrema):
    start_date, end_date = extrema
    delta_time = end_date - start_date
    delta_time = int(delta_time.total_seconds() // 60)
    _reception = np.zeros(delta_time)
    _formation = np.zeros(delta_time)
    _depart = np.zeros(delta_time)
    return(_reception, _formation, _depart)

def remplissage_voies(chantiers, solved_variables, arrivees, departs):
    reception, formation, depart = chantiers
    # Remplissage des voies pour les trains d'arrivée
    for index in arrivees.index:
        jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
        numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]

        # Chantier Reception
        creneau_arrivee = int(arrivees[ArriveesColumnNames.ARR_CRENEAU][index])
        creneau_depart = int(solved_variables[f"Train_ARR_{jour}_{numero}_DEB"].x) + 15

        reception[creneau_arrivee: creneau_depart] += 1

    for index in departs.index:
        jour = departs[DepartsColumnNames.DEP_DATE][index]
        numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]

        # Chantier Formation
        creneau_arrivee = int(solved_variables[f"min_DEB_{jour}_{numero}"].x)
        creneau_depart = int(solved_variables[f"Train_DEP_{jour}_{numero}_DEG"].x) +15
        formation[creneau_arrivee: creneau_depart] += 1

        # Chantier Départ
        creneau_arrivee = int(solved_variables[f"Train_DEP_{jour}_{numero}_DEG"].x)
        creneau_depart = int(departs[DepartsColumnNames.DEP_CRENEAU][index])
        depart[creneau_arrivee: creneau_depart] += 1

def rewriting_stats(chantiers, start_date):
    """
    Rewrites the occupation of worksites in a list of occupation and deltatimes
    """
    dict_stats = {}
    occupations_max = {}
    nom_chantiers = ('REC', 'FOR', 'DEP')
    for i, chantier in enumerate(chantiers):
        dates, occupation = [], []
        current_date, current_level, current_index = start_date, -1, 0
        for j, level in enumerate(chantier):
            if level != current_level:
                current_date += timedelta(minutes=j-current_index)
                current_index=j
                current_level = level
                dates.append(current_date)
                occupation.append(level)
        dates.append(start_date+timedelta(minutes=len(chantier)))

        occupations_max[nom_chantiers[i]] = max(occupation)
        dict_stats[nom_chantiers[i]] = (dates, occupation)

    return dict_stats, occupations_max


def full_process_stats(extrema, solved_variables, arrivees, departs, nombre_voies):
    """ Executes the full computation of stats """
    earliest, lastest = extrema
    day, month, year = earliest.split('/')
    earliest = datetime(int(year), int(month), int(day), hour=0, minute=0)
    day, month, year = lastest.split('/')
    lastest = datetime(int(year), int(month), int(day), hour=23, minute=59)
    worksites = generate_worksites((earliest, lastest))

    remplissage_voies(worksites, solved_variables, arrivees, departs)
    dictionnaire, occupations_max = rewriting_stats(worksites, earliest)

    #print(dictionnaire)
    displays_track_occupation(earliest, lastest, dictionnaire, occupations_max, nombre_voies)
