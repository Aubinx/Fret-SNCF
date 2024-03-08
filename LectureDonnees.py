# Modules
import pandas as pd
import pickle
import time, datetime
import os
import re

from Util import *
import Horaires

# Chemin d'accès du fichier contenant l'instance
instance = "Instances/mini_instance"
instance_file = instance + ".xlsx"
instance_pickle_file = instance + ".pkl"

# Expressions régulières pour les différents formats de jours
re_jour = re.compile('\d{2}/\d{2}/\d{4}')
re_jourheure = re.compile('\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')

## CHARGER L'INSTANCE
def load_instance(file_path) -> dict:
    """
    Charge l'instance du problème de la gare de fret donnée par `file_path` et crée un dictionnaire qui stocke toutes le données pertinentes
    """
    all_dict = dict()
    all_dict[InstanceSheetNames.SHEET_CHANTIERS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_CHANTIERS, dtype=str)
    all_dict[InstanceSheetNames.SHEET_MACHINES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_MACHINES, dtype=str)
    all_dict[InstanceSheetNames.SHEET_ARRIVEES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_ARRIVEES, dtype=str)
    all_dict[InstanceSheetNames.SHEET_DEPARTS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_DEPARTS, dtype=str)
    all_dict[InstanceSheetNames.SHEET_CORRESPONDANCES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_CORRESPONDANCES, dtype=str)
    all_dict[InstanceSheetNames.SHEET_TACHES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_TACHES, dtype=str)
    all_dict[InstanceSheetNames.SHEET_ROULEMENTS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_ROULEMENTS, dtype=str)
    set_date_to_standard(all_dict)
    dates_to_creneaux(all_dict)
    return all_dict

