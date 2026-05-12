#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generator - 报告生成器

功能：
1. 生成 Markdown 报告
2. 生成 Word 报告
3. 生成 PDF 报告
4. 钉钉推送

Author: SmartShrimp contributors
Version: 1.0.0
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import pandas as pd


def generate_markdown_report(analyzer, visualizer, output_dir: str) -> str:
    """生成 Markdown 格式报告"""
    
    lines = []
    
    # 标题
    lines.append("# 🦐 对虾养殖数据分析报告\n")
    lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**数据来源**: {analyzer.data_path}\n")
    lines.append(f"**分析工具**: OpenClaw 对虾比赛系统 v1.0.0\n")
    lines.append(f"**作者**: SmartShrimp contributors\n\n")
    
    # 执行摘要
    lines.append("## 📋 执行摘要\n")
    insights = analyzer.generate_insights()
    for i, insight in enumerate(insights, 1):
        lines.append(f"{i}. {insight}")
    lines.append("")
    
    # 数据概况
    if 'quality' in analyzer.analysis_results:
        q = analyzer.analysis_results['quality']
        lines.append("\n## 📊 数据概况\n")
        lines.append(f"- **总行数**: {q['total_rows']:,}")
        lines.append(f"- **总列数**: {q['total_columns']}")
        lines.append(f"- **数据质量评分**: {q['quality_score']:.1f}/100")
        lines.append(f"- **缺失值总数**: {sum(q['missing_values'].values())}")
        lines.append(f"- **重复行数**: {q['duplicate_rows']}\n")
    
    # 统计摘要
    if 'statistics' in analyzer.analysis_results:
        lines.append("\n## 📈 统计摘要\n")
        stats = analyzer.analysis_results['statistics']
        
        lines.append("| 变量 | 均值 | 标准差 | 最小值 | 中位数 | 最大值 |")
        lines.append("|------|------|--------|--------|--------|--------|")
        
        for col in stats['mean'].keys():
            lines.append(
                f"| {col} | {stats['mean'][col]:.2f} | {stats['std'][col]:.2f} | "
                f"{stats['min'][col]:.2f} | {stats['50%'][col]:.2f} | {stats['max'][col]:.2f} |"
            )
        lines.append("")
    
    # 趋势分析
    if 'trends' in analyzer.analysis_results:
        lines.append("\n## 📉 趋势分析\n")
        for var, trend in analyzer.analysis_results['trends'].items():
            trend_arrow = "📈" if trend['trend'] == '上升' else "📉" if trend['trend'] == '下降' else "➡️"
            lines.append(
                f"### {trend_arrow} {var}\n"
                f"- 趋势：{trend['trend']}\n"
                f"- 增长率：{trend['growth_rate']:.2f}%\n"
                f"- 起始值：{trend['start_value']:.2f}\n"
                f"- 结束值：{trend['end_value']:.2f}\n"
            )
    
    # 相关性分析
    if 'correlation' in analyzer.analysis_results:
        corr = analyzer.analysis_results['correlation']
        if 'key_findings' in corr and corr['key_findings']:
            lines.append("\n## 🔗 相关性分析\n")
            for finding in corr['key_findings']:
                lines.append(f"- {finding}")
            lines.append("")
    
    # 异常值检测
    if 'anomalies' in analyzer.analysis_results:
        anom = analyzer.analysis_results['anomalies']
        lines.append("\n## ⚠️ 异常值检测\n")
        lines.append(f"- 检测方法：{anom['method']}")
        lines.append(f"- 阈值：{anom['threshold']}")
        lines.append(f"- 异常值总数：{anom['total_anomalies']}\n")
        
        for col, data in anom['anomalies_by_column'].items():
            if data['count'] > 0:
                lines.append(f"### {col}")
                lines.append(f"- 异常值数量：{data['count']}")
                lines.append(f"- 异常率：{data['rate']}%\n")
    
    # 图表展示
    lines.append("\n## 📊 可视化图表\n")
    if visualizer.saved_files:
        lines.append("### 生成的图表文件:\n")
        for i, filepath in enumerate(visualizer.saved_files, 1):
            filename = Path(filepath).name
            lines.append(f"{i}. ![{filename}]({filename})")
    lines.append("")
    
    # 结论与建议
    lines.append("\n## 💡 结论与建议\n")
    lines.append("### 主要发现\n")
    for i, insight in enumerate(insights, 1):
        lines.append(f"{i}. {insight}")
    
    lines.append("\n### 行动建议\n")
    lines.append("1. **监控关键指标**: 水温、盐度、溶解氧需保持在适宜范围")
    lines.append("2. **优化投喂策略**: 根据摄食率调整投喂量，减少浪费")
    lines.append("3. **预防疾病**: 定期检查存活率，及时发现异常")
    lines.append("4. **成本控制**: 分析成本结构，优化投入产出比")
    lines.append("5. **数据驱动决策**: 持续收集数据，建立预测模型\n")
    
    # 附录
    lines.append("\n## 📎 附录\n")
    lines.append("### 数据字典\n")
    if 'quality' in analyzer.analysis_results:
        for col, dtype in analyzer.analysis_results['quality']['data_types'].items():
            lines.append(f"- `{col}`: {dtype}")
    
    lines.append("\n### 关于本报告\n")
    lines.append("- **生成工具**: OpenClaw 对虾比赛系统")
    lines.append("- **分析库**: Pandas, NumPy, Matplotlib, Seaborn")
    lines.append("- **报告格式**: Markdown → Word/PDF")
    lines.append("- **团队**: SmartShrimp Team")
    lines.append(f"- **日期**: {datetime.now().strftime('%Y年%m月%d日')}\n")
    
    # 保存文件
    content = "\n".join(lines)
    output_file = Path(output_dir) / "analysis_report.md"
    output_file.write_text(content, encoding='utf-8')
    
    return str(output_file)


