"""Dashboard Agent — explore agent_dashboard_playground.csv with the OpenAI Responses API.

Five tools give a model everything it needs to answer questions and build
visualizations over the mission-operations dataset:

  1. get_schema       — describe columns, dtypes, categorical values, numeric ranges
  2. aggregate        — group-by + metric + aggregation + filters + sort/top-N
  3. describe_numeric — distribution stats for a numeric column (optionally segmented)
  4. plot_chart       — save a bar/line/hist/scatter/box PNG
  5. run_python       — sandboxed pandas escape hatch for arbitrary questions

Run:  python app.py "Which department has the highest average cost per mission?"
"""

import json
import sys

import matplotlib
matplotlib.use("Agg")  # headless: render straight to PNG files
import matplotlib.pyplot as plt
import pandas as pd
from openai import OpenAI

DATA_PATH = "./agent_dashboard_playground.csv"
CHART_DIR = "./charts"
MODEL = "gpt-5.4-mini"

df = pd.read_csv(DATA_PATH, parse_dates=["started_at"])
client = OpenAI()


# --------------------------------------------------------------------------- #
# Tool implementations                                                        #
# --------------------------------------------------------------------------- #
def get_schema() -> dict:
    """Column-level map of the dataset so the agent never guesses names/values."""
    schema = {"n_rows": len(df), "columns": {}}
    for col in df.columns:
        s = df[col]
        info = {"dtype": str(s.dtype)}
        if pd.api.types.is_numeric_dtype(s):
            info.update(min=float(s.min()), max=float(s.max()), mean=round(float(s.mean()), 3))
        elif s.nunique() <= 30:
            info["categories"] = sorted(map(str, s.dropna().unique()))
        else:
            info.update(n_unique=int(s.nunique()), examples=list(map(str, s.dropna().unique()[:5])))
        schema["columns"][col] = info
    return schema


def _apply_filters(frame: pd.DataFrame, filters: list[dict] | None) -> pd.DataFrame:
    """filters: [{"column","op","value"}] with op in ==,!=,>,>=,<,<=,in."""
    if not filters:
        return frame
    for f in filters:
        col, op, val = f["column"], f["op"], f["value"]
        s = frame[col]
        if op == "==":
            frame = frame[s == val]
        elif op == "!=":
            frame = frame[s != val]
        elif op == ">":
            frame = frame[s > val]
        elif op == ">=":
            frame = frame[s >= val]
        elif op == "<":
            frame = frame[s < val]
        elif op == "<=":
            frame = frame[s <= val]
        elif op == "in":
            frame = frame[s.isin(val)]
        else:
            raise ValueError(f"unsupported op: {op}")
    return frame


def aggregate(group_by, metric=None, agg="count", filters=None, sort_desc=True, top_n=20) -> dict:
    """Group-by aggregation: the core analytical query."""
    frame = _apply_filters(df, filters)
    group_by = [group_by] if isinstance(group_by, str) else group_by

    if agg == "count":
        out = frame.groupby(group_by).size().reset_index(name="count")
        sort_col = "count"
    else:
        out = getattr(frame.groupby(group_by)[metric], agg)().reset_index()
        sort_col = metric

    out = out.sort_values(sort_col, ascending=not sort_desc).head(top_n)
    return {"rows": json.loads(out.round(4).to_json(orient="records")), "n_returned": len(out)}


def describe_numeric(column, group_by=None, filters=None) -> dict:
    """Distribution stats (mean/median/std/percentiles) for a numeric column."""
    frame = _apply_filters(df, filters)
    stats = ["mean", "median", "std", "min", "max"]
    if group_by:
        g = frame.groupby(group_by)[column]
        out = g.agg(["mean", "median", "std", "min", "max", "count"]).round(4)
        return {"by": group_by, "rows": json.loads(out.reset_index().to_json(orient="records"))}
    s = frame[column]
    return {
        "column": column,
        "count": int(s.count()),
        **{k: round(float(getattr(s, k)()), 4) for k in stats},
        "p25": round(float(s.quantile(0.25)), 4),
        "p75": round(float(s.quantile(0.75)), 4),
        "p95": round(float(s.quantile(0.95)), 4),
    }


