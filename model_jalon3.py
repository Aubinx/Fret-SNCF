import datetime
from gurobipy import *
from tqdm import tqdm
import donnees_trains, horaires, lecture_donnees
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  RoulementsColumnNames, TachesColumnNames)
from model_jalon2 import FretModelJal2

class FretModelJal3(FretModelJal2):
    # additional variables
    horaires_arrivees = {}
    horaires_departs = {}
    all_days = []
    dict_taches = {} # "Duree": duree, f"train" : {"Attribution":[], "Horaire":[]}
    dict_taches_par_agent = {} # "agent": {"Cycle":[], "Attribution":[], "Horaire":[]}

    def roulements(self):
        """Renvoie le dataframe des roulements d'agents"""
        return self.data[InstanceSheetNames.SHEET_ROULEMENTS]
    def taches_humaines(self):
        """Renvoie le dataframe des taches humaines à réaliser"""
        return self.data[InstanceSheetNames.SHEET_TACHES]

    # override
    def __init__(self, _data):
        super().__init__(_data)
        try:
            self.horaires_arrivees = donnees_trains.dict_horaires_arrivees(_data)
            self.horaires_departs = donnees_trains.dict_horaires_departs(_data)
            self.all_days = lecture_donnees.get_all_days_as_numbers(_data)
        except:
            self.horaires_arrivees = {}
            self.horaires_departs = {}
            self.all_days = []
        for index in self.taches_humaines().index:
            type_train = self.taches_humaines()[TachesColumnNames.TASK_TYPE_TRAIN][index]
            task_id = self.taches_humaines()[TachesColumnNames.TASK_ORDRE][index]
            duree = int(self.taches_humaines()[TachesColumnNames.TASK_DURATION][index])
            self.dict_taches[type_train+"_"+task_id] = {"Duree": duree}

    # override
    def reset_model(self):
        super().reset_model()
        self.horaires_arrivees = {}
        self.horaires_departs = {}
        self.all_days = []

    # override
    def load_whole_model(self):
        super().load_whole_model()
        self.add_vars_tertiary_taches_humaines()
        self.add_constr_ordre_taches_arrivee()
        self.add_constr_ordre_taches_depart()
        self.add_constr_attrib_tache_unique()
        self.add_constr_respect_horaire_agent()
        self.add_constr_agent_cycle_unique()
        self.add_constr_parallelisation_machines_humains()
        self.add_constr_taches_humaines_simultanées()
        self.add_constr_indispos_chantiers_humains()
        self.create_model_objective_jalon3()
        self.set_model_objective_jalon3()

    def set_model_objective_jalon3(self):
        self.model.setObjective(self.obj_function, GRB.MINIMIZE) 

    def add_vars_tertiary_taches_humaines(self):
        for roulement_id in self.roulements()[RoulementsColumnNames.ROUL_NAME].index:
            jours_dispos = [int(day) for day in self.roulements()[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
            for jour in self.all_days:
                if not jour%7+1 in jours_dispos:
                    continue
                nombre_agents = int(self.roulements()[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
                cycles = self.roulements()[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
                connaissances_chantiers = self.roulements()[RoulementsColumnNames.ROUL_CONN_CHANTIER][roulement_id].split(';')
                for agent in range(1, nombre_agents + 1):
                    dict_agent_name = f"roul{roulement_id}_jour{str(jour)}_ag{str(agent)}"
                    self.dict_taches_par_agent[dict_agent_name] = {"Cycle":[], "Attribution":[], "Horaire":[]}
                    for cycle_index in range(len(cycles)) :
                        self.variables[f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle_index}"] = self.model.addVar(
                            name = f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle_index}",
                            vtype = GRB.BINARY
                        )
                        self.dict_taches_par_agent[dict_agent_name]["Cycle"].append(f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle_index}")
                    for chantier in connaissances_chantiers :
                        taches_sub_chantier = self.taches_humaines()[self.taches_humaines()[TachesColumnNames.TASK_CHANTIER] == chantier]
                        trains_chantier = self.arrivees() if chantier == "WPY_REC" else self.departs()
                        trains_dates = self.arrivees()[ArriveesColumnNames.ARR_DATE] if chantier == "WPY_REC" else self.departs()[DepartsColumnNames.DEP_DATE]
                        trains_id = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER] if chantier == "WPY_REC" else self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER]
                        for tache_id in taches_sub_chantier.index:
                            task_name = taches_sub_chantier[TachesColumnNames.TASK_ORDRE][tache_id]
                            task_train_type = taches_sub_chantier[TachesColumnNames.TASK_TYPE_TRAIN][tache_id]
                            for train_index in trains_chantier.index:
                                train_day = trains_dates[train_index]
                                train_number = trains_id[train_index]
                                if f"{train_day}_{train_number}" not in self.dict_taches[f"{task_train_type}_{task_name}"]:
                                    self.dict_taches[f"{task_train_type}_{task_name}"][f"{train_day}_{train_number}"] = {"Attribution":[], "Horaire":[]}
                                self.variables[f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}"] = self.model.addVar(
                                    name = f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}",
                                    vtype = GRB.BINARY
                                )
                                self.variables[f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}"] = self.model.addVar(
                                    name = f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}",
                                    vtype = GRB.INTEGER
                                )
                                self.dict_taches[f"{task_train_type}_{task_name}"][f"{train_day}_{train_number}"]["Attribution"].append(f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                                self.dict_taches[f"{task_train_type}_{task_name}"][f"{train_day}_{train_number}"]["Horaire"].append(f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                                self.dict_taches_par_agent[dict_agent_name]["Attribution"].append(f"Attr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")
                                self.dict_taches_par_agent[dict_agent_name]["Horaire"].append(f"H_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_{chantier}_{task_name}_train_{train_day}_{train_number}")

    def add_constr_agent_cycle_unique(self):
        for jour in self.all_days:
            for roulement_id in self.roulements().index:
                jours_dispos = [int(day) for day in self.roulements()[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
                if not jour%7+1 in jours_dispos:
                    continue
                nombre_agents = int(self.roulements()[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
                cycles = self.roulements()[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
                for agent_id in range(1, nombre_agents+1):
                    agent_somme_cycle = 0
                    for cycle_index in range(len(cycles)):
                        agent_somme_cycle += self.variables[f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent_id)}_cy{cycle_index}"]
                    self.contraintes[f"Constr_AttrCycleUnique_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}"] = self.model.addConstr(agent_somme_cycle <= 1, name=f"Constr_AttrCycleUnique_{roulement_id}_jour{str(jour)}_ag{str(agent_id)}")

    # override
    def add_constr_ordre_taches_arrivee(self):
        # ARR_1 après arrivée du train
        for train_name in self.dict_taches["ARR_1"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            temp_df = self.arrivees()[self.arrivees()[ArriveesColumnNames.ARR_DATE] == train_day]
            temp_df = temp_df[temp_df[ArriveesColumnNames.ARR_TRAIN_NUMBER] == train_number]
            correct_index = temp_df.index[0]
            arr_cren = self.arrivees()[ArriveesColumnNames.ARR_CRENEAU][correct_index]
            for grb_var_name in self.dict_taches["ARR_1"][train_name]["Horaire"]:
                self.contraintes[f"Constr_ordre_arriveeREC_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] >= arr_cren, name=f"Constr_ordre_arriveeREC_{grb_var_name}")

        # ARR_2 après ARR_1
        for train_name in tqdm(self.dict_taches["ARR_2"], desc="ARR_2 après ARR_1"):
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["ARR_2"][train_name]["Horaire"]:
                for grb_var_name_prec in self.dict_taches["ARR_1"][train_name]["Horaire"]:
                    self.contraintes[f"Constr_ordre_arr2apresarr1_{grb_var_name}_{grb_var_name_prec}"] = self.model.addConstr(self.variables[grb_var_name] >= self.variables[grb_var_name_prec] + 15, name=f"Constr_ordre_arr2apresarr1_{grb_var_name}_{grb_var_name_prec}")

        # ARR_2 avant ARR_3=DEB
        for train_name in self.dict_taches["ARR_2"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["ARR_2"][train_name]["Horaire"]:
                self.contraintes[f"Constr_ordre_arr2avantDEB_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] + 45 <= self.variables[f"Train_ARR_{train_day}_{train_number}_DEB"], name=f"Constr_ordre_arr2avantDEB_{grb_var_name}")

    # override
    def add_constr_ordre_taches_depart(self):
        for train_name in self.dict_taches["DEP_2"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["DEP_2"][train_name]["Horaire"]:
        # DEP_2 après DEP_1=FOR
                self.contraintes[f"Constr_ordre_dep2apresFOR_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] >= self.variables[f"Train_DEP_{train_day}_{train_number}_FOR"] + 15, name=f"Constr_ordre_dep2apresFOR_{grb_var_name}")
        # DEP_2 avant DEP_3=DEG
                self.contraintes[f"Constr_ordre_dep2avantDEG_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] + 150 <= self.variables[f"Train_DEP_{train_day}_{train_number}_DEG"], name=f"Constr_ordre_dep2avantDEG_{grb_var_name}")

        for train_name in self.dict_taches["DEP_4"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            temp_df = self.departs()[self.departs()[DepartsColumnNames.DEP_DATE] == train_day]
            temp_df = temp_df[temp_df[DepartsColumnNames.DEP_TRAIN_NUMBER] == train_number]
            correct_index = temp_df.index[0]
            dep_cren = self.departs()[DepartsColumnNames.DEP_CRENEAU][correct_index]
            for grb_var_name in self.dict_taches["DEP_4"][train_name]["Horaire"]:
        # DEP_4 après DEP_3=DEG
                self.contraintes[f"Constr_ordre_dep4apresDEG_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] >= self.variables[f"Train_DEP_{train_day}_{train_number}_DEG"] + 15, name=f"Constr_ordre_dep4apresDEG_{grb_var_name}")
        # DEP_4 avant départ du train
                self.contraintes[f"Constr_ordre_departDEP_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] + 20 <= dep_cren, name=f"Constr_ordre_departDEP_{grb_var_name}")

    def add_constr_parallelisation_machines_humains(self):
        """Assurer que le créneau sur lequel a lieu une tâche machine est aussi celui de l'agent qui la réalise"""
        # Tache DEB
        for train_name in self.dict_taches["ARR_3"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["ARR_3"][train_name]["Horaire"]:
                self.contraintes[f"Constr_ordre_arr3simultDEB_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] == self.variables[f"Train_ARR_{train_day}_{train_number}_DEB"], name=f"Constr_ordre_arr3simultDEB_{grb_var_name}")
        # Tache FOR
        for train_name in self.dict_taches["DEP_1"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["DEP_1"][train_name]["Horaire"]:
                self.contraintes[f"Constr_ordre_dep1simultFOR_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] == self.variables[f"Train_DEP_{train_day}_{train_number}_FOR"], name=f"Constr_ordre_dep1simultFOR_{grb_var_name}")
        # Tache FOR
        for train_name in self.dict_taches["DEP_3"]:
            if train_name == "Duree":
                continue
            train_day, train_number = train_name.split(sep="_")
            for grb_var_name in self.dict_taches["DEP_3"][train_name]["Horaire"]:
                self.contraintes[f"Constr_ordre_dep3simultDEG_{grb_var_name}"] = self.model.addConstr(self.variables[grb_var_name] == self.variables[f"Train_DEP_{train_day}_{train_number}_DEG"], name=f"Constr_ordre_dep3simultDEG_{grb_var_name}")

    def add_constr_taches_humaines_simultanées(self):
        for agent_name in tqdm(self.dict_taches_par_agent, desc="Taches Simult Agent"):
            for attr_1 in self.dict_taches_par_agent[agent_name]["Attribution"]:
                name_elts_1 = attr_1.split(sep="_")
                _, var_name_1 = attr_1.split(sep="_", maxsplit=1)
                train_number_1 = name_elts_1[-1]
                train_day_1 = name_elts_1[-2]
                horaire_debut_1 = self.variables[f"H_{var_name_1}"]
                chantier_1 = name_elts_1[5] # le chantier est stocké en position 5 dans le nom de variable
                type_train_1 = "ARR" if chantier_1 == "REC" else "DEP"
                task_id_1 = name_elts_1[6]
                horaire_fin_1 = horaire_debut_1 + self.dict_taches[type_train_1+"_"+task_id_1]["Duree"]
                for attr_2 in self.dict_taches_par_agent[agent_name]["Attribution"]:
                    if attr_1 == attr_2:
                        continue
                    name_elts_2 = attr_2.split(sep="_")
                    _, var_name_2 = attr_2.split(sep="_", maxsplit=1)
                    train_number_2 = name_elts_2[-1]
                    train_day_2 = name_elts_2[-2]
                    horaire_debut_2 = self.variables[f"H_{var_name_2}"]
                    chantier_2 = name_elts_2[5] # le chantier est stocké en position 5 dans le nom de variable
                    type_train_2 = "ARR" if chantier_2 == "REC" else "DEP"
                    task_id_2 = name_elts_2[6]
                    horaire_fin_2 = horaire_debut_2 + self.dict_taches[type_train_2+"_"+task_id_2]["Duree"]
                    # Preprocessing pour eviter des cas particuliers inutiles
                    if type_train_1 == type_train_2 == "ARR" and (
                        self.dict_max_dep_for_train_arr[f"{train_day_1}_{train_number_1}"] <= self.horaires_arrivees[f"{train_day_2}_{train_number_2}"]
                        or self.dict_max_dep_for_train_arr[f"{train_day_2}_{train_number_2}"] <= self.horaires_arrivees[f"{train_day_1}_{train_number_1}"]
                    ):
                        continue
                    if type_train_1 == type_train_2 == "DEP" and (
                        self.dict_min_arr_for_train_dep[f"{train_day_1}_{train_number_1}"] >= self.horaires_departs[f"{train_day_2}_{train_number_2}"]
                        or self.dict_min_arr_for_train_dep[f"{train_day_2}_{train_number_2}"] >= self.horaires_departs[f"{train_day_1}_{train_number_1}"]
                    ):
                        continue
                    if type_train_1 == "ARR" and type_train_2 == "DEP" and (
                        self.dict_max_dep_for_train_arr[f"{train_day_1}_{train_number_1}"] <= self.dict_min_arr_for_train_dep[f"{train_day_2}_{train_number_2}"]
                        or self.horaires_departs[f"{train_day_2}_{train_number_2}"] <= self.horaires_arrivees[f"{train_day_1}_{train_number_1}"]
                    ):
                        continue
                    if type_train_1 == "DEP" and type_train_2 == "ARR" and (
                        self.dict_max_dep_for_train_arr[f"{train_day_2}_{train_number_2}"] <= self.dict_min_arr_for_train_dep[f"{train_day_1}_{train_number_1}"]
                        or self.horaires_departs[f"{train_day_1}_{train_number_1}"] <= self.horaires_arrivees[f"{train_day_2}_{train_number_2}"]
                    ):
                        continue
                    # var binaire delta_arr2_dep1
                    delta1_name = f"delta_Db2-inf-Fn1_{var_name_1}_{var_name_2}"
                    self.variables[delta1_name] = self.model.addVar(vtype=GRB.BINARY, name=delta1_name)
                    self.contraintes["Constr1"+delta1_name] = self.model.addConstr(self.MAJORANT * (1 - self.variables[delta1_name]) >= horaire_debut_2 - horaire_fin_1,
                                                                        name="Constr1_"+delta1_name)
                    self.contraintes["Constr2"+delta1_name] = self.model.addConstr(- self.MAJORANT * self.variables[delta1_name] <= horaire_debut_2 - horaire_fin_1,
                                                                        name="Constr2_"+delta1_name)
                    # var binaire delta_arr1_dep2
                    delta2_name = f"delta_Fn2-inf-Db1_{var_name_1}_{var_name_2}"
                    self.variables[delta2_name] = self.model.addVar(vtype=GRB.BINARY, name=delta2_name)
                    self.contraintes["Constr1"+delta2_name] = self.model.addConstr(self.MAJORANT * (1 - self.variables[delta2_name]) >= horaire_fin_2 - horaire_debut_1,
                                                                        name="Constr1"+delta2_name)
                    self.contraintes["Constr2"+delta2_name] = self.model.addConstr(- self.MAJORANT * self.variables[delta2_name] <= horaire_fin_2 - horaire_debut_1,
                                                                        name="Constr2"+delta2_name)
                    # Contrainte tâches agent simultanées
                    cstr_name = f"Constr_TacheAgentSimult_{var_name_1}_{var_name_2}"
                    self.contraintes[cstr_name] = self.model.addConstr(self.variables[attr_1] + self.variables[attr_2] + self.variables[delta1_name] <= 2 + self.variables[delta2_name],
                                                        name=cstr_name)

    def add_constr_indispos_chantiers_humains(self):
        for roulement_id in tqdm(self.roulements()[RoulementsColumnNames.ROUL_NAME].index, desc="Indispos Chantier"):
            jours_dispos = [int(day) for day in self.roulements()[RoulementsColumnNames.ROUL_DAYS][roulement_id].split(sep=";")]
            for jour in self.all_days:
                if not jour%7+1 in jours_dispos:
                    continue
                nombre_agents = int(self.roulements()[RoulementsColumnNames.ROUL_NB_AGENTS][roulement_id])
                cycles = self.roulements()[RoulementsColumnNames.ROUL_CYCLES][roulement_id].split(';')
                connaissances_chantiers = self.roulements()[RoulementsColumnNames.ROUL_CONN_CHANTIER][roulement_id].split(';')
                for chantier in connaissances_chantiers :
                    indispo_list = donnees_trains.indispo_to_intervalle(self.data, "chantier", chantier)
                    for agent in range(1, nombre_agents + 1):
                        for cycle_index in range(len(cycles)):
                            cycle = cycles[cycle_index]
                            debut_cycle, fin_cycle = cycle.split(sep="-")
                            debut_cycle = horaires.triplet_vers_entier(jour, int(debut_cycle.split(sep=":")[0]), int(debut_cycle.split(sep=":")[1]))
                            fin_cycle = horaires.triplet_vers_entier(jour, int(fin_cycle.split(sep=":")[0]), int(fin_cycle.split(sep=":")[1]))
                            for debut_indisp, fin_indisp in indispo_list:
                                if debut_cycle == debut_indisp and fin_cycle == fin_indisp:
                                    var_cr_name = f"Cr_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle_index}"
                                    new_cstr_name = f"Constr_indispo_chantier_{chantier}_roul{roulement_id}_jour{str(jour)}_ag{str(agent)}_cy{cycle_index}"
                                    self.contraintes[new_cstr_name] = self.model.addConstr(self.variables[var_cr_name] == 0, name=new_cstr_name)
                                else:
                                    # TODO 
                                    pass

    def add_constr_respect_horaire_agent(self):
        for agent_name in tqdm(self.dict_taches_par_agent, desc="Resp Horaires Agents"):
            horaire_debut_travail = 0
            horaire_fin_travail = 0
            # agent_name de la forme : "roul{roulement_id}_jour{str(jour)}_ag{str(agent)}"
            roul_id = int("".join(agent_name.split(sep="_")[0][4::]))
            jour = "".join(agent_name.split(sep="_")[1][4::])
            cycles = self.roulements()[RoulementsColumnNames.ROUL_CYCLES][roul_id].split(';')
            for var_cycle in self.dict_taches_par_agent[agent_name]["Cycle"]:
                length = len(var_cycle)
                cycle_index = int(var_cycle[length-1])
                cycle = cycles[cycle_index]
                debut_cycle, fin_cycle = self.creneaux_from_cycle(jour, cycle)
                horaire_debut_travail += debut_cycle * self.variables[var_cycle]
                horaire_fin_travail += fin_cycle * self.variables[var_cycle]
            for var_tache in self.dict_taches_par_agent[agent_name]["Horaire"]:
                var_attrib = "Attr_"+var_tache[2::]
                constr_name = f"RespHorairesAgent_Start_{var_tache}"
                # self.contraintes[constr_name] = self.model.addConstr(self.variables[var_tache] >= horaire_debut_travail, name=constr_name)
                self.contraintes[constr_name] = self.model.addConstr(self.variables[var_tache] + (1-self.variables[var_attrib]) * self.MAJORANT >= horaire_debut_travail, name=constr_name)
                _, var_name = var_tache.split(sep="_", maxsplit=1)
                chantier = var_name.split(sep="_")[4]
                type_train = "ARR" if chantier == "REC" else "DEP"
                task_id = var_name.split(sep="_")[5]
                duree = self.dict_taches[type_train+"_"+task_id]["Duree"]
                constr_name = f"RespHorairesAgent_End_{var_tache}"
                # self.contraintes[constr_name] = self.model.addConstr(self.variables[var_tache] + duree <= horaire_fin_travail, name=constr_name)
                self.contraintes[constr_name] = self.model.addConstr(self.variables[var_tache] + duree <= horaire_fin_travail + (1-self.variables[var_attrib]) * self.MAJORANT, name=constr_name)

    def creneaux_from_cycle(self, jour, cycle):
        debut_cycle_str, fin_cycle_str = cycle.split(sep="-")
        debut_cycle_datetime = datetime.datetime.strptime(debut_cycle_str, "%H:%M")
        fin_cycle_datetime = datetime.datetime.strptime(fin_cycle_str, "%H:%M")
        debut_cycle = horaires.triplet_vers_entier(int(jour), int(debut_cycle_str.split(sep=":")[0]), int(debut_cycle_str.split(sep=":")[1]))
        fin_cycle = horaires.triplet_vers_entier(int(jour), int(fin_cycle_str.split(sep=":")[0]), int(fin_cycle_str.split(sep=":")[1]))
        if fin_cycle_datetime < debut_cycle_datetime:
            fin_cycle = horaires.triplet_vers_entier(int(jour)+1, int(fin_cycle_str.split(sep=":")[0]), int(fin_cycle_str.split(sep=":")[1]))
        return debut_cycle, fin_cycle

    def add_constr_attrib_tache_unique(self):
        for tache in tqdm(self.dict_taches, desc="Attrib Tache Unique"):
            for train in self.dict_taches[tache]:
                if train == "Duree":
                    continue
                cstr_name = f"AttribUnique_{tache}_{train}"
                somme_attribs = 0
                for var_name in self.dict_taches[tache][train]["Attribution"]:
                    somme_attribs += self.variables[var_name]
                self.contraintes[cstr_name] = self.model.addConstr(somme_attribs == 1, name=cstr_name)

    def create_model_objective_jalon3(self):
        objective = 0
        for agent_name in self.dict_taches_par_agent:
            for var_cycle in self.dict_taches_par_agent[agent_name]["Cycle"]:
                objective += self.variables[var_cycle]
        self.obj_function = objective
