"""Module contenant des informations utiles pour extraire et traiter les données"""

ORDERED_MACHINES = ["DEB", "FOR", "DEG"]
ORDERED_CHANTIERS = ["WPY_REC", "WPY_FOR", "WPY_DEP"]
TACHES_PAR_CHANTIER = {"WPY_REC": ["DEB"], "WPY_FOR": ["FOR", "DEG"], "WPY_DEP": []}

class InstanceSheetNames:
    SHEET_CHANTIERS = "Chantiers"
    SHEET_MACHINES = "Machines"
    SHEET_ARRIVEES = "Sillons arrivee"
    SHEET_DEPARTS = "Sillons depart"
    SHEET_CORRESPONDANCES = "Correspondances"
    SHEET_TACHES = "Taches humaines"
    SHEET_ROULEMENTS = "Roulements agents"

class ChantiersColumnNames:
    CHANTIER_NAME = "Chantier"
    CHANTIER_CAPA_VOIES = "Nombre de voies"
    CHANTIER_INDISPONIBILITES = "Indisponibilites"

class MachinesColumnNames:
    MACHINE_NAME = "Machine"
    MACHINE_TYPE_TACHE = "Type de tache"
    MACHINE_DUREE = "Duree"
    MACHINE_INDISPONIBILITES = "Indisponibilites"

class ArriveesColumnNames:
    ARR_TRAIN_NUMBER = "n°TRAIN"
    ARR_DATE = "JARR"
    ARR_HOUR = "HARR"
    ARR_CRENEAU = "Creneau"

class DepartsColumnNames:
    DEP_TRAIN_NUMBER = "n°TRAIN"
    DEP_DATE = "JDEP"
    DEP_HOUR = "HDEP"
    DEP_CRENEAU = "Creneau"

class CorrespondancesColumnNames:
    CORR_WAGON = "Id wagon"
    CORR_ARR_DATE = "Jour arrivee"
    CORR_ARR_TRAIN_NUMBER = "n°Train arrivee"
    CORR_DEP_DATE = "Jour depart"
    CORR_DEP_TRAIN_NUMBER = "n°Train depart"

class TachesColumnNames:
    TASK_TYPE_TRAIN = "Type de train"
    TASK_TYPE_HUMAN = "Type de tache humaine"
    TASK_LINK = "Lien machine"
    TASK_DURATION = "Durée"
    TASK_CHANTIER = "Chantier"
    TASK_ORDRE = "Ordre"

class RoulementsColumnNames:
    ROUL_NAME = "Roulement"
    ROUL_DAYS = "Jours de la semaine"
    ROUL_NB_AGENTS = "Nombre agents"
    ROUL_CYCLES = "Cycles horaires"
    ROUL_CONN_CHANTIER = "Connaissances chantiers"

class OutputColumnNames:
    OUT_TASK_ID = "Id tâche"
    OUT_TASK_TYPE = "Type de tâche"
    OUT_DATE = "Jour"
    OUT_START_TIME = "Heure début"
    OUT_DURATION = "Durée"
    OUT_TRAIN = "Sillon"
