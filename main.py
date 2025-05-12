import pygame
import math
import sys
import random # Assurez-vous que random est importé

# --- Constantes ---
# Dimensions de l'écran (format TikTok : 9:16)
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 800
CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GRAY = (150, 150, 150)
BLUE = (100, 100, 255) # Couleur pour les cercles

# Paramètres de la balle
BALL_RADIUS = 8
INITIAL_BALL_SPEED = 250 # Pixels par seconde

# Paramètres des cercles
NUM_CIRCLES = 16 # 1 initial + 15 autour
INITIAL_RADIUS = 40
RADIUS_STEP = (SCREEN_HEIGHT // 2 - INITIAL_RADIUS - BALL_RADIUS * 3) / (NUM_CIRCLES -1) if NUM_CIRCLES > 1 else 0 # Ajuste l'espacement
CIRCLE_THICKNESS = 3
GAP_PERCENTAGE = 0.15 # 15% de la circonférence
GAP_ANGLE_RAD = 2 * math.pi * GAP_PERCENTAGE
# Orientation initiale de l'ouverture (ex: en haut)
INITIAL_GAP_CENTER_ANGLE_RAD = 3 * math.pi / 2
# Vitesse de rotation (radians par seconde). Positif = anti-horaire, Négatif = horaire
# Mettons une vitesse de base, on pourra la varier pour chaque cercle
BASE_ROTATION_SPEED_RAD_PER_SEC = math.pi / 4 # Tour complet en 8 secondes

# Physique et jeu
FPS = 60

# --- Initialisation Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Balle dans Cercles Rotatifs")
clock = pygame.time.Clock()

# --- Fonctions Utilitaires (Gestion des angles) ---
def normalize_angle(angle_rad):
    """ Normalise un angle en radians dans l'intervalle [0, 2*pi) """
    while angle_rad < 0:
        angle_rad += 2 * math.pi
    while angle_rad >= 2 * math.pi:
        angle_rad -= 2 * math.pi
    return angle_rad

def is_angle_in_gap(angle_rad, gap_center_rad, gap_width_rad):
    """ Vérifie si un angle est dans l'ouverture """
    norm_angle = normalize_angle(angle_rad)
    gap_start = normalize_angle(gap_center_rad - gap_width_rad / 2)
    gap_end = normalize_angle(gap_center_rad + gap_width_rad / 2)

    if gap_start > gap_end: # L'ouverture passe par 0 radians
        return norm_angle >= gap_start or norm_angle <= gap_end
    else: # Ouverture "normale"
        return gap_start <= norm_angle <= gap_end

# --- Classe Ball (Inchangée) ---
class Ball:
    def __init__(self, x, y, radius, color, initial_vx, initial_vy):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        self.vx = float(initial_vx)
        self.vy = float(initial_vy)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def reflect_velocity(self, nx, ny):
        dot_product = self.vx * nx + self.vy * ny
        # Prévenir les rebonds multiples si la balle est déjà en train de s'éloigner
        if dot_product < 0: # Seulement si la balle va *vers* le mur
             self.vx -= 2 * dot_product * nx
             self.vy -= 2 * dot_product * ny

    def get_pos(self):
        return self.x, self.y

    def get_velocity(self):
         return self.vx, self.vy

# --- Classe CircleWall (Modifiée) ---
class CircleWall:
    def __init__(self, center_x, center_y, radius, color, thickness,
                 initial_gap_center_rad, gap_width_rad, rotation_speed):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.gap_width_rad = gap_width_rad
        self.rotation_speed = rotation_speed # Vitesse de rotation en rad/s

        # Angle courant du centre de l'ouverture (commence à l'initial)
        self.gap_center_rad = normalize_angle(initial_gap_center_rad)

        # Initialiser les angles de dessin (seront mis à jour dans update)
        self.arc_start_angle_pygame = 0
        self.arc_end_angle_pygame = 0
        self._recalculate_draw_angles() # Appel initial

    def _recalculate_draw_angles(self):
        """ Recalcule les angles nécessaires pour pygame.draw.arc """
        gap_start_rad = normalize_angle(self.gap_center_rad - self.gap_width_rad / 2)
        gap_end_rad = normalize_angle(self.gap_center_rad + self.gap_width_rad / 2)

        # Angles pour pygame.draw.arc (sens horaire Pygame, 0=droite)
        # L'arc commence à la fin de l'ouverture et finit au début
        self.arc_start_angle_pygame = gap_end_rad
        self.arc_end_angle_pygame = gap_start_rad

    def update(self, dt):
        """ Met à jour l'angle de l'ouverture et les angles de dessin """
        self.gap_center_rad += self.rotation_speed * dt
        self.gap_center_rad = normalize_angle(self.gap_center_rad)
        # Recalculer les angles pour le dessin après la mise à jour de la position du gap
        self._recalculate_draw_angles()

    def draw(self, surface):
        """ Dessine l'arc de cercle (le mur) """
        rect = pygame.Rect(self.center_x - self.radius, self.center_y - self.radius,
                           2 * self.radius, 2 * self.radius)
        # Utilise les angles pré-calculés dans update
        pygame.draw.arc(surface, self.color, rect,
                        self.arc_start_angle_pygame,
                        self.arc_end_angle_pygame,
                        self.thickness)

    def is_ball_in_gap(self, ball):
        """ Vérifie si la position de la balle correspond à l'ouverture ACTUELLE du cercle """
        dx = ball.x - self.center_x
        dy = ball.y - self.center_y
        # Angle de la balle par rapport au centre (convention mathématique standard)
        ball_angle_math = math.atan2(-dy, dx)

        # Vérifie si cet angle est dans l'ouverture ACTUELLE
        return is_angle_in_gap(ball_angle_math, self.gap_center_rad, self.gap_width_rad)

# --- Logique Principale (Modifiée) ---
def main():
    # --- Création des objets ---
    angle_start = random.uniform(0, 2*math.pi)
    ball = Ball(CENTER_X + 1, CENTER_Y, BALL_RADIUS, RED,
                INITIAL_BALL_SPEED * math.cos(angle_start),
                INITIAL_BALL_SPEED * math.sin(angle_start))

    circles = []
    for i in range(NUM_CIRCLES):
        radius = INITIAL_RADIUS + i * RADIUS_STEP
        # Donner une vitesse de rotation différente à chaque cercle pour l'esthétique
        # Par exemple, alterner le sens et varier légèrement la vitesse
        direction = 1 if i % 2 == 0 else -1
        # Vitesse légèrement différente, ex: plus rapide pour les petits cercles
        speed_modifier = 1 + (NUM_CIRCLES - 1 - i) * 0.2 # Plus rapide à l'intérieur
        rotation_speed = direction * BASE_ROTATION_SPEED_RAD_PER_SEC * speed_modifier

        circle = CircleWall(CENTER_X, CENTER_Y, radius, BLUE, CIRCLE_THICKNESS,
                            INITIAL_GAP_CENTER_ANGLE_RAD, # Chaque cercle commence avec le même alignement
                            GAP_ANGLE_RAD,
                            rotation_speed) # Passer la vitesse de rotation
        circles.append(circle)

    # --- Boucle de jeu ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # --- Gestion des événements ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Mises à jour ---
        ball.update(dt)
        # Mettre à jour la rotation de tous les cercles actifs
        for circle in circles:
            circle.update(dt) # Appel de la nouvelle méthode update

        # --- Détection des collisions et logique ---
        if circles:
            current_circle = circles[0]

            dx = ball.x - current_circle.center_x
            dy = ball.y - current_circle.center_y
            dist_sq = dx*dx + dy*dy
            dist = math.sqrt(dist_sq)

            collision_threshold = current_circle.radius
            # Pour le rebond, on veut la surface intérieure du mur épais
            # Mais pour détecter si on DOIT rebondir, le rayon extérieur suffit.
            # Pour passer, on vérifie si le *centre* de la balle a dépassé le rayon
            # Modifions légèrement la logique pour être plus précis:
            # Collision si la distance bord_balle < rayon_mur_interne
            # Passage si dist > rayon_mur_externe et angle dans le gap

            # Test de collision potentiel (la balle touche la zone du cercle)
            # On regarde si le bord extérieur de la balle touche ou dépasse le rayon intérieur du mur
            # Ou si le centre de la balle est proche du rayon
            if dist + ball.radius >= collision_threshold - current_circle.thickness / 2: # Proche ou à l'intérieur du mur

                 # Vérifier si la balle est "alignée" avec l'ouverture au moment où elle atteint le rayon
                 if current_circle.is_ball_in_gap(ball):
                     # Pour considérer un passage, la balle doit effectivement avoir dépassé le rayon
                     # Vérifions si le *centre* de la balle est sorti (dist > radius)
                     # Ou si la balle est suffisamment engagée dans l'ouverture
                     # Une condition simple : si elle touche et est dans l'angle, et va vers l'extérieur
                     vel_x, vel_y = ball.get_velocity()
                     # Produit scalaire de la position relative et de la vitesse
                     # Si positif, la balle s'éloigne du centre
                     dot_product_pos_vel = dx * vel_x + dy * vel_y
                     
                     # On passe si on est dans l'angle du gap ET on s'éloigne du centre
                     # ET que le centre de la balle a au moins atteint le rayon
                     if dot_product_pos_vel > 0 and dist >= collision_threshold - ball.radius: # Ajustement pour le passage
                         print(f"Balle passée à travers le cercle de rayon {current_circle.radius:.0f} (Gap: {current_circle.gap_center_rad:.2f})")
                         circles.pop(0)
                         current_circle = None # Le cercle courant n'existe plus pour cette frame
                     # Sinon (même si dans l'angle, mais on va vers l'intérieur ou on n'a pas dépassé), on rebondit quand même sur le "bord" du gap? Non, laissons passer.
                     # Si on est dans l'angle mais on arrive de l'extérieur vers l'intérieur? Ça ne devrait pas arriver si on commence dedans.

                 # Si collision ET pas dans le gap => Rebond
                 elif current_circle and dist + ball.radius >= collision_threshold: # Assurons nous qu'on touche bien
                     # Normal vector (centre vers balle)
                     nx = dx / dist
                     ny = dy / dist

                     # Reflect velocity
                     ball.reflect_velocity(nx, ny)

                     # Position correction (replacer la balle exactement sur le cercle)
                     # Pousser la balle pour que son bord soit sur le rayon
                     target_dist = collision_threshold - ball.radius
                     correction_dist = target_dist - dist
                     ball.x += correction_dist * nx
                     ball.y += correction_dist * ny
                     #print(f"Rebond sur cercle {current_circle.radius:.0f}") # Debug

            # Alternative pour le passage: si la balle sort complètement du rayon ET est dans l'angle?
            # if dist - ball.radius > current_circle.radius: # La balle est complètement sortie
            #      if current_circle.is_ball_in_gap(ball):
            #           print(f"Balle passée (méthode 2)...")
            #           circles.pop(0)
            #           current_circle = None


        if not circles:
            pass

        # --- Dessin ---
        screen.fill(BLACK)
        for circle in circles:
            circle.draw(screen)
        ball.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()