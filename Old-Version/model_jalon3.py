"""Ce module rassemble tous les apports liés au jalon 2"""
import time
from gurobipy import *
from tqdm import tqdm
from lecture_donnees import (INSTANCE, ARRIVEES, DEPARTS, DATA_DICT,
                             composition_train_depart_creneau,
                             composition_train_arrivee_creneau,
                             indispo_to_intervalle, get_all_days_as_numbers)
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  ChantiersColumnNames, TachesColumnNames, RoulementsColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS)
from model_jalon2 import MODEL, VARIABLES, CONTRAINTES, MAJORANT, linearise_abs

#import display_tools.display_agenda as dis_agenda
import display_tools.compute_stats as dis_tracks

overall_start_time = time.time()
EPSILON = 1/4

ARRIVEES_DATE = ARRIVEES[ArriveesColumnNames.ARR_DATE]
ARRIVEES_TR_NB = ARRIVEES[ArriveesColumnNames.ARR_TRAIN_NUMBER]
ARRIVEES_CRENEAUX = ARRIVEES[ArriveesColumnNames.ARR_CRENEAU]
DEPARTS_DATE = DEPARTS[DepartsColumnNames.DEP_DATE]
DEPARTS_TR_NB = DEPARTS[DepartsColumnNames.DEP_TRAIN_NUMBER]
DEPARTS_CRENEAUX = DEPARTS[DepartsColumnNames.DEP_CRENEAU]

## VARIABLES
# Variables de décision concernant l'occupation des voies (jalon 2)
NB_VOIES = DATA_DICT[InstanceSheetNames.SHEET_CHANTIERS][ChantiersColumnNames.CHANTIER_CAPA_VOIES]
ALL_DAYS = get_all_days_as_numbers(DATA_DICT)
TACHES_HUMAINES = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
ROULEMENTS_AGENTS = DATA_DICT[InstanceSheetNames.SHEET_ROULEMENTS]

# Dictionnaire contenant le nom de toutes les variables relatives à une tâche
DICT_TACHES = {}
# initialisation
for index in TACHES_HUMAINES.index:
    type_train = TACHES_HUMAINES[TachesColumnNames.TASK_TYPE_TRAIN][index]
    task_id = TACHES_HUMAINES[TachesColumnNames.TASK_ORDRE][index]
    duree = int(TACHES_HUMAINES[TachesColumnNames.TASK_DURATION][index])
    DICT_TACHES[type_train+"_"+task_id] = {"Attribution":[], "Horaire":[], "Duree": duree}
DICT_TACHES_PAR_AGENT = {}
# "agent": {"Cycle":[], "Attribution":[], "Horaire":[]}
# contient les clés des variables pour accéder au dictionnaire VARIABLES

