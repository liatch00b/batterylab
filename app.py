import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import patches
from matplotlib import font_manager
import numpy as np
import os
import re
import sys
import subprocess
import urllib.request
import tempfile
import json
import shutil
from pathlib import Path

from utils.data_loader import loadMat, getBatteryCapacity, getBatteryValues

st.set_page_config(page_title="BatteryLab", layout="wide")
st.title("🔋 BatteryLab：电池健康预测仿真工坊")

st.markdown(
        """
<style>
:root {
    --ink: #22313f;
    --muted: #5c6b7a;
    --accent: #2b6777;
    --accent-soft: #d8e6ea;
    --surface: #ffffff;
    --surface-2: #f7f9fb;
}
html, body {
    font-family: "Source Han Serif SC", "Songti SC", "PingFang SC", "Heiti SC", serif;
    color: var(--ink);
}
h1, h2, h3, h4, h5, p, li, label, span, div[data-testid="stMarkdownContainer"] {
    font-family: "Source Han Serif SC", "Songti SC", "PingFang SC", "Heiti SC", serif;
}
h1, h2, h3, h4, h5 {
    font-family: "Source Han Sans SC", "PingFang SC", "Heiti SC", sans-serif;
    color: var(--accent);
    letter-spacing: 0.2px;
}
h1 { color: #1f4f5a; }
h2, h3 { color: var(--accent); }
p, li, .stMarkdown {
    color: var(--ink);
}
code, pre, .stMarkdown code, .stCode, .stCodeBlock {
    font-family: "Avenir Next Rounded", "SF Pro Rounded", "Nunito", "Quicksand", "Arial Rounded MT Bold", "PingFang SC", sans-serif;
}
span.material-symbols-outlined,
span.material-symbols-rounded,
i.material-icons {
    font-family: "Material Symbols Outlined", "Material Symbols Rounded", "Material Icons" !important;
}
a {
    color: var(--accent);
    text-decoration: none;
}
a:hover {
    color: #1f4f5a;
}
.hero {
    background: linear-gradient(120deg, #fef6e4 0%, #e3f2fd 100%);
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 18px;
}
.hero h3 { margin: 0 0 6px 0; }
.card-row { display: flex; gap: 10px; flex-wrap: wrap; }
.card {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 10px 12px;
    background: var(--surface);
    min-width: 160px;
    flex: 1;
}
.link-card { color: inherit; text-decoration: none; }
.link-card:hover { border-color: #b0bec5; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06); }
.card-title { font-weight: 600; margin-bottom: 4px; }
.section-title { margin-top: 18px; }
.nav-links a { display: block; margin: 6px 0; text-decoration: none; }
.tag { display: inline-block; background: var(--accent-soft); padding: 2px 6px; border-radius: 6px; color: var(--accent); }
.kpi { border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px 12px; background: var(--surface-2); }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: center !important; }
th { font-weight: 700; }
td:first-child { font-weight: 700; }
.hint-card { border: 1px solid #e0e0e0; border-radius: 10px; padding: 10px 12px; background: #ffffff; height: 100%; }
.hint-title { font-weight: 700; font-size: 14px; margin-bottom: 6px; }
.hint-body { font-size: 12px; line-height: 1.4; color: #333; }
.hl { color: var(--accent); font-weight: 700; }
.hl-warm { color: #a66c2b; font-weight: 700; }
.stMarkdown strong {
    background: #fff2a8;
    padding: 0 4px;
    border-radius: 4px;
}
.stButton > button {
    border-radius: 999px;
    border: 1px solid #d6dee3;
    background: linear-gradient(180deg, #ffffff 0%, #f3f6f8 100%);
    color: #2b3a42;
    padding: 0.35rem 0.9rem;
}
.stButton > button:hover {
    border-color: #b7c3cc;
    background: linear-gradient(180deg, #ffffff 0%, #e9eef2 100%);
}
</style>
        """,
        unsafe_allow_html=True
)

def configure_chinese_font_for_matplotlib():
    preferred_fonts = [
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "WenQuanYi Zen Hei",
        "Source Han Sans SC",
        "Source Han Sans CN",
        "Microsoft YaHei",
        "SimHei",
        "PingFang SC",
        "Heiti SC",
        "STHeiti",
        "Arial Unicode MS",
    ]
    installed_fonts = {font.name for font in font_manager.fontManager.ttflist}
    available_fonts = [name for name in preferred_fonts if name in installed_fonts]

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False

    if available_fonts:
        plt.rcParams["font.sans-serif"] = available_fonts + ["DejaVu Sans"]
        return available_fonts[0], None

    local_font_dir = Path(__file__).resolve().parent / ".fonts"
    local_font_path = local_font_dir / "NotoSansCJKsc-Regular.otf"
    font_url = (
        "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/"
        "NotoSansCJKsc-Regular.otf"
    )

    try:
        local_font_dir.mkdir(parents=True, exist_ok=True)
        if not local_font_path.exists():
            urllib.request.urlretrieve(font_url, str(local_font_path))

        font_manager.fontManager.addfont(str(local_font_path))
        font_manager._load_fontmanager(try_read_cache=False)

        refreshed_fonts = {font.name for font in font_manager.fontManager.ttflist}
        fallback_name = "Noto Sans CJK SC"
        if fallback_name in refreshed_fonts:
            plt.rcParams["font.sans-serif"] = [fallback_name, "DejaVu Sans"]
            return fallback_name, None
    except Exception as exc:
        return None, str(exc)

    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    return None, "字体文件已下载，但 Matplotlib 未识别到字体名称 Noto Sans CJK SC"


active_chinese_font, font_setup_error = configure_chinese_font_for_matplotlib()
if active_chinese_font is None:
    st.warning(
        "未检测到可用中文字体，且自动下载字体失败，Matplotlib 图表中的中文可能仍无法显示。"
        "可在 Debian/Ubuntu 环境执行：`apt-get update && apt-get install -y fonts-noto-cjk`，"
        "安装后重启应用。"
    )
    if font_setup_error:
        st.caption(f"字体初始化详情：{font_setup_error}")

#云端训练安装环境
APP_DIR = Path(__file__).resolve().parent
CODE_REPO_DIR = APP_DIR.parent / "代码作品集" / "2.3"
DEFAULT_RUL_REPO = CODE_REPO_DIR / "RUL_prediction-main"
DEFAULT_CNN_REPO = CODE_REPO_DIR / "CNN-ASTLSTM-main"
PRETRAINED_RUL_DIR = APP_DIR / "pretrained" / "rul_prediction"
HEYWHALE_RUL_URL = "https://www.heywhale.com/mw/project/69981707a1b39231ae4cc95b?shareby=6998159ba81373657c741dad#"
HEYWHALE_CNN_URL = "https://www.heywhale.com/mw/project/69981707a1b39231ae4cc95b?shareby=6998159ba81373657c741dad#"
LOCAL_COLAB_DIR = APP_DIR / "colab"
DATA_REPO_OWNER = os.getenv("DATALAB_REPO_OWNER", "liatch00b")
DATA_REPO_NAME = os.getenv("DATALAB_REPO_NAME", "batterylab")
DATA_REPO_BRANCH = os.getenv("DATALAB_REPO_BRANCH", "main")


# ---------- 数据加载与处理函数 ----------
def build_mock_rul_curve(cycles, base, decay, noise):
    # Simple synthetic curve for interactive visualization.
    trend = base * np.exp(-decay * cycles)
    jitter = np.sin(cycles / 6.0) * noise
    return np.maximum(trend + jitter, 0)


def build_mock_battery_data(name, total_cycles=120):
    seed = sum(ord(ch) for ch in name)
    rng = np.random.default_rng(seed)

    cycles = np.arange(1, total_cycles + 1)
    base_capacity = 2.05 + rng.normal(0, 0.02)
    slope = 0.0038 + rng.normal(0, 0.0002)
    capacities = base_capacity - slope * cycles + 0.015 * np.sin(cycles / 8.0)
    capacities = np.clip(capacities, 1.2, None)

    charge_data = []
    discharge_data = []
    for idx in range(total_cycles):
        time_axis = np.linspace(0, 3600, 140)

        charge_current = 1.55 + 0.12 * np.sin(time_axis / 330.0 + idx * 0.1)
        charge_current += rng.normal(0, 0.01, size=time_axis.shape)

        discharge_voltage = 4.2 - 0.00034 * time_axis - 0.0022 * idx
        discharge_voltage += 0.03 * np.sin(time_axis / 500.0 + idx * 0.06)
        discharge_voltage += rng.normal(0, 0.006, size=time_axis.shape)
        discharge_voltage = np.clip(discharge_voltage, 2.8, 4.25)

        charge_data.append({
            "Time": time_axis.tolist(),
            "Current_measured": charge_current.tolist(),
        })
        discharge_data.append({
            "Time": time_axis.tolist(),
            "Voltage_measured": discharge_voltage.tolist(),
        })

    return {
        "raw": [],
        "capacity": [cycles.tolist(), capacities.tolist()],
        "charge": charge_data,
        "discharge": discharge_data,
        "is_mock": True,
    }


def load_local_notebook(filename):
    notebook_path = LOCAL_COLAB_DIR / filename
    if not notebook_path.exists():
        return None
    return notebook_path.read_bytes()


def render_astlstm_diagram():
    fig, ax = plt.subplots(figsize=(10, 2.4))
    ax.set_axis_off()

    def add_box(x, y, w, h, text):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1,
            edgecolor="#4c4c4c",
            facecolor="#f2f2f2"
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)

    add_box(0.02, 0.25, 0.2, 0.5, "Input 输入\n(V/I/T/C)")
    add_box(0.28, 0.25, 0.18, 0.5, "CNN 特征\nFeature")
    add_box(0.52, 0.25, 0.18, 0.5, "ATS-LSTM 时序\nTemporal")
    add_box(0.76, 0.25, 0.22, 0.5, "Dense 输出\nSOH / RUL")

    ax.annotate("", xy=(0.28, 0.5), xytext=(0.22, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.52, 0.5), xytext=(0.46, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.76, 0.5), xytext=(0.70, 0.5), arrowprops={"arrowstyle": "->"})

    return fig


def render_cnn_diagram():
    fig, ax = plt.subplots(figsize=(10, 2.4))
    ax.set_axis_off()

    def add_box(x, y, w, h, text, color):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1,
            edgecolor="#3b3b3b",
            facecolor=color
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)

    add_box(0.02, 0.25, 0.22, 0.5, "Input 输入\nMatrix", "#f2f2f2")
    add_box(0.30, 0.25, 0.18, 0.5, "Conv 卷积\nFilters", "#e8f0fe")
    add_box(0.54, 0.25, 0.18, 0.5, "Pooling 池化", "#e9f7ef")
    add_box(0.78, 0.25, 0.20, 0.5, "Dense 输出\nOutput", "#fff3cd")

    ax.annotate("", xy=(0.30, 0.5), xytext=(0.24, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.54, 0.5), xytext=(0.48, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.78, 0.5), xytext=(0.72, 0.5), arrowprops={"arrowstyle": "->"})
    return fig


def render_lstm_diagram():
    fig, ax = plt.subplots(figsize=(10, 2.4))
    ax.set_axis_off()

    def add_box(x, y, w, h, text):
        rect = patches.FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.02,rounding_size=0.02",
            linewidth=1,
            edgecolor="#3b3b3b",
            facecolor="#f8f9fa"
        )
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=11)

    add_box(0.02, 0.25, 0.2, 0.5, "x(t-1)\n上一时刻输入")
    add_box(0.28, 0.25, 0.2, 0.5, "LSTM\n记忆单元")
    add_box(0.54, 0.25, 0.2, 0.5, "h(t)\n隐藏状态")
    add_box(0.78, 0.25, 0.2, 0.5, "Output\n输出")

    ax.annotate("", xy=(0.28, 0.5), xytext=(0.22, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.54, 0.5), xytext=(0.48, 0.5), arrowprops={"arrowstyle": "->"})
    ax.annotate("", xy=(0.78, 0.5), xytext=(0.72, 0.5), arrowprops={"arrowstyle": "->"})
    return fig


