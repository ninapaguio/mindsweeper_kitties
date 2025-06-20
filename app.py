from flask import Flask, render_template, request, jsonify, redirect, url_for
import random
from ai import MindSweeperAI

app = Flask(__name__)

games = {}
DIFFICULTIES = {
    'easy': {'grid': '9×9', 'mines': 10, 'confidence': '12.35'},
    'medium': {'grid': '16×16', 'mines': 40, 'confidence': '15.63'},
    'hard': {'grid': '30×16', 'mines': 99, 'confidence': '20.63'}
}

class MindSweeperGame:
    SCORE_CORRECT_FLAG = 10
    SCORE_REVEAL_TILE = 2
    SCORE_PENALTY_MINE = -20
    SCORE_BLANK_TILE = 0
    SCORE_WRONG_FLAG = -4

    def __init__(self, difficulty):
        self.difficulty = difficulty
        self.setup_difficulty()
        self.player_board = [['hidden' for _ in range(self.width)] for _ in range(self.height)]
        self.game_over = False
        self.winner = None
        self.scores = {'human': 0, 'ai': 0}
        self.ai = MindSweeperAI(self.width, self.height, self.mine_count)
        self.first_move = True
        self.board = []
        self.last_moves = {'human': None, 'ai': None}

    def setup_difficulty(self):
        if self.difficulty == 'easy': self.width, self.height, self.mine_count = 9, 9, 10
        elif self.difficulty == 'medium': self.width, self.height, self.mine_count = 16, 16, 40
        else: self.width, self.height, self.mine_count = 30, 16, 99

    def generate_board(self, safe_x, safe_y):
        board = [[0 for _ in range(self.width)] for _ in range(self.height)]
        possible_mine_locations = [i for i in range(self.width * self.height) if (i % self.width, i // self.width) != (safe_x, safe_y)]
        mine_indices = random.sample(possible_mine_locations, self.mine_count)
        for mine_index in mine_indices:
            x, y = mine_index % self.width, mine_index // self.width
            board[y][x] = 'mine'
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0: continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height and board[ny][nx] != 'mine':
                        board[ny][nx] += 1
        return board

    def reveal_tile(self, x, y, player):
        if self.first_move:
            self.board = self.generate_board(safe_x=x, safe_y=y)
            self.first_move = False
        if self.game_over or self.player_board[y][x] != 'hidden': 
            return False

        self.last_moves[player] = ('reveal', x, y)
        score = 0

        # Handle mine hit, which is common for all difficulties
        if self.board[y][x] == 'mine':
            score = self.SCORE_PENALTY_MINE
            self.player_board[y][x] = 'mine'

        # EASY difficulty: one-by-one reveal
        elif self.difficulty == 'easy':
            score = self.SCORE_BLANK_TILE if self.board[y][x] == 0 else self.SCORE_REVEAL_TILE
            self.player_board[y][x] = self.board[y][x]

        # MEDIUM and HARD difficulties: flood-fill reveal
        else:
            q = [(x, y)]
            visited = set([(x, y)])
            while q:
                curr_x, curr_y = q.pop(0)
                if self.player_board[curr_y][curr_x] != 'hidden':
                    continue
                
                cell_value = self.board[curr_y][curr_x]
                self.player_board[curr_y][curr_x] = cell_value
                
                if cell_value == 0:
                    score += self.SCORE_BLANK_TILE
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dx == 0 and dy == 0: continue
                            nx, ny = curr_x + dx, curr_y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited:
                                visited.add((nx, ny))
                                q.append((nx, ny))
                else: # Numbered tile
                    score += self.SCORE_REVEAL_TILE
        
        # Adjust score for simultaneous moves
        if (self.last_moves['human'] and self.last_moves['ai'] and 
            self.last_moves['human'] == self.last_moves['ai']):
            score /= 2

        self.scores[player] += score
        self.check_win_condition()
        return True

    def flag_tile(self, x, y, player):
        if self.game_over or self.player_board[y][x] != 'hidden':
            return False

        self.last_moves[player] = ('flag', x, y)
        self.player_board[y][x] = 'flagged'

        score = self.SCORE_CORRECT_FLAG if self.board[y][x] == 'mine' else self.SCORE_WRONG_FLAG

        if (self.last_moves['human'] and self.last_moves['ai'] and 
            self.last_moves['human'] == self.last_moves['ai']):
            score = score / 2

        self.scores[player] += score
        self.check_win_condition()
        return True

    def calculate_mines_left(self):
        return self.mine_count - sum(row.count('flagged') for row in self.player_board)

    def check_win_condition(self):
        if self.game_over: return

        hidden_tiles_left = sum(row.count('hidden') for row in self.player_board)

        if not self.first_move and hidden_tiles_left == 0:
            self.game_over = True
            if self.scores['human'] > self.scores['ai']: self.winner = 'human'
            elif self.scores['ai'] > self.scores['human']: self.winner = 'ai'
            else: self.winner = 'tie'

            for y in range(self.height):
                for x in range(self.width):
                    if self.player_board[y][x] == 'flagged' and self.board[y][x] != 'mine':
                        self.player_board[y][x] = 'wrong_flag'

    def ai_turn(self):
        if self.game_over: return None
        decision = self.ai.make_decision(self.player_board)
        if decision is None:
            self.check_win_condition()
            return None
        action, x, y = decision
        if (action == 'reveal' and self.player_board[y][x] != 'hidden') or \
           (action == 'flag' and self.player_board[y][x] not in ['hidden', 'flagged']):
            return None
        if action == 'reveal': self.reveal_tile(x, y, 'ai')
        elif action == 'flag': self.flag_tile(x, y, 'ai')
        return {'action': action, 'x': x, 'y': y}

@app.route('/')
def game_setup():
    return render_template('main.html', difficulties=DIFFICULTIES)

@app.route('/start-game', methods=['POST'])
def start_game():
    difficulty = request.form.get('difficulty', 'easy')
    game_id = random.randint(10000, 99999)
    games[game_id] = MindSweeperGame(difficulty)
    return redirect(url_for('play_game', game_id=game_id))

@app.route('/game/<int:game_id>')
def play_game(game_id):
    if game_id not in games: return "Game not found!", 404
    game = games[game_id]
    total_tiles = game.width * game.height
    uniform_conf = game.mine_count / total_tiles
    ai_confidence = [[uniform_conf for _ in range(game.width)] for _ in range(game.height)]
    return render_template(
        'game.html',
        game_id=game_id,
        difficulty=game.difficulty,
        initial_confidence=ai_confidence
    )

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    game_id, x, y, action = data.get('game_id'), data.get('x'), data.get('y'), data.get('action')
    if game_id not in games: return jsonify({'error': 'Invalid game ID'}), 400
    game = games[game_id]
    if game.game_over: return jsonify({'error': 'Game is over'}), 400

    ai_move = None
    human_points = 0
    ai_points = 0

    if action == 'getInfo':
        pass
    elif action == 'reveal':
        old_score = game.scores['human']
        game.reveal_tile(x, y, 'human')
        human_points = game.scores['human'] - old_score
        old_ai_score = game.scores['ai']
        ai_move = game.ai_turn()
        if ai_move:
            ai_points = game.scores['ai'] - old_ai_score
    elif action == 'flag':
        old_score = game.scores['human']
        game.flag_tile(x, y, 'human')
        human_points = game.scores['human'] - old_score
        old_ai_score = game.scores['ai']
        ai_move = game.ai_turn()
        if ai_move:
            ai_points = game.scores['ai'] - old_ai_score
    else:
        return jsonify({'error': 'Invalid action'}), 400

    response = {
        'player_board': game.player_board,
        'scores': game.scores,
        'mines_left': game.calculate_mines_left(),
        'game_over': game.game_over,
        'winner': game.winner,
        'ai_move': ai_move,
        'points_gained': {
            'human': human_points,
            'ai': ai_points
        }
    }

    if data.get('show_confidence'):
        response['ai_confidence'] = game.ai.get_confidence_grid(game.player_board)

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)
