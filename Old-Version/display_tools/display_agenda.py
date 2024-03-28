""" Display tasks into a plotly agenda """
from datetime import datetime, timedelta
import plotly.graph_objects as go

from display_tools.color import generate_colors

import horaires
from util import ArriveesColumnNames, DepartsColumnNames

# TOOLS

def darker_color_tool(color, factor=.6):
    """ Darkens a color with a factor"""
    _r, _g, _b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    # Assombrir les composantes RGB
    r_assombri = int(_r * factor)
    g_assombri = int(_g * factor)
    b_assombri = int(_b * factor)
    return f"#{r_assombri:02x}{g_assombri:02x}{b_assombri:02x}"

def add_task_to_agenda(fig, start_time, end_time, names, color, ref_day):
    """ Add a task to the displayed agenda """
    delta_day = start_time.replace(hour=0, minute=0)-ref_day.replace(hour=0, minute=0)
    delta_day = delta_day.days

    # Tests whereas the event is over dwo days
    lenght =  end_time.replace(hour=0, minute=0)-start_time.replace(hour=0, minute=0)
    lenght = lenght.days
    if lenght>=1:
        # We need to split the event in multiple ones
        # The event is splited into the one on the first day and the rest
        new_end = start_time.replace(hour=23, minute=59)
        add_task_to_agenda(fig, start_time, new_end, names, color, ref_day)
        next_task_start = start_time.replace(hour=0, minute=0) + timedelta(days=1)
        add_task_to_agenda(fig, next_task_start, end_time, names, color, ref_day)
    else:
        # Start
        start = ref_day.replace(hour=start_time.hour, minute=start_time.minute)
        # End
        end = ref_day.replace(hour=end_time.hour, minute=end_time.minute)
        _h =  start.hour if start.hour!=0 else '00'
        _m = start.minute if start.minute>=10 else f'0{start.minute}'
        str_hour_min = f'{_h}h{_m}'
        _h =  end.hour if end.hour!=0 else '00'
        _m = end.minute if end.minute>=10 else f'0{end.minute}'
        str_hour_max = f'{_h}h{_m}'
        train, task_name = names
        assert task_name in ('DEB', 'FOR', 'DEG'), f'Task was named {task_name}'
        possible_levels = ('DEB', 'FOR', 'DEG')
        level = possible_levels.index(task_name)
        delta_day += level/3
        fig.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[delta_day, delta_day, delta_day+1/3, delta_day+1/3, delta_day],
                fill='toself',
                mode='lines',
                line={'color':color},
                text=f'{train}<br>Arrivée : {str_hour_min}<br>Départ : {str_hour_max}',
                hoverinfo='text'
                ))
        difference = end - start
        _x = start + difference / 2
        _y= delta_day+1/6
        couleur_assombrie = darker_color_tool(color)
        fig.add_annotation(
            x=_x, y=_y, text=task_name, showarrow=False,
            xanchor='center', xshift=0, yanchor='middle',
            font={'color':couleur_assombrie}
                           )


