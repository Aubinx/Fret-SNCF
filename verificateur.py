""" Vérifie la validité d'une solution obtenue par le modèle """

from datetime import datetime, timedelta

import horaires
from util import ArriveesColumnNames, DepartsColumnNames

def full_checking_process(solved_variables, extrema):#, arrival_pandas, departures_pandas, indisponibilities):
    """ Effectue la vérification de la solution """
    tasks, start_date = import_tasks_from_model(
                            solved_variables, extrema)

    for t in tasks:
        print(t)
    #import_arrival_from_model(fig, arrival_pandas, start_date, color_codes)
    #import_departures_from_model(fig, departures_pandas, start_date, color_codes)
    #displays_machine_indisponibilities(fig, indisponibilities, start_date)




# # Ajout de différentes tâches
#     for task in tasks:
#         train, tache, date, lenght = task
#         color = color_codes[train]
#         add_task_to_agenda(fig, date, date+lenght, (train, tache), color, start)

#     # Personnalisation de la mise en page
#     liste_jours = [start+timedelta(days=i) for i in range(delta_days)]
#     days_of_week = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
#     months_in_year = ['Janvier', 'Février', 'Mars', 'Avril',  'Mai', 'Juin',
#                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
#     dates_str = [f'{days_of_week[da.weekday()]} {da.day} {months_in_year[da.month-1]}'
#                  for da in liste_jours]

    
#     return fig

def import_tasks_from_model(solved_variables, earliest_date):
    """ Converts the result of the model into displayable data"""
    day, month, year = earliest_date.split('/')
    start_date = datetime(int(year), int(month), int(day))

    distinct_trains = []
    trains = []
    taches = []
    dates = []
    def extract_name_task(name_var):
        # Example format = Train_ARR_02/05/2023_sillon1_DEB
        if 'Train' not in name_var:
            return None,None
        return name_var[:-4], name_var[-3:]
    def date_code_to_date_time(date_tuple):
        day, hour, minute = date_tuple
        return start_date.replace(hour=hour, minute=minute) + timedelta(days=day-1)

    for var, value in solved_variables.items():
        name, task = extract_name_task(var)
        if name is not None:
            if name not in distinct_trains:
                distinct_trains.append(name)
            trains.append(name)
            taches.append(task)
            dates.append(date_code_to_date_time(horaires.entier_vers_triplet(int(value.x))))

    # Need to adapt this time when different times
    delta_temps = 15
    tasks = [(trains[i], taches[i], dates[i],
              timedelta(minutes=delta_temps)) for i in range(len(trains))]
    tasks = tuple(tasks)
    return(tasks, start_date, distinct_trains)

def import_arrival_from_model(fig, arrival_pandas, start_date, color_codes):
    """ Imports and displays the hour for arrival for each train """
    def date_code_to_date_time_and_day(date_tuple):
        day, hour, minute = date_tuple
        date = start_date.replace(hour=hour, minute=minute)
        return date, day-1

    for index in arrival_pandas.index :
        jour = arrival_pandas[ArriveesColumnNames.ARR_DATE][index]
        numero = arrival_pandas[ArriveesColumnNames.ARR_TRAIN_NUMBER][index]
        creneau_arrivee, delta_day = date_code_to_date_time_and_day(
            horaires.entier_vers_triplet(int(arrival_pandas[ArriveesColumnNames.ARR_CRENEAU][index])
                                         )
            )


def import_departures_from_model(fig, departures_pandas, start_date, color_codes):
    """ Imports and displays the hour for departures for each train """
    def date_code_to_date_time_and_day(date_tuple):
        day, hour, minute = date_tuple
        date = start_date.replace(hour=hour, minute=minute)
        return date, day-1

    for index in departures_pandas.index :
        jour = departures_pandas[DepartsColumnNames.DEP_DATE][index]
        numero = departures_pandas[DepartsColumnNames.DEP_TRAIN_NUMBER][index]
        creneau_dep, delta_day = date_code_to_date_time_and_day(
            horaires.entier_vers_triplet(
                int(departures_pandas[DepartsColumnNames.DEP_CRENEAU][index])
                                         )
            )
        # str_train = f"Train_DEP_{numero}_{jour}"
        # color = darker_color_tool(color_codes[f"Train_DEP_{jour}_{numero}"], factor=.7)
        # fig.add_trace(go.Scatter(
        #     x=[creneau_dep, creneau_dep],
        #     y=[delta_day, delta_day+1],
        #     mode="lines",
        #     line={'color':color, 'width':2, 'dash':"solid"},
        #     name=str_train,
        #     hoverinfo="name"  # Show the name when hovering over the line
        # ))

def displays_machine_indisponibilities(fig, indisponibilities, start_date):
    """ Displays a grey rectangle on indisponibilities """
    def date_code_to_date_time(date_tuple):
        day, hour, minute = date_tuple
        return start_date.replace(hour=hour, minute=minute) + timedelta(days=day-1)

    for indispo in indisponibilities:
        machine, t_min, t_max = indispo
        date_min = date_code_to_date_time(horaires.entier_vers_triplet(int(t_min)))
        date_max = date_code_to_date_time(horaires.entier_vers_triplet(int(t_max)))
