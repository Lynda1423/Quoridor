"""
FICHIER : main.py
ROLE : Point d'entrée principal du programme Quoridor.
Ce fichier orchestre le lancement de l'application, gère l'intro cinématographique,
le menu principal (choix des modes, difficulté) et la boucle de jeu de haut niveau.
"""

import sys, os, pygame, math, random

# Ajout du dossier courant au PATH pour permettre les imports relatifs 'from src.xxx'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from src.gui import QuoridorGUI, TEXT_COLOR, P1_COLOR, P2_COLOR, create_bg_surface

def generate_intro_music():
    """
    Génère une petite séquence sonore pour l'introduction.
    Utilisation de la synthèse additive simple pour créer un son de 'marimba'.
    """
    import array, math
    pygame.mixer.pre_init(44100, -16, 2, 512)
    sample_rate = 44100
    notes = [440.0, 523.25, 659.25, 440.0] # Notes de l'accord de base
    duration_per_note = 0.4
    total_samples = int(len(notes) * duration_per_note * sample_rate)
    buf = array.array('h')
    
    for i in range(total_samples):
        note_idx = int(i / (duration_per_note * sample_rate))
        freq = notes[note_idx]
        t = float(i) / sample_rate
        # Synthèse additive : Fondamentale + Harmonique impaire pour un timbre riche
        val = math.sin(2.0 * math.pi * freq * t) * 0.6 + math.sin(2.0 * math.pi * freq * 3 * t) * 0.1
        volume = 0.1
        local_i = i % int(duration_per_note * sample_rate)
        # Enveloppe ADSR (ici juste Decay) pour un son percutant
        envelope = math.exp(-3.0 * local_i / (duration_per_note * sample_rate))
        sample = int(val * volume * envelope * 32767.0)
        buf.append(sample)
        buf.append(sample)
    try:
        snd = pygame.mixer.Sound(buffer=buf)
        snd.play()
    except Exception:
        pass

