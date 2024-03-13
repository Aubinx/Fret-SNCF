""" Display tasks into a plotly agenda """
from datetime import datetime, timedelta
import plotly.graph_objects as go

from display_tools.color import generate_colors

import Horaires


def add_task_to_agenda(fig, start_time, end_time, names, color, place, ref_day):
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
        add_task_to_agenda(fig, start_time, new_end, names, color, place, ref_day)
        next_task_start = start_time.replace(hour=0, minute=0) + timedelta(days=1)
        add_task_to_agenda(fig, next_task_start, end_time, names, color, place, ref_day)
    else:
        # Start
        start = ref_day.replace(hour=start_time.hour, minute=start_time.minute)
        # End
        end = ref_day.replace(hour=end_time.hour, minute=end_time.minute)
        level, size = place
        delta_day = delta_day+(level-1)/size
        train, task_name = names
        fig.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[delta_day, delta_day, delta_day+1/size, delta_day+1/size, delta_day],
                fill='toself',
                line={'color':color},
                name=train))
        difference = end - start
        _x = start + difference / 2
        _y= delta_day+.5/size
        _r, _g, _b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        # Assombrir les composantes RGB
        facteur = .5
        r_assombri = int(_r * facteur)
        g_assombri = int(_g * facteur)
        b_assombri = int(_b * facteur)
        couleur_assombrie = f"#{r_assombri:02x}{g_assombri:02x}{b_assombri:02x}"
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
    # Verification des tâches en parallèle
    overlap_level = {}
    number_of_overlap = {}
    for i, task in enumerate(tasks):
        overlap_level[task]=1
        number_of_overlap[task]=1
        if i==0:
            continue
        for other_task in tasks[:i]:
            _, _, date, lenght = task
            t11, t12 = date, date+lenght
            _, _, date, lenght = other_task
            t21, t22 = date, date+lenght
            if t21 < t11 < t22 or t21 < t12 < t22:
                overlap_level[task]=max(overlap_level[task],  overlap_level[other_task]+1)
                number_of_overlap[task]+=1
                number_of_overlap[other_task]+=1

    # Ajout de différentes tâches
    for task in tasks:
        train, tache, date, lenght = task
        color = color_codes[train]
        place = (overlap_level[task], number_of_overlap[task])
        add_task_to_agenda(fig, date, date+lenght, (train, tache), color, place, start)

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
    fig.show()

def import_tasks_from_model(variables, earliest_date, latest_date):
    """ Converts the result of the model into displayable data"""
    day, month, year = earliest_date.split('/')
    start_date = datetime(int(year), int(month), int(day))
    day, month, year = latest_date.split('/')
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

    for var, value in variables.items():
        name, task = extract_name_task(var)
        if name is not None:
            if name not in distinct_trains:
                distinct_trains.append(name)
            trains.append(name)
            taches.append(task)
            dates.append(date_code_to_date_time(Horaires.entier_vers_triplet(int(value.x))))

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
    return(tasks, trains_color, (start_date, end_date))
