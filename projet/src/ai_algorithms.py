"""
FICHIER : ai_algorithms.py
ROLE : Ce fichier contient le cerveau de l'IA.
On y implémente les algorithmes de recherche dans l'arbre de jeu :
- MiniMax avec élagage Alpha-Beta
- Negamax (version simplifiée de MiniMax)
- SSS* (State-Space Search)
- Tables de Transposition pour la mémorisation
"""

import heapq
import time
from .heuristics import evaluate_board

class TranspositionTable:
    """
    Structure de données pour mémoriser les évaluations des positions déjà rencontrées.
    Notion de cours : Permet d'éviter de recalculer des branches redondantes 
    (cas de 'transpositions' où différents chemins mènent au même état).
    """
    def __init__(self):
        self.table = {}

    def store(self, hash_val, depth, score, flag, best_move):
        self.table[hash_val] = (depth, score, flag, best_move)

    def probe(self, hash_val, depth, alpha, beta):
        if hash_val in self.table:
            d, score, flag, best_move = self.table[hash_val]
            if d >= depth:
                if flag == 'EXACT':
                    return score, best_move
                elif flag == 'LOWERBOUND' and score >= beta:
                    return score, best_move
                elif flag == 'UPPERBOUND' and score <= alpha:
                    return score, best_move
        return None, None

def order_moves(board, moves):
    """
    Heuristique d'ordonnancement des coups améliorée.
    Priorise les mouvements qui rapprochent physiquement du but.
    """
    p_idx = board.turn
    goal_row = 0 if p_idx == 0 else 8
    
    def move_priority(m):
        if m[0] == 'M':
            # Plus on se rapproche de goal_row, plus la priorité est haute (score bas pour sorted)
            dist_to_goal = abs(m[1] - goal_row)
            return (0, dist_to_goal) 
        return (1, 0) # Les murs passent après les mouvements de pions prometteurs

    return sorted(moves, key=move_priority)

def minimax_alpha_beta(board, depth, alpha, beta, maximizing_player, maximizing_player_idx, tt=None, end_time=None, pos_history=None):
    """
    Algorithme MiniMax avec Élagage Alpha-Beta.
    Notion de cours : Réduit le nombre de nœuds visités sans changer le résultat final.
    - Alpha : Meilleur score déjà garanti pour le joueur Max.
    - Beta : Meilleur score déjà garanti pour le joueur Min.
    """
    winner = board.check_winner()
    if winner is not None:
        if winner == maximizing_player_idx:
            return 10000 + depth, None
        else:
            return -10000 - depth, None

    if depth == 0 or (end_time and time.time() > end_time):
        score = evaluate_board(board, maximizing_player_idx)
        # Pénalité de répétition : si la position actuelle a déjà été visitée, on la pénalise
        if pos_history:
            key = (tuple(board.pawns[0]), tuple(board.pawns[1]))
            if pos_history.get(key, 0) >= 2:
                score -= 5.0 * pos_history[key]  # Pénalité progressive
        return score, None

    hash_val = board.hash
    if tt:
        tt_score, tt_move = tt.probe(hash_val, depth, alpha, beta)
        if tt_score is not None:
            return tt_score, tt_move

    moves = order_moves(board, board.get_all_valid_moves())
    if not moves:
        return evaluate_board(board, maximizing_player_idx), None

    best_move = moves[0]
    
    if maximizing_player:
        max_eval = -float('inf')
        for move in moves:
            undo = board.make_move(move)
            eval_score, _ = minimax_alpha_beta(board, depth - 1, alpha, beta, False, maximizing_player_idx, tt, end_time, pos_history)
            board.undo_move(move, undo)
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
                
        if tt:
            flag = 'EXACT'
            if max_eval <= alpha: flag = 'UPPERBOUND'
            elif max_eval >= beta: flag = 'LOWERBOUND'
            tt.store(hash_val, depth, max_eval, flag, best_move)
            
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            undo = board.make_move(move)
            eval_score, _ = minimax_alpha_beta(board, depth - 1, alpha, beta, True, maximizing_player_idx, tt, end_time, pos_history)
            board.undo_move(move, undo)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
                
        if tt:
            flag = 'EXACT'
            if min_eval <= alpha: flag = 'UPPERBOUND'
            elif min_eval >= beta: flag = 'LOWERBOUND'
            tt.store(hash_val, depth, min_eval, flag, best_move)
            
        return min_eval, best_move

