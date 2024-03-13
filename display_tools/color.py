""" Generates n colors spread across the visible spectrum """
import colorsys

def generate_colors(number_of_colors):
    """ Generates n colors spread across the visible spectrum """
    # Calculer l'espacement entre les couleurs
    hue_spacing = 1.0 / number_of_colors

    # Initialiser une liste pour stocker les couleurs générées
    colors = []

    # Générer n couleurs réparties uniformément sur le spectre
    for i in range(number_of_colors):
        hue = i * hue_spacing
        rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        _r,_g,_b = tuple(int(c * 255) for c in rgb)
        colors.append(f"#{_r:02x}{_g:02x}{_b:02x}")
    return colors
