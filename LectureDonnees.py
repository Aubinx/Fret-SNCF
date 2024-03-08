# Modules
import pandas as pd
import pickle
import time, datetime
import os

from Util import *
import Horaires

# Chemin d'accès du fichier contenant l'instance
instance = "Instances/mini_instance"
instance_file = instance + ".xlsx"
instance_pickle_file = instance + ".pkl"

## CHARGER L'INSTANCE
def load_instance(file_path) -> dict:
    """
    Charge l'instance du problème de la gare de fret donnée par `file_path` et crée un dictionnaire qui stocke toutes le données pertinentes
    """
    all_dict = dict()
    all_dict[InstanceSheetNames.SHEET_CHANTIERS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_CHANTIERS)
    all_dict[InstanceSheetNames.SHEET_MACHINES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_MACHINES)
    all_dict[InstanceSheetNames.SHEET_ARRIVEES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_ARRIVEES)
    all_dict[InstanceSheetNames.SHEET_DEPARTS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_DEPARTS)
    all_dict[InstanceSheetNames.SHEET_CORRESPONDANCES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_CORRESPONDANCES)
    all_dict[InstanceSheetNames.SHEET_TACHES] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_TACHES)
    all_dict[InstanceSheetNames.SHEET_ROULEMENTS] = pd.read_excel(file_path, sheet_name=InstanceSheetNames.SHEET_ROULEMENTS)
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
        if isinstance(arrival_date, str):
            jour = datetime.datetime.strptime(arrival_date, '%d/%m/%Y').date()
        else:
            jour = arrival_date.date()
        time_delta = jour - first_day
        numero_jour = time_delta.days + 1
        horaire = row[ArriveesColumnNames.ARR_HOUR]
        heure, minute = horaire.hour, horaire.minute
        creneau = Horaires.triplet_vers_entier(numero_jour, heure, minute)
        data[InstanceSheetNames.SHEET_ARRIVEES]["Creneau"][index] = creneau
    
    for index, row in data[InstanceSheetNames.SHEET_DEPARTS].iterrows():
        departure_date = row[DepartsColumnNames.DEP_DATE]
        if isinstance(departure_date, str):
            jour = datetime.datetime.strptime(departure_date, '%d/%m/%Y').date()
        else:
            jour = departure_date.date()
        time_delta = jour - first_day
        numero_jour = time_delta.days + 1
        horaire = row[DepartsColumnNames.DEP_HOUR]
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
    argument : `id_train_depart` est l'identifiant unique du train de départ considéré
    returns : `related_trains` la liste des trains à l'arrivées qui contiennent un wagon faisant partie du train au départ considéré
    """
    related_trains = []
    correspondances = data[InstanceSheetNames.SHEET_CORRESPONDANCES]
    for index, row in correspondances.iterrows():
        print(row)
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
    print(data_dict[InstanceSheetNames.SHEET_ARRIVEES]["Creneau"])

