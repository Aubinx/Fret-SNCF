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

def add_vars_taches_humaines():
    for roulement_id in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NAME].index:
        jours_dispos = [int(day) for day in ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
        for jour in ALL_DAYS:
            if not jour%7+1 in jours_dispos:
                continue
            nombre_agents = int(ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
            cycles = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
            for agent in range(1, nombre_agents + 1):
                for cycle in cycles :
                    VARIABLES[f"Cr_{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}"] = MODEL.addVar(
                        name = f"Cr_{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle}",
                        vtype = GRB.BINARY
                    )
                connaissances_chantiers = ROULEMENTS_AGENTS[RoulementsColumnNames.ROUL_CONN_CHANTIER][roulement_id].split(';')
                for chantier in connaissances_chantiers :
                    taches_sub_chantier = TACHES_HUMAINES[TACHES_HUMAINES[TachesColumnNames.TASK_CHANTIER] == chantier]
                    for tache_id in taches_sub_chantier.index:
                        task_name = taches_sub_chantier[TachesColumnNames.TASK_ORDRE][tache_id]
                        VARIABLES[f"Attr_{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}"] = MODEL.addVar(
                            name = f"Attr_{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}",
                            vtype = GRB.BINARY
                        )
                        VARIABLES[f"H_{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}"] = MODEL.addVar(
                            name = f"H_{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}",
                            vtype = GRB.BINARY
                        )

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
                    agent_somme_cycle += VARIABLES[f"Cr_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}_cy{cycle}"]
                MODEL.addConstr(agent_somme_cycle <= 1, name=f"Constr_AttrCycleUnique_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}")

# override
def add_constr_ordre_taches_arrivee():
    pass

# override
def add_constr_ordre_taches_depart():
    pass

def add_constr_taches_humaines_simultanées():
    pass

def add_constr_indispos_chantiers_humains():
    pass

def add_constr_respect_horaire_agent():
    pass

add_vars_taches_humaines()
add_constr_agent_cycle_unique()
