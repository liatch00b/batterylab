# utils/nasa_loader.py
import scipy.io
from datetime import datetime
import os
import numpy as np


def _is_git_lfs_pointer(matfile):
    try:
        with open(matfile, "rb") as f:
            head = f.read(256)
        return head.startswith(b"version https://git-lfs.github.com/spec/v1")
    except OSError:
        return False


def _extract_numeric_values(obj, output):
    if isinstance(obj, np.ndarray):
        if obj.dtype == object:
            for item in obj.flat:
                _extract_numeric_values(item, output)
        else:
            output.extend(np.asarray(obj).reshape(-1).tolist())
        return

    if isinstance(obj, (list, tuple)):
        for item in obj:
            _extract_numeric_values(item, output)
        return

    try:
        output.append(float(obj))
    except (TypeError, ValueError):
        return


def _to_int_scalar(value, default=0):
    nums = []
    _extract_numeric_values(value, nums)
    if not nums:
        return default
    return int(nums[0])

def convert_to_time(hmm):
    """将MATLAB日期向量转换为datetime对象"""
    nums = []
    _extract_numeric_values(hmm, nums)
    if len(nums) < 6:
        raise ValueError(f"时间向量解析失败，期望至少6个元素，实际为{len(nums)}")

    year, month, day, hour, minute, second = [int(nums[idx]) for idx in range(6)]
    return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)

def loadMat(matfile):
    """加载MAT文件并解析为结构化的电池数据列表"""
    if _is_git_lfs_pointer(matfile):
        raise RuntimeError(
            "检测到 Git LFS 指针文件，当前 MAT 数据未实际下载。"
            "请在仓库根目录执行 `git lfs pull` 后重试。"
        )

    data = scipy.io.loadmat(matfile)
    filename = matfile.split('/')[-1].split('.')[0]
    col = data[filename]
    col = col[0][0][0][0]  # 根据NASA数据结构解包
    size = col.shape[0]
    result = []
    for i in range(size):
        k = list(col[i][3][0].dtype.fields.keys())
        d2 = {}
        # 跳过 impedance 类型（如果不需要）
        if str(col[i][0][0]) != 'impedance':
            for j in range(len(k)):
                t = col[i][3][0][0][j][0]
                l = [t[m] for m in range(len(t))]
                d2[k[j]] = l
            try:
                parsed_time = convert_to_time(col[i][2][0])
            except Exception:
                parsed_time = datetime(1970, 1, 1)
            d1 = {
                'type': str(col[i][0][0]),
                'temp': _to_int_scalar(col[i][1][0]),
                'time': parsed_time,
                'data': d2
            }
            result.append(d1)
    return result

def getBatteryCapacity(Battery):
    """从加载的电池数据中提取容量序列"""
    cycle, capacity = [], []
    i = 1
    for Bat in Battery:
        if Bat['type'] == 'discharge':
            capacity.append(Bat['data']['Capacity'][0])
            cycle.append(i)
            i += 1
    return [cycle, capacity]

def getBatteryValues(Battery, Type='charge'):
    """提取指定类型（charge/discharge）的所有循环数据"""
    data = []
    for Bat in Battery:
        if Bat['type'] == Type:
            data.append(Bat['data'])
    return data