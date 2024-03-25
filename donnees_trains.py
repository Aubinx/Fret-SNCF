"""
FONCTIONS UTILES POUR extraire des DONNEES des trains
"""
from util import (InstanceSheetNames, CorrespondancesColumnNames,
                  ArriveesColumnNames, DepartsColumnNames,
                  ChantiersColumnNames, MachinesColumnNames)
import horaires

def composition_train_depart(data, id_train_depart):
    """
    argument : `id_train_depart` est l'identifiant unique du train de départ considéré
    sous la frome du couple (`date`, `numero de train`)
    Renvoie `related_trains` la liste des trains à l'arrivée
    qui contiennent un wagon faisant partie du train au départ considéré
    """
    related_trains = []
    correspondances = data[InstanceSheetNames.SHEET_CORRESPONDANCES]
    for _, row in correspondances.iterrows():
        dep_train_id = (row[CorrespondancesColumnNames.CORR_DEP_DATE],
                        row[CorrespondancesColumnNames.CORR_DEP_TRAIN_NUMBER])
        if dep_train_id == id_train_depart:
            arr_train_id = (row[CorrespondancesColumnNames.CORR_ARR_DATE],
                            row[CorrespondancesColumnNames.CORR_ARR_TRAIN_NUMBER])
            related_trains.append(arr_train_id)
    return list(set(related_trains))

def composition_train_depart_creneau(data, id_train_depart):
    """
    Pour un train de départ donné sous la frome du couple (`date`, `numero de train`)
    Renvoie `creneaux` la liste des créneaux d'arrivée des trains
    qui contiennent un wagon faisant partie de ce train
    """
    trains_arrivee = composition_train_depart(data, id_train_depart)
    creneaux = []
    arrivees = data[InstanceSheetNames.SHEET_ARRIVEES]
    for index in arrivees.index :
        jour = arrivees[ArriveesColumnNames.ARR_DATE][index]
        numero = arrivees[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
        for jour_obj, numero_obj in trains_arrivee:
            if jour == jour_obj and numero == numero_obj :
                creneaux.append(arrivees[ArriveesColumnNames.ARR_CRENEAU][index])
    return creneaux

def composition_train_arrivee(data, id_train_arrivee):
    """
    argument : `id_train_arrivee` est l'identifiant unique du train de départ considéré
    sous la frome du couple (`date`, `numero de train`)
    Renvoie `related_trains` la liste des trains au départ
    qui contiennent un wagon faisant partie du train à l'arrivée considéré
    """
    related_trains = []
    correspondances = data[InstanceSheetNames.SHEET_CORRESPONDANCES]
    for _, row in correspondances.iterrows():
        arr_train_id = (row[CorrespondancesColumnNames.CORR_ARR_DATE],
                        row[CorrespondancesColumnNames.CORR_ARR_TRAIN_NUMBER])
        if arr_train_id == id_train_arrivee:
            dep_train_id = (row[CorrespondancesColumnNames.CORR_DEP_DATE],
                            row[CorrespondancesColumnNames.CORR_DEP_TRAIN_NUMBER])
            related_trains.append(dep_train_id)
    return list(set(related_trains))

def composition_train_arrivee_creneau(data, id_train_arrivee):
    """
    Pour un train à l'arrivée donné sous la frome du couple (`date`, `numero de train`)
    Renvoie `creneaux` la liste des créneaux de départ de tous les trains
    à qui il donne au moins un wagon
    """
    trains_depart = composition_train_arrivee(data, id_train_arrivee)
    departs = data[InstanceSheetNames.SHEET_DEPARTS]
    creneaux = []
    for index in departs.index :
        jour = departs[DepartsColumnNames.DEP_DATE][index]
        numero = departs[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
        for jour_obj, numero_obj in trains_depart:
            if jour == jour_obj and numero == numero_obj :
                creneaux.append(departs[DepartsColumnNames.DEP_CRENEAU][index])
    return creneaux

def indispo_to_intervalle(data, target_type, target_id):
    """
    Cherche les indisponibilités (selon `target_type`) de la machine/chantier `target_id`
    Renvoie ces indisponibilités sous la forme d'une liste de couple de créneaux (`debut`, `fin`)
    """
    assert target_type in ["chantier", "machine"]
    if target_type == "chantier":
        sheet = InstanceSheetNames.SHEET_CHANTIERS
        name_column = ChantiersColumnNames.CHANTIER_NAME
        indisp_column = ChantiersColumnNames.CHANTIER_INDISPONIBILITES
    elif target_type == "machine":
        sheet = InstanceSheetNames.SHEET_MACHINES
        name_column = MachinesColumnNames.MACHINE_NAME
        indisp_column = MachinesColumnNames.MACHINE_INDISPONIBILITES

    indispos_creneaux = []
    machine_data = data[sheet]
    for _, row in machine_data.iterrows():
        if row[name_column] == target_id:
            total_indisp = row[indisp_column]
            if total_indisp == "0":
                break
            list_indisp = total_indisp.split(sep=";")
            for indisp in list_indisp:
                creneau_start, creneau_end = creneau_from_indisp(indispos_creneaux, indisp)
                indispos_creneaux.append((creneau_start, creneau_end))
    return indispos_creneaux

def creneau_from_indisp(indispos_creneaux, indisp):
    """
    Prend en argument une indisponibilité telle qu'extraite directement de l'excel
    Renvoie les créneaux de début et fin associés
    """
    indisp = indisp.lstrip("(").rstrip(")")
    day_number, time_span = indisp.split(",")
    day_number = int(day_number)
    time_start, time_end = time_span.split("-")
    time_start = time_start.strip(" ")
    time_end = time_end.strip(" ")
    start_hour, start_minute = [int(var) for var in time_start.split(":")]
    end_hour, end_minute = [int(var) for var in time_end.split(":")]
    creneau_start = horaires.triplet_vers_entier(day_number, start_hour, start_minute)
    creneau_end = horaires.triplet_vers_entier(day_number, end_hour, end_minute)
    if time_start == time_end: # l'indsiponibilité dure 24h
        creneau_end = horaires.triplet_vers_entier(day_number+1, end_hour, end_minute)
        if day_number == 7: # l'indisponibilité déborde sur le lundi
            # -> elle doit aussi être prise en compte pour le lundi de la semaine 1
            indispos_creneaux.append((0, horaires.triplet_vers_entier(1, end_hour, end_minute)))
    return creneau_start,creneau_end
