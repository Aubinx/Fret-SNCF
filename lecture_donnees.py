"""Module permettant de lire les données d'une instance de fret à partir de l'excel associé"""
# Modules
import os
import re
import time
import datetime
import pickle
import pandas as pd

from util import (InstanceSheetNames, ChantiersColumnNames, CorrespondancesColumnNames,
                 DepartsColumnNames, ArriveesColumnNames, MachinesColumnNames)
import horaires

# Chemin d'accès du fichier contenant l'instance
INSTANCE = "Instances/mini_instance"
INSTANCE_FILE = INSTANCE + ".xlsx"
INSTANCE_PICKLE_FILE = INSTANCE + ".pkl"

# Expressions régulières pour les différents formats de jours
# qui apparaissent à la lecture du fichier excel par pandas
re_jour = re.compile('\\d{2}/\\d{2}/\\d{4}') # jj/mm/aaaa
re_jourheure = re.compile('\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}') # aaaa-mm-jj HH:MM:SS
re_hour_min = re.compile('\\d{2}:\\d{2}') # HH:MM
re_hour_min_sec = re.compile('\\d{2}:\\d{2}:\\d{2}') # HH:MM:SS

## CHARGER L'INSTANCE
def load_instance(file_path) -> dict:
    """
    Charge l'instance du problème de la gare de fret donnée par `file_path` 
    et crée un dictionnaire qui stocke toutes le données pertinentes
    """
    print("Début de la lecture de données")
    all_dict = {}
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_CHANTIERS}")
    all_dict[InstanceSheetNames.SHEET_CHANTIERS] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_CHANTIERS, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_CHANTIERS}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_MACHINES}")
    all_dict[InstanceSheetNames.SHEET_MACHINES] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_MACHINES, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_MACHINES}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_ARRIVEES}")
    all_dict[InstanceSheetNames.SHEET_ARRIVEES] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_ARRIVEES, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_ARRIVEES}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_DEPARTS}")
    all_dict[InstanceSheetNames.SHEET_DEPARTS] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_DEPARTS, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_DEPARTS}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_CORRESPONDANCES}")
    all_dict[InstanceSheetNames.SHEET_CORRESPONDANCES] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_CORRESPONDANCES, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_CORRESPONDANCES}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_TACHES}")
    all_dict[InstanceSheetNames.SHEET_TACHES] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_TACHES, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_TACHES}")
    print(f"Lecture de la feuille : {InstanceSheetNames.SHEET_ROULEMENTS}")
    all_dict[InstanceSheetNames.SHEET_ROULEMENTS] = pd.read_excel(file_path,
                    sheet_name=InstanceSheetNames.SHEET_ROULEMENTS, dtype=str)
    print(f"Fin de la lecture de la feuille : {InstanceSheetNames.SHEET_ROULEMENTS}")
    print("Standardisation de tous les formats de dates")
    set_date_to_standard(all_dict)
    print("Ajout des creneaux")
    dates_to_creneaux(all_dict)
    return all_dict

def get_first_day(data):
    """
    Recherche dans l'instance `data` et renvoie le premier jour.
    Particulièrement utile pour transformer les couples (jour, heure) d'un train
    en un créneau stocké sur un entier tel qu'utilisé dans le module `horaires.py`.
    """
    first_day = datetime.date.max
    for _, row in data[InstanceSheetNames.SHEET_ARRIVEES].iterrows():
        jour = datetime.datetime.strptime(row[ArriveesColumnNames.ARR_DATE], '%d/%m/%Y').date()
        if jour < first_day:
            first_day = jour
    return first_day

