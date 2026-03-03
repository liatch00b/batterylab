# BatteryLab

## 运行

1. 安装依赖：`pip install -r requirements.txt`
2. 启动应用：`streamlit run app.py`

## 数据准备

- 本仓库的 `data/*.mat` 通过 Git LFS 管理。
- 首次 clone 后请在仓库根目录执行：`git lfs pull`
- 若未执行该命令，`data/*.mat` 可能只是指针文本，会导致 `Unknown mat file type` 报错。

### 部署提示

- 本项目已提供 `packages.txt`，包含 `git-lfs`。
- 若你的部署平台支持 apt 依赖安装（如 Streamlit Community Cloud），会在构建时自动安装 `git-lfs`。
- 重新部署后应用会自动尝试 `git lfs pull`，成功后即可直接加载真实数据。
- 若部署环境未安装 `git-lfs`，应用会自动尝试从 GitHub 媒体地址下载真实 `data/*.mat`（不使用模拟数据）。

## Matplotlib 中文显示说明

- 应用启动时会优先使用系统已安装的中文字体（如 `Noto Sans CJK SC`、`SimHei` 等）。
- 若系统无中文字体，应用会自动下载并注册 `NotoSansCJKsc-Regular.otf` 到项目目录 `.fonts/`，用于图表中文渲染（无需 root）。
- 若自动下载失败，页面会显示告警与失败详情。

### 可选：系统级安装中文字体（Debian/Ubuntu）

如需统一系统字体，可执行：

`apt-get update && apt-get install -y fonts-noto-cjk`

安装后请重启 Streamlit 应用。
