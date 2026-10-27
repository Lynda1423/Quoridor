"""
FICHIER : gui.py
ROLE : Ce fichier gère l'interface graphique (GUI) du jeu.
Il utilise Pygame pour le rendu 2.5D et gère les interactions utilisateur.
Notion de cours : Interface Homme-Machine (IHM) pédagogique.
"""

import pygame
import math
import array
from .board import QuoridorBoard
from .ai_algorithms import iterative_deepening
from .heuristics import evaluate_board

# ... (les couleurs et constantes restent identiques)
# [Note : Je garde les constantes pour la cohérence visuelle]
BG_COLOR1 = (18, 20, 25)
BG_COLOR2 = (30, 35, 45)
PANEL_COLOR = (45, 48, 55)
BOARD_BASE = (20, 22, 30)
TILE_COLOR = (180, 150, 110)
TILE_HOVER = (220, 200, 150)
P1_COLOR = (240, 235, 220)
P2_COLOR = (40, 30, 20)
WALL_COLOR = (230, 170, 80)
TEXT_COLOR = (245, 240, 230)

TILE_W = 54
TILE_H = 54
Z_SCALE = 16
OFFSET_X = 156
OFFSET_Y = 56

def to_3d(wx, wy, wz=0):
    """Projection pseudo-3D."""
    sx = OFFSET_X + wx * TILE_W
    sy = OFFSET_Y + wy * TILE_H - wz * Z_SCALE
    return int(sx), int(sy)

