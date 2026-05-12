"""
成本收益计算器 - ROI Calculator
基于CNKI论文《我国南美白对虾养殖的经济效益分析》
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

class ROICalculator:
    """投资回报率计算器"""

    def __init__(self):
        """初始化计算器，加载CNKI论文数据"""
        # 三种养殖模式的基础数据（来自CNKI论文）
        self.farming_modes = {
            "土池": {
                "stocking_density_min": 30000,  # 尾/亩
                "stocking_density_max": 90000,
                "yield_min": 50,  # kg/亩
                "yield_max": 300,
                "survival_rate_min": 0.20,
                "survival_rate_max": 0.70,
                "cycles_per_year": 1.5,
                "land_rent": 1000,  # 元/亩/年
                "initial_investment": 5000  # 元/亩（基础设施）
            },
            "高位池": {
                "stocking_density_min": 100000,
                "stocking_density_max": 250000,
                "yield_min": 1250,  # kg/亩/造
                "yield_max": 2500,
                "survival_rate_min": 0.60,
                "survival_rate_max": 0.85,
                "cycles_per_year": 2.5,
                "land_rent": 900,
                "initial_investment": 15000  # 高位池建设成本更高
            },
            "工厂化": {
                "stocking_density_min": 300000,
                "stocking_density_max": 1000000,
                "yield_min": 2500,  # kg/亩/造
                "yield_max": 6500,
                "survival_rate_min": 0.80,
                "survival_rate_max": 0.90,
                "cycles_per_year": 4,
                "land_rent": 900,
                "initial_investment": 50000  # 工厂化设施成本最高
            }
        }

        # 成本数据（来自CNKI论文）
        self.costs = {
            "shrimp_seed": {"min": 100, "max": 300, "unit": "元/万尾"},  # 苗种
            "feed": {"min": 2, "max": 5, "unit": "元/斤"},  # 饲料
            "fcr": {"min": 1.0, "max": 2.0},  # 饲料系数
            "labor": {"min": 3000, "max": 4000, "unit": "元/月/人"},  # 人工
            "medicine": {"min": 200, "max": 500, "unit": "元/亩/年"},  # 渔药
            "utilities": {"min": 500, "max": 1500, "unit": "元/亩/年"},  # 水电
            "transport": {"min": 100, "max": 300, "unit": "元/亩/年"}  # 运输
        }

        # 市场价格
        self.market_price = {
            "min": 30,  # 元/kg
            "max": 60,
            "avg": 40
        }

    def calculate_annual_cost(self, mode: str, area: float,
                            yield_per_cycle: float,
                            survival_rate: float) -> Dict:
        """
        计算年度成本

        Args:
            mode: 养殖模式 ('土池', '高位池', '工厂化')
            area: 面积（亩）
            yield_per_cycle: 每造产量（kg/亩）
            survival_rate: 成活率

        Returns:
            成本明细字典
        """
        mode_data = self.farming_modes[mode]
        cycles = mode_data["cycles_per_year"]

        # 1. 苗种成本
        seed_cost_per_10k = (self.costs["shrimp_seed"]["min"] +
                            self.costs["shrimp_seed"]["max"]) / 2
        seed_density = (mode_data["stocking_density_min"] +
                       mode_data["stocking_density_max"]) / 2
        total_seed_cost = (seed_density / 10000 * seed_cost_per_10k *
                          area * cycles)

        # 2. 饲料成本
        fcr = (self.costs["fcr"]["min"] + self.costs["fcr"]["max"]) / 2
        feed_price = (self.costs["feed"]["min"] +
                     self.costs["feed"]["max"]) / 2  # 元/斤 = 元/0.5kg
        total_feed_cost = (yield_per_cycle * area * cycles *
                          fcr * feed_price * 2)  # 转换为元/kg

        # 3. 人工成本
        labor_cost = self.costs["labor"]["avg"] * 12  # 按年计算

        # 4. 地租
        land_rent = mode_data["land_rent"] * area

        # 5. 其他成本
        medicine = (self.costs["medicine"]["min"] +
                   self.costs["medicine"]["max"]) / 2 * area
        utilities = (self.costs["utilities"]["min"] +
                    self.costs["utilities"]["max"]) / 2 * area
        transport = (self.costs["transport"]["min"] +
                    self.costs["transport"]["max"]) / 2 * area

        # 总成本
        total_cost = (total_seed_cost + total_feed_cost +
                     labor_cost + land_rent +
                     medicine + utilities + transport)

        return {
            "seed_cost": total_seed_cost,
            "feed_cost": total_feed_cost,
            "labor_cost": labor_cost,
            "land_rent": land_rent,
            "medicine": medicine,
            "utilities": utilities,
            "transport": transport,
            "total_cost": total_cost,
            "cost_breakdown": {
                "饲料成本": total_feed_cost / total_cost * 100,
                "苗种成本": total_seed_cost / total_cost * 100,
                "人工成本": labor_cost / total_cost * 100,
                "地租": land_rent / total_cost * 100,
                "其他": (medicine + utilities + transport) / total_cost * 100
            }
        }

    def calculate_annual_revenue(self, mode: str, area: float,
                                yield_per_cycle: float,
                                price: float = None) -> Dict:
        """
        计算年度收益

        Args:
            mode: 养殖模式
            area: 面积（亩）
            yield_per_cycle: 每造产量（kg/亩）
            price: 市场价格（元/kg），默认使用平均值

        Returns:
            收益明细
        """
        if price is None:
            price = self.market_price["avg"]

        mode_data = self.farming_modes[mode]
        cycles = mode_data["cycles_per_year"]

        # 年产量
        annual_yield = yield_per_cycle * area * cycles

        # 年收入
        total_revenue = annual_yield * price

        return {
            "annual_yield": annual_yield,
            "total_revenue": total_revenue,
            "price_per_kg": price
        }

    def calculate_roi(self, mode: str, area: float,
                     yield_per_cycle: float,
                     survival_rate: float,
                     price: float = None,
                     years: int = 3) -> pd.DataFrame:
        """
        计算多年投资回报率

        Args:
            mode: 养殖模式
            area: 面积（亩）
            yield_per_cycle: 每造产量
            survival_rate: 成活率
            price: 市场价格
            years: 计算年数

        Returns:
            包含每年详细数据的DataFrame
        """
        if price is None:
            price = self.market_price["avg"]

        mode_data = self.farming_modes[mode]
        initial_investment = mode_data["initial_investment"] * area

        results = []

        for year in range(1, years + 1):
            # 成本
            cost = self.calculate_annual_cost(mode, area,
                                             yield_per_cycle,
                                             survival_rate)

            # 收益
            revenue = self.calculate_annual_revenue(mode, area,
                                                   yield_per_cycle,
                                                   price)

            # 利润
            profit = revenue["total_revenue"] - cost["total_cost"]

            # 第一年需要减去初始投资
            if year == 1:
                net_profit = profit - initial_investment
                cumulative_profit = net_profit
            else:
                net_profit = profit
                cumulative_profit += net_profit

            # ROI
            if year == 1:
                roi = (net_profit / initial_investment * 100)
            else:
                roi = (cumulative_profit / initial_investment * 100)

            results.append({
                "年份": f"第{year}年",
                "初始投资": initial_investment if year == 1 else 0,
                "年度成本": cost["total_cost"],
                "年度收入": revenue["total_revenue"],
                "年度利润": profit,
                "净利润": net_profit,
                "累计利润": cumulative_profit,
                "ROI": roi,
                "投资回收状态": "✅ 已回收" if cumulative_profit > 0 else "⏳ 回收中"
            })

        return pd.DataFrame(results)

    def compare_modes(self, area: float = 10, years: int = 3) -> pd.DataFrame:
        """
        对比三种养殖模式

        Args:
            area: 面积（亩）
            years: 计算年数

        Returns:
            对比结果DataFrame
        """
        results = []

        for mode in self.farming_modes.keys():
            mode_data = self.farming_modes[mode]

            # 使用中等产量计算
            yield_per_cycle = (mode_data["yield_min"] +
                              mode_data["yield_max"]) / 2
            survival_rate = (mode_data["survival_rate_min"] +
                            mode_data["survival_rate_max"]) / 2

            # 计算3年ROI
            roi_df = self.calculate_roi(mode, area, yield_per_cycle,
                                       survival_rate, years=years)

            results.append({
                "养殖模式": mode,
                "初始投资": mode_data["initial_investment"] * area,
                "年产量（吨）": roi_df.iloc[0]["年度收入"] / self.market_price["avg"] / 1000,
                "年成本（万元）": roi_df.iloc[0]["年度成本"] / 10000,
                "年收入（万元）": roi_df.iloc[0]["年度收入"] / 10000,
                "年利润（万元）": roi_df.iloc[0]["年度利润"] / 10000,
                "回收期（年）": self._calculate_payback_period(mode, area,
                                                             yield_per_cycle,
                                                             survival_rate),
                "3年累计ROI": roi_df.iloc[-1]["ROI"]
            })

        return pd.DataFrame(results)

    def _calculate_payback_period(self, mode: str, area: float,
                                  yield_per_cycle: float,
                                  survival_rate: float) -> float:
        """计算投资回收期"""
        mode_data = self.farming_modes[mode]
        initial_investment = mode_data["initial_investment"] * area

        cost = self.calculate_annual_cost(mode, area, yield_per_cycle,
                                         survival_rate)
        revenue = self.calculate_annual_revenue(mode, area, yield_per_cycle)

        annual_profit = revenue["total_revenue"] - cost["total_cost"]

        if annual_profit <= 0:
            return float('inf')  # 无法回收

        payback_period = initial_investment / annual_profit
        return round(payback_period, 1)

    def compare_with_traditional(self, area: float = 10) -> Dict:
        """
        与传统养殖方式对比

        Args:
            area: 面积（亩）

        Returns:
            对比结果
        """
        # 传统方式数据（行业调研）
        traditional = {
            "FCR": 2.2,  # 传统饲料系数
            "survival_rate": 0.65,  # 传统成活率
            "yield_per_mu": 400,  # kg/亩/年（土池平均水平）
            "labor_cost_per_mu": 5000,  # 人工成本更高
        }

        # 智能系统数据
        smart = {
            "FCR": 1.9,  # 优化后的饲料系数（仿真验证）
            "survival_rate": 0.75,  # 提升的成活率
            "yield_per_mu": 480,  # 提升的产量（+20%）
            "labor_cost_per_mu": 2000,  # 自动化降低人工成本
        }

        # 计算成本和收益
        price = self.market_price["avg"]

        # 传统方式
        traditional_feed_cost = (traditional["yield_per_mu"] * area *
                               traditional["FCR"] * 3.5 * 2)  # 3.5元/斤
        traditional_labor_cost = traditional["labor_cost_per_mu"] * area
        traditional_revenue = traditional["yield_per_mu"] * area * price
        traditional_profit = (traditional_revenue -
                             traditional_feed_cost - traditional_labor_cost)

        # 智能系统
        smart_feed_cost = (smart["yield_per_mu"] * area *
                          smart["FCR"] * 3.5 * 2)
        smart_labor_cost = smart["labor_cost_per_mu"] * area
        smart_system_cost = 2000  # 系统年成本
        smart_revenue = smart["yield_per_mu"] * area * price
        smart_profit = (smart_revenue - smart_feed_cost -
                       smart_labor_cost - smart_system_cost)

        improvement = {
            "饲料节省": (1 - smart_feed_cost / traditional_feed_cost) * 100,
            "人工节省": (1 - smart_labor_cost / traditional_labor_cost) * 100,
            "产量提升": (smart_revenue / traditional_revenue - 1) * 100,
            "利润提升": (smart_profit / traditional_profit - 1) * 100,
            "年节省成本（元）": (traditional_feed_cost + traditional_labor_cost) -
                              (smart_feed_cost + smart_labor_cost + smart_system_cost)
        }

        return {
            "传统方式": {
                "年成本": traditional_feed_cost + traditional_labor_cost,
                "年收入": traditional_revenue,
                "年利润": traditional_profit,
                "FCR": traditional["FCR"],
                "成活率": f"{traditional['survival_rate']*100:.0f}%"
            },
            "智能系统": {
                "年成本": smart_feed_cost + smart_labor_cost + smart_system_cost,
                "年收入": smart_revenue,
                "年利润": smart_profit,
                "FCR": smart["FCR"],
                "成活率": f"{smart['survival_rate']*100:.0f}%"
            },
            "改进效果": improvement
        }

    def generate_investment_report(self, mode: str, area: float = 10) -> str:
        """
        生成投资报告

        Args:
            mode: 养殖模式
            area: 面积（亩）

        Returns:
            Markdown格式的报告
        """
        mode_data = self.farming_modes[mode]
        yield_per_cycle = (mode_data["yield_min"] +
                          mode_data["yield_max"]) / 2
        survival_rate = (mode_data["survival_rate_min"] +
                        mode_data["survival_rate_max"]) / 2

        # 3年ROI
        roi_df = self.calculate_roi(mode, area, yield_per_cycle,
                                   survival_rate, years=3)

        # 与传统对比
        comparison = self.compare_with_traditional(area)

        report = f"""
