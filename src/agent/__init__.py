#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智虾系统 - 智能决策模块

符合 OpenClaw 核心要求的智能养殖管理系统
"""

from .shrimp_farming_agent import (
    ShrimpFarmingAgent,
    Action,
    MonitoringAlert,
    run_agent_demo
)

# 可选导入（需要requests的模块）
try:
    from .device_controller import (
        RealExecutionController,
        FileController,
        MessageController,
        ReportGenerator as DeviceReportGenerator,
        DeviceController
    )
except ImportError:
    pass  # requests未安装，跳过设备控制器

try:
    from .autonomous_agent import (
        AutonomousAgent
    )
except ImportError:
    pass  # 依赖于device_controller，可能无法导入

from .autonomous_loop import (
    AutonomousLoop,
    LoopStatus
)
from .skill_manager import (
    Skill,
    SkillManager,
    SkillResult,
    WaterMonitoringSkill,
    FeedingOptimizationSkill,
    AerationControlSkill,
    create_skill_manager
)

# 可选导入（需要yaml）
try:
    from .task_evaluator import (
        TaskEvaluator,
        TaskResult
    )
except ImportError:
    pass  # yaml未安装，跳过任务评估器

__all__ = [
    # 核心类
    'ShrimpFarmingAgent',
    'AutonomousAgent',
    'AutonomousLoop',
    'SkillManager',

    # 数据类
    'Action',
    'MonitoringAlert',
    'TaskResult',
    'SkillResult',
    'LoopStatus',

    # 执行控制器
    'RealExecutionController',
    'FileController',
    'MessageController',
    'ReportGenerator',
    'DeviceController',

    # 技能相关
    'Skill',
    'WaterMonitoringSkill',
    'FeedingOptimizationSkill',
    'AerationControlSkill',
    'create_skill_manager',

    # 评估器
    'TaskEvaluator',

    # 演示函数
    'run_agent_demo'
]

__version__ = '3.0.0'
__author__ = 'SmartShrimp Team'
__date__ = '2026-03-18'
