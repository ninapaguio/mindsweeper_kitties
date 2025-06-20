import random

class MindSweeperAI:
    def __init__(self, width, height, mine_count):
        self.width = width
        self.height = height
        self.total_mines = mine_count

    def get_neighbors(self, x, y):
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    neighbors.append((nx, ny))
        return neighbors

    def _find_frontier_and_constraints(self, board):
        frontier = set()
        constraints = []
        for y in range(self.height):
            for x in range(self.width):
                cell = board[y][x]
                if isinstance(cell, int) and cell > 0:
                    neighbors = self.get_neighbors(x, y)
                    hidden_neighbors = {n for n in neighbors if board[n[1]][n[0]] == 'hidden'}
                    if hidden_neighbors:
                        flagged_count = sum(1 for n in neighbors if board[n[1]][n[0]] == 'flagged')
                        constraints.append({'coords': (x, y), 'value': cell - flagged_count, 'neighbors': hidden_neighbors})
                        frontier.update(hidden_neighbors)
        return list(frontier), constraints

    def _solve_constraints(self, frontier, constraints, mines_left):
        frontier_map = {coord: i for i, coord in enumerate(frontier)}
        num_frontier_tiles = len(frontier)
        mine_counts = [0] * num_frontier_tiles
        total_solutions = 0
        
        def check_consistency(assignment):
            for con in constraints:
                assigned_mines_count = sum(1 for neighbor in con['neighbors'] if assignment[frontier_map[neighbor]] == 1)
                if assigned_mines_count != con['value']:
                    return False
            return True

        def backtrack(index, num_mines_placed, assignment):
            nonlocal total_solutions
            if num_mines_placed > mines_left: return
            if index == num_frontier_tiles:
                if check_consistency(assignment):
                    total_solutions += 1
                    for i in range(num_frontier_tiles):
                        if assignment[i] == 1:
                            mine_counts[i] += 1
                return
            assignment[index] = 1
            backtrack(index + 1, num_mines_placed + 1, assignment)
            assignment[index] = 0
            backtrack(index + 1, num_mines_placed, assignment)
            
        if num_frontier_tiles > 0 and num_frontier_tiles < 18:
             backtrack(0, 0, [0] * num_frontier_tiles)
        return mine_counts, total_solutions
    
    # *** NEW PUBLIC METHOD FOR CONFIDENCE ***
    def get_confidence_grid(self, board):
        """Calculates and returns a full grid of mine probabilities."""
        confidence_grid = [[-1.0 for _ in range(self.width)] for _ in range(self.height)]
        mines_left = self.total_mines - sum(row.count('flagged') for row in board)
        
        frontier, constraints = self._find_frontier_and_constraints(board)
        
        if not frontier:
            return confidence_grid # Return empty grid if no frontier

        mine_counts, total_solutions = self._solve_constraints(frontier, constraints, mines_left)

        if total_solutions > 0:
            for i, (x, y) in enumerate(frontier):
                confidence_grid[y][x] = mine_counts[i] / total_solutions
        
        return confidence_grid

    def make_decision(self, board):
        # 1. Quick check for trivial moves
        for y in range(self.height):
            for x in range(self.width):
                cell = board[y][x]
                if isinstance(cell, int) and cell > 0:
                    neighbors = self.get_neighbors(x, y)
                    hidden_neighbors = [n for n in neighbors if board[n[1]][n[0]] == 'hidden']
                    flagged_neighbors_count = sum(1 for n in neighbors if board[n[1]][n[0]] == 'flagged')
                    if cell == flagged_neighbors_count and hidden_neighbors:
                        return 'reveal', hidden_neighbors[0][0], hidden_neighbors[0][1]
                    if cell - flagged_neighbors_count == len(hidden_neighbors) and hidden_neighbors:
                        return 'flag', hidden_neighbors[0][0], hidden_neighbors[0][1]

        # 2. Belief-state analysis
        frontier, constraints = self._find_frontier_and_constraints(board)
        if not frontier:
            hidden_tiles = [(x, y) for y in range(self.height) for x in range(self.width) if board[y][x] == 'hidden']
            if hidden_tiles:
                return 'reveal', *random.choice(hidden_tiles)
            return None 

        mines_left = self.total_mines - sum(row.count('flagged') for row in board)
        mine_counts, total_solutions = self._solve_constraints(frontier, constraints, mines_left)
        
        if total_solutions > 0:
            min_prob, best_reveal = 1.0, None
            for i, (x, y) in enumerate(frontier):
                prob = mine_counts[i] / total_solutions
                if prob == 0: return 'reveal', x, y
                if prob == 1: return 'flag', x, y
                if prob < min_prob:
                    min_prob, best_reveal = prob, (x, y)
            if best_reveal:
                return 'reveal', *best_reveal

        if frontier:
            return 'reveal', *random.choice(frontier)
        
        return None