import pygame
import math
import sys
import random
import pygame.midi 
import mido  # <-- ADD THIS

# --- Constantes ---
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 800
CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2.8
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)       # Player 1 color
BLUE = (50, 150, 255)     # Player 2 color
CIRCLE_COLOR = (255, 255, 255) # Circle wall color
OUTLINE_COLOR = (100, 100, 100)   # Ball outline color
PARTICLE_COLOR = (150, 150, 150) # Color for disappearance effect

# --- TITLE CONSTANTS ---
TITLE_TEXT = "Who will win?"
TITLE_FONT_SIZE = 48
TITLE_COLOR = WHITE
TITLE_TOP_MARGIN = 15
# --- END TITLE CONSTANTS ---

# --- SCORE PARTICLE CONSTANTS ---
NUM_SCORE_PARTICLES = 15
SCORE_PARTICLE_LIFETIME = 0.4 # Shorter lifetime
SCORE_PARTICLE_MAX_SPEED = 80
SCORE_PARTICLE_COLOR = WHITE
# --- END SCORE PARTICLE CONSTANTS ---


# --- BANNER CONSTANTS ---
BANNER_HEIGHT = 135  # INCREASED HEIGHT to fit name and score
BANNER_ALPHA = 185   # Transparency (0=invisible, 255=opaque)
BANNER_BG_COLOR = (30, 30, 30)
BANNER_PADDING = 20 # Slightly more padding maybe
BANNER_NAME_COLOR_P1 = RED
BANNER_NAME_COLOR_P2 = BLUE
BANNER_SCORE_COLOR = WHITE # Color for the score number
BANNER_NAME_FONT_SIZE = 35
BANNER_SCORE_FONT_SIZE = 50
BANNER_VERTICAL_SPACING = 2 # Small space between name and score
# --- END BANNER CONSTANTS ---
# --- MIDI Constants ---
MIDI_DEVICE_ID = None # Keep device selection as before
MIDI_INSTRUMENT = 0   # Still useful to set initially
MIDI_FILENAME = "midiFiles/MarioBros.mid" # <-- ADD THIS - Change if your file has a different name
MIDI_VELOCITY_FALLBACK = 100 # Velocity to use if MIDI file velocity is weird (optional)
MIDI_PLAYBACK_VELOCITY = 160

BALL_RADIUS = 9
BALL_OUTLINE_WIDTH = 1
INITIAL_BALL_SPEED = 180
NUM_CIRCLES = 430
INITIAL_RADIUS = 90
#RADIUS_STEP = (SCREEN_HEIGHT // 2 - INITIAL_RADIUS - BALL_RADIUS * 5) / (NUM_CIRCLES -1) if NUM_CIRCLES > 1 else 0 # More space
RADIUS_STEP = 35
CIRCLE_THICKNESS = 7
GAP_PERCENTAGE = 0.15
GAP_ANGLE_RAD = 2 * math.pi * GAP_PERCENTAGE
INITIAL_GAP_CENTER_ANGLE_RAD = 3 * math.pi / 2
BASE_ROTATION_SPEED_RAD_PER_SEC = math.pi / 2 # Slightly slower rotation
ROTATION_SLOWDOWN_FACTOR = 0.92
CIRCLE_SHRINK_SPEED = 45.0 # Shrink speed
FPS = 60
GRAVITY_ACCELERATION = 350.0 # Slightly less gravity


# Particle Effect Constantes
NUM_PARTICLES_ON_BREAK = 120
PARTICLE_LIFETIME = 1 # seconds
PARTICLE_MAX_SPEED = 100

# --- Initialisation Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dual Ball Circle Break")
clock = pygame.time.Clock()
score_font = pygame.font.Font(None, 36) # Font for scores

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
    if gap_start > gap_end: return norm_angle >= gap_start or norm_angle <= gap_end
    else: return gap_start <= norm_angle <= gap_end

