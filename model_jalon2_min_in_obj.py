
from gurobipy import *

from model import DEPARTS, DepartsColumnNames, DATA_DICT
from lecture_donnees import composition_train_depart


def model_jalon2_min_in_obj(model, variables, contraintes):
    """
    Implementation du minimum pour le premier wagon arriant au chantier FOR
    
    Retourne l'expression Gurobi à MAXIMISER 
    """
    # Variables de décision concernant les trains au départ :
    epsilon_minimum = LinExpr()
    for index in DEPARTS.index:
        jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
        numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]

        variables[f"min_DEB_{jour}_{numero}"] = model.addVar(
            name = f"min_DEB_{jour}_{numero}",
            vtype = GRB.INTEGER,
            lb = 0
        )
        epsilon_minimum += variables[f"min_DEB_{jour}_{numero}"]
        for related_train in composition_train_depart(DATA_DICT, (jour, numero)):
            date, id_name = related_train
            contraintes[f"min_DEB_depart_{jour}_{numero}_arrivee_{date}_{id_name}_MINIMUM"] = model.addConstr(
                variables[f"min_DEB_{jour}_{numero}"] <= variables[f"Train_ARR_{date}_{id_name}_DEB"],
                name = f"min_DEB_depart_{jour}_{numero}_arrivee_{date}_{id_name}_MINIMUM"
        )

    return epsilon_minimum