def _resolve_colors(colors, n):
    """Return a list of n colors from an explicit list, a named colormap, or a default palette."""
    from matplotlib import colormaps
    if isinstance(colors, list) and colors:  # explicit colors, cycled to length n
        return [colors[i % len(colors)] for i in range(n)]
    if isinstance(colors, str) and colors in colormaps:  # named colormap, e.g. "viridis"
        cmap = colormaps[colors]
        return [cmap(i / max(n - 1, 1)) for i in range(n)]
    if isinstance(colors, str):  # single named/hex color for every bar
        return [colors] * n
    return [f"C{i % 10}" for i in range(n)]  # default: distinct color per bar


def plot_chart(kind, x, y=None, agg="mean", filters=None, top_n=20, title=None, colors=None) -> dict:
    """Render a chart to PNG. kind in bar,line,hist,scatter,box.

    colors: optional. A list of colors (one per bar/point, cycled), a single color name/hex,
    or a named matplotlib colormap (e.g. "viridis"). Bars default to a distinct color each.
    """
    import os
    os.makedirs(CHART_DIR, exist_ok=True)
    frame = _apply_filters(df, filters)
    fig, ax = plt.subplots(figsize=(9, 5))

    if kind == "hist":
        ax.hist(frame[x].dropna(), bins=30, color=_resolve_colors(colors, 1)[0] if colors else "C0")
        ax.set_xlabel(x); ax.set_ylabel("frequency")
    elif kind == "scatter":
        ax.scatter(frame[x], frame[y], s=12, alpha=0.5, c=_resolve_colors(colors, 1)[0] if colors else "C0")
        ax.set_xlabel(x); ax.set_ylabel(y)
    elif kind == "box":
        groups = [g[y].dropna().values for _, g in frame.groupby(x)]
        ax.boxplot(groups, labels=[str(k) for k, _ in frame.groupby(x)])
        ax.set_xlabel(x); ax.set_ylabel(y); plt.xticks(rotation=45, ha="right")
    else:  # bar / line: aggregate y over x
        data = getattr(frame.groupby(x)[y], agg)().sort_values(ascending=False).head(top_n)
        labels = data.index.astype(str)
        if kind == "bar":
            ax.bar(labels, data.values, color=_resolve_colors(colors, len(data)))  # distinct color per bar
        else:
            ax.plot(labels, data.values, color=_resolve_colors(colors, 1)[0] if colors else "C0")
        ax.set_xlabel(x); ax.set_ylabel(f"{agg}({y})"); plt.xticks(rotation=45, ha="right")

    ax.set_title(title or f"{kind} of {y or x} by {x}")
    fig.tight_layout()
    path = f"{CHART_DIR}/chart_{kind}_{x}.png"
    fig.savefig(path, dpi=120); plt.close(fig)
    return {"chart_path": path, "kind": kind}


def run_python(code: str) -> dict:
    """Escape hatch: execute pandas code against `df`. Assign result to `result`."""
    scope = {"df": df, "pd": pd, "result": None}
    exec(code, scope)  # noqa: S102 — demo sandbox; trust the model's own code
    result = scope["result"]
    if isinstance(result, (pd.DataFrame, pd.Series)):
        result = json.loads(result.head(50).to_json(orient="records" if isinstance(result, pd.DataFrame) else "index"))
    elif hasattr(result, "item"):  # numpy scalar -> native python
        result = result.item()
    return {"result": result}


TOOL_FNS = {
    "get_schema": get_schema,
    "aggregate": aggregate,
    "describe_numeric": describe_numeric,
    "plot_chart": plot_chart,
    "run_python": run_python,
}


