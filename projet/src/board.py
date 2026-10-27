"""
FICHIER : board.py
ROLE : Ce fichier constitue le 'Cœur' ou le 'Modèle' (Model) du jeu Quoridor.
Il gère la structure de données du plateau, les règles de déplacement, 
la validation des murs et l'état du jeu (hachage Zobrist).
"""

import random
from collections import deque

# --- TABLE DE ZOBRIST ---
# Utilisée pour le hachage efficace des configurations du plateau.
# Notion de cours : Permet d'identifier rapidement des positions déjà rencontrées 
# pour les stocker dans les Tables de Transposition (Transposition Tables).
ZOBRIST_TABLE = {}

def init_zobrist():
    """Initialise des nombres aléatoires 64-bits pour chaque composante du jeu."""
    if ZOBRIST_TABLE:
         return
    random.seed(42) # Graine fixe pour la reproductibilité du hachage
    for p in (0, 1): # Pour chaque pion (2 joueurs)
        for r in range(9):
            for c in range(9):
                ZOBRIST_TABLE[('pawn', p, r, c)] = random.getrandbits(64)
    for r in range(8):
        for c in range(8):
            ZOBRIST_TABLE[('wall_h', r, c)] = random.getrandbits(64)
            ZOBRIST_TABLE[('wall_v', r, c)] = random.getrandbits(64)
    ZOBRIST_TABLE['turn'] = random.getrandbits(64)

init_zobrist()

