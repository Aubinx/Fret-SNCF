"""Génère et optimise le modèle gurobi associé à l'instance considérée"""
# Modules
from gurobipy import *

from lecture_donnees import DATA_DICT, composition_train_depart, indispo_to_intervalle
from util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames, TachesColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS
import horaires

import display_tools.display_agenda as dis_agenda

def linearise_abs(model : Model, variables, contraintes, expr_var : LinExpr, var_name : str, majorant):
    """
    linéarise la variable `|expr_var|` en ajoutant des variables et des contraintes au modèle gurobi `model` ainsi que dans les dictionnaire `variables` et `contraintes`
    Renvoie l'expression linéaire de `|expr_var|`
    """
    # Créer la variable binaire indicatrice et les contraintes associées
    delta = model.addVar(name=f"linabs_binary_{var_name}",
                         vtype=GRB.BINARY)
    cb1 = model.addConstr(majorant * delta >= expr_var, name=f"linabs_ConstrBinary1_{var_name}")
    cb2 = model.addConstr(majorant *( delta - 1) <= expr_var, name=f"linabs_ConstrBinary2_{var_name}")

    # Créer la nouvelle variable entière et les contraintes associées
    prod = model.addVar(name=f"linabs_integer_{var_name}",
                        vtype=GRB.INTEGER, lb=0)
    ci1 = model.addConstr(prod <= expr_var, name=f"linabs_ConstrInteger1_{var_name}")
    ci2 = model.addConstr(prod <= majorant * delta, name=f"linabs_ConstrInteger2_{var_name}")
    ci3 = model.addConstr(prod >= expr_var - majorant * (delta - 1), name=f"linabs_ConstrInteger3_{var_name}")
    
    # Mettre à jour les dictionnaires des variables et contraintes
    model.update()
    variables[delta.VarName] = delta
    variables[prod.VarName] = prod
    contraintes[cb1.ConstrName] = cb1
    contraintes[cb2.ConstrName] = cb2
    contraintes[ci1.ConstrName] = ci1
    contraintes[ci2.ConstrName] = ci2
    contraintes[ci3.ConstrName] = ci3
    lin_abs = LinExpr(2 * prod - expr_var)
    return lin_abs

# Modèle
MODEL = Model("Fret SNCF")

## VARIABLES
VARIABLES = {}

MAJORANT = 10**6

# Variables de décision concernant les trains à l'arrivée :
arrivees = DATA_DICT[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] = MODEL.addVar(
        name = f"Train_ARR_{jour}_{numero}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
departs = DATA_DICT[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    VARIABLES[f"Train_DEP_{jour}_{numero}_FOR"] = MODEL.addVar(
        name = f"Train_DEP_{jour}_{numero}_FOR",
        vtype = GRB.INTEGER,
        lb = 0
    )
    VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] = MODEL.addVar(
        name = f"Train_DEP_{jour}_{numero}_DEG",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant l'occupation des voies
'''À faire quand tout le reste fonctionne'''

## CONTRAINTES
CONTRAINTES = {}

# Contraintes sur l'ordre des tâches du train d'arrivée
for index in arrivees.index :
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    creneau_arrivee = arrivees[ArriveesColumnNames.ARR_CRENEAU][index]
    CONTRAINTES[f"Train_ARR_{jour}_{numero}_ORDRE"] = MODEL.addConstr(
        VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 60,
        name = f"Train_ARR_{jour}_{numero}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
for index in departs.index :
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    creneau_depart = departs[DepartsColumnNames.DEP_CRENEAU][index]
    CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = MODEL.addConstr(
        VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] >= VARIABLES[f"Train_DEP_{jour}_{numero}_FOR"] + 165,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
    )
    # CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = MODEL.addConstr(
    #     VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] + 35 <= creneau_depart,
    #     name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
    # )

# Contraintes d'indisponibilité
# Indisponibilités Machines
for machine in ORDERED_MACHINES:
    df = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
    for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(DATA_DICT, "machine", machine)):
        duree_task = int(df[df[TachesColumnNames.TASK_LINK]==f"{machine}="][TachesColumnNames.TASK_DURATION])
        if machine == ORDERED_MACHINES[0]:
            for index in arrivees.index :
                jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
                numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                creneau_arrivee = arrivees[ArriveesColumnNames.ARR_CRENEAU][index]
                to_abs = 2 * VARIABLES[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task + 1)
                lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, f"Train_ARR_{jour}_{numero}_INDISPO_{machine}_{index_indisp}", MAJORANT)
                CONTRAINTES[f"Constr_INDISPO_Train_ARR_{jour}_{numero}_{machine}_{index_indisp}"] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name="Constr_INDISPO_Train_ARR_{jour}_{numero}_{machine}")
        else:
            for index in departs.index :
                jour = departs[DepartsColumnNames.DEP_DATE][index]
                numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                creneau_arrivee = departs[DepartsColumnNames.DEP_CRENEAU][index]
                to_abs = 2 * VARIABLES[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task + 1)
                lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, f"Train_DEP_{jour}_{numero}_INDISPO_{machine}_{index_indisp}", MAJORANT)
                CONTRAINTES[f"Constr_INDISPO_Train_DEP_{jour}_{numero}_{machine}_{index_indisp}"] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name="Constr_INDISPO_Train_DEP_{jour}_{numero}_{machine}")

