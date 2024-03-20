import time
from gurobipy import *
from tqdm import tqdm
from lecture_donnees import (INSTANCE, ARRIVEES, DEPARTS, DATA_DICT,
                             composition_train_depart_creneau, 
                             composition_train_arrivee_creneau,
                             indispo_to_intervalle)
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  ChantiersColumnNames, TachesColumnNames,
                  ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER)
from model import MODEL, VARIABLES, CONTRAINTES, MAJORANT, linearise_abs
from model_jalon2_min_in_obj import model_jalon2_min_in_obj
from model_jalon2_min_lin import model_jalon2_min_lin

import display_tools.display_by_train as dis_agenda

overall_start_time = time.time()
USE_MIN_OBJ = True
EPSILON = 1/4

## VARIABLES
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

## CONTRAINTES
# Contraintes d'occupation des voies
eps_obj = LinExpr(0)
if USE_MIN_OBJ:
    eps_obj = model_jalon2_min_in_obj(MODEL, VARIABLES, CONTRAINTES)
else:
    model_jalon2_min_lin(MODEL, VARIABLES, CONTRAINTES)

# Assignation à une voie
for i in tqdm(range(len(ORDERED_CHANTIERS)), desc="Assignation Voie Unique", colour='#ffffff'):
    chantier_id = ORDERED_CHANTIERS[i]
    if chantier_id == ORDERED_CHANTIERS[0]: # Chantier de réception
        for index in ARRIVEES.index:
            jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
            numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
            somme_cvt = 0
            for voie in range(1, int(NB_VOIES[i]) + 1):
                somme_cvt += VARIABLES[f"CVT_{chantier_id}_{str(voie)}_{jour}_{numero}"]
            cstr_name = f"ASSIGNATION_{chantier_id}_{str(voie)}_train_{jour}_{numero}"
            CONTRAINTES[cstr_name] = MODEL.addConstr(somme_cvt == 1, name=cstr_name)
    else:
        for index in DEPARTS.index:
            jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
            numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            somme_cvt = 0
            for voie in range(1, int(NB_VOIES[i]) + 1):
                somme_cvt += VARIABLES[f"CVT_{chantier_id}_{str(voie)}_{jour}_{numero}"]
            cstr_name = f"ASSIGNATION_{chantier_id}_{str(voie)}_train_{jour}_{numero}"
            CONTRAINTES[cstr_name] = MODEL.addConstr(somme_cvt == 1, name=cstr_name)


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

# Initialisation des dictionnaires DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE et DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART

DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE = {}
for index in tqdm(ARRIVEES.index, desc="Dictionnaire DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE") :
    jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
    numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE[index] = max(composition_train_arrivee_creneau(DATA_DICT, (jour, numero)))  

DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART = {}
for index in tqdm(DEPARTS.index, desc="Dictionnaire DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART") :
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART[index] = min(composition_train_depart_creneau(DATA_DICT, (jour, numero)))

# Chantier "réception"
for index_1 in tqdm(ARRIVEES.index, desc="Occupation WPY_REC", colour='#00ff00') :
    jour_1 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_1]
    numero_1 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
    creneau_arrivee_1 = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index_1]
    creneau_depart_1 = DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE[index_1]
    for index_2 in ARRIVEES.index :
        if index_1 == index_2:
            continue
        jour_2 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_2]
        numero_2 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
        creneau_arrivee_2 = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index_2]
        creneau_depart_2 = DICT_MAX_DEPART_DU_TRAIN_D_ARRIVEE[index_2]
        if creneau_depart_1 >= creneau_arrivee_2 and creneau_depart_2 >= creneau_arrivee_1 :
            for voie in range(1, int(NB_VOIES[0]) + 1) :
                add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_REC", voie, jour_1, numero_1, jour_2, numero_2, creneau_arrivee_1, creneau_arrivee_2, MAJORANT)

# Chantiers de "formation" et de "départ"
for index_1 in tqdm(DEPARTS.index, desc="Occupation WPY_FOR et WPY_DEP", colour='#00ff00') :
    jour_1 = DEPARTS[DepartsColumnNames.DEP_DATE][index_1]
    numero_1 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
    creneau_depart_1 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_1]
    creneau_arrivee_1 = DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART[index_1]
    for index_2 in DEPARTS.index :
        if index_1 == index_2:
            continue
        jour_2 = DEPARTS[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        creneau_depart_2 = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index_2]
        creneau_arrivee_2 = DICT_MIN_ARRIVEE_DU_TRAIN_DE_DEPART[index_2]
        if creneau_depart_1 >= creneau_arrivee_2 and creneau_depart_2 >= creneau_arrivee_1 :
            for voie in range(1, int(NB_VOIES[1]) + 1) :
                add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_FOR", voie, jour_1, numero_1, jour_2, numero_2, creneau_depart_1, creneau_depart_2, MAJORANT)
            for voie in range(1, int(NB_VOIES[2]) + 1) :
                add_occu_voies(MODEL, VARIABLES, CONTRAINTES, "WPY_DEP", voie, jour_1, numero_1, jour_2, numero_2, creneau_depart_1, creneau_depart_2, MAJORANT)

## FONCTION OBJECTIF
# minimiser le nombre de voie max dans le chantier de formation
obj_somme_indic = 0
for voie in tqdm(range(1, int(NB_VOIES[1]) + 1), desc="Fonction OBJ", colour='#ff8800') :
    indic_voie_name = f"indicatrice_FOR_voie{voie}_occupee"
    indic_voie_constr = f"Constr_indic_FOR_voie{voie}"
    somme_cvt_indic = -1
    for index in DEPARTS.index :
        jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
        numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
        somme_cvt_indic += VARIABLES[f"CVT_WPY_FOR_{voie}_{jour}_{numero}"]
    VARIABLES[indic_voie_name] = MODEL.addVar(vtype=GRB.BINARY,
                                              name=indic_voie_name)
    CONTRAINTES[indic_voie_constr+"_1"] = MODEL.addConstr(MAJORANT * VARIABLES[indic_voie_name] >= somme_cvt_indic + EPSILON,
                                                          name=indic_voie_constr+"_1")
    CONTRAINTES[indic_voie_constr+"_2"] = MODEL.addConstr(MAJORANT * (VARIABLES[indic_voie_name] - 1) <= somme_cvt_indic + EPSILON,
                                                          name=indic_voie_constr+"_2")
    obj_somme_indic += VARIABLES[indic_voie_name]

MODEL.setObjective(obj_somme_indic - eps_obj, GRB.MINIMIZE)
            



# MODEL.display()
# MODEL.params.OutputFlag = 0
# MODEL.optimize()

if __name__=='__main__':
    MODEL.update()
    start_time = time.time()
    print("~~Time before optimization :", start_time - overall_start_time)
    print("~~Started optimizing.")
    MODEL.optimize()
    # model_type = "min_in_obj" if USE_MIN_OBJ else "min_lin"
    # MODEL.write(f"Modeles/model_{INSTANCE}_jalon2_{model_type}.lp")
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

    print("## Valeur de l'objectif : ", MODEL.ObjVal + eps_obj.getValue())
