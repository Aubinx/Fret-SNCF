# Modules
import pandas as pd
import pickle
import time
import os

# Chemin d'accès du fichier contenant l'instance
instance = "mini_instance"
instance_file = instance + ".xlsx"
instance_pickle_file = instance + ".pkl"

def load_instance(file_path) -> dict:
    """
    Charge l'instance du problème de la gare de fret donnée par `file_path` et crée un dictionnaire qui stocke toutes le données pertinentes
    """
    all_dict = dict()

    chantiers = pd.read_excel(file_path, sheet_name="Chantiers")
    all_dict["Chantiers"] = chantiers

    machines = pd.read_excel(file_path, sheet_name="Machines")
    all_dict["Machines"] = machines

    arrivees = pd.read_excel(file_path, sheet_name="Sillons arrivee")
    all_dict["Sillons arrivee"] = arrivees

    departs = pd.read_excel(file_path, sheet_name="Sillons depart")
    all_dict["Sillons depart"] = departs

    correspondances = pd.read_excel(file_path, sheet_name="Correspondances")
    all_dict["Correspondances"] = correspondances

    taches_humaines = pd.read_excel(file_path, sheet_name="Taches humaines")
    all_dict["Taches humaines"] = taches_humaines

    roulements_agents = pd.read_excel(file_path, sheet_name="Roulements agents")
    all_dict["Roulements agents"] = roulements_agents

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


def make_train_id_unique():
    arrivees = data_dict["Sillons arrivee"]
    couple_unique = ["JARR", "n°TRAIN"]
    
    pass


if __name__ == "__main__":
    print(data_dict.keys())
