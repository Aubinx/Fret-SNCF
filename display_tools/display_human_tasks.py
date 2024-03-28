""" Dispalys the human tasks on the given span of time """

from datetime import datetime, timedelta
import plotly.graph_objects as go

def darker_color_tool(color, factor=.6):
    """ Darkens a color with a factor"""
    _r, _g, _b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    # Assombrir les composantes RGB
    r_assombri = int(_r * factor)
    g_assombri = int(_g * factor)
    b_assombri = int(_b * factor)
    return f"#{r_assombri:02x}{g_assombri:02x}{b_assombri:02x}"

def add_human_task(figure, start, end, level, liste_id):
    """ Dispalys a rectangle for the human task """
    id_task, id_roulement, id_agent, id_chantier, str_train = liste_id
    _h =  start.hour if start.hour!=0 else '00'
    _m = start.minute if start.minute>=10 else f'0{start.minute}'
    str_hour_min = f'{_h}h{_m}'
    _h =  end.hour if end.hour!=0 else '00'
    _m = end.minute if end.minute>=10 else f'0{end.minute}'
    str_hour_max = f'{_h}h{_m}'
    str_tache = {
        'REC':['arrivée Reception', 'préparation tri', 'débranchement'],
        'FOR':['appui voie + mise en place câle', 'attelage véhicules',
            'dégarage / bouger de rame'],
        'DEP':{3:'essai de frein départ'}
                }[id_chantier][int(id_task)-1]
    str_roulement =['roulement_reception', 'roulement_formation',
                'roulement_depart', 'roulement_reception_depart',
                'roulement_formation_depart'][int(id_roulement)]
    couleur = {'REC':'#0000FF', 'FOR':'#FF0000', 'DEP':'#13cf13'}[id_chantier]
    if str_tache in  ('appui voie + mise en place câle', 'dégarage / bouger de rame', 'débranchement'):
        couleur  = darker_color_tool(couleur, .6)

    figure.add_trace(go.Scatter(
                x=[start, end, end, start, start],
                y=[level, level, level+1, level+1, level],
                fill='toself',
                mode='lines',
                line={'color':couleur},
                text=f'Chantier : {id_chantier}<br>Tâche : {str_tache}\
                    <br>Début : {str_hour_min}<br>Fin : {str_hour_max}\
                    <br>Roulement : {str_roulement}<br>Agent n°{id_agent}\
                    <br>Train : {str_train}',
                hoverinfo='text'# Display custom text on hover
                        )
                      )
    # Affichage des tâches humaines // tâches machine
    taches_machine = {'appui voie + mise en place câle':'FOR',
                      'dégarage / bouger de rame':'DEG',
                      'débranchement':"DEB"}
    if str_tache in taches_machine:
        nom_tache = taches_machine[str_tache]
        couleur = darker_color_tool(couleur, .6)
        difference = end - start
        _x = start + difference / 2
        figure.add_annotation(
            x=_x, y=level+.5, text=nom_tache, showarrow=False,
            xanchor='center', xshift=0, yanchor='middle',
            font={'color':couleur}
                           )


