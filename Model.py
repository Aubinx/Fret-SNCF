# Modules
from gurobipy import *

from FretSncf_grp4.LectureDonnees import data_dict
from FretSncf_grp4.Util import InstanceSheetNames, ArrivalColumnNames, DepartureColumnNames

# Modèle
m = Model("Fret SNCF")

# Variables de décision concernant les trains à l'arrivée :
arrivees = data_dict[InstanceSheetNames.SHEET_ARRIVEES]
for index in arrivees.index:
    jour = arrivees[ArrivalColumnNames.ARR_DATE][index]
    heure = arrivees[ArrivalColumnNames.ARR_HOUR][index]
    m.addVar(name=f"Train_ARR_{jour}_{heure}_DEB",
             vtype=GRB.INTEGER, lb=0)

# Variables de décision concernant les trains au départ :
departs = data_dict[InstanceSheetNames.SHEET_DEPARTS]
for index in departs.index:
    jour = departs[DepartureColumnNames.DEP_DATE][index]
    heure = departs[DepartureColumnNames.DEP_HOUR][index]
    m.addVar(name=f"Train_DEP_{jour}_{heure}_FOR",
             vtype=GRB.INTEGER, lb=0)
    m.addVar(name=f"Train_DEP_{jour}_{heure}_DEG",
             vtype=GRB.INTEGER, lb=0)




m.update()
m.display()
