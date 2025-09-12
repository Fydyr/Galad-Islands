# Importations
import pygame



# Couleurs
BLANC = (255, 255, 255)
VERT = (0, 200, 0)
GRIS = (150, 150, 150)
ROUGE = (200, 0, 0)

# Fenêtre principale
TAILLE_FENETRE = (1000, 600)
fenetre = pygame.display.set_mode(TAILLE_FENETRE)
pygame.display.set_caption("Galad Islands")
pygame.font.init() # Initialisation du module font de Pygame

# Titres
font_titre = pygame.font.SysFont(None, 72)
font_sous_titre = pygame.font.SysFont(None, 36)
titre = font_titre.render("Galad Islands", True, (0, 0, 0))
sous_titre = font_sous_titre.render("Menu Principal", True, (50, 50, 50))

# Fonction pour dessiner un bouton
def dessiner_bouton(x, y, largeur, hauteur, couleur, texte):
    pygame.draw.rect(fenetre, couleur, (x, y, largeur, hauteur))
    font_bouton = pygame.font.SysFont(None, 32)
    texte_surface = font_bouton.render(texte, True, (0, 0, 0))
    texte_rect = texte_surface.get_rect(center=(x + largeur // 2, y + hauteur // 2))
    fenetre.blit(texte_surface, texte_rect)

# Fonction pour le menu principal
def menu_principal():
    """Gére le menu principal du jeu

    Returns:
        None
    """
    en_cours = True
    while en_cours:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                en_cours = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Vérifiez si un bouton a été cliqué
                if 250 <= x <= 750 and 200 <= y <= 250: # Debut d'une partie
                    # Lancer la partie rapide
                    return None
                elif 250 <= x <= 750 and 250 <= y <= 300: # Scénario
                    # Afficher un message d'indisponibilité
                    return None
                elif 250 <= x <= 750 and 300 <= y <= 350: # Quitter
                    en_cours = False

        fenetre.fill(BLANC)  # Efface l'écran

        # Dessinez vos boutons dans l'état du menu
        logo = pygame.image.load("assets/logo.png")
        fenetre.blit(titre, (100, 100))
        fenetre.blit(sous_titre, (100, 150))
        # Changer les positions des boutons pour les espacer
        dessiner_bouton(250, 200, 500, 50, VERT, "Partie rapide")
        dessiner_bouton(250, 250, 500, 50, GRIS,
                        "Scénario")
        dessiner_bouton(250, 300, 500, 50, ROUGE, "Quitter")

        pygame.display.flip()
