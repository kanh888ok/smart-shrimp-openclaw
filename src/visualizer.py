#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shrimp Data Visualizer - 对虾养殖数据可视化模块

功能：
1. 折线图（趋势分析）
2. 柱状图（对比分析）
3. 饼图（占比分析）
4. 热力图（相关性）
5. 箱线图（分布与异常值）
6. 组合图表

Author: SmartShrimp contributors
Version: 1.0.0
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import List, Optional, Dict, Tuple, Union
import platform
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体（跨平台）
def setup_chinese_font():
    """跨平台中文字体配置"""
    system = platform.system()
    if system == 'Windows':
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
    elif system == 'Darwin':  # macOS
        plt.rcParams['font.sans-serif'] = ['PingFang SC', 'Heiti TC', 'DejaVu Sans']
    else:  # Linux
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

setup_chinese_font()

# Seaborn 样式
sns.set_style("whitegrid")
sns.set_palette("husl")


class ShrimpVisualizer:
    """对虾养殖数据专业可视化器"""
    
    def __init__(self, df: pd.DataFrame, output_dir: str = 'reports/figures'):
        """
        初始化可视化器
        
        Args:
            df: 数据 DataFrame
            output_dir: 输出目录
        """
        self.df = df
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.saved_files: List[str] = []
    
    def save_figure(self, fig: plt.Figure, filename: str, 
                    dpi: int = 300, tight: bool = True) -> str:
        """
        保存图表
        
        Args:
            fig: 图表对象
            filename: 文件名
            dpi: 分辨率
            tight: 是否紧凑布局
            
        Returns:
            str: 保存路径
        """
        filepath = self.output_dir / filename
        
        if tight:
            fig.tight_layout()
        
        fig.savefig(filepath, dpi=dpi, bbox_inches='tight' if tight else None)
        plt.close(fig)
        
        self.saved_files.append(str(filepath))
        return str(filepath)
    
    def plot_line_chart(self, x_col: str, y_cols: List[str], 
                        title: str = "趋势图", figsize: Tuple[int, int] = (12, 6)) -> str:
        """
        绘制折线图（趋势分析）
        
        Args:
            x_col: X 轴列名
            y_cols: Y 轴列名列表
            title: 图表标题
            figsize: 图表尺寸
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        for col in y_cols:
            if col in self.df.columns:
                ax.plot(self.df[x_col], self.df[col], marker='o', 
                       linewidth=2, markersize=6, label=col)
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 旋转 X 轴标签
        plt.xticks(rotation=45)
        
        filename = f"line_chart_{x_col}.png"
        return self.save_figure(fig, filename)
    
    def plot_bar_chart(self, x_col: str, y_col: str, 
                       title: str = "柱状图", figsize: Tuple[int, int] = (10, 6),
                       hue_col: Optional[str] = None) -> str:
        """
        绘制柱状图（对比分析）
        
        Args:
            x_col: X 轴列名
            y_col: Y 轴列名
            title: 图表标题
            figsize: 图表尺寸
            hue_col: 分组列名（可选）
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if hue_col and hue_col in self.df.columns:
            # 分组柱状图
            grouped = self.df.groupby([x_col, hue_col])[y_col].sum().unstack()
            grouped.plot(kind='bar', ax=ax, width=0.8)
        else:
            # 简单柱状图
            grouped = self.df.groupby(x_col)[y_col].sum().sort_values(ascending=False)
            grouped.plot(kind='bar', ax=ax, color='steelblue', width=0.6)
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.xticks(rotation=45)
        
        filename = f"bar_chart_{x_col}_{y_col}.png"
        return self.save_figure(fig, filename)
    
    def plot_pie_chart(self, category_col: str, value_col: str,
                       title: str = "占比图", figsize: Tuple[int, int] = (8, 8),
                       top_n: Optional[int] = None) -> str:
        """
        绘制饼图（占比分析）
        
        Args:
            category_col: 分类列名
            value_col: 数值列名
            title: 图表标题
            figsize: 图表尺寸
            top_n: 仅显示前 N 个类别（可选）
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 聚合数据
        grouped = self.df.groupby(category_col)[value_col].sum().sort_values(ascending=False)
        
        # Top N
        if top_n:
            grouped = grouped.head(top_n)
        
        # 绘制饼图
        colors = plt.cm.Set3(np.linspace(0, 1, len(grouped)))
        wedges, texts, autotexts = ax.pie(
            grouped.values, 
            labels=grouped.index,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
            pctdistance=0.85
        )
        
        # 美化
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
        
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
        
        filename = f"pie_chart_{category_col}.png"
        return self.save_figure(fig, filename)
    
    def plot_correlation_heatmap(self, columns: Optional[List[str]] = None,
                                  title: str = "相关性热力图",
                                  figsize: Tuple[int, int] = (10, 8)) -> str:
        """
        绘制相关性热力图
        
        Args:
            columns: 需要分析的列（可选，默认所有数值列）
            title: 图表标题
            figsize: 图表尺寸
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        # 选择数值列
        if columns:
            df_numeric = self.df[columns].select_dtypes(include=[np.number])
        else:
            df_numeric = self.df.select_dtypes(include=[np.number])
        
        # 计算相关系数
        corr_matrix = df_numeric.corr()
        
        # 绘制热力图
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        sns.heatmap(corr_matrix, 
                   mask=mask,
                   annot=True, 
                   fmt='.2f', 
                   cmap='RdBu_r', 
                   center=0,
                   square=True,
                   linewidths=0.5,
                   ax=ax,
                   cbar_kws={'shrink': 0.8})
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        filename = "correlation_heatmap.png"
        return self.save_figure(fig, filename)
    
    def plot_box_plot(self, x_col: str, y_col: str,
                      title: str = "箱线图", figsize: Tuple[int, int] = (10, 6)) -> str:
        """
        绘制箱线图（分布与异常值）
        
        Args:
            x_col: X 轴列名（分类）
            y_col: Y 轴列名（数值）
            title: 图表标题
            figsize: 图表尺寸
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        data = [group[y_col].dropna() for _, group in self.df.groupby(x_col)]
        labels = sorted(self.df[x_col].unique())
        
        bp = ax.boxplot(data, labels=labels, patch_artist=True,
                       showmeans=True, whis=1.5)
        
        # 美化
        colors = plt.cm.Pastel1(np.linspace(0, 1, len(data)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.xticks(rotation=45)
        
        filename = f"box_plot_{x_col}_{y_col}.png"
        return self.save_figure(fig, filename)
    
    def plot_scatter_plot(self, x_col: str, y_col: str,
                          title: str = "散点图", figsize: Tuple[int, int] = (10, 6),
                          hue_col: Optional[str] = None) -> str:
        """
        绘制散点图（关系分析）
        
        Args:
            x_col: X 轴列名
            y_col: Y 轴列名
            title: 图表标题
            figsize: 图表尺寸
            hue_col: 分组列名（可选）
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        if hue_col and hue_col in self.df.columns:
            # 分组散点图
            for name, group in self.df.groupby(hue_col):
                ax.scatter(group[x_col], group[y_col], label=name, alpha=0.6, s=50)
            ax.legend(loc='best')
        else:
            # 简单散点图
            ax.scatter(self.df[x_col], self.df[y_col], alpha=0.6, s=50, c='steelblue')
        
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        filename = f"scatter_plot_{x_col}_{y_col}.png"
        return self.save_figure(fig, filename)
    
    def plot_histogram(self, column: str, bins: int = 20,
                       title: str = "分布直方图", figsize: Tuple[int, int] = (10, 6)) -> str:
        """
        绘制直方图（分布分析）
        
        Args:
            column: 列名
            bins: 分组数
            title: 图表标题
            figsize: 图表尺寸
            
        Returns:
            str: 保存路径
        """
        fig, ax = plt.subplots(figsize=figsize)
        
        data = self.df[column].dropna()
        
        ax.hist(data, bins=bins, color='skyblue', edgecolor='black', alpha=0.7)
        
        # 添加均值和中位数线
        mean = data.mean()
        median = data.median()
        
        ax.axvline(mean, color='red', linestyle='--', linewidth=2, label=f'均值：{mean:.2f}')
        ax.axvline(median, color='green', linestyle='-.', linewidth=2, label=f'中位数：{median:.2f}')
        
        ax.set_xlabel(column, fontsize=12)
        ax.set_ylabel('频数', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        filename = f"histogram_{column}.png"
        return self.save_figure(fig, filename)
    
    def create_dashboard(self, charts_config: List[Dict],
                         title: str = "数据分析仪表板",
                         figsize: Tuple[int, int] = (16, 12)) -> str:
        """
        创建组合仪表板
        
        Args:
            charts_config: 图表配置列表
            title: 仪表板标题
            figsize: 总尺寸
            
        Returns:
            str: 保存路径
        """
        n_charts = len(charts_config)
        n_cols = 2
        n_rows = (n_charts + 1) // 2
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
        axes = axes.flatten() if n_rows > 1 else [axes] if n_rows == 1 else []
        
        fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
        
        for i, config in enumerate(charts_config):
            if i >= len(axes):
                break
            
            ax = axes[i]
            chart_type = config.get('type', 'line')
            
            # 根据配置绘制不同类型的图表
            if chart_type == 'line':
                x_col = config.get('x')
                y_cols = config.get('y', [])
                for y_col in y_cols:
                    if y_col in self.df.columns and x_col in self.df.columns:
                        ax.plot(self.df[x_col], self.df[y_col], marker='o', label=y_col)
                ax.set_xlabel(x_col)
                ax.set_ylabel('数值')
                ax.legend()
            
            elif chart_type == 'bar':
                x_col = config.get('x')
                y_col = config.get('y')
                if x_col in self.df.columns and y_col in self.df.columns:
                    grouped = self.df.groupby(x_col)[y_col].sum()
                    grouped.plot(kind='bar', ax=ax, color='steelblue')
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            
            elif chart_type == 'scatter':
                x_col = config.get('x')
                y_col = config.get('y')
                if x_col in self.df.columns and y_col in self.df.columns:
                    ax.scatter(self.df[x_col], self.df[y_col], alpha=0.6)
                ax.set_xlabel(x_col)
                ax.set_ylabel(y_col)
            
            ax.set_title(config.get('title', f'Chart {i+1}'), fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        # 删除多余的子图
        for j in range(n_charts, len(axes)):
            fig.delaxes(axes[j])
        
        plt.tight_layout()
        
        filename = "analysis_dashboard.png"
        return self.save_figure(fig, filename)
    
    def generate_all_charts(self) -> Dict:
        """
        一键生成所有图表
        
        Returns:
            Dict: 图表文件列表
        """
        print("📊 开始生成图表...")
        
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        charts = {}
        
        # 1. 数值列的直方图
        for col in numeric_cols[:5]:  # 最多 5 个
            try:
                path = self.plot_histogram(col, title=f"{col} 分布")
                charts[f'hist_{col}'] = path
                print(f"  ✅ {col} 直方图")
            except Exception as e:
                print(f"  ❌ {col} 直方图失败：{e}")
        
        # 2. 相关性热力图
        if len(numeric_cols) >= 2:
            try:
                path = self.plot_correlation_heatmap(title="变量相关性热力图")
                charts['correlation'] = path
                print(f"  ✅ 相关性热力图")
            except Exception as e:
                print(f"  ❌ 相关性热力图失败：{e}")
        
        # 3. 分类变量的饼图
        for cat_col in categorical_cols[:3]:  # 最多 3 个
            if len(numeric_cols) > 0:
                try:
                    path = self.plot_pie_chart(cat_col, numeric_cols[0], 
                                              title=f"{cat_col} 占比", top_n=8)
                    charts[f'pie_{cat_col}'] = path
                    print(f"  ✅ {cat_col} 饼图")
                except Exception as e:
                    print(f"  ❌ {cat_col} 饼图失败：{e}")
        
        # 4. 箱线图
        if len(categorical_cols) > 0 and len(numeric_cols) > 0:
            for cat_col in categorical_cols[:2]:
                for num_col in numeric_cols[:2]:
                    try:
                        path = self.plot_box_plot(cat_col, num_col, 
                                                 title=f"{num_col} by {cat_col}")
                        charts[f'box_{cat_col}_{num_col}'] = path
                        print(f"  ✅ 箱线图 {cat_col}-{num_col}")
                    except Exception as e:
                        print(f"  ❌ 箱线图失败：{e}")
        
        print(f"\n✅ 图表生成完成！共 {len(charts)} 个图表")
        
        return {
            'status': 'success',
            'charts_count': len(charts),
            'charts': charts,
            'output_dir': str(self.output_dir)
        }


# 便捷函数
def visualize_shrimp_data(df: pd.DataFrame, output_dir: str = 'reports/figures') -> Dict:
    """
    一键可视化对虾养殖数据
    
    Args:
        df: 数据 DataFrame
        output_dir: 输出目录
        
    Returns:
        Dict: 可视化结果
    """
    visualizer = ShrimpVisualizer(df, output_dir)
    return visualizer.generate_all_charts()


if __name__ == '__main__':
    print("Shrimp Data Visualizer v1.0.0")
    print("Author: SmartShrimp contributors")
    print("Date: 2026-03-17")
