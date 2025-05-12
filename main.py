import pygame
import math
import sys
import random

# --- Constantes (Identiques à avant) ---
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 800
CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (100, 100, 255)
BALL_RADIUS = 8
INITIAL_BALL_SPEED = 250
NUM_CIRCLES = 16
INITIAL_RADIUS = 40
RADIUS_STEP = (SCREEN_HEIGHT // 2 - INITIAL_RADIUS - BALL_RADIUS * 3) / (NUM_CIRCLES -1) if NUM_CIRCLES > 1 else 0
CIRCLE_THICKNESS = 3
GAP_PERCENTAGE = 0.15
GAP_ANGLE_RAD = 2 * math.pi * GAP_PERCENTAGE
INITIAL_GAP_CENTER_ANGLE_RAD = 3 * math.pi / 2
BASE_ROTATION_SPEED_RAD_PER_SEC = math.pi / 4
FPS = 60
GRAVITY_ACCELERATION = 400.0 # Pixels par seconde^2 (Ajustez cette valeur !)

# --- Initialisation Pygame (Identique) ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Balle dans Cercles Rotatifs")
clock = pygame.time.Clock()

# --- Fonctions Utilitaires (Identiques) ---
def normalize_angle(angle_rad):
    while angle_rad < 0:
        angle_rad += 2 * math.pi
    while angle_rad >= 2 * math.pi:
        angle_rad -= 2 * math.pi
    return angle_rad

def is_angle_in_gap(angle_rad, gap_center_rad, gap_width_rad):
    norm_angle = normalize_angle(angle_rad)
    gap_start = normalize_angle(gap_center_rad - gap_width_rad / 2)
    gap_end = normalize_angle(gap_center_rad + gap_width_rad / 2)
    if gap_start > gap_end:
        return norm_angle >= gap_start or norm_angle <= gap_end
    else:
        return gap_start <= norm_angle <= gap_end

# --- Classe Ball (Identique) ---
class Ball:
    def __init__(self, x, y, radius, color, initial_vx, initial_vy):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        self.vx = float(initial_vx)
        self.vy = float(initial_vy)

    def update(self, dt):

        self.vy += GRAVITY_ACCELERATION * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.radius)

    def reflect_velocity(self, nx, ny):
        dot_product = self.vx * nx + self.vy * ny
        # On ne réfléchit que si la balle va VERS le mur (produit scalaire < 0)
        if dot_product > 0: # Corrigé: Normal (nx,ny) pointe vers l'extérieur. Si v et n pointent dans la même direction générale (dot > 0), la balle s'éloigne déjà. On ne réfléchit que si elle va vers le centre (dot < 0). MAIS ATTENTION, la normale pour la REFLEXION doit être celle du point d'impact. Si la balle est à l'intérieur et touche, la normale pointe VERS L'EXTERIEUR (centre->balle). Si la balle va vers l'extérieur (vx*nx + vy*ny > 0), elle heurte le mur.
            # Mise à jour: La réflexion doit se faire si la composante de vitesse normale est positive (allant vers l'extérieur).
            # Formule: v' = v - 2 * proj_n(v) = v - 2 * dot(v, n) * n
             reflect_vx = self.vx - 2 * dot_product * nx
             reflect_vy = self.vy - 2 * dot_product * ny
             # Vérification simple de changement de direction radiale
             # new_dot = reflect_vx * nx + reflect_vy * ny
             # if new_dot < 0: # S'assurer que la nouvelle vitesse va bien vers l'intérieur
             self.vx = reflect_vx
             self.vy = reflect_vy


    def get_pos(self):
        return self.x, self.y

    def get_velocity(self):
         return self.vx, self.vy

# --- Classe CircleWall (Modification mineure: is_ball_in_gap prend l'angle) ---
class CircleWall:
    def __init__(self, center_x, center_y, radius, color, thickness,
                 initial_gap_center_rad, gap_width_rad, rotation_speed):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.gap_width_rad = gap_width_rad
        self.rotation_speed = rotation_speed
        self.gap_center_rad = normalize_angle(initial_gap_center_rad)
        self.arc_start_angle_pygame = 0
        self.arc_end_angle_pygame = 0
        self._recalculate_draw_angles()

    def _recalculate_draw_angles(self):
        gap_start_rad = normalize_angle(self.gap_center_rad - self.gap_width_rad / 2)
        gap_end_rad = normalize_angle(self.gap_center_rad + self.gap_width_rad / 2)
        self.arc_start_angle_pygame = gap_end_rad
        self.arc_end_angle_pygame = gap_start_rad

    def update(self, dt):
        self.gap_center_rad += self.rotation_speed * dt
        self.gap_center_rad = normalize_angle(self.gap_center_rad)
        self._recalculate_draw_angles()

    def draw(self, surface):
        rect = pygame.Rect(self.center_x - self.radius, self.center_y - self.radius,
                           2 * self.radius, 2 * self.radius)
        # Éviter l'erreur si start == end après normalisation et flottants
        if abs(self.arc_start_angle_pygame - self.arc_end_angle_pygame) < 0.001:
             pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), self.radius, self.thickness)
        else:
             pygame.draw.arc(surface, self.color, rect,
                             self.arc_start_angle_pygame,
                             self.arc_end_angle_pygame,
                             self.thickness)

    # Prend directement l'angle calculé pour éviter recalcul
    def is_angle_in_gap(self, ball_angle_math):
        """ Vérifie si l'angle donné correspond à l'ouverture ACTUELLE du cercle """
        # Utilise la fonction globale avec les paramètres actuels du cercle
        return is_angle_in_gap(ball_angle_math, self.gap_center_rad, self.gap_width_rad)


# --- Logique Principale (CORRIGÉE) ---
def main():
    angle_start = random.uniform(0, 2*math.pi)
    ball = Ball(CENTER_X, CENTER_Y, BALL_RADIUS, RED, # Start at center
                INITIAL_BALL_SPEED * math.cos(angle_start),
                INITIAL_BALL_SPEED * math.sin(angle_start))

    circles = []
    for i in range(NUM_CIRCLES):
        radius = INITIAL_RADIUS + i * RADIUS_STEP
        direction = 1 if i % 2 == 0 else -1
        speed_modifier = 1 + (NUM_CIRCLES - 1 - i) * 0.1 # Légère variation
        rotation_speed = direction * BASE_ROTATION_SPEED_RAD_PER_SEC * speed_modifier
        circle = CircleWall(CENTER_X, CENTER_Y, radius, BLUE, CIRCLE_THICKNESS,
                            INITIAL_GAP_CENTER_ANGLE_RAD + i * math.pi / 8, # Décaler légèrement les gaps initiaux
                            GAP_ANGLE_RAD, rotation_speed)
        circles.append(circle)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.1: dt = 0.1 # Limiter le dt max pour éviter les sauts physiques

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        ball.update(dt)
        for circle in circles:
            circle.update(dt)

        if circles:
            current_circle = circles[0]

            dx = ball.x - current_circle.center_x
            dy = ball.y - current_circle.center_y
            dist_sq = dx*dx + dy*dy
            dist = math.sqrt(dist_sq)

            # --- Logique de Collision/Passage Révisée ---
            # Point de contact = quand la distance du centre de la balle est rayon_cercle - rayon_balle
            collision_dist = current_circle.radius - ball.radius

            # On vérifie si la balle a dépassé ce point de contact (vers l'extérieur)
            if dist >= collision_dist:
                # Calculer la normale (pointe du centre vers la balle)
                # Gérer le cas où dist est quasi nulle (balle au centre exact), rare mais possible
                if dist < 1e-6:
                    # Pas de direction définie, on ne fait rien ou on choisit une direction arbitraire
                    # Le plus simple est d'attendre qu'elle bouge un peu
                     pass # Éviter division par zéro
                else:
                    nx = dx / dist
                    ny = dy / dist

                    # Calculer l'angle de la balle (convention mathématique)
                    ball_angle_math = math.atan2(-dy, dx) # Y inversé pour Pygame -> Math

                    # Vérifier si cet angle est dans l'ouverture
                    in_gap = current_circle.is_angle_in_gap(ball_angle_math)

                    # Calculer la composante radiale de la vitesse (vitesse le long de la normale)
                    radial_speed = ball.vx * nx + ball.vy * ny

                    # --- Décision: Passer ou Rebondir ---
                    if in_gap:
                        # Si dans l'ouverture ET la balle s'éloigne du centre (ou est déjà dehors)
                        if radial_speed >= 0: # S'éloigne ou vitesse radiale nulle mais dehors
                            print(f"Balle passée par le gap du cercle {current_circle.radius:.0f}")
                            circles.pop(0)
                            # Important: Ne pas traiter d'autre collision/rebond pour cette balle cette frame
                            current_circle = None # Marquer que le cercle a été traité/supprimé
                        else:
                             # Dans le gap mais va vers l'intérieur? Théoriquement impossible si elle vient de l'intérieur.
                             # Si ça arrive (ex: dt trop grand), on pourrait la laisser passer ou la faire rebondir sur le "bord" du gap (complexe).
                             # Pour l'instant, traitons comme un rebond normal si elle n'est pas en train de sortir.
                             # print(f"Info: Dans le gap mais vitesse radiale négative ({radial_speed:.2f}). Rebond.")
                             ball.reflect_velocity(nx, ny)
                             # Correction de position
                             overlap = dist - collision_dist
                             ball.x -= overlap * nx
                             ball.y -= overlap * ny


                    else: # Pas dans l'ouverture -> Rebondir
                        # Rebondir seulement si la vitesse est sortante (radial_speed > 0)
                        # S'assurer qu'elle heurte bien le mur
                        if radial_speed > 0: # Va vers l'extérieur
                             #print(f"Rebond sur mur du cercle {current_circle.radius:.0f}") # Debug
                             ball.reflect_velocity(nx, ny)

                             # Correction de position : ramener exactement au point de contact
                             overlap = dist - collision_dist # Combien la balle a dépassé le point de contact
                             ball.x -= overlap * nx # Reculer le long de la normale
                             ball.y -= overlap * ny
                        # else: La balle est "derrière" le point de contact mais va vers l'intérieur,
                        #      elle n'a pas encore "heurté" le mur de ce côté. Laisser continuer.


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