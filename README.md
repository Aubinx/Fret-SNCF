# Projet triage fret gare SCNF Trenitalia groupe 4

Bienvenue dans ce répôt Git ! :grinning:

Dans ce projet, nous cherchons à modéliser la gestion d'une gare de triage fret. :steam_locomotive: Nous utilisons les données de la gare de Woippy, la plus grande gare de triage en France :fr:, à la frontière avec le Luxembourg et l'Allemagne. Mais le principe est le même quelque soit la gare de triage considérée.

Le dossier "Instances" stocke les instances de différentes tailles : la mini-instance qui a moins de 10 trains, l'instance simple et enfin l'instance réaliste avec une centaine de trains, qui correspond aux vraies données de la gare de Woippy. :train2:

Le dossier "display_tools" contient tous les modules que nous avons développé pour l'affichage des résultats du modèle sous la forme d'un magnifique agenda. :calendar:

Ensuite il y a plusieurs fichiers :
- le `.gitignore`
- le `requirements.txt` qui permet de savoir avec quelles bibliothèques python et quelles versions nous avons travaillé. 
- `estim_nb_vars.ipynb` un notebook python qui permet manuellement d'estimer le nombre de variables présents dans le modèle d'après l'étude théorique menée dans le rapport.
- `horaires.py` permet de gérer les dates en passant du format entier que nous utilisons dans le modèle à celui usuel avec l'heure et la date.
- `lecture_donnees.py` qui permet de lire toutes les donnés utiles à partir des fichiers du dossier Instances et d'en faire des dataframe `pandas` plus faciles à manipuler
- `donnees_trains.py` qui contient beaucoup de fonctions utiles à inférer depuis les données de l'instance : par exemple les liens entre les trains d'arrivées et de départ ou les créneaux d'indisponibilités des machines.
- `model.py`, `model_jalon2.py` et `model_jalon3.py` : il s'agit des fichiers contenant les modèles gurobi que nous avons développés. Chaque nouveau jalon vient raffiner le modèle du jalon précédent pour prendre en compte un aspect supplémentaire.
- `main.py` c'est le fichier qu'il faut lancer pour faire tourner le modèle d'optimisation implémenté.
- `heuristic_dichotomy.py` un fichier à exécuter pour chercher à résoudre le jalon 2 sur une instance trop grosse. Il implémente une recherche dichotomique du nombre optimal de voies occupées dans le chantier de formation.
- `output.py` : ce fichier permet de générer automatiquement un fichier `excel` contenant l'ordonnancement des tâches obtenu après optimisation du modèle.
- `util.py` : un fichier utilitaire regroupant différentes classes qui facilitent le reste du code.
- et enfin, ce Readme. :wink:

Pour que tous les codes puissent bien s'exécuter, il faut veiller à créer encore deux dossiers à la racine de ce répôt : "Outputs" et "Modeles". Ces dossiers seront utilisés pour écrire respectivement les fichiers de sortie du modèle (fichiers `excel` créés par `output.py` et fichier `.sol` créés par gurobi dans `main.py`) et les modèles gurobi juste avant optimisation sous le format `.lp` créés par gurobi dans `main.py`

Bon voyage dans ce répôt Git ! :roller_coaster: :runner:
