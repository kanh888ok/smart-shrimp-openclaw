#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shrimp Data Analyzer - 对虾养殖数据分析核心模块

功能：
1. 数据读取与验证（Excel/CSV）
2. 数据质量检查
3. 统计分析
4. 趋势分析
5. 异常检测
6. 可视化生成

Author: SmartShrimp contributors
Version: 1.0.0
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import warnings
warnings.filterwarnings('ignore')


class ShrimpDataAnalyzer:
    """对虾养殖数据专业分析器"""
    
    def __init__(self, data_path: Optional[str] = None):
        """
        初始化分析器
        
        Args:
            data_path: 数据文件路径（Excel 或 CSV）
        """
        self.data_path = Path(data_path) if data_path else None
        self.df: Optional[pd.DataFrame] = None
        self.analysis_results: Dict = {}
        
    def load_data(self, file_path: Optional[str] = None, 
                  sheet_name: Optional[Union[int, str]] = 0) -> pd.DataFrame:
        """
        读取数据文件（支持 Excel 和 CSV）
        
        Args:
            file_path: 文件路径
            sheet_name: Excel sheet 名称或索引
            
        Returns:
            pd.DataFrame: 加载的数据
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 不支持的文件格式
        """
        path = Path(file_path) if file_path else self.data_path
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在：{path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.xlsx':
            # 使用 openpyxl 引擎读取 xlsx
            self.df = pd.read_excel(path, sheet_name=sheet_name, engine='openpyxl')
        elif suffix == '.xls':
            self.df = pd.read_excel(path, sheet_name=sheet_name)
        elif suffix == '.csv':
            self.df = pd.read_csv(path, encoding='utf-8-sig')
        else:
            raise ValueError(f"不支持的文件格式：{suffix}")
        
        self.data_path = path
        return self.df
    
    def quality_check(self) -> Dict:
        """
        数据质量检查
        
        Returns:
            Dict: 质量检查报告
        """
        if self.df is None:
            raise ValueError("请先加载数据")
        
        report = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'column_names': list(self.df.columns),
            'missing_values': {},
            'missing_rate': {},
            'duplicate_rows': 0,
            'data_types': {},
            'quality_score': 100.0
        }
        
        # 缺失值统计
        for col in self.df.columns:
            missing = self.df[col].isnull().sum()
            rate = (missing / len(self.df)) * 100
            report['missing_values'][col] = int(missing)
            report['missing_rate'][col] = round(rate, 2)
        
        # 重复值统计
        report['duplicate_rows'] = int(self.df.duplicated().sum())
        
        # 数据类型
        for col in self.df.columns:
            report['data_types'][col] = str(self.df[col].dtype)
        
        # 计算质量分数
        total_missing = sum(report['missing_values'].values())
        total_cells = len(self.df) * len(self.df.columns)
        if total_cells > 0:
            missing_penalty = (total_missing / total_cells) * 50
            duplicate_penalty = min(report['duplicate_rows'] / len(self.df) * 30, 30)
            report['quality_score'] = max(0, 100 - missing_penalty - duplicate_penalty)
        
        self.analysis_results['quality'] = report
        return report
    
    def descriptive_statistics(self, numeric_only: bool = True) -> Dict:
        """
        描述性统计分析
        
        Args:
            numeric_only: 是否仅分析数值列
            
        Returns:
            Dict: 统计结果
        """
        if self.df is None:
            raise ValueError("请先加载数据")
        
        if numeric_only:
            df_numeric = self.df.select_dtypes(include=[np.number])
        else:
            df_numeric = self.df
        
        stats = {
            'count': df_numeric.count().to_dict(),
            'mean': df_numeric.mean().to_dict(),
            'std': df_numeric.std().to_dict(),
            'min': df_numeric.min().to_dict(),
            '25%': df_numeric.quantile(0.25).to_dict(),
            '50%': df_numeric.quantile(0.50).to_dict(),
            '75%': df_numeric.quantile(0.75).to_dict(),
            'max': df_numeric.max().to_dict(),
            'skewness': df_numeric.skew().to_dict(),
            'kurtosis': df_numeric.kurtosis().to_dict()
        }
        
        self.analysis_results['statistics'] = stats
        return stats
    
    def trend_analysis(self, date_column: str, value_columns: List[str]) -> Dict:
        """
        趋势分析（时间序列）
        
        Args:
            date_column: 日期列名
            value_columns: 需要分析的数值列
            
        Returns:
            Dict: 趋势分析结果
        """
        if self.df is None:
            raise ValueError("请先加载数据")
        
        if date_column not in self.df.columns:
            raise ValueError(f"日期列不存在：{date_column}")
        
        # 转换日期
        df = self.df.copy()
        df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        df = df.sort_values(date_column)
        
        trends = {}
        for col in value_columns:
            if col not in df.columns:
                continue
            
            # 计算趋势
            values = df[col].dropna()
            if len(values) < 2:
                continue
            
            # 简单线性回归斜率
            x = np.arange(len(values))
            slope = np.polyfit(x, values, 1)[0]
            
            # 增长率
            if values.iloc[0] != 0:
                growth_rate = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0]) * 100
            else:
                growth_rate = 0
            
            # 移动平均
            if len(values) >= 3:
                ma_3 = values.rolling(window=3).mean().tolist()
            else:
                ma_3 = []
            
            trends[col] = {
                'slope': float(slope),
                'trend': '上升' if slope > 0 else '下降' if slope < 0 else '平稳',
                'growth_rate': float(growth_rate),
                'start_value': float(values.iloc[0]),
                'end_value': float(values.iloc[-1]),
                'moving_avg_3': ma_3
            }
        
        self.analysis_results['trends'] = trends
        return trends
    
    def correlation_analysis(self) -> Dict:
        """
        相关性分析
        
        Returns:
            Dict: 相关系数矩阵和关键发现
        """
        if self.df is None:
            raise ValueError("请先加载数据")
        
        df_numeric = self.df.select_dtypes(include=[np.number])
        
        if df_numeric.shape[1] < 2:
            return {'error': '数值列不足 2 列，无法进行相关性分析'}
        
        corr_matrix = df_numeric.corr()
        
        # 找出强相关对
        strong_corrs = []
        columns = corr_matrix.columns.tolist()
        for i in range(len(columns)):
            for j in range(i + 1, len(columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.7:  # 强相关阈值
                    strong_corrs.append({
                        'var1': columns[i],
                        'var2': columns[j],
                        'correlation': float(corr_value),
                        'strength': '强正相关' if corr_value > 0 else '强负相关'
                    })
        
        results = {
            'correlation_matrix': corr_matrix.to_dict(),
            'strong_correlations': strong_corrs,
            'key_findings': []
        }
        
        # 生成关键发现
        for corr in strong_corrs:
            if corr['correlation'] > 0.8:
                results['key_findings'].append(
                    f"{corr['var1']} 与 {corr['var2']} 高度正相关 (r={corr['correlation']:.2f})"
                )
            elif corr['correlation'] < -0.8:
                results['key_findings'].append(
                    f"{corr['var1']} 与 {corr['var2']} 高度负相关 (r={corr['correlation']:.2f})"
                )
        
        self.analysis_results['correlation'] = results
        return results
    
    def anomaly_detection(self, method: str = 'zscore', threshold: float = 3.0) -> Dict:
        """
        异常值检测
        
        Args:
            method: 检测方法 ('zscore' 或 'iqr')
            threshold: 阈值
            
        Returns:
            Dict: 异常值检测结果
        """
        if self.df is None:
            raise ValueError("请先加载数据")
        
        df_numeric = self.df.select_dtypes(include=[np.number])
        anomalies = {}
        
        for col in df_numeric.columns:
            values = df_numeric[col].dropna()
            
            if method == 'zscore':
                # Z-Score 方法
                mean = values.mean()
                std = values.std()
                if std > 0:
                    z_scores = np.abs((values - mean) / std)
                    anomaly_mask = z_scores > threshold
                    anomaly_indices = values[anomaly_mask].index.tolist()
                    anomaly_values = values[anomaly_mask].tolist()
                else:
                    anomaly_indices = []
                    anomaly_values = []
                
            elif method == 'iqr':
                # IQR 方法
                q1 = values.quantile(0.25)
                q3 = values.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - threshold * iqr
                upper_bound = q3 + threshold * iqr
                anomaly_mask = (values < lower_bound) | (values > upper_bound)
                anomaly_indices = values[anomaly_mask].index.tolist()
                anomaly_values = values[anomaly_mask].tolist()
            else:
                raise ValueError(f"不支持的检测方法：{method}")
            
            anomalies[col] = {
                'count': len(anomaly_indices),
                'rate': round(len(anomaly_indices) / len(values) * 100, 2),
                'indices': anomaly_indices[:10],  # 最多显示 10 个
                'values': anomaly_values[:10]
            }
        
        results = {
            'method': method,
            'threshold': threshold,
            'anomalies_by_column': anomalies,
            'total_anomalies': sum(v['count'] for v in anomalies.values())
        }
        
        self.analysis_results['anomalies'] = results
        return results
    
    def generate_insights(self) -> List[str]:
        """
        生成数据洞察
        
        Returns:
            List[str]: 洞察列表
        """
        insights = []
        
        # 基于质量检查
        if 'quality' in self.analysis_results:
            quality = self.analysis_results['quality']
            if quality['quality_score'] >= 90:
                insights.append("✅ 数据质量优秀，可直接用于分析")
            elif quality['quality_score'] >= 70:
                insights.append("⚠️ 数据质量良好，建议处理少量缺失值")
            else:
                insights.append("❌ 数据质量较差，需要数据清洗")
        
        # 基于趋势分析
        if 'trends' in self.analysis_results:
            for var, trend in self.analysis_results['trends'].items():
                if trend['growth_rate'] > 20:
                    insights.append(f"📈 {var} 呈现显著增长趋势 (增长率 {trend['growth_rate']:.1f}%)")
                elif trend['growth_rate'] < -20:
                    insights.append(f"📉 {var} 呈现显著下降趋势 (下降率 {abs(trend['growth_rate']):.1f}%)")
        
        # 基于相关性
        if 'correlation' in self.analysis_results:
            if 'key_findings' in self.analysis_results['correlation']:
                for finding in self.analysis_results['correlation']['key_findings']:
                    insights.append(f"🔗 {finding}")
        
        # 基于异常值
        if 'anomalies' in self.analysis_results:
            total = self.analysis_results['anomalies']['total_anomalies']
            if total > 0:
                insights.append(f"⚠️ 检测到 {total} 个异常值，建议进一步核查")
        
        return insights
    
    def export_summary(self, output_path: str) -> str:
        """
        导出分析摘要（Markdown 格式）
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            str: 生成的摘要内容
        """
        lines = []
        lines.append("# 📊 数据分析摘要报告\n")
        lines.append(f"**数据源**: {self.data_path}\n")
        lines.append(f"**分析时间**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # 数据概况
        if 'quality' in self.analysis_results:
            q = self.analysis_results['quality']
            lines.append("## 一、数据概况\n")
            lines.append(f"- 总行数：{q['total_rows']:,}")
            lines.append(f"- 总列数：{q['total_columns']}")
            lines.append(f"- 数据质量评分：{q['quality_score']:.1f}/100\n")
        
        # 关键洞察
        insights = self.generate_insights()
        if insights:
            lines.append("\n## 二、关键洞察\n")
            for i, insight in enumerate(insights, 1):
                lines.append(f"{i}. {insight}")
        
        # 统计摘要
        if 'statistics' in self.analysis_results:
            lines.append("\n## 三、统计摘要\n")
            stats = self.analysis_results['statistics']
            for col in stats['mean'].keys():
                lines.append(f"### {col}")
                lines.append(f"- 均值：{stats['mean'][col]:.2f}")
                lines.append(f"- 标准差：{stats['std'][col]:.2f}")
                lines.append(f"- 最小值：{stats['min'][col]:.2f}")
                lines.append(f"- 最大值：{stats['max'][col]:.2f}\n")
        
        content = "\n".join(lines)
        
        # 保存文件
        output_file = Path(output_path)
        output_file.write_text(content, encoding='utf-8')
        
        return content
    
    def run_full_analysis(self, output_dir: str = 'reports') -> Dict:
        """
        运行完整分析流程
        
        Args:
            output_dir: 输出目录
            
        Returns:
            Dict: 完整分析结果
        """
        print("🔍 开始数据分析...")
        
        # 1. 数据加载
        print("1️⃣ 加载数据...")
        self.load_data()
        
        # 2. 质量检查
        print("2️⃣ 数据质量检查...")
        self.quality_check()
        
        # 3. 描述统计
        print("3️⃣ 描述性统计...")
        self.descriptive_statistics()
        
        # 4. 相关性分析
        print("4️⃣ 相关性分析...")
        self.correlation_analysis()
        
        # 5. 异常检测
        print("5️⃣ 异常值检测...")
        self.anomaly_detection()
        
        # 6. 生成洞察
        print("6️⃣ 生成洞察...")
        insights = self.generate_insights()
        
        # 7. 导出摘要
        print("7️⃣ 导出报告...")
        output_path = Path(output_dir) / "analysis_summary.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        summary = self.export_summary(str(output_path))
        
        results = {
            'status': 'success',
            'data_loaded': True,
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'insights': insights,
            'report_path': str(output_path)
        }
        
        print(f"✅ 分析完成！报告已保存至：{output_path}")
        return results


# 便捷函数
def analyze_shrimp_data(file_path: str, output_dir: str = 'reports') -> Dict:
    """
    一键分析对虾养殖数据
    
    Args:
        file_path: 数据文件路径
        output_dir: 输出目录
        
    Returns:
        Dict: 分析结果
    """
    analyzer = ShrimpDataAnalyzer(file_path)
    return analyzer.run_full_analysis(output_dir)


if __name__ == '__main__':
    # 测试示例
    print("Shrimp Data Analyzer v1.0.0")
    print("Author: SmartShrimp contributors")
    print("Date: 2026-03-17")
