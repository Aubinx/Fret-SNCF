import plotly.graph_objects as go
from datetime import datetime, timedelta

def add_task_to_agenda(fig, start_time, end_time, task_name, color, ref_day):
    delta_day = start_time.replace(hour=0, minute=0)-ref_day.replace(hour=0, minute=0)
    delta_day = delta_day.days

    # Tests wheras the event is over dwo days
    lenght =  end_time.replace(hour=0, minute=0)-start_time.replace(hour=0, minute=0)
    lenght = lenght.days
    if lenght>=1:
        # We need to split the event in multiple ones
        # The event is splited into the one on the first day and the rest
        new_end = start_time.replace(hour=23, minute=59)
        add_task_to_agenda(fig, start_time, new_end, task_name, color, ref_day)
        next_task_start = start_time.replace(hour=0, minute=0) + timedelta(days=1)
        add_task_to_agenda(fig, next_task_start, end_time, task_name, color, ref_day)
    else:
        # Start
        start = ref_day.replace(hour=start_time.hour, minute=start_time.hour)
        # End
        end = ref_day.replace(hour=end_time.hour, minute=end_time.minute)
        fig.add_trace(go.Scatter(x=[start, end, end, start, start],
                                y=[delta_day, delta_day, delta_day+1, delta_day+1, delta_day],
                                fill='toself',
                                line=dict(color=color),
                                name=task_name))

def generate_empty_agenda(start, end):
    # Création des heures et jours de la semaine
    year, month, day = start.year, start.month, start.day
    hours = [datetime(year, month, day, hour=hour, minute=0) for hour in range(24)]
    #days_of_week = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    delta_days = end - start
    delta_days = delta_days.days +1

    days = [f'Jour {i}' for i in range(delta_days)]
    # Création du tableau
    fig = go.Figure()

    for day in range(delta_days):
        for hour in hours:
            # Ajout d'une case de 5 minutes
            end_time = hour + timedelta(minutes=60)
            fig.add_trace(go.Scatter(x=[hour, end_time, end_time, hour, hour],
                                     y=[day, day, day + 1, day + 1, day],
                                     fill='toself',
                                     line=dict(color='white'),
                                     hoverinfo='skip'))
     # Ajout de différentes tâches
    #add_task_to_agenda(fig, datetime(2024, 3, 4, hour=10, minute=0), datetime(2024, 3, 4, hour=12, minute=0), 'Réunion', 'blue', start)
    add_task_to_agenda(fig, datetime(2024, 3, 4, hour=10, minute=0), datetime(2024, 3, 5, hour=0, minute=0), 'Réunion', 'yellow', start)
    #add_task_to_agenda(fig, datetime(2024, 3, 5, hour=14, minute=0), datetime(2024, 3, 5, hour=15, minute=30), 'Travail sur le projet', 'green', start)

    # Personnalisation de la mise en page
    fig.update_layout(title='Agenda de la semaine',
                      xaxis=dict(title='Heure de la journée', tickformat='%H:%M'),
                      yaxis=dict(title='Jour ', tickvals=list(range(delta_days)), ticktext=days),
                      showlegend=False)

    fig.show()


# Appel de la fonction pour générer l'agenda
date_min, date_max = datetime(2024, 3, 4), datetime(2024, 3, 10)
generate_empty_agenda(date_min, date_max)
