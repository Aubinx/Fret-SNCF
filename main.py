"""Module principal à configurer puis exécuter pour optimiser le modèle"""
import os
import time
import lecture_donnees
from donnees_trains import indispo_to_intervalle
from model import FretModel
from model_jalon2 import FretModelJal2
from model_jalon3 import FretModelJal3
from util import ORDERED_MACHINES
import display_tools.display_agenda as dis_agenda
import display_tools.compute_stats as dis_tracks


overall_start_time = time.time()

# Chemin d'accès du fichier contenant l'instance
INSTANCE = lecture_donnees.ALL_INSTANCES[0]
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


JALON = 1
DATA_DICT = create_data_dict()
if JALON == 1:
    FRET_MODEL = FretModel(DATA_DICT)
elif JALON == 2:
    FRET_MODEL = FretModelJal2(DATA_DICT)
elif JALON == 3:
    FRET_MODEL = FretModelJal3(DATA_DICT)
if __name__ == "__main__":
    FRET_MODEL.load_whole_model()
    if JALON == 2:
        FRET_MODEL.set_model_objective_jalon2()
    elif JALON == 3:
        FRET_MODEL.set_model_objective_jalon3()
    FRET_MODEL.update_model()
    start_time = time.time()
    print("~~Time before optimization :", start_time - overall_start_time)
    print("~~Started optimizing.")
    FRET_MODEL.optimize_model()
    FRET_MODEL.model.write(f"Modeles/model_{INSTANCE}_jalon{JALON}.lp")
    FRET_MODEL.model.write(f"Outputs/out_{INSTANCE}_jalon{JALON}.sol")
    opti_finished_time = time.time()
    print("~~Finished optimizing.\n~~Duration : ", opti_finished_time - start_time)
    print("~ Chargement du modèle et optimisation :", opti_finished_time - overall_start_time)
    indispo = []
    for machine in ORDERED_MACHINES:
        for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(
                    DATA_DICT, "machine", machine)):
            indispo.append((machine, creneau_min, creneau_max))
    earliest_arrival = min(FRET_MODEL.arrivees()["JARR"])
    latest_departure = max(FRET_MODEL.departs()["JDEP"])
    dis_agenda.full_process(FRET_MODEL.variables, (earliest_arrival, latest_departure),
                            FRET_MODEL.arrivees(), FRET_MODEL.departs(), indispo)
    if JALON >= 2:
        dis_tracks.full_process_stats((earliest_arrival, latest_departure), FRET_MODEL.variables,
                                      FRET_MODEL.arrivees(), FRET_MODEL.departs(), FRET_MODEL.voies)
    print("~ Affichage du résultat : ", time.time() - opti_finished_time)
    print("## Valeur de l'objectif : ", FRET_MODEL.model.ObjVal)
