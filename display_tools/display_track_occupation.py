""" Dispalys the occupation of tracks on the given span of time """

""" Display tasks into a plotly agenda """
from datetime import datetime, timedelta
import plotly.graph_objects as go

from display_tools.color import  create_color_scale

MARGE = 1/30

def add_filling_level(fig, start_time, end_time, filling_level, nb_voies, worksite, max_occup, ref_day):
    """ Add a period of equi-filling level to the displayed agenda """
    delta_day = start_time.replace(hour=0, minute=0)-ref_day.replace(hour=0, minute=0)
    delta_day = delta_day.days

    # Tests whereas the event is over two days
    lenght =  end_time.replace(hour=0, minute=0)-start_time.replace(hour=0, minute=0)
    lenght = lenght.days
    if lenght>=1:
        # We need to split the event in multiple ones
        # The event is splited into the one on the first day and the rest
        new_end = start_time.replace(hour=23, minute=59)
        add_filling_level(fig, start_time, new_end, filling_level,
                          nb_voies, worksite, max_occup, ref_day)
        next_task_start = start_time.replace(hour=0, minute=0) + timedelta(days=1)
        add_filling_level(fig, next_task_start, end_time,
                          filling_level, nb_voies, worksite, max_occup, ref_day)
    else:
        # Start
        start = ref_day.replace(hour=start_time.hour, minute=start_time.minute)
        # End
        end = ref_day.replace(hour=end_time.hour, minute=end_time.minute)

        possible_worsites = ('REC', 'FOR', 'DEP')
        assert worksite in possible_worsites, 'Wrong worksite'
        offset = {'REC':1.5*MARGE, 'FOR':0, 'DEP':-1.5*MARGE}
        #dict_color = {'REC':(255, 0, 0), 'FOR':(0, 255, 0), 'DEP':(0, 0, 255)}
        level = possible_worsites.index(worksite)
        delta_day += level/3 + offset[worksite]
        relative_occupation = filling_level/int(nb_voies[level])
        color = create_color_scale(relative_occupation, max_occup/int(nb_voies[level]),
                                   _color1=(0,255,0), _color2=(255,0,0))
        _h =  start_time.hour if start_time.hour!=0 else '00'
        _m =  start_time.minute if start_time.minute!=0 else '00'
        str_hour_min = f'{_h}h{_m}'
        _h =  end_time.hour if end_time.hour!=0 else '00'
        _m =  end_time.minute if end_time.minute!=0 else '00'
        str_hour_max = f'{_h}h{_m}'
        fig.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[delta_day+MARGE, delta_day+MARGE,
                   delta_day+1/3-MARGE, delta_day+1/3-MARGE, delta_day+MARGE],
                fill='toself',
                mode='lines',
                line={'color':color},
                text=f'Chantier: {worksite}<br>Occupation: {100*round(relative_occupation, 4)}%\
                    <br>Voies utilisées : {int(filling_level)} / {nb_voies[level]}\
                    <br>Heure de début : {str_hour_min}<br>Heure de fin : {str_hour_max}',
                hoverinfo='text'# Display custom text on hover
                        )
                      )

def displays_track_occupation(start, end, filling_levels, occupations_max, nombre_voies):
    """ Generates the Plotly Fig and displays an agenda """
    # Création des heures et jours de la semaine
    delta_days = end - start
    delta_days = delta_days.days +1

    # Création du tableau
    fig = go.Figure()
    ref_day = start.replace(hour=0, minute=0)
    # Ajout de différentes tâches
    for worksite, data in filling_levels.items():
        dates, levels = data
        max_occup = occupations_max[worksite]
        for i, level in enumerate(levels):
            add_filling_level(fig, dates[i], dates[i+1], level, nombre_voies, worksite, max_occup, ref_day)

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
                      showlegend=False
                      )
    fig.update_layout(
    title={
        'text': 'Occupation des voies sur les 3 chantiers',
        'font': {'size': 25}  # Adjust font properties as needed
    }
)
    fig.show()