def draw_3d_obj(screen, wx, wy, wz, sx, sy, sz, top_c, front_c, is_pawn=False):
    t0 = to_3d(wx, wy, wz + sz)
    t1 = to_3d(wx + sx, wy, wz + sz)
    t2 = to_3d(wx + sx, wy + sy, wz + sz)
    t3 = to_3d(wx, wy + sy, wz + sz)
    b2 = to_3d(wx + sx, wy + sy, wz)
    b3 = to_3d(wx, wy + sy, wz)
    if is_pawn:
        rc = min(t1[0]-t0[0], t3[1]-t0[1]) // 2
        cx = t0[0] + (t1[0]-t0[0])//2
        cy = t0[1] + (t3[1]-t0[1])//2
        pygame.draw.rect(screen, front_c, pygame.Rect(cx - rc, cy, rc*2, (b3[1]-t3[1]) + rc))
        pygame.draw.circle(screen, front_c, (cx, b3[1] + rc//2), rc)
        pygame.draw.circle(screen, top_c, (cx, cy), rc)
        pygame.draw.circle(screen, (255,255,255), (cx-rc//3, cy-rc//3), rc//4)
    else:
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(b3[0]-2, b3[1]-2, t1[0]-t0[0]+4, (b2[1]-b3[1])+4), border_radius=4)
        pygame.draw.polygon(screen, front_c, [t3, t2, b2, b3])
        pygame.draw.polygon(screen, top_c, [t0, t1, t2, t3])
        pygame.draw.polygon(screen, (max(0, top_c[0]-30), max(0, top_c[1]-25), max(0, top_c[2]-20)), [t0, t1, t2, t3], width=1)

def draw_2d_arrow(screen, wx, wy, wz, dr, dc, color):
    cx, cy = to_3d(wx + 0.5, wy + 0.5, wz)
    angle = math.atan2(dr * TILE_H, dc * TILE_W)
    size = 12
    pts = [(cx+size*math.cos(angle), cy+size*math.sin(angle)),
           (cx+size*math.cos(angle+2.5), cy+size*math.sin(angle+2.5)),
           (cx+size*math.cos(angle-2.5), cy+size*math.sin(angle-2.5))]
    pygame.draw.polygon(screen, color, pts)
    pygame.draw.polygon(screen, (0,0,0), pts, width=1)

def create_bg_surface():
    s = pygame.Surface((800, 600))
    for y in range(600):
        t = y / 600.0
        r = int(BG_COLOR1[0] + (BG_COLOR2[0]-BG_COLOR1[0])*t)
        g = int(BG_COLOR1[1] + (BG_COLOR2[1]-BG_COLOR1[1])*t)
        b = int(BG_COLOR1[2] + (BG_COLOR2[2]-BG_COLOR1[2])*t)
        pygame.draw.line(s, (r, g, b), (0, y), (800, y))
    return s

def lerp(a, b, t): return a + (b - a) * t

def generate_sound(freq, duration, volume=0.3, noise=False):
    pygame.mixer.pre_init(44100, -16, 2, 512)
    sample_rate = 44100
    n_samples = int(duration * sample_rate)
    buf = array.array('h')
    for i in range(n_samples):
        t = float(i) / sample_rate
        val = int(volume*32767.0*random.uniform(-1,1)) if noise else int(volume*32767.0*math.sin(2.0*math.pi*freq*t))
        envelope = 1.0 - (float(i)/n_samples)
        sample = int(val * envelope); buf.append(sample); buf.append(sample)
    try: return pygame.mixer.Sound(buffer=buf)
    except: return None

def generate_fx(type="win"):
    """Génère des effets sonores complexes (Victoire/Défaite)."""
    pygame.mixer.pre_init(44100, -16, 2, 512)
    sample_rate = 44100
    duration = 1.0
    buf = array.array('h')
    for i in range(int(duration * sample_rate)):
        t = float(i) / sample_rate
        if type == "win": # "Weeee" : Fréquence montante
            freq = 400 + 400 * t + 100 * math.sin(20 * t)
        else: # "Ohhhh" : Fréquence descendante
            freq = 300 - 150 * t + 50 * math.sin(10 * t)
            
        val = int(0.3 * 32767.0 * math.sin(2.0 * math.pi * freq * t))
        env = math.exp(-2.0 * t) # Fade out
        s = int(val * env); buf.append(s); buf.append(s)
    try: return pygame.mixer.Sound(buffer=buf)
    except: return None

def generate_bgm():
    """Génère une boucle de musique d'ambiance Moderne & Motivante (BPM 120)."""
    pygame.mixer.pre_init(44100, -16, 2, 512)
    sample_rate = 44100
    duration = 4.0 
    buf = array.array('h')
    
    for i in range(int(duration * sample_rate)):
        t = float(i) / sample_rate
        # Kick plus percutant (2 coups par seconde)
        beat = (i % (sample_rate // 2)) / (sample_rate // 2)
        kick = math.sin(2.0 * math.pi * 60 * math.exp(-15 * beat)) * math.exp(-8 * beat)
        
        # Snare/Charley (Bruit blanc rythmé)
        noise_val = random.uniform(-1, 1) if (i % (sample_rate // 2)) > (sample_rate // 4) else 0
        snare = noise_val * math.exp(-12 * ((i % (sample_rate // 4)) / (sample_rate // 4))) * 0.1
        
        # Mélodie synthétique moderne (Lead)
        note_cycle = [220, 261, 329, 392] # Accord Am7
        freq = note_cycle[int(t * 2) % len(note_cycle)]
        lead = 0.15 * math.sin(2.0 * math.pi * freq * t) * (0.5 + 0.5 * math.sin(2.0 * math.pi * 4 * t))
        
        val = int(0.25 * 32767.0 * (kick + snare + lead))
        buf.append(val); buf.append(val)
    try:
        snd = pygame.mixer.Sound(buffer=buf)
        snd.set_volume(0.3)
        return snd
    except: return None

class Particle:
    """Système de particules pour les ballons et confettis de victoire."""
    def __init__(self, x, y, color):
        self.x, self.y = x, y
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-10, -2)
        self.color = color
        self.life = 100
        self.size = random.randint(4, 12)
        self.type = random.choice(["balloon", "confetti"])

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.1 # Gravité
        self.life -= 1

    def draw(self, screen):
        alpha = min(255, self.life * 3)
        s = pygame.Surface((self.size*2, self.size*3), pygame.SRCALPHA)
        if self.type == "balloon":
            pygame.draw.ellipse(s, (*self.color, alpha), (0, 0, self.size*2, self.size*2.5))
            pygame.draw.line(s, (200, 200, 200, alpha), (self.size, self.size*2), (self.size, self.size*3))
        else:
            pygame.draw.rect(s, (*self.color, alpha), (0, 0, self.size, self.size//2))
        screen.blit(s, (self.x, self.y))

# Import random for generate_sound
import random

class QuoridorGUI:
    """
    Classe principale gérant la boucle de jeu et l'affichage.
    Notion de cours : Pattern MVC (Model-View-Controller).
    """
    def __init__(self, mode="PvAI", difficulty=3, algo="alphabeta"):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Quoridor Modern - Pédagogique")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont("segoeui", 36, bold=True)
        self.font_mid = pygame.font.SysFont("segoeui", 20, bold=True)
        self.font_small = pygame.font.SysFont("segoeui", 14)
        
        self.board = QuoridorBoard()
        self.mode = mode
        self.difficulty = difficulty
        self.algo = algo
        
        self.pawn_visual_pos = [[c*1.1, r*1.1] for r, c in self.board.pawns]
        self.bg_surface = create_bg_surface()
        self.time_elapsed = 0
        
        # Audio
        self.snd_move = generate_sound(600, 0.1, 0.15)
        self.snd_wall = generate_sound(100, 0.2, 0.3, noise=True)
        
        self.selected_wall = None
        self.hovered_tile = None
        self.game_over = False
        self.winner = None
        self.thinking = False
        self.action = None
        
        # Nouveaux sons
        self.snd_win = generate_fx("win")
        self.snd_loss = generate_fx("loss")
        
        # Rects pour les nouveaux boutons 3D
        self.btn_restart = pygame.Rect(15, 545, 110, 45)
        self.btn_quit = pygame.Rect(675, 545, 110, 45)
        
        self.demo_text = "Lancement de la Démo..."
        self.show_path = True # Option pédagogique : afficher le chemin court
        
        self.replay_btn = pygame.Rect(300, 360, 200, 42)
        self.menu_btn = pygame.Rect(300, 415, 200, 42)
        self.hover_replay = False
        self.hover_menu = False
        self.last_ai_move_time = pygame.time.get_ticks()
        self.moves_played = 0
        self.active_algo_name = "Alpha-Beta"
        
        # Musique, Particules et Chrono
        self.sound_on = True
        self.btn_sound = pygame.Rect(750, 10, 35, 30)
        
        # Init du nom d'algo pour l'affichage
        if algo == "sss_star": self.active_algo_name = "SSS*"
        elif algo == "adaptive": self.active_algo_name = "Alpha-Beta"
        else: self.active_algo_name = "Alpha-Beta"
        
        pygame.mixer.stop()
        self.bgm = generate_bgm()
        if self.bgm: self.bgm.play(-1)
        self.particles = []
        self.start_ticks = pygame.time.get_ticks()
        self.final_time = None
        self.ai_move_pending = None
        self.ai_next_move_time = 0
        self.pos_history = {}  # Historique des positions pour détecter les oscillations

    def update_animations(self):
        """Mise à jour fluide de la position des pions (Animation)."""
        for i in range(2):
            tc, tr = self.board.pawns[i][1]*1.1, self.board.pawns[i][0]*1.1
            # Utilisation d'un facteur lerp plus réactif
            self.pawn_visual_pos[i][0] = lerp(self.pawn_visual_pos[i][0], tc, 0.3)
            self.pawn_visual_pos[i][1] = lerp(self.pawn_visual_pos[i][1], tr, 0.3)

    def draw(self):
        self.screen.blit(self.bg_surface, (0, 0))
        self.time_elapsed += 1
        
        self.draw_ui()
        valid_moves = []
        if not self.game_over and not self.thinking:
            if self.mode == 'PvP' or (self.mode == 'PvAI' and self.board.turn == 0):
                valid_moves = self.board.get_valid_pawn_moves()

        objects = []
        objects.append((-1.0, "BASE", -0.1, -0.1, -0.4, 10.0, 10.0, 0.4, BOARD_BASE, (10,12,18), False, 0, 0))
        
        for r in range(9):
            for c in range(9):
                is_valid = (r, c) in valid_moves
                top_c, front_c = TILE_COLOR, (135, 110, 75)
                
                if is_valid:
                    pulse = int(15 * math.sin(self.time_elapsed * 0.1))
                    top_c = (min(255, top_c[0]+pulse), min(255, top_c[1]+pulse), top_c[2])
                if self.hovered_tile == (r, c) and is_valid:
                    top_c = TILE_HOVER
                objects.append((r*1.1, "TILE", c*1.1, r*1.1, 0.0, 1.0, 1.0, 0.1, top_c, front_c, is_valid, r, c))
                
        for r, c in self.board.walls_h:
            objects.append((r*1.1+1.0, "WALL", c*1.1, r*1.1+1.0, 0.0, 2.1, 0.1, 0.7, WALL_COLOR, (170,130,40), False, 0, 0))
        for r, c in self.board.walls_v:
            objects.append((r*1.1, "WALL", c*1.1+1.0, r*1.1, 0.0, 0.1, 2.1, 0.7, WALL_COLOR, (170,130,40), False, 0, 0))

        if self.selected_wall and not self.game_over and not self.thinking:
            orient, r, c = self.selected_wall
            if self.board.is_valid_wall(orient, r, c):
                h_wt, h_wf = (255, 230, 150), (200, 160, 80)
                if orient == 'H': objects.append((r*1.1+1.0, "WALL", c*1.1, r*1.1+1.0, 0.0, 2.1, 0.1, 0.7, h_wt, h_wf, False, 0, 0))
                else: objects.append((r*1.1, "WALL", c*1.1+1.0, r*1.1, 0.0, 0.1, 2.1, 0.7, h_wt, h_wf, False, 0, 0))

        for i in range(2):
            wx, wy = self.pawn_visual_pos[i]
            col = P1_COLOR if i == 0 else P2_COLOR
            objects.append((wy+0.5, "PAWN", wx+0.2, wy+0.2, 0.1, 0.6, 0.6, 0.9, col, (max(0,col[0]-40),max(0,col[1]-40),max(0,col[2]-40)), False, 0, 0))
            
        objects.sort(key=lambda o: o[0])
        for obj in objects:
            wy_depth, type_, wx, wy, wz, sx, sy, sz, top_c, front_c, is_valid, r, c = obj
            draw_3d_obj(self.screen, wx, wy, wz, sx, sy, sz, top_c, front_c, type_ == "PAWN")
            if type_ == "TILE" and is_valid:
                pr, pc = self.board.pawns[self.board.turn]
                draw_2d_arrow(self.screen, wx, wy, 0.22, r-pr, c-pc, P1_COLOR if self.board.turn==0 else P2_COLOR)

        if self.game_over:
            self.draw_game_over()
        pygame.display.flip()

    def draw_ui(self):
        """Affiche les panneaux latéraux (murs, noms) et la barre d'état."""
        p1_rect = pygame.Rect(15, OFFSET_Y, 110, 480)
        p2_rect = pygame.Rect(675, OFFSET_Y, 110, 480)
        for r_ in [p1_rect, p2_rect]:
            pygame.draw.rect(self.screen, (10, 12, 15), r_.move(0, 4), border_radius=12)
            pygame.draw.rect(self.screen, PANEL_COLOR, r_, border_radius=12)
        
        # Affichage du Score d'Évaluation (Pédagogie)
        score = evaluate_board(self.board, 0)
        score_text = f"Avantage: {'P1' if score > 0 else 'P2'} ({abs(score)})"
        st = self.font_small.render(score_text, True, (150, 200, 255))
        self.screen.blit(st, (400 - st.get_width()//2, 53))

        # Noms et Buts
        t1 = self.font_mid.render("P1 (Vous)", True, P1_COLOR)
        self.screen.blit(t1, (p1_rect.centerx - t1.get_width()//2, p1_rect.top+15))
        g1 = self.font_small.render("But: HAUT", True, (150, 150, 150))
        self.screen.blit(g1, (p1_rect.centerx - g1.get_width()//2, p1_rect.bottom-30))

        t2 = self.font_mid.render("P2 (IA)", True, P2_COLOR)
        self.screen.blit(t2, (p2_rect.centerx - t2.get_width()//2, p2_rect.top+15))
        g2 = self.font_small.render("But: BAS", True, (150, 150, 150))
        self.screen.blit(g2, (p2_rect.centerx - g2.get_width()//2, p2_rect.bottom-30))
        
        # Affichage des murs restants (piles visuelles)
        for p_idx, r_ in [(0, p1_rect), (1, p2_rect)]:
            for w in range(self.board.walls_left[p_idx]):
                w_r = pygame.Rect(r_.centerx-25, r_.top+60+w*28 + (10-self.board.walls_left[p_idx])*28, 50, 14)
                # Effet de relief sur les murs
                pygame.draw.rect(self.screen, (20, 15, 10), w_r.move(0, 2), border_radius=3)
                pygame.draw.rect(self.screen, WALL_COLOR, w_r, border_radius=3)
                pygame.draw.rect(self.screen, (255, 200, 120), w_r.inflate(-4, -8), border_radius=1)

        # Bar Top Cinématique
        bar = pygame.Surface((800, 45), pygame.SRCALPHA); bar.fill((15, 18, 25, 230))
        self.screen.blit(bar, (0, 0))
        
        # Calcul du statut dynamique (Tour et Algo)
        if self.algo == "adaptive":
            algo_display = self.active_algo_name
        else:
            algo_display = "SSS*" if self.algo == "sss_star" else "Alpha-Beta"
            
        if self.mode == "AIvAI":
            status = f"Tour IA {self.board.turn + 1} ({algo_display})"
        elif self.mode == "PvP":
            status = f"Tour Joueur {self.board.turn + 1}"
        elif self.board.turn == 1:
            status = f"Tour IA ({algo_display})"
        else:
            status = "C'est votre tour"

        txt_val = status
        txt = self.font_mid.render(txt_val, True, (180, 220, 255))
        self.screen.blit(txt, (400 - txt.get_width()//2, 10))

        # Boutons 3D de contrôle (Positionnés proprement)
        self.draw_custom_3d_button("REJOUER", self.btn_restart, (40, 180, 100))
        self.draw_custom_3d_button("QUITTER", self.btn_quit, (200, 60, 60))

        # Bouton Son (Toggle avec icône 'Baffle')
        s_col = (100, 200, 255) if self.sound_on else (150, 150, 150)
        pygame.draw.rect(self.screen, s_col, self.btn_sound, border_radius=5, width=2)
        
        # Dessin du baffle (Haut-parleur)
        bx, by = self.btn_sound.x + 8, self.btn_sound.y + 10
        pygame.draw.rect(self.screen, s_col, (bx, by+3, 6, 6)) # Base
        pygame.draw.polygon(self.screen, s_col, [(bx+6, by+3), (bx+12, by), (bx+12, by+12), (bx+6, by+9)]) # Pavillon
        
        if self.sound_on:
            # Ondes sonores
            pygame.draw.arc(self.screen, s_col, (bx+10, by, 10, 12), -math.pi/3, math.pi/3, 2)
        else:
            # Barre muet (X)
            pygame.draw.line(self.screen, (200, 50, 50), (bx+2, by), (bx+16, by+14), 2)

    def draw_custom_3d_button(self, text, rect, color):
        """Dessine un bouton avec un effet 3D 'Premium' ultra-travaillé."""
        mx, my = pygame.mouse.get_pos()
        hover = rect.collidepoint(mx, my)
        offset = 4 if not hover else 1
        
        # Ombre portée
        pygame.draw.rect(self.screen, (5, 5, 8), rect.move(0, 6), border_radius=10)
        # Profondeur du bouton
        dark = (max(0, color[0]-60), max(0, color[1]-60), max(0, color[2]-60))
        pygame.draw.rect(self.screen, dark, rect.move(0, offset), border_radius=10)
        
        # Face supérieure
        top_c = color if not hover else (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30))
        pygame.draw.rect(self.screen, top_c, rect.move(0, - (4-offset)), border_radius=10)
        
        # Reflet de lumière
        pygame.draw.rect(self.screen, (255, 255, 255, 60), rect.move(0, - (4-offset)), width=1, border_radius=10)
        
        # Texte avec ombre portée
        stxt = self.font_small.render(text, True, (0, 0, 0, 100))
        self.screen.blit(stxt, (rect.centerx - stxt.get_width()//2 + 1, rect.centery - stxt.get_height()//2 - (4-offset) + 1))
        txt = self.font_small.render(text, True, (255, 255, 255))
        self.screen.blit(txt, (rect.centerx - txt.get_width()//2, rect.centery - txt.get_height()//2 - (4-offset)))

    def handle_mouse(self, pos):
        if self.game_over or self.thinking: return
        self.hovered_tile, self.selected_wall = None, None
        mx, my = pos
        for r in range(9):
            for c in range(9):
                # On ajuste la détection à wz=0.1 (surface supérieure des tuiles)
                tx, ty = to_3d(c*1.1, r*1.1, 0.1)
                if pygame.Rect(tx, ty, TILE_W, TILE_H).collidepoint(mx, my):
                    self.hovered_tile = (r, c); return
        best_d, best_w = 1000, None # Sensibilité augmentée (1000 vs 600)
        for r in range(8):
            for c in range(8):
                # On cible l'intersection exacte entre 4 cases
                ix, iy = to_3d(c*1.1+1.0, r*1.1+1.0, 0.2)
                d = (mx-ix)**2 + (my-iy)**2
                if d < best_d:
                    best_d = d
                    # Logique corrigée : 
                    # Si l'écart horizontal est plus grand que l'écart vertical, 
                    # cela veut dire qu'on est sur une ligne HORIZONTALE.
                    best_w = ('H' if abs(mx-ix) > abs(my-iy) else 'V', r, c)
        self.selected_wall = best_w

    def process_click(self, pos):
        # Clic sur les boutons de contrôle
        if self.btn_restart.collidepoint(pos):
            self.action = "REPLAY"; return
        if self.btn_quit.collidepoint(pos):
            self.action = "MENU"; return
            
        # Clic sur le bouton Son
        if self.btn_sound.collidepoint(pos):
            self.sound_on = not self.sound_on
            if not self.sound_on: pygame.mixer.stop()
            elif self.bgm: self.bgm.play(-1)
            return

        if self.game_over:
            if self.replay_btn.collidepoint(pos): self.action = "REPLAY"
            elif self.menu_btn.collidepoint(pos): self.action = "MENU"
            return
        if self.thinking: return
        t = self.board.turn
        if self.hovered_tile and self.hovered_tile in self.board.get_valid_pawn_moves():
            self.apply_move(('M', *self.hovered_tile))
        elif self.selected_wall and self.board.is_valid_wall(*self.selected_wall):
            self.apply_move(('W', *self.selected_wall))

    def apply_move(self, move):
        """Applique un mouvement (M ou W) de manière unifiée avec Snap visuel."""
        t = self.board.turn
        if move[0] == 'M':
            r, c = move[1], move[2]
            self.pawn_visual_pos[t][0] = c * 1.1
            self.pawn_visual_pos[t][1] = r * 1.1
            self.board.make_move(move)
            if self.sound_on and self.snd_move: self.snd_move.play()
        else:
            self.board.make_move(move)
            if self.sound_on and self.snd_wall: self.snd_wall.play()
            
        self.moves_played += 1
        
        # Mise à jour de l'historique des positions (pour détecter les oscillations de l'IA)
        key = (tuple(self.board.pawns[0]), tuple(self.board.pawns[1]))
        self.pos_history[key] = self.pos_history.get(key, 0) + 1
        # On garde l'historique compact (effacement des très vieilles positions)
        if len(self.pos_history) > 30:
            oldest_key = next(iter(self.pos_history))
            del self.pos_history[oldest_key]
        
        self.check_win()

    def check_win(self):
        w = self.board.check_winner()
        if w is not None: 
            self.game_over, self.winner = True, w
            self.final_time = pygame.time.get_ticks() 
            if self.bgm: self.bgm.stop()
            if self.sound_on:
                # En PvP, c'est toujours une victoire humaine. En PvAI, seulement si w=0.
                if self.mode == 'PvP' or (self.mode == 'PvAI' and w == 0):
                    if self.snd_win: self.snd_win.play()
                else:
                    if self.snd_loss: self.snd_loss.play()

    def run(self):
        while True:
            self.clock.tick(60); self.update_animations()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "QUIT"
                if event.type == pygame.MOUSEMOTION: self.handle_mouse(event.pos)
                if event.type == pygame.MOUSEBUTTONDOWN: self.process_click(event.pos)
                
                # GESTION DU CLAVIER
                if event.type == pygame.KEYDOWN and not self.game_over and not self.thinking:
                    if (self.mode == 'PvP' or (self.mode == 'PvAI' and self.board.turn == 0)):
                        dr, dc = 0, 0
                        if event.key == pygame.K_UP: dr = -1
                        elif event.key == pygame.K_DOWN: dr = 1
                        elif event.key == pygame.K_LEFT: dc = -1
                        elif event.key == pygame.K_RIGHT: dc = 1
                        
                        if dr != 0 or dc != 0:
                            cr, cc = self.board.pawns[self.board.turn]
                            target = (cr + dr, cc + dc)
                            # On vérifie si ce mouvement est dans la liste des coups valides
                            if target in self.board.get_valid_pawn_moves():
                                self.apply_move(('M', target[0], target[1]))
            self.draw()
            if self.action: return self.action
            if not self.game_over and ((self.mode=='PvAI' and self.board.turn==1) or self.mode=='AIvAI'):
                now = pygame.time.get_ticks()
                # On ne réfléchit QUE si on n'est pas déjà en train de penser ET qu'aucun mouvement n'attend d'être joué
                if not self.thinking and not self.ai_move_pending and now > self.ai_next_move_time:
                    self.thinking = True
                    self.draw()
                    
                    # On utilise la vraie difficulté choisie par l'utilisateur
                    depth = self.difficulty 
                    
                    if self.algo == "adaptive":
                        from .ai_algorithms import adaptive_search
                        move, active_algo = adaptive_search(self.board, depth, self.board.turn)
                        self.active_algo_name = active_algo 
                    else:
                        move = iterative_deepening(self.board, depth, algo=self.algo, maximizing_player_idx=self.board.turn, pos_history=self.pos_history)
                    
                    if move:
                        # On laisse 800ms pour que l'utilisateur puisse lire l'algorithme utilisé
                        self.ai_move_pending = move
                    
                    # Délai de réflexion visuelle pour la lisibilité de l'algorithme
                    self.ai_next_move_time = pygame.time.get_ticks() + 800
                    self.thinking = False

                # Si un mouvement est prêt et que le délai est passé
                if self.ai_move_pending and now > self.ai_next_move_time:
                    self.apply_move(self.ai_move_pending)
                    self.ai_move_pending = None
                    self.ai_next_move_time = now + 150 # Repos minimal (150ms)

    def draw_game_over(self):
        """Écran de fin 'Haute Couture' 2026."""
        # Calcul du temps final formaté
        t_ticks = self.final_time if self.final_time else pygame.time.get_ticks()
        total_seconds = (t_ticks - self.start_ticks) // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        time_str = f"{minutes} min {seconds} s" if minutes > 0 else f"{seconds} s"

        # Overlay cinématique
        s = pygame.Surface((800, 600), pygame.SRCALPHA)
        s.fill((10, 15, 25, 210))
        self.screen.blit(s, (0, 0))
        
        # Carte centrale plus élégante
        card_rect = pygame.Rect(220, 120, 360, 380)
        pygame.draw.rect(self.screen, (30, 35, 50), card_rect, border_radius=25)
        pygame.draw.rect(self.screen, (100, 180, 255, 80), card_rect, width=1, border_radius=25)
        
        # Détermination du nom du vainqueur
        if self.mode == 'PvP':
            winner_name = f"JOUEUR {self.winner + 1}"
            res_txt = "VICTOIRE !"
            is_human_win = True
        else:
            winner_name = "P1 (VOUS)" if self.winner == 0 else "IA SUBTLE"
            res_txt = "VICTOIRE" if self.winner == 0 else "DÉFAITE"
            is_human_win = (self.winner == 0)
            
        # Titre avec un léger effet de glow
        title_color = P1_COLOR if self.winner == 0 else (255, 100, 100)
        t1 = self.font_large.render(res_txt, True, title_color)
        self.screen.blit(t1, (400 - t1.get_width()//2, 160))
        
        # Ligne de séparation
        pygame.draw.line(self.screen, (60, 70, 90), (250, 215), (550, 215), 1)
        
        # Statistiques compactes
        f_s = pygame.font.SysFont("segoeui", 16)
        f_v = pygame.font.SysFont("segoeui", 17, bold=True)
        
        stats = [
            ("Vainqueur", winner_name),
            ("Mouvements", f"{self.moves_played} coups"),
            ("Durée", time_str),
            ("Intelligence", self.active_algo_name if self.mode != 'PvP' else "Cerveau Humain")
        ]
        
        for i, (label, val) in enumerate(stats):
            lb = f_s.render(label, True, (140, 160, 180))
            vl = f_v.render(val, True, (255, 255, 255))
            self.screen.blit(lb, (270, 235 + i * 32))
            self.screen.blit(vl, (530 - vl.get_width(), 235 + i * 32))

        # Effets Visuels : Ballons pour toute victoire humaine (PvP ou PvAI)
        if is_human_win:
            if random.random() < 0.2:
                for _ in range(3):
                    self.particles.append(Particle(random.randint(200, 600), 500, [random.randint(150, 255) for _ in range(3)]))
            for p in self.particles[:]:
                p.update(); p.draw(self.screen)
                if p.life <= 0: self.particles.remove(p)
        else:
            # Smiley Triste discret
            cx, cy = 400, 480
            pygame.draw.circle(self.screen, (200, 220, 255, 30), (cx, cy), 20, 1)

        # Boutons plus petits et plus chics
        self.draw_custom_3d_button("REPRENDRE", self.replay_btn, (60, 160, 90))
        self.draw_custom_3d_button("QUITTER", self.menu_btn, (160, 60, 60))
