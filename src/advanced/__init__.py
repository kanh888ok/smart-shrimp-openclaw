"""高级机器学习模块"""

# 可选导入（需要torch的模块）
try:
    from .deep_learning_models import *
except ImportError:
    pass  # torch未安装，跳过深度学习模块

try:
    from .multi_modal_fusion import *
except ImportError:
    pass  # torch或transformers未安装

# 标准机器学习模块
try:
    from .time_series_models import *
except ImportError:
    pass  # prophet或pmdarima未安装

try:
    from .model_ensemble import *
except ImportError:
    pass

try:
    from .hyperparameter_tuning import *
except ImportError:
    pass  # optuna未安装

try:
    from .model_explainer import *
except ImportError:
    pass  # shap未安装

try:
    from .temporal_validation import *
except ImportError:
    pass

try:
    from .multi_seed_ensemble import *
except ImportError:
    pass

try:
    from .horizon_modeling import *
except ImportError:
    pass

try:
    from .post_calibration import *
except ImportError:
    pass
