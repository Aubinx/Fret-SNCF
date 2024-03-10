# Modules
from gurobipy import *

from LectureDonnees import data_dict, composition_train_depart
from Util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames
import Horaires


def linearise_abs(model : Model, variables, contraintes, expr_var : LinExpr, var_name : str, majorant):
    """
    linéarise la variable `|expr_var|` en ajoutant des variables et des contraintes au modèle gurobi `model` ainsi que dans les dictionnaire `variables` et `contraintes`
    Renvoie l'expression linéaire de `|expr_var|`
    """    
    # Créer la variable binaire indicatrice et les contraintes associées
    delta = model.addVar(name=f"linabs_binary_{var_name}",
                         vtype=GRB.BINARY)
    variables[delta.VarName] = delta
    cb1 = model.addConstr(majorant * delta >= expr_var, name=f"linabs_ConstrBinary1_{var_name}")
    cb2 = model.addConstr(majorant *( delta - 1) <= expr_var, name=f"linabs_ConstrBinary2_{var_name}")
    contraintes[cb1.ConstrName] = cb1
    contraintes[cb2.ConstrName] = cb2

    # Créer la nouvelle variable entière et les contraintes associées
    prod = model.addVar(name=f"linabs_integer_{var_name}",
                        vtype=GRB.INTEGER, lb=0)
    variables[prod.VarName] = prod
    ci1 = model.addConstr(prod <= expr_var, name=f"linabs_ConstrInteger1_{var_name}")
    ci2 = model.addConstr(prod <= majorant * delta, name=f"linabs_ConstrInteger2_{var_name}")
    ci3 = model.addConstr(prod >= expr_var - majorant * (delta - 1), name=f"linabs_ConstrInteger3_{var_name}")
    contraintes[ci1.ConstrName] = ci1
    contraintes[ci2.ConstrName] = ci2
    contraintes[ci3.ConstrName] = ci3
    lin_abs = LinExpr(2 * prod - expr_var)
    return lin_abs

# Modèle
m = Model("Fret SNCF")

## VARIABLES
VARS = {}

M = 10**10

