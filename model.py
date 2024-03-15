"""Génère et optimise le modèle gurobi associé à l'instance considérée"""
# Modules
from gurobipy import *
from lecture_donnees import INSTANCE, DATA_DICT, composition_train_depart, indispo_to_intervalle
from util import InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames, TachesColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER
import display_tools.display_by_train as dis_agenda

def linearise_abs(model : Model, variables, contraintes, expr_var : LinExpr, var_name : str, majorant):
    """
    linéarise la variable `|expr_var|` en ajoutant des variables et des contraintes au modèle gurobi `model` ainsi que dans les dictionnaire `variables` et `contraintes`
    Renvoie l'expression linéaire de `|expr_var|`
    """
    # Créer la variable binaire indicatrice et les contraintes associées
    delta = model.addVar(name=f"linabs_binary_{var_name}", vtype=GRB.BINARY)
    cb1 = model.addConstr(majorant * delta >= expr_var, name=f"linabs_ConstrBinary1_{var_name}")
    cb2 = model.addConstr(majorant * (delta - 1) <= expr_var, name=f"linabs_ConstrBinary2_{var_name}")

    # Créer la nouvelle variable entière et les contraintes associées
    prod = model.addVar(name=f"linabs_integer_{var_name}", vtype=GRB.INTEGER, lb=0)
    ci1 = model.addConstr(prod >= expr_var, name=f"linabs_ConstrInteger1_{var_name}")
    ci2 = model.addConstr(prod <= majorant * delta, name=f"linabs_ConstrInteger2_{var_name}")
    ci3 = model.addConstr(prod <= expr_var - majorant * (delta - 1), name=f"linabs_ConstrInteger3_{var_name}")

    # Mettre à jour les dictionnaires des variables et contraintes
    model.update()
    variables[delta.VarName] = delta
    variables[prod.VarName] = prod
    contraintes[cb1.ConstrName] = cb1
    contraintes[cb2.ConstrName] = cb2
    contraintes[ci1.ConstrName] = ci1
    contraintes[ci2.ConstrName] = ci2
    contraintes[ci3.ConstrName] = ci3
    linear_abs = LinExpr(2 * prod - expr_var)
    return linear_abs

# Modèle
MODEL = Model("Fret SNCF")
MAJORANT = 10**6

## VARIABLES
VARIABLES = {}

# Variables de décision concernant les trains à l'arrivée :
ARRIVEES = DATA_DICT[InstanceSheetNames.SHEET_ARRIVEES]
for index in ARRIVEES.index:
    jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
    numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] = MODEL.addVar(
        name = f"Train_ARR_{jour}_{numero}_DEB",
        vtype = GRB.INTEGER,
        lb = 0
    )

# Variables de décision concernant les trains au départ :
DEPARTS = DATA_DICT[InstanceSheetNames.SHEET_DEPARTS]
for index in DEPARTS.index:
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
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

# Variables de décision concernant l'occupation des voies (jalon 2)
'''À faire quand tout le reste fonctionne'''

## CONTRAINTES
CONTRAINTES = {}

# Contraintes sur l'ordre des tâches du train d'arrivée
for index in ARRIVEES.index :
    jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
    numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
    creneau_arrivee = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index]
    CONTRAINTES[f"Train_ARR_{jour}_{numero}_ORDRE"] = MODEL.addConstr(
        VARIABLES[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 60,
        name = f"Train_ARR_{jour}_{numero}_ORDRE"
    )

# Contraintes sur l'ordre des tâches du train de départ
somme_departs = 0
for index in DEPARTS.index :
    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    creneau_depart = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index]
    CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = MODEL.addConstr(
        VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] >= VARIABLES[f"Train_DEP_{jour}_{numero}_FOR"] + 165,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
    )
    CONTRAINTES[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = MODEL.addConstr(
        VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] + 35 <= creneau_depart,
        name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
    )
#     somme_departs += VARIABLES[f"Train_DEP_{jour}_{numero}_DEG"] + 35 - creneau_depart
# MODEL.setObjective(somme_departs, GRB.MINIMIZE)

# Contraintes de raccordement
for index in DEPARTS.index :
    jour_depart = DEPARTS[DepartsColumnNames.DEP_DATE][index]
    numero_depart = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
    id_train_depart = (jour_depart, numero_depart)
    trains_arrivee_lies = composition_train_depart(DATA_DICT, id_train_depart)
    for jour_arrivee, numero_arrivee in trains_arrivee_lies:
        CONTRAINTES[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = MODEL.addConstr(
            VARIABLES[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= VARIABLES[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 15,
            name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
        )

# Contrainte de placement des tâches sur des créneaux horaires
new_vars = []
for nom_variable in VARIABLES.keys():
    train_str, rest = nom_variable.split("_", maxsplit=1)
    train_str = train_str.lower()
    new_var = f"PLACEMENT_CRENEAU_{train_str}_{rest}"
    new_vars.append((new_var, MODEL.addVar(vtype=GRB.INTEGER, lb=0, name=new_var), nom_variable))
for name, variable, old_var in new_vars:
    VARIABLES[name] = variable
    new_cstr = "Constr_" + name
    CONTRAINTES[new_cstr] = MODEL.addConstr(variable * 15 == VARIABLES[old_var],
                                            name=new_cstr)

# Contraintes d'indisponibilité
# Indisponibilités Machines
for machine in ORDERED_MACHINES:
    df = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
    for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(DATA_DICT, "machine", machine)):
        duree_task = int(df[df[TachesColumnNames.TASK_LINK]==f"{machine}="][TachesColumnNames.TASK_DURATION])
        if machine == ORDERED_MACHINES[0]:
            for index in ARRIVEES.index :
                jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
                numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                creneau_arrivee = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index]
                to_abs = 2 * VARIABLES[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                name_new_var = f"INDISPO_train_ARR_{jour}_{numero}_{machine}_{index_indisp}"
                cstr_name = "Constr_"+name_new_var
                lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, name_new_var, MAJORANT)
                CONTRAINTES[cstr_name] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)
        else:
            for index in DEPARTS.index :
                jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
                numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                creneau_arrivee = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index]
                to_abs = 2 * VARIABLES[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                name_new_var = f"INDISPO_train_DEP_{jour}_{numero}_{machine}_{index_indisp}"
                cstr_name = "Constr_"+name_new_var
                lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, name_new_var, MAJORANT)
                CONTRAINTES[cstr_name] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)

