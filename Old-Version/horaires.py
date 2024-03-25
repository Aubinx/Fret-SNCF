"""Module pour gérer les transformations entre créneau et date réelle"""

def triplet_vers_entier(jour, heure, minute):
    '''
    Convertit un triplet de la forme (jour, heure, minute) en un entier positif avec :
        `jour` un entier supérieur ou égal à 1.
        Par convention, on choisit le jour 1 comme le lundi de la première semaine.
        `heure` un entier compris entre 0 et 23.
        `minute` un entier compris entre 0 et 59.
    Toute minute correspond à un entier positif, par ordre chronologique.
    Par convention, l'entier 0 correspond au lundi du jour 1 à 00h00,
    c'est-à-dire au triplet (1, 0, 0)
    '''
    assert isinstance(jour, int) and jour >= 1, "Le jour doit être un entier supérieur ou égal à 1"
    assert heure in range(24) , "L'heure doit être un entier compris entre 0 et 23"
    assert minute in range(60) , "La minute doit être un entier compris entre 0 et 59"

    entier = (jour - 1) * 24 * 60 + heure * 60 + minute
    return entier

def entier_vers_triplet(entier):
    """
    Convertit un entier positif en triplet de la forme (jour, heure, minute)
    comme défini dans l'en-tête de la fonction "triplet_vers_entier"
    """
    assert isinstance(entier, int) and entier >= 0
    jour = entier // (24 * 60) + 1
    reste_minutes = entier % (24 * 60)
    heure = reste_minutes // 60
    minute = reste_minutes % 60
    return (jour, heure, minute)
