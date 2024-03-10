from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import colorsys

def generate_colors(n):
    # Calculer l'espacement entre les couleurs
    hue_spacing = 1.0 / n

    # Initialiser une liste pour stocker les couleurs générées
    colors = []

    # Générer n couleurs réparties uniformément sur le spectre
    for i in range(n):
        hue = i * hue_spacing
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colors.append(tuple(int(c * 255) for c in rgb))

    return colors

def generate_colors(n):
    hue_spacing = 1.0 / n
    colors = []

    for i in range(n):
        hue = i * hue_spacing
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        colors.append(tuple(int(c * 255) for c in rgb))

    return colors



# Exemple d'utilisation avec n=10 et hauteur de chaque bande = 30 pixels
nombre_de_couleurs = 100
hauteur_de_chaque_bande = 30
couleurs = generate_colors(nombre_de_couleurs)