def get_first_day(data):
    """
    Recherche dans l'instance `data` et renvoie le premier jour.
    Particulièrement utile pour transformer les couples (jour, heure) d'arrivée ou de départ d'un train
    en un créneau stocké sur un entier tel qu'utilisé dans le module `Horaires.py`.
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
        if re_jourheure.match(arrival_date) != None:
            jour = datetime.datetime.strptime(arrival_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_ARRIVEES][ArriveesColumnNames.ARR_DATE][index] = std_date
    for index, row in data[InstanceSheetNames.SHEET_DEPARTS].iterrows():
        departure_date = row[DepartsColumnNames.DEP_DATE]
        if re_jourheure.match(departure_date) != None:
            jour = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_DEPARTS][DepartsColumnNames.DEP_DATE][index] = std_date
    for index, row in data[InstanceSheetNames.SHEET_CORRESPONDANCES].iterrows():
        departure_date = row[CorrespondancesColumnNames.CORR_DEP_DATE]
        if re_jourheure.match(departure_date) != None:
            jour = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S').date()
            std_date = datetime.datetime.strftime(jour, '%d/%m/%Y')
            data[InstanceSheetNames.SHEET_CORRESPONDANCES][CorrespondancesColumnNames.CORR_DEP_DATE][index] = std_date
        arrival_date = row[CorrespondancesColumnNames.CORR_ARR_DATE]
        if re_jourheure.match(arrival_date) != None:
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
    # Create new column with default value of 0
    data[InstanceSheetNames.SHEET_ARRIVEES]["Creneau"] = 0
    data[InstanceSheetNames.SHEET_DEPARTS]["Creneau"] = 0

    # Fill the new columns with the right value
    for index, row in data[InstanceSheetNames.SHEET_ARRIVEES].iterrows():
        arrival_date = row[ArriveesColumnNames.ARR_DATE]
        if re_jour.match(arrival_date) != None:
            jour = datetime.datetime.strptime(arrival_date, '%d/%m/%Y').date()
        elif re_jourheure.match(arrival_date) != None:
            jour = datetime.datetime.strptime(arrival_date, '%Y-%m-%d %H:%M:%S').date()
        else:
            jour = arrival_date.date()
        time_delta = jour - first_day
        numero_jour = time_delta.days + 1
        time_str = row[ArriveesColumnNames.ARR_HOUR]
        horaire = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
        heure, minute = horaire.hour, horaire.minute
        creneau = Horaires.triplet_vers_entier(numero_jour, heure, minute)
        data[InstanceSheetNames.SHEET_ARRIVEES]["Creneau"][index] = creneau
    
    for index, row in data[InstanceSheetNames.SHEET_DEPARTS].iterrows():
        departure_date = row[DepartsColumnNames.DEP_DATE]
        if re_jour.match(departure_date) != None:
            jour = datetime.datetime.strptime(departure_date, '%d/%m/%Y').date()
        elif re_jourheure.match(departure_date) != None:
            jour = datetime.datetime.strptime(departure_date, '%Y-%m-%d %H:%M:%S').date()
        else:
            jour = departure_date.date()
        time_delta = jour - first_day
        numero_jour = time_delta.days + 1
        time_str = row[DepartsColumnNames.DEP_HOUR]
        horaire = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
        heure, minute = horaire.hour, horaire.minute
        creneau = Horaires.triplet_vers_entier(numero_jour, heure, minute)
        data[InstanceSheetNames.SHEET_DEPARTS]["Creneau"][index] = creneau

def save_to_pickle(data, pkl_file_path):
    """
    sauvegarde le dictionnaire `data` en fichier pickle à l'emplacement donné par `pkl_file_path`
    """
    pickle.dump(data, open(pkl_file_path, 'wb'))

def load_from_pickle(pkl_file_path):
    """
    Si possible, charge le fichier donné par `pkl_file_path` et le renvoie
    Sinon, renvoie None.
    """
    if os.path.isfile(pkl_file_path):
        return pickle.load(open(pkl_file_path, 'rb'))
    else:
        print("Ce fichier n'existe pas")
        return None

data_dict = None
if not os.path.isfile(instance_pickle_file):
    start_time = time.time()
    data_dict = load_instance(instance_file)
    end_time = time.time()
    print("Durée du chargement : ", end_time-start_time)
    save_to_pickle(data_dict, instance_pickle_file)
else:
    data_dict = load_from_pickle(instance_pickle_file)

## FONCTIONS UTILES POUR LA LECTURE DE DONNEES
def composition_train_depart(data, id_train_depart):
    """
    argument : `id_train_depart` est l'identifiant unique du train de départ considéré sous la frome du couple (`date`, `numero de train`)
    returns : `related_trains` la liste des trains à l'arrivées qui contiennent un wagon faisant partie du train au départ considéré
    """
    related_trains = []
    correspondances = data[InstanceSheetNames.SHEET_CORRESPONDANCES]
    for index, row in correspondances.iterrows():
        dep_train_id = (row[CorrespondancesColumnNames.CORR_DEP_DATE], row[CorrespondancesColumnNames.CORR_DEP_TRAIN_NUMBER])
        if dep_train_id == id_train_depart:
            arr_train_id = (row[CorrespondancesColumnNames.CORR_ARR_DATE], row[CorrespondancesColumnNames.CORR_ARR_TRAIN_NUMBER])
            related_trains.append(arr_train_id)
    return related_trains


def indispo_machine_to_intervalle(data, machine):
    """
    Parcourt dans l'instances les indisponibiltés machines de la machine `machine`
    Renvoie cette indisponibilité sous la forme d'une liste de couple (`debut`, `fin`) qui indiquent les créneaux de début et de fin de chaque indisponibilité
    """
    machine_data = data[InstanceSheetNames.SHEET_MACHINES]
    for _, row in machine_data.iterrows():
        if row[MachinesColumnNames.MACHINE_NAME] == machine:
            total_indisp = row[MachinesColumnNames.MACHINE_INDISPONIBILITES]
            list_indisp = total_indisp.split(sep=";")
            for indisp in list_indisp:
                indisp = indisp.lstrip("(")
                indisp = indisp.rstrip(")")
                day_number, time_span = indisp.split(",")
                time_start, time_end = time_span.split("-")
                print(day_number, time_start, time_end)
                if time_start == time_end:
                    
                    pass
    return None

def indispo_chantier_to_intervalle(data, chantier):
    """
    Parcourt dans l'instances les indisponibiltés chantiers du chaniter `chantier`
    Renvoie cette indisponibilité sous la forme d'une liste de couple (`debut`, `fin`) qui indiquent les créneaux de début et de fin de chaque indisponibilité
    """
    chantier_data = data[InstanceSheetNames.SHEET_CHANTIERS]
    for index, row in chantier_data.iterrows():
        if row[ChantiersColumnNames.CHANTIER_NAME] == chantier:
            indisp = row[ChantiersColumnNames.CHANTIER_INDISPONIBILITES]
            print(indisp)

    return None

if __name__ == "__main__":
    print(data_dict.keys())
    print("===========")
    print(indispo_machine_to_intervalle(data_dict, "FOR"))
    print("===========")
    departs = data_dict[InstanceSheetNames.SHEET_DEPARTS]
    for index in departs.index :
        jour = departs[DepartsColumnNames.DEP_DATE][index]
        numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
        id_train_depart = (jour, numero)
        trains_arrivee_lies = composition_train_depart(data_dict, id_train_depart)
        print(trains_arrivee_lies)