nb_variables_new = 0
def add_vars_taches_humaines():
    global nb_variables_new
    for roulement_id in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NAME].index:
        jours_dispos = [int(day) for day in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
        for jour in ALL_DAYS:
            if not jour%7+1 in jours_dispos:
                continue
            nombre_agents = int(ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
            cycles = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
            connaissances_chantiers = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CONN_CHANTIER][roulement_id].split(';')
            for agent in range(1, nombre_agents + 1):
                dict_agent_name = f"roul{roulement_id}_jour{str(jour)}_ag{str(agent)}"
                DICT_TACHES_PAR_AGENT[dict_agent_name] = {"Cycle":[], "Attribution":[], "Horaire":[]}
                for cycle in cycles :
                    VARIABLES[f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}"] = MODEL.addVar(
                        name = f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}",
                        vtype = GRB.BINARY
                    )
                    DICT_TACHES_PAR_AGENT[dict_agent_name]["Cycle"].append(f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}")
                    nb_variables_new += 1
                for chantier in connaissances_chantiers :
                    taches_sub_chantier = TACHES_HUMAINES[TACHES_HUMAINES[TachesColumnNames.TASK_CHANTIER] == chantier]
                    trains_chantier = ARRIVEES if chantier == "WPY_REC" else DEPARTS
                    trains_dates = ARRIVEES_DATE if chantier == "WPY_REC" else DEPARTS_DATE
                    trains_id = ARRIVEES_TR_NB if chantier == "WPY_REC" else DEPARTS_TR_NB
                    for train_index in trains_chantier.index:
                        train_day = trains_dates[train_index]
                        train_number = trains_id[train_index]
                        for tache_id in taches_sub_chantier.index:
                            task_name = taches_sub_chantier[TachesColumnNames.TASK_ORDRE][tache_id]
                            task_train_type = taches_sub_chantier[TachesColumnNames.TASK_TYPE_TRAIN][tache_id]
                            VARIABLES[f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}"] = MODEL.addVar(
                                name = f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}",
                                vtype = GRB.BINARY
                            )
                            VARIABLES[f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}"] = MODEL.addVar(
                                name = f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}",
                                vtype = GRB.INTEGER
                            )
                            DICT_TACHES[task_train_type+"_"+task_name]["Attribution"].append(f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                            DICT_TACHES[task_train_type+"_"+task_name]["Horaire"].append(f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                            DICT_TACHES_PAR_AGENT[dict_agent_name]["Attribution"].append(f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                            DICT_TACHES_PAR_AGENT[dict_agent_name]["Horaire"].append(f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                            nb_variables_new += 2
add_vars_taches_humaines()

def add_constr_agent_cycle_unique():
    for jour in ALL_DAYS:
        for roulement_id in ROULEMENTS_AGENTS.index:
            jours_dispos = [int(day) for day in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
            if not jour%7+1 in jours_dispos:
                continue
            nombre_agents = int(ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
            cycles = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
            for agent_id in range(1, nombre_agents+1):
                agent_somme_cycle = 0
                for cycle in cycles:
                    agent_somme_cycle += VARIABLES[f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent_id)}_cy{cycle}"]
                CONTRAINTES[f"Constr_AttrCycleUnique_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}"] = MODEL.addConstr(agent_somme_cycle <= 1, name=f"Constr_AttrCycleUnique_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}")

# Créer des dictionnaires d'association entre taches
TACHE_PRECEDENTE = {"ARR_1":"ARR",  # cas particulier à régler manuellement
                    "ARR_2":"ARR_1", "ARR_3":"ARR_2",
                    "DEP_1":"ARR_3", "DEP_2":"DEP_1", "DEP_3":"DEP_2", "DEP_4":"DEP_3"
                    }
TACHE_SUIVANTE = {"ARR_1":"ARR_2", "ARR_2":"ARR_3", "ARR_3":"DEP_1",
                  "DEP_1":"DEP_2", "DEP_2":"DEP_3", "DEP_3":"DEP_4",
                  "DEP_4":"DEP"     # cas particulier à régler manuellement
                 }

# override
def add_constr_ordre_taches_arrivee():
    # ARR_1 après arrivée du train
    for grb_var_name in DICT_TACHES["ARR_1"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        temp_df = ARRIVEES[ARRIVEES[ArriveesColumnNames.ARR_DATE] == train_day]
        temp_df = temp_df[temp_df[ArriveesColumnNames.ARR_TRAIN_NUMBER] == train_number]
        correct_index = temp_df.index[0]
        arr_cren = ARRIVEES_CRENEAUX[correct_index]
        CONTRAINTES[f"Constr_ordre_arriveeREC_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] >= arr_cren, name=f"Constr_ordre_arriveeREC_{grb_var_name}")

    # ARR_2 après ARR_1
    for grb_var_name in tqdm(DICT_TACHES["ARR_2"]["Horaire"]):
        prec=TACHE_PRECEDENTE["ARR_2"]
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        for grb_var_name_prec in DICT_TACHES[prec]["Horaire"]:
            name_elements_prec = grb_var_name_prec.split(sep="_")
            length_prec = len(name_elements_prec)
            train_day_prec, train_number_prec = name_elements_prec[length_prec-2], name_elements_prec[length_prec-1]
            if train_day == train_day_prec and train_number == train_number_prec:
                CONTRAINTES[f"Constr_ordre_arr2apresarr1_{grb_var_name}_{grb_var_name_prec}"] = MODEL.addConstr(VARIABLES[grb_var_name] >= VARIABLES[grb_var_name_prec] + 15, name=f"Constr_ordre_arr2apresarr1_{grb_var_name}")

    # ARR_2 avant ARR_3=DEB
    for grb_var_name in DICT_TACHES["ARR_2"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        CONTRAINTES[f"Constr_ordre_arr2avantDEB_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] + 45 <= VARIABLES[f"Train_ARR_{train_day}_{train_number}_DEB"], name=f"Constr_ordre_arr2avantDEB_{grb_var_name}")

# Racordement pas changé depuis jalon 1

# override
def add_constr_ordre_taches_depart():
    for grb_var_name in DICT_TACHES["DEP_2"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
    # DEP_2 après DEP_1=FOR
        CONTRAINTES[f"Constr_ordre_dep2apresFOR_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] >= VARIABLES[f"Train_DEP_{train_day}_{train_number}_FOR"] + 15, name=f"Constr_ordre_dep2apresFOR_{grb_var_name}")
    # DEP_2 avant DEP_3=DEG
        CONTRAINTES[f"Constr_ordre_dep2avantDEG_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] + 150 <= VARIABLES[f"Train_DEP_{train_day}_{train_number}_DEG"], name=f"Constr_ordre_dep2avantDEG_{grb_var_name}")

    for grb_var_name in DICT_TACHES["DEP_4"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
    # DEP_4 après DEP_3=DEG
        CONTRAINTES[f"Constr_ordre_dep4apresDEG_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] >= VARIABLES[f"Train_DEP_{train_day}_{train_number}_DEG"] + 15, name=f"Constr_ordre_dep4apresDEG_{grb_var_name}")
    # DEP_4 avant départ du train
        temp_df = DEPARTS[DEPARTS[DepartsColumnNames.DEP_DATE] == train_day]
        temp_df = temp_df[temp_df[DepartsColumnNames.DEP_TRAIN_NUMBER] == train_number]
        correct_index = temp_df.index[0]
        dep_cren = DEPARTS_CRENEAUX[correct_index]
        CONTRAINTES[f"Constr_ordre_departDEP_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] + 20 <= dep_cren, name=f"Constr_ordre_departDEP_{grb_var_name}")

def add_constr_parallelisation_machines_humains():
    """Assurer que le créneau sur lequel a lieu une tâche machine est aussi celui de l'agent qui la réalise"""
    # Tache DEB
    for grb_var_name in DICT_TACHES["ARR_3"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        CONTRAINTES[f"Constr_ordre_arr3simultDEB_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] == VARIABLES[f"Train_ARR_{train_day}_{train_number}_DEB"], name=f"Constr_ordre_arr3simultDEB_{grb_var_name}")
    # Tache FOR
    for grb_var_name in DICT_TACHES["DEP_1"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        CONTRAINTES[f"Constr_ordre_dep1simultFOR_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] == VARIABLES[f"Train_DEP_{train_day}_{train_number}_FOR"], name=f"Constr_ordre_dep1simultFOR_{grb_var_name}")
    # Tache FOR
    for grb_var_name in DICT_TACHES["DEP_3"]["Horaire"]:
        name_elements = grb_var_name.split(sep="_")
        length = len(name_elements)
        train_day, train_number = name_elements[length-2], name_elements[length-1]
        CONTRAINTES[f"Constr_ordre_dep3simultDEG_{grb_var_name}"] = MODEL.addConstr(VARIABLES[grb_var_name] == VARIABLES[f"Train_DEP_{train_day}_{train_number}_DEG"], name=f"Constr_ordre_dep3simultDEG_{grb_var_name}")

def add_constr_taches_humaines_simultanées():
    for agent_name in tqdm(DICT_TACHES_PAR_AGENT):
        for attr_1 in DICT_TACHES_PAR_AGENT[agent_name]["Attribution"]:
            name_elts_1 = attr_1.split(sep="_")
            _, var_name_1 = attr_1.split(sep="_", maxsplit=1)
            horaire_debut_1 = VARIABLES[f"H_{var_name_1}"]
            chantier_1 = name_elts_1[5] # le chantier est stocké en position 5 dans le nom de variable
            type_train_1 = "ARR" if chantier_1 == "REC" else "DEP"
            task_id_1 = name_elts_1[6]
            horaire_fin_1 = horaire_debut_1 + DICT_TACHES[type_train_1+"_"+task_id_1]["Duree"]
            for attr_2 in DICT_TACHES_PAR_AGENT[agent_name]["Attribution"]:
                if attr_1 == attr_2:
                    continue
                name_elts_2 = attr_2.split(sep="_")
                _, var_name_2 = attr_2.split(sep="_", maxsplit=1)
                horaire_debut_2 = VARIABLES[f"H_{var_name_2}"]
                chantier_2 = name_elts_2[5] # le chantier est stocké en position 5 dans le nom de variable
                type_train_2 = "ARR" if chantier_2 == "REC" else "DEP"
                task_id_2 = name_elts_2[6]
                horaire_fin_2 = horaire_debut_2 + DICT_TACHES[type_train_2+"_"+task_id_2]["Duree"]

                # var binaire delta_arr2_dep1
                delta1_name = f"delta_Db2-inf-Fn1_{var_name_1}_{var_name_2}"
                VARIABLES[delta1_name] = MODEL.addVar(vtype=GRB.BINARY, name=delta1_name)
                CONTRAINTES["Constr1"+delta1_name] = MODEL.addConstr(MAJORANT * (1 - VARIABLES[delta1_name]) >= horaire_debut_2 - horaire_fin_1 + EPSILON,
                                                                    name="Constr1_"+delta1_name)
                CONTRAINTES["Constr2"+delta1_name] = MODEL.addConstr(- MAJORANT * VARIABLES[delta1_name] <= horaire_debut_2 - horaire_fin_1 + EPSILON,
                                                                    name="Constr2_"+delta1_name)
                # var binaire delta_arr1_dep2
                delta2_name = f"delta_Fn2-inf-Db1_{var_name_1}_{var_name_2}"
                VARIABLES[delta2_name] = MODEL.addVar(vtype=GRB.BINARY, name=delta2_name)
                CONTRAINTES["Constr1"+delta2_name] = MODEL.addConstr(MAJORANT * (1 - VARIABLES[delta2_name]) >= horaire_fin_2 - horaire_debut_1 + EPSILON,
                                                                    name="Constr1"+delta2_name)
                CONTRAINTES["Constr2"+delta2_name] = MODEL.addConstr(- MAJORANT * VARIABLES[delta2_name] <= horaire_fin_2 - horaire_debut_1 + EPSILON,
                                                                    name="Constr2"+delta2_name)
                # Contrainte tâches agent simultanées
                cstr_name = f"Constr_TacheAgentSimult_{var_name_1}_{var_name_2}"
                CONTRAINTES[cstr_name] = MODEL.addConstr(VARIABLES[attr_1] + VARIABLES[attr_2] + VARIABLES[delta1_name] <= 2 + VARIABLES[delta2_name],
                                                    name=cstr_name)

def add_constr_indispos_chantiers_humains():
    for roulement_id in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NAME].index:
        jours_dispos = [int(day) for day in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
        for jour in ALL_DAYS:
            if not jour%7+1 in jours_dispos:
                continue
            nombre_agents = int(ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
            cycles = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
            connaissances_chantiers = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CONN_CHANTIER][roulement_id].split(';')
            for chantier in connaissances_chantiers :
                indispo_list = indispo_to_intervalle(DATA_DICT, "chantier", chantier)
                for agent in range(1, nombre_agents + 1):
                    for cycle in cycles:
                        debut_cycle, fin_cycle = cycle.split(sep="-")
                        cr_name = f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}"
                        VARIABLES[cr_name]
    pass

def add_constr_respect_horaire_agent():
    pass


add_constr_agent_cycle_unique()
add_constr_ordre_taches_arrivee()
add_constr_ordre_taches_depart()
add_constr_parallelisation_machines_humains()
add_constr_taches_humaines_simultanées()
MODEL.update()
MODEL.optimize()
print("Nombre de variables ajoutées au modèle : ", nb_variables_new)