# Variables de décision concernant les trains à l'arrivée :
arrivees = data_dict[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    VARS[f"Train_ARR_{jour}_{numero}_DEB"] = m.addVar(
        name = f"Train_ARR_{jour}_{numero}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
departs = data_dict[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    VARS[f"Train_DEP_{jour}_{numero}_FOR"] = m.addVar(
        name = f"Train_DEP_{jour}_{numero}_FOR",
        vtype = GRB.INTEGER,
        lb = 0
    )
    VARS[f"Train_DEP_{jour}_{numero}_DEG"] = m.addVar(
        name = f"Train_DEP_{jour}_{numero}_DEG",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant l'occupation des voies
'''À faire quand tout le reste fonctionne'''

## CONTRAINTES
contr = {}

# Contraintes sur l'ordre des tâches du train d'arrivée
for index in arrivees.index :
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    creneau_arrivee = arrivees[ArriveesColumnNames.ARR_CRENEAU][index]
    contr[f"Train_ARR_{jour}_{numero}_ORDRE"] = m.addConstr(
        VARS[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 12,
        name = f"Train_ARR_{jour}_{numero}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
for index in departs.index :
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    creneau_depart = departs[DepartsColumnNames.DEP_CRENEAU][index]
    contr[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = m.addConstr(
        VARS[f"Train_DEP_{jour}_{numero}_DEG"] >= VARS[f"Train_DEP_{jour}_{numero}_FOR"] + 33,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
    )
    contr[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = m.addConstr(
        VARS[f"Train_DEP_{jour}_{numero}_DEG"] + 7 <= creneau_depart,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
    )

# Contraintes d'indisponibilité
'''À faire quand tout le reste fonctionne'''
#Test indipso machine DEB
t_min = 0
t_max = Horaires.triplet_vers_entier(1, 13, 0)
delta_t = 3
jour_test = arrivees[ArriveesColumnNames.ARR_DATE][0]
numero_test = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][0]
to_abs = 2 * vars[f"Train_ARR_{jour_test}_{numero_test}_DEB"] - (t_max + t_min - delta_t + 1)
delta, prod, lin_abs, cstr_list = linearise_abs(m, to_abs, "TEST_INDISPO_Train_ARR_sillon1", M)
m.addConstr(lin_abs >= t_max - t_min + delta_t, name="Constr_INDISPO_DEB_Train0")

# Contraintes de raccordement
for index in departs.index :
    jour_depart = departs[DepartsColumnNames.DEP_DATE][index]
    numero_depart = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    id_train_depart = (jour_depart, numero_depart)
    trains_arrivee_lies = composition_train_depart(data_dict, id_train_depart)
    for jour_arrivee, numero_arrivee in trains_arrivee_lies:
        contr[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = m.addConstr(
            VARS[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= VARS[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 3,
            name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
        )

# Contraintes d'occupation des machines
for i, index_1 in enumerate(arrivees.index):
    for index_2 in arrivees.index[i+1:]:
        jour_1 = arrivees[ArriveesColumnNames.ARR_DATE][index_1]
        numero_1 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
        jour_2 = arrivees[ArriveesColumnNames.ARR_DATE][index_2]
        numero_2 = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
        VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.BINARY,
        )
        VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB",
            vtype = GRB.INTEGER,
            lb = 0
        )
        contr[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARS[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARS[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        contr[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - M <= VARS[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARS[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        contr[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= VARS[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARS[f"Train_ARR_{jour_1}_{numero_1}_DEB"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        contr[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] <= M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        contr[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] >= VARS[f"Train_ARR_{jour_2}_{numero_2}_DEB"] - VARS[f"Train_ARR_{jour_1}_{numero_1}_DEB"] - M + M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )
        contr[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] = m.addConstr(
            2 * VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"] - VARS[f"Train_ARR_{jour_2}_{numero_2}_DEB"] + VARS[f"Train_ARR_{jour_1}_{numero_1}_DEB"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEB"
        )

for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.BINARY,
        )
        VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR",
            vtype = GRB.INTEGER,
            lb = 0
        )
        contr[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARS[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        contr[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - M <= VARS[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        contr[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= VARS[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_FOR"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        contr[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] <= M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        contr[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] >= VARS[f"Train_DEP_{jour_2}_{numero_2}_FOR"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_FOR"] - M + M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )
        contr[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] = m.addConstr(
            2 * VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"] - VARS[f"Train_DEP_{jour_2}_{numero_2}_FOR"] + VARS[f"Train_DEP_{jour_1}_{numero_1}_FOR"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_FOR"
        )

for i, index_1 in enumerate(departs.index):
    for index_2 in departs.index[i+1:]:
        jour_1 = departs[DepartsColumnNames.DEP_DATE][index_1]
        numero_1 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
        jour_2 = departs[DepartsColumnNames.DEP_DATE][index_2]
        numero_2 = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
        VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addVar(
            name = f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.BINARY,
        )
        VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addVar(
            name = f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG",
            vtype = GRB.INTEGER,
            lb = 0
        )
        contr[f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARS[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C1_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        contr[f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - M <= VARS[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C2_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        contr[f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= VARS[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_DEG"],
            name = f"Occupation_Machine_C3_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        contr[f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] <= M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C4_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        contr[f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] >= VARS[f"Train_DEP_{jour_2}_{numero_2}_DEG"] - VARS[f"Train_DEP_{jour_1}_{numero_1}_DEG"] - M + M * VARS[f"Occupation_Machine_B_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"],
            name = f"Occupation_Machine_C5_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )
        contr[f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] = m.addConstr(
            2 * VARS[f"Occupation_Machine_BX_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"] - VARS[f"Train_DEP_{jour_2}_{numero_2}_DEG"] + VARS[f"Train_DEP_{jour_1}_{numero_1}_DEG"] >= 3,
            name = f"Occupation_Machine_CF_{jour_1}_{numero_1}_{jour_2}_{numero_2}_DEG"
        )

m.update()
#m.display()
m.optimize()

for var in VARS:
    print(f"{var}: {VARS[var].x}")
    print("triplet :", Horaires.entier_vers_triplet(int(VARS[var].x)))
