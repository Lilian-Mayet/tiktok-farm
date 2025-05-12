import pygame
import math
import sys
import random

# --- Constantes ---
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 800
CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2.4
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)       # Player 1 color
BLUE = (50, 150, 255)     # Player 2 color
CIRCLE_COLOR = (200, 200, 200) # Circle wall color
OUTLINE_COLOR = (100, 100, 100)   # Ball outline color
PARTICLE_COLOR = (150, 150, 150) # Color for disappearance effect

BALL_RADIUS = 9
BALL_OUTLINE_WIDTH = 1
INITIAL_BALL_SPEED = 180
NUM_CIRCLES = 20
INITIAL_RADIUS = 90
#RADIUS_STEP = (SCREEN_HEIGHT // 2 - INITIAL_RADIUS - BALL_RADIUS * 5) / (NUM_CIRCLES -1) if NUM_CIRCLES > 1 else 0 # More space
RADIUS_STEP = 35
CIRCLE_THICKNESS = 5
GAP_PERCENTAGE = 0.15
GAP_ANGLE_RAD = 2 * math.pi * GAP_PERCENTAGE
INITIAL_GAP_CENTER_ANGLE_RAD = 3 * math.pi / 2
BASE_ROTATION_SPEED_RAD_PER_SEC = math.pi / 7 # Slightly slower rotation
CIRCLE_SHRINK_SPEED = 30.0 # Shrink speed
FPS = 60
GRAVITY_ACCELERATION = 350.0 # Slightly less gravity

# Particle Effect Constantes
NUM_PARTICLES_ON_BREAK = 50
PARTICLE_LIFETIME = 10 # seconds
PARTICLE_MAX_SPEED = 100

# --- Initialisation Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dual Ball Circle Break")
clock = pygame.time.Clock()
score_font = pygame.font.Font(None, 36) # Font for scores
# Pour des particules avec alpha variable (plus joli mais plus lent):

def normalize_angle(angle_rad):
    while angle_rad < 0: angle_rad += 2 * math.pi
    while angle_rad >= 2 * math.pi: angle_rad -= 2 * math.pi
    return angle_rad

def is_angle_in_gap(angle_rad, gap_center_rad, gap_width_rad):
    norm_angle = normalize_angle(angle_rad)
    gap_start = normalize_angle(gap_center_rad - gap_width_rad / 2)
    gap_end = normalize_angle(gap_center_rad + gap_width_rad / 2)
    if gap_start > gap_end: return norm_angle >= gap_start or norm_angle <= gap_end
    else: return gap_start <= norm_angle <= gap_end

def calculate_rotation_speed(index, total_initial_circles):
    """Calcule la vitesse de rotation basée sur l'index (0 = plus rapide)."""
    direction = 1 if index % 2 == 0 else -1
    # Modificateur: plus l'index est petit (proche du centre), plus c'est rapide
    # Utilise une base relative au nombre total de cercles pour la cohérence
    # L'ancien calcul était `1 + (NUM_CIRCLES - 1 - i) * factor`
    speed_modifier = 1.0 + (total_initial_circles - 1 - index) * 0.15 # Ajuster le facteur 0.15 si besoin
    speed_modifier = max(0.2, speed_modifier) # Vitesse minimale
    return direction * BASE_ROTATION_SPEED_RAD_PER_SEC * speed_modifier
# --- Classe Particle (Pour l'effet de disparition) ---
class Particle:
    def __init__(self, x, y, color):
        self.x = float(x)
        self.y = float(y)
        self.color = (random.randint(0,255),random.randint(0,255),random.randint(0,255))
        #self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(PARTICLE_MAX_SPEED * 0.5, PARTICLE_MAX_SPEED)
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.lifetime = PARTICLE_LIFETIME

        self.initial_size = random.randint(1, 5) 
        self.size = float(self.initial_size) # Stocker en float pour la précision

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Optional: Add gravity to particles too?
        self.vy += GRAVITY_ACCELERATION * 0.5 * dt # Less gravity for particles
        self.lifetime -= dt
        # Fade out (simple size reduction)
                # Calculer la taille proportionnellement au temps restant, basé sur la taille initiale
        if self.lifetime > 0 and PARTICLE_LIFETIME > 0:
            lerp_factor = max(0, self.lifetime / PARTICLE_LIFETIME) # 1.0 -> 0.0
            self.size = self.initial_size * lerp_factor
        else:
            self.size = 0 # Assurer la disparition


    def draw(self, surface):
        draw_size = int(self.size)
        if draw_size > 0:
             pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), draw_size, draw_size))