def calculate_rotation_speed_magnitude(index):
    """
    Calcule la MAGNITUDE de la vitesse de rotation.
    Index 0 a la magnitude BASE_ROTATION_SPEED_RAD_PER_SEC.
    Chaque cercle suivant (index > 0) est plus lent d'un facteur ROTATION_SLOWDOWN_FACTOR.
    """
    # Calculer la magnitude de la vitesse
    # Pour index 0: factor ^ 0 = 1 -> speed = base_speed
    # Pour index 1: factor ^ 1 = factor -> speed = base_speed * factor
    # etc.
    if ROTATION_SLOWDOWN_FACTOR >= 1.0 and index > 0:
         print(f"Warning: ROTATION_SLOWDOWN_FACTOR ({ROTATION_SLOWDOWN_FACTOR}) >= 1.0, speed magnitude will not decrease for index {index}.")

    speed_magnitude = BASE_ROTATION_SPEED_RAD_PER_SEC * (ROTATION_SLOWDOWN_FACTOR ** index)

    # Retourner uniquement la magnitude (toujours positive)
    return speed_magnitude

# --- MIDI File Loading Function ---
def load_midi_notes(filename):
    """Loads Note On events from a MIDI file into a list."""
    note_sequence = []
    try:
        mid = mido.MidiFile(filename)
        print(f"Loading MIDI file: {filename}")
        time_since_last = 0
        for i, track in enumerate(mid.tracks):
            print(f"--- Track {i}: {track.name}")
            # Reset time for each track if needed, but absolute time might be better if combining
            # For sequential notes regardless of timing, just iterate messages
            for msg in track:
                # We only care about note_on events with positive velocity
                if msg.type == 'note_on' and msg.velocity > 0:
                    note_sequence.append({
                        'note': msg.note,
                        'velocity': msg.velocity,
                        # 'time': msg.time # Original delta time, we ignore this for sequential playback
                    })
        print(f"Loaded {len(note_sequence)} note events.")

        return note_sequence
    except FileNotFoundError:
        print(f"Error: MIDI file not found at '{filename}'")
        return []
    except Exception as e:
        print(f"Error loading MIDI file '{filename}': {e}")
        return []

