
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
        r,g,b = tuple(int(c * 255) for c in rgb)
        colors.append(f"#{r:02x}{g:02x}{b:02x}")
    print(colors)
    return colors