def format_py_value(value):
    if isinstance(value, str):
        return repr(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    return str(value)


def update_param_file(param_path, overrides):
    if not param_path.exists():
        return False, f"参数文件不存在: {param_path}"
    lines = param_path.read_text(encoding="utf-8").splitlines()
    found = set()
    for i, line in enumerate(lines):
        for key, value in overrides.items():
            pattern = rf"^(\s*{re.escape(key)}\s*=\s*).*$"
            match = re.match(pattern, line)
            if match:
                lines[i] = f"{match.group(1)}{format_py_value(value)}"
                found.add(key)
                break
    param_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    missing = [key for key in overrides.keys() if key not in found]
    if missing:
        return True, f"已更新参数，但未找到: {', '.join(missing)}"
    return True, "参数已更新"


def run_external_script(script_path, work_dir, timeout_sec):
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec if timeout_sec > 0 else None
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        return exc.stdout or "", f"运行超时（{timeout_sec}s）", 124
    except Exception as exc:
        return "", f"运行失败: {exc}", 1


def run_git_lfs_pull(repo_dir, timeout_sec=300):
    try:
        result = subprocess.run(
            ["git", "lfs", "pull"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", "未检测到 git 或 git lfs 命令，请先安装 Git LFS。", 127
    except subprocess.TimeoutExpired as exc:
        return exc.stdout or "", f"git lfs pull 运行超时（{timeout_sec}s）", 124
    except Exception as exc:
        return "", f"执行失败: {exc}", 1


def _is_git_lfs_pointer_file(file_path):
    try:
        with open(file_path, "rb") as f:
            return f.read(128).startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def _read_lfs_pointer_info(file_path):
    try:
        text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None, None

    oid_match = re.search(r"oid\s+sha256:([0-9a-f]{64})", text)
    size_match = re.search(r"size\s+(\d+)", text)
    if not oid_match:
        return None, None
    oid = oid_match.group(1)
    size = int(size_match.group(1)) if size_match else None
    return oid, size


def _download_lfs_object_via_batch(rel_path, target_path, oid, size):
    batch_url = f"https://github.com/{DATA_REPO_OWNER}/{DATA_REPO_NAME}.git/info/lfs/objects/batch"
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "ref": {"name": f"refs/heads/{DATA_REPO_BRANCH}"},
        "objects": [{"oid": oid, "size": size or 0}],
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.git-lfs+json",
        "Content-Type": "application/vnd.git-lfs+json",
        "User-Agent": "BatteryLab/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(
        batch_url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8", errors="ignore"))

    objects = result.get("objects", [])
    if not objects:
        return False, "LFS Batch API 未返回 objects。"

    obj0 = objects[0]
    if "error" in obj0:
        return False, f"LFS 对象访问失败：{obj0['error']}"

    action = obj0.get("actions", {}).get("download", {})
    download_url = action.get("href")
    if not download_url:
        return False, "LFS Batch API 未返回下载链接。"

    dl_headers = {"User-Agent": "BatteryLab/1.0"}
    action_headers = action.get("header", {})
    if isinstance(action_headers, dict):
        dl_headers.update(action_headers)

    dl_req = urllib.request.Request(download_url, headers=dl_headers)
    with urllib.request.urlopen(dl_req, timeout=120) as response:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mat") as tmp_file:
            tmp_file.write(response.read())
            tmp_name = tmp_file.name

    tmp_path = Path(tmp_name)
    if _is_git_lfs_pointer_file(tmp_path):
        tmp_path.unlink(missing_ok=True)
        return False, "LFS Batch 下载结果仍是指针文本。"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tmp_path), str(target_path))
    return True, ""


def _download_real_mat_from_github(rel_path, target_path):
    rel_path = rel_path.replace("\\", "/")
    urls = [
        (
            f"https://media.githubusercontent.com/media/"
            f"{DATA_REPO_OWNER}/{DATA_REPO_NAME}/{DATA_REPO_BRANCH}/{rel_path}"
        ),
        (
            f"https://raw.githubusercontent.com/"
            f"{DATA_REPO_OWNER}/{DATA_REPO_NAME}/{DATA_REPO_BRANCH}/{rel_path}"
        ),
    ]

    errors = []
    target_path.parent.mkdir(parents=True, exist_ok=True)

    for url in urls:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "BatteryLab/1.0"})
            with urllib.request.urlopen(request, timeout=60) as response:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mat") as tmp_file:
                    tmp_file.write(response.read())
                    tmp_name = tmp_file.name

            tmp_path = Path(tmp_name)
            if _is_git_lfs_pointer_file(tmp_path):
                tmp_path.unlink(missing_ok=True)
                errors.append(f"下载地址返回了 LFS 指针文本：{url}")
                continue

            shutil.move(str(tmp_path), str(target_path))
            return True, ""
        except Exception as exc:
            errors.append(f"{url} -> {exc}")

    oid, size = _read_lfs_pointer_info(target_path)
    if oid:
        try:
            ok, detail = _download_lfs_object_via_batch(rel_path, target_path, oid, size)
            if ok:
                return True, ""
            errors.append(f"LFS Batch API 下载失败：{detail}")
        except Exception as exc:
            errors.append(f"LFS Batch API 异常：{exc}")

    return False, " | ".join(errors) if errors else "未知下载错误"


def ensure_real_mat_file(mat_rel_path):
    full_path = APP_DIR / mat_rel_path
    if not full_path.exists():
        return False, f"数据文件不存在：{mat_rel_path}"
    if not _is_git_lfs_pointer_file(full_path):
        return True, ""
    return _download_real_mat_from_github(mat_rel_path, full_path)


