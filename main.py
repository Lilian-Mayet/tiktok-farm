import pygame
import math
import sys
import random
import pygame.midi 
import mido  # <-- ADD THIS
import math


# --- Constantes ---
SCREEN_HEIGHT = 800
SCREEN_WIDTH = int(SCREEN_HEIGHT* (9/16))

# NOUVEAU CENTRE DE JEU (plus bas)
GAME_CENTER_Y_OFFSET = 0 # Combien descendre le centre du jeu
CENTER_X, CENTER_Y = SCREEN_WIDTH // 2, (SCREEN_HEIGHT // 2.5) + GAME_CENTER_Y_OFFSET # Ajusté
WHITE = (255, 255, 255)
GREEN = (0,255,0)
BLACK = (0, 0, 0)
RED = (255, 50, 50)       # Player 1 color
BLUE = (50, 150, 255)     # Player 2 color
CIRCLE_COLOR = (255, 255, 255) # Circle wall color
OUTLINE_COLOR = (100, 100, 100)   # Ball outline color
PARTICLE_COLOR = (220, 220, 220) # Color for disappearance effect

# --- TEXT UI CONSTANTS (Replaces Banner & Title) ---
UI_TOP_MARGIN = 30         # Marge du haut pour les éléments UI
UI_SIDE_PADDING = 15       # Marge latérale pour les éléments UI
UI_ELEMENT_SPACING = 15    # Espace vertical entre les éléments (titre, scores)

# Style pour les "bulles" de texte
TEXT_BOX_BG_COLOR = WHITE
TEXT_BOX_ALPHA = 230       # Légère transparence pour le fond de la bulle
TEXT_BOX_PADDING = 8       # Padding intérieur de la bulle de texte
TEXT_BOX_BORDER_RADIUS = 12 # Rayon des coins arrondis

# Fonts (utiliser les mêmes MAIN_FONT_PATH, BOLD_FONT_PATH)
TITLE_TEXT_CONTENT = "MARIO or LUIGI?" # Renommé pour clarté
TITLE_TEXT_FONT_SIZE = 38    # Ajusté
TITLE_TEXT_COLOR = BLACK     # Texte noir sur fond blanc
TITLE_OUTLINE_SIZE = 0       # On n'utilise plus l'outline direct sur le texte

PLAYER_NAME_FONT_SIZE = 32
PLAYER_NAME_COLOR_P1 = RED
PLAYER_NAME_COLOR_P2 = GREEN
PLAYER_SCORE_FONT_SIZE = 45
PLAYER_SCORE_COLOR = (30, 30, 30) # Gris foncé pour le score

# --- END TEXT UI CONSTANTS ---
# --- TEXT STYLING ---
MAIN_FONT_PATH = "font/TikTokDisplay-Bold.ttf" # Mettez le chemin vers votre police .ttf ici
BOLD_FONT_PATH = "font/TikTokText-Bold.ttf"# Mettez le chemin vers une police grasse .ttf ici
# --- END TEXT STYLING ---



# --- SCORE PARTICLE CONSTANTS ---
NUM_SCORE_PARTICLES = 15
SCORE_PARTICLE_LIFETIME = 0.4 # Shorter lifetime
SCORE_PARTICLE_MAX_SPEED = 80
SCORE_PARTICLE_COLOR = WHITE
# --- END SCORE PARTICLE CONSTANTS ---

# --- BALL ENHANCEMENT CONSTANTS ---
BALL_IMAGE_P1 = "img/mario.png" # Mettez le bon nom/chemin
BALL_IMAGE_P2 = "img/luigi.png"
BALL_TRAIL_LENGTH = 8  # Number of past positions to draw for the trail
BALL_TRAIL_START_ALPHA = 120 # Starting transparency for the trail
# --- END BALL ENHANCEMENT ---

# --- BANNER CONSTANTS ---
BANNER_HEIGHT = 135  # INCREASED HEIGHT to fit name and score
BANNER_ALPHA = 185   # Transparency (0=invisible, 255=opaque)
BANNER_BG_COLOR = (30, 30, 30)
BANNER_PADDING = 20 # Slightly more padding maybe
BANNER_NAME_COLOR_P1 = RED
BANNER_NAME_COLOR_P2 = GREEN
BANNER_SCORE_COLOR = WHITE # Color for the score number
BANNER_NAME_FONT_SIZE = 35
BANNER_SCORE_FONT_SIZE = 65
BANNER_VERTICAL_SPACING = 2 # Small space between name and score
# --- END BANNER CONSTANTS ---