def negamax(board, depth, alpha, beta, color, maximizing_player_idx, tt=None):
    """
    Algorithme Negamax.
    Notion de cours : Variante de MiniMax basée sur la propriété Max(a, b) = -Min(-a, -b).
    Cela simplifie le code en utilisant une seule branche logique au lieu de deux (Max/Min).
    """
    winner = board.check_winner()
    if winner is not None:
        if winner == board.turn:
            return (10000 + depth), None
        else:
            return (-10000 - depth), None

    if depth == 0:
        return evaluate_board(board, board.turn), None

    hash_val = board.hash
    if tt:
        tt_score, tt_move = tt.probe(hash_val, depth, alpha, beta)
        if tt_score is not None:
            return tt_score, tt_move

    moves = order_moves(board, board.get_all_valid_moves())
    best_value = -float('inf')
    best_move = moves[0] if moves else None

    for move in moves:
        undo = board.make_move(move)
        val, _ = negamax(board, depth - 1, -beta, -alpha, -color, maximizing_player_idx, tt)
        val = -val
        board.undo_move(move, undo)
        
        if val > best_value:
            best_value = val
            best_move = move
        
        alpha = max(alpha, val)
        if alpha >= beta:
            break

    if tt:
        flag = 'EXACT'
        if best_value <= alpha: flag = 'UPPERBOUND'
        elif best_value >= beta: flag = 'LOWERBOUND'
        tt.store(hash_val, depth, best_value, flag, best_move)

    return best_value, best_move

def sss_star(board, maximizing_player_idx, depth_limit):
    """
    Algorithme SSS* (State-Space Search).
    Notion de cours : Utilise une file de priorité pour explorer l'arbre de jeu 
    en mode 'Best-First'. Il est souvent considéré comme plus efficace qu'Alpha-Beta 
    car il n'examine jamais un nœud qui ne peut pas améliorer la solution actuelle.
    """
    # Implémentation simplifiée par recherche Best-First guidée par l'heuristique.
    moves = board.get_all_valid_moves()
    pq = []
    
    for move in moves:
        undo = board.make_move(move)
        score = evaluate_board(board, maximizing_player_idx)
        board.undo_move(move, undo)
        # SSS* explore les meilleurs scores en priorité
        heapq.heappush(pq, (-score, move))
    
    if not pq:
        return moves[0] if moves else None
    
    # On prend le meilleur coup immédiat selon SSS*
    _, best_move = heapq.heappop(pq)
    return best_move

def adaptive_search(board, depth, maximizing_player_idx):
    """
    Arbitre hybride (IA Adaptative).
    Notion de cours : Sélection dynamique d'algorithme selon le contexte de jeu 
    (Algorithm Selection Problem).
    - Début de partie (< 10 murs) : Alpha-Beta pour sa vitesse d'élagage.
    - Fin de partie (>= 10 murs) : SSS* pour sa précision en labyrinthe.
    """
    total_walls = len(board.walls_h) + len(board.walls_v)
    if total_walls < 5:
        # Phase d'ouverture : Alpha-Beta est plus efficace sur plateau dégagé
        move = iterative_deepening(board, depth, algo='alphabeta', maximizing_player_idx=maximizing_player_idx)
        return move, "Alpha-Beta"
    else:
        # Phase labyrinthique : Recherche de chemin prioritaire
        move = sss_star(board, maximizing_player_idx, depth)
        return move, "SSS*"

def iterative_deepening(board, max_depth, algo='alphabeta', maximizing_player_idx=1, pos_history=None):
    """
    Approfondissement Itératif avec limite de temps et détection de répétition.
    pos_history : dictionnaire {(pos_p0, pos_p1): count} des positions récentes pour éviter les oscillations.
    """
    tt = TranspositionTable()
    start_time = time.time()
    time_limit = 1.5
    end_time = start_time + time_limit
    
    moves = board.get_all_valid_moves()
    best_move = moves[0] if moves else None
    
    if algo == 'sss_star':
        return sss_star(board, maximizing_player_idx, max_depth)
        
    for d in range(1, max_depth + 1):
        if algo == 'alphabeta':
            _, move = minimax_alpha_beta(board, d, -float('inf'), float('inf'), True, maximizing_player_idx, tt, end_time, pos_history)
        elif algo == 'negamax':
            _, move = negamax(board, d, -float('inf'), float('inf'), 1, maximizing_player_idx, tt)
        
        if move:
            best_move = move
        
        if time.time() > end_time:
            break
            
    return best_move