def set_date_to_standard(data):
    """
    Transforme toutes les dates présentes dans l'instance `data` au format `jj/mm/aaaa`
    """
    for index, row in data[InstanceSheetNames.SHEET_ARRIVEES].iterrows():
        arrival_date = row[ArriveesColumnNames.ARR_DATE]
        if re_jourheure.match(arrival_date) is not None:
            jour = datetime.datetime.strptime(arrival_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_ARRIVEES][ArriveesColumnNames.ARR_DATE][index] = std_date
    for index, row in data[InstanceSheetNames.SHEET_DEPARTS].iterrows():
        departure_date = row[DepartsColumnNames.DEP_DATE]
        if re_jourheure.match(departure_date) is not None:
            jour = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_DEPARTS][DepartsColumnNames.DEP_DATE][index] = std_date
    for index, row in data[InstanceSheetNames.SHEET_CORRESPONDANCES].iterrows():
        departure_date = row[CorrespondancesColumnNames.CORR_DEP_DATE]
        if re_jourheure.match(departure_date) is not None:
            jour = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_CORRESPONDANCES][CorrespondancesColumnNames.CORR_DEP_DATE][index] = std_date
        arrival_date = row[CorrespondancesColumnNames.CORR_ARR_DATE]
        if re_jourheure.match(arrival_date) is not None:
            jour = datetime.datetime.strptime(arrival_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_CORRESPONDANCES][CorrespondancesColumnNames.CORR_ARR_DATE][index] = std_date

def dates_to_creneaux(data):
    """
    Parcourt les données de l'instance et ajoute une colonne "Creneau" 
    dans le dataframe contenant les trains à l'arrivée et au départ 
    qui stocke leur horaire d'arrivée sous la forme d'un créneau entier
    """
    first_day = get_first_day(data)
    # Crée les nouvelles colonnes avec 0 pour valeur par défaut
    data[InstanceSheetNames.SHEET_ARRIVEES]["Creneau"] = 0
    data[InstanceSheetNames.SHEET_DEPARTS]["Creneau"] = 0

    # Remplit ces colonnes avec la valeur adaptée
    for index, row in data[InstanceSheetNames.SHEET_ARRIVEES].iterrows():
        arrival_date = row[ArriveesColumnNames.ARR_DATE]
        time_str = row[ArriveesColumnNames.ARR_HOUR]
        creneau = creneau_from_train_info(first_day, arrival_date, time_str)
        data[InstanceSheetNames.SHEET_ARRIVEES].loc[index, "Creneau"] = creneau

    for index, row in data[InstanceSheetNames.SHEET_DEPARTS].iterrows():
        departure_date = row[DepartsColumnNames.DEP_DATE]
        time_str = row[DepartsColumnNames.DEP_HOUR]
        creneau = creneau_from_train_info(first_day, departure_date, time_str)
        data[InstanceSheetNames.SHEET_DEPARTS].loc[index, "Creneau"] = creneau

def creneau_from_train_info(first_day, train_date, train_time):
    """
    Prend en argument les informations relatives à un train
    Renvoie le créneau d'arrivée (ou de départ) de ce train
    """
    if re_jour.match(train_date) is not None:
        jour = datetime.datetime.strptime(train_date, '%d/%m/%Y').date()
    elif re_jourheure.match(train_date) is not None:
        jour = datetime.datetime.strptime(train_date, '%Y-%m-%d %H:%M:%S').date()
    else:
        print(train_date)
        jour = train_date.date()
    time_delta = jour - first_day
    numero_jour = time_delta.days + 1
    if re_hour_min.match(train_time) is not None:
        horaire = datetime.datetime.strptime(train_time, '%H:%M:%S').time()
    elif re_hour_min_sec.match(train_time) is not None:
        horaire = datetime.datetime.strptime(train_time, '%H:%M').time()
    else:
        horaire = datetime.datetime.strptime(train_time, '%H:%M:%S').time()
    heure, minute = horaire.hour, horaire.minute
    creneau = horaires.triplet_vers_entier(numero_jour, heure, minute)
    return creneau

def save_to_pickle(data, pkl_file_path):
    """
    sauvegarde le dictionnaire `data` en fichier pickle à l'emplacement donné par `pkl_file_path`
    """
    with open(pkl_file_path, 'wb') as pickle_file:
        pickle.dump(data, pickle_file)

def load_from_pickle(pkl_file_path):
    """
    Si possible, charge le fichier donné par `pkl_file_path` et le renvoie
    Sinon, renvoie None.
    """
    if os.path.isfile(pkl_file_path):
        return pickle.load(open(pkl_file_path, 'rb'))
    print("Ce fichier n'existe pas")
    return None

DATA_DICT = None
if not os.path.isfile(INSTANCE_PICKLE_FILE):
    start_time = time.time()
    DATA_DICT = load_instance(INSTANCE_FILE)
    end_time = time.time()
    print("Durée du chargement : ", end_time-start_time)
    save_to_pickle(DATA_DICT, INSTANCE_PICKLE_FILE)