def has_git_lfs():
    try:
        result = subprocess.run(
            ["git", "lfs", "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, ""
        message = (result.stderr or result.stdout or "").strip()
        return False, message
    except FileNotFoundError:
        return False, "未检测到 git 命令。"
    except Exception as exc:
        return False, str(exc)


def find_latest_eval_dir(base_dir):
    if not base_dir.exists():
        return None
    metrics_files = sorted(
        base_dir.glob("**/eval_metrics.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not metrics_files:
        return None
    return metrics_files[0].parent


def parse_eval_metrics(metrics_path):
    metrics = {}
    if not metrics_path.exists():
        return metrics
    text = metrics_path.read_text(encoding="utf-8")
    return parse_eval_metrics_text(text)


def parse_eval_metrics_text(text):
    metrics = {}
    patterns = {
        "MAE": r"Test Mean Absolute Error:\s*([0-9.]+)",
        "MSE": r"Test Mean Square Error:\s*([0-9.]+)",
        "MAPE": r"Test Mean Absolute Percentage Error:\s*([0-9.]+)",
        "RMSE": r"Test Root Mean Squared Error:\s*([0-9.]+)"
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            metrics[key] = float(match.group(1))
    return metrics


def load_predictions(eval_dir):
    pred_path = eval_dir / "test_predict.txt"
    true_path = eval_dir / "test_true.txt"
    if not pred_path.exists() or not true_path.exists():
        return None, None
    pred = np.loadtxt(pred_path)
    true = np.loadtxt(true_path)
    return true, pred


def load_pretrained_rul(model_name):
    model_dir = PRETRAINED_RUL_DIR / model_name
    metrics_path = model_dir / "eval_metrics.txt"
    pred_path = model_dir / "test_predict.txt"
    true_path = model_dir / "test_true.txt"
    if not (metrics_path.exists() and pred_path.exists() and true_path.exists()):
        return None, None, None
    metrics_text = metrics_path.read_text(encoding="utf-8", errors="ignore")
    metrics = parse_eval_metrics_text(metrics_text)
    pred = np.loadtxt(pred_path)
    true = np.loadtxt(true_path)
    return metrics, true, pred


# ---------- 侧边栏：模块导航 ----------
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "home"


def set_mode(mode):
    st.session_state["app_mode"] = mode


def safe_sidebar_radio(label, options, key):
    current_value = st.session_state.get(key)
    if current_value not in options:
        st.session_state[key] = options[0] if options else None
    return st.sidebar.radio(label, options, key=key)


st.sidebar.header("🧩 模块导航")
st.sidebar.button("主页", on_click=set_mode, args=("home",), use_container_width=True)
st.sidebar.button("学习模块", on_click=set_mode, args=("learning",), use_container_width=True)
st.sidebar.button("数据工坊", on_click=set_mode, args=("data",), use_container_width=True)
st.sidebar.button("复现模块", on_click=set_mode, args=("repro",), use_container_width=True)
st.sidebar.button("模拟仿真", on_click=set_mode, args=("sim",), use_container_width=True)
st.sidebar.button("进阶动手", on_click=set_mode, args=("advanced",), use_container_width=True)

app_mode = st.session_state.get("app_mode", "home")
if app_mode == "learning":
    st.sidebar.markdown("---")
    safe_sidebar_radio(
        "学习小节",
        ["深度学习", "CNN", "LSTM", "RUL 意义", "NASA 数据集", "指标", "参数", "小测"],
        key="learning_section"
    )
elif app_mode == "repro":
    st.sidebar.markdown("---")
    safe_sidebar_radio("复现小节", ["RUL_prediction", "CNN-ASTLSTM"], key="repro_section")
elif app_mode == "sim":
    st.sidebar.markdown("---")
    safe_sidebar_radio("仿真小节", ["参数可视化"], key="sim_section")
elif app_mode == "data":
    st.sidebar.markdown("---")
    safe_sidebar_radio(
        "数据视图",
        ["容量衰减曲线", "充电电流曲线", "放电电压曲线"],
        key="data_view"
    )
elif app_mode == "advanced":
    st.sidebar.markdown("---")
    safe_sidebar_radio(
        "任务等级",
        [
            "任务1：理解参数（⭐）",
            "任务2：流程练习（⭐）",
            "任务3：调参对比（lr + seq_len）（⭐⭐）",
            "任务4：层数与隐藏维度（⭐⭐⭐）",
            "任务5：综合优化·（⭐⭐⭐⭐ 挑战）",
            "代码差异练习：理解模型变化"
        ],
        key="advanced_task"
    )

# 定义电池MAT文件路径
mat_files = {
    "B0005": "data/B0005.mat",
    "B0006": "data/B0006.mat",
    "B0007": "data/B0007.mat",
    "B0018": "data/B0018.mat"
}


@st.cache_resource
def load_battery_data(name):
    matfile = mat_files[name]
    ok, detail = ensure_real_mat_file(matfile)
    if not ok:
        raise RuntimeError(
            "检测到 Git LFS 指针文件，且自动下载真实数据失败。"
            f"详情：{detail}"
        )
    raw_data = loadMat(matfile)
    capacity = getBatteryCapacity(raw_data)
    charge_data = getBatteryValues(raw_data, Type="charge")
    discharge_data = getBatteryValues(raw_data, Type="discharge")
    return {
        "raw": raw_data,
        "capacity": capacity,          # [cycles, capacities]
        "charge": charge_data,
        "discharge": discharge_data
    }


def render_data_workshop(view_mode=None):
    st.markdown('<div id="data"></div>', unsafe_allow_html=True)
    st.subheader("🧩 数据工坊")
    # 加载电池列表
    available_batteries = [name for name, path in mat_files.items() if os.path.exists(path)]
    if not available_batteries:
        st.error("未找到任何MAT文件！请将NASA数据集放在 `data/` 文件夹下。")
        return

    selected_battery = st.selectbox(
        "1. 选择电池",
        available_batteries,
        index=0
    )

    data = None
    try:
        data = load_battery_data(selected_battery)
    except Exception as exc:
        error_text = str(exc)
        is_lfs_pointer_error = "Git LFS 指针文件" in error_text

        if is_lfs_pointer_error and not st.session_state.get("_lfs_pull_attempted", False):
            st.session_state["_lfs_pull_attempted"] = True
            lfs_ok, _ = has_git_lfs()
            if lfs_ok:
                with st.spinner("检测到缺少真实数据，正在自动同步数据..."):
                    _, _, return_code = run_git_lfs_pull(APP_DIR)
                if return_code == 0:
                    load_battery_data.clear()
                    st.rerun()

        st.error(f"数据加载失败：{error_text}")
        st.info("请为部署环境安装 git-lfs，并重新部署后重试。")
        return

    if view_mode is None:
        view_mode = st.radio(
            "2. 选择视图",
            ["容量衰减曲线", "充电电流曲线", "放电电压曲线"]
        )
    else:
        st.caption(f"当前视图：{view_mode}")

    if view_mode in ["充电电流曲线", "放电电压曲线"]:
        if view_mode == "充电电流曲线":
            max_cycles = len(data["charge"])
        else:
            max_cycles = len(data["discharge"])

        if max_cycles == 0:
            st.warning("该电池无对应类型数据")
            selected_cycles = []
        else:
            default_cycles = list(range(min(3, max_cycles)))
            selected_cycles = st.multiselect(
                f"选择要显示的循环序号 (0 ~ {max_cycles - 1})",
                options=list(range(max_cycles)),
                default=default_cycles
            )
    else:
        selected_cycles = []

    if view_mode == "容量衰减曲线":
        show_split = st.checkbox("显示训练/测试划分", value=False)
        total_cycles = len(data["capacity"][0])
        if show_split:
            train_ratio = st.slider("训练集比例 (%)", 20, 90, 70, 5)
            split_idx = int(total_cycles * train_ratio / 100)
            eol_mode = st.radio("EOL阈值设置", ["固定值 (1.38Ah)", "动态阈值 (初始容量的80%)"])
            if eol_mode == "固定值 (1.38Ah)":
                eol_threshold = 1.38
            else:
                eol_threshold = data["capacity"][1][0] * 0.8

            eol_cycle_count = total_cycles
            for i, cap in enumerate(data["capacity"][1]):
                if cap <= eol_threshold:
                    eol_cycle_count = i + 1
                    break
            if split_idx > eol_cycle_count:
                split_idx = eol_cycle_count
                train_ratio = int(round(split_idx / total_cycles * 100)) if total_cycles else 0
                st.warning("训练集样本数不能超过真实失效循环数，已自动调整。")
        else:
            train_ratio = None
            split_idx = None
            eol_threshold = None
    else:
        train_ratio = None
        split_idx = None
        eol_threshold = None

    st.subheader(f"📈 {selected_battery} - {view_mode}")

    fig, ax = plt.subplots(figsize=(12, 5))

    if view_mode == "容量衰减曲线":
        cycles = data["capacity"][0]
        capacities = data["capacity"][1]
        ax.plot(cycles, capacities, "b-", label="Full lifecycle", alpha=0.6, linewidth=2)
        if show_split and split_idx is not None:
            ax.plot(cycles[:split_idx], capacities[:split_idx], "g-", label=f"Train ({train_ratio}%)", linewidth=2.5)
            ax.plot(cycles[split_idx:], capacities[split_idx:], "r--", label=f"Test ({100 - train_ratio}%)", linewidth=2)
            ax.axhline(y=eol_threshold, color="purple", linestyle=":", linewidth=2, label=f"EOL threshold = {eol_threshold:.2f}Ah")
            ax.axvline(x=split_idx, color="gray", linestyle="--", alpha=0.7)
            ax.text(split_idx + 2, ax.get_ylim()[1] * 0.9, f"Split\n{split_idx} cycles", fontsize=9)
        ax.set_xlabel("Cycle")
        ax.set_ylabel("Capacity (Ah)")
        ax.set_title(f"{selected_battery} Capacity degradation")

    elif view_mode == "充电电流曲线":
        if not selected_cycles:
            ax.text(0.5, 0.5, "请在上方选择要显示的循环", ha="center", va="center", transform=ax.transAxes)
        else:
            color_list = ["b", "g", "r", "c", "m", "y"]
            for i, cycle_idx in enumerate(selected_cycles):
                if cycle_idx < len(data["charge"]):
                    cycle_data = data["charge"][cycle_idx]
                    ax.plot(cycle_data["Time"], cycle_data["Current_measured"],
                            color=color_list[i % len(color_list)],
                            label=f"Cycle {cycle_idx}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Current (A)")
            ax.set_title(f"{selected_battery} Charge current (multiple cycles)")

    elif view_mode == "放电电压曲线":
        if not selected_cycles:
            ax.text(0.5, 0.5, "请在上方选择要显示的循环", ha="center", va="center", transform=ax.transAxes)
        else:
            color_list = ["b", "g", "r", "c", "m", "y"]
            for i, cycle_idx in enumerate(selected_cycles):
                if cycle_idx < len(data["discharge"]):
                    cycle_data = data["discharge"][cycle_idx]
                    ax.plot(cycle_data["Time"], cycle_data["Voltage_measured"],
                            color=color_list[i % len(color_list)],
                            label=f"Cycle {cycle_idx}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Voltage (V)")
            ax.set_title(f"{selected_battery} Discharge voltage (multiple cycles)")

    ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)

    if view_mode == "容量衰减曲线":
        if show_split and split_idx is not None:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总循环数", len(data["capacity"][0]))
            with col2:
                st.metric("训练集样本", split_idx)
            with col3:
                st.metric("测试集样本", len(data["capacity"][0]) - split_idx)
            with col4:
                st.metric("初始容量", f"{data['capacity'][1][0]:.2f} Ah")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总循环数", len(data["capacity"][0]))
            with col2:
                st.metric("初始容量", f"{data['capacity'][1][0]:.2f} Ah")
    else:
        total_cycles = len(data["charge"]) if view_mode == "充电电流曲线" else len(data["discharge"])
        st.info(f"该电池共有 {total_cycles} 个{'充电' if view_mode == '充电电流曲线' else '放电'}循环数据")

    st.caption("数据来源：NASA PCoE 公开数据集。")


def render_home():
    st.subheader("请选择模块")
    cols = st.columns(5)
    with cols[0]:
        st.button("📚 学习模块", on_click=set_mode, args=("learning",), use_container_width=False)
    with cols[1]:
        st.button("🧩 数据工坊", on_click=set_mode, args=("data",), use_container_width=False)
    with cols[2]:
        st.button("🧪 复现模块", on_click=set_mode, args=("repro",), use_container_width=False)
    with cols[3]:
        st.button("🧪 模拟仿真", on_click=set_mode, args=("sim",), use_container_width=False)
    with cols[4]:
        st.button("💪 进阶动手", on_click=set_mode, args=("advanced",), use_container_width=False)
    st.caption("点击按钮进入模块")

def render_learning_module(section=None):
    st.markdown('<div id="learning"></div>', unsafe_allow_html=True)
    st.subheader("📚 学习模块：基础概念速览")
    st.markdown("**你将学到：** 深度学习、CNN、LSTM 的核心概念，以及 **RUL** 预测的意义。")

    sections = ["深度学习", "CNN", "LSTM", "RUL 意义", "NASA 数据集", "指标", "参数", "小测"]
    current = section if section in sections else sections[0]

    if current == "深度学习":
        st.markdown("### 深度学习是什么？")
        st.markdown(
            """
深度学习是一类通过多层神经网络自动学习特征的机器学习方法。
它能从原始数据中提取高层表示，用于分类、预测或序列建模。
            """
        )
        st.markdown(
            """
**学习重点：**<span class="hl">自动特征学习</span> 和 <span class="hl">多层非线性表示</span>。
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            """
自动特征学习：模型会从原始序列里自己寻找规律，例如电压曲线的形状、拐点、变化速率等，不需要人工手写规则。

多层非线性表示：前几层学“局部形状/短期变化”，更深层学“整体趋势/长期退化”。层数越深，表达的模式越复杂。
            """
        )
        st.markdown("**基本公式：前向传播**")
        st.markdown(
            r"""
$$
\mathbf{h}^{(l)} = f(\mathbf{W}^{(l)}\mathbf{h}^{(l-1)} + \mathbf{b}^{(l)}),\quad
\hat{y}=g(\mathbf{W}^{(L)}\mathbf{h}^{(L-1)}+\mathbf{b}^{(L)})
$$
            """
        )
        st.markdown(
            """
**符号说明**
- $\mathbf{h}^{(l)}$：第 $l$ 层的隐藏表示该层输出，是网络在这一层提取到的特征
- $\mathbf{h}^{(l-1)}$：上一层输出，说明特征是逐层叠加得到的
- $\mathbf{W}^{(l)}$：第 $l$ 层权重矩阵，决定哪些特征“更重要”，训练会学习它
- $\mathbf{b}^{(l)}$：偏置向量，允许模型在没有输入信号时也能做出合适输出
- $f(\cdot)$：激活函数，让模型具备非线性表达能力，否则只能做线性拟合
- $\hat{y}$：模型预测值，用于和真实值比较计算误差
- $\mathbf{W}^{(L)},\mathbf{b}^{(L)}$：输出层权重与偏置，把隐藏特征变成最终预测
- $g(\cdot)$：输出层激活函数，回归通常用线性函数确保数值可连续变化
            """
        )
    elif current == "CNN":
        st.markdown("### CNN 是什么？")
        st.markdown(
            """
卷积神经网络（CNN）擅长从局部区域提取模式，例如曲线的形状、峰值、突变等。
在电池场景中，CNN 可以提取电压/电流序列中的局部特征。
            """
        )
        st.markdown(
            """
CNN 是<span class="hl">局部模式检测器</span>，能捕捉“局部形状”。
            """,
            unsafe_allow_html=True
        )
        st.markdown("**卷积公式**")
        st.markdown(
            r"""
$$
(\mathbf{x} * \mathbf{w})(t) = \sum_{k} \mathbf{x}(t-k)\,\mathbf{w}(k)
$$
            """
        )
        st.markdown(
            """
**符号说明**
- $\mathbf{x}$：输入序列，如电压/电流时间序列，是原始信号
- $\mathbf{w}$：卷积核（可学习参数），相当于“模式检测器”
- $t$：时间位置/索引，表示当前位置的输出
- $k$：卷积核索引，用来遍历局部窗口
- $(\mathbf{x} * \mathbf{w})(t)$：在位置 $t$ 的卷积输出，表示该窗口的局部特征强度
            """
        )
        st.pyplot(render_cnn_diagram())
    elif current == "LSTM":
        st.markdown("### LSTM 是什么？")
        st.markdown(
            """
长短期记忆网络（LSTM）用于时间序列建模，可以“记住”过去信息，
适合学习电池容量随循环变化的长期依赖。
            """
        )
        st.markdown(
            """
LSTM 通过门控机制实现<span class="hl">长期依赖建模</span>。
            """,
            unsafe_allow_html=True
        )
        st.markdown("**LSTM 关键公式：门控机制**")
        st.markdown(
            r"""
$$
\begin{aligned}
\mathbf{f}_t &= \sigma(\mathbf{W}_f[\mathbf{h}_{t-1},\mathbf{x}_t]+\mathbf{b}_f) \\
\mathbf{i}_t &= \sigma(\mathbf{W}_i[\mathbf{h}_{t-1},\mathbf{x}_t]+\mathbf{b}_i) \\
\widetilde{\mathbf{c}}_t &= \tanh(\mathbf{W}_c[\mathbf{h}_{t-1},\mathbf{x}_t]+\mathbf{b}_c) \\
\mathbf{c}_t &= \mathbf{f}_t\odot \mathbf{c}_{t-1} + \mathbf{i}_t\odot \tilde{\mathbf{c}}_t \\
\mathbf{o}_t &= \sigma(\mathbf{W}_o[\mathbf{h}_{t-1},\mathbf{x}_t]+\mathbf{b}_o) \\
\mathbf{h}_t &= \mathbf{o}_t\odot \tanh(\mathbf{c}_t)
\end{aligned}
$$
            """
        )
        st.markdown(
            """
**符号说明**
- $\mathbf{x}_t$：时刻 $t$ 的输入（当前时间点的观测）
- $\mathbf{h}_{t-1},\mathbf{h}_t$：上一步/当前的隐藏状态，表示短期信息
- $\mathbf{c}_{t-1},\mathbf{c}_t$：上一步/当前的记忆单元，保存长期信息
- $\mathbf{f}_t$：遗忘门，控制“过去信息保留多少”
- $\mathbf{i}_t$：输入门，控制“新信息写入多少”
- $\mathbf{o}_t$：输出门，控制“当前输出暴露多少”
- $\widetilde{\mathbf{c}}_t$：候选记忆，用于更新长期记忆
- $\mathbf{W}_f, \mathbf{W}_i, \mathbf{W}_c, \mathbf{W}_o$：各门的权重矩阵，决定门如何响应输入
- $\mathbf{b}_f, \mathbf{b}_i, \mathbf{b}_c, \mathbf{b}_o$：各门的偏置向量，提供基线响应
- $\sigma(\cdot)$：Sigmoid 函数，输出 0~1 的“开关系数”
- $\tanh(\cdot)$：将数值压到 -1~1，稳定训练
- $\odot$：逐元素乘法，用于门控筛选信息
            """
        )
        st.pyplot(render_lstm_diagram())
    elif current == "RUL 意义":
        st.markdown("### 为什么要预测 **RUL**？")
        st.markdown(
            """
**RUL**（Remaining Useful Life）表示电池从当前状态到失效的剩余寿命。
预测 **RUL** 有助于：
            """
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="kpi"><div class="card-title">安全</div>提前预警</div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="kpi"><div class="card-title">成本</div>优化维护</div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="kpi"><div class="card-title">效率</div>减少停机</div>', unsafe_allow_html=True)

        st.markdown("### CNN + LSTM 如何应用于 RUL 预测？")
        st.markdown(
            """
CNN 负责捕捉局部形状特征，LSTM 负责建模时间序列趋势，
二者组合能同时学习“局部模式”和“长期变化”。
            """
        )
        st.markdown(
            """CNN 学习数据的<span class="hl">局部形状</span>，LSTM 学习数据的<span class="hl">长期趋势</span>。
            """,
            unsafe_allow_html=True
        )
        st.pyplot(render_astlstm_diagram())
    elif current == "NASA 数据集":
        st.markdown("### 认识 NASA 电池数据集")
        st.markdown(
            """
NASA PCoE Battery Dataset 由 NASA Prognostics Center of Excellence (PCoE) 与 NASA Ames Research Center 提供，
包含多节 18650 锂离子电池在恒定室温下的充放电循环数据。

**核心特征**
- 每节电池持续循环至容量降至额定容量的约 70%
- 单次循环包含：恒流充电 → 恒压充电 → 静置 → 恒流放电
- 记录电压、电流、温度、容量等时间序列数据

**适用方向**
- 仅用容量序列实现单变量 RUL 预测
- 结合电压/电流曲线特征多变量融合预测
- 退化建模与早期算法验证
            """
        )
        st.markdown("**数据分组与典型样本**")
        st.markdown(
            """
| 数据集（6组） | 典型电池编号 | 温度 | 放电模式 | 总循环数（至EOL） | 数据特点与关键现象 | 备注 |
|---|---|---|---|---|---|---|
| PCoE（6组） | B0005 B0006 B0007 | 室温 | 恒定电流（2A） | ～168 | 容量衰减平滑、规律，噪声小。是最经典理想的学习样本 | 线性回归、指数平滑趋势预测 CNN/LSTM 时间序列预测入门理解 EOL 阈值、滑动窗口、训练/测试集划分等基础概念 |
|  | B0018 | 室温 | 可变电流（脉冲负载） | ～132 | 衰减后期出现明显的容量再生波动 | 展示容量再生现象对预测的干扰验证 + 残差验证、滤波算法处理波动的有效性 |
|  | B0025 B0026 B0027 B0028 | 室温 | 可变负载（DST等） | 不等 | 使用动态应力测试（DST）等复杂工况，衰减曲线更具波动性 | 对比不同放电模式对电池老化的影响，多变量模型的尝试 |
| Randomized Usage（7组） | RW#系列 | 室温/40°C | 完全随机电流（0.5-4A） | 约100-200 | 高度模拟真实使用场景，非线性强、噪声大 | 测试模型在非平稳、随机工况下的性能；工程应用中模型过拟合与泛化的平衡 |
            """
        )
        st.markdown(
            """
关注<span class="hl">容量衰减</span>与<span class="hl">工况差异</span>对模型的影响。
            """,
            unsafe_allow_html=True
        )
    elif current == "指标":
        st.markdown("### 训练损失与评估指标")
        st.markdown(
            r"""
常用回归损失与指标：
$$
\mathrm{MSE}=\frac{1}{N}\sum_{i=1}^N (y_i-\hat{y}_i)^2,\quad
\mathrm{RMSE}=\sqrt{\mathrm{MSE}},\quad
\mathrm{MAE}=\frac{1}{N}\sum_{i=1}^N |y_i-\hat{y}_i|
$$
            """
        )
        st.markdown(
            """
**符号说明**
- $N$：样本数量，越大统计越稳定
- $y_i$：第 $i$ 个样本的真实值
- $\hat{y}_i$：第 $i$ 个样本的预测值
            """
        )
        st.markdown(
            """
**RMSE（均方根误差）**：更敏感于大误差，能强调预测中的“严重偏差”。

**MAE（平均绝对误差）**：直接反映平均偏差大小，易解释、对异常值不如 RMSE 敏感。
            """
        )
    elif current == "参数":
        st.markdown("### 参数含义速查")
        st.markdown(
            """
| 参数 | 含义 | 变大会怎样 | 变小会怎样 |
|---|---|---|---|
| epochs | 训练轮数 | 训练更充分，但更慢 | 训练不足，可能欠拟合 |
| batch_size | 每次更新使用的样本数 | 更稳定但可能泛化差 | 噪声更大但泛化好 |
| lr | 学习率 | 太大易发散 | 太小收敛慢 |
| seq_len | 序列窗口长度 | 捕获更长期依赖 | 更局部、信息少 |
| hop | 滑动步长 | 训练样本少、快 | 样本多、慢 |
| sample | 采样间隔/降采样 | 抗噪更强 | 更细节但噪声多 |
| layers | 层数 | 表达力强但易过拟合 | 表达力不足 |
| hidden_dim | 隐藏维度 | 模型容量更大 | 容量更小 |
| k-fold | 交叉验证折数 | 评估更稳定但更慢 | 评估不稳定 |
            """
        )
    elif current == "小测":
        st.markdown("### 小测验")
        st.markdown("每题只需选择一个选项，然后点击提交：")
        questions = [
            {
                "q": "Q1: 深度学习的核心特点是？",
                "options": ["手工设计特征", "通过多层网络自动学习特征", "只做线性回归", "只用于图像"],
                "answer": "通过多层网络自动学习特征",
                "section": "深度学习"
            },
            {
                "q": "Q2: CNN 最擅长做什么？",
                "options": ["建模长期依赖", "提取局部模式", "聚类", "贝叶斯推断"],
                "answer": "提取局部模式",
                "section": "CNN"
            },
            {
                "q": "Q3: LSTM 主要解决什么问题？",
                "options": ["提取局部空间特征", "建模时间序列的长期依赖", "图像分割", "聚类"],
                "answer": "建模时间序列的长期依赖",
                "section": "LSTM"
            },
            {
                "q": "Q4: RUL 的含义是？",
                "options": ["电池当前电压", "剩余可用寿命", "充电时间", "环境温度"],
                "answer": "剩余可用寿命",
                "section": "RUL 意义"
            },
            {
                "q": "Q5: MAE 代表什么？",
                "options": ["平均绝对误差", "均方误差", "均方根误差", "平均相对误差"],
                "answer": "平均绝对误差",
                "section": "指标"
            },
            {
                "q": "Q6: RMSE 更敏感于什么？",
                "options": ["小误差", "大误差", "缺失值", "学习率"],
                "answer": "大误差",
                "section": "指标"
            },
            {
                "q": "Q7: 学习率太大可能导致什么？",
                "options": ["收敛过慢", "训练发散", "模型过拟合", "显存不足"],
                "answer": "训练发散",
                "section": "参数"
            },
            {
                "q": "Q8: batch_size 变大一般会？",
                "options": ["更稳定但可能泛化差", "更不稳定但泛化更好", "必然更快更准", "不影响训练"],
                "answer": "更稳定但可能泛化差",
                "section": "参数"
            },
            {
                "q": "Q9: seq_len 表示什么？",
                "options": ["序列窗口长度", "学习率", "隐藏维度", "训练轮数"],
                "answer": "序列窗口长度",
                "section": "参数"
            },
            {
                "q": "Q10: hop 增大通常会？",
                "options": ["样本更多、训练更慢", "样本更少、训练更快", "不影响样本数量", "只影响测试集"],
                "answer": "样本更少、训练更快",
                "section": "参数"
            },
            {
                "q": "Q11: NASA PCoE 数据集主要包含什么电池？",
                "options": ["18650 锂离子电池", "镍氢电池", "铅酸电池", "固态电池"],
                "answer": "18650 锂离子电池",
                "section": "NASA 数据集"
            },
            {
                "q": "Q12: 单次循环包含的流程是？",
                "options": ["恒流充电→恒压充电→静置→恒流放电", "恒压充电→恒流充电→放电", "恒流放电→恒压放电", "随机充放电"],
                "answer": "恒流充电→恒压充电→静置→恒流放电",
                "section": "NASA 数据集"
            },
            {
                "q": "Q13: CNN + LSTM 组合中，CNN 的主要作用是？",
                "options": ["建模长期依赖", "提取局部形状特征", "直接输出 RUL", "减少数据量"],
                "answer": "提取局部形状特征",
                "section": "RUL 意义"
            },
            {
                "q": "Q14: MSE 的含义是？",
                "options": ["平均绝对误差", "平方误差平均", "均方根误差", "平均相对误差"],
                "answer": "平方误差平均",
                "section": "指标"
            },
            {
                "q": "Q15: hidden_dim 变大一般会？",
                "options": ["模型容量更大", "一定更快", "一定更稳定", "不影响模型"],
                "answer": "模型容量更大",
                "section": "参数"
            },
            {
                "q": "Q16: B0018 的典型特点是？",
                "options": ["容量衰减平滑", "后期出现容量再生波动", "无测试数据", "只在40°C"],
                "answer": "后期出现容量再生波动",
                "section": "NASA 数据集"
            },
            {
                "q": "Q17: Randomized Usage 数据的主要作用是？",
                "options": ["检验模型在随机工况下的泛化", "只用于训练集", "减少噪声", "只做可视化"],
                "answer": "检验模型在随机工况下的泛化",
                "section": "NASA 数据集"
            },
            {
                "q": "Q18: RUL 预测的价值不包括？",
                "options": ["提前预警", "优化维护", "减少停机", "保证电池永不衰退"],
                "answer": "保证电池永不衰退",
                "section": "RUL 意义"
            },
            {
                "q": "Q19: LSTM 的门控机制主要用于？",
                "options": ["控制信息保留与遗忘", "提取空间特征", "改变输入维度", "替代卷积"],
                "answer": "控制信息保留与遗忘",
                "section": "LSTM"
            },
            {
                "q": "Q20: 卷积核的作用是？",
                "options": ["滑动提取局部模式", "生成随机噪声", "降低学习率", "替代激活函数"],
                "answer": "滑动提取局部模式",
                "section": "CNN"
            }
        ]

        answers = {}
        for idx, item in enumerate(questions, 1):
            answers[idx] = st.selectbox(item["q"], item["options"], key=f"quiz_{idx}")

        if st.button("提交答案"):
            wrong = []
            for idx, item in enumerate(questions, 1):
                if answers[idx] != item["answer"]:
                    wrong.append((idx, item["section"]))

            correct = len(questions) - len(wrong)
            if not wrong:
                st.success("太棒了天才！20 题全对！")
            else:
                st.warning(f"答对 {correct}/20。以下错题可以在对应板块找到答案：")
                st.markdown("\n".join([f"- Q{i}：请回到「{sec}」板块复习" for i, sec in wrong]))

def render_reproduction_module(section=None):
    st.markdown('<div id="repro"></div>', unsafe_allow_html=True)
    st.subheader("🧪 复现模块")
    st.info("点击链接即可运行在线 notebook")

    sections = ["RUL_prediction", "CNN-ASTLSTM"]
    current = section if section in sections else sections[0]
    st.caption(f"当前小节：{current}")

    if current == "RUL_prediction":
        st.markdown(
            """
<div class="card-row">
    <div class="card"><div class="card-title">Heywhale</div><a target="_blank" href="{rul}">NASA｜RUL_prediction 开源论文教学复现实例</a></div>
</div>
            """.format(rul=HEYWHALE_RUL_URL),
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("### RUL_prediction（CNN/LSTM 混合框架）")
        st.markdown(
            """
**任务目标**
- 输入：每个循环的电压 V、电流 I、温度 T、容量 C 的时间序列特征
- 输出：下一循环容量或剩余寿命（RUL）的回归预测

**模型结构**
- SC/MC：SC 使用单通道（V+C），MC 使用多通道（V/I/T/C）
- LSTM 负责建模长期时序依赖，CNN 负责捕捉局部形状特征
- CNN+LSTM 先提取局部模式，再在时间维度上建模趋势

**训练思路**
- 滑动窗口切片（`seq_len`、`hop`）构造样本
- 交叉验证（`k-fold`）验证稳定性
- 关注 MAE / RMSE 等误差指标进行对比
            """
        )
    else:
        st.markdown(
            """
<div class="card-row">
    <div class="card"><div class="card-title">Heywhale</div><a target="_blank" href="{cnn}">CNN-ASTLSTM 在线 Notebook</a></div>
</div>
            """.format(cnn=HEYWHALE_CNN_URL),
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("### CNN-ASTLSTM（注意力时序建模）")
        st.markdown(
            """
**任务目标**
- 通过容量曲线与充放电特征估计 SOH 与 RUL

**模型结构**
- CNN 提取局部退化形状特征
- ATS-LSTM 作为注意力时序单元，强调关键时间片的贡献
- 输出层回归容量衰减或剩余寿命
            """
        )

def render_advanced_practice_module(task_index=None):
    st.markdown('<div id="advanced"></div>', unsafe_allow_html=True)
    st.subheader("💪 进阶挑战")
    st.markdown(
        """
**学习要点预览**
- 数据流程：样本构造、切分、预处理
- 训练评估：loss/MAE 的解读与对比
- 调参与结构：学习率、序列长度、模型容量
        """
    )
    st.markdown("**一键跳转 Notebook（在线运行）**")
    st.info("如果在线 Notebook 出现图像不显示：请先刷新页面，再从依赖安装单元开始依次重新运行。")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            f"""
<a href="{HEYWHALE_RUL_URL}" target="_blank" class="link-card">
    <div class="card">
        <div class="card-title">RUL_prediction</div>
        打开 RUL 预测 Notebook
    </div>
</a>
            """,
            unsafe_allow_html=True
        )
    with col_b:
        st.markdown(
            f"""
<a href="{HEYWHALE_CNN_URL}" target="_blank" class="link-card">
    <div class="card">
        <div class="card-title">CNN-ASTLSTM</div>
        打开 CNN-ASTLSTM Notebook
    </div>
</a>
            """,
            unsafe_allow_html=True
        )

    tasks = [
        {
            "title": "任务1：理解参数（⭐）",
            "description": "在这个任务中，我们要理解三个关键参数：**seq_len**（序列窗口长度）、**lr**（学习率）、**epochs**（训练轮数）。",
            "objective": "阅读代码，找出这三个参数在代码中的位置并运行模型，观察训练曲线与输出并理解含义。",
            "code": r"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

# 生成一条“虚拟容量衰减曲线”
np.random.seed(42)
n_cycles = 220
cycles = np.arange(n_cycles)
capacity_data = 1.6 - 0.0025 * cycles + 0.03 * np.sin(cycles / 6) + 0.01 * np.random.randn(n_cycles)
capacity_data = np.clip(capacity_data, 0.9, None)

# ============ 关键参数 ============
seq_len = 10      # 序列窗口长度：用过去多少个 cycle 预测下一个
lr = 0.001        # 学习率：参数更新的步长，太大易发散，太小收敛慢
epochs = 50       # 训练轮数：扫过整个数据集多少次

# 构造样本
def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

# 数据预处理
X, y = create_sequences(capacity_data, seq_len)
X = X.reshape((X.shape[0], X.shape[1], 1))
scaler = StandardScaler()
X = scaler.fit_transform(X.reshape(-1, 1)).reshape(X.shape)

# 构建LSTM模型
model = Sequential([
    LSTM(64, activation='relu', input_shape=(seq_len, 1)),
    Dense(1)
])

# 编译模型
model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])

# 训练模型
history = model.fit(X, y, epochs=epochs, batch_size=32, validation_split=0.2, verbose=1)

# 可视化训练曲线
import matplotlib.pyplot as plt
plt.figure(figsize=(8, 4))
plt.plot(history.history['loss'], label='train loss')
plt.plot(history.history['val_loss'], label='val loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title(f'seq_len={seq_len}, lr={lr}, epochs={epochs}')
plt.show()
            """,
            "hints": [
                "🔍 找到代码中的这一行：`seq_len = 10` - 这控制了看多少个历史cycle来预测",
                "🔍 找到代码中的这一行：`lr = 0.001` - 这控制了学习速度",
                "🔍 找到代码中的这一行：`epochs = 50` - 这控制了训练次数",
                "✅ 观察变化：lr 变大更易振荡/发散，epochs 变大曲线更长但可能过拟合，seq_len 变大样本变少、趋势更长"
            ],
            "verification": [
                "✅ 代码成功运行，打印出 model.fit() 的输出",
                "✅ 画出 loss / val_loss 曲线，观察变化趋势",
                "✅ 记录最后一个 epoch 的损失值"
            ]
        },
        {
            "title": "任务2：流程练习（⭐）",
            "description": "在调参前先熟悉完整机器学习流程：样本构造 → 数据切分 → 预处理 → 建模 → 训练 → 评估。",
            "objective": "运行自包含脚本，并指出每个流程步骤在代码中的位置。",
            "code": r"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

# ============ 自包含虚拟数据 ============
np.random.seed(42)
n_cycles = 220
cycles = np.arange(n_cycles)
capacity_data = 1.62 - 0.0026 * cycles + 0.03 * np.sin(cycles / 6.5) + 0.01 * np.random.randn(n_cycles)
capacity_data = np.clip(capacity_data, 0.9, None)

seq_len = 10
lr = 0.001
epochs = 30

def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

# ============ 机器学习完整流程 ============
# 构造样本
X, y = create_sequences(capacity_data, seq_len)
X = X.reshape((X.shape[0], X.shape[1], 1))

# 训练测试集分割
split_idx = int(len(X) * 0.7)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

# 数据预处理
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)

# 构建模型
model = Sequential([
    LSTM(64, activation='relu', input_shape=(seq_len, 1)),
    Dense(1)
])
model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])

# 训练
model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)

# 评估
y_pred = model.predict(X_test, verbose=0).flatten()
mae = mean_absolute_error(y_test, y_pred)
print(f"MAE = {mae:.6f}")

plt.figure(figsize=(8, 3))
plt.plot(y_test, label='true')
plt.plot(y_pred, label='pred')
plt.title('Prediction vs True')
plt.legend()
plt.show()
            """,
            "hints": [
                "💡 先用注释标出每个流程步骤，再运行代码。",
                "💡 如果图不显示：刷新在线 notebook 并从依赖安装单元重新运行。",
                "💡 观察 MAE 大致范围即可，不需要追求最小值。"
            ],
            "verification": [
                "✅ 能指出 6 个流程步骤在代码中的位置",
                "✅ 成功输出 MAE 并绘制预测对比图",
                "✅ 用一句话总结本流程的作用"
            ]
        },
        {
            "title": "任务3：调参对比（lr + seq_len）（⭐⭐）",
            "description": "把学习率与序列长度放在同一个任务里系统比较，理解两类参数对效果的不同影响。",
            "objective": "运行自包含脚本，分别完成多学习率对比和多序列长度对比，并写出推荐值。",
            "code": r"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

# ============ 自包含虚拟数据 ============
np.random.seed(42)
n_cycles = 240
cycles = np.arange(n_cycles)
capacity_data = 1.6 - 0.0026 * cycles + 0.03 * np.sin(cycles / 6.0) + 0.01 * np.random.randn(n_cycles)
capacity_data = np.clip(capacity_data, 0.9, None)

def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

def train_with_params(lr, seq_len=10, epochs=30):
    X, y = create_sequences(capacity_data, seq_len)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    scaler = StandardScaler()
    X = scaler.fit_transform(X.reshape(-1, 1)).reshape(X.shape)

    model = Sequential([
        LSTM(64, activation='relu', input_shape=(seq_len, 1)),
        Dense(1)
    ])
    model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])

    history = model.fit(
        X, y,
        epochs=epochs,
        batch_size=32,
        validation_split=0.2,
        verbose=0
    )
    return history

# ============ A. 学习率对比 ============
lr_list = [0.0005, 0.001, 0.005, 0.01]
lr_hist = {}

for lr in lr_list:
    print(f"Training with lr={lr} ...")
    lr_hist[lr] = train_with_params(lr, seq_len=10, epochs=30)

plt.figure(figsize=(10, 4))
for lr, hist in lr_hist.items():
    plt.plot(hist.history['val_loss'], label=f'lr={lr}')
plt.xlabel('Epoch')
plt.ylabel('Validation Loss')
plt.title('Learning Rate Comparison')
plt.legend()
plt.grid(alpha=0.3)
plt.show()

# ============ B. 序列长度对比 ============
seq_list = [5, 10, 15, 20]
seq_hist = {}

for seq_len in seq_list:
    print(f"Training with seq_len={seq_len} ...")
    seq_hist[seq_len] = train_with_params(0.001, seq_len=seq_len, epochs=30)

plt.figure(figsize=(10, 4))
for seq_len, hist in seq_hist.items():
    plt.plot(hist.history['val_loss'], label=f'seq_len={seq_len}')
plt.xlabel('Epoch')
plt.ylabel('Validation Loss')
plt.title('Sequence Length Comparison')
plt.legend()
plt.grid(alpha=0.3)
plt.show()
            """,
            "hints": [
                "💡 先看学习率曲线稳定性，再看序列长度带来的趋势变化。",
                "💡 两个对比实验的唯一变化项要清晰（lr 或 seq_len）。",
                "💡 如果曲线抖动明显，通常表示学习率偏大或样本不足。"
            ],
            "verification": [
                "✅ 完成两组对比曲线（lr 与 seq_len）",
                "✅ 给出推荐 lr 与推荐 seq_len，并说明依据",
                "✅ 至少改动 1 个候选值并复跑对比"
            ]
        },
        {
            "title": "任务4：层数与隐藏维度（⭐⭐⭐）",
            "description": "系统比较模型深度（层数）和宽度（隐藏维度）对效果与复杂度的影响。",
            "objective": "运行完整脚本，比较多种模型配置并找出 MAE 最优结构。",
            "code": r"""
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

# ============ 自包含虚拟数据 ============
np.random.seed(42)
n_cycles = 260
cycles = np.arange(n_cycles)
capacity_data = 1.62 - 0.0027 * cycles + 0.025 * np.sin(cycles / 5.5) + 0.01 * np.random.randn(n_cycles)
capacity_data = np.clip(capacity_data, 0.9, None)

def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

SEQ_LEN = 10
X, y = create_sequences(capacity_data, SEQ_LEN)
X = X.reshape((X.shape[0], X.shape[1], 1))

split_idx = int(len(X) * 0.7)
X_train, X_test = X[:split_idx], X[split_idx:]
y_train, y_test = y[:split_idx], y[split_idx:]

scaler = StandardScaler()
X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)

def build_lstm_model(seq_len, num_layers=1, hidden_dim=64, lr=0.001):
    # 构建可配置的LSTM模型
    model = Sequential()
    
    # 第一层 LSTM
    model.add(LSTM(hidden_dim, activation='relu', 
                   input_shape=(seq_len, 1), 
                   return_sequences=(num_layers > 1)))
    
    # 添加更多 LSTM 层
    for i in range(1, num_layers):
        return_seq = (i < num_layers - 1)
        model.add(LSTM(hidden_dim, activation='relu', 
                       return_sequences=return_seq))
    
    # 输出层
    model.add(Dense(1))
    
    model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
    return model

# 对比不同配置
configs = [
    {'num_layers': 1, 'hidden_dim': 64},    # 原始配置
    {'num_layers': 2, 'hidden_dim': 64},    # 增加层数
    {'num_layers': 1, 'hidden_dim': 128},   # 增加隐藏维度
    {'num_layers': 2, 'hidden_dim': 128},   # 同时增加两者
    {'num_layers': 3, 'hidden_dim': 64},    # 更深的模型
]

results = {}
for cfg in configs:
    model = build_lstm_model(seq_len=SEQ_LEN, **cfg)
    model.fit(X_train, y_train, epochs=35, batch_size=32, verbose=0)
    y_pred = model.predict(X_test, verbose=0).flatten()
    mae = mean_absolute_error(y_test, y_pred)
    key = f"L{cfg['num_layers']}_D{cfg['hidden_dim']}"
    results[key] = mae
    print(f"{key} -> MAE = {mae:.6f}")

# 找最优配置
best_cfg = min(results, key=results.get)
print(f"✅ 最佳配置: {best_cfg}, MAE = {results[best_cfg]:.6f}")
            """,
            "hints": [
                "💡 `num_layers` 增加会提升表达力，但训练更慢。",
                "💡 `hidden_dim` 增大可拟合更复杂模式，也更容易过拟合。",
                "💡 关注 MAE 与训练成本的平衡，不只追求最小误差。"
            ],
            "verification": [
                "✅ 成功比较 5 种结构并输出 MAE",
                "✅ 找到最佳配置并说明原因",
                "✅ 指出至少 1 个“更复杂但不更好”的配置"
            ]
        },
        {
            "title": "任务5：综合优化·（⭐⭐⭐⭐ 挑战）",
            "description": "综合调参挑战：在自包含数据上同时搜索 `seq_len / lr / epochs / layers / hidden_dim / batch_size`，找出最优组合。",
            "objective": "运行完整脚本并输出最佳参数组合，目标是尽可能降低测试集 MAE。",
            "code": r"""
import itertools
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

# ============ 自包含虚拟数据 ============
np.random.seed(42)
n_cycles = 200
cycles = np.arange(n_cycles)
capacity = 1.66 - 0.0029 * cycles + 0.03 * np.sin(cycles / 7.5) + 0.012 * np.random.randn(n_cycles)
capacity = np.clip(capacity, 0.85, None)

print(f"电池容量序列长度: {len(capacity)}")
print(f"初始容量: {capacity[0]:.4f} Ah")
print(f"最终容量: {capacity[-1]:.4f} Ah")

def create_sequences(data, seq_len):
    X, y = [], []
    for i in range(len(data) - seq_len):
        X.append(data[i:i+seq_len])
        y.append(data[i+seq_len])
    return np.array(X), np.array(y)

def build_model(seq_len, num_layers, hidden_dim, lr):
    model = Sequential()
    model.add(LSTM(hidden_dim, activation='relu', input_shape=(seq_len, 1), return_sequences=(num_layers > 1)))
    for layer_idx in range(1, num_layers):
        model.add(LSTM(hidden_dim, activation='relu', return_sequences=(layer_idx < num_layers - 1)))
    model.add(Dense(1))
    model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
    return model

def evaluate_config(cfg):
    seq_len, lr, epochs, batch_size, num_layers, hidden_dim = cfg

    X, y = create_sequences(capacity, seq_len)
    X = X.reshape((X.shape[0], X.shape[1], 1))
    split_idx = int(len(X) * 0.7)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)
    X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)

    model = build_model(seq_len, num_layers, hidden_dim, lr)
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=0.2,
        verbose=0
    )

    y_pred = model.predict(X_test, verbose=0).flatten()
    mae = mean_absolute_error(y_test, y_pred)
    return mae, history, y_test, y_pred

# ============ 搜索空间 ============
seq_len_list = [10, 12]
lr_list = [0.001, 0.003]
epochs_list = [15]
batch_list = [32]
layers_list = [1]
hidden_list = [32, 64]

search_space = list(itertools.product(
    seq_len_list, lr_list, epochs_list, batch_list, layers_list, hidden_list
))

best_mae = float('inf')
best_cfg = None
best_history = None
best_y_test = None
best_y_pred = None

print(f"开始搜索，共 {len(search_space)} 组参数...\n")
for idx, cfg in enumerate(search_space, 1):
    mae, history, y_test, y_pred = evaluate_config(cfg)
    print(f"[{idx:03d}/{len(search_space)}] cfg={cfg} -> MAE={mae:.6f}")
    if mae < best_mae:
        best_mae = mae
        best_cfg = cfg
        best_history = history
        best_y_test = y_test
        best_y_pred = y_pred

print("\n" + "=" * 60)
print("搜索完成，最优结果如下：")
print(f"best_cfg = (seq_len, lr, epochs, batch, layers, hidden) = {best_cfg}")
print(f"best_mae = {best_mae:.6f}")
print("=" * 60)

# 绘制最优配置训练曲线与预测效果
plt.figure(figsize=(12, 4))
plt.subplot(1, 2, 1)
plt.plot(best_history.history['loss'], label='train loss')
plt.plot(best_history.history['val_loss'], label='val loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()
plt.title('Best Config Training History')

plt.subplot(1, 2, 2)
plt.plot(best_y_test, 'b-', label='true', alpha=0.7)
plt.plot(best_y_pred, 'r--', label='pred', alpha=0.7)
plt.xlabel('Sample')
plt.ylabel('Capacity (Ah)')
plt.legend()
plt.title(f'Best Test Predictions (MAE={best_mae:.6f})')
plt.tight_layout()
plt.show()
            """,
            "hints": [
                "💡 先用小搜索空间跑通，再逐步扩展参数范围。",
                "💡 搜索组合数会快速增长，建议先固定部分参数。",
                "💡 推荐先看 MAE，再结合训练曲线判断是否过拟合。"
            ],
            "verification": [
                "✅ 成功遍历多组参数并输出最优组合",
                "✅ 输出并记录 best MAE",
                "✅ 绘制最优配置的训练曲线和预测对比图",
                "✅ 至少扩展一项搜索空间并复跑对比"
            ]
        },
        {
            "title": "代码差异练习：理解模型变化",
            "description": "对比两段代码，找出关键差异，理解模型结构变化对性能的影响。",
            "objective": "通过代码对比，掌握 LSTM 层数和隐藏维度调整的实际效果。",
            "code_diff": {
                "before": r"""
model = Sequential([
    LSTM(64, activation='relu', input_shape=(seq_len, 1)),
    Dense(1)
])
model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
                """,
                "after": r"""
model = Sequential()
model.add(LSTM(128, activation='relu', input_shape=(seq_len, 1), return_sequences=True))
model.add(LSTM(64, activation='relu'))
model.add(Dense(1))
model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
                """
            },
            "hints": [
                "💡 第一段代码：单层 LSTM，隐藏维度为 64",
                "💡 第二段代码：两层 LSTM，第一层 128维且 return_sequences=True，第二层 64维",
                "💡 多层结构可学习更复杂的特征，但也更容易过拟合"
            ],
            "verification": [
                "✅ 运行两段代码，记录 MAE",
                "✅ 比较两者训练曲线和预测效果",
                "✅ 讨论多层结构的优缺点"
            ]
        }
    ]

    # 显示任务列表
    task_names = [t["title"] for t in tasks]
    selected_task = st.session_state.get("advanced_task", task_names[0])
    if selected_task not in task_names:
        normalized_selected = selected_task.split("（")[0].strip() if isinstance(selected_task, str) else ""
        matched_task = next((name for name in task_names if name.split("（")[0].strip() == normalized_selected), None)
        selected_task = matched_task if matched_task else task_names[0]
        st.session_state["advanced_task"] = selected_task
    current_task_idx = task_names.index(selected_task)

    task = tasks[current_task_idx]

    # 任务卡片
    st.markdown(f"### {task['title']}")
    st.info(f"学习目标：{task['objective']}")
    
    with st.expander("📋 任务描述", expanded=True):
        st.markdown(task['description'])
        st.markdown(f"**目标：** {task['objective']}")

    if 'code_diff' in task:
        with st.expander("🆚 代码差异对比", expanded=True):
            st.markdown("**原始代码：**")
            st.code(task['code_diff']['before'], language='python')
            st.markdown("**修改后代码：**")
            st.code(task['code_diff']['after'], language='python')
            st.caption("💡 对比两段代码，理解结构变化。建议分别运行并记录 MAE。")
    else:
        code_expanded = True
        with st.expander("💻 代码示例", expanded=code_expanded):
            code_content = task.get('code', '')
            if not isinstance(code_content, str):
                code_content = str(code_content)
            st.code(code_content.strip(), language='python')
            st.caption("💡 提示：可在 Heywhale 在线 notebook、本地 notebook 或终端运行，按标记修改后执行。")

    with st.expander("🔍 修改提示", expanded=True):
        for hint in task['hints']:
            st.markdown(hint)

    if current_task_idx != len(tasks) - 1:
        with st.expander("✅ 验证步骤", expanded=False):
            for verify in task['verification']:
                st.markdown(verify)

        if current_task_idx == 1:
            st.markdown("---")
            st.markdown("### 🧩 选择题：理解流程含义")

            q1 = st.radio(
                "题目1：`StandardScaler` 在这个流程中主要做什么？",
                [
                    "把输入特征缩放到均值为0、方差为1",
                    "把时间序列变成更长的序列",
                    "把训练集和测试集混合在一起"
                ],
                key="task2_quiz_q1"
            )

            q2 = st.radio(
                "题目2：为什么要做训练/测试划分？",
                [
                    "为了评估模型泛化性能",
                    "为了减少数据量加快训练",
                    "因为模型只能接受测试集"
                ],
                key="task2_quiz_q2"
            )

            st.markdown("#### 进阶题")
            q3 = st.radio(
                "题目3：为什么要在训练集上 `fit` 标准化，再用同一变换处理测试集？",
                [
                    "避免数据泄露，保证评估公平",
                    "让测试集的均值和方差更大",
                    "因为测试集不能做任何变换"
                ],
                key="task2_quiz_q3"
            )

            q4 = st.multiselect(
                "题目4：下面哪些步骤可能引入数据泄露？",
                [
                    "在全量数据上 fit 标准化",
                    "只在训练集上 fit 标准化",
                    "在测试集上单独 fit 标准化",
                    "先随机打乱再划分训练/测试"
                ],
                key="task2_quiz_q4"
            )

            q5 = st.multiselect(
                "题目5：下面哪些指标适合回归任务评估？",
                [
                    "MAE",
                    "RMSE",
                    "Accuracy",
                    "F1-score"
                ],
                key="task2_quiz_q5"
            )

            if st.button("提交题目答案", key="task2_quiz_submit"):
                correct = {
                    "q1": "把输入特征缩放到均值为0、方差为1",
                    "q2": "为了评估模型泛化性能",
                    "q3": "避免数据泄露，保证评估公平",
                    "q4": {"在全量数据上 fit 标准化", "在测试集上单独 fit 标准化"},
                    "q5": {"MAE", "RMSE"}
                }
                explain = {
                    "q1": "标准化能让不同量级特征处于相似尺度，训练更稳定。",
                    "q2": "用未见过的数据评估，才能判断模型是否真正泛化。",
                    "q3": "如果用测试集信息参与拟合，会导致评估结果被高估。",
                    "q4": "任何在测试集上拟合统计量的行为都属于信息泄露。",
                    "q5": "MAE 与 RMSE 是回归常用误差度量，Accuracy/F1 适用于分类。"
                }

                ok1 = q1 == correct["q1"]
                ok2 = q2 == correct["q2"]
                ok3 = q3 == correct["q3"]
                ok4 = set(q4) == correct["q4"]
                ok5 = set(q5) == correct["q5"]

                st.markdown("#### 判题结果")
                st.success("题目1正确" if ok1 else "题目1错误")
                st.info(f"答案：{correct['q1']}")
                st.caption(f"解析：{explain['q1']}")

                st.success("题目2正确" if ok2 else "题目2错误")
                st.info(f"答案：{correct['q2']}")
                st.caption(f"解析：{explain['q2']}")

                st.success("题目3正确" if ok3 else "题目3错误")
                st.info(f"答案：{correct['q3']}")
                st.caption(f"解析：{explain['q3']}")

                st.success("题目4正确" if ok4 else "题目4错误")
                st.info(f"答案：{', '.join(sorted(correct['q4']))}")
                st.caption(f"解析：{explain['q4']}")

                st.success("题目5正确" if ok5 else "题目5错误")
                st.info(f"答案：{', '.join(sorted(correct['q5']))}")
                st.caption(f"解析：{explain['q5']}")

    if current_task_idx == len(tasks) - 1:
        st.markdown("---")
        st.markdown("### 🧩 填空题：找出变化点")
        if st.session_state.get("task_last_active") != task_names[current_task_idx]:
            st.session_state["task_last_active"] = task_names[current_task_idx]
            st.session_state["task_last_submitted"] = False
            st.session_state["task_last_show_answers"] = False
        if "task_last_show_answers" not in st.session_state:
            st.session_state["task_last_show_answers"] = False
        if "task_last_submitted" not in st.session_state:
            st.session_state["task_last_submitted"] = False

        blank_left, blank_right = st.columns([3, 2])
        with blank_left:
            change_blank_1 = st.text_input("变化点1：这段代码里新增了______（请写关键词）", key="task_last_blank_1")
            change_blank_2 = st.text_input("变化点2：这段代码里新增了______（请写关键词）", key="task_last_blank_2")
        with blank_right:
            if st.session_state.get("task_last_show_answers"):
                st.markdown("**答案：** 多层LSTM / 隐藏维度增加 / `return_sequences` 等")
                st.caption("解析：变化点通常体现在结构更深、参数更多或序列输出方式变化，这些都会改变模型表达能力与过拟合风险。")

        st.markdown("### 🧩 选择题：功能变化与提升")
        left_q1, right_q1 = st.columns([3, 2])
        with left_q1:
            change_q1 = st.radio(
                "题目1：相比原始版本，新的代码更突出的优势是？",
                ["结构更深、表达能力更强", "训练更慢但更稳定", "预测更差但更可解释"],
                key="task_last_q1"
            )
        with right_q1:
            if st.session_state.get("task_last_show_answers"):
                st.markdown("**答案：** 结构更深、表达能力更强")
                st.caption("解析：多层结构和更高容量通常提升表达力，能拟合更复杂的时序关系，但也更容易过拟合。")

        left_q2, right_q2 = st.columns([3, 2])
        with left_q2:
            change_q2 = st.radio(
                "题目2：加入多层结构后，最可能带来的提升是？",
                ["可学习更复杂的时序模式", "减少训练数据需求", "完全避免过拟合"],
                key="task_last_q2"
            )
        with right_q2:
            if st.session_state.get("task_last_show_answers"):
                st.markdown("**答案：** 可学习更复杂的时序模式")
                st.caption("解析：多层 LSTM 的核心提升是特征表达更丰富，能捕捉更复杂的时序模式；但并不会减少数据需求，也无法避免过拟合。")

        submit_col, answer_col = st.columns([1, 1])
        with submit_col:
            if st.button("提交本题答案", key="task_last_submit"):
                st.session_state["task_last_submitted"] = True
        with answer_col:
            if st.button("显示答案", key="task_last_show_answer_btn"):
                st.session_state["task_last_show_answers"] = not st.session_state["task_last_show_answers"]

        if st.session_state.get("task_last_submitted"):
            expected_keywords = {"多层", "隐藏维度", "return_sequences", "LSTM"}
            ok_blank_1 = any(k in (change_blank_1 or "") for k in expected_keywords)
            ok_blank_2 = any(k in (change_blank_2 or "") for k in expected_keywords)
            ok_q1 = change_q1 == "结构更深、表达能力更强"
            ok_q2 = change_q2 == "可学习更复杂的时序模式"

            st.markdown("#### 判题结果")
            st.success("填空1正确" if ok_blank_1 else "填空1有待完善")
            st.success("填空2正确" if ok_blank_2 else "填空2有待完善")
            st.success("题目1正确" if ok_q1 else "题目1错误")
            st.success("题目2正确" if ok_q2 else "题目2错误")

            st.info("参考答案：变化点可写 '多层LSTM' / '隐藏维度增加' / 'return_sequences' 等关键词。")


    if current_task_idx == 0:
        st.markdown("---")
        st.markdown("### 自动调参方法练习")
        st.markdown("补全关键代码并提交核对。")
        st.markdown("在 Notebook 运行本节代码前，请先执行依赖安装：")
        st.code("!pip install scikit-learn scikit-optimize", language="bash")
        st.markdown(
            """
**探索方法提示**
- **GridSearch（网格搜索）**：把参数组合列成网格逐一试，优点是直观可复现，缺点是组合多时很耗时。
- **Bayesian Optimization（贝叶斯优化）**：用概率模型预测更可能好的参数点，试验次数更少但实现更复杂。
            """
        )

        if "task1_method" not in st.session_state:
            st.session_state["task1_method"] = None

        choose_col1, choose_col2 = st.columns(2)
        with choose_col1:
            if st.button("GridSearch", key="task1_btn_grid", use_container_width=True):
                st.session_state["task1_method"] = "grid"
        with choose_col2:
            if st.button("Bayesian Optimization", key="task1_btn_bayes", use_container_width=True):
                st.session_state["task1_method"] = "bayes"

        if st.session_state["task1_method"] == "grid":
            st.markdown("**GridSearch 逻辑：** 枚举参数组合 → 训练与评估 → 选最优 MAE。")
            st.markdown("请补全关键代码（包含 `for` 遍历参数组合这一段）。")
            st.info("提示：利用一个函数把参数字典展开成“所有组合”，再在 for 循环里逐个训练。")
            if "task1_grid_show_answer" not in st.session_state:
                st.session_state["task1_grid_show_answer"] = False
            for key in ["task1_grid_hint1", "task1_grid_hint2", "task1_grid_hint3", "task1_grid_hint4"]:
                if key not in st.session_state:
                    st.session_state[key] = False

            with st.container():
                if st.button("显示答案", key="task1_grid_show_answer_btn"):
                    st.session_state["task1_grid_show_answer"] = not st.session_state["task1_grid_show_answer"]

                st.code(
                    """
# TODO 1: 导入遍历参数网格所需函数
__请填写第1行__

param_grid = {
    "seq_len": [5, 10, 15],
    "lr": [0.0005, 0.001, 0.005],
    "epochs": [30, 50]
}

# TODO 2: for 遍历参数组合
__请填写第2行___
    # TODO 3: 取当前组合的学习率
    __请填写第3行__
    # TODO 4: 取当前组合的训练轮数
    __请填写第4行__
    print(params, current_lr, current_epochs)
                """,
                    language="python"
                )

                if st.session_state["task1_grid_show_answer"]:
                    st.code(
                        """
from sklearn.model_selection import ParameterGrid

param_grid = {
    "seq_len": [5, 10, 15],
    "lr": [0.0005, 0.001, 0.005],
    "epochs": [30, 50]
}

for params in ParameterGrid(param_grid):
    current_lr = params["lr"]
    current_epochs = params["epochs"]
    print(params, current_lr, current_epochs)
                        """,
                        language="python"
                    )

            row1_input_col, row1_hint_col = st.columns([5, 1])
            with row1_input_col:
                grid_blank_1 = st.text_input("第1行", key="task1_grid_blank_1")
            with row1_hint_col:
                if st.button("提示1", key="task1_grid_hint1_btn", use_container_width=True):
                    st.session_state["task1_grid_hint1"] = not st.session_state["task1_grid_hint1"]
            if st.session_state["task1_grid_hint1"]:
                st.markdown("提示1：`ParameterGrid` 用来把参数网格转成可遍历的参数组合列表。")
                st.markdown("补充：它来自 `sklearn.model_selection`，这个模块主要用于数据集划分、交叉验证和超参数搜索。")

            row2_input_col, row2_hint_col = st.columns([5, 1])
            with row2_input_col:
                grid_blank_2 = st.text_input("第2行", key="task1_grid_blank_2")
            with row2_hint_col:
                if st.button("提示2", key="task1_grid_hint2_btn", use_container_width=True):
                    st.session_state["task1_grid_hint2"] = not st.session_state["task1_grid_hint2"]
            if st.session_state["task1_grid_hint2"]:
                st.markdown("提示2：第2行是 `for` 循环，遍历 `ParameterGrid(param_grid)`。")

            row3_input_col, row3_hint_col = st.columns([5, 1])
            with row3_input_col:
                grid_blank_3 = st.text_input("第3行", key="task1_grid_blank_3")
            with row3_hint_col:
                if st.button("提示3", key="task1_grid_hint3_btn", use_container_width=True):
                    st.session_state["task1_grid_hint3"] = not st.session_state["task1_grid_hint3"]
            if st.session_state["task1_grid_hint3"]:
                st.markdown("提示3：语法形态是 `变量 = 字典[\"键\"]`，这里键是学习率对应的 `\"lr\"`。")

            row4_input_col, row4_hint_col = st.columns([5, 1])
            with row4_input_col:
                grid_blank_4 = st.text_input("第4行", key="task1_grid_blank_4")
            with row4_hint_col:
                if st.button("提示4", key="task1_grid_hint4_btn", use_container_width=True):
                    st.session_state["task1_grid_hint4"] = not st.session_state["task1_grid_hint4"]
            if st.session_state["task1_grid_hint4"]:
                st.markdown("提示4：语法形态同上 `变量 = 字典[\"键\"]`，这里键是训练轮数对应的 `\"epochs\"`。")

            if st.button("提交 GridSearch 答案", key="task1_submit_grid"):
                ok1 = grid_blank_1.strip() == "from sklearn.model_selection import ParameterGrid"
                ok2 = grid_blank_2.strip() == "for params in ParameterGrid(param_grid):"
                ok3 = grid_blank_3.strip() == "current_lr = params[\"lr\"]"
                ok4 = grid_blank_4.strip() == "current_epochs = params[\"epochs\"]"
                if ok1 and ok2 and ok3 and ok4:
                    st.success("✅ 全部正确！")
                    st.markdown(
                        """
**解析：**
- `ParameterGrid` 会把参数字典展开为所有参数组合（笛卡尔积）。
- `for params in ParameterGrid(param_grid)` 的作用是逐个遍历每一种超参数组合。
- `params['lr']` 和 `params['epochs']` 用来读取当前组合的学习率与训练轮数。
                        """
                    )
                else:
                    st.error("❌ 还有填空不正确，请根据提示继续修改。")
                    if not ok1:
                        st.warning("第1行不正确：需要导入遍历参数网格的函数。")
                    if not ok2:
                        st.warning("第2行不正确：应在 for 循环中遍历参数组合。")
                    if not ok3:
                        st.warning("第3行不正确：应从 params 里取出学习率。")
                    if not ok4:
                        st.warning("第4行不正确：应从 params 里取出训练轮数。")
                st.info("操作提示：请复制这个单元格里的完整代码，去 Notebook 中替换你原来那一小段参数遍历代码后再运行。")

        elif st.session_state["task1_method"] == "bayes":
            st.markdown("**Bayesian Optimization 逻辑：** 用代理模型建议下一组参数，减少无效尝试次数。")
            st.markdown("请补全：执行贝叶斯优化时应该用哪个函数。")
            if "task1_bayes_hint" not in st.session_state:
                st.session_state["task1_bayes_hint"] = False
            if "task1_bayes_show_answer" not in st.session_state:
                st.session_state["task1_bayes_show_answer"] = False
            st.code(
                """
import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer

# 一个最小可运行的目标函数示例
def objective(params):
    seq_len, lr = params
    # 示例：让目标在 seq_len=10、lr=0.001 时最小
    return (seq_len - 10) ** 2 + (lr - 0.001) ** 2

space = [Integer(5, 20), Real(1e-4, 1e-2, prior="log-uniform")]

# TODO: 执行贝叶斯优化
res = ____(objective, space, n_calls=20, random_state=42)

print("best params:", res.x)
print("best score:", res.fun)
                """,
                language="python"
            )
            bayes_input_col, bayes_hint_col, bayes_answer_col = st.columns([4, 1, 1])
            with bayes_input_col:
                bayes_blank = st.text_input("填空（函数名）", key="task1_bayes_blank")
            with bayes_hint_col:
                if st.button("提示", key="task1_bayes_hint_btn", use_container_width=True):
                    st.session_state["task1_bayes_hint"] = not st.session_state["task1_bayes_hint"]
            with bayes_answer_col:
                if st.button("显示答案", key="task1_bayes_show_answer_btn", use_container_width=True):
                    st.session_state["task1_bayes_show_answer"] = not st.session_state["task1_bayes_show_answer"]
            if st.session_state["task1_bayes_hint"]:
                st.markdown("提示：`gp_minimize` 是 skopt 的高斯过程优化函数，参数里要传入 objective 和 space。")
            if st.session_state["task1_bayes_show_answer"]:
                st.code(
                    """
import numpy as np
from skopt import gp_minimize
from skopt.space import Real, Integer

def objective(params):
    seq_len, lr = params
    return (seq_len - 10) ** 2 + (lr - 0.001) ** 2

space = [Integer(5, 20), Real(1e-4, 1e-2, prior="log-uniform")]
res = gp_minimize(objective, space, n_calls=20, random_state=42)

print("best params:", res.x)
print("best score:", res.fun)
                    """,
                    language="python"
                )
            if st.button("提交 Bayesian 答案", key="task1_submit_bayes"):
                if bayes_blank.strip() == "gp_minimize":
                    st.success("✅ 正确：应使用 gp_minimize 进行贝叶斯优化。")
                else:
                    st.error("❌ 不正确。提示：函数来自 skopt 包。")
                st.info("可复制上面代码到 Heywhale Notebook 运行完整版本并观察结果。")

    elif current_task_idx == 1:
        st.markdown("---")
        st.markdown("### 任务2小练习：补全流程关键行")

        def fill_task2_blank(blank_key, code_line):
            st.session_state[blank_key] = code_line

        for key in [
            "task2_flow_hint1",
            "task2_flow_hint2",
            "task2_flow_hint3",
            "task2_flow_hint4",
            "task2_flow_hint5",
            "task2_flow_hint6",
            "task2_flow_hint7",
            "task2_flow_hint8"
        ]:
            if key not in st.session_state:
                st.session_state[key] = False

        st.code(
            """
# 构造样本
__请填写第1行___
__请填写第2行___

# 训练测试集分割
__请填写第3行___
__请填写第4行___

# 数据预处理
scaler = StandardScaler()
__请填写第5行___
__请填写第6行___

# 构建模型
model = Sequential([
    LSTM(64, activation='relu', input_shape=(seq_len, 1)),
    Dense(1)
])
__请填写第7行___

# 训练
__请填写第8行___

# 评估
y_pred = model.predict(X_test, verbose=0).flatten()
mae = mean_absolute_error(y_test, y_pred)
print(f"MAE = {mae:.6f}")
            """,
            language="python"
        )

        row1_input_col, row1_hint_col, row1_answer_col = st.columns([4, 1, 1])
        with row1_input_col:
            task2_flow_blank_1 = st.text_input("第1行", key="task2_flow_blank_1")
        with row1_hint_col:
            if st.button("提示1", key="task2_flow_hint1_btn", use_container_width=True):
                st.session_state["task2_flow_hint1"] = not st.session_state["task2_flow_hint1"]
        with row1_answer_col:
            st.button(
                "答案1",
                key="task2_flow_ans1_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_1", "X, y = create_sequences(capacity_data, seq_len)")
            )
        if st.session_state["task2_flow_hint1"]:
            st.markdown("提示1：使用 `create_sequences` 生成 `X, y`，参数是 `capacity_data` 和 `seq_len`。")

        row2_input_col, row2_hint_col, row2_answer_col = st.columns([4, 1, 1])
        with row2_input_col:
            task2_flow_blank_2 = st.text_input("第2行", key="task2_flow_blank_2")
        with row2_hint_col:
            if st.button("提示2", key="task2_flow_hint2_btn", use_container_width=True):
                st.session_state["task2_flow_hint2"] = not st.session_state["task2_flow_hint2"]
        with row2_answer_col:
            st.button(
                "答案2",
                key="task2_flow_ans2_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_2", "X = X.reshape((X.shape[0], X.shape[1], 1))")
            )
        if st.session_state["task2_flow_hint2"]:
            st.markdown("提示2：把 X 变成三维输入 `(样本数, seq_len, 1)`。")

        row3_input_col, row3_hint_col, row3_answer_col = st.columns([4, 1, 1])
        with row3_input_col:
            task2_flow_blank_3 = st.text_input("第3行", key="task2_flow_blank_3")
        with row3_hint_col:
            if st.button("提示3", key="task2_flow_hint3_btn", use_container_width=True):
                st.session_state["task2_flow_hint3"] = not st.session_state["task2_flow_hint3"]
        with row3_answer_col:
            st.button(
                "答案3",
                key="task2_flow_ans3_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_3", "split_idx = int(len(X) * 0.7)")
            )
        if st.session_state["task2_flow_hint3"]:
            st.markdown("提示3：用比例切分训练/测试，格式是 `split_idx = int(len(X) * 0.7)`。")

        row4_input_col, row4_hint_col, row4_answer_col = st.columns([4, 1, 1])
        with row4_input_col:
            task2_flow_blank_4 = st.text_input("第4行", key="task2_flow_blank_4")
        with row4_hint_col:
            if st.button("提示4", key="task2_flow_hint4_btn", use_container_width=True):
                st.session_state["task2_flow_hint4"] = not st.session_state["task2_flow_hint4"]
        with row4_answer_col:
            st.button(
                "答案4",
                key="task2_flow_ans4_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_4", "X_train, X_test = X[:split_idx], X[split_idx:]")
            )
        if st.session_state["task2_flow_hint4"]:
            st.markdown("提示4：用 `split_idx` 切分 `X, y` 得到训练集和测试集。")

        row5_input_col, row5_hint_col, row5_answer_col = st.columns([4, 1, 1])
        with row5_input_col:
            task2_flow_blank_5 = st.text_input("第5行", key="task2_flow_blank_5")
        with row5_hint_col:
            if st.button("提示5", key="task2_flow_hint5_btn", use_container_width=True):
                st.session_state["task2_flow_hint5"] = not st.session_state["task2_flow_hint5"]
        with row5_answer_col:
            st.button(
                "答案5",
                key="task2_flow_ans5_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_5", "X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)")
            )
        if st.session_state["task2_flow_hint5"]:
            st.markdown("提示5：在训练集上 `fit_transform`，并还原回原形状。")

        row6_input_col, row6_hint_col, row6_answer_col = st.columns([4, 1, 1])
        with row6_input_col:
            task2_flow_blank_6 = st.text_input("第6行", key="task2_flow_blank_6")
        with row6_hint_col:
            if st.button("提示6", key="task2_flow_hint6_btn", use_container_width=True):
                st.session_state["task2_flow_hint6"] = not st.session_state["task2_flow_hint6"]
        with row6_answer_col:
            st.button(
                "答案6",
                key="task2_flow_ans6_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_6", "X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)")
            )
        if st.session_state["task2_flow_hint6"]:
            st.markdown("提示6：在测试集上只 `transform`，同样要还原形状。")

        row7_input_col, row7_hint_col, row7_answer_col = st.columns([4, 1, 1])
        with row7_input_col:
            task2_flow_blank_7 = st.text_input("第7行", key="task2_flow_blank_7")
        with row7_hint_col:
            if st.button("提示7", key="task2_flow_hint7_btn", use_container_width=True):
                st.session_state["task2_flow_hint7"] = not st.session_state["task2_flow_hint7"]
        with row7_answer_col:
            st.button(
                "答案7",
                key="task2_flow_ans7_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_7", "model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])")
            )
        if st.session_state["task2_flow_hint7"]:
            st.markdown("提示7：编译模型，注意 `Adam(lr=lr)`、`loss='mse'`、`metrics=['mae']`。")

        row8_input_col, row8_hint_col, row8_answer_col = st.columns([4, 1, 1])
        with row8_input_col:
            task2_flow_blank_8 = st.text_input("第8行", key="task2_flow_blank_8")
        with row8_hint_col:
            if st.button("提示8", key="task2_flow_hint8_btn", use_container_width=True):
                st.session_state["task2_flow_hint8"] = not st.session_state["task2_flow_hint8"]
        with row8_answer_col:
            st.button(
                "答案8",
                key="task2_flow_ans8_btn",
                use_container_width=True,
                on_click=fill_task2_blank,
                args=("task2_flow_blank_8", "model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)")
            )
        if st.session_state["task2_flow_hint8"]:
            st.markdown("提示8：训练时传入 `X_train, y_train`、`epochs`、`batch_size=32`、`verbose=0`。")

        if st.button("提交 任务2 答案", key="task2_flow_submit"):
            ok1 = task2_flow_blank_1.strip() == "X, y = create_sequences(capacity_data, seq_len)"
            ok2 = task2_flow_blank_2.strip() == "X = X.reshape((X.shape[0], X.shape[1], 1))"
            ok3 = task2_flow_blank_3.strip() == "split_idx = int(len(X) * 0.7)"
            ok4 = task2_flow_blank_4.strip() == "X_train, X_test = X[:split_idx], X[split_idx:]\ny_train, y_test = y[:split_idx], y[split_idx:]" or task2_flow_blank_4.strip() == "X_train, X_test = X[:split_idx], X[split_idx:]"
            ok5 = task2_flow_blank_5.strip() == "X_train = scaler.fit_transform(X_train.reshape(-1, 1)).reshape(X_train.shape)"
            ok6 = task2_flow_blank_6.strip() == "X_test = scaler.transform(X_test.reshape(-1, 1)).reshape(X_test.shape)"
            ok7 = task2_flow_blank_7.strip() == "model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])"
            ok8 = task2_flow_blank_8.strip() == "model.fit(X_train, y_train, epochs=epochs, batch_size=32, verbose=0)"
            if ok1 and ok2 and ok3 and ok4 and ok5 and ok6 and ok7 and ok8:
                st.success("✅ 全部正确！")
                st.markdown(
                    """
**解析：**
- 样本构造、切分、预处理、建模、训练、评估共同组成完整机器学习流程。
                    """
                )
            else:
                st.error("❌ 还有填空不正确，请根据提示继续修改。")
                if not ok1:
                    st.warning("第1行不正确：需要生成 X, y 训练样本。")
                if not ok2:
                    st.warning("第2行不正确：需要把 X 变成三维输入。")
                if not ok3:
                    st.warning("第3行不正确：需要按 0.7 比例切分索引。")
                if not ok4:
                    st.warning("第4行不正确：需要用 split_idx 切分训练/测试。")
                if not ok5:
                    st.warning("第5行不正确：训练集需要 fit_transform。")
                if not ok6:
                    st.warning("第6行不正确：测试集需要 transform。")
                if not ok7:
                    st.warning("第7行不正确：需要编译模型。")
                if not ok8:
                    st.warning("第8行不正确：需要训练模型。")


    elif current_task_idx == 2:
        st.markdown("---")
        st.markdown("### 任务3小练习：补全多学习率循环")
        st.markdown("请补全两行关键代码，完成学习率循环与结果记录。")
        if "task2_lr_show_answer" not in st.session_state:
            st.session_state["task2_lr_show_answer"] = False
        for key in ["task2_lr_hint1", "task2_lr_hint2"]:
            if key not in st.session_state:
                st.session_state[key] = False

        if st.button("显示答案", key="task2_lr_show_answer_btn"):
            st.session_state["task2_lr_show_answer"] = not st.session_state["task2_lr_show_answer"]

        st.code(
            """
lr_list = [0.0005, 0.001, 0.005, 0.01]
all_hist = {}

# TODO 1: for 循环
__请填写第1行___
    print(f"Training with lr={lr} ...")
    # TODO 2: 保存当前 lr 的训练结果
    _请填写第2行___
            """,
            language="python"
        )

        if st.session_state["task2_lr_show_answer"]:
            st.code(
                """
for lr in lr_list:
    print(f"Training with lr={lr} ...")
    all_hist[lr] = train_with_lr(lr, seq_len=10, epochs=30)
                """,
                language="python"
            )

        row1_input_col, row1_hint_col = st.columns([5, 1])
        with row1_input_col:
            task2_blank_1 = st.text_input("第1行", key="task2_lr_blank_1")
        with row1_hint_col:
            if st.button("提示1", key="task2_lr_hint1_btn", use_container_width=True):
                st.session_state["task2_lr_hint1"] = not st.session_state["task2_lr_hint1"]
        if st.session_state["task2_lr_hint1"]:
            st.markdown("提示1：用 `for` 循环遍历 `lr_list`，格式是 `for 变量 in 列表:`。")

        row2_input_col, row2_hint_col = st.columns([5, 1])
        with row2_input_col:
            task2_blank_2 = st.text_input("第2行（", key="task2_lr_blank_2")
        with row2_hint_col:
            if st.button("提示2", key="task2_lr_hint2_btn", use_container_width=True):
                st.session_state["task2_lr_hint2"] = not st.session_state["task2_lr_hint2"]
        if st.session_state["task2_lr_hint2"]:
            st.markdown("提示2：把训练结果存入字典，格式是 `字典[键] = 函数(...)`。")
            st.markdown("补充：`train_with_lr` 需要传入当前 `lr`，并用 `seq_len=10, epochs=30`。")

        if st.button("提交 任务2 答案", key="task2_submit_lr"):
            ok1 = task2_blank_1.strip() == "for lr in lr_list:"
            ok2 = task2_blank_2.strip() == "all_hist[lr] = train_with_lr(lr, seq_len=10, epochs=30)"
            if ok1 and ok2:
                st.success("✅ 全部正确！")
                st.markdown(
                    """
**解析：**
- `for lr in lr_list:` 会遍历每一个学习率。
- `all_hist[lr] = train_with_lr(...)` 把对应训练历史保存下来，便于后续绘图对比。
                    """
                )
            else:
                st.error("❌ 还有填空不正确，请根据提示继续修改。")
                if not ok1:
                    st.warning("第1行不正确：需要写 for 循环并以冒号结尾。")
                if not ok2:
                    st.warning("第2行不正确：需要把训练结果保存到 all_hist 字典里。")
            st.info("操作提示：请复制完整代码到 Notebook 对应位置替换后运行。")

    elif current_task_idx == 3:
        st.markdown("---")
        st.markdown("### 任务4小练习：补全模型构建函数")
        st.markdown("请补全 `build_lstm_model` 这一整段，其他代码保持不变。")
        if "task4_block_hint" not in st.session_state:
            st.session_state["task4_block_hint"] = False
        if "task4_block_show_answer" not in st.session_state:
            st.session_state["task4_block_show_answer"] = False

        st.code(
            """
# 作用：定义一个可配置的 LSTM 架构（层数、隐藏维度、学习率）
# 语法：函数定义、for 循环、条件表达式、列表/字典参数传递
__第1段填写__
            """,
            language="python"
        )

        task4_block = st.text_area("填写第1段", key="task4_block_blank", height=140)
        col_hint, col_ans, col_submit = st.columns([1, 1, 1])
        with col_hint:
            if st.button("提示", key="task4_block_hint_btn", use_container_width=True):
                st.session_state["task4_block_hint"] = not st.session_state["task4_block_hint"]
        with col_ans:
            if st.button("显示答案", key="task4_block_answer_btn", use_container_width=True):
                st.session_state["task4_block_show_answer"] = not st.session_state["task4_block_show_answer"]
        with col_submit:
            if st.button("确认答案", key="task4_block_submit_btn", use_container_width=True):
                expected = """def build_lstm_model(seq_len, num_layers=1, hidden_dim=64, lr=0.001):
    # 构建可配置的LSTM模型
    model = Sequential()

    # 第一层 LSTM
    model.add(LSTM(hidden_dim, activation='relu', 
                   input_shape=(seq_len, 1), 
                   return_sequences=(num_layers > 1)))

    # 添加更多 LSTM 层
    for i in range(1, num_layers):
        return_seq = (i < num_layers - 1)
        model.add(LSTM(hidden_dim, activation='relu', 
                       return_sequences=return_seq))

    # 输出层
    model.add(Dense(1))

    model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
    return model"""
                if task4_block.strip() == expected.strip():
                    st.success("✅ 正确！")
                else:
                    st.error("❌ 还有细节不正确，请结合提示再检查。")
        if st.session_state["task4_block_hint"]:
            st.markdown("提示：函数内部需要先建 `Sequential()`，再根据 `num_layers` 追加 LSTM 层，最后 `compile` 并 `return`。")
        if st.session_state["task4_block_show_answer"]:
            st.code(
                """def build_lstm_model(seq_len, num_layers=1, hidden_dim=64, lr=0.001):
    # 构建可配置的LSTM模型
    model = Sequential()

    # 第一层 LSTM
    model.add(LSTM(hidden_dim, activation='relu', 
                   input_shape=(seq_len, 1), 
                   return_sequences=(num_layers > 1)))

    # 添加更多 LSTM 层
    for i in range(1, num_layers):
        return_seq = (i < num_layers - 1)
        model.add(LSTM(hidden_dim, activation='relu', 
                       return_sequences=return_seq))

    # 输出层
    model.add(Dense(1))

    model.compile(optimizer=Adam(lr=lr), loss='mse', metrics=['mae'])
    return model""",
                language="python"
            )

    elif current_task_idx == 4:
        st.markdown("---")
        st.markdown("### 任务5小练习：补全一段搜索空间")
        st.markdown("请补全“搜索过程”这一整段，其他代码保持不变。")
        if "task5_block_hint" not in st.session_state:
            st.session_state["task5_block_hint"] = False
        if "task5_block_show_answer" not in st.session_state:
            st.session_state["task5_block_show_answer"] = False

        st.code(
            """
# 说明：print 行无需填写，请补全搜索循环与最优结果更新
print(f"开始搜索，共 {len(search_space)} 组参数...\n")
__第1段由你填写__

print("\n" + "=" * 60)
print("✅ 搜索完成，最优结果如下：")
print(f"best_cfg = (seq_len, lr, epochs, batch, layers, hidden) = {best_cfg}")
print(f"best_mae = {best_mae:.6f}")
print("=" * 60)
            """,
            language="python"
        )

        task5_block = st.text_area("填写第1段", key="task5_block_blank", height=180)
        col_hint, col_ans, col_submit = st.columns([1, 1, 1])
        with col_hint:
            if st.button("提示", key="task5_block_hint_btn", use_container_width=True):
                st.session_state["task5_block_hint"] = not st.session_state["task5_block_hint"]
        with col_ans:
            if st.button("显示答案", key="task5_block_answer_btn", use_container_width=True):
                st.session_state["task5_block_show_answer"] = not st.session_state["task5_block_show_answer"]
        with col_submit:
            if st.button("确认答案", key="task5_block_submit_btn", use_container_width=True):
                expected = """for idx, cfg in enumerate(search_space, 1):
    mae, history, y_test, y_pred = evaluate_config(cfg)
    print(f"[{idx:03d}/{len(search_space)}] cfg={cfg} -> MAE={mae:.6f}")
    if mae < best_mae:
        best_mae = mae
        best_cfg = cfg
        best_history = history
        best_y_test = y_test
        best_y_pred = y_pred"""
                if task5_block.strip() == expected.strip():
                    st.success("✅ 正确！")
                else:
                    st.error("❌ 还有细节不正确，请结合提示再检查。")
        if st.session_state["task5_block_hint"]:
            st.markdown("提示：需要完成 `for` 循环、计算 MAE、打印进度，并在更优时更新 best_* 变量。")
        if st.session_state["task5_block_show_answer"]:
            st.code(
                """for idx, cfg in enumerate(search_space, 1):
    mae, history, y_test, y_pred = evaluate_config(cfg)
    print(f"[{idx:03d}/{len(search_space)}] cfg={cfg} -> MAE={mae:.6f}")
    if mae < best_mae:
        best_mae = mae
        best_cfg = cfg
        best_history = history
        best_y_test = y_test
        best_y_pred = y_pred""",
                language="python"
            )

    # 总结框（放在选做任务下方、按钮上方）
    st.markdown("---")
    summary_map = {
        0: """
    ### 📚 总结与反思

    - 识别并理解 `seq_len / lr / epochs` 三个核心参数。
    - 了解参数变化如何体现在训练曲线（平滑、振荡、过拟合）上。
    - 完成 GridSearch / Bayesian 的基础逻辑练习。

    小结：建立参数直觉，为后续系统调参打基础。
        """,
        1: """
    ### 📚 总结与反思

    - 完成完整的机器学习流程练习（样本、切分、预处理、建模、训练、评估）。
    - 定位每个流程步骤在代码中的位置。

    小结：任务2重点是把“训练代码”理解成一条完整流程链。
        """,
        2: """
    ### 📚 总结与反思

    - 完成学习率与序列长度的两组对比实验。
    - 能给出推荐 `lr` 与 `seq_len` 并说明依据。

    小结：任务3重点是用对比实验做出有依据的调参选择。
        """,
        3: """
    ### 📚 总结与反思

    - 比较不同层数和隐藏维度的模型结构表现。
    - 理解“模型更复杂 ≠ 一定更好”的真实现象。

    小结：任务4重点是结构复杂度与泛化性能之间的平衡。
        """,
        4: """
    ### 📚 总结与反思

    - 完成综合参数搜索并输出了最优配置。
    - 根据 MAE 与训练曲线一起判断配置质量。

    小结：任务5重点是形成完整的调参闭环：设空间 → 跑实验 → 选最优 → 复盘。
        """,
        5: """
    ### 📚 总结与反思

    - 对比不同模型结构的代码差异与效果差异。
    - 解释为什么某些结构改动会带来性能变化。

    小结：本练习重点是把“代码修改”转化成“模型行为理解”。
        """
    }
    st.markdown(summary_map.get(current_task_idx, summary_map[0]))

    # 进度指示器
    st.markdown("---")
    progress = (current_task_idx + 1) / len(tasks)
    st.progress(progress, f"进度：{current_task_idx + 1}/{len(tasks)}")
    
    col1, col2, col3 = st.columns(3)
    if current_task_idx > 0:
        with col1:
            st.button("⬅️ 上一个任务", on_click=lambda: st.session_state.update({"advanced_task": task_names[current_task_idx-1]}), use_container_width=True)
    
    if current_task_idx < len(tasks) - 1:
        with col3:
            st.button("下一个任务 ➡️", on_click=lambda: st.session_state.update({"advanced_task": task_names[current_task_idx+1]}), use_container_width=True)