# --------------------------------------------------------------------------- #
# Tool schemas (Responses API function-calling format)                        #
# --------------------------------------------------------------------------- #
TOOLS = [
    {
        "type": "function",
        "name": "get_schema",
        "description": "Return columns, dtypes, categorical values, and numeric ranges. Call this FIRST to learn valid column names and filter values.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "type": "function",
        "name": "aggregate",
        "description": "Group-by aggregation over the dataset. Use for questions like 'average cost by department' or 'mission count by model'.",
        "parameters": {
            "type": "object",
            "properties": {
                "group_by": {"type": "array", "items": {"type": "string"}, "description": "Column(s) to group by."},
                "metric": {"type": "string", "description": "Numeric column to aggregate (omit for agg='count')."},
                "agg": {"type": "string", "enum": ["count", "mean", "sum", "median", "min", "max", "std"]},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string"},
                            "op": {"type": "string", "enum": ["==", "!=", ">", ">=", "<", "<=", "in"]},
                            "value": {},
                        },
                        "required": ["column", "op", "value"],
                    },
                },
                "sort_desc": {"type": "boolean"},
                "top_n": {"type": "integer"},
            },
            "required": ["group_by"],
        },
    },
    {
        "type": "function",
        "name": "describe_numeric",
        "description": "Distribution statistics (mean, median, std, percentiles) for a numeric column, optionally grouped by a categorical column.",
        "parameters": {
            "type": "object",
            "properties": {
                "column": {"type": "string"},
                "group_by": {"type": "string"},
                "filters": {"type": "array", "items": {"type": "object"}},
            },
            "required": ["column"],
        },
    },
    {
        "type": "function",
        "name": "plot_chart",
        "description": "Render a chart to a PNG file and return its path. kind: bar/line (aggregate y over x), hist (distribution of x), scatter (x vs y), box (y distribution per x).",
        "parameters": {
            "type": "object",
            "properties": {
                "kind": {"type": "string", "enum": ["bar", "line", "hist", "scatter", "box"]},
                "x": {"type": "string"},
                "y": {"type": "string"},
                "agg": {"type": "string", "enum": ["mean", "sum", "count", "median", "max", "min"]},
                "filters": {"type": "array", "items": {"type": "object"}},
                "top_n": {"type": "integer"},
                "title": {"type": "string"},
                "colors": {
                    "description": "Optional bar/point coloring: a list of color names/hex (one per bar, cycled), a single color, or a named matplotlib colormap like 'viridis' or 'plasma'. Bars are distinctly colored by default.",
                    "anyOf": [
                        {"type": "array", "items": {"type": "string"}},
                        {"type": "string"},
                    ],
                },
            },
            "required": ["kind", "x"],
        },
    },
    {
        "type": "function",
        "name": "run_python",
        "description": "Execute pandas code against the DataFrame `df` for anything the other tools can't express. Assign the answer to a variable named `result`.",
        "parameters": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code. `df` and `pd` are in scope; set `result`."}},
            "required": ["code"],
        },
    },
]

SYSTEM = (
    "You are a dashboard analyst for an AI-agent operations dataset. "
    "Call get_schema before referencing columns. Prefer the structured tools; "
    "use run_python only when needed. "
    "To show a chart you MUST call plot_chart every time the user asks to see or update a "
    "visualization, even if a similar chart was made earlier. NEVER paste or mention raw file "
    "paths like ./charts/foo.png; charts render automatically in the dashboard panel beside the "
    "chat — just briefly describe what the chart shows. "
    "Answer with concrete numbers and a brief interpretation."
    "For charts, be colorful, bar charts for example differnt color for each bar"
    "Always be as concise as possible!"
)


# --------------------------------------------------------------------------- #
# Agent loop                                                                  #
# --------------------------------------------------------------------------- #
def ask(question: str, max_turns: int = 8) -> str:
    input_items = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": question},
    ]
    for _ in range(max_turns):
        resp = client.responses.create(model=MODEL, input=input_items, tools=TOOLS)
        input_items += resp.output  # carry forward reasoning + tool calls

        calls = [item for item in resp.output if item.type == "function_call"]
        if not calls:
            return resp.output_text

        for call in calls:
            args = json.loads(call.arguments)
            try:
                output = TOOL_FNS[call.name](**args)
            except Exception as e:  # feed errors back so the model can recover
                output = {"error": f"{type(e).__name__}: {e}"}
            print(f"  ↳ {call.name}({args}) ")
            input_items.append(
                {"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(output)}
            )
    return "Stopped: reached max turns."


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "Which department has the highest average cost per mission, and show a bar chart of avg cost by department."
    print(f"\nQ: {q}\n")
    print(ask(q))
