# Modules
from gurobipy import *

from LectureDonnees import data_dict, composition_train_depart
from Util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames
import Horaires

# Modèle
m = Model("Fret SNCF")

## VARIABLES
vars = {}

# Variables de décision concernant les trains à l'arrivée :
arrivees = data_dict[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    vars[f"Train_ARR_{jour}_{numero}_DEB"] = m.addVar(
        name = f"Train_ARR_{jour}_{numero}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
departs = data_dict[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    vars[f"Train_DEP_{jour}_{numero}_FOR"] = m.addVar(
        name = f"Train_DEP_{jour}_{numero}_FOR",
        vtype = GRB.INTEGER,
        lb = 0
    )
    vars[f"Train_DEP_{jour}_{numero}_DEG"] = m.addVar(
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
        vars[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 12,
        name = f"Train_ARR_{jour}_{numero}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
for index in departs.index :
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    creneau_depart = departs[DepartsColumnNames.DEP_CRENEAU][index]
    contr[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = m.addConstr(
        vars[f"Train_DEP_{jour}_{numero}_DEG"] >= vars[f"Train_DEP_{jour}_{numero}_FOR"] + 33,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
    )
    contr[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = m.addConstr(
        vars[f"Train_DEP_{jour}_{numero}_DEG"] + 7 <= creneau_depart,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
    )

# Contraintes d'indisponibilité
'''À faire quand tout le reste fonctionne'''

# Contraintes de raccordement

for index in departs.index :
    jour_depart = departs[DepartsColumnNames.DEP_DATE][index]
    numero_depart = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    id_train_depart = (jour_depart, numero_depart)
    trains_arrivee_lies = composition_train_depart(data_dict, id_train_depart)
    print(trains_arrivee_lies)
    for jour_arrivee, numero_arrivee in trains_arrivee_lies:
        contr[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = m.addConstr(
            vars[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= vars[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 3,
            name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
        )

m.update()
#m.display()
m.optimize()

for var in vars:
    print(f"{var}: {vars[var].x}")
    print("triplet :", Horaires.entier_vers_triplet(int(vars[var].x)))