def render_simulation_module():
    st.markdown('<div id="sim"></div>', unsafe_allow_html=True)
    st.subheader("🧪 模拟仿真模块")
    st.markdown("**参数变动可视化（模拟曲线）**")
    with st.expander("参数设置", expanded=True):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            preview_epochs = st.slider("训练轮数（预览）", 1, 200, 30, 1)
            preview_lr = st.number_input("学习率（预览）", min_value=0.00001, max_value=0.1, value=0.001, step=0.0001, format="%.5f")
        with col_b:
            preview_batch = st.select_slider("Batch size（预览）", options=[8, 16, 32, 64, 128], value=32)
            preview_layers = st.slider("层数（预览）", 1, 6, 3, 1)
        with col_c:
            preview_hidden = st.slider("隐藏维度（预览）", 16, 256, 64, 8)
            preview_eol = st.slider("EOL 阈值 (Ah)", 0.6, 1.6, 1.0, 0.05)

        fig, ax = plt.subplots(figsize=(12, 5))
        cycle_idx = np.arange(1, 151)
        base_default = 1.55 - (3 * 0.03)
        decay_default = 0.006 + (0.001 * 5)
        noise_default = 0.02 + (64 / 1024)
        default_curve = build_mock_rul_curve(cycle_idx, base=base_default, decay=decay_default, noise=noise_default)

        base = 1.55 - (preview_layers * 0.03)
        decay = 0.006 + (preview_lr * 5)
        noise = 0.02 + (preview_hidden / 1024)
        mock_curve = build_mock_rul_curve(cycle_idx, base=base, decay=decay, noise=noise)

        ax.plot(cycle_idx, default_curve, color="#8c8c8c", linewidth=2, linestyle="--", label="Default")
        ax.plot(cycle_idx, mock_curve, color="#1f77b4", linewidth=2.5, label="Current")
        ax.axhline(y=preview_eol, color="gray", linestyle="--", linewidth=1.5, label="EOL threshold")
        ax.set_xlabel("Cycle")
        ax.set_ylabel("Capacity (Ah)")
        ax.set_title("Mock degradation curve (interactive comparison)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Epochs", preview_epochs)
        with col2:
            st.metric("LR", f"{preview_lr:.5f}")
        with col3:
            st.metric("Batch", preview_batch)
        with col4:
            st.metric("Layers", preview_layers)

        st.markdown("**参数解释提示**")
        lr_hint = "偏大：可能训练发散" if preview_lr > 0.01 else "偏小：收敛较慢" if preview_lr < 0.0005 else "适中：更稳定"
        batch_hint = "偏大：更稳定但泛化差" if preview_batch >= 64 else "偏小：噪声大但可能泛化好"
        layer_hint = "偏大：容量高但易过拟合" if preview_layers >= 5 else "适中：训练更稳"
        hidden_hint = "偏大：表达力强但训练慢" if preview_hidden >= 128 else "偏小：可能欠拟合"

        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(
                f"""
<div class="hint-card">
    <div class="hint-title">LR 影响</div>
    <div class="hint-body">{lr_hint}</div>
</div>
                """,
                unsafe_allow_html=True
            )
        with col6:
            st.markdown(
                f"""
<div class="hint-card">
    <div class="hint-title">Batch 影响</div>
    <div class="hint-body">{batch_hint}</div>
</div>
                """,
                unsafe_allow_html=True
            )
        with col7:
            st.markdown(
                f"""
<div class="hint-card">
    <div class="hint-title">Layers 影响</div>
    <div class="hint-body">{layer_hint}</div>
</div>
                """,
                unsafe_allow_html=True
            )
        with col8:
            st.markdown(
                f"""
<div class="hint-card">
    <div class="hint-title">Hidden 影响</div>
    <div class="hint-body">{hidden_hint}</div>
</div>
                """,
                unsafe_allow_html=True
            )

        st.caption("说明：对比曲线是教学用模拟，展示参数变化趋势，不等同于真实训练结果。")


if app_mode == "home":
    render_home()
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
elif app_mode == "learning":
    render_learning_module(st.session_state.get("learning_section"))
    st.markdown("---")
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
elif app_mode == "data":
    render_data_workshop(st.session_state.get("data_view"))
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
elif app_mode == "repro":
    render_reproduction_module(st.session_state.get("repro_section"))
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
elif app_mode == "advanced":
    render_advanced_practice_module(st.session_state.get("advanced_task"))
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
elif app_mode == "sim":
    render_simulation_module()
    st.markdown("<div style='color:#9aa0a6; font-style:italic; font-size:12px; opacity:0.8;'>CHEN Shuangshuang · isabella_chen2113@outlook.com</div>", unsafe_allow_html=True)