def draw_button(screen, rect, color, text, font, hover=False, anim_offset=0):
    """
    Dessine un bouton interactif avec un effet de relief et une animation au survol.
    """
    bg_color = (15, 12, 10)
    base_rect = rect.move(0, anim_offset)
    if hover:
        actual_rect = base_rect.move(0, 3) # Effet d'enclenchement
    else:
        actual_rect = base_rect
        pygame.draw.rect(screen, bg_color, base_rect.move(0, 5), border_radius=8)
    
    pygame.draw.rect(screen, color, actual_rect, border_radius=8)
    # Bordure brillante pour l'esthétique "Premium"
    pygame.draw.rect(screen, (min(255, color[0]+30), min(255, color[1]+30), min(255, color[2]+30)), actual_rect, width=2, border_radius=8)
    
    txt_color = (30, 25, 20) if sum(color) > 400 else (245, 240, 230)
    txt = font.render(text, True, txt_color)
    screen.blit(txt, (actual_rect.centerx - txt.get_width()//2, actual_rect.centery - txt.get_height()//2))

class MenuBackground:
    """
    Gère le fond d'écran animé du menu (Particules et dégradés).
    """
    def __init__(self):
        self.bg_surf = create_bg_surface()
        # Système de particules léger
        self.particles = [[random.uniform(0, 800), random.uniform(0, 600), random.uniform(-0.5, 0.5), random.uniform(-2, -0.5)] for _ in range(40)]
        self.t = 0
        
    def draw(self, screen):
        screen.blit(self.bg_surf, (0, 0))
        self.t += 1
        for p in self.particles:
            p[0] += p[2] + math.sin(self.t*0.02 + p[1]*0.01) * 0.5
            p[1] += p[3]
            if p[1] < 0:
                p[1] = 600
                p[0] = random.uniform(0, 800)
            alpha = max(0, min(255, p[1] * 2))
            s = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(s, (100, 150, 200, int(alpha*0.3)), (2, 2), 2)
            screen.blit(s, (int(p[0]), int(p[1])))

def run_intro_animation(screen):
    """
    Lance l'animation d'introduction 'Splash Screen'.
    """
    generate_intro_music()
    font_logo = pygame.font.SysFont("segoeui", 100, bold=True)
    font_sub = pygame.font.SysFont("segoeui", 30)
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    particles = []
    bg = MenuBackground()
    
    while True:
        dt = pygame.time.get_ticks() - start_time
        if dt > 3500: break
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN: break
                
        bg.draw(screen)
        alpha = min(255, dt / 4)
        scale = 1.0 + math.sin(dt / 500) * 0.05
        
        logo = font_logo.render("QUORIDOR", True, (255, 255, 255))
        logo.set_alpha(int(alpha))
        l_w, l_h = logo.get_size()
        logo_s = pygame.transform.scale(logo, (int(l_w * scale), int(l_h * scale)))
        screen.blit(logo_s, logo_s.get_rect(center=(400, 280)))
        
        if dt > 1500:
            sub = font_sub.render("Projet MASTER 1 GIL", True, (150, 150, 150))
            sub.set_alpha(int(min(255, (dt - 1500) / 3)))
            screen.blit(sub, sub.get_rect(center=(400, 360)))
            
        pygame.display.flip()
        clock.tick(60)

def show_rules(screen, bg):
    """Affiche l'écran des règles du jeu."""
    font_rules = pygame.font.SysFont("segoeui", 22)
    rules = [
        "RÈGLES DE QUORIDOR :",
        "",
        "1. Chaque joueur possède un pion et 10 barrières.",
        "2. Le but est d'atteindre la ligne du bord opposé le premier.",
        "3. À votre tour : avancez d'une case (H/B/G/D) ou placez un mur.",
        "4. Vous pouvez sauter par-dessus l'adversaire s'il vous fait face.",
        "5. L'accès au but ne peut jamais être totalement fermé."
    ]
    running = True
    start_time = pygame.time.get_ticks()
    while running:
        dt = pygame.time.get_ticks() - start_time
        bg.draw(screen)
        for i, line in enumerate(rules):
            if dt > i * 100:
                txt = font_rules.render(line, True, TEXT_COLOR)
                screen.blit(txt, (60, 30 + i*35))
        back_btn = pygame.Rect(300, 500, 200, 60)
        hover = back_btn.collidepoint(pygame.mouse.get_pos())
        draw_button(screen, back_btn, P1_COLOR, "Retour", font_rules, hover=hover)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and hover: running = False

if __name__ == "__main__":
    """Boucle principale du contrôleur de menus."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    run_intro_animation(screen)
    bg = MenuBackground()
    
    while True:
        font_title = pygame.font.SysFont("segoeui", 75, bold=True)
        font_menu = pygame.font.SysFont("segoeui", 32)
        difficulty, mode = 3, "PvAI"
        algo = "alphabeta" # Option par défaut
        
        menu_running = True
        while menu_running:
            bg.draw(screen)
            dt = pygame.time.get_ticks()
            title = font_title.render("QUORIDOR", True, (250, 245, 230))
            screen.blit(title, title.get_rect(center=(400, 60)))
            
            # Définition des boutons du menu (6 boutons maintenant)
            if algo == "sss_star": algo_label = "SSS*"
            elif algo == "adaptive": algo_label = "IA Adaptative"
            else: algo_label = "Alpha-Beta"
            
            btns = [
                (pygame.Rect(200, 140, 400, 55), (230, 170, 80), "JOUER"),
                (pygame.Rect(200, 205, 400, 55), (180, 150, 110), f"Mode: {mode}"),
                (pygame.Rect(200, 270, 400, 55), (160, 130, 90), f"Algo: {algo_label}"),
                (pygame.Rect(200, 335, 400, 55), (150, 120, 85), f"Niveau IA: {difficulty}"),
                (pygame.Rect(200, 400, 400, 55), (140, 110, 80), "Voir une Démo"),
                (pygame.Rect(200, 465, 400, 55), (130, 100, 75), "Règles")
            ]
            
            mouse = pygame.mouse.get_pos()
            for rect, col, txt in btns:
                draw_button(screen, rect, col, txt, font_menu, hover=rect.collidepoint(mouse))
            
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if btns[0][0].collidepoint(event.pos): menu_running = False
                    if btns[1][0].collidepoint(event.pos): mode = "PvP" if mode=="PvAI" else "PvAI"
                    if btns[2][0].collidepoint(event.pos): 
                        # Cycle entre les 3 algos
                        if algo == "alphabeta": algo = "sss_star"
                        elif algo == "sss_star": algo = "adaptive"
                        else: algo = "alphabeta"
                    if btns[3][0].collidepoint(event.pos): difficulty = (difficulty % 4) + 1
                    if btns[4][0].collidepoint(event.pos): mode="AIvAI"; menu_running = False
                    if btns[5][0].collidepoint(event.pos): show_rules(screen, bg)

        # Lancement de la partie
        while True:
            gui = QuoridorGUI(mode=mode, difficulty=difficulty, algo=algo)
            action = gui.run()
            if action == "REPLAY": continue
            else: break
