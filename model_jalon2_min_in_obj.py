
from gurobipy import *

from model import MODEL, DEPARTS, DepartsColumnNames, VARIABLES, DATA_DICT, CONTRAINTES
from lecture_donnees import composition_train_depart

# Variables de décision concernant les trains au départ :
EPSILON_MINIMUM = LinExpr()
for index in DEPARTS.index:
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    
    VARIABLES[f"min_DEB_{jour}_{numero}"] = MODEL.addVar(
        name = f"min_DEB_{jour}_{numero}",
        vtype = GRB.INTEGER,
        lb = 0
    )
    EPSILON_MINIMUM += VARIABLES[f"min_DEB_{jour}_{numero}"]
    for related_train in composition_train_depart(DATA_DICT, (jour, numero)):
        date, id_name = related_train
        CONTRAINTES[f"min_DEB_depart_{jour}_{numero}_arrivee_{date}_{id_name}_MINIMUM"] = MODEL.addConstr(
        VARIABLES[f"min_DEB_{jour}_{numero}"] <= VARIABLES[f"Train_ARR_{date}_{id_name}_DEB"],
        name = f"min_DEB_depart_{jour}_{numero}_arrivee_{date}_{id_name}_MINIMUM"
    )

MODEL.setObjective(EPSILON_MINIMUM, GRB.MAXIMIZE)

MODEL.update()
# MODEL.display()
# MODEL.params.OutputFlag = 0
MODEL.optimize()
