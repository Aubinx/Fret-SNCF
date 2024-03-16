import time
from gurobipy import *
from lecture_donnees import (INSTANCE, ARRIVEES, DEPARTS, DATA_DICT,
                             composition_train_depart, indispo_to_intervalle)
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  ChantiersColumnNames, TachesColumnNames,
                  ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER)
from model import MODEL, VARIABLES, CONTRAINTES, MAJORANT, linearise_abs
from model_jalon2_min_in_obj import model_jalon2_min_in_obj
from model_jalon2_min_lin import model_jalon2_min_lin

import display_tools.display_by_train as dis_agenda

overall_start_time = time.time()
USE_MIN_OBJ = True

# Variables de décision concernant l'occupation des voies (jalon 2)
NB_VOIES = DATA_DICT[InstanceSheetNames.SHEET_CHANTIERS][ChantiersColumnNames.CHANTIER_CAPA_VOIES]
# Variables binaires d'occupation des voies pour chaque chantier
# Occupations des voies du chantier "réception"
for index in ARRIVEES.index:
    jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
    numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    for voie in range(1, int(NB_VOIES[0]) + 1) :
        VARIABLES[f"CVT_WPY_REC_{str(voie)}_{jour}_{numero}"] = MODEL.addVar(
            name = f"CVT_WPY_REC_{str(voie)}_{jour}_{numero}",
            vtype = GRB.BINARY,
        )

# Occupations des voies du chantier "formation"
for index in DEPARTS.index:
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    for voie in range(1, int(NB_VOIES[1]) + 1) :
        VARIABLES[f"CVT_WPY_FOR_{str(voie)}_{jour}_{numero}"] = MODEL.addVar(
            name = f"CVT_WPY_FOR_{str(voie)}_{jour}_{numero}",
            vtype = GRB.BINARY,
        )

# Occupations des voies du chantier "départ"
for index in DEPARTS.index:
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    for voie in range(1, int(NB_VOIES[2]) + 1) :
        VARIABLES[f"CVT_WPY_DEP_{str(voie)}_{jour}_{numero}"] = MODEL.addVar(
            name = f"CVT_WPY_DEP_{str(voie)}_{jour}_{numero}",
            vtype = GRB.BINARY,
        )

# Contraintes d'occupation des voies
eps_obj = 0
if USE_MIN_OBJ:
    eps_obj = model_jalon2_min_in_obj(MODEL, VARIABLES, CONTRAINTES)
else:
    model_jalon2_min_lin(MODEL, VARIABLES, CONTRAINTES)

def add_occu_voies(model, variables, contraintes, chantier_id, voie, jour1, numero1, jour2, numero2, creneau1, creneau2, majorant):
    type_train = "ARR" if chantier_id == "WPY_REC" else "DEP"
    if chantier_id == "WPY_REC":
        train_arrivee_1 = creneau1
        train_arrivee_2 = creneau2
        train_depart_1 = variables[f"Train_{type_train}_{jour1}_{numero1}_DEB"] + 15
        train_depart_2 = variables[f"Train_{type_train}_{jour2}_{numero2}_DEB"] + 15
    elif chantier_id == "WPY_FOR":
        train_arrivee_1 = variables[f"min_DEB_{jour1}_{numero1}"]
        train_arrivee_2 = variables[f"min_DEB_{jour2}_{numero2}"]
        train_depart_1 = variables[f"Train_{type_train}_{jour1}_{numero1}_DEG"]
        train_depart_2 = variables[f"Train_{type_train}_{jour2}_{numero2}_DEG"]
    elif chantier_id == "WPY_DEP":
        train_arrivee_1 = variables[f"Train_{type_train}_{jour1}_{numero1}_DEG"]
        train_arrivee_2 = variables[f"Train_{type_train}_{jour2}_{numero2}_DEG"]
        train_depart_1 = creneau1
        train_depart_2 = creneau2
    cvt_1 = variables[f"CVT_{chantier_id}_{voie}_{jour1}_{numero1}"]
    cvt_2 = variables[f"CVT_{chantier_id}_{voie}_{jour2}_{numero2}"]
    # Contrainte 1
    to_abs = 2 * train_arrivee_1 - train_arrivee_2 - train_depart_2
    name_new_var = f"CVT_entree_{chantier_id}_{voie}_{jour1}_{numero1}_{jour2}_{numero2}"
    cstr_name = "Constr_"+name_new_var
    lin_abs = linearise_abs(model, to_abs, name_new_var, variables, contraintes, majorant)
    contraintes[cstr_name] = model.addConstr(lin_abs >= train_depart_2 - train_arrivee_2 + majorant * (cvt_2 + cvt_1 - 2), name=cstr_name)
    # Contrainte 2
    to_abs = 2 * train_depart_1 - train_arrivee_2 - train_depart_2
    name_new_var = f"CVT_sortie_{chantier_id}_{voie}_{jour1}_{numero1}_{jour2}_{numero2}"
    cstr_name = "Constr_"+name_new_var
    lin_abs = linearise_abs(model, to_abs, name_new_var, variables, contraintes, majorant)
    contraintes[cstr_name] = model.addConstr(lin_abs >= train_depart_2 - train_arrivee_2 + majorant * (cvt_2 + cvt_1 - 2), name=cstr_name)

