""" Tools used to generates colors for the agenda """
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

def create_color_scale(filling_level, max_level, _color1=(0, 0, 255), _color2=(255, 0, 0)):
    """
    Returns the value color for filling_level in [color1, color2]
    Filing_level is in [0, max_level]
    """
    ratio = filling_level/max_level
    r1, g1, b1 = _color1
    r2, g2, b2 = _color2
    interpolated_r = r1 + ratio*(r2 - r1)
    interpolated_g = g1 + ratio*(g2 - g1)
    interpolated_b = b1 + ratio*(b2 - b1)

    return f"#{int(interpolated_r):02x}{int(interpolated_g):02x}{int(interpolated_b):02x}"