class QuoridorBoard:
    """
    Représente un plateau de Quoridor 9x9.
    Structure de données :
    - pawns : liste de tuples (ligne, colonne)
    - walls_h / walls_v : Ensembles (sets) pour une recherche en O(1)
    - walls_left : Nombre de barrières restantes par joueur
    """
    def __init__(self):
        # player 0 = Joueur 1 (Démarre en bas, monte vers ligne 0)
        # player 1 = Joueur 2 (Démarre en haut, descend vers ligne 8)
        self.pawns = [(8, 4), (0, 4)]
        self.walls_h = set() # Murs horizontaux (indexés par le coin haut-gauche)
        self.walls_v = set() # Murs verticaux (indexés par le coin haut-gauche)
        self.walls_left = [10, 10]
        self.turn = 0 # Joueur dont c'est le tour (0 ou 1)
        
        # Valeur de hachage actuelle pour la Table de Transposition
        self.hash = 0
        self._compute_initial_hash()

    def _compute_initial_hash(self):
        """Calcule le hachage complet initial du plateau."""
        h = 0
        for p, (r, c) in enumerate(self.pawns):
            h ^= ZOBRIST_TABLE[('pawn', p, r, c)]
        if self.turn == 1:
            h ^= ZOBRIST_TABLE['turn']
        self.hash = h

    def is_blocked(self, r, c, nr, nc):
        """
        Vérifie si un mur bloque le passage direct entre (r, c) et (nr, nc).
        Notion de cours : Prédicat de collision utilisé dans le graphe de jeu.
        """
        if nr < 0 or nr >= 9 or nc < 0 or nc >= 9:
            return True
        if nr == r - 1 and nc == c: # Tentative de monter
            return (r - 1, c) in self.walls_h or (r - 1, c - 1) in self.walls_h
        if nr == r + 1 and nc == c: # Tentative de descendre
            return (r, c) in self.walls_h or (r, c - 1) in self.walls_h
        if nc == c - 1 and nr == r: # Tentative d'aller à gauche
            return (r, c - 1) in self.walls_v or (r - 1, c - 1) in self.walls_v
        if nc == c + 1 and nr == r: # Tentative d'aller à droite
            return (r, c) in self.walls_v or (r - 1, c) in self.walls_v
        return False

    def get_valid_pawn_moves(self, player_idx=None):
        """
        Génère les mouvements possibles du pion en respectant les règles :
        - Déplacement simple (H/B/G/D)
        - Saut par-dessus l'adversaire (Jump rule)
        - Bifurcation si le saut direct est bloqué par un mur.
        """
        if player_idx is None:
            player_idx = self.turn
        
        r, c = self.pawns[player_idx]
        opp_r, opp_c = self.pawns[1 - player_idx]
        
        moves = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] # HAUT, BAS, GAUCHE, DROITE
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if nr < 0 or nr >= 9 or nc < 0 or nc >= 9:
                continue
            
            if not self.is_blocked(r, c, nr, nc):
                if (nr, nc) == (opp_r, opp_c):
                    # Cas spécial : Le pion adverse est devant nous
                    nnr, nnc = nr + dr, nc + dc
                    if not self.is_blocked(nr, nc, nnr, nnc) and 0 <= nnr < 9 and 0 <= nnc < 9:
                        # Saut simple
                        moves.append((nnr, nnc))
                    else:
                        # Si le saut simple est impossible (mur ou bord), bifurcation possible
                        if dr != 0: # Mouvement vertical
                            if not self.is_blocked(nr, nc, nr, nc - 1) and nc - 1 >= 0:
                                moves.append((nr, nc - 1))
                            if not self.is_blocked(nr, nc, nr, nc + 1) and nc + 1 < 9:
                                moves.append((nr, nc + 1))
                        else: # Mouvement horizontal
                            if not self.is_blocked(nr, nc, nr - 1, nc) and nr - 1 >= 0:
                                moves.append((nr - 1, nc))
                            if not self.is_blocked(nr, nc, nr + 1, nc) and nr + 1 < 9:
                                moves.append((nr + 1, nc))
                else:
                    # Mouvement classique
                    moves.append((nr, nc))
        return moves

    def is_valid_wall(self, orient, r, c):
        """
        Vérifie la validité d'un mur selon trois critères :
        1. Le joueur a encore des murs.
        2. Le mur n'overlap pas un mur existant et ne croise rien.
        3. Le mur ne bloque pas totalement l'accès au but (Règle d'or de Quoridor).
        """
        if self.walls_left[self.turn] == 0:
            return False
        if r < 0 or r >= 8 or c < 0 or c >= 8:
            return False
            
        if orient == 'H':
            # Vérification de collision horizontale
            if (r, c) in self.walls_h or (r, c - 1) in self.walls_h or (r, c + 1) in self.walls_h:
                return False
            if (r, c) in self.walls_v: # Intersection au centre
                return False
        else: # 'V'
            # Vérification de collision verticale
            if (r, c) in self.walls_v or (r - 1, c) in self.walls_v or (r + 1, c) in self.walls_v:
                return False
            if (r, c) in self.walls_h: # Intersection au centre
                return False
                
        # --- TEST DE CONNEXITÉ ---
        # Temporairement poser le mur pour vérifier si un chemin existe toujours (BFS)
        if orient == 'H':
            self.walls_h.add((r, c))
        else:
            self.walls_v.add((r, c))
            
        p1_can_reach = self.has_path(0)
        p2_can_reach = self.has_path(1)
        
        # Retirer le mur
        if orient == 'H':
            self.walls_h.remove((r, c))
        else:
            self.walls_v.remove((r, c))
            
        return p1_can_reach and p2_can_reach

    def has_path(self, player_idx):
        """
        Utilise un parcours en largeur (BFS) pour vérifier s'il existe un chemin vers la ligne but.
        Notion de cours : Algorithme de recherche de chemin dans un graphe.
        """
        start_r, start_c = self.pawns[player_idx]
        goal_row = 0 if player_idx == 0 else 8
        
        visited = set([(start_r, start_c)])
        queue = deque([(start_r, start_c)])
        
        while queue:
            r, c = queue.popleft()
            if r == goal_row:
                return True
                
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 9 and 0 <= nc < 9 and (nr, nc) not in visited:
                    if not self.is_blocked(r, c, nr, nc):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return False

    def get_shortest_path(self, player_idx):
        """
        Retourne la liste des nœuds constituant le chemin le plus court vers le but.
        Utile pour la visualisation 'Pédagogique'.
        """
        start_r, start_c = self.pawns[player_idx]
        goal_row = 0 if player_idx == 0 else 8
        
        queue = deque([(start_r, start_c, [])])
        visited = set([(start_r, start_c)])
        
        while queue:
            r, c, path = queue.popleft()
            new_path = path + [(r, c)]
            if r == goal_row:
                return new_path
                
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 9 and 0 <= nc < 9 and (nr, nc) not in visited:
                    if not self.is_blocked(r, c, nr, nc):
                        visited.add((nr, nc))
                        queue.append((nr, nc, new_path))
        return []

    def get_valid_wall_moves(self):
        """Répertorie tous les murs posables légalement."""
        moves = []
        if self.walls_left[self.turn] > 0:
            for r in range(8):
                for c in range(8):
                    if self.is_valid_wall('H', r, c):
                        moves.append(('H', r, c))
                    if self.is_valid_wall('V', r, c):
                        moves.append(('V', r, c))
        return moves

    def get_all_valid_moves(self):
        """Combine mouvements de pion et poses de murs pour l'algorithme Alpha-Beta."""
        pawn_moves = [('M', r, c) for (r, c) in self.get_valid_pawn_moves()]
        wall_moves = [('W', orient, r, c) for (orient, r, c) in self.get_valid_wall_moves()]
        return pawn_moves + wall_moves

    def make_move(self, move):
        """
        Applique un coup (Mouvement ou Mur) et met à jour le hachage Zobrist.
        Retourne l'état nécessaire pour l'opération 'Undo'.
        """
        undo_state = {
            'pawns': list(self.pawns),
            'walls_left': list(self.walls_left),
            'hash': self.hash
        }
        
        if move[0] == 'M':
            # Mouvement de pion
            _, nr, nc = move
            old_r, old_c = self.pawns[self.turn]
            self.hash ^= ZOBRIST_TABLE[('pawn', self.turn, old_r, old_c)]
            self.hash ^= ZOBRIST_TABLE[('pawn', self.turn, nr, nc)]
            self.pawns[self.turn] = (nr, nc)
        elif move[0] == 'W':
            # Pose de mur
            _, orient, r, c = move
            if orient == 'H':
                self.walls_h.add((r, c))
                self.hash ^= ZOBRIST_TABLE[('wall_h', r, c)]
            else:
                self.walls_v.add((r, c))
                self.hash ^= ZOBRIST_TABLE[('wall_v', r, c)]
            self.walls_left[self.turn] -= 1
            
        self.turn = 1 - self.turn
        self.hash ^= ZOBRIST_TABLE['turn']
        
        return undo_state

    def undo_move(self, move, undo_state):
        """Annule l'effet d'un coup pour l'exploration de l'arbre (Backtracking)."""
        self.turn = 1 - self.turn
        self.pawns = list(undo_state['pawns'])
        self.walls_left = list(undo_state['walls_left'])
        self.hash = undo_state['hash']
        
        if move[0] == 'W':
            _, orient, r, c = move
            if orient == 'H':
                self.walls_h.remove((r, c))
            else:
                self.walls_v.remove((r, c))

    def copy(self):
        """Crée une copie profonde du plateau."""
        new_b = QuoridorBoard()
        new_b.pawns = list(self.pawns)
        new_b.walls_h = set(self.walls_h)
        new_b.walls_v = set(self.walls_v)
        new_b.walls_left = list(self.walls_left)
        new_b.turn = self.turn
        new_b.hash = self.hash
        return new_b

    def check_winner(self):
        """Vérifie si un joueur a atteint sa ligne de but."""
        if self.pawns[0][0] == 0:
            return 0
        if self.pawns[1][0] == 8:
            return 1
        return None
