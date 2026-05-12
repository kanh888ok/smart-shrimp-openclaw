"""
成本分析数据 - 来源于CNKI学术论文
来源：《我国南美白对虾养殖的经济效益分析》王静，上海海洋大学
"""

# 成本结构数据（单位：元）
COST_STRUCTURE = {
    "variable_costs": {
        "shrimp_seed": {
            "range": "100-300元/万尾",
            "min": 100,
            "max": 300,
            "unit": "元/万尾",
            "description": "虾苗成本"
        },
        "feed": {
            "range": "2-5元/斤",
            "min": 2,
            "max": 5,
            "unit": "元/斤",
            "description": "饲料成本",
            "fcr_range": "1:1 到 1:2"  # 饲料系数
        },
        "medicine": {
            "description": "渔药成本",
            "note": "包含消毒剂、抗生素、免疫增强剂等"
        },
        "utilities": {
            "description": "水电费",
            "note": "主要包括电费（增氧机、水泵）和水费"
        },
        "transport": {
            "description": "运输费用",
            "note": "苗种运输、饲料运输、成虾运输"
        },
        "temporary_labor": {
            "description": "临时人工费用",
            "note": "捕捞、分拣、装车等临时用工"
        }
    },
    "fixed_costs": {
        "land_rent": {
            "土池": 1000,  # 元/亩/年
            "高位池": 900,
            "工厂化": 900,
            "unit": "元/亩/年",
            "description": "土地租金"
        },
        "fixed_labor": {
            "range": "3000-4000元/月",
            "min": 3000,
            "max": 4000,
            "unit": "元/月",
            "description": "固定人工费用",
            "note": "技术员和长期管理人员工资"
        },
        "equipment_maintenance": {
            "description": "设备维修费",
            "note": "增氧机、水泵、投饵机等设备维护"
        },
        "loan_interest": {
            "description": "贷款利息",
            "note": "流动资金贷款利息"
        },
        "depreciation": {
            "description": "折旧费",
            "note": "固定资产折旧"
        },
        "rd": {
            "description": "研发费用",
            "note": "技术改进、试验费用"
        }
    }
}

# 养殖模式数据
FARMING_MODES = {
    "土池": {
        "stocking_density": {
            "range": "3-9万尾/亩",
            "min": 30000,
            "max": 90000,
            "unit": "尾/亩"
        },
        "yield": {
            "range": "100-600斤/亩",
            "min": 50,  # kg
            "max": 300,  # kg
            "unit": "kg/亩"
        },
        "survival_rate": {
            "range": "20-70%",
            "min": 0.2,
            "max": 0.7
        },
        "cycles_per_year": "1-2造/年",
        "land_rent": 1000  # 元/亩/年
    },
    "高位池": {
        "stocking_density": {
            "range": "10-25万尾/亩",
            "min": 100000,
            "max": 250000,
            "unit": "尾/亩"
        },
        "yield": {
            "range": "2500-5000斤/亩/造",
            "min": 1250,  # kg
            "max": 2500,  # kg
            "unit": "kg/亩/造"
        },
        "survival_rate": {
            "range": "60-85%",
            "min": 0.6,
            "max": 0.85
        },
        "cycles_per_year": "2-3造/年",
        "land_rent": 900  # 元/亩/年
    },
    "工厂化": {
        "stocking_density": {
            "range": "30-100万尾/亩",
            "min": 300000,
            "max": 1000000,
            "unit": "尾/亩"
        },
        "yield": {
            "range": "5000-13000斤/亩/造",
            "min": 2500,  # kg
            "max": 6500,  # kg
            "unit": "kg/亩/造"
        },
        "survival_rate": {
            "range": "80-90%",
            "min": 0.8,
            "max": 0.9
        },
        "cycles_per_year": "3-5造/年",
        "land_rent": 900  # 元/亩/年
    }
}

# 典型成本结构占比（参考值）
COST_PROPORTION = {
    "饲料成本": "60-70%",
    "苗种成本": "10-15%",
    "人工成本": "5-10%",
    "水电费": "5-8%",
    "渔药": "3-5%",
    "其他": "5-10%"
}

# 数据来源
DATA_SOURCE = {
    "paper_title": "我国南美白对虾养殖的经济效益分析",
    "author": "王静",
    "institution": "上海海洋大学",
    "publisher": "CNKI中国知网",
    "note": "本数据来源于学术论文的调研统计，代表行业平均水平"
}


def get_cost_by_mode(mode, area_mu, yield_kg, survival_rate=0.8):
    """
    根据养殖模式计算成本

    Args:
        mode: 养殖模式 ('土池', '高位池', '工厂化')
        area_mu: 面积（亩）
        yield_kg: 预期产量（kg）
        survival_rate: 成活率

    Returns:
        dict: 成本明细
    """
    mode_data = FARMING_MODES.get(mode, FARMING_MODES["土池"])

    # 可变成本计算
    # 饲料成本（按产量计算，假设FCR=1.5）
    fcr = 1.5
    feed_cost = yield_kg * 2 * fcr * 3.5  # 3.5元/斤是中间值

    # 苗种成本（按放养密度计算）
    seed_count = mode_data["stocking_density"]["max"] * area_mu
    seed_cost = seed_count / 10000 * 200  # 200元/万尾是中间值

    # 固定成本
    land_rent = mode_data["land_rent"] * area_mu
    labor_cost = 3500 * 12  # 按年计算

    total_cost = feed_cost + seed_cost + land_rent + labor_cost

    return {
        "feed_cost": feed_cost,
        "seed_cost": seed_cost,
        "land_rent": land_rent,
        "labor_cost": labor_cost,
        "total_cost": total_cost,
        "cost_per_kg": total_cost / yield_kg if yield_kg > 0 else 0
    }


def calculate_benefit(yield_kg, price_per_kg=40):
    """
    计算收益

    Args:
        yield_kg: 产量（kg）
        price_per_kg: 市场价格（元/kg）

    Returns:
        float: 总收益
    """
    return yield_kg * price_per_kg


def calculate_profit_margin(total_cost, total_revenue):
    """
    计算利润率

    Args:
        total_cost: 总成本
        total_revenue: 总收入

    Returns:
        float: 利润率（百分比）
    """
    if total_revenue == 0:
        return 0
    return ((total_revenue - total_cost) / total_revenue) * 100
