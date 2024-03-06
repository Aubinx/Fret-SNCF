# Modules
import pandas as pd
import pickle
import time
import os

from FretSncf_grp4.Util import InstanceSheetNames

# Chemin d'accès du fichier contenant l'instance
instance = "mini_instance"
instance_file = instance + ".xlsx"
instance_pickle_file = instance + ".pkl"

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
    return all_dict

def save_to_pickle(data, pkl_file_path):
    """
    sauvegarde le dictionnaire `data` en fichier pickle à l'emplacement donné par `pkl_file_path`
    """
    pickle.dump(data, open(pkl_file_path, 'wb'))

def load_from_pickle(pkl_file_path):
    """
    charge (si possible) le fichier donné par `pkl_file_path` et le renvoie
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

if __name__ == "__main__":
    print(data_dict.keys())
