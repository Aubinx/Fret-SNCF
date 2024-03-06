# Modules
from gurobipy import *

from LectureDonnees import data_dict
from Util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames

# Modèle
m = Model("Fret SNCF")

## VARIABLES
vars = {}

# Variables de décision concernant les trains à l'arrivée :
arrivees = data_dict[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
    heure = arrivees[ArriveesColumnNames.ARR_HOUR][index]
    vars[f"Train_ARR_{jour}_{heure}_DEB"] = m.addVar(
        name = f"Train_ARR_{jour}_{heure}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
departs = data_dict[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    heure = departs[DepartsColumnNames.DEP_HOUR][index]
    vars[f"Train_DEP_{jour}_{heure}_FOR"] = m.addVar(
        name = f"Train_DEP_{jour}_{heure}_FOR",
        vtype = GRB.INTEGER,
        lb = 0
    )
    vars[f"Train_DEP_{jour}_{heure}_DEG"] = m.addVar(
        name = f"Train_DEP_{jour}_{heure}_DEG",
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
    heure = arrivees[ArriveesColumnNames.ARR_HOUR][index]
    creneau_arrivee = arrivees[ArriveesColumnNames.ARR_CRENEAU][index]
    contr[f"Train_ARR_{jour}_{heure}_ORDRE"] = m.addConstr(
        vars[f"Train_ARR_{jour}_{heure}_DEB"] >= creneau_arrivee + 12,
        name = f"Train_ARR_{jour}_{heure}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
for index in departs.index :
    jour = departs[DepartsColumnNames.DEP_DATE][index]
    heure = departs[DepartsColumnNames.DEP_HOUR][index]
    creneau_departs = arrivees[DepartsColumnNames.DEP_CRENEAU][index]
    contr[f"Train_DEP_{jour}_{heure}_ORDRE_DEG"] = m.addConstr(
        vars[f"Train_DEP_{jour}_{heure}_DEG"] >= vars[f"Train_DEP_{jour}_{heure}_FOR"] + 33,
        name = f"Train_DEP_{jour}_{heure}_ORDRE_DEG"
    )
    contr[f"Train_DEP_{jour}_{heure}_ORDRE_DEP"] = m.addConstr(
        vars[f"Train_DEP_{jour}_{heure}_DEG"] + 7 <= 0, # HEURE DE DEPART
        name = f"Train_DEP_{jour}_{heure}_ORDRE_DEP"
    )

# Contraintes d'indisponibilité

'''À faire quand tout le reste fonctionne'''

#m.update()
#m.display()
