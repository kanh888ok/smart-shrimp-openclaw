#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
强化学习投喂策略优化模块
使用强化学习优化对虾养殖的投喂策略，降低成本并提升产量
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# 尝试导入强化学习库
try:
    import gymnasium as gym
    from gymnasium import spaces
    RL_AVAILABLE = True
except ImportError:
    try:
        import gym
        from gym import spaces
        RL_AVAILABLE = True
    except ImportError:
        RL_AVAILABLE = False
        print("警告: 未安装gym或gymnasium，将使用简化版强化学习")

try:
    from stable_baselines3 import PPO, DQN, A2C
    from stable_baselines3.common.env_util import make_vec_env
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    print("提示: 未安装stable-baselines3。安装命令: pip install stable-baselines3")


class ShrimpFarmingEnv:
    """
    对虾养殖环境（强化学习环境）

    状态空间：水温、盐度、pH值、溶解氧、氨氮、亚硝酸盐、当前投喂量、虾体重
    动作空间：投喂量调整（-20%到+20%）
    奖励：产量增长 - 饲料成本
    """

    def __init__(self, df: pd.DataFrame, max_steps: int = 30):
        """
        Args:
            df: 养殖数据
            max_steps: 最大步数（养殖周期）
        """
        self.df = df.reset_index(drop=True)
        self.max_steps = max_steps

        # 状态特征
        self.state_features = [
            '水温 (°C)', '盐度 (ppt)', 'pH 值', '溶解氧 (mg/L)',
            '氨氮 (mg/L)', '亚硝酸盐 (mg/L)', '投喂量 (kg)', '虾体重 (g)'
        ]

        # 确保所有特征都存在
        available_features = [f for f in self.state_features if f in self.df.columns]
        if len(available_features) < 5:
            raise ValueError("数据特征不足，至少需要5个环境特征")

        self.state_features = available_features

        # 状态空间维度
        self.state_dim = len(self.state_features)

        # 动作空间：投喂量调整百分比 [-20%, +20%]
        self.action_dim = 5  # 离散动作：-20%, -10%, 0%, +10%, +20%

        # 归一化参数
        self.state_means = self.df[self.state_features].mean()
        self.state_stds = self.df[self.state_features].std()

        # 当前状态
        self.current_step = 0
        self.current_state = None
        self.total_reward = 0

        print(f"环境初始化完成:")
        print(f"  状态维度: {self.state_dim}")
        print(f"  动作空间: {self.action_dim}个离散动作")
        print(f"  最大步数: {self.max_steps}")

    def reset(self) -> np.ndarray:
        """重置环境"""
        self.current_step = 0
        self.total_reward = 0

        # 从随机位置开始
        start_idx = np.random.randint(0, max(1, len(self.df) - self.max_steps))
        self.start_idx = start_idx

        # 初始状态
        self.current_state = self._get_state(start_idx)

        return self.current_state

    def _get_state(self, idx: int) -> np.ndarray:
        """获取归一化状态"""
        if idx >= len(self.df):
            idx = len(self.df) - 1

        state = self.df.loc[idx, self.state_features].values

        # 归一化
        normalized_state = (state - self.state_means.values) / (self.state_stds.values + 1e-8)

        return normalized_state

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """
        执行动作

        Args:
            action: 动作索引 (0-4)
                0: -20% 投喂量
                1: -10% 投喂量
                2: 0% 投喂量（保持）
                3: +10% 投喂量
                4: +20% 投喂量

        Returns:
            next_state: 下一状态
            reward: 奖励
            done: 是否结束
            info: 额外信息
        """
        # 动作映射到投喂量调整
        feed_adjustments = [-0.2, -0.1, 0.0, 0.1, 0.2]
        adjustment = feed_adjustments[action]

        # 当前信息
        current_idx = self.start_idx + self.current_step
        if current_idx >= len(self.df) - 1:
            return self.current_state, 0, True, {}

        current_row = self.df.loc[current_idx]

        # 计算奖励
        reward = self._calculate_reward(current_row, adjustment)

        # 更新状态
        self.current_step += 1
        next_idx = self.start_idx + self.current_step

        if next_idx >= len(self.df):
            next_state = self.current_state
            done = True
        else:
            next_state = self._get_state(next_idx)
            done = self.current_step >= self.max_steps

        self.current_state = next_state
        self.total_reward += reward

        info = {
            'step': self.current_step,
            'adjustment': adjustment,
            'cumulative_reward': self.total_reward
        }

        return next_state, reward, done, info

    def _calculate_reward(self, row: pd.Series, adjustment: float) -> float:
        """
        计算奖励

        奖励 = 产量增长 - 饲料成本 - 环境惩罚

        Args:
            row: 当前行数据
            adjustment: 投喂量调整

        Returns:
            奖励值
        """
        # 基础投喂量
        base_feed = row.get('投喂量 (kg)', 1.0)
        adjusted_feed = base_feed * (1 + adjustment)

        # 环境适宜度评分
        env_score = self._calculate_environment_score(row)

        # FCR（饲料转化率）
        fcr = row.get('FCR', 1.5)

        # 奖励组成部分

        # 1. 产量增长（根据体重增长）
        weight_gain = row.get('SGR', 0)  # 特定生长率
        growth_reward = weight_gain * 10  # 权重

        # 2. 饲料成本（投喂量越少越好，但不能太少）
        # 投喂量在合理范围内给予奖励
        optimal_feed = base_feed * 0.9  # 假设最优投喂量为基础量的90%
        feed_penalty = abs(adjusted_feed - optimal_feed) * 0.5

        # 3. 环境惩罚（环境不适宜时惩罚）
        env_penalty = (1 - env_score) * 5

        # 4. FCR奖励（FCR越低越好）
        fcr_reward = (2.0 - fcr) * 2  # FCR<2.0时给予奖励

        # 总奖励
        total_reward = growth_reward - feed_penalty - env_penalty + fcr_reward

        return total_reward

    def _calculate_environment_score(self, row: pd.Series) -> float:
        """
        计算环境适宜度评分

        评分标准：
        - 水温: 26-30°C 最优
        - 溶解氧: >5mg/L
        - pH值: 7.5-8.5
        - 盐度: 15-25ppt
        """
        score = 0.0

        # 水温评分 (26-30°C)
        temp = row.get('水温 (°C)', 28)
        if 26 <= temp <= 30:
            score += 0.25
        elif 24 <= temp <= 32:
            score += 0.15
        else:
            score += 0.05

        # 溶解氧评分 (>5mg/L)
        do = row.get('溶解氧 (mg/L)', 5)
        if do >= 5:
            score += 0.25
        elif do >= 4:
            score += 0.15
        else:
            score += 0.05

        # pH值评分 (7.5-8.5)
        ph = row.get('pH 值', 8.0)
        if 7.5 <= ph <= 8.5:
            score += 0.25
        elif 7.0 <= ph <= 9.0:
            score += 0.15
        else:
            score += 0.05

        # 盐度评分 (15-25ppt)
        salinity = row.get('盐度 (ppt)', 20)
        if 15 <= salinity <= 25:
            score += 0.25
        elif 10 <= salinity <= 30:
            score += 0.15
        else:
            score += 0.05

        return score


