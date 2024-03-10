import plotly.graph_objects as go
from datetime import datetime, timedelta

def add_task_to_agenda(fig, start_time, end_time, task_name, color, ref_day):
    delta_day = start_time-ref_day
    delta_day = delta_day.days
    fig.add_trace(go.Scatter(x=[start_time, end_time, end_time, start_time, start_time],
                             y=[delta_day, delta_day, delta_day+1, delta_day+1, delta_day],
                             fill='toself',
                             line=dict(color=color),
                             name=task_name))

def generate_empty_agenda(start, end):
    # Création des heures et jours de la semaine
    hours = [datetime(2024, 3, 4, hour=hour, minute=0) for hour in range(24)]
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
    add_task_to_agenda(fig, datetime(2024, 3, 4, hour=10, minute=0), datetime(2024, 3, 4, hour=12, minute=0), 'Réunion', 'blue', start)
    add_task_to_agenda(fig, datetime(2024, 3, 5, hour=14, minute=0), datetime(2024, 3, 5, hour=15, minute=30), 'Travail sur le projet', 'green', start)

    # Personnalisation de la mise en page
    fig.update_layout(title='Agenda de la semaine',
                      xaxis=dict(title='Heure de la journée', tickformat='%H:%M'),
                      yaxis=dict(title='Jour ', tickvals=list(range(delta_days)), ticktext=days),
                      showlegend=False)

    fig.show()


# Appel de la fonction pour générer l'agenda
date_min, date_max = datetime(2024, 3, 4, hour=10, minute=0), datetime(2024, 3, 10, hour=10, minute=0)
generate_empty_agenda(date_min, date_max)
