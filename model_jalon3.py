from gurobipy import *
from tqdm import tqdm
import donnees_trains
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  TachesColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER)
from model_jalon2 import FretModelJal2

class FretModelJal3(FretModelJal2):

    def add_vars_tertiary_taches_humaines(self):
        pass

    def add_constr_agent_cycle_unique(self):
        pass

    # override
    def add_constr_ordre_taches_arrivee(self):
        pass

    # override
    def add_constr_ordre_taches_depart(self):
        pass

    def add_constr_taches_humaines_simultanées(self):
        pass

    def add_constr_indispos_chantiers_humains(self):
        pass

    def add_constr_respect_horaire_agent(self):
        pass
