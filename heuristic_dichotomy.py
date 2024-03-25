"""Module principal à configurer puis exécuter pour optimiser le modèle"""
import os
import time
from math import floor
from gurobipy import GRB
import lecture_donnees
import donnees_trains
from util import ORDERED_MACHINES, InstanceSheetNames, ChantiersColumnNames
from model_jalon2 import FretModelJal2
import display_tools.display_agenda as dis_agenda
import display_tools.compute_stats as dis_tracks


overall_start_time = time.time()

# Chemin d'accès du fichier contenant l'instance
INSTANCE = lecture_donnees.ALL_INSTANCES[1]
INSTANCE_DIR = "Instances/" + INSTANCE
INSTANCE_FILE = INSTANCE_DIR + ".xlsx"
INSTANCE_PICKLE_FILE = INSTANCE_DIR + ".pkl"

def create_data_dict() -> dict:
    """Crée le dictionnaire contenant l'ensemble des données de l'instance"""
    data_dict = None
    if not os.path.isfile(INSTANCE_PICKLE_FILE):
        start_loading_time = time.time()
        data_dict = lecture_donnees.load_instance(INSTANCE_FILE)
        end_loading_time = time.time()
        print("Durée du chargement : ", end_loading_time-start_loading_time)
        lecture_donnees.save_to_pickle(data_dict, INSTANCE_PICKLE_FILE)
    else:
        data_dict = lecture_donnees.load_from_pickle(INSTANCE_PICKLE_FILE)
    return data_dict

def gradual_optimization(data: dict) -> FretModelJal2:
    """Recherche l'optimum du jalon 2 en décrémentant progressivement
    le nombre de voies du chantier de formation"""
    max_voies_occupees = -1
    old_model = FretModelJal2({})
    fret_model = truncated_fret_model(data)
    while not fret_model.model.status == GRB.INFEASIBLE:
        max_voies_occupees = int(fret_model.obj_function.getValue())
        old_model = fret_model
        print(f"==Current best objective==\n{max_voies_occupees}")
        fret_model = truncated_fret_model(data, max_voies_occupees-1)
    return old_model

def dichotomic_optimization(data: dict) -> FretModelJal2:
    """Recherche l'optimum du jalon 2 par exploration dichotomique"""
    # Initialize bounds
    max_bound = int(data[InstanceSheetNames.SHEET_CHANTIERS][ChantiersColumnNames.CHANTIER_CAPA_VOIES][1])
    min_bound = 0 # infeasible model so long as instance is not empty
    # Initialize models
    last_feasible_model = FretModelJal2({})
    fret_model = truncated_fret_model(data, max_bound)
    if fret_model.model.status == GRB.INFEASIBLE:
        return last_feasible_model
    else:
        last_feasible_model = fret_model
    # Dichotomic search
    while not max_bound == min_bound + 1:
        mean = floor((max_bound + min_bound) / 2)
        print(f"\n==Searching for objective==\n\t{mean} tracks taken\n")
        fret_model = truncated_fret_model(data, mean)
        if fret_model.model.status == GRB.INFEASIBLE:
            min_bound = mean
        else:
            max_bound = mean
            last_feasible_model = fret_model
        print(f"\n==Current best objective==\n\t{max_bound} tracks\n")
    return last_feasible_model

def truncated_fret_model(data, nb_voies=-2):
    """Crée un modèle jalon 2 avec un nombre limité de voies sur le chantier de formation"""
    fret_model = FretModelJal2(data)
    fret_model.set_nb_voies_fromation(nb_voies)
    fret_model.load_whole_model()
    fret_model.update_model()
    fret_model.optimize_model()
    return fret_model

DATA_DICT = create_data_dict()
if __name__ == "__main__":
    best_model = dichotomic_optimization(DATA_DICT)
    execution_end_time = time.time()
    best_model.model.write(f"Modeles/model_{INSTANCE}_jalon2_grad.lp")
    best_model.model.write(f"Outputs/out_{INSTANCE}_jalon2_grad.sol")
    indispo = []
    for machine in ORDERED_MACHINES:
        for index_indisp, (creneau_min, creneau_max) in enumerate(donnees_trains.indispo_to_intervalle(
                    DATA_DICT, "machine", machine)):
            indispo.append((machine, creneau_min, creneau_max))
    earliest_arrival = min(best_model.arrivees()["JARR"])
    latest_departure = max(best_model.departs()["JDEP"])
    dis_agenda.full_process(best_model.variables, (earliest_arrival, latest_departure),
                            best_model.arrivees(), best_model.departs(), indispo)
    dis_tracks.full_process_stats((earliest_arrival, latest_departure), best_model.variables,
                                  best_model.arrivees(), best_model.departs(), DATA_DICT[InstanceSheetNames.SHEET_CHANTIERS][ChantiersColumnNames.CHANTIER_CAPA_VOIES])
    print("## Valeur de l'objectif : ", best_model.obj_function.getValue())
    print("Durée totale d'exécution : ", execution_end_time - overall_start_time)