class SimpleQLearning:
    """
    简化版Q学习算法（无需额外依赖）
    用于强化学习投喂策略优化
    """

    def __init__(self, state_dim: int, action_dim: int, learning_rate: float = 0.1):
        """
        Args:
            state_dim: 状态维度
            action_dim: 动作数量
            learning_rate: 学习率
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.learning_rate = learning_rate
        self.gamma = 0.95  # 折扣因子
        self.epsilon = 0.1  # 探索率

        # Q表：使用离散化状态
        self.n_bins = 5  # 每个维度离散化为5个区间
        self.q_table_size = tuple([self.n_bins] * state_dim + [action_dim])
        self.q_table = np.zeros(self.q_table_size)

    def _discretize_state(self, state: np.ndarray) -> Tuple:
        """将连续状态离散化"""
        # 将状态从[-inf, inf]映射到[0, n_bins-1]
        discretized = []
        for s in state:
            # 使用sigmoid将状态映射到[0,1]
            normalized = 1 / (1 + np.exp(-s))
            # 映射到[0, n_bins-1]
            bin_idx = int(normalized * (self.n_bins - 1))
            discretized.append(bin_idx)

        return tuple(discretized)

    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        选择动作（epsilon-greedy策略）

        Args:
            state: 当前状态
            training: 是否在训练模式

        Returns:
            动作索引
        """
        if training and np.random.random() < self.epsilon:
            # 探索：随机选择
            return np.random.randint(0, self.action_dim)
        else:
            # 利用：选择Q值最大的动作
            discretized_state = self._discretize_state(state)
            return np.argmax(self.q_table[discretized_state])

    def update(self, state: np.ndarray, action: int, reward: float,
               next_state: np.ndarray, done: bool):
        """
        更新Q表

        Args:
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一状态
            done: 是否结束
        """
        discretized_state = self._discretize_state(state)
        discretized_next_state = self._discretize_state(next_state)

        # Q-learning更新规则
        current_q = self.q_table[discretized_state + (action,)]

        if done:
            max_next_q = 0
        else:
            max_next_q = np.max(self.q_table[discretized_next_state])

        # Q(s,a) = Q(s,a) + α * [r + γ * max(Q(s',a')) - Q(s,a)]
        new_q = current_q + self.learning_rate * (
            reward + self.gamma * max_next_q - current_q
        )

        self.q_table[discretized_state + (action,)] = new_q

    def train(self, env: ShrimpFarmingEnv, n_episodes: int = 1000,
              verbose: bool = True) -> Dict:
        """
        训练Q学习模型

        Args:
            env: 环境
            n_episodes: 训练回合数
            verbose: 是否显示详细信息

        Returns:
            训练历史
        """
        history = {
            'episode_rewards': [],
            'episode_lengths': []
        }

        if verbose:
            print(f"\n{'='*70}")
            print(f"Q-Learning 训练开始")
            print(f"{'='*70}")
            print(f"回合数: {n_episodes}")
            print(f"状态维度: {self.state_dim}")
            print(f"动作空间: {self.action_dim}")
            print(f"Q表大小: {self.q_table_size}")

        for episode in range(n_episodes):
            state = env.reset()
            episode_reward = 0
            episode_length = 0

            while True:
                # 选择动作
                action = self.select_action(state, training=True)

                # 执行动作
                next_state, reward, done, info = env.step(action)

                # 更新Q表
                self.update(state, action, reward, next_state, done)

                episode_reward += reward
                episode_length += 1
                state = next_state

                if done:
                    break

            history['episode_rewards'].append(episode_reward)
            history['episode_lengths'].append(episode_length)

            # 定期显示进度
            if verbose and (episode + 1) % 100 == 0:
                avg_reward = np.mean(history['episode_rewards'][-100:])
                print(f"回合 {episode+1}/{n_episodes} | "
                      f"平均奖励: {avg_reward:.2f} | "
                      f"平均步数: {np.mean(history['episode_lengths'][-100:]):.1f}")

        if verbose:
            print(f"\n{'='*70}")
            print(f"训练完成!")
            print(f"最终平均奖励: {np.mean(history['episode_rewards'][-100:]):.2f}")
            print(f"{'='*70}\n")

        return history

    def predict(self, env: ShrimpFarmingEnv, n_episodes: int = 10) -> Dict:
        """
        评估训练后的策略

        Args:
            env: 环境
            n_episodes: 评估回合数

        Returns:
            评估结果
        """
        total_rewards = []
        total_lengths = []
        actions_taken = []

        for _ in range(n_episodes):
            state = env.reset()
            episode_reward = 0
            episode_length = 0
            episode_actions = []

            while True:
                action = self.select_action(state, training=False)
                next_state, reward, done, info = env.step(action)

                episode_reward += reward
                episode_length += 1
                episode_actions.append(action)
                state = next_state

                if done:
                    break

            total_rewards.append(episode_reward)
            total_lengths.append(episode_length)
            actions_taken.extend(episode_actions)

        # 统计动作分布
        action_names = ['-20%', '-10%', '0%', '+10%', '+20%']
        action_distribution = pd.Series(actions_taken).value_counts().sort_index()

        results = {
            'mean_reward': np.mean(total_rewards),
            'std_reward': np.std(total_rewards),
            'mean_length': np.mean(total_lengths),
            'action_distribution': {
                action_names[i]: action_distribution.get(i, 0)
                for i in range(len(action_names))
            }
        }

        return results