def displays_human_tasks_1_day(id_day, tasks, ref_day):
    """ Generates the Plotly Fig and displays an agenda """
    ref_day = ref_day + timedelta(days=id_day-1)
    # Dictionnaire des durées des tâches
    durees = {
        'REC':[15,45,15],
        'FOR':[15,150,15],
        'DEP':{3:20}
        }
    # Création du tableau
    fig = go.Figure()

    # # Ajout de différentes tâches
    dict_roulements =['roulement_reception', 'roulement_formation',
                'roulement_depart', 'roulement_reception_depart',
                'roulement_formation_depart']
    level_compteur = 0
    level_roulements = [0]
    id_roulements = []
    for r_key, roulement in tasks.items():
        for a_key, agent in roulement.items():
            for tache in agent:
                (chantier, id_tache, str_train), start = tache
                end = start + timedelta(minutes=durees[chantier][int(id_tache)-1])
                liste_id = id_tache, r_key, a_key, chantier, str_train
                add_human_task(fig, start, end, level_compteur, liste_id)
            level_compteur+=1
        level_roulements.append(level_compteur)
        id_roulements.append(dict_roulements[int(r_key)])

    # On ajoute une ligne entre chaque roulement
    for level in level_roulements[0:]:
        fig.add_trace(go.Scatter(
            x=[ref_day.replace(hour=5, minute=0),
                            ref_day.replace(hour=5, minute=0)+timedelta(days=1)],
            y=[level, level],
            mode='lines',  # Mode 'lines' pour tracer une ligne
            line=dict(color='black', width=1, dash='dash')
        ))

    # Personnalisation de la mise en page
    roulement_place = [(level_roulements[i+1]+level_roulements[i])/2 for i in range(len(level_roulements)-1)]
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
                                'text':'Agents',
                                'font': {'size': 20}
                                    },
                            'tickvals':roulement_place,
                            'ticktext':id_roulements, 
                            'showgrid':False,
                            'tickangle':-45,
                            'tickfont':{'size':17},
                            'range':[ref_day.replace(hour=5, minute=0),
                                     ref_day.replace(hour=5, minute=0)+timedelta(days=1)]
                            },
                      showlegend=False
                      )
    months_in_year = ['Janvier', 'Février', 'Mars', 'Avril',  'Mai', 'Juin',
                      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']

    fig.update_layout(
    title={
        'text': f'Tâches humaines pour le {ref_day.day} \
{months_in_year[ref_day.month-1]} {ref_day.year}',
        'font': {'size': 25}  # Adjust font properties as needed
    }
)
    fig.show()



def display_human_tasks(dict_agents_on_day, ref_day):
    """ Creates plannings for human tasks and for each day """
    for id_day, day in dict_agents_on_day.items():
        displays_human_tasks_1_day(id_day, day, ref_day)


dic = {1:
    {1: 
        {1: [(('REC', '1', '02/05/2023'), datetime(2023, 5, 2, 13, 0)), (('REC', '1', '02/05/2023'),datetime(2023, 5, 2, 16, 0)),
            (('REC', '3', '02/05/2023'), datetime(2023, 5, 2, 14, 0)), (('REC', '3', '02/05/2023'), datetime(2023, 5, 2, 17, 0)),
            (('FOR', '1', '02/05/2023'), datetime(2023, 5, 2, 14, 30)), (('FOR', '1', '02/05/2023'), datetime(2023, 5, 2, 17, 30)),
            (('FOR', '3', '02/05/2023'), datetime(2023, 5, 2, 20, 0)), (('FOR', '3', '02/05/2023'), datetime(2023, 5, 2, 19, 30)),
            (('DEP', '4', '02/05/2023'), datetime(2023, 5, 2, 20, 40))],
        7: [(('REC', '1', '02/05/2023'), datetime(2023, 5, 2, 13, 0)), (('REC', '2', '02/05/2023'), datetime(2023, 5, 2, 13, 16)),
            (('REC', '2', '02/05/2023'), datetime(2023, 5, 2, 16, 15)), (('FOR', '1', '02/05/2023'), datetime(2023, 5, 2, 17, 15)),
            (('FOR', '2', '02/05/2023'), datetime(2023, 5, 2, 17, 45)), (('DEP', '4', '02/05/2023'), datetime(2023, 5, 2, 20, 40))],
        8: [(('REC', '2', '02/05/2023'), datetime(2023, 5, 2, 13, 15)), (('REC', '3', '02/05/2023'), datetime(2023, 5, 2, 14, 15)),
            (('FOR', '2', '02/05/2023'), datetime(2023, 5, 2, 17, 30)), (('FOR', '2', '02/05/2023'), datetime(2023, 5, 2, 14, 46)),
            (('FOR', '3', '02/05/2023'), datetime(2023, 5, 2, 20, 15)), (('DEP', '4', '02/05/2023'), datetime(2023, 5, 2, 20, 40))]}}}

if __name__=='__main__':
    display_human_tasks(dic,datetime(2023, 5, 2, 13, 0) )
