from datetime import datetime, timedelta
import numpy as np
from util import ArriveesColumnNames, DepartsColumnNames

import horaires
from display_tools.display_track_occupation import displays_track_occupation
from display_tools.display_human_tasks import display_human_tasks
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

def extract_infos_from_var_name(var_name):
    """ Retruns the name of the agent """
    items = var_name.split('_')

    jour, roulement, id_agent = int(items[2][4:]), int(items[1][4:]), int(items[3][2:])
    chantier, id_tache, train = items[5], items[6], f'{items[8]}_{items[9]}'
    return (jour, roulement, id_agent), (chantier, id_tache, train)


def date_code_to_datetime(date_code, ref_day):
    """ Converts the value of the variable to a proper datetime """
    date_tuple = horaires.entier_vers_triplet(int(date_code))
    day, hour, minute = date_tuple
    return ref_day.replace(hour=hour, minute=minute) + timedelta(days=day-1)


def full_process_human_tasks(solved_variables, ref_day):
    """ Executes the full computation of human tasks on one 3x8 work day """
    # "Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}"
    day, month, year = ref_day.split('/')
    ref_day = datetime(int(year), int(month), int(day))

    distinct_agents = {}
    for variable_name, variable in solved_variables.items():
        if 'Attr_roul' in variable_name:
            if variable.x==0:
                continue

            (_j, _r, _a), tache = extract_infos_from_var_name(variable_name)
            tache = (tache,
                     date_code_to_datetime(
                         solved_variables[f'H_roul{variable_name[9:]}'].x, ref_day))
            if _j not in distinct_agents:
                distinct_agents[_j]={_r:{_a:[tache]}}
            else:
                if _r not in distinct_agents[_j]:
                    distinct_agents[_j][_r]={_a:[tache]}
                else:
                    if _a not in distinct_agents[_j][_r]:
                        distinct_agents[_j][_r][_a] = [tache]
                    else:
                        distinct_agents[_j][_r][_a].append(tache)

    display_human_tasks(distinct_agents, ref_day)
