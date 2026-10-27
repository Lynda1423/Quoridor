"""
FICHIER : heuristics.py
ROLE : Ce fichier contient les fonctions d'évaluation (Heuristiques).
Une heuristique est une estimation de la 'qualité' d'une position donnée.
Notion de cours : Utilisation de la distance de Manhattan modifiée (BFS) 
pour guider l'algorithme Alpha-Beta.
"""

from collections import deque

def shortest_path_distance(board, player_idx):
    """
    Calcule la distance minimale séparant un joueur de sa ligne de but.
    Algorithme : Parcours en largeur (BFS).
    Complexité : O(V + E) où V=81 cases et E=environ 320 arêtes.
    Incidence pédagogique : Plus la distance est faible, meilleure est la position.
    """
    start_r, start_c = board.pawns[player_idx]
    goal_row = 0 if player_idx == 0 else 8
    
    if start_r == goal_row:
        return 0
        
    visited = set([(start_r, start_c)])
    queue = deque([(start_r, start_c, 0)])
    
    while queue:
        r, c, dist = queue.popleft()
        
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 9 and 0 <= nc < 9 and (nr, nc) not in visited:
                if not board.is_blocked(r, c, nr, nc):
                    if nr == goal_row:
                        return dist + 1
                    visited.add((nr, nc))
                    queue.append((nr, nc, dist + 1))
    return 999  # Position bloquée (théoriquement impossible par les règles)

def evaluate_board(board, maximizing_player_idx):
    """
    Fonction d'évaluation principale (Heuristique combinée).
    Score = (Distance adversaire - Ma distance) + Bonus Murs
    
    Notion de cours : Une évaluation doit être rapide car elle est appelée
    des milliers de fois par l'algorithme de recherche (Alpha-Beta/SSS*).
    """
    p0_dist = shortest_path_distance(board, 0)
    p1_dist = shortest_path_distance(board, 1)
    
    # On cherche à minimiser sa propre distance et maximiser celle de l'adversaire.
    if maximizing_player_idx == 0:
        # Score positif si P1 est plus proche de gagner que P2
        score = p1_dist - p0_dist
    else:
        # Score positif si P2 est plus proche de gagner que P1
        score = p0_dist - p1_dist
        
    # Bonus stratégique : Garder des murs en réserve.
    wall_bonus = (board.walls_left[maximizing_player_idx] - board.walls_left[1 - maximizing_player_idx]) * 0.5
    
    # Bonus de Progression (Anti-oscillation) : 
    # Force l'IA à avancer physiquement même si le chemin BFS (murs) semble identique.
    r0, c0 = board.pawns[0]
    r1, c1 = board.pawns[1]
    
    # Poids de la progression verticale augmenté (0.1 -> 0.8)
    prog0 = (8 - r0) * 0.8
    prog1 = r1 * 0.8
    
    # Bonus de centralité (évite de tourner en bourrique sur les bords)
    center_bonus0 = (4 - abs(4 - c0)) * 0.1
    center_bonus1 = (4 - abs(4 - c1)) * 0.1
    
    if maximizing_player_idx == 0:
        progression_bonus = (prog0 + center_bonus0) - (prog1 + center_bonus1)
    else:
        progression_bonus = (prog1 + center_bonus1) - (prog0 + center_bonus0)

    return score + wall_bonus + progression_bonus