# --- MIDI Constants ---
MIDI_DEVICE_ID = None # Keep device selection as before
MIDI_INSTRUMENT = 0   # Still useful to set initially
MIDI_FILENAME = "midiFiles/MarioBros.mid" # <-- ADD THIS - Change if your file has a different name
MIDI_VELOCITY_FALLBACK = 100 # Velocity to use if MIDI file velocity is weird (optional)
MIDI_PLAYBACK_VELOCITY = 255

BALL_RADIUS = 20
BALL_OUTLINE_WIDTH = 2
INITIAL_BALL_SPEED = 160
NUM_CIRCLES = 39
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
FPS = 120
GRAVITY_ACCELERATION = 350.0 # Slightly less gravity


# Particle Effect Constantes
NUM_PARTICLES_ON_BREAK = 120
PARTICLE_LIFETIME = 1 # seconds
PARTICLE_MAX_SPEED = 100

# --- Initialisation Pygame ---
pygame.init()
pygame.mixer.init() 
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


def draw_rounded_rect(surface, rect, color, corner_radius):
    """
    Dessine un rectangle avec des coins arrondis.
    Assumes rect is a pygame.Rect.
    Color est un tuple (R, G, B) ou (R, G, B, A) si surface supporte alpha.
    """
    if corner_radius < 0:
        raise ValueError(f"Corner radius {corner_radius} must be >= 0")
    if corner_radius > rect.width // 2 or corner_radius > rect.height // 2:
        # Si le rayon est trop grand, dessiner un cercle/ellipse ou un rect normal
        pygame.draw.rect(surface, color, rect)
        return

    # Dessiner les 4 rectangles qui forment la croix centrale
    pygame.draw.rect(surface, color, (rect.left + corner_radius, rect.top, rect.width - 2 * corner_radius, rect.height))
    pygame.draw.rect(surface, color, (rect.left, rect.top + corner_radius, rect.width, rect.height - 2 * corner_radius))

    # Dessiner les 4 cercles pour les coins
    pygame.draw.circle(surface, color, (rect.left + corner_radius, rect.top + corner_radius), corner_radius)
    pygame.draw.circle(surface, color, (rect.right - corner_radius -1, rect.top + corner_radius), corner_radius) # -1 pour ajustement pixel
    pygame.draw.circle(surface, color, (rect.left + corner_radius, rect.bottom - corner_radius -1), corner_radius)
    pygame.draw.circle(surface, color, (rect.right - corner_radius -1, rect.bottom - corner_radius -1), corner_radius)


def normalize_angle_for_sweep(angle_rad):
    """ Normalizes an angle to [0, 2*pi) for sweep calculations. """
    while angle_rad < 0:
        angle_rad += 2 * math.pi
    while angle_rad >= 2 * math.pi:
        angle_rad -= 2 * math.pi
    return angle_rad

