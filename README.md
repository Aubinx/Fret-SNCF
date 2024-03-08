# Projet triage fret gare SCNF Trenitalia groupe 4

Bienvenue dans ce répôt Git ! :grinning:

Dans ce projet, nous cherchons à modéliser la gestion d'une gare de triage fret. :steam_locomotive: Nous utilisons les données de la gare de Woippy, la plus grande gare de triage en France :fr:, à la frontière avec le Luxembourg et l'Allemagne. Mais le principe est le même quelque soit la gare de triage considérée.

Le dossier "Instances" stocke les instances de différentes tailles : la mini-instance qui a moins de 10 trains, l'instance simple et enfin l'instance réaliste avec une centaine de trains, qui correspond aux vraies données de la gare de Woippy. :train2:

Ensuite il y a plusieurs fichiers :
- le .gitignore
- Horaires.py permet de gérer les dates en passant du format entier que nous utilisons dans le modèle à celui usuel avec l'heure et la date.
- LectureDonnees.py qui permet de récupérer toutes les donnés utiles à partir des fichiers du dossier Instances : par exemple les informations sur les trains d'arrivées et de départ et les indisponibilités des machines.
- Model.py : c'est le fichier qu'il faut lancer pour faire tourner le modèle d'optimisation implémenté.
- Util.py : un fichier utilitaire regroupant différentes classes.
- et enfin, ce Readme. :wink:

Bon voyage dans ce répôt Git ! :roller_coaster: :runner:
