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
INITIAL_BALL_SPEED = 75
NUM_CIRCLES = 16
INITIAL_RADIUS = 90
RADIUS_STEP = (SCREEN_HEIGHT // 2 - INITIAL_RADIUS - BALL_RADIUS * 3) / (NUM_CIRCLES -1) if NUM_CIRCLES > 1 else 0
CIRCLE_THICKNESS = 5
GAP_PERCENTAGE = 0.15
GAP_ANGLE_RAD = 2 * math.pi * GAP_PERCENTAGE
INITIAL_GAP_CENTER_ANGLE_RAD = 3 * math.pi / 2
BASE_ROTATION_SPEED_RAD_PER_SEC = math.pi / 4
FPS = 60
GRAVITY_ACCELERATION = 400.0 # Pixels par seconde^2 (Ajustez cette valeur !)
CIRCLE_SHRINK_SPEED = 30.0 # Vitesse de rétrécissement en pixels par seconde (Ajustez !)

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
        # Le rayon actuel et le rayon cible commencent identiques
        self.radius = float(radius)
        self.target_radius = float(radius) # Le rayon vers lequel on veut animer
        self.color = color
        self.thickness = thickness
        self.gap_width_rad = gap_width_rad
        self.rotation_speed = rotation_speed
        self.gap_center_rad = normalize_angle(initial_gap_center_rad)
        self.shrink_speed = CIRCLE_SHRINK_SPEED # Vitesse d'animation du rayon

        self.arc_start_angle_pygame = 0
        self.arc_end_angle_pygame = 0
        self._recalculate_draw_angles()

    def _recalculate_draw_angles(self):
        # ... (cette méthode reste identique) ...
        gap_start_rad = normalize_angle(self.gap_center_rad - self.gap_width_rad / 2)
        gap_end_rad = normalize_angle(self.gap_center_rad + self.gap_width_rad / 2)
        self.arc_start_angle_pygame = gap_end_rad
        self.arc_end_angle_pygame = gap_start_rad

    def update(self, dt):
        """ Met à jour l'angle ET anime le rayon vers la cible """
        # Mise à jour de la rotation du gap
        self.gap_center_rad += self.rotation_speed * dt
        self.gap_center_rad = normalize_angle(self.gap_center_rad)
        self._recalculate_draw_angles()

        # Animation du rayon vers la cible
        if abs(self.radius - self.target_radius) > 0.1: # Si pas déjà à la cible (avec une petite tolérance)
            change = self.shrink_speed * dt
            if self.radius > self.target_radius:
                self.radius -= change
                # Empêcher de dépasser la cible en rétrécissant
                if self.radius < self.target_radius:
                    self.radius = self.target_radius
            # elif self.radius < self.target_radius: # Gérer aussi l'agrandissement si nécessaire
            #     self.radius += change
            #     if self.radius > self.target_radius:
            #         self.radius = self.target_radius

    def draw(self, surface):
        """ Dessine l'arc de cercle avec le rayon actuel """
        # Utilise self.radius qui est animé dans update()
        current_radius_int = int(self.radius)
        if current_radius_int <= 0: return # Ne rien dessiner si le rayon est nul ou négatif

        rect = pygame.Rect(self.center_x - current_radius_int, self.center_y - current_radius_int,
                           2 * current_radius_int, 2 * current_radius_int)

        # Gérer le cas où le dessin d'arc échoue si start ~ end
        # Ou si le rayon est trop petit pour l'épaisseur
        if abs(self.arc_start_angle_pygame - self.arc_end_angle_pygame) < 0.01 or current_radius_int < self.thickness:
             # Dessiner un cercle complet si l'arc est invalide ou trop petit
              pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), current_radius_int, self.thickness)
        else:
             try:
                pygame.draw.arc(surface, self.color, rect,
                                self.arc_start_angle_pygame,
                                self.arc_end_angle_pygame,
                                self.thickness)
             except ValueError: # Peut arriver si le rect dégénère (rayon trop petit)
                 pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), current_radius_int, self.thickness)


    # is_angle_in_gap reste identique
    def is_angle_in_gap(self, ball_angle_math):
        return is_angle_in_gap(ball_angle_math, self.gap_center_rad, self.gap_width_rad)

    # Nouvelle méthode pour définir la cible du rayon
    def set_target_radius(self, new_target_radius):
        self.target_radius = float(new_target_radius)

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
        circle = CircleWall(CENTER_X, CENTER_Y, radius, WHITE, CIRCLE_THICKNESS,
                            INITIAL_GAP_CENTER_ANGLE_RAD + i * math.pi / 8, # Décaler légèrement les gaps initiaux
                            GAP_ANGLE_RAD, rotation_speed)
        circles.append(circle)

    running = True
    while running:
        # ... (Gestion temps, événements, update balle, update cercles [qui inclut anim rayon]) ...
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.1: dt = 0.1

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        ball.update(dt)
        for circle in circles:
            circle.update(dt) # Appelle la méthode update modifiée

        if circles:
            current_circle = circles[0]

            # --- Logique Collision/Passage ---
            # Utilise current_circle.radius (qui est en cours d'animation)
            collision_dist = current_circle.radius - ball.radius

            dx = ball.x - current_circle.center_x
            dy = ball.y - current_circle.center_y
            dist_sq = dx*dx + dy*dy
            dist = math.sqrt(dist_sq)

            if dist >= collision_dist:
                if dist > 1e-6:
                    nx = dx / dist
                    ny = dy / dist
                    ball_angle_math = math.atan2(-dy, dx)
                    in_gap = current_circle.is_angle_in_gap(ball_angle_math)
                    radial_speed = ball.vx * nx + ball.vy * ny

                    if in_gap:
                        if radial_speed >= 0:
                            print(f"Balle passée par le gap du cercle {current_circle.radius:.0f}")
                            circles.pop(0)
                            current_circle = None

                            # --- !!! MODIFICATION ICI : Définir le NOUVEAU target_radius !!! ---
                            if circles:
                                for i, circle_to_update in enumerate(circles):
                                    # Calculer le rayon cible pour la nouvelle position i
                                    target_radius = INITIAL_RADIUS + i * RADIUS_STEP
                                    # Définir la cible pour l'animation
                                    circle_to_update.set_target_radius(target_radius)
                                    # La méthode update de circle_to_update s'occupera de l'animation

                        else: # Dans le gap mais va vers l'intérieur
                            # ... (rebond) ...
                            if radial_speed > 0: # Correction: il faut aller vers l'extérieur pour rebondir
                                 ball.reflect_velocity(nx, ny)
                                 overlap = dist - collision_dist
                                 ball.x -= overlap * nx
                                 ball.y -= overlap * ny


                    else: # Pas dans l'ouverture -> Rebondir
                        if radial_speed > 0:
                            # ... (rebond) ...
                            ball.reflect_velocity(nx, ny)
                            overlap = dist - collision_dist
                            ball.x -= overlap * nx
                            ball.y -= overlap * ny

        # --- Dessin ---
        screen.fill(BLACK)
        for circle in circles:
            circle.draw(screen) # Utilise la méthode draw modifiée
        ball.draw(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()