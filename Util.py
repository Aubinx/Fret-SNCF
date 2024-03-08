
ORDERED_MACHINES = ["DEB", "FOR", "DEG"]

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
    CHANITER_CAPA_VOIES = "Nombre de voies"
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