def draw_thick_arc(surface, color, center, inner_radius, outer_radius,
                   arc_segment_start_rad_ccw, arc_segment_stop_rad_ccw,
                   segments_per_radian=10):
    """
    Draws a 'filled' thick arc manually using polygons.
    Angles are expected in standard mathematical convention (radians, 0 is East/right, positive is Counter-Clockwise).
    The arc is drawn Counter-Clockwise from arc_segment_start_rad_ccw to arc_segment_stop_rad_ccw.

    - surface: Pygame surface to draw on.
    - color: Color of the arc.
    - center: (x, y) tuple for the arc's center.
    - inner_radius: Radius of the inner edge of the arc.
    - outer_radius: Radius of the outer edge of the arc.
    - arc_segment_start_rad_ccw: Start angle of the arc segment to draw (math radians, CCW).
    - arc_segment_stop_rad_ccw: Stop angle of the arc segment to draw (math radians, CCW).
    - segments_per_radian: How many line segments to use per radian of arc.
                           Higher values give smoother curves but are more costly.
    """
    if outer_radius <= inner_radius or outer_radius <= 0:
        # print(f"Debug: Invalid radii: inner={inner_radius}, outer={outer_radius}")
        return
    if inner_radius < 0: # Treat as 0 if negative
        inner_radius = 0

    cx, cy = center

    # Normalize angles to ensure they are in a comparable range for sweep calculation
    start_norm = normalize_angle_for_sweep(arc_segment_start_rad_ccw)
    stop_norm = normalize_angle_for_sweep(arc_segment_stop_rad_ccw)

    # Calculate the angular sweep (delta) in CCW direction
    delta_angle = stop_norm - start_norm
    if delta_angle < 0: # If stop is "before" start after normalization (e.g., start=330deg, stop=30deg)
        delta_angle += 2 * math.pi # Make it the positive CCW sweep

    if abs(delta_angle) < 0.001: # Arc is essentially a line or point, or full circle if delta_angle was ~2pi
        if abs(delta_angle - 2 * math.pi) < 0.001: # Full circle (annulus)
            # Draw outer circle
            pygame.draw.circle(surface, color, center, int(outer_radius), 0)
            # Punch out inner circle (if inner_radius > 0 and surface supports transparency for punch-out)
            # This requires a more complex approach like drawing to a temp surface with colorkey.
            # For now, if it's a full ring and inner_radius > 0, we draw two circles.
            # This won't work perfectly if the surface behind isn't a solid color.
            # A better way for an annulus is two circles if the background is known,
            # or a filled polygon approach.
            # Given this function's purpose, a full 2*pi arc should be a ring.
            if inner_radius > 0:
                # To draw a ring, draw the larger circle, then a smaller circle of the background color
                # This is a simplification. A true annulus needs different handling.
                # For now, let's just draw the outer if it's a full circle for simplicity,
                # or if the intent is a filled disc (inner_radius == 0).
                if inner_radius == 0:
                    pygame.draw.circle(surface, color, center, int(outer_radius), 0)
                else:
                    # This is complex; for now, a full ring is approximated
                    # by many segments by the polygon method below if delta_angle is close to 2*pi.
                    # Let's make delta_angle slightly less than 2*pi if it's effectively full.
                    if abs(delta_angle) >= 2 * math.pi - 0.001:
                        delta_angle = 2 * math.pi - 0.001 # Ensure it's not exactly 0 or 2pi for step calc
        else: # Arc is too small (a line)
            return


    # Determine the number of segments based on the sweep and desired density
    num_segments = max(2, int(abs(delta_angle) * segments_per_radian)) # At least 2 segments for a polygon
    angle_step = delta_angle / num_segments

    points = []

    # Outer edge points (CCW)
    for i in range(num_segments + 1):
        angle = arc_segment_start_rad_ccw + i * angle_step # Iterate CCW
        x = cx + outer_radius * math.cos(angle)
        y = cy - outer_radius * math.sin(angle) # Pygame Y is inverted from math standard
        points.append((x, y))

    # Inner edge points (CW relative to the outer sweep, so iterate backwards from the stop angle)
    for i in range(num_segments + 1):
        angle = (arc_segment_start_rad_ccw + delta_angle) - (i * angle_step) # Iterate CW
        x = cx + inner_radius * math.cos(angle)
        y = cy - inner_radius * math.sin(angle) # Pygame Y is inverted
        points.append((x, y))

    if len(points) >= 3:
        try:
            pygame.draw.polygon(surface, color, points, 0) # width=0 for filled polygon
        except TypeError as e:
            print(f"Error drawing thick_arc polygon: {e}. Points: {len(points)}")
            # print(f"Sample points: {points[:3]} ... {points[-3:]}")
    # else:
    #     print(f"Warning: Not enough points for thick_arc polygon: {len(points)}")
