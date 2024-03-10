"""Génère et optimise le modèle gurobi associé à l'instance considérée"""
# Modules
from gurobipy import *

from lecture_donnees import DATA_DICT, composition_train_depart
from util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames
import horaires


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
m = Model("Fret SNCF")

## VARIABLES
VARIABLES = {}

M = 10**10

# Variables de décision concernant les trains à l'arrivée :
arrivees = DATA_DICT[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] = m.addVar(
        name = f"Train_ARR_{jour}_{numero}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
departs = DATA_DICT[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    VARIABLES[f"Train_DEP_{jour}_{numero}_FOR"] = m.addVar(
        name = f"Train_DEP_{jour}_{numero}_FOR",
        vtype = GRB.INTEGER,
        lb = 0
    )
    VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] = m.addVar(
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
    CONTRAINTES[f"Train_ARR_{jour}_{numero}_ORDRE"] = m.addConstr(
        VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 12,
        name = f"Train_ARR_{jour}_{numero}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
for index in departs.index :
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    creneau_depart = departs[DepartsColumnNames.DEP_CRENEAU][index]
    CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = m.addConstr(
        VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] >= VARIABLES[f"Train_DEP_{jour}_{numero}_FOR"] + 33,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
    )
    CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = m.addConstr(
        VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] + 7 <= creneau_depart,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
    )

# Contraintes d'indisponibilité
'''À faire quand tout le reste fonctionne'''
#Test indipso machine DEB
t_min = 0
t_max = horaires.triplet_vers_entier(1, 13, 0)
delta_t = 3
jour_test = arrivees[ArriveesColumnNames.ARR_DATE][0]
numero_test = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][0]
to_abs = 2 * VARIABLES[f"Train_ARR_{jour_test}_{numero_test}_DEB"] - (t_max + t_min - delta_t + 1)
lin_abs = linearise_abs(m, VARIABLES, CONTRAINTES, to_abs, "TEST_INDISPO_Train_ARR_sillon1", M)
CONTRAINTES["Constr_INDISPO_DEB_Train0"] = m.addConstr(lin_abs >= t_max - t_min + delta_t, name="Constr_INDISPO_DEB_Train0")

# Contraintes de raccordement
for index in departs.index :
    jour_depart = departs[DepartsColumnNames.DEP_DATE][index]
    numero_depart = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    id_train_depart = (jour_depart, numero_depart)
    trains_arrivee_lies = composition_train_depart(DATA_DICT, id_train_depart)
    for jour_arrivee, numero_arrivee in trains_arrivee_lies:
        CONTRAINTES[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = m.addConstr(
            VARIABLES[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= VARIABLES[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 3,
            name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
        )

# Contraintes d'occupation des machines
for i, index_1 in enumerate(arrivees.index):
    for index_2 in arrivees.index[i+1:]:
        jour_1 = arrivees[ArriveesColumnNames.ARR_DATE][index_1]
        numero_1 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
        jour_2 = arrivees[ArriveesColumnNames.ARR_DATE][index_2]
        numero_2 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - M <= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"] - M + M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - VARIABLES[f"Train_ARR_{jour_2}_{numero_2}_DEB"] + VARIABLES[f"Train_ARR_{jour_1}_{numero_1}_DEB"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )

for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - M <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"] - M + M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_FOR"] + VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_FOR"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )

for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.BINARY,
        )
        VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.INTEGER,
            lb = 0
        )
        CONTRAINTES[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - M <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"] - M + M * VARIABLES[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        CONTRAINTES[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            2 * VARIABLES[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - VARIABLES[f"Train_DEP_{jour_2}_{numero_2}_DEG"] + VARIABLES[f"Train_DEP_{jour_1}_{numero_1}_DEG"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )

m.update()
#m.display()
m.optimize()

for var in VARIABLES:
    print(f"{var}: {VARIABLES[var].x}")
    print("triplet :", horaires.entier_vers_triplet(int(VARIABLES[var].x)))
