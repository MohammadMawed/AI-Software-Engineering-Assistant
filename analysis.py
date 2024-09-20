# analysis.py
import matplotlib.pyplot as plt
from database import get_all_rl_data

def plot_rewards_over_time():
    rl_data = get_all_rl_data()
    rewards = [record['reward'] for record in rl_data]
    timestamps = [record['timestamp'] for record in rl_data]
    plt.plot(timestamps, rewards)
    plt.xlabel('Time')
    plt.ylabel('Reward')
    plt.title('Rewards Over Time')
    plt.show()