def generate_empty_agenda(start, end, tasks, color_codes):
    """ Generates the Plotly Fig and displays an agenda """
    # Création des heures et jours de la semaine
    delta_days = end - start
    delta_days = delta_days.days +1

    # Création du tableau
    fig = go.Figure()

    _s, _e = start.replace(hour=0, minute=0), start.replace(hour=23, minute=59)
    for day in range(delta_days):
        # Ajout d'une case par jour
        fig.add_trace(go.Scatter(x=[_s, _e, _e, _s, _s],
                                    y=[day, day, day + 1, day + 1, day],
                                    fill='toself',
                                    line={'color':'white'},
                                    hoverinfo='skip'))

    # Ajout de différentes tâches
    for task in tasks:
        train, tache, date, lenght = task
        color = color_codes[train]
        add_task_to_agenda(fig, date, date+lenght, (train, tache), color, start)

    # Personnalisation de la mise en page
    liste_jours = [start+timedelta(days=i) for i in range(delta_days)]
    days_of_week = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    months_in_year = ['Janvier', 'Février', 'Mars', 'Avril',  'Mai', 'Juin',
                      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
    dates_str = [f'{days_of_week[da.weekday()]} {da.day} {months_in_year[da.month-1]}'
                 for da in liste_jours]

    fig.update_layout(
                      xaxis={
                            'title':{
                                'text':'Heure de la journée',
                                'font': {'size': 20}
                                    },
                            'tickformat':'%H:%M',
                            'tickfont':{'size':17}

                            },
                      yaxis={
                            'title':{
                                'text':'Jour',
                                'font': {'size': 20}
                                    },
                            'tickvals':[i+.5 for i in list(range(delta_days))],
                            'ticktext':dates_str, 
                            'showgrid':False,
                            'tickangle':-45,
                            'tickfont':{'size':17}
                            },
                      showlegend=False)
    fig.update_layout(
    title={
        'text': 'Répartition des tâches machines pour chaque train',
        'font': {'size': 25}  # Adjust font properties as needed
    }
)
    return fig

def import_tasks_from_model(solved_variables, extrema):
    """ Converts the result of the model into displayable data"""
    earliest, lastest = extrema
    day, month, year = earliest.split('/')
    start_date = datetime(int(year), int(month), int(day))
    day, month, year = lastest.split('/')
    end_date = datetime(int(year), int(month), int(day))

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

    # for i, train in enumerate(trains):
    #     print('train : ', train)
    #     print('tache : ', taches[i])
    #     print('date : ', dates[i])

    n_colors = generate_colors(len(distinct_trains))
    trains_color = {train:n_colors[i] for i,train in enumerate(distinct_trains)}
    # Need to adapt this time when different times
    delta_temps = 15
    tasks = [(trains[i], taches[i], dates[i],
              timedelta(minutes=delta_temps)) for i in range(len(trains))]
    tasks = tuple(tasks)
    end_date =max(*dates, end_date)
    return(tasks, trains_color, (start_date, end_date))

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
        str_train = f"Train_ARR_{numero}_{jour}"

        color = darker_color_tool(color_codes[f"Train_ARR_{jour}_{numero}"], factor=.8)
        fig.add_trace(go.Scatter(
            x=[creneau_arrivee, creneau_arrivee],
            y=[delta_day, delta_day+1],
            mode="lines",
            line=dict(color=color, width=2, dash="dashdot"),
            name=str_train,
            hoverinfo="name"  # Show the name when hovering over the line
))

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
        str_train = f"Train_DEP_{numero}_{jour}"
        color = darker_color_tool(color_codes[f"Train_DEP_{jour}_{numero}"], factor=.7)
        fig.add_trace(go.Scatter(
            x=[creneau_dep, creneau_dep],
            y=[delta_day, delta_day+1],
            mode="lines",
            line=dict(color=color, width=2, dash="solid"),
            name=str_train,
            hoverinfo="name"  # Show the name when hovering over the line
        ))

def displays_machine_indisponibilities(fig, indisponibilities, start_date):
    """ Displays a grey rectangle on indisponibilities """
    def date_code_to_date_time(date_tuple):
        day, hour, minute = date_tuple
        return start_date.replace(hour=hour, minute=minute) + timedelta(days=day-1)

    for indispo in indisponibilities:
        machine, t_min, t_max = indispo
        date_min = date_code_to_date_time(horaires.entier_vers_triplet(int(t_min)))
        date_max = date_code_to_date_time(horaires.entier_vers_triplet(int(t_max)))
        add_task_to_agenda(fig, date_min, date_max, ('Indisponibilité', machine), '#AAAAAA', start_date)

    
def full_process(solved_variables, extrema, arrival_pandas, departures_pandas, indisponibilities):
    """ Displays the agenda with the whole data """
    tasks, color_codes, (start_date, end_date) = import_tasks_from_model(
                            solved_variables, extrema)
    fig = generate_empty_agenda(start_date, end_date, tasks, color_codes)
    import_arrival_from_model(fig, arrival_pandas, start_date, color_codes)
    import_departures_from_model(fig, departures_pandas, start_date, color_codes)
    displays_machine_indisponibilities(fig, indisponibilities, start_date)
    fig.show()