# --- Classe Particle (Pour l'effet de disparition) ---
class Particle:
    def __init__(self, x, y,has_gravity, random_color, color, lifetime=PARTICLE_LIFETIME, max_speed=PARTICLE_MAX_SPEED): # Add params
        self.x = float(x)
        self.y = float(y)
        # Allow specific color or random if original color passed
        if random_color: # Check if it's the default break color
             self.color = (random.randint(100,200), random.randint(100,200), random.randint(100,200)) # Varying grays
        else:
             self.color = color # Use specified color (e.g., WHITE for score)

        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(max_speed * 0.2, max_speed) # Use max_speed param
        self.vx = speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.lifetime = lifetime # Use lifetime param
        self.base_lifetime = lifetime # Store base for calculation
        self.has_gravity = has_gravity

        self.initial_size = random.randint(2, 4)
        self.size = float(self.initial_size)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.has_gravity :
            self.vy += GRAVITY_ACCELERATION * 0.5 * dt
        
        self.lifetime -= dt

        if self.lifetime > 0 and self.base_lifetime > 0:
            lerp_factor = max(0, self.lifetime / self.base_lifetime)
            self.size = self.initial_size * lerp_factor
        else:
            self.size = 0

    def draw(self, surface):
        draw_size = int(self.size)
        if draw_size > 0:
             # Use a circle for score particles maybe? Looks softer.
             if self.color == SCORE_PARTICLE_COLOR:
                 pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), draw_size // 2 + 1)
             else: # Rect for break particles
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
        initial_speed_sq = self.vx**2 + self.vy**2
        initial_ke = 0.5 * initial_speed_sq
        self.just_scored = False
        # Énergie Potentielle Initiale (PE = m * g * h, on prend m=1, h = -y par rapport au haut de l'écran)
        # Utiliser g = GRAVITY_ACCELERATION. PE est négative car Y augmente vers le bas.
        initial_pe = -GRAVITY_ACCELERATION * self.y
        # Énergie Totale (constante que l'on veut maintenir)
        self.total_energy = initial_ke + initial_pe
        self.score = 0

    def update(self, dt):
            # --- MODIFICATION : Méthode update complète avec conservation d'énergie ---

            # 1. Appliquer l'accélération gravitationnelle (style Euler simple)
            self.vy += GRAVITY_ACCELERATION * dt

            # 2. Mettre à jour la position basée sur la vitesse actuelle (potentiellement incorrecte énergétiquement)
            self.x += self.vx * dt
            self.y += self.vy * dt

            # 3. Calculer l'énergie potentielle ACTUELLE basée sur la NOUVELLE position y
            current_pe = -GRAVITY_ACCELERATION * self.y

            # 4. Calculer l'énergie cinétique REQUISE pour conserver l'énergie totale
            required_ke = self.total_energy - current_pe

            # S'assurer que l'énergie cinétique requise n'est pas négative (ça peut arriver par erreur numérique)
            if required_ke < 0:
                required_ke = 0 # La balle ne peut pas aller plus haut que son énergie totale le permet

            # 5. Calculer la vitesse (magnitude) requise à partir de KE = 0.5 * speed^2
            # required_speed^2 = 2 * required_ke
            required_speed_sq = 2 * required_ke
            required_speed = math.sqrt(required_speed_sq)

            # 6. Obtenir la vitesse actuelle (après l'étape 1 & 2)
            current_speed_sq = self.vx**2 + self.vy**2

            # 7. Mettre à l'échelle le vecteur vitesse actuel pour correspondre à la vitesse requise
            if current_speed_sq > 1e-9: # Éviter la division par zéro si la vitesse est nulle
                current_speed = math.sqrt(current_speed_sq)
                # Calculer le facteur de mise à l'échelle
                scale_factor = required_speed / current_speed
                # Appliquer l'échelle au vecteur vitesse
                self.vx *= scale_factor
                self.vy *= scale_factor
            elif required_speed > 1e-6:
                # Cas étrange: la vitesse actuelle est nulle, mais elle devrait être > 0.
                # On n'a pas de direction ! On ne peut pas faire grand-chose.
                # Peut-être lui donner une petite vitesse verticale basée sur required_speed ?
                # Pour la simplicité, on la laisse à zéro pour l'instant.
                self.vx = 0.0
                # self.vy = -required_speed # Lui donner une vitesse vers le haut ? Ou 0 ?
                self.vy = 0.0 # Plus sûr pour l'instant
                # print(f"Warning: Ball {self.name} speed became zero but required speed is {required_speed}")

    def draw(self, surface):
        pos = (int(self.x), int(self.y))
        # Draw outline first
        pygame.draw.circle(surface, self.outline_color, pos, self.radius + self.outline_width)
        # Draw main ball color
        pygame.draw.circle(surface, self.color, pos, self.radius)

    def reflect_velocity(self, nx, ny):
            # --- MODIFICATION : Simplifier maintenant que update() gère l'énergie ---
            """ Réfléchit la vélocité par rapport à la normale (nx, ny).
                L'énergie est conservée par la méthode update(). """

            dot_product = self.vx * nx + self.vy * ny

            if dot_product > 0: # Va vers l'extérieur/mur
                # Formule de réflexion standard, SANS re-scaling ici.
                # La méthode update() s'assurera que la magnitude finale est correcte.
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
        self.just_scored = True

# --- Classe CircleWall (Inchangée par rapport à l'animation) ---
class CircleWall:
    def __init__(self, center_x, center_y, radius, color, thickness,
                 initial_gap_center_rad, gap_width_rad,initial_index, total_initial_circles):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = float(radius)
        self.target_radius = float(radius)
        self.color = color
        self.thickness = thickness
        self.gap_width_rad = gap_width_rad
        self.rotation_direction = 1 if initial_index % 2 == 0 else -1
        initial_speed_magnitude = calculate_rotation_speed_magnitude(initial_index) # Utiliser la nouvelle fonction (voir étape 2)
        self.rotation_speed = self.rotation_direction * initial_speed_magnitude
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
        if current_radius_int>500:
            return #don't draw too large circle for performance
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




# --- MIDI Setup (pygame.midi part remains mostly the same) ---
pygame.midi.init()
# ... (Code to list devices, select MIDI_DEVICE_ID, open midi_output) ...
# ... (Make sure midi_output is None if opening fails) ...
print(pygame.midi.get_default_output_id())
print( pygame.midi.get_device_info(0))
midi_output = pygame.midi.Output(0)
if midi_output:
     midi_output.set_instrument(MIDI_INSTRUMENT, channel=0)

