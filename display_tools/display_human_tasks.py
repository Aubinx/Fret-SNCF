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

def add_human_task(figure, start, end, level, liste_id, is_it_mini):
    """ Dispalys a rectangle for each human task """
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
    if is_it_mini:
        str_roulement = ['roulement1', 'roulement2'][int(id_roulement)]

    couleur = {'REC':'#0000FF', 'FOR':'#FF0000', 'DEP':'#13cf13'}[id_chantier]
    if str_tache in ('appui voie + mise en place câle',
                     'dégarage / bouger de rame', 'débranchement'):
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


def displays_human_tasks_1_day(id_day, tasks, ref_day, is_it_mini):
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

    # Ajout de différentes tâches
    dict_roulements =['roulement_reception', 'roulement_formation',
                'roulement_depart', 'roulement_reception_depart',
                'roulement_formation_depart']
    if is_it_mini:
        dict_roulements = ['roulement1', 'roulement2']


    # Créneaux possibles
    if is_it_mini:
        dictionnaire_creneaux = {
            True : [((5,0), (13,0)), ((13,0), (21,0)), ((21,0), (5,1))],
            False : [((5,0), (13,0)), ((13,0), (21,0))]
        }
    else:
        dictionnaire_creneaux = {
            True : [((5,0), (13,0)), ((13,0), (21,0)), ((21,0), (5,1))],
            False : [((22, -1), (6, 0)), ((9,0), (17,0))]
        }


    level_compteur = 0
    level_roulements = [0]
    id_roulements = []
    is_there_a_non_3x8_on_first_cycle = False
    for r_key, roulement in tasks.items():
        for a_key, agent in roulement.items():
            # Affichage des tâches
            for tache in agent[1]:
                (chantier, id_tache, str_train), start = tache
                end = start + timedelta(minutes=durees[chantier][int(id_tache)-1])
                liste_id = id_tache, r_key, a_key, chantier, str_train
                add_human_task(fig, start, end, level_compteur, liste_id, is_it_mini)

            # Affichage du cycle de l'agent
            cycle, is3x8 = agent[0]
            if not is3x8 and cycle==0:
                is_there_a_non_3x8_on_first_cycle = True
            (hinf, jinf), (hsup, jsup) = dictionnaire_creneaux[is3x8][cycle]
            xinf = ref_day.replace(hour=hinf, minute=0) + timedelta(days=jinf)
            xsup = ref_day.replace(hour=hsup, minute=0) + timedelta(days=jsup)
            fig.add_trace(go.Scatter(
                x=[xinf, xinf],
                y=[level_compteur, level_compteur+1],
                mode='lines',  # Mode 'lines' pour tracer une ligne
                line=dict(color='black', width=2, dash='solid')
            ))
            fig.add_trace(go.Scatter(
                x=[xsup, xsup],
                y=[level_compteur, level_compteur+1],
                mode='lines',  # Mode 'lines' pour tracer une ligne
                line=dict(color='black', width=2, dash='solid')
            ))

            level_compteur += 1


        level_roulements.append(level_compteur)
        id_roulements.append(dict_roulements[int(r_key)])


    # On ajoute une ligne entre chaque roulement
    if not is_it_mini:
        (h, d) = (22, -1) if is_there_a_non_3x8_on_first_cycle else (5, 0)
    else :
        (h, d) = (5, 0)
    display_h_min = ref_day.replace(hour=h, minute=0) + timedelta(days=d)
    for level in level_roulements[0:]:
        fig.add_trace(go.Scatter(
            x=[display_h_min, ref_day.replace(hour=5, minute=0)+timedelta(days=1)],
            y=[level, level],
            mode='lines',  # Mode 'lines' pour tracer une ligne
            line=dict(color='black', width=1, dash='dash')
        ))

    # Personnalisation de la mise en page
    roulement_place = [(level_roulements[i+1]+level_roulements[i])/2
                       for i in range(len(level_roulements)-1)]
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
                            'range':[display_h_min,
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



def display_human_tasks(dict_agents_on_day, ref_day, is_it_mini):
    """ Creates plannings for human tasks and for each day """
    for id_day, day in dict_agents_on_day.items():
        displays_human_tasks_1_day(id_day, day, ref_day, is_it_mini)


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

total_dic = {1:
    {1:
        {1: [(1, False),
             [(('REC', '1', '02/05/2023_sillon1'), datetime(2023, 5, 2, 13, 0)),
              (('REC', '1', '02/05/2023_sillon3'), datetime(2023, 5, 2, 16, 0)),
              (('REC', '2', '02/05/2023_sillon1'), datetime(2023, 5, 2, 13, 15)),
              (('REC', '2', '02/05/2023_sillon3'), datetime(2023, 5, 2, 16, 15)),
              (('REC', '3', '02/05/2023_sillon1'), datetime(2023, 5, 2, 14, 0)),
              (('REC', '3', '02/05/2023_sillon3'), datetime(2023, 5, 2, 17, 0)),
              (('FOR', '2', '02/05/2023_sillon4'), datetime(2023, 5, 2, 17, 30)),
              (('FOR', '3', '02/05/2023_sillon4'), datetime(2023, 5, 2, 20, 0)),
              (('FOR', '3', '02/05/2023_sillon5'), datetime(2023, 5, 2, 17, 15)),
              (('DEP', '4', '02/05/2023_sillon4'), datetime(2023, 5, 2, 20, 35)),
              (('DEP', '4', '02/05/2023_sillon5'), datetime(2023, 5, 2, 20, 15))]
             ],
         3: [(1, False),
             [(('REC', '1', '02/05/2023_sillon2'), datetime(2023, 5, 2, 13, 0)),
              (('REC', '2', '02/05/2023_sillon2'), datetime(2023, 5, 2, 13, 15)),
              (('REC', '3', '02/05/2023_sillon2'), datetime(2023, 5, 2, 14, 15)),
              (('FOR', '1', '02/05/2023_sillon4'), datetime(2023, 5, 2, 17, 15)),
              (('FOR', '1', '02/05/2023_sillon5'), datetime(2023, 5, 2, 14, 30)),
              (('FOR', '1', '02/05/2023_sillon6'), datetime(2023, 5, 2, 17, 30)),
              (('FOR', '2', '02/05/2023_sillon5'), datetime(2023, 5, 2, 14, 45)),
              (('FOR', '2', '02/05/2023_sillon6'), datetime(2023, 5, 2, 17, 45)),
              (('FOR', '3', '02/05/2023_sillon6'), datetime(2023, 5, 2, 20, 15)),
              (('DEP', '4', '02/05/2023_sillon6'), datetime(2023, 5, 2, 20, 30))
              ]]
         }}}
if __name__=='__main__':
    dic_instance2 = {1: {0: {3: [(2, True), [(('REC', '1', '08/08/2022_A3'), datetime(2022, 8, 8, 22, 0)), (('REC', '2', '08/08/2022_A3'), datetime(2022, 8, 8, 22, 15)), (('REC', '3', '08/08/2022_A3'), datetime(2022, 8, 8, 23, 0))]]}, 3: {1: [(1, False), [(('REC', '1', '08/08/2022_A1'), datetime(2022, 8, 8, 10, 0)), (('REC', '1', '08/08/2022_A2'), datetime(2022, 8, 8, 11, 30)), (('REC', '2', '08/08/2022_A1'), datetime(2022, 8, 8, 10, 45)), (('REC', '2', '08/08/2022_A2'), datetime(2022, 8, 8, 11, 45)), (('REC', '3', '08/08/2022_A1'), datetime(2022, 8, 8, 13, 15)), (('REC', '3', '08/08/2022_A2'), datetime(2022, 8, 8, 13, 0))]]}, 4: {5: [(2, True), [(('FOR', '1', '09/08/2022_D3'), datetime(2022, 8, 8, 23, 15)), (('FOR', '2', '09/08/2022_D3'), datetime(2022, 8, 8, 23, 30)), (('FOR', '3', '09/08/2022_D3'), datetime(2022, 8, 9, 2, 0)), (('DEP', '4', '09/08/2022_D3'), datetime(2022, 8, 9, 2, 15))]], 7: [(1, True), [(('FOR', '1', '08/08/2022_D1'), datetime(2022, 8, 8, 13, 30)), (('FOR', '1', '08/08/2022_D2'), datetime(2022, 8, 8, 13, 15)), (('FOR', '2', '08/08/2022_D1'), datetime(2022, 8, 8, 13, 45)), (('FOR', '2', '08/08/2022_D2'), datetime(2022, 8, 8, 16, 50)), (('FOR', '3', '08/08/2022_D1'), datetime(2022, 8, 8, 16, 15)), (('FOR', '3', '08/08/2022_D2'), datetime(2022, 8, 8, 19, 30)), (('DEP', '4', '08/08/2022_D1'), datetime(2022, 8, 8, 16, 30)), (('DEP', '4', '08/08/2022_D2'), datetime(2022, 8, 8, 19, 45))]]}}, 2: {0: {1: [(2, True), [(('REC', '1', '09/08/2022_A3'), datetime(2022, 8, 9, 22, 0)), (('REC', '2', '09/08/2022_A3'), datetime(2022, 8, 9, 22, 15)), (('REC', '3', '09/08/2022_A3'), datetime(2022, 8, 9, 23, 0))]]}, 1: {6: [(1, True), [(('FOR', '1', '09/08/2022_D1'), datetime(2022, 8, 9, 13, 0)), (('FOR', '1', '09/08/2022_D2'), datetime(2022, 8, 9, 13, 15)), (('FOR', '2', '09/08/2022_D1'), datetime(2022, 8, 9, 13, 30)), (('FOR', '2', '09/08/2022_D2'), datetime(2022, 8, 9, 16, 15)), (('FOR', '3', '09/08/2022_D1'), datetime(2022, 8, 9, 16, 0)), (('FOR', '3', '09/08/2022_D2'), datetime(2022, 8, 9, 18, 45))]]}, 3: {1: [(1, False), [(('REC', '1', '09/08/2022_A2'), datetime(2022, 8, 9, 11, 30)), (('REC', '1', '09/08/2022_A1'), datetime(2022, 8, 9, 10, 0)), (('REC', '2', '09/08/2022_A2'), datetime(2022, 8, 9, 11, 45)), (('REC', '2', '09/08/2022_A1'), datetime(2022, 8, 9, 10, 15)), (('REC', '3', '09/08/2022_A2'), datetime(2022, 8, 9, 12, 30)), (('REC', '3', '09/08/2022_A1'), datetime(2022, 8, 9, 11, 0)), (('DEP', '4', '09/08/2022_D1'), datetime(2022, 8, 9, 16, 40))]]}, 4: {1: [(2, True), [(('FOR', '1', '10/08/2022_D3'), datetime(2022, 8, 9, 23, 15)), (('FOR', '2', '10/08/2022_D3'), datetime(2022, 8, 9, 23, 30)), (('FOR', '3', '10/08/2022_D3'), datetime(2022, 8, 10, 2, 0)), (('DEP', '4', '09/08/2022_D2'), datetime(2022, 8, 9, 22, 30)), (('DEP', '4', '10/08/2022_D3'), datetime(2022, 8, 10, 2, 15))]]}}, 3: {0: {1: [(2, True), [(('REC', '1', '10/08/2022_A3'), datetime(2022, 8, 10, 22, 0)), (('REC', '2', '10/08/2022_A3'), datetime(2022, 8, 10, 22, 15)), (('REC', '3', '10/08/2022_A3'), datetime(2022, 8, 10, 23, 0))]]}, 3: {1: [(1, False), [(('REC', '1', '10/08/2022_A1'), datetime(2022, 8, 10, 10, 0)), (('REC', '1', '10/08/2022_A2'), datetime(2022, 8, 10, 11, 30)), (('REC', '2', '10/08/2022_A1'), datetime(2022, 8, 10, 10, 15)), (('REC', '2', '10/08/2022_A2'), datetime(2022, 8, 10, 11, 45)), (('REC', '3', '10/08/2022_A1'), datetime(2022, 8, 10, 11, 0)), (('REC', '3', '10/08/2022_A2'), datetime(2022, 8, 10, 12, 30))]]}, 4: {1: [(1, True), [(('FOR', '1', '10/08/2022_D1'), datetime(2022, 8, 10, 13, 0)), (('FOR', '1', '10/08/2022_D2'), datetime(2022, 8, 10, 14, 30)), (('FOR', '2', '10/08/2022_D1'), datetime(2022, 8, 10, 14, 45)), (('FOR', '2', '10/08/2022_D2'), datetime(2022, 8, 10, 18, 30)), (('FOR', '3', '10/08/2022_D1'), datetime(2022, 8, 10, 17, 15)), (('DEP', '4', '10/08/2022_D1'), datetime(2022, 8, 10, 17, 30))]], 7: [(2, True), [(('FOR', '1', '11/08/2022_D3'), datetime(2022, 8, 10, 23, 15)), (('FOR', '2', '11/08/2022_D3'), datetime(2022, 8, 10, 23, 30)), (('FOR', '3', '10/08/2022_D2'), datetime(2022, 8, 10, 21, 0)), (('FOR', '3', '11/08/2022_D3'), datetime(2022, 8, 11, 2, 0)), (('DEP', '4', '10/08/2022_D2'), datetime(2022, 8, 10, 21, 15)), (('DEP', '4', '11/08/2022_D3'), datetime(2022, 8, 11, 2, 15))]]}}, 4: {0: {2: [(2, True), [(('REC', '1', '11/08/2022_A3'), datetime(2022, 8, 11, 22, 0)), (('REC', '2', '11/08/2022_A3'), datetime(2022, 8, 11, 22, 15)), (('REC', '3', '11/08/2022_A3'), datetime(2022, 8, 11, 23, 0))]]}, 3: {1: [(1, False), [(('REC', '1', '11/08/2022_A2'), datetime(2022, 8, 11, 11, 30)), (('REC', '1', '11/08/2022_A1'), datetime(2022, 8, 11, 10, 0)), (('REC', '2', '11/08/2022_A2'), datetime(2022, 8, 11, 11, 45)), (('REC', '2', '11/08/2022_A1'), datetime(2022, 8, 11, 10, 15)), (('REC', '3', '11/08/2022_A2'), datetime(2022, 8, 11, 12, 30)), (('REC', '3', '11/08/2022_A1'), datetime(2022, 8, 11, 11, 0))]]}, 4: {4: [(2, True), [(('FOR', '1', '12/08/2022_D3'), datetime(2022, 8, 11, 23, 15)), (('FOR', '2', '12/08/2022_D3'), datetime(2022, 8, 11, 23, 30)), (('FOR', '3', '11/08/2022_D2'), datetime(2022, 8, 11, 22, 15)), (('FOR', '3', '12/08/2022_D3'), datetime(2022, 8, 12, 2, 0)), (('DEP', '4', '11/08/2022_D2'), datetime(2022, 8, 11, 22, 30)), (('DEP', '4', '12/08/2022_D3'), datetime(2022, 8, 12, 2, 15))]], 7: [(1, True), [(('FOR', '1', '11/08/2022_D1'), datetime(2022, 8, 11, 14, 30)), (('FOR', '1', '11/08/2022_D2'), datetime(2022, 8, 11, 14, 15)), (('FOR', '2', '11/08/2022_D1'), datetime(2022, 8, 11, 14, 45)), (('FOR', '2', '11/08/2022_D2'), datetime(2022, 8, 11, 18, 30)), (('FOR', '3', '11/08/2022_D1'), datetime(2022, 8, 11, 17, 15)), (('DEP', '4', '11/08/2022_D1'), datetime(2022, 8, 11, 17, 40))]]}}, 5: {0: {1: [(0, True), [(('REC', '1', '12/08/2022_A2'), datetime(2022, 8, 12, 11, 30)), (('REC', '1', '12/08/2022_A1'), datetime(2022, 8, 12, 10, 0)), (('REC', '2', '12/08/2022_A2'), datetime(2022, 8, 12, 11, 45)), (('REC', '2', '12/08/2022_A1'), datetime(2022, 8, 12, 10, 15)), (('REC', '3', '12/08/2022_A2'), datetime(2022, 8, 12, 12, 30)), (('REC', '3', '12/08/2022_A1'), datetime(2022, 8, 12, 11, 0))]], 2: [(2, True), [(('REC', '1', '12/08/2022_A3'), datetime(2022, 8, 12, 22, 0)), (('REC', '2', '12/08/2022_A3'), datetime(2022, 8, 12, 22, 15)), (('REC', '3', '12/08/2022_A3'), datetime(2022, 8, 12, 23, 0))]]}, 4: {4: [(1, True), [(('FOR', '1', '12/08/2022_D2'), datetime(2022, 8, 12, 18, 0)), (('FOR', '1', '12/08/2022_D1'), datetime(2022, 8, 12, 13, 0)), (('FOR', '2', '12/08/2022_D2'), datetime(2022, 8, 12, 18, 15)), (('FOR', '2', '12/08/2022_D1'), datetime(2022, 8, 12, 13, 15)), (('FOR', '3', '12/08/2022_D1'), datetime(2022, 8, 12, 17, 15)), (('DEP', '4', '12/08/2022_D1'), datetime(2022, 8, 12, 17, 30))]], 7: [(2, True), [(('FOR', '1', '13/08/2022_D3'), datetime(2022, 8, 12, 23, 15)), (('FOR', '2', '13/08/2022_D3'), datetime(2022, 8, 12, 23, 30)), (('FOR', '3', '12/08/2022_D2'), datetime(2022, 8, 12, 22, 15)), (('FOR', '3', '13/08/2022_D3'), datetime(2022, 8, 13, 2, 0)), (('DEP', '4', '12/08/2022_D2'), datetime(2022, 8, 12, 22, 30)), (('DEP', '4', '13/08/2022_D3'), datetime(2022, 8, 13, 2, 15))]]}}, 6: {0: {1: [(2, True), [(('REC', '1', '13/08/2022_A3'), datetime(2022, 8, 13, 22, 0)), (('REC', '2', '13/08/2022_A3'), datetime(2022, 8, 13, 22, 15)), (('REC', '3', '13/08/2022_A3'), datetime(2022, 8, 13, 23, 0))]], 5: [(0, True), [(('REC', '1', '13/08/2022_A4'), datetime(2022, 8, 13, 8, 45)), (('REC', '2', '13/08/2022_A4'), datetime(2022, 8, 13, 9, 0)), (('REC', '3', '13/08/2022_A4'), datetime(2022, 8, 13, 9, 45))]]}, 1: {2: [(0, True), [(('FOR', '1', '13/08/2022_D4'), datetime(2022, 8, 13, 10, 0)), (('FOR', '2', '13/08/2022_D4'), datetime(2022, 8, 13, 10, 15)), (('FOR', '3', '13/08/2022_D4'), datetime(2022, 8, 13, 12, 45))]]}, 4: {3: [(2, True), [(('FOR', '1', '14/08/2022_D3'), datetime(2022, 8, 13, 23, 15)), (('FOR', '2', '14/08/2022_D3'), datetime(2022, 8, 13, 23, 30)), (('FOR', '3', '14/08/2022_D3'), datetime(2022, 8, 14, 2, 0)), (('DEP', '4', '13/08/2022_D4'), datetime(2022, 8, 13, 21, 0)), (('DEP', '4', '14/08/2022_D3'), datetime(2022, 8, 14, 2, 15))]]}}, 7: {0: {2: [(0, True), [(('REC', '1', '14/08/2022_A4'), datetime(2022, 8, 14, 8, 45)), (('REC', '2', '14/08/2022_A4'), datetime(2022, 8, 14, 9, 0)), (('REC', '3', '14/08/2022_A4'), datetime(2022, 8, 14, 9, 45))]]}, 4: {1: [(0, True), [(('FOR', '1', '14/08/2022_D4'), datetime(2022, 8, 14, 10, 0)), (('FOR', '2', '14/08/2022_D4'), datetime(2022, 8, 14, 10, 15)), (('FOR', '3', '14/08/2022_D4'), datetime(2022, 8, 14, 12, 45))]], 6: [(2, True), [(('DEP', '4', '14/08/2022_D4'), datetime(2022, 8, 14, 21, 0))]]}}}
    display_human_tasks(dic_instance2,datetime(2022, 8, 8, 22, 0) , False)
