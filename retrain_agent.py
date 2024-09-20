# retrain_agent.py
from rl_agent import RLAgent

def retrain_agent():
    agent = RLAgent(actions=['action1', 'action2'])
    agent.load_q_table()
    agent.retrain()
    agent.save_q_table()

if __name__ == "__main__":
    retrain_agent()
