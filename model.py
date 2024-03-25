"""Génère et optimise le modèle gurobi associé à l'instance considérée"""
from gurobipy import *
from tqdm import tqdm
import donnees_trains
from util import (InstanceSheetNames, ArriveesColumnNames, DepartsColumnNames,
                  TachesColumnNames, ORDERED_MACHINES, ORDERED_CHANTIERS, TACHES_PAR_CHANTIER)

class FretModel:
    """Classe rassemblant tous les éléments nécessaires
    à la modélisation et l'optimisation d'une gare de fret"""
    data = {}
    model = Model()
    variables = {}
    contraintes = {}

    MAJORANT = 10**5
    EPSILON = 1/4

    def arrivees(self):
        """Renvoie le dataframe des sillons à l'arrivée"""
        return self.data[InstanceSheetNames.SHEET_ARRIVEES]
    def departs(self):
        """Renvoie le dataframe des sillons au départ"""
        return self.data[InstanceSheetNames.SHEET_DEPARTS]

    def __init__(self, _data):
        """Constructeur de la classe `FretModel`"""
        self.var_name_counter = 0
        self.data = _data
        self.reset_model()

    def reset_model(self):
        """Méthode pour réinitialiser les données de l'instance de `FretModel`"""
        self.model = Model("Fret SNCF")
        self.variables = {}
        self.contraintes = {}

    def load_whole_model(self):
        """Charge l'ensemble des variables et contraintes du modèle jusqu'au `jalon` demandé"""
        self.add_vars_primary_trains()
        self.add_constr_ordre_taches_arrivee()
        self.add_constr_ordre_taches_depart()
        self.add_constr_raccordement()
        self.add_constr_placement_creneau()
        self.add_constr_indispos_machines()
        self.add_constr_indispos_chantiers()
        self.add_constr_capa_machines()

    def update_model(self):
        """Permet d'appeler `update` sur le modèle gurobi"""
        self.model.update()

    def optimize_model(self):
        """Permet d'appeler `optimize` sur le modèle gurobi"""
        self.model.optimize()

    def add_vars_primary_trains(self):
        """Variables de décision concernant le passage des trains aux taches machines"""
        # Variables de décision concernant les trains à l'arrivée :
        for index in self.arrivees().index:
            jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
            numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
            self.variables[f"Train_ARR_{jour}_{numero}_DEB"] = self.model.addVar(
                name = f"Train_ARR_{jour}_{numero}_DEB",
                vtype = GRB.INTEGER,
                lb = 0)
        # Variables de décision concernant les trains au départ :
        for index in self.departs().index:
            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            self.variables[f"Train_DEP_{jour}_{numero}_FOR"] = self.model.addVar(
                name = f"Train_DEP_{jour}_{numero}_FOR",
                vtype = GRB.INTEGER,
                lb = 0)
            self.variables[f"Train_DEP_{jour}_{numero}_DEG"] = self.model.addVar(
                name = f"Train_DEP_{jour}_{numero}_DEG",
                vtype = GRB.INTEGER,
                lb = 0)

    def add_constr_ordre_taches_arrivee(self):
        """Contraintes sur l'ordre des tâches du train d'arrivée"""
        for index in self.arrivees().index:
            jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
            numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
            creneau_arrivee = self.arrivees()[ArriveesColumnNames.ARR_CRENEAU][index]
            self.contraintes[f"Train_ARR_{jour}_{numero}_ORDRE"] = self.model.addConstr(
                self.variables[f"Train_ARR_{jour}_{numero}_DEB"] >= creneau_arrivee + 60,
                name = f"Train_ARR_{jour}_{numero}_ORDRE"
            )

    def add_constr_ordre_taches_depart(self):
        """Contraintes sur l'ordre des tâches du train de départ"""
        for index in self.departs().index :
            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            creneau_depart = self.departs()[DepartsColumnNames.DEP_CRENEAU][index]
            self.contraintes[f"Train_DEP_{jour}_{numero}_ORDRE_DEG"] = self.model.addConstr(
                self.variables[f"Train_DEP_{jour}_{numero}_DEG"] >= self.variables[f"Train_DEP_{jour}_{numero}_FOR"] + 165,
                name = f"Train_DEP_{jour}_{numero}_ORDRE_DEG"
            )
            self.contraintes[f"Train_DEP_{jour}_{numero}_ORDRE_DEP"] = self.model.addConstr(
                self.variables[f"Train_DEP_{jour}_{numero}_DEG"] + 35 <= creneau_depart,
                name = f"Train_DEP_{jour}_{numero}_ORDRE_DEP"
            )

    def add_constr_raccordement(self):
        """Contraintes de raccordement"""
        for index in tqdm(self.departs().index, desc="Cstr RAC", colour='#ff4422'):
            jour_depart = self.departs()[DepartsColumnNames.DEP_DATE][index]
            numero_depart = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
            id_train_depart = (jour_depart, numero_depart)
            trains_arrivee_lies = donnees_trains.composition_train_depart(self.data, id_train_depart)
            for jour_arrivee, numero_arrivee in trains_arrivee_lies:
                self.contraintes[f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"] = self.model.addConstr(
                    self.variables[f"Train_DEP_{jour_depart}_{numero_depart}_FOR"] >= self.variables[f"Train_ARR_{jour_arrivee}_{numero_arrivee}_DEB"] + 15,
                    name = f"Train_RAC_{jour_arrivee}_{numero_arrivee}_{jour_depart}_{numero_depart}"
                )

    def add_constr_placement_creneau(self):
        """Contraintes de placement des tâches sur des créneaux horaires"""
        new_vars = []
        for nom_variable in self.variables:
            train_str, rest = nom_variable.split("_", maxsplit=1)
            train_str = train_str.lower()
            new_var = f"PLACEMENT_CRENEAU_{train_str}_{rest}"
            new_vars.append((new_var, self.model.addVar(vtype=GRB.INTEGER, lb=0, name=new_var), nom_variable))
        for name, variable, old_var in new_vars:
            self.variables[name] = variable
            new_cstr = "Constr_" + name
            self.contraintes[new_cstr] = self.model.addConstr(variable * 15 == self.variables[old_var],
                                                    name=new_cstr)

    def add_constr_indispos_machines(self):
        """Contraintes d'indisponibilités machines"""
        for machine in tqdm(ORDERED_MACHINES, desc="Indispos Machines", colour='#cc00ff'):
            tasks_df = self.data[InstanceSheetNames.SHEET_TACHES]
            for index_indisp, (creneau_min, creneau_max) in enumerate(donnees_trains.indispo_to_intervalle(self.data, "machine", machine)):
                duree_task = int(tasks_df[tasks_df[TachesColumnNames.TASK_LINK]==f"{machine}="][TachesColumnNames.TASK_DURATION])
                if machine == ORDERED_MACHINES[0]:
                    for index in self.arrivees().index :
                        jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
                        numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                        to_abs = 2 * self.variables[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                        name_new_var = f"INDISPO_train_ARR_{jour}_{numero}_{machine}_{index_indisp}"
                        cstr_name = "Constr_"+name_new_var
                        lin_abs = self.linearise_abs(to_abs, name_new_var)
                        self.contraintes[cstr_name] = self.model.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)
                else:
                    for index in self.departs().index :
                        jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                        numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                        to_abs = 2 * self.variables[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                        name_new_var = f"INDISPO_train_DEP_{jour}_{numero}_{machine}_{index_indisp}"
                        cstr_name = "Constr_"+name_new_var
                        lin_abs = self.linearise_abs(to_abs, name_new_var)
                        self.contraintes[cstr_name] = self.model.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)

    def add_constr_indispos_chantiers(self):
        """Contraintes d'indisponibilités chantiers"""
        for chantier in tqdm(ORDERED_CHANTIERS, desc="Indispos Chantiers", colour='#cc00ff'):
            tasks_df = self.data[InstanceSheetNames.SHEET_TACHES]
            for index_indisp, (creneau_min, creneau_max) in enumerate(donnees_trains.indispo_to_intervalle(self.data, "chantier", chantier)):
                for machine in TACHES_PAR_CHANTIER[chantier]:
                    duree_task = int(tasks_df[tasks_df[TachesColumnNames.TASK_LINK]==f"{machine}="][TachesColumnNames.TASK_DURATION])
                    if machine == ORDERED_MACHINES[0]:
                        for index in self.arrivees().index :
                            jour = self.arrivees()[ArriveesColumnNames.ARR_DATE][index]
                            numero = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
                            to_abs = 2 * self.variables[f"Train_ARR_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                            name_new_var = f"INDISPO_train_ARR_{jour}_{numero}_{chantier}_{machine}_{index_indisp}"
                            cstr_name = "Constr_"+name_new_var
                            lin_abs = self.linearise_abs(to_abs, name_new_var)
                            self.contraintes[cstr_name] = self.model.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)
                    else:
                        for index in self.departs().index :
                            jour = self.departs()[DepartsColumnNames.DEP_DATE][index]
                            numero = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
                            to_abs = 2 * self.variables[f"Train_DEP_{jour}_{numero}_{machine}"] - (creneau_max + creneau_min - duree_task)
                            name_new_var = f"INDISPO_train_DEP_{jour}_{numero}_{chantier}_{machine}_{index_indisp}"
                            cstr_name = "Constr_"+name_new_var
                            lin_abs = self.linearise_abs(to_abs, name_new_var)
                            self.contraintes[cstr_name] = self.model.addConstr(lin_abs >= creneau_max - creneau_min + duree_task, name=cstr_name)

    def add_constr_capa_machines(self):
        """Contraintes de capacité des machines"""
        for machine in tqdm(ORDERED_MACHINES, desc="Machines Uniques", colour='#226677'):
            if machine == ORDERED_MACHINES[0]: # Machine de débranchement
                for i, index_1 in enumerate(self.arrivees().index):
                    for index_2 in self.arrivees().index[i+1:]:
                        jour_1 = self.arrivees()[ArriveesColumnNames.ARR_DATE][index_1]
                        numero_1 = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_1]
                        jour_2 = self.arrivees()[ArriveesColumnNames.ARR_DATE][index_2]
                        numero_2 = self.arrivees()[ArriveesColumnNames.ARR_TRAIN_NUMBER][index_2]
                        self.mono_constr_capa_machine(jour_1, numero_1, jour_2, numero_2, machine)
            else:
                for i, index_1 in enumerate(self.departs().index):
                    for index_2 in self.departs().index[i+1:]:
                        jour_1 = self.departs()[DepartsColumnNames.DEP_DATE][index_1]
                        numero_1 = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index_1]
                        jour_2 = self.departs()[DepartsColumnNames.DEP_DATE][index_2]
                        numero_2 = self.departs()[DepartsColumnNames.DEP_TRAIN_NUMBER][index_2]
                        self.mono_constr_capa_machine(jour_1, numero_1, jour_2, numero_2, machine)

    def mono_constr_capa_machine(self, jour1, num1, jour2, num2, machine_id):
        """Contrainte de capacité machine pour un couple de trains donné"""
        type_train = "ARR" if machine_id == ORDERED_MACHINES[0] else "DEP"
        train_1 = self.variables[f"Train_{type_train}_{jour1}_{num1}_{machine_id}"]
        train_2 = self.variables[f"Train_{type_train}_{jour2}_{num2}_{machine_id}"]
        to_abs = train_2 - train_1
        name_new_var = f"OCCUPATION_MACHINE_{jour1}_{num1}_{jour2}_{num2}_{machine_id}"
        cstr_name = "Constr_"+name_new_var
        lin_abs = self.linearise_abs(to_abs, name_new_var)
        self.contraintes[cstr_name] = self.model.addConstr(lin_abs >= 15, name=cstr_name)

    def linearise_abs(self, expr_var : LinExpr, var_name : str):
        """
        linéarise la variable `|expr_var|` en ajoutant des variables et des contraintes au modèle
        Renvoie l'expression linéaire de `|expr_var|`
        """
        assert var_name not in self.variables, "Nom déjà présent dans les variables du modèle"
        # Créer la variable binaire indicatrice et les contraintes associées
        delta_name = f"linabs_binary_{var_name}"
        cb1_name = f"linabs_ConstrBinary1_{var_name}"
        cb2_name = f"linabs_ConstrBinary2_{var_name}"
        delta = self.model.addVar(name=delta_name, vtype=GRB.BINARY)
        cb1 = self.model.addConstr(self.MAJORANT * delta >= expr_var, name=cb1_name)
        cb2 = self.model.addConstr(self.MAJORANT * (delta - 1) <= expr_var, name=cb2_name)

        # Créer la nouvelle variable entière et les contraintes associées
        prod_name = f"linabs_integer_{var_name}"
        ci1_name = f"linabs_ConstrInteger1_{var_name}"
        ci2_name = f"linabs_ConstrInteger2_{var_name}"
        ci3_name = f"linabs_ConstrInteger3_{var_name}"
        prod = self.model.addVar(name=prod_name, vtype=GRB.INTEGER, lb=0)
        ci1 = self.model.addConstr(prod >= expr_var, name=ci1_name)
        ci2 = self.model.addConstr(prod <= self.MAJORANT * delta, name=ci2_name)
        ci3 = self.model.addConstr(prod <= expr_var - self.MAJORANT * (delta - 1), name=ci3_name)

        # Mettre à jour les dictionnaires des variables et contraintes
        self.variables[delta_name] = delta
        self.variables[prod_name] = prod
        self.contraintes[cb1_name] = cb1
        self.contraintes[cb2_name] = cb2
        self.contraintes[ci1_name] = ci1
        self.contraintes[ci2_name] = ci2
        self.contraintes[ci3_name] = ci3
        linear_abs = LinExpr(2 * prod - expr_var)
        return linear_abs