# # Indisponibilités Chantiers
# for chantier in ORDERED_CHANTIERS:
#     for (creneau_min, creneau_max) in indispo_to_intervalle(DATA_DICT, "chantier", chantier):
#         df = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
#         duree_task = df.iloc[df[TachesColumnNames.TASK_CHANTIER]==chantier, TachesColumnNames.TASK_DURATION]
#         if machine == ORDERED_MACHINES[0]:
#             for index in arrivees.index :
#                 jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
#                 numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
#                 creneau_arrivee = arrivees[ArriveesColumnNames.ARR_CRENEAU][index]
#                 to_abs = 2 * VARIABLES[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task + 1)
#                 lin_abs = linearise_abs(m, VARIABLES, CONTRAINTES, to_abs, f"Train_ARR_{jour}_{numero}_INDISPO_{machine}", M)
#                 CONTRAINTES[f"Constr_INDISPO_Train_ARR_{jour}_{numero}_{machine}"] = m.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name="Constr_INDISPO_Train_ARR_{jour}_{numero}_{machine}")
#         else:
#             for index in departs.index :
#                 jour = departs[DepartsColumnNames.DEP_DATE][index]
#                 numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
#                 creneau_arrivee = departs[DepartsColumnNames.DEP_CRENEAU][index]
#                 to_abs = 2 * VARIABLES[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task + 1)
#                 lin_abs = linearise_abs(m, VARIABLES, CONTRAINTES, to_abs, f"Train_DEP_{jour}_{numero}_INDISPO_{machine}", M)
#                 CONTRAINTES[f"Constr_INDISPO_Train_DEP_{jour}_{numero}_{machine}"] = m.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name="Constr_INDISPO_Train_DEP_{jour}_{numero}_{machine}")

# Contraintes de raccordement
for index in departs.index :
    jour_depart = departs[DepartsColumnNames.DEP_DATE][index]
    numero_depart = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    id_train_depart = (jour_depart, numero_depart)
    trains_arrivee_lies = composition_train_depart(DATA_DICT, id_train_depart)
    for jour_arrivee, numero_arrivee in trains_arrivee_lies:
        CONTRAINTES[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = MODEL.addConstr(
            VARIABLES[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= VARIABLES[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 15,
            name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
        )

# Contraintes d'occupation des machines

# Machine de débranchement
for i, index_1 in enumerate(arrivees.index):
    for index_2 in arrivees.index[i+1:]:
        jour_1 = arrivees[ArriveesColumnNames.ARR_DATE][index_1]
        numero_1 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
        jour_2 = arrivees[ArriveesColumnNames.ARR_DATE][index_2]
        numero_2 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - MAJORANT <= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"] - MAJORANT + MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = MODEL.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] + VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"] >= 15,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )

# Machine de formation
for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - MAJORANT <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"] - MAJORANT + MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = MODEL.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] + VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"] >= 15,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )

# Machine de dégarage
for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - MAJORANT <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"] - MAJORANT + MAJORANT * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = MODEL.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] + VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"] >= 15,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )

MODEL.update()
# MODEL.display()
MODEL.optimize()

for var in VARIABLES:
    print(f"{var}: {VARIABLES[var].x}")
    print("triplet :", horaires.entier_vers_triplet(int(VARIABLES[var].x)))

if __name__=='__main__':
    early, late = min(arrivees['JARR']), max(departs['JDEP'])
    tasks, color_codes, (start_date, end_date) = dis_agenda.import_tasks_from_model(VARIABLES, early, late)
    dis_agenda.generate_empty_agenda(start_date, end_date, tasks, color_codes)
