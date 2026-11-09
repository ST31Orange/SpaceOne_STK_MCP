"""Generate docs/TOOL_CATALOG.md from the Python registry."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "stk-mcp" / "src"))

from spaceone_stk_mcp.registry import catalog  # noqa: E402


def main() -> int:
    data = catalog()
    lines = [
        "# spaceone-stk-mcp 工具目录",
        "",
        "本文件由 `stk-mcp/scripts/export_tool_docs.py` 从 Python 注册表生成，请勿手工编辑。",
        "",
        f"- 产品版本：`{data['version']}`",
        f"- 操作总数：**{data['tool_count']}**",
        f"- 分类：{', '.join(f'`{name}`' for name in data['categories'])}",
        "- 完整 JSON Schema：`stk-mcp/contracts/tools.json`",
        "",
        "| 操作 | 分类 | 写操作 | 说明 |",
        "|---|---|---|---|",
    ]
    for tool in data["tools"]:
        lines.append(
            f"| `{tool['name']}` | {tool['category']} | {'是' if tool['mutating'] else '否'} | {tool['description']} |"
        )
    lines.append("")
    (ROOT / "docs").mkdir(exist_ok=True)
    target = ROOT / "docs" / "TOOL_CATALOG.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {target} ({data['tool_count']} tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
