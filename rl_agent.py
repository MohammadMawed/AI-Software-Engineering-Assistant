import random
import pickle
from database import insert_rl_data, get_connection

class RLAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.experiences = []

    def get_state(self, code_quality_metrics, comparison_result):
        return tuple(code_quality_metrics + [int(comparison_result)])

    def choose_action(self, state, epsilon=0.1):
        if random.uniform(0, 1) < epsilon:
            return random.choice(self.actions)
        self.q_table.setdefault(state, {a: 0.0 for a in self.actions})
        max_q = max(self.q_table[state].values())
        return random.choice([a for a, q in self.q_table[state].items() if q == max_q])

    def learn(self, state, action, reward, next_state):
        self.q_table.setdefault(state, {a: 0.0 for a in self.actions})
        self.q_table.setdefault(next_state, {a: 0.0 for a in self.actions})
        predict = self.q_table[state][action]
        target = reward + self.gamma * max(self.q_table[next_state].values())
        self.q_table[state][action] += self.alpha * (target - predict)
        self.experiences.append((state, action, reward, next_state))

    def save_q_table(self, filename='q_table.pkl'):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load_q_table(self, filename='q_table.pkl'):
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
        except FileNotFoundError:
            pass

    def learn_from_experiences(self, experiences):
        for state, action, reward, next_state in experiences:
            # Convert state and next_state back to tuples if they're lists
            state = tuple(state) if isinstance(state, list) else state
            next_state = tuple(next_state) if isinstance(next_state, list) else next_state
            self.learn(state, action, reward, next_state)
            
            
    def load_experiences_from_db(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT state, action, reward, next_state FROM RLData')
        experiences = cur.fetchall()
        conn.close()
        return experiences

    def retrain(self):
        experiences = self.load_experiences_from_db()
        self.learn_from_experiences(experiences)