# Indisponibilités Chantiers
for chantier in ORDERED_CHANTIERS:
    df = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
    for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(DATA_DICT, "chantier", chantier)):
        for machine in TACHES_PAR_CHANTIER[chantier]:
            duree_task = int(df[df[TachesColumnNames.TASK_LINK]==f"{machine}="][TachesColumnNames.TASK_DURATION])
            if machine == ORDERED_MACHINES[0]:
                for index in ARRIVEES.index :
                    jour = ARRIVEES[ArriveesColumnNames.ARR_DATE][index]
                    numero = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                    creneau_arrivee = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU][index]
                    to_abs = 2 * VARIABLES[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                    name_new_var = f"INDISPO_train_ARR_{jour}_{numero}_{chantier}_{machine}_{index_indisp}"
                    cstr_name = "Constr_"+name_new_var
                    lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, name_new_var, MAJORANT)
                    CONTRAINTES[cstr_name] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)
            else:
                for index in DEPARTS.index :
                    jour = DEPARTS[DepartsColumnNames.DEP_DATE][index]
                    numero = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                    creneau_arrivee = DEPARTS[DepartsColumnNames.DEP_CRENEAU][index]
                    to_abs = 2 * VARIABLES[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                    name_new_var = f"INDISPO_train_DEP_{jour}_{numero}_{chantier}_{machine}_{index_indisp}"
                    cstr_name = "Constr_"+name_new_var
                    lin_abs = linearise_abs(MODEL, VARIABLES, CONTRAINTES, to_abs, name_new_var, MAJORANT)
                    CONTRAINTES[cstr_name] = MODEL.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)

# Contraintes d'occupation des machines
def add_constr_occu_machine(model, variables, contraintes, jour1, num1, jour2, num2, machine_id, majorant):
    type_train = "ARR" if machine_id == ORDERED_MACHINES[0] else "DEP"
    train_1 = variables[f"Train_{type_train}_{jour1}_{num1}_{machine_id}"]
    train_2 = variables[f"Train_{type_train}_{jour2}_{num2}_{machine_id}"]
    to_abs = train_2 - train_1
    name_new_var = f"OCCUPATION_MACHINE_{jour1}_{num1}_{jour2}_{num2}_{machine_id}"
    cstr_name = "Constr_"+name_new_var
    lin_abs = linearise_abs(model, variables, contraintes, to_abs, name_new_var, majorant)
    contraintes[cstr_name] = model.addConstr(lin_abs >= 15, name=cstr_name)
for machine in ORDERED_MACHINES:
    if machine == ORDERED_MACHINES[0]: # Machine de débranchement
        for i, index_1 in enumerate(ARRIVEES.index):
            for index_2 in ARRIVEES.index[i+1:]:
                jour_1 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_1]
                numero_1 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
                jour_2 = ARRIVEES[ArriveesColumnNames.ARR_DATE][index_2]
                numero_2 = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
                add_constr_occu_machine(MODEL, VARIABLES, CONTRAINTES, jour_1, numero_1, jour_2, numero_2, machine, MAJORANT)
    else:
        for i, index_1 in enumerate(DEPARTS.index):
            for index_2 in DEPARTS.index[i+1:]:
                jour_1 = DEPARTS[DepartsColumnNames.DEP_DATE][index_1]
                numero_1 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
                jour_2 = DEPARTS[DepartsColumnNames.DEP_DATE][index_2]
                numero_2 = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
                add_constr_occu_machine(MODEL, VARIABLES, CONTRAINTES, jour_1, numero_1, jour_2, numero_2, machine, MAJORANT)                 

MODEL.update()
# MODEL.write(f"Modeles/model_{INSTANCE}.lp")
# MODEL.display()
# MODEL.params.OutputFlag = 0
# MODEL.optimize()

if __name__=='__main__':
    MODEL.optimize()
    indispo = []
    for machine in ORDERED_MACHINES:
        for index_indisp, (creneau_min, creneau_max) in enumerate(indispo_to_intervalle(
                    DATA_DICT, "machine", machine)):
            indispo.append((machine, creneau_min, creneau_max))
    earliest_arrival = min(ARRIVEES['JARR'])
    latest_departure = max(DEPARTS["JDEP"])
    dis_agenda.full_process(VARIABLES, (earliest_arrival, latest_departure),
                            ARRIVEES, DEPARTS, indispo)