# --- Classe Particle (Pour l'effet de disparition) ---
class Particle:
    def __init__(self, x, y,has_gravity, random_color, color, size_range, lifetime=PARTICLE_LIFETIME, max_speed=PARTICLE_MAX_SPEED): # Add params
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

        self.initial_size = random.randint(size_range[0], size_range[1])
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
    def __init__(self, x, y, radius, color, outline_color, outline_width, name, initial_vx, initial_vy, image_path=None):
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
        self.trail_positions = [] # List to store (x, y) tuples

        # --- AJOUT IMAGE ---
        self.image_surf = None
        if image_path:
            try:
                original_image = pygame.image.load(image_path).convert_alpha()
                # Scale image to fit inside the ball (minus a small margin)
                image_diameter = int(self.radius * 2 * 0.85) # 85% of ball diameter
                self.image_surf = pygame.transform.smoothscale(original_image, (image_diameter, image_diameter))
            except pygame.error as e:
                print(f"Warning: Could not load ball image '{image_path}': {e}")
        # --- FIN AJOUT IMAGE ---

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
        # --- AJOUT TRAIL DRAWING (Dessiner la trainée DERRIÈRE la balle) ---
        if self.trail_positions:
            # Calculate alpha step for fading
            alpha_step = BALL_TRAIL_START_ALPHA / len(self.trail_positions) if len(self.trail_positions) > 0 else BALL_TRAIL_START_ALPHA

            for i, trail_pos in enumerate(reversed(self.trail_positions)): # Draw oldest first
                # Trail circles get smaller and more transparent
                current_radius = int(self.radius * (1 - (i / len(self.trail_positions))) * 0.7) # Smaller trail
                current_alpha = int(BALL_TRAIL_START_ALPHA - (i * alpha_step))
                current_alpha = max(0, min(255, current_alpha)) # Clamp alpha

                if current_radius > 0 and current_alpha > 0:
                    # Create a temporary surface for each trail segment to handle alpha
                    trail_segment_surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(trail_segment_surf, (*self.color, current_alpha),
                                       (current_radius, current_radius), current_radius)
                    surface.blit(trail_segment_surf, (int(trail_pos[0]) - current_radius, int(trail_pos[1]) - current_radius))
        # --- FIN AJOUT TRAIL ---
        # Draw outline first
        pygame.draw.circle(surface, self.outline_color, pos, self.radius + self.outline_width)
        # Draw main ball color
        pygame.draw.circle(surface, self.color, pos, self.radius)

        # --- AJOUT IMAGE DRAWING ---
        if self.image_surf:
            # Center the image inside the ball
            img_rect = self.image_surf.get_rect(center=pos)
            surface.blit(self.image_surf, img_rect)
        # --- FIN AJOUT IMAGE ---

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
            center_line_radius = self.radius # Readability

            if center_line_radius <= self.thickness / 2:
                return
            # Optimization for very large/distant circles
            if current_radius_int > SCREEN_HEIGHT and NUM_CIRCLES > 15 : # Or some other heuristic
                if self.radius > INITIAL_RADIUS + (NUM_CIRCLES - 7) * RADIUS_STEP:
                    return


            inner_r = center_line_radius - self.thickness / 2
            outer_r = center_line_radius + self.thickness / 2

            if inner_r < 0: inner_r = 0
            if outer_r <= inner_r: return

            # Get gap boundaries in MATH RADIANS (CCW, 0=East)
            # These are assumed to be correctly calculated and stored in the CircleWall instance
            # (e.g., updated in self.update along with rotation)
            gap_start_math_rad = normalize_angle_for_sweep(self.gap_center_rad - self.gap_width_rad / 2)
            gap_end_math_rad   = normalize_angle_for_sweep(self.gap_center_rad + self.gap_width_rad / 2)

            # The wall segment starts where the gap ends (CCW) and ends where the gap starts (CCW).
            wall_arc_start_ccw = gap_end_math_rad
            wall_arc_stop_ccw  = gap_start_math_rad

            # Determine number of segments dynamically
            # More segments for larger radius or larger angular sweep
            angular_sweep_for_segments = wall_arc_stop_ccw - wall_arc_start_ccw
            if angular_sweep_for_segments < 0:
                angular_sweep_for_segments += 2 * math.pi
            
            # Ensure a minimum number of segments for small arcs, and more for larger ones
            # segments_count = max(6, int(center_line_radius / 10) + int(angular_sweep_for_segments * 5))
            segments_density_per_radian = 10 # Default, can be adjusted
            if center_line_radius > 150:
                segments_density_per_radian = 15
            elif center_line_radius > 300:
                segments_density_per_radian = 20


            # Check if the gap is almost non-existent (i.e., draw a full ring)
            if abs(self.gap_width_rad) < 0.01: # Very small gap, treat as full circle
                # For a full ring, we can draw from 0 to 2*pi
                draw_thick_arc(surface, self.color, (self.center_x, self.center_y),
                            inner_r, outer_r,
                            0, 2 * math.pi - 0.0001, # Slightly less than 2*pi to avoid segment issues
                            segments_per_radian=segments_density_per_radian)
            else:
                draw_thick_arc(surface, self.color, (self.center_x, self.center_y),
                            inner_r, outer_r,
                            wall_arc_start_ccw, wall_arc_stop_ccw,
                            segments_per_radian=segments_density_per_radian)
        
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

