import ast
import operator
from datetime import datetime, timezone

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a basic arithmetic expression and return the numeric result. "
                           "Supports + - * / ** and parentheses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "e.g. 47 * 89"},
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time (UTC). Takes no arguments.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}
_ALLOWED_UNARYOPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        return _ALLOWED_BINOPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        return _ALLOWED_UNARYOPS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression element: {type(node).__name__}")


def _calculate(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except Exception as exc:
        return f"Error: could not evaluate '{expression}': {exc}"


def _get_current_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_tool(name: str, arguments: dict) -> str:
    """Executes a tool by name. Never raises — returns an error string instead,
    so a hallucinated tool name or bad arguments can't crash the request; the
    model sees the error and can retry or explain to the user.
    """
    if name == "calculate":
        expression = arguments.get("expression", "")
        return _calculate(expression)
    if name == "get_current_time":
        return _get_current_time()
    return f"Error: unknown tool '{name}'"
