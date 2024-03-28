from gurobipy import *
from tqdm import tqdm
import donnees_trains
from util import (InstanceSheetNames, DepartsColumnNames, ArriveesColumnNames,
                  ChantiersColumnNames, ORDERED_CHANTIERS)
from model import FretModel

class FretModelJal2(FretModel):
    # additional variables
    voies = []
    dict_max_dep_for_train_arr = {}
    dict_min_arr_for_train_dep = {}
    var_name_counter = 0
    obj_function = LinExpr(0)

    # override
    def __init__(self, _data):
        super().__init__(_data)
        try:
            self.voies = _data[InstanceSheetNames.SHEET_CHANTIERS][ChantiersColumnNames.CHANTIER_CAPA_VOIES].copy(deep=True)
            self.dict_max_dep_for_train_arr = donnees_trains.dict_max_depart_du_train_d_arrivee(_data)
            self.dict_min_arr_for_train_dep = donnees_trains.dict_min_arrivee_du_train_de_depart(_data)
        except:
            self.voies = []
            self.dict_max_dep_for_train_arr = {}
            self.dict_min_arr_for_train_dep = {}

    # override
    def reset_model(self):
        super().reset_model()
        self.dict_max_dep_for_train_arr = {}
        self.dict_min_arr_for_train_dep = {}

    # override
    def load_whole_model(self):
        super().load_whole_model()
        self.add_vars_secondary_occupation_voies()
        self.model_jalon2_min_lin()
        self.add_constr_assignation_voie()
        self.add_constr_occu_voies()
        self.add_constr_remplissage_croissant()
        self.create_model_objective_jalon2()
    
    def set_model_objective_jalon2(self):
        self.model.setObjective(self.obj_function, GRB.MINIMIZE)

    def set_nb_voies_fromation(self, nb_voies:int=-2):
        """Règle manuellement le nombre de voies laissées au chantier de formation"""
        if not nb_voies == -2:
            self.voies[1] = str(nb_voies)

    def add_vars_secondary_occupation_voies(self):
        """Variables binaires d'occupation des voies pour chaque chantier"""
        # Occupations des voies du chantier "réception"
        for index in self.arrivees().index:
            jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
            numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
            for voie in range(1, int(self.voies[0]) + 1) :
                self.variables[f"CVT_WPY_REC_{str(voie)}_{jour}_{numero}"] = self.model.addVar(
                    name = f"CVT_WPY_REC_{str(voie)}_{jour}_{numero}",
                    vtype = GRB.BINARY)
        # Occupations des voies du chantier "formation"
        for index in self.departs().index:
            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            for voie in range(1, int(self.voies[1]) + 1) :
                self.variables[f"CVT_WPY_FOR_{str(voie)}_{jour}_{numero}"] = self.model.addVar(
                    name = f"CVT_WPY_FOR_{str(voie)}_{jour}_{numero}",
                    vtype = GRB.BINARY)
        # Occupations des voies du chantier "départ"
        for index in self.departs().index:
            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            for voie in range(1, int(self.voies[2]) + 1) :
                self.variables[f"CVT_WPY_DEP_{str(voie)}_{jour}_{numero}"] = self.model.addVar(
                    name = f"CVT_WPY_DEP_{str(voie)}_{jour}_{numero}",
                    vtype = GRB.BINARY)

    def linearise_min(self, elt_1, elt_2):
        """
        Linéarise l'expression `min(elt_1, elt2)` et renvoie l'expression linéaire associée
        """
        middle = elt_1 + elt_2
        to_abs = elt_1 - elt_2
        try:
            name_el1 = elt_1.VarName.replace("T", "t")
        except:
            name_el1 = f"lin_expr_in_linearise_min_{self.var_name_counter}"
            self.var_name_counter += 1
        try:
            name_el2 = elt_2.VarName.replace("T", "t")
        except:
            name_el2 = f"lin_expr_in_linearise_min_{self.var_name_counter}"
            self.var_name_counter += 1
        dist = self.linearise_abs(to_abs, f"dist_{name_el1}_{name_el2}")
        return (middle - dist) / 2

    def linearise_min_list(self, expr_list):
        """
        Linéarise l'expression `min(expr_list)` et renvoie l'expression linéaire associée
        """
        length = len(expr_list)
        # traiter les cas limites
        if length == 0:
            return expr_list
        if length == 1:
            return expr_list[0]
        # cas général
        current_min_expr = self.linearise_min(expr_list[0], expr_list[1])
        for i in range(2, length):
            current_min_expr = self.linearise_min(current_min_expr, expr_list[i])
        return current_min_expr

    def model_jalon2_min_lin(self):
        """
        Implementation du minimum pour le premier wagon
        arrivant au chantier FOR en linéarisant l'expression
        """
        for index in self.departs().index:
            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            train_arr_necessaires = [self.variables[f"Train_ARR_{jour_arr}_{numero_arr}_DEB"]
                                    for (jour_arr, numero_arr)
                                    in donnees_trains.composition_train_depart(self.data, (jour, numero))]
            min_deb = self.linearise_min_list(train_arr_necessaires)
            mindeb_var_name = f"min_DEB_{jour}_{numero}"
            self.variables[mindeb_var_name] = self.model.addVar(vtype=GRB.INTEGER, lb=0, name=mindeb_var_name)
            self.contraintes["Constr_"+mindeb_var_name] = self.model.addConstr(self.variables[mindeb_var_name] == min_deb,
                                                                    name="Constr_"+mindeb_var_name)

    def add_constr_assignation_voie(self):
        """Contrainte d'assignation de chaque train à une voie unique pour chaque chantier"""
        for i in tqdm(range(len(ORDERED_CHANTIERS)), desc="Assignation Voie Unique", colour='#ffffff'):
            chantier_id = ORDERED_CHANTIERS[i]
            if chantier_id == ORDERED_CHANTIERS[0]: # Chantier de réception
                for index in self.arrivees().index:
                    jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
                    numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                    somme_cvt = 0
                    for voie in range(1, int(self.voies[i]) + 1):
                        somme_cvt += self.variables[f"CVT_{chantier_id}_{str(voie)}_{jour}_{numero}"]
                    cstr_name = f"ASSIGNATION_{chantier_id}_{str(voie)}_train_{jour}_{numero}"
                    self.contraintes[cstr_name] = self.model.addConstr(somme_cvt == 1, name=cstr_name)
            else:
                for index in self.departs().index:
                    jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                    numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                    somme_cvt = 0
                    for voie in range(1, int(self.voies[i]) + 1):
                        somme_cvt += self.variables[f"CVT_{chantier_id}_{str(voie)}_{jour}_{numero}"]
                    cstr_name = f"ASSIGNATION_{chantier_id}_{str(voie)}_train_{jour}_{numero}"
                    self.contraintes[cstr_name] = self.model.addConstr(somme_cvt == 1, name=cstr_name)

    def mono_constr_occu_voies(self, chantier_id: str, voie: str, jour1: str, numero1: str, creneau1: int,
                               jour2: str, numero2: str, creneau2: int):
        """
        Variables et Contraintes nécessaires pour vérifier la réutilisation des voies.
        Version sans linéarisation de valeur absolue.
        """
        type_train = "ARR" if chantier_id == "WPY_REC" else "DEP"
        if chantier_id == "WPY_REC":
            train_arrivee_1 = creneau1
            train_arrivee_2 = creneau2
            train_depart_1 = self.variables[f"Train_{type_train}_{jour1}_{numero1}_DEB"] + 15
            train_depart_2 = self.variables[f"Train_{type_train}_{jour2}_{numero2}_DEB"] + 15
        elif chantier_id == "WPY_FOR":
            train_arrivee_1 = self.variables[f"min_DEB_{jour1}_{numero1}"]
            train_arrivee_2 = self.variables[f"min_DEB_{jour2}_{numero2}"]
            train_depart_1 = self.variables[f"Train_{type_train}_{jour1}_{numero1}_DEG"]
            train_depart_2 = self.variables[f"Train_{type_train}_{jour2}_{numero2}_DEG"]
        elif chantier_id == "WPY_DEP":
            train_arrivee_1 = self.variables[f"Train_{type_train}_{jour1}_{numero1}_DEG"]
            train_arrivee_2 = self.variables[f"Train_{type_train}_{jour2}_{numero2}_DEG"]
            train_depart_1 = creneau1
            train_depart_2 = creneau2
        cvt_1 = self.variables[f"CVT_{chantier_id}_{voie}_{jour1}_{numero1}"]
        cvt_2 = self.variables[f"CVT_{chantier_id}_{voie}_{jour2}_{numero2}"]
        # var binaire delta_arr2_dep1
        delta1_name = f"delta_Di_Aj_{chantier_id}_{voie}_{jour1}_{numero1}_{jour2}_{numero2}"
        self.variables[delta1_name] = self.model.addVar(vtype=GRB.BINARY, name=delta1_name)
        self.contraintes["Constr1"+delta1_name] = self.model.addConstr(self.MAJORANT * (1 - self.variables[delta1_name]) >= train_arrivee_2 - train_depart_1 + self.EPSILON,
                                                            name="Constr1"+delta1_name)
        self.contraintes["Constr2"+delta1_name] = self.model.addConstr(- self.MAJORANT * self.variables[delta1_name] <= train_arrivee_2 - train_depart_1 + self.EPSILON,
                                                            name="Constr2"+delta1_name)
        # var binaire delta_arr1_dep2
        delta2_name = f"delta_Dj_Ai_{chantier_id}_{voie}_{jour1}_{numero1}_{jour2}_{numero2}"
        self.variables[delta2_name] = self.model.addVar(vtype=GRB.BINARY, name=delta2_name)
        self.contraintes["Constr1"+delta2_name] = self.model.addConstr(self.MAJORANT * (1 - self.variables[delta2_name]) >= train_depart_2 - train_arrivee_1 + self.EPSILON,
                                                            name="Constr1"+delta2_name)
        self.contraintes["Constr2"+delta2_name] = self.model.addConstr(- self.MAJORANT * self.variables[delta2_name] <= train_depart_2 - train_arrivee_1 + self.EPSILON,
                                                            name="Constr2"+delta2_name)
        # Contrainte d'occupation
        cstr_name = f"Occu_non_abs_{chantier_id}_{voie}_{jour1}_{numero1}_{jour2}_{numero2}"
        self.contraintes[cstr_name] = self.model.addConstr(cvt_1 + cvt_2 + self.variables[delta1_name] <= 2 + self.variables[delta2_name],
                                                name=cstr_name)

    def add_constr_occu_voies(self):
        """Contrainte d'occupation des voies"""
        # Chantier "réception"
        for index_1 in tqdm(self.arrivees().index, desc="Occupation WPY_REC", colour='#00ff00') :
            jour_1 = self.arrivees()[ArriveesColumnNames.ARR_DATE][index_1]
            numero_1 = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
            creneau_arrivee_1 = self.arrivees()[ArriveesColumnNames.ARR_CRENEAU][index_1]
            creneau_depart_1 = self.dict_max_dep_for_train_arr[index_1]
            for index_2 in self.arrivees().index :
                if index_1 == index_2:
                    continue
                jour_2 = self.arrivees()[ArriveesColumnNames.ARR_DATE][index_2]
                numero_2 = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
                creneau_arrivee_2 = self.arrivees()[ArriveesColumnNames.ARR_CRENEAU][index_2]
                creneau_depart_2 = self.dict_max_dep_for_train_arr[index_2]
                if creneau_depart_1 >= creneau_arrivee_2 and creneau_depart_2 >= creneau_arrivee_1 :
                    for voie in range(1, int(self.voies[0]) + 1) :
                        self.mono_constr_occu_voies("WPY_REC", voie,
                                jour_1, numero_1, creneau_arrivee_1, jour_2, numero_2, creneau_arrivee_2)
        # Chantiers de "formation" et de "départ"
        for index_1 in tqdm(self.departs().index, desc="Occupation WPY_FOR et WPY_DEP", colour='#00ff00') :
            jour_1 = self.departs()[DepartsColumnNames.DEP_DATE][index_1]
            numero_1 = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
            creneau_depart_1 = self.departs()[DepartsColumnNames.DEP_CRENEAU][index_1]
            creneau_arrivee_1 = self.dict_min_arr_for_train_dep[index_1]
            for index_2 in self.departs().index :
                if index_1 == index_2:
                    continue
                jour_2 = self.departs()[DepartsColumnNames.DEP_DATE][index_2]
                numero_2 = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
                creneau_depart_2 = self.departs()[DepartsColumnNames.DEP_CRENEAU][index_2]
                creneau_arrivee_2 = self.dict_min_arr_for_train_dep[index_2]
                if creneau_depart_1 >= creneau_arrivee_2 and creneau_depart_2 >= creneau_arrivee_1 :
                    for voie in range(1, int(self.voies[1]) + 1) :
                        self.mono_constr_occu_voies("WPY_FOR", voie,
                                jour_1, numero_1, creneau_depart_1, jour_2, numero_2, creneau_depart_2)
                    for voie in range(1, int(self.voies[2]) + 1) :
                        self.mono_constr_occu_voies("WPY_DEP", voie,
                                jour_1, numero_1, creneau_depart_1, jour_2, numero_2, creneau_depart_2)

    def add_constr_remplissage_croissant(self):
        """Contrainte de remplissage des voies par ordre croissant"""
        # Chantier "réception"
        for voie in tqdm(range(1, int(self.voies[0])), desc="Remplissage WPY_REC", colour='#ffff00'):
            curr_cvt = 0
            next_cvt = 0
            for index in self.arrivees().index:
                jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
                numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                cvt_name_1 = f"CVT_WPY_REC_{str(voie)}_{jour}_{numero}"
                cvt_name_2 = f"CVT_WPY_REC_{str(voie+1)}_{jour}_{numero}"
                curr_cvt += self.variables[cvt_name_1]
                next_cvt += self.variables[cvt_name_2]
            self.model.addConstr(curr_cvt >= next_cvt, name=f"Remplissage_WPY_REC_{str(voie)}_{str(voie+1)}")
        # Chantier "formation"
        for voie in tqdm(range(1, int(self.voies[1])), desc="Remplissage WPY_FOR", colour='#ffff00'):
            curr_cvt = 0
            next_cvt = 0
            for index in self.departs().index:
                jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                cvt_name_1 = f"CVT_WPY_FOR_{str(voie)}_{jour}_{numero}"
                cvt_name_2 = f"CVT_WPY_FOR_{str(voie+1)}_{jour}_{numero}"
                curr_cvt += self.variables[cvt_name_1]
                next_cvt += self.variables[cvt_name_2]
            self.model.addConstr(curr_cvt >= next_cvt, name=f"Remplissage_WPY_FOR_{str(voie)}_{str(voie+1)}")
        # Chantier "départ"
        for voie in tqdm(range(1, int(self.voies[2])), desc="Remplissage WPY_DEP", colour='#ffff00'):
            curr_cvt = 0
            next_cvt = 0
            for index in self.departs().index:
                jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                cvt_name_1 = f"CVT_WPY_DEP_{str(voie)}_{jour}_{numero}"
                cvt_name_2 = f"CVT_WPY_DEP_{str(voie+1)}_{jour}_{numero}"
                curr_cvt += self.variables[cvt_name_1]
                next_cvt += self.variables[cvt_name_2]
            self.model.addConstr(curr_cvt >= next_cvt, name=f"Remplissage_WPY_DEP_{str(voie)}_{str(voie+1)}")

    def create_model_objective_jalon2(self):
        """
        Objectif du jalon 2 :
        Minimiser le nombre max de voie occupées dans le chantier de formation
        """
        obj_somme_indic = 0
        for voie in tqdm(range(1, int(self.voies[1]) + 1), desc="Fonction OBJ", colour='#ff8800') :
            indic_voie_name = f"indicatrice_FOR_voie{voie}_occupee"
            indic_voie_constr = f"Constr_indic_FOR_voie{voie}"
            somme_cvt_indic = -1
            for index in self.departs().index :
                jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                somme_cvt_indic += self.variables[f"CVT_WPY_FOR_{voie}_{jour}_{numero}"]
            self.variables[indic_voie_name] = self.model.addVar(vtype=GRB.BINARY,
                                                    name=indic_voie_name)
            self.contraintes[indic_voie_constr+"_1"] = self.model.addConstr(self.MAJORANT * self.variables[indic_voie_name] >= somme_cvt_indic + self.EPSILON,
                                                                name=indic_voie_constr+"_1")
            self.contraintes[indic_voie_constr+"_2"] = self.model.addConstr(self.MAJORANT * (self.variables[indic_voie_name] - 1) <= somme_cvt_indic + self.EPSILON,
                                                                name=indic_voie_constr+"_2")
            obj_somme_indic += self.variables[indic_voie_name]
        self.obj_function = obj_somme_indic