# --- Logique Principale (Modifiée pour 2 balles, score, effets) ---
def main():
    # --- Load MIDI Notes Sequence ---
    loaded_notes = load_midi_notes(MIDI_FILENAME)
    current_note_index = 1 # Index for the next note to play from the loaded sequence
    # --- Create Banner Surface ---
    banner_surface = pygame.Surface((SCREEN_WIDTH, BANNER_HEIGHT), pygame.SRCALPHA)
    TRANSPARENT_BANNER_BG = (*BANNER_BG_COLOR, BANNER_ALPHA)
     # --- Create Banner Fonts ---
    banner_name_font = pygame.font.Font(None, BANNER_NAME_FONT_SIZE)
    banner_score_font = pygame.font.Font(None, BANNER_SCORE_FONT_SIZE)

    # --- ADD TITLE FONT ---
    title_font = pygame.font.Font(None, TITLE_FONT_SIZE)
    # --- END TITLE FONT ---

    # --- Render Title (Do this once) ---
    title_surf = title_font.render(TITLE_TEXT, True, TITLE_COLOR)
    title_rect = title_surf.get_rect(centerx=SCREEN_WIDTH // 2, top=TITLE_TOP_MARGIN)


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

        # --- FIN MODIFICATION ---
        initial_gap = INITIAL_GAP_CENTER_ANGLE_RAD + i * math.pi / (total_initial_circles / 1.5) # Stagger un peu plus
        # Le constructeur CircleWall calcule maintenant la direction et la vitesse initiale
        circle = CircleWall(CENTER_X, CENTER_Y, radius, CIRCLE_COLOR, CIRCLE_THICKNESS,
                            initial_gap, GAP_ANGLE_RAD,
                            i, total_initial_circles)
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
                collision_dist = (current_circle.radius - CIRCLE_THICKNESS/2) - ball.radius
                dx = ball.x - current_circle.center_x
                dy = ball.y - current_circle.center_y
                dist_sq = dx*dx + dy*dy

                # Optimization: check square distance first
                if dist_sq >= collision_dist * collision_dist - 0.1 : # Check a bit before exact collision
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
                                        particles.append(Particle(px, py,has_gravity=True,random_color=True, color  = None))


                                    circles.pop(0)
                                    circle_broken_this_frame = True # Marquer comme cassé

                                    # Préparer l'ajustement des rayons pour PLUS TARD (après la boucle des balles)
                                    if circles:
                                        next_updates = {}
                                        for i, circle_to_update in enumerate(circles):
                                            target_radius = INITIAL_RADIUS + i * RADIUS_STEP

                                            # Calculer la NOUVELLE magnitude basée sur le nouvel index 'i'
                                            new_speed_magnitude = calculate_rotation_speed_magnitude(i)
                                            # Utiliser la direction STOCKÉE dans le cercle
                                            new_full_speed = circle_to_update.rotation_direction * new_speed_magnitude
                                            # Stocker les deux mises à jour
                                            next_updates[circle_to_update] = {'radius': target_radius, 'speed': new_full_speed}

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
                                # --- !!! MIDI NOTE PLAYBACK (FROM FILE SEQUENCE) !!! ---
                                if midi_output and current_note_index < len(loaded_notes):
                                    try:
                                        # Get the next note event from the loaded list
                                        note_event = loaded_notes[current_note_index]
                                        note_to_play = note_event['note']

                                        # --- MODIFICATION ---
                                        # ALWAYS use the fixed, constant velocity,
                                        # IGNORING the velocity stored in note_event['velocity'].
                                        velocity_to_play = MIDI_PLAYBACK_VELOCITY
                                        # --- END MODIFICATION ---

                                        # Clamp just in case, to ensure it's valid (1-127)
                                        velocity_to_play = max(1, min(127, velocity_to_play))
                    
                                        # Updated print statement to reflect fixed velocity is used
                                        print(f"Playing Note {current_note_index+1}/{len(loaded_notes)} from MIDI file: Note={note_to_play}, FIXED Vel={velocity_to_play}")
                                        
                                        # Send Note On using the FIXED velocity
                                        midi_output.note_on(note_to_play, velocity_to_play, channel=0)
                                        midi_output.note_off(note_to_play, 0, channel=0) # Immediate note off

                                        # Move to the next note in the sequence
                                        current_note_index += 1

                                    except Exception as e:
                                            print(f"Error playing MIDI note: {e}")
                                elif midi_output and current_note_index >= len(loaded_notes):
                                    print("End of MIDI file notes reached.")
                                # --- !!! END MIDI NOTE PLAYBACK !!! ---    

            # Fin de la boucle sur les balles. Si un cercle a été cassé, appliquer les target_radius.
            if circle_broken_this_frame:
                 # Appliquer les mises à jour stockées
                 for circle, updates in next_updates.items():
                     circle.set_target_radius(updates['radius'])
                     # Définir directement la nouvelle vitesse de rotation
                     circle.rotation_speed = updates['speed']

        

        # --- Dessin ---
        screen.fill(BLACK)
        # --- Draw Title ---
        screen.blit(title_surf, title_rect)
        # --- End Draw Title ---

        # Dessiner les cercles
        for circle in circles:
            circle.draw(screen)

        # Dessiner les particules
        for particle in particles:
            particle.draw(screen)

        # Dessiner les balles
        for ball in balls:
            ball.draw(screen)

       # --- Préparer et Dessiner le Bandeau ---
        # 1. Fill banner background (will be made transparent later)
        banner_surface.fill(TRANSPARENT_BANNER_BG)


        # --- Player 1 Display (Left) ---
        # Render Name
        p1_name_text = balls[0].name
        p1_name_surf = banner_name_font.render(p1_name_text, True, BANNER_NAME_COLOR_P1)
        p1_name_rect = p1_name_surf.get_rect(topleft=(BANNER_PADDING, BANNER_PADDING // 2)) # Position name near top-left
        banner_surface.blit(p1_name_surf, p1_name_rect)

        # Render Score (Below Name)
        p1_score_text = str(balls[0].score)
        p1_score_surf = banner_score_font.render(p1_score_text, True, BANNER_SCORE_COLOR)
        # Position score's top-left below name's bottom-left
        p1_score_rect = p1_score_surf.get_rect(topleft=(p1_name_rect.left, p1_name_rect.bottom + BANNER_VERTICAL_SPACING))
        banner_surface.blit(p1_score_surf, p1_score_rect)

        # --- Player 2 Display (Right) ---
        # Render Name
        p2_name_text = balls[1].name
        p2_name_surf = banner_name_font.render(p2_name_text, True, BANNER_NAME_COLOR_P2)
        p2_name_rect = p2_name_surf.get_rect(topright=(SCREEN_WIDTH - BANNER_PADDING, BANNER_PADDING // 2)) # Position name near top-right
        banner_surface.blit(p2_name_surf, p2_name_rect)

        # Render Score (Below Name)
        p2_score_text = str(balls[1].score)
        p2_score_surf = banner_score_font.render(p2_score_text, True, BANNER_SCORE_COLOR)
        # Position score's top-right below name's bottom-right
        p2_score_rect = p2_score_surf.get_rect(topright=(p2_name_rect.right, p2_name_rect.bottom + BANNER_VERTICAL_SPACING))
        banner_surface.blit(p2_score_surf, p2_score_rect)

        # --- !! SCORE PARTICLE TRIGGER !! ---
        # Check AFTER drawing the banner and calculating score rects
        banner_y_offset = SCREEN_HEIGHT - BANNER_HEIGHT

        # Player 1 Score Particles
        if balls[0].just_scored:
            # Spawn particles around the center of the score text
            center_x = p1_score_rect.centerx
            center_y = banner_y_offset + p1_score_rect.centery # Add banner offset
            for _ in range(NUM_SCORE_PARTICLES):
                 # Use specific score particle properties
                 particles.append(Particle(center_x, center_y,  has_gravity=False,random_color=False, color = SCORE_PARTICLE_COLOR))
            balls[0].just_scored = False # Reset flag

        # Player 2 Score Particles
        if balls[1].just_scored:
            center_x = p2_score_rect.centerx
            center_y = banner_y_offset + p2_score_rect.centery # Add banner offset
            for _ in range(NUM_SCORE_PARTICLES):
                 particles.append(Particle(center_x, center_y, has_gravity=False,random_color=False, color = SCORE_PARTICLE_COLOR))
            balls[1].just_scored = False # Reset flag
        # --- !! END SCORE PARTICLE TRIGGER !! ---
        # --- Blit the transparent banner onto the main screen ---
        screen.blit(banner_surface, (0, SCREEN_HEIGHT - BANNER_HEIGHT))
        # --- Fin Dessin Bandeau ---

        # --- Make sure old score drawing is removed ---

        pygame.display.flip()

    # --- Fin ---
    pygame.quit()
    sys.exit()

# --- Point d'entrée ---
if __name__ == '__main__':
    main()