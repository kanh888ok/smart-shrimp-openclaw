# GitHub 上传说明

这个版本可以直接作为 GitHub 仓库上传。

## 推荐仓库名

```text
policypilot-ai-agent
```

## 上传方式 A：网页上传

1. 在 GitHub 新建仓库。
2. 解压本 ZIP。
3. 进入 `policypilot_ai_agent/` 文件夹。
4. 全选里面的文件和文件夹，上传到 GitHub 仓库根目录。
5. 提交 commit：`initial commit: PolicyPilot AI Agent MVP`。

## 上传方式 B：命令行上传

```bash
cd policypilot_ai_agent
git init
git add .
git commit -m "initial commit: PolicyPilot AI Agent MVP"
git branch -M main
git remote add origin https://github.com/<your-username>/policypilot-ai-agent.git
git push -u origin main
```

## 本地运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 命令行 Demo

```bash
python cli_demo_public.py
python cli_demo.py
PYTHONPATH=. pytest -q
```

## 公开仓库检查结果

- 不包含 `.env`。
- 不包含真实 API Key。
- 不包含企业实名、统一社会信用代码、联系人、电话、地址、财务报表或申报书原文。
- `.env.example` 仅保留空变量名。
- `outputs/` 和 `outputs_public/` 已加入 `.gitignore`。
- 示例运行结果已整理到 `examples/`。