coin_sound = None # Initialiser à None
try:
    coin_sound_path = "mp3/mario_coin.mp3" # Assure-toi que le fichier est dans le bon dossier
    coin_sound = pygame.mixer.Sound(coin_sound_path)
    coin_sound.set_volume(0.01) # <-- Optionnel: Ajuste le volume (0.0 à 1.0)
    print(f"Loaded sound: {coin_sound_path}")
except pygame.error as e:
    print(f"Warning: Could not load sound file '{coin_sound_path}': {e}")
# --- Fin chargement son ---

# --- Logique Principale (Modifiée pour 2 balles, score, effets) ---
def main():
    # --- Load MIDI Notes Sequence ---
    loaded_notes = load_midi_notes(MIDI_FILENAME)
    current_note_index = 1 # Index for the next note to play from the loaded sequence
    # --- Create Banner Surface ---
    banner_surface = pygame.Surface((SCREEN_WIDTH, BANNER_HEIGHT), pygame.SRCALPHA)
    TRANSPARENT_BANNER_BG = (*BANNER_BG_COLOR, BANNER_ALPHA)
    # --- Fonts (TikTok Style) ---
# --- Fonts (TikTok Style) ---
    try:
        title_ui_font = pygame.font.Font(BOLD_FONT_PATH or MAIN_FONT_PATH, TITLE_TEXT_FONT_SIZE)
        player_name_font = pygame.font.Font(MAIN_FONT_PATH, PLAYER_NAME_FONT_SIZE)
        player_score_font = pygame.font.Font(BOLD_FONT_PATH or MAIN_FONT_PATH, PLAYER_SCORE_FONT_SIZE)
        print("Custom fonts loaded.")
    except Exception as e:
        # ... (fallback to default fonts) ...
        title_ui_font = pygame.font.Font(None, TITLE_TEXT_FONT_SIZE)
        player_name_font = pygame.font.Font(None, PLAYER_NAME_FONT_SIZE)
        player_score_font = pygame.font.Font(None, PLAYER_SCORE_FONT_SIZE)


    # --- Création des objets ---
    balls = []
    # Balle 1 (Rouge)
    angle_start1 = random.uniform(math.pi / 4, 3 * math.pi / 4) # Start upwards-left
    ball1 = Ball(CENTER_X - 10, CENTER_Y, BALL_RADIUS, RED, OUTLINE_COLOR, BALL_OUTLINE_WIDTH, "Mario",
                 INITIAL_BALL_SPEED * math.cos(angle_start1),
                 INITIAL_BALL_SPEED * math.sin(angle_start1),image_path=BALL_IMAGE_P1)
    balls.append(ball1)

    # Balle 2 (Bleue)
    angle_start2 = random.uniform(5 * math.pi / 4, 7 * math.pi / 4) # Start downwards-right
    ball2 = Ball(CENTER_X + 10, CENTER_Y, BALL_RADIUS, GREEN, OUTLINE_COLOR, BALL_OUTLINE_WIDTH, "Luigi",
                 INITIAL_BALL_SPEED * math.cos(angle_start2),
                 INITIAL_BALL_SPEED * math.sin(angle_start2),image_path=BALL_IMAGE_P2)
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

    game_started = False
    while not game_started:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # --- Cleanup before exit if quitting here ---
                if midi_output:
                    midi_output.close()
                pygame.midi.quit()
                pygame.mixer.quit()
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    game_started = True
                if event.key == pygame.K_ESCAPE: # Allow escape to quit from start screen
                    # --- Cleanup before exit if quitting here ---
                    if midi_output:
                        midi_output.close()
                    pygame.midi.quit()
                    pygame.mixer.quit()
                    pygame.quit()
                    sys.exit()



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
                collision_dist = (current_circle.radius - CIRCLE_THICKNESS/2) - (ball.radius + ball.outline_width)
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
                                     # --- AJOUTER LA LIGNE SUIVANTE ---
                                    if coin_sound: # Vérifie si le son a été chargé
                                        coin_sound.play()
                                    # --- FIN AJOUT ---

                                    # Créer l'effet de particules
                                    broken_circle_radius = current_circle.radius
                                    broken_circle_center_x = current_circle.center_x
                                    broken_circle_center_y = current_circle.center_y
                                    for _ in range(NUM_PARTICLES_ON_BREAK):
                                        # Start particles on the circle's edge
                                        p_angle = random.uniform(0, 2*math.pi)
                                        px = broken_circle_center_x + broken_circle_radius * math.cos(p_angle)
                                        py = broken_circle_center_y - broken_circle_radius * math.sin(p_angle) # Y down
                                        particles.append(Particle(px, py,has_gravity=True,random_color=True, color  = None,size_range=[1,5]))


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
                                        if current_note_index==len(loaded_notes):
                                            current_note_index =1

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


        # Dessiner les cercles
        for circle in circles:
            circle.draw(screen)



        # Dessiner les balles
        for ball in balls:
            ball.draw(screen)




                # --- Dessiner les Éléments UI en Haut ---
        current_ui_y = UI_TOP_MARGIN # Position Y de départ pour les éléments UI

        # 1. TITRE "MARIO or LUIGI?"
        title_text_surf = title_ui_font.render(TITLE_TEXT_CONTENT, True, TITLE_TEXT_COLOR)
        title_text_rect = title_text_surf.get_rect() # Obtenir la taille du texte

        # Créer le rectangle pour le fond de la bulle du titre
        title_box_width = title_text_rect.width + 2 * TEXT_BOX_PADDING
        title_box_height = title_text_rect.height + 2 * TEXT_BOX_PADDING
        title_box_rect = pygame.Rect(
            (SCREEN_WIDTH - title_box_width) // 2, # Centré horizontalement
            current_ui_y,
            title_box_width,
            title_box_height
        )
        # Dessiner le fond de la bulle (semi-transparent)
        title_box_bg_surf = pygame.Surface(title_box_rect.size, pygame.SRCALPHA)
        draw_rounded_rect(title_box_bg_surf, title_box_bg_surf.get_rect(), (*TEXT_BOX_BG_COLOR, TEXT_BOX_ALPHA), TEXT_BOX_BORDER_RADIUS)
        screen.blit(title_box_bg_surf, title_box_rect.topleft)

        # Positionner et dessiner le texte du titre DESSUS la bulle
        title_text_rect.center = title_box_rect.center
        screen.blit(title_text_surf, title_text_rect)

        current_ui_y += title_box_rect.height + UI_ELEMENT_SPACING # Mettre à jour Y pour le prochain élément

        # 2. SCORES DES JOUEURS (côte à côte)
        # Créer une surface temporaire pour contenir les deux scores, pour les centrer ensemble
        scores_container_width = SCREEN_WIDTH - 2 * UI_SIDE_PADDING
        # Estimer la hauteur max (plus grand entre nom et score + padding)
        temp_name_h = player_name_font.get_height()
        temp_score_h = player_score_font.get_height()
        player_box_inner_height = temp_name_h + temp_score_h + TEXT_BOX_PADDING * 2 + BANNER_VERTICAL_SPACING #BANNER_VERTICAL_SPACING est ancien, renommer
        player_box_height = player_box_inner_height # Hauteur pour la bulle d'un joueur

        # --- Boîte pour Joueur 1 (Gauche) ---
        p1_name_surf = player_name_font.render(balls[0].name, True, PLAYER_NAME_COLOR_P1)
        p1_score_surf = player_score_font.render(str(balls[0].score), True, PLAYER_SCORE_COLOR)
        # Largeur de la boîte basée sur le plus large entre nom et score
        p1_content_width = max(p1_name_surf.get_width(), p1_score_surf.get_width())
        p1_box_width = p1_content_width + 2 * TEXT_BOX_PADDING

        p1_box_rect = pygame.Rect(
            UI_SIDE_PADDING,
            current_ui_y,
            p1_box_width,
            player_box_height
        )
        p1_box_bg_surf = pygame.Surface(p1_box_rect.size, pygame.SRCALPHA)
        draw_rounded_rect(p1_box_bg_surf, p1_box_bg_surf.get_rect(), (*TEXT_BOX_BG_COLOR, TEXT_BOX_ALPHA), TEXT_BOX_BORDER_RADIUS)
        screen.blit(p1_box_bg_surf, p1_box_rect.topleft)

        # Positionner textes dans la boîte P1
        p1_name_pos_x = p1_box_rect.left + (p1_box_rect.width - p1_name_surf.get_width()) // 2 # Centré dans la boite
        p1_name_pos_y = p1_box_rect.top + TEXT_BOX_PADDING
        screen.blit(p1_name_surf, (p1_name_pos_x, p1_name_pos_y))

        p1_score_pos_x = p1_box_rect.left + (p1_box_rect.width - p1_score_surf.get_width()) // 2 # Centré
        p1_score_pos_y = p1_name_pos_y + p1_name_surf.get_height() + BANNER_VERTICAL_SPACING # BANNER_VERTICAL_SPACING
        screen.blit(p1_score_surf, (p1_score_pos_x, p1_score_pos_y))


        # --- Boîte pour Joueur 2 (Droite) ---
        p2_name_surf = player_name_font.render(balls[1].name, True, PLAYER_NAME_COLOR_P2)
        p2_score_surf = player_score_font.render(str(balls[1].score), True, PLAYER_SCORE_COLOR)
        p2_content_width = max(p2_name_surf.get_width(), p2_score_surf.get_width())
        p2_box_width = p2_content_width + 2 * TEXT_BOX_PADDING

        p2_box_rect = pygame.Rect(
            SCREEN_WIDTH - UI_SIDE_PADDING - p2_box_width,
            current_ui_y,
            p2_box_width,
            player_box_height
        )
        p2_box_bg_surf = pygame.Surface(p2_box_rect.size, pygame.SRCALPHA)
        draw_rounded_rect(p2_box_bg_surf, p2_box_bg_surf.get_rect(), (*TEXT_BOX_BG_COLOR, TEXT_BOX_ALPHA), TEXT_BOX_BORDER_RADIUS)
        screen.blit(p2_box_bg_surf, p2_box_rect.topleft)

        # Positionner textes dans la boîte P2
        p2_name_pos_x = p2_box_rect.left + (p2_box_rect.width - p2_name_surf.get_width()) // 2
        p2_name_pos_y = p2_box_rect.top + TEXT_BOX_PADDING
        screen.blit(p2_name_surf, (p2_name_pos_x, p2_name_pos_y))

        p2_score_pos_x = p2_box_rect.left + (p2_box_rect.width - p2_score_surf.get_width()) // 2
        p2_score_pos_y = p2_name_pos_y + p2_name_surf.get_height() + BANNER_VERTICAL_SPACING # BANNER_VERTICAL_SPACING
        screen.blit(p2_score_surf, (p2_score_pos_x, p2_score_pos_y))


        # --- Décalage Y pour les particules de score (si elles sont toujours relatives aux boîtes de score) ---
        # Note : les particules de score doivent maintenant être générées par rapport aux positions p1_score_rect.center et p2_score_rect.center
        # qui sont maintenant en coordonnées d'écran (car on blit directement sur `screen`).

        # --- !! SCORE PARTICLE TRIGGER !! ---
        # La logique ici doit être ajustée car p1_score_rect et p2_score_rect sont maintenant
        # des rects locaux à leur "boîte" de texte. Il faut calculer leur position globale.
        if balls[0].just_scored:
            # Position globale du centre du score P1
            score_p1_global_centerx = p1_score_pos_x + p1_score_surf.get_width() // 2
            score_p1_global_centery = p1_score_pos_y + p1_score_surf.get_height() // 2
            for _ in range(NUM_SCORE_PARTICLES):
                 particles.append(Particle(score_p1_global_centerx, score_p1_global_centery, has_gravity=False,random_color=True, color = SCORE_PARTICLE_COLOR,size_range= [2,10], lifetime=SCORE_PARTICLE_LIFETIME, max_speed=SCORE_PARTICLE_MAX_SPEED))
            balls[0].just_scored = False

        if balls[1].just_scored:
            score_p2_global_centerx = p2_score_pos_x + p2_score_surf.get_width() // 2
            score_p2_global_centery = p2_score_pos_y + p2_score_surf.get_height() // 2
            for _ in range(NUM_SCORE_PARTICLES):
                 particles.append(Particle(score_p2_global_centerx, score_p2_global_centery, has_gravity=False,random_color=True, color = SCORE_PARTICLE_COLOR,size_range= [2,10], lifetime=SCORE_PARTICLE_LIFETIME, max_speed=SCORE_PARTICLE_MAX_SPEED))
            balls[1].just_scored = False
        # --- FIN Dessin UI ---
       

                # Dessiner les particules
        for particle in particles:
            particle.draw(screen)
        pygame.display.flip()

    # --- Fin ---
    pygame.quit()
    sys.exit()

# --- Point d'entrée ---
if __name__ == '__main__':
    main()