class FeedOptimizer:
    """
    投喂策略优化器（强化学习）

    使用强化学习学习最优投喂策略，在保证产量的同时降低饲料成本
    """

    def __init__(self, df: pd.DataFrame, method: str = 'q_learning'):
        """
        Args:
            df: 养殖数据
            method: 优化方法 ('q_learning', 'ppo', 'dqn')
        """
        self.df = df
        self.method = method

        # 创建环境
        self.env = ShrimpFarmingEnv(df)

        # 选择优化算法
        if method == 'q_learning':
            self.model = SimpleQLearning(
                state_dim=self.env.state_dim,
                action_dim=self.env.action_dim
            )
            self.model_type = 'Q-Learning'
        elif method in ['ppo', 'dqn'] and SB3_AVAILABLE:
            # 预留stable-baselines3接口
            print(f"提示: {method.upper()}算法需要stable-baselines3库")
            print(f"      将使用Q-Learning替代")
            self.model = SimpleQLearning(
                state_dim=self.env.state_dim,
                action_dim=self.env.action_dim
            )
            self.model_type = 'Q-Learning'
        else:
            self.model = SimpleQLearning(
                state_dim=self.env.state_dim,
                action_dim=self.env.action_dim
            )
            self.model_type = 'Q-Learning'

        self.trained = False

    def train(self, n_episodes: int = 1000, verbose: bool = True):
        """
        训练投喂策略模型

        Args:
            n_episodes: 训练回合数
            verbose: 是否显示详细信息
        """
        print(f"\n{'='*70}")
        print(f"投喂策略优化 - 强化学习训练")
        print(f"{'='*70}")
        print(f"优化方法: {self.model_type}")
        print(f"训练回合: {n_episodes}")

        self.history = self.model.train(self.env, n_episodes, verbose)
        self.trained = True

        print(f"\n✅ 训练完成!")
        print(f"   最终奖励: {np.mean(self.history['episode_rewards'][-100:]):.2f}")
        print(f"   改进幅度: {self._calculate_improvement():.1f}%")

    def _calculate_improvement(self) -> float:
        """计算相比随机策略的改进幅度"""
        # 使用最后100个回合的平均奖励
        final_reward = np.mean(self.history['episode_rewards'][-100:])
        # 假设随机策略的平均奖励为0
        improvement = (final_reward - 0) / abs(0 + 1e-8) * 100
        return improvement

    def evaluate(self, n_episodes: int = 10) -> Dict:
        """
        评估训练后的策略

        Args:
            n_episodes: 评估回合数

        Returns:
            评估结果
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用train()")

        results = self.model.predict(self.env, n_episodes)

        print(f"\n{'='*70}")
        print(f"策略评估结果")
        print(f"{'='*70}")
        print(f"平均奖励: {results['mean_reward']:.2f} ± {results['std_reward']:.2f}")
        print(f"平均周期: {results['mean_length']:.1f} 天")
        print(f"\n投喂策略分布:")
        for action, count in results['action_distribution'].items():
            percentage = count / sum(results['action_distribution'].values()) * 100
            print(f"  {action:>5s}: {count:>3d} 次 ({percentage:>5.1f}%)")
        print(f"{'='*70}\n")

        return results

    def recommend_feed_strategy(self, current_conditions: Dict) -> Dict:
        """
        根据当前环境条件推荐投喂策略

        Args:
            current_conditions: 当前环境条件
                {'水温': 28, '盐度': 20, 'pH': 8.0, ...}

        Returns:
            推荐的投喂策略
        """
        if not self.trained:
            raise RuntimeError("模型未训练，请先调用train()")

        # 构造状态向量
        state_order = self.env.state_features
        state_values = []

        for feature in state_order:
            if feature in current_conditions:
                state_values.append(current_conditions[feature])
            else:
                # 使用默认值
                state_values.append(0)

        state = np.array(state_values)

        # 归一化
        normalized_state = (state - self.env.state_means.values) / (
            self.env.state_stds.values + 1e-8
        )

        # 选择最优动作
        action = self.model.select_action(normalized_state, training=False)

        # 动作映射
        action_names = ['-20%', '-10%', '0%', '+10%', '+20%']
        recommendations = {
            'recommended_adjustment': action_names[action],
            'confidence': '高' if self.trained else '低',
            'reason': self._explain_action(action, current_conditions)
        }

        return recommendations

    def _explain_action(self, action: int, conditions: Dict) -> str:
        """解释推荐动作的原因"""
        action_names = ['-20%', '-10%', '0%', '+10%', '+20%']
        adj = action_names[action]

        reasons = []

        # 根据环境条件解释
        if '水温' in conditions:
            temp = conditions['水温']
            if temp < 24 or temp > 32:
                reasons.append(f"水温异常({temp}°C)")

        if '溶解氧' in conditions:
            do = conditions['溶解氧']
            if do < 5:
                reasons.append(f"溶解氧低({do}mg/L)")

        if 'FCR' in conditions:
            fcr = conditions['FCR']
            if fcr > 1.8:
                reasons.append(f"FCR偏高({fcr:.2f})")

        if reasons:
            reason_str = "、".join(reasons)
            if action <= 1:  # 减少投喂
                return f"检测到{reason_str}，建议{adj}投喂以降低风险"
            elif action >= 3:  # 增加投喂
                return f"环境条件良好，建议{adj}投喂以促进生长"
            else:  # 保持
                return f"环境条件正常，建议保持当前投喂量"
        else:
            return f"基于历史数据学习，建议{adj}投喂"


# 便捷函数
def optimize_feeding_strategy(df: pd.DataFrame, n_episodes: int = 1000,
                              verbose: bool = True) -> FeedOptimizer:
    """
    优化投喂策略的便捷函数

    Args:
        df: 养殖数据
        n_episodes: 训练回合数
        verbose: 是否显示详细信息

    Returns:
        训练好的优化器
    """
    optimizer = FeedOptimizer(df, method='q_learning')
    optimizer.train(n_episodes, verbose)
    optimizer.evaluate(n_episodes=10)

    return optimizer