class Ball:
    def __init__(self, x, y, radius, color, outline_color, outline_width, name, initial_vx, initial_vy):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.color = color
        self.outline_color = outline_color
        self.outline_width = outline_width
        self.name = name
        self.vx = float(initial_vx)
        self.vy = float(initial_vy)
        self.score = 0

    def update(self, dt):
        self.vy += GRAVITY_ACCELERATION * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        pos = (int(self.x), int(self.y))
        # Draw outline first
        pygame.draw.circle(surface, self.outline_color, pos, self.radius + self.outline_width)
        # Draw main ball color
        pygame.draw.circle(surface, self.color, pos, self.radius)

    def reflect_velocity(self, nx, ny):
        dot_product = self.vx * nx + self.vy * ny
        if dot_product > 0: # Moving towards the outside normal
             reflect_vx = self.vx - 2 * dot_product * nx
             reflect_vy = self.vy - 2 * dot_product * ny
             self.vx = reflect_vx
             self.vy = reflect_vy

    def get_pos(self):
        return self.x, self.y

    def get_velocity(self):
         return self.vx, self.vy

    def add_score(self, points=1):
        self.score += points

# --- Classe CircleWall (Inchangée par rapport à l'animation) ---
class CircleWall:
    def __init__(self, center_x, center_y, radius, color, thickness,
                 initial_gap_center_rad, gap_width_rad, rotation_speed):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = float(radius)
        self.target_radius = float(radius)
        self.color = color
        self.thickness = thickness
        self.gap_width_rad = gap_width_rad
        self.rotation_speed = rotation_speed
        self.gap_center_rad = normalize_angle(initial_gap_center_rad)
        self.shrink_speed = CIRCLE_SHRINK_SPEED
        self.arc_start_angle_pygame = 0
        self.arc_end_angle_pygame = 0
        self._recalculate_draw_angles()

    def _recalculate_draw_angles(self):
        gap_start_rad = normalize_angle(self.gap_center_rad - self.gap_width_rad / 2)
        gap_end_rad = normalize_angle(self.gap_center_rad + self.gap_width_rad / 2)
        self.arc_start_angle_pygame = gap_end_rad
        self.arc_end_angle_pygame = gap_start_rad

    def update(self, dt):
        # Rotation
        self.gap_center_rad += self.rotation_speed * dt
        self.gap_center_rad = normalize_angle(self.gap_center_rad)
        self._recalculate_draw_angles()
        # Shrink animation
        if abs(self.radius - self.target_radius) > 0.1:
            change = self.shrink_speed * dt
            if self.radius > self.target_radius:
                self.radius -= change
                if self.radius < self.target_radius: self.radius = self.target_radius

    def draw(self, surface):
        current_radius_int = int(self.radius)
        if current_radius_int <= 0: return
        rect = pygame.Rect(self.center_x - current_radius_int, self.center_y - current_radius_int,
                           2 * current_radius_int, 2 * current_radius_int)
        if abs(self.arc_start_angle_pygame - self.arc_end_angle_pygame) < 0.01 or current_radius_int < self.thickness:
             pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), current_radius_int, self.thickness)
        else:
             try:
                pygame.draw.arc(surface, self.color, rect,
                                self.arc_start_angle_pygame,
                                self.arc_end_angle_pygame,
                                self.thickness)
             except ValueError:
                 pygame.draw.circle(surface, self.color, (self.center_x, self.center_y), current_radius_int, self.thickness)

    def is_angle_in_gap(self, ball_angle_math):
        return is_angle_in_gap(ball_angle_math, self.gap_center_rad, self.gap_width_rad)

    def set_target_radius(self, new_target_radius):
        self.target_radius = float(new_target_radius)

    # Helper to get properties for effects
    def get_position_at_angle(self, angle_rad):
        x = self.center_x + self.radius * math.cos(angle_rad)
        y = self.center_y - self.radius * math.sin(angle_rad) # Pygame Y inversion
        return x, y