# Chantier "réception"
for voie in range(1, int(NB_VOIES[0]) + 1) :
    for index_1 in ARRIVEES.index :
        for index_2 in ARRIVEES.index :
            if index_1 == index_2:
                continue
            jour_1 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_1]
            numero_1 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
            creneau_1 = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index_1]
            jour_2 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_2]
            numero_2 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
            creneau_2 = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index_2]
            add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_REC", voie, jour_1, numero_1, jour_2, numero_2, creneau_1, creneau_2, MAJORANT)

# Chantier "formation"
for voie in range(1, int(NB_VOIES[1]) + 1) :
    for index_1 in DEPARTS.index :
        for index_2 in DEPARTS.index :
            if index_1 == index_2:
                continue
            jour_1 = DEPARTS[DepartsColumnNames.DEP_DATE][index_1]
            numero_1 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
            creneau_1 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_1]
            jour_2 = DEPARTS[DepartsColumnNames.DEP_DATE][index_2]
            numero_2 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
            creneau_2 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_2]
            add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_FOR", voie, jour_1, numero_1, jour_2, numero_2, creneau_1, creneau_2, MAJORANT)

# Chantier "départ"
for voie in range(1, int(NB_VOIES[2]) + 1) :
    for index_1 in DEPARTS.index :
        for index_2 in DEPARTS.index :
            if index_1 == index_2:
                continue
            jour_1 = DEPARTS[DepartsColumnNames.DEP_DATE][index_1]
            numero_1 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
            creneau_1 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_1]
            jour_2 = DEPARTS[DepartsColumnNames.DEP_DATE][index_2]
            numero_2 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
            creneau_2 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_2]
            add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_DEP", voie, jour_1, numero_1, jour_2, numero_2, creneau_1, creneau_2, MAJORANT)



# MODEL.display()
# MODEL.params.OutputFlag = 0
# MODEL.optimize()

if __name__=='__main__':
    MODEL.update()
    MODEL.setObjective(-eps_obj, GRB.MINIMIZE)
    start_time = time.time()
    print("~~Time before optimization :", start_time - overall_start_time)
    print("~~Started optimizing.")
    MODEL.optimize()
    model_type = "min_in_obj" if USE_MIN_OBJ else "min_lin"
    MODEL.write(f"Modeles/model_{INSTANCE}_jalon2_{model_type}.lp")
    opti_finished_time = time.time()
    print("~~Finished optimizing.\n~~Duration : ", opti_finished_time - start_time)
    print("~ Chargement du modèle et optimisation :", opti_finished_time - overall_start_time)
    indispo = []
    for machine in ORDERED_MACHINES:
        for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(
                    DATA_DICT, "machine", machine)):
            indispo.append((machine, creneau_min, creneau_max))
    earliest_arrival = min(ARRIVEES['JARR'])
    latest_departure = max(DEPARTS["JDEP"])
    dis_agenda.full_process(VARIABLES, (earliest_arrival, latest_departure),
                            ARRIVEES, DEPARTS, indispo)
    print("~ Affichage du résultat : ", time.time() - opti_finished_time)
