"""
Tool registry for agents. Tools provide concrete capabilities that agents
can use during execution (web search, file operations, HTTP requests, etc.)
"""

import json
import time
import httpx
from dataclasses import dataclass
from typing import Any, Callable, Awaitable


@dataclass
class ToolResult:
    success: bool
    data: Any
    error: str | None = None


class Tool:
    """Base tool that agents can invoke."""
    def __init__(self, name: str, description: str, fn: Callable[..., Awaitable[ToolResult]]):
        self.name = name
        self.description = description
        self.fn = fn

    async def invoke(self, **kwargs) -> ToolResult:
        try:
            return await self.fn(**kwargs)
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


class ToolRegistry:
    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, name: str, description: str):
        def decorator(fn):
            cls._tools[name] = Tool(name, description, fn)
            return fn
        return decorator

    @classmethod
    def get(cls, name: str) -> Tool | None:
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> list[dict]:
        return [
            {"name": t.name, "description": t.description}
            for t in sorted(cls._tools.values(), key=lambda x: x.name)
        ]


@ToolRegistry.register("web_fetch", "Fetch content from a URL")
async def web_fetch(url: str, **kwargs) -> ToolResult:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, follow_redirects=True)
            text = resp.text[:5000]
            return ToolResult(success=True, data={"status": resp.status_code, "content": text, "url": str(resp.url)})
    except Exception as e:
        return ToolResult(success=False, data=None, error=str(e))


@ToolRegistry.register("text_transform", "Transform text (uppercase, lowercase, reverse, word_count, char_count)")
async def text_transform(text: str, operation: str = "word_count", **kwargs) -> ToolResult:
    ops = {
        "uppercase": lambda t: t.upper(),
        "lowercase": lambda t: t.lower(),
        "reverse": lambda t: t[::-1],
        "word_count": lambda t: str(len(t.split())),
        "char_count": lambda t: str(len(t)),
        "title_case": lambda t: t.title(),
        "strip": lambda t: t.strip(),
    }
    fn = ops.get(operation)
    if not fn:
        return ToolResult(success=False, data=None, error=f"Unknown operation: {operation}")
    return ToolResult(success=True, data={"result": fn(text), "operation": operation})


@ToolRegistry.register("json_parse", "Parse and validate JSON string")
async def json_parse(text: str, **kwargs) -> ToolResult:
    try:
        data = json.loads(text)
        return ToolResult(success=True, data={"parsed": data, "valid": True, "type": type(data).__name__})
    except json.JSONDecodeError as e:
        return ToolResult(success=False, data={"valid": False}, error=str(e))


@ToolRegistry.register("csv_analyze", "Analyze CSV data and return summary statistics")
async def csv_analyze(csv_text: str, **kwargs) -> ToolResult:
    lines = csv_text.strip().split("\n")
    if len(lines) < 2:
        return ToolResult(success=False, data=None, error="CSV must have header and at least one row")

    headers = [h.strip() for h in lines[0].split(",")]
    rows = []
    for line in lines[1:]:
        values = [v.strip() for v in line.split(",")]
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))

    numeric_cols = {}
    for header in headers:
        vals = []
        for row in rows:
            try:
                vals.append(float(row[header]))
            except (ValueError, KeyError):
                break
        if len(vals) == len(rows) and vals:
            numeric_cols[header] = {
                "min": min(vals),
                "max": max(vals),
                "mean": sum(vals) / len(vals),
                "count": len(vals),
            }

    return ToolResult(success=True, data={
        "row_count": len(rows),
        "columns": headers,
        "numeric_summary": numeric_cols,
        "sample_rows": rows[:3],
    })


@ToolRegistry.register("timer", "Get current timestamp or measure elapsed time")
async def timer(action: str = "now", **kwargs) -> ToolResult:
    return ToolResult(success=True, data={"timestamp": time.time(), "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