# --- Logique Principale (Modifiée pour 2 balles, score, effets) ---
def main():
    # --- Création des objets ---
    balls = []
    # Balle 1 (Rouge)
    angle_start1 = random.uniform(math.pi / 4, 3 * math.pi / 4) # Start upwards-left
    ball1 = Ball(CENTER_X - 10, CENTER_Y, BALL_RADIUS, RED, OUTLINE_COLOR, BALL_OUTLINE_WIDTH, "Player 1",
                 INITIAL_BALL_SPEED * math.cos(angle_start1),
                 INITIAL_BALL_SPEED * math.sin(angle_start1))
    balls.append(ball1)

    # Balle 2 (Bleue)
    angle_start2 = random.uniform(5 * math.pi / 4, 7 * math.pi / 4) # Start downwards-right
    ball2 = Ball(CENTER_X + 10, CENTER_Y, BALL_RADIUS, BLUE, OUTLINE_COLOR, BALL_OUTLINE_WIDTH, "Player 2",
                 INITIAL_BALL_SPEED * math.cos(angle_start2),
                 INITIAL_BALL_SPEED * math.sin(angle_start2))
    balls.append(ball2)

    circles = []
    total_initial_circles = NUM_CIRCLES # Stocker le nombre initial

    for i in range(total_initial_circles):
        radius = INITIAL_RADIUS + i * RADIUS_STEP
        # --- MODIFICATION ---
        # Utiliser la nouvelle fonction pour calculer la vitesse initiale
        rotation_speed = calculate_rotation_speed(i, total_initial_circles)
        # --- FIN MODIFICATION ---
        initial_gap = INITIAL_GAP_CENTER_ANGLE_RAD + i * math.pi / (total_initial_circles / 1.5) # Stagger un peu plus
        circle = CircleWall(CENTER_X, CENTER_Y, radius, CIRCLE_COLOR, CIRCLE_THICKNESS,
                            initial_gap, GAP_ANGLE_RAD, rotation_speed)
        circles.append(circle)

    particles = [] # Liste pour gérer les particules actives

    # --- Boucle de jeu ---
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt > 0.1: dt = 0.1 # Limiter dt

        # --- Gestion des événements ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: running = False

        # --- Mises à jour ---
        for ball in balls:
            ball.update(dt)
        for circle in circles:
            circle.update(dt) # Rotation et animation du rayon
        # Update particles
        for particle in particles[:]: # Iterate over a copy for safe removal
             particle.update(dt)
             if particle.lifetime <= 0:
                 particles.remove(particle)


        # --- Détection des collisions et logique ---
        circle_broken_this_frame = False
        if circles:
            current_circle = circles[0]
            next_target_radius_map = {} # Pour stocker les nouvelles cibles si le cercle casse

            for ball in balls:
                # Vérifier la collision de CETTE balle avec le current_circle
                collision_dist = current_circle.radius - ball.radius
                dx = ball.x - current_circle.center_x
                dy = ball.y - current_circle.center_y
                dist_sq = dx*dx + dy*dy

                # Optimization: check square distance first
                if dist_sq >= collision_dist * collision_dist - 10 : # Check a bit before exact collision
                    dist = math.sqrt(dist_sq)

                    if dist >= collision_dist and dist > 1e-6:
                        nx = dx / dist
                        ny = dy / dist
                        ball_angle_math = math.atan2(-dy, dx)
                        in_gap = current_circle.is_angle_in_gap(ball_angle_math)
                        radial_speed = ball.vx * nx + ball.vy * ny

                        # Décision: Passer ou Rebondir pour CETTE balle
                        if in_gap:
                            if radial_speed >= 0: # Sort par le gap
                                if not circle_broken_this_frame: # Le cercle n'a pas déjà été cassé CETTE FRAME
                                    print(f"{ball.name} passed through circle {current_circle.radius:.0f}")
                                    ball.add_score(1)

                                    # Créer l'effet de particules
                                    broken_circle_radius = current_circle.radius
                                    broken_circle_center_x = current_circle.center_x
                                    broken_circle_center_y = current_circle.center_y
                                    for _ in range(NUM_PARTICLES_ON_BREAK):
                                        # Start particles on the circle's edge
                                        p_angle = random.uniform(0, 2*math.pi)
                                        px = broken_circle_center_x + broken_circle_radius * math.cos(p_angle)
                                        py = broken_circle_center_y - broken_circle_radius * math.sin(p_angle) # Y down
                                        particles.append(Particle(px, py, PARTICLE_COLOR))


                                    circles.pop(0)
                                    circle_broken_this_frame = True # Marquer comme cassé

                                    # Préparer l'ajustement des rayons pour PLUS TARD (après la boucle des balles)
                                    if circles:
                                        next_updates = {}
                                        for i, circle_to_update in enumerate(circles):
                                            target_radius = INITIAL_RADIUS + i * RADIUS_STEP
                                            # Calculer la NOUVELLE vitesse basée sur le nouvel index 'i'
                                            new_rotation_speed = calculate_rotation_speed(i, total_initial_circles)
                                            # Stocker les deux mises à jour
                                            next_updates[circle_to_update] = {'radius': target_radius, 'speed': new_rotation_speed}

                                # Important: même si le cercle est cassé, la balle continue sa trajectoire
                                # sans rebondir pour cette frame si elle est dans le gap et sortante.

                            else: # Dans le gap mais va vers l'intérieur (cas rare, rebondir ?)
                                # Pour simplifier, on pourrait juste ne rien faire ici,
                                # ou forcer un rebond sur le 'bord' du gap (complexe).
                                # On choisit le rebond normal pour l'instant si radial_speed est négatif.
                                ball.reflect_velocity(nx, ny)
                                overlap = dist - collision_dist
                                ball.x -= overlap * nx
                                ball.y -= overlap * ny


                        else: # Pas dans l'ouverture -> Rebondir
                            if radial_speed > 0: # Va vers l'extérieur, heurte le mur
                                ball.reflect_velocity(nx, ny)
                                # Correction de position
                                overlap = dist - collision_dist
                                ball.x -= overlap * nx
                                ball.y -= overlap * ny

            # Fin de la boucle sur les balles. Si un cercle a été cassé, appliquer les target_radius.
            if circle_broken_this_frame:
                 # Appliquer les mises à jour stockées
                 for circle, updates in next_updates.items():
                     circle.set_target_radius(updates['radius'])
                     # Définir directement la nouvelle vitesse de rotation
                     circle.rotation_speed = updates['speed']

        

        # --- Dessin ---
        screen.fill(BLACK)

        # Dessiner les cercles
        for circle in circles:
            circle.draw(screen)

        # Dessiner les particules
        for particle in particles:
            particle.draw(screen)

        # Dessiner les balles
        for ball in balls:
            ball.draw(screen)

        # Dessiner les scores
        # Player 1 (Gauche)
        score_surf_p1 = score_font.render(f"{balls[0].name}: {balls[0].score}", True, WHITE)
        score_rect_p1 = score_surf_p1.get_rect(topleft=(15, 10))
        screen.blit(score_surf_p1, score_rect_p1)

        # Player 2 (Droite)
        score_surf_p2 = score_font.render(f"{balls[1].name}: {balls[1].score}", True, WHITE)
        score_rect_p2 = score_surf_p2.get_rect(topright=(SCREEN_WIDTH - 15, 10))
        screen.blit(score_surf_p2, score_rect_p2)


        pygame.display.flip() # Mettre à jour l'affichage

    # --- Fin ---
    pygame.quit()
    sys.exit()

# --- Point d'entrée ---
if __name__ == '__main__':
    main()