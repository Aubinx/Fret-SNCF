from gurobipy import *
from tqdm import tqdm
import donnees_trains
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  TachesColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER)
from model_jalon2 import FretModelJal2

class FretModelJal3(FretModelJal2):
    pass