else:
    DATA_DICT = load_from_pickle(INSTANCE_PICKLE_FILE)

## FONCTIONS UTILES POUR LA LECTURE DE DONNEES
def composition_train_depart(data, id_train_depart):
    """
    argument : `id_train_depart` est l'identifiant unique du train de départ considéré
    sous la frome du couple (`date`, `numero de train`)
    Renvoie `related_trains` la liste des trains à l'arrivées
    qui contiennent un wagon faisant partie du train au départ considéré
    """
    related_trains = []
    correspondances = data[InstanceSheetNames.SHEET_CORRESPONDANCES]
    for _, row in correspondances.iterrows():
        dep_train_id = (row[CorrespondancesColumnNames.CORR_DEP_DATE], row[CorrespondancesColumnNames.CORR_DEP_TRAIN_NUMBER])
        if dep_train_id == id_train_depart:
            arr_train_id = (row[CorrespondancesColumnNames.CORR_ARR_DATE], row[CorrespondancesColumnNames.CORR_ARR_TRAIN_NUMBER])
            related_trains.append(arr_train_id)
    return related_trains

def indispo_to_intervalle(data, target_type, target_id):
    """
    Cherche les indisponibilités (selon `target_type`) de la machine/chantier `target_id`
    Renvoie ces indisponibilités sous la forme d'une liste de couple de créneaux (`debut`, `fin`)
    """
    assert target_type in ["chantier", "machine"]
    if target_type == "chantier":
        sheet = InstanceSheetNames.SHEET_CHANTIERS
        name_column = ChantiersColumnNames.CHANTIER_NAME
        indisp_column = ChantiersColumnNames.CHANTIER_INDISPONIBILITES
    elif target_type == "machine":
        sheet = InstanceSheetNames.SHEET_MACHINES
        name_column = MachinesColumnNames.MACHINE_NAME
        indisp_column = MachinesColumnNames.MACHINE_INDISPONIBILITES

    indispos_creneaux = []
    machine_data = data[sheet]
    for _, row in machine_data.iterrows():
        if row[name_column] == target_id:
            total_indisp = row[indisp_column]
            if total_indisp == "0":
                break
            list_indisp = total_indisp.split(sep=";")
            for indisp in list_indisp:
                creneau_start, creneau_end = creneau_from_indisp(indispos_creneaux, indisp)
                indispos_creneaux.append((creneau_start, creneau_end))
    return indispos_creneaux

def creneau_from_indisp(indispos_creneaux, indisp):
    """
    Prend en argument une indisponibilité telle qu'extraite directement de l'excel
    Renvoie les créneaux de début et fin associés
    """
    indisp = indisp.lstrip("(").rstrip(")")
    day_number, time_span = indisp.split(",")
    day_number = int(day_number)
    time_start, time_end = time_span.split("-")
    time_start = time_start.strip(" ")
    time_end = time_end.strip(" ")
    start_hour, start_minute = [int(var) for var in time_start.split(":")]
    end_hour, end_minute = [int(var) for var in time_end.split(":")]
    creneau_start = horaires.triplet_vers_entier(day_number, start_hour, start_minute)
    creneau_end = horaires.triplet_vers_entier(day_number, end_hour, end_minute)
    if time_start == time_end: # l'indsiponibilité dure 24h
        creneau_end = horaires.triplet_vers_entier(day_number+1, end_hour, end_minute)
        if day_number == 7: # l'indisponibilité déborde sur le lundi
            # -> elle doit aussi être prise en compte pour le lundi de la semaine 1
            indispos_creneaux.append((0, horaires.triplet_vers_entier(1, end_hour, end_minute)))
    return creneau_start,creneau_end

if __name__ == "__main__":
    print(DATA_DICT.keys())
    print("===========")
    print("Test indispo Machines/Chantiers")
    thing = indispo_to_intervalle(DATA_DICT, "machine", "FOR")
    print(thing)
    for start, end in thing:
        print("Debut : ", horaires.entier_vers_triplet(start))
        print("Fin : ", horaires.entier_vers_triplet(end))
    print("===========")