def generate_word_report(markdown_path: str, output_dir: str) -> Optional[str]:
    """将 Markdown 转换为 Word"""
    
    try:
        from skills.md2word_cn.scripts.md2word import convert as md2word_convert
        
        output_file = Path(output_dir) / "analysis_report.docx"
        md2word_convert(markdown_path, str(output_file))
        
        return str(output_file)
    except Exception as e:
        print(f"⚠️ Word 转换失败：{e}")
        return None


def generate_pdf_report(markdown_path: str, output_dir: str) -> Optional[str]:
    """将 Markdown 转换为 PDF"""
    
    try:
        # 使用 pdf-generator skill
        import subprocess
        
        output_file = Path(output_dir) / "analysis_report.pdf"
        
        # 尝试使用 pandoc（如果已安装）
        result = subprocess.run(
            ['pandoc', markdown_path, '-o', str(output_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return str(output_file)
        else:
            print(f"⚠️ Pandoc 转换失败：{result.stderr}")
            return None
            
    except FileNotFoundError:
        print("⚠️ Pandoc 未安装，跳过 PDF 生成")
        return None
    except Exception as e:
        print(f"⚠️ PDF 转换失败：{e}")
        return None


def generate_full_report(analyzer, visualizer, output_dir: str) -> Dict:
    """生成完整报告（Markdown + Word + PDF）"""
    
    print("1️⃣ 生成 Markdown 报告...")
    md_report = generate_markdown_report(analyzer, visualizer, output_dir)
    print(f"   ✅ Markdown: {md_report}")
    
    print("2️⃣ 生成 Word 报告...")
    word_report = generate_word_report(md_report, output_dir)
    if word_report:
        print(f"   ✅ Word: {word_report}")
    else:
        print("   ⚠️ Word 生成失败")
    
    print("3️⃣ 生成 PDF 报告...")
    pdf_report = generate_pdf_report(md_report, output_dir)
    if pdf_report:
        print(f"   ✅ PDF: {pdf_report}")
    else:
        print("   ⚠️ PDF 生成失败")
    
    return {
        'markdown_report': md_report,
        'word_report': word_report,
        'pdf_report': pdf_report
    }


def send_dingtalk_notification(report_path: str, webhook_url: Optional[str] = None):
    """发送钉钉通知"""
    
    # TODO: 实现钉钉推送
    # 需要配置 webhook URL
    print("\n📱 钉钉推送功能待配置...")
    print("   请设置 DINGTALK_WEBHOOK 环境变量")
    
    pass


if __name__ == '__main__':
    print("Report Generator v1.0.0")
    print("Author: SmartShrimp contributors")
    print("Date: 2026-03-17")
