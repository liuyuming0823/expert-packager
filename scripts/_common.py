"""expert-packager 共用工具：路径定位、frontmatter 解析、字段常量、校验基础件。

纯标准库实现，无第三方依赖。
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True

# ────────────────────────────────────────────────────────────── 常量

EXPERT_MARKETPLACE = "my-experts"
PLUGIN_DIR = ".codebuddy-plugin"

# 行业分类：开放平台 / 专家中心枚举，不可自造
CATEGORIES = {
    "01-ProductDesign": "产品设计",
    "02-Engineering": "技术工程",
    "03-GameSpatial": "游戏空间",
    "04-DataAI": "数据智能",
    "05-MarketingGrowth": "营销增长",
    "06-ContentCreative": "内容创作",
    "07-SalesCommerce": "销售商务",
    "08-FinanceInvestment": "金融投资",
    "09-OperationsHR": "运营人力",
    "10-ProjectQuality": "项目质量",
    "11-SecurityCompliance": "法务安全",
    "12-IndustryConsultant": "行业顾问",
}

KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TODO_RE = re.compile(r"\[TODO\]|\{\{.*?\}\}|<<.*?>>")
PLACEHOLDER_RE = re.compile(r"\{[a-z][a-z0-9_]*\}")

C_ERR, C_WARN, C_OK, C_DIM, C_RST = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"


def use_utf8_stdout() -> None:
    """Windows 控制台默认 cp936，直接 print 中文会炸，这里强制切 UTF-8。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass


# ────────────────────────────────────────────────────────────── 路径

def config_home() -> Path:
    """WorkBuddy 配置根目录，优先读环境变量注入的值。"""
    for var in ("WORKBUDDY_CONFIG_DIR", "CODEBUDDY_CONFIG_DIR"):
        value = os.environ.get(var)
        if value:
            return Path(value).expanduser()
    return Path.home() / ".workbuddy"


def experts_plugins_dir() -> Path:
    """专家安装目录（固定）——专家必须落在这里才会被专家中心检测到。"""
    return config_home() / "plugins" / "marketplaces" / EXPERT_MARKETPLACE / "plugins"


def find_marketplace_json(start) -> Path | None:
    """从给定目录向上查找 .codebuddy-plugin/marketplace.json。"""
    path = Path(start).resolve()
    for parent in (path, *path.parents):
        candidate = parent / PLUGIN_DIR / "marketplace.json"
        if candidate.is_file():
            return candidate
    return None


def find_plugin_json(root) -> Path | None:
    path = Path(root) / PLUGIN_DIR / "plugin.json"
    return path if path.is_file() else None


# ────────────────────────────────────────────────────────────── JSON 读写

def read_json(path, default=None):
    path = Path(path)
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SystemExit(f"[X] JSON 解析失败：{path}\n    {exc}") from exc


def write_json(path, data) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ────────────────────────────────────────────────────────────── frontmatter

def read_frontmatter(text: str) -> dict:
    """解析 SKILL.md / agent.md 的 YAML frontmatter。

    只支持本场景实际会用到的子集：单行标量、折叠块（>- / > / |）、简单列表。
    嵌套映射（如 metadata.author）不展开，键值取到缩进块的第一行。
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return {}
    body = stripped[3:]
    end = body.find("\n---")
    if end < 0:
        return {}

    out: dict = {}
    block_key: str | None = None
    block_lines: list[str] = []

    def flush() -> None:
        nonlocal block_key, block_lines
        if block_key is not None:
            out[block_key] = " ".join(x for x in block_lines if x)
        block_key, block_lines = None, []

    for line in body[:end].splitlines():
        if block_key is not None:
            if not line.strip() or line[:1] in (" ", "\t"):
                block_lines.append(line.strip().lstrip("-").strip())
                continue
            flush()
        match = re.match(r"^([A-Za-z_][\w.\-]*):\s*(.*)$", line)
        if not match:
            continue
        key, value = match.group(1), match.group(2).strip()
        # 折叠块、空值（后跟缩进的嵌套映射或列表）都按块收集，
        # 这样 displayName: / trigger: 这类写法也能取到非空值。
        if value in (">-", ">", "|-", "|", ""):
            block_key, block_lines = key, []
        else:
            out[key] = value.strip('"').strip("'")
    flush()
    return out


def char_count(text: str) -> int:
    """字数统计：忽略空白，中文按字计。"""
    return len(re.sub(r"\s+", "", text or "")) if isinstance(text, str) else 0


def word_count(text: str) -> int:
    return len((text or "").split()) if isinstance(text, str) else 0


# ────────────────────────────────────────────────────────────── 专家包识别

def load_plugin_json(root) -> dict | None:
    path = find_plugin_json(root)
    return read_json(path, {}) if path else None


def is_expert_dir(root) -> bool:
    """判断目录是不是专家包：有 plugin.json 且声明了 expertType，或有 agents/ 目录。"""
    root = Path(root)
    data = load_plugin_json(root)
    if isinstance(data, dict) and data.get("expertType") in ("agent", "team"):
        return True
    agents = root / "agents"
    return agents.is_dir() and any(agents.glob("*.md"))


def is_skill_dir(root) -> bool:
    return (Path(root) / "SKILL.md").is_file()


def normalize_path(raw: str) -> str:
    """把 ./agents/x.md / agents\\x.md 统一成 posix 相对路径。"""
    return raw.strip().lstrip("./").replace("\\", "/")


# ────────────────────────────────────────────────────────────── 报告

class Report:
    """P0/P1/P2 分级报告：按 (级别, 规则) 聚合，只给计数 + 样例，避免刷屏。"""

    LEVELS = {"P0": "阻断", "P1": "警告", "P2": "知情"}

    def __init__(self, title: str = "校验报告"):
        self.title = title
        self.items: list[tuple[str, str, str]] = []  # (level, rule, detail)

    def add(self, level: str, rule: str, detail: str = "") -> None:
        self.items.append((level, rule, detail))

    def count(self, level: str) -> int:
        return sum(1 for lv, _, _ in self.items if lv == level)

    @property
    def ok(self) -> bool:
        return self.count("P0") == 0 and self.count("P1") == 0

    def render(self, max_samples: int = 2) -> str:
        lines = [f"\n{self.title}", "─" * 56]
        if not self.items:
            lines.append(f"{C_OK}[OK]{C_RST} 全部检查通过")
            return "\n".join(lines)

        grouped: dict[tuple[str, str], list[str]] = {}
        for level, rule, detail in self.items:
            grouped.setdefault((level, rule), []).append(detail)

        for level in ("P0", "P1", "P2"):
            rows = {k: v for k, v in grouped.items() if k[0] == level}
            if not rows:
                continue
            color = {"P0": C_ERR, "P1": C_WARN, "P2": C_DIM}[level]
            total = sum(len(v) for v in rows.values())
            lines.append(f"\n{color}[{level} · {self.LEVELS[level]}]{C_RST} {total} 项")
            for (_, rule), details in rows.items():
                lines.append(f"  · {rule}  ({len(details)})")
                for detail in details[:max_samples]:
                    lines.append(f"      - {detail}")
                if len(details) > max_samples:
                    lines.append(f"      … 另有 {len(details) - max_samples} 处同类")
        lines.append("─" * 56)
        lines.append(
            f"小结：P0={self.count('P0')}  P1={self.count('P1')}  P2={self.count('P2')}"
        )
        return "\n".join(lines)