# {mode}养殖投资分析报告

## 基本信息
- 养殖模式：{mode}
- 养殖面积：{area}亩
- 初始投资：{mode_data['initial_investment'] * area:,}元
- 年产量：{roi_df.iloc[0]['年度收入'] / self.market_price['avg'] / 1000:.1f}吨

## 3年投资回报分析

{roi_df.to_markdown(index=False)}

## 与传统方式对比

### 传统方式
- 年利润：{comparison['传统方式']['年利润']/10000:.1f}万元
- FCR：{comparison['传统方式']['FCR']}
- 成活率：{comparison['传统方式']['成活率']}

### 智能系统
- 年利润：{comparison['智能系统']['年利润']/10000:.1f}万元
- FCR：{comparison['智能系统']['FCR']}
- 成活率：{comparison['智能系统']['成活率']}

### 改进效果
- 饲料节省：{comparison['改进效果']['饲料节省']:.1f}%
- 人工节省：{comparison['改进效果']['人工节省']:.1f}%
- 产量提升：{comparison['改进效果']['产量提升']:.1f}%
- 利润提升：{comparison['改进效果']['利润提升']:.1f}%
- 年节省成本：{comparison['改进效果']['年节省成本（元）']:,.0f}元

## 投资建议
基于CNKI论文数据和仿真验证结果，{mode}模式使用智能系统：
- 投资回收期：约{self._calculate_payback_period(mode, area, yield_per_cycle, survival_rate)}年
- 3年累计ROI：{roi_df.iloc[-1]['ROI']:.1f}%
- 建议：{'✅ 推荐投资' if roi_df.iloc[-1]['ROI'] > 50 else '⚠️ 谨慎投资'}

---
*数据来源：CNKI论文《我国南美白对虾养殖的经济效益分析》*
*仿真验证：智虾系统30天仿真实验*
"""

        return report


# 使用示例
if __name__ == "__main__":
    calculator = ROICalculator()

    # 生成投资报告
    print("=" * 60)
    print("高位池养殖投资分析报告（10亩）")
    print("=" * 60)
    report = calculator.generate_investment_report("高位池", area=10)
    print(report)

    # 三种模式对比
    print("\n" + "=" * 60)
    print("三种养殖模式对比")
    print("=" * 60)
    comparison = calculator.compare_modes(area=10)
    print(comparison.to_markdown(index=False))
