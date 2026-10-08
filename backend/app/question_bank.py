"""原创 Python 新手题库生成器。

生成器不会用“同一个模板只换数字/变量名”的方式凑题量。每道代码题都计算 AST
结构指纹；指纹比较前会抹去常量与自定义名称，所以仅替换数字、字符串或变量名的
候选题会被拒绝。题目程序在生成时实际运行，运行输出就是正确答案。
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import re
from contextlib import redirect_stdout
from dataclasses import dataclass
from random import Random
from typing import Callable


STAGES = {
    1: "输出与基础语法",
    2: "变量与数据类型",
    3: "运算符与表达式",
    4: "字符串",
    5: "列表与元组",
    6: "字典与集合",
    7: "条件判断",
    8: "循环",
    9: "函数",
    10: "异常、模块与面向对象入门",
}
QUESTIONS_PER_STAGE = 1_000
TOTAL_QUESTIONS = len(STAGES) * QUESTIONS_PER_STAGE
QUESTION_BANK_VERSION = "2026.10-structural-unique-v4"
LETTERS = "ABCD"
CODE_PATTERN = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


@dataclass(frozen=True)
class Draft:
    code: str
    analysis: str
    prompt: str = "运行下面的代码，输出结果是什么？"
    distractors: tuple[str, ...] = ()


@dataclass(frozen=True)
class GeneratedQuestion:
    data: dict[str, str | None]
    stage: int
    structure_fingerprint: str


class _StructureNormalizer(ast.NodeTransformer):
    """抹去可随意替换的值，只留下真正的程序结构。"""

    _kept_names = {
        "print", "len", "type", "int", "float", "str", "bool", "list",
        "tuple", "dict", "set", "range", "enumerate", "zip", "sum", "min",
        "max", "sorted", "reversed", "abs", "round", "all", "any", "map",
        "filter", "isinstance", "chr", "ord", "bin", "hex", "divmod", "pow",
        "math", "statistics", "json", "True", "False", "None", "next", "super",
        "ValueError", "TypeError", "ZeroDivisionError", "KeyError", "IndexError",
    }

    def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802
        value = node.value
        if value is None:
            marker: object = None
        elif isinstance(value, bool):
            marker = "<bool>"
        elif isinstance(value, int):
            marker = "<int>"
        elif isinstance(value, float):
            marker = "<float>"
        elif isinstance(value, str):
            marker = "<str>"
        else:
            marker = f"<{type(value).__name__}>"
        return ast.copy_location(ast.Constant(value=marker), node)

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: N802
        name = node.id if node.id in self._kept_names else "VAR"
        return ast.copy_location(ast.Name(id=name, ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:  # noqa: N802
        return ast.copy_location(ast.arg(arg="ARG", annotation=None), node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
        node = self.generic_visit(node)
        node.name = "FUNCTION"
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:  # noqa: N802
        node = self.generic_visit(node)
        node.name = "CLASS"
        return node


def structure_fingerprint(code: str) -> str:
    tree = ast.parse(code)
    normalized = _StructureNormalizer().visit(tree)
    ast.fix_missing_locations(normalized)
    return ast.dump(normalized, annotate_fields=True, include_attributes=False)


def _run(code: str) -> str:
    """运行生成器内部的可信代码；这里不执行任何用户输入。"""
    stream = io.StringIO()
    namespace = {"__builtins__": __builtins__}
    with redirect_stdout(stream):
        exec(compile(code, "<question-bank>", "exec"), namespace, namespace)
    output = stream.getvalue()
    if len(output) > 240:
        raise ValueError("题目输出过长")
    return output[:-1] if output.endswith("\n") else output


def _code(source: str) -> str:
    return f"```python\n{source}\n```"


def _choice_text(value: object) -> str:
    if value == "":
        return "（无输出）"
    if value is None:
        return "None"
    return str(value)


def visible_choice_signature(value: object) -> str:
    """按页面可见效果归一化选项，避免换行和空格看起来完全相同。"""
    return re.sub(r"\s+", " ", _choice_text(value)).strip()


def _generic_distractors(correct: str) -> list[str]:
    candidates: list[str] = []
    stripped = correct.strip()
    if re.fullmatch(r"-?\d+", stripped):
        number = int(stripped)
        candidates.extend([str(number + 1), str(number - 1), str(number * 2), "0"])
    elif re.fullmatch(r"-?\d+\.\d+", stripped):
        number = float(stripped)
        candidates.extend([str(int(number)), str(number + 1), str(round(number, 1))])
    elif stripped in {"True", "False"}:
        candidates.extend(["False" if stripped == "True" else "True", "None", "0"])
    lines = correct.splitlines()
    if len(lines) > 1:
        candidates.extend(["\n".join(reversed(lines)), lines[0], " ".join(lines)])
    words = correct.split()
    if len(words) > 1:
        candidates.extend(["".join(words), " ".join(reversed(words))])
    if correct:
        candidates.extend([correct[::-1], correct.upper(), correct.lower()])
    candidates.extend(["None", "程序报错", "（无输出）"])
    return candidates


def _make_question(
    stage: int,
    draft: Draft,
    fingerprint: str,
    question_type: str,
) -> dict[str, str | None]:
    correct = _choice_text(_run(draft.code))
    seed = int(hashlib.sha256(fingerprint.encode()).hexdigest()[:16], 16)
    rng = Random(seed)

    if question_type == "fill_blank":
        prompt = "填写下面代码的输出结果（多行输出可用换行或 `\\n` 表示）。"
        choices = ["", "", "", ""]
        answer = "A"  # 兼容原 questions.answer 的 A-D 约束，实际答案见 accepted_answers。
        accepted_answers = json.dumps([correct], ensure_ascii=False)
    elif question_type == "true_false":
        wrong_answers = [item for item in _generic_distractors(correct) if item != correct]
        statement_is_true = rng.choice([True, False])
        claimed = correct if statement_is_true else wrong_answers[0]
        claimed_shown = claimed.replace("\n", "\\n")
        prompt = f"判断题：下面代码的输出是 `{claimed_shown}`。这个说法是否正确？"
        choices = ["正确", "错误", "", ""]
        answer = "A" if statement_is_true else "B"
        accepted_answers = None
    else:
        prompt = draft.prompt
        choices = [correct]
        visible_choices = {visible_choice_signature(correct)}
        for item in [*draft.distractors, *_generic_distractors(correct)]:
            text = _choice_text(item)
            signature = visible_choice_signature(text)
            if text not in choices and signature not in visible_choices:
                choices.append(text)
                visible_choices.add(signature)
            if len(choices) == 4:
                break
        if len(choices) != 4:
            raise ValueError("无法生成四个不同的选项")
        rng.shuffle(choices)
        answer = LETTERS[choices.index(correct)]
        accepted_answers = None

    title = f"【阶段 {stage}：{STAGES[stage]}】\n\n{prompt}\n\n{_code(draft.code)}"
    shown_answer = correct.replace("\n", "\\n")
    return {
        "title": title,
        "option_a": choices[0],
        "option_b": choices[1],
        "option_c": choices[2],
        "option_d": choices[3],
        "answer": answer,
        "analysis": f"{draft.analysis} 因此最终输出为 `{shown_answer}`。",
        "question_type": question_type,
        "accepted_answers": accepted_answers,
    }


def _question_type(index: int) -> str:
    """每阶段严格保持 60% 选择、20% 判断、20% 填空。"""
    return ("fill_blank", "true_false", "single_choice", "single_choice", "single_choice")[index % 5]


def _string_literal(rng: Random) -> str:
    words = ["python", "code", "learn", "hello", "data", "apple", "banana", "river", "cloud", "green", "book", "music", "robot", "panda", "星星", "学习"]
    return repr(rng.choice(words))


def _numeric_expr(rng: Random, depth: int) -> str:
    if depth <= 0 or rng.random() < 0.25:
        return str(rng.randint(1, 9))
    kind = rng.choice(["binary", "binary", "unary", "builtin"])
    if kind == "unary":
        return f"{rng.choice(['+', '-'])}({_numeric_expr(rng, depth - 1)})"
    if kind == "builtin":
        return f"{rng.choice(['abs', 'round'])}({_numeric_expr(rng, depth - 1)})"
    left = _numeric_expr(rng, depth - 1)
    op = rng.choice(["+", "-", "*", "//", "%"])
    right = str(rng.randint(1, 7)) if op in {"//", "%"} else _numeric_expr(rng, max(0, depth - 2))
    return f"({left} {op} {right})"


def _comparison(rng: Random, depth: int = 2) -> str:
    return f"{_numeric_expr(rng, depth)} {rng.choice(['<', '<=', '>', '>=', '==', '!='])} {_numeric_expr(rng, max(0, depth - 1))}"


def _list_values(rng: Random, size: int | None = None) -> list[int]:
    return [rng.randint(1, 12) for _ in range(size or rng.randint(3, 6))]


def _stage_1(attempt: int) -> Draft:
    rng = Random(101_000_003 + attempt)
    statements: list[str] = []
    notes: list[str] = []
    for line_index in range(rng.randint(1, 4)):
        expressions: list[str] = []
        for _ in range(rng.randint(1, 4)):
            kind = rng.choice(["text", "integer", "repeat", "length", "sum", "type", "escape"])
            if kind == "text":
                expressions.append(_string_literal(rng))
            elif kind == "integer":
                expressions.append(str(rng.randint(-9, 18)))
            elif kind == "repeat":
                expressions.append(f"{repr(rng.choice(['Py', 'Hi', '*', 'Go']))} * {rng.randint(2, 4)}")
            elif kind == "length":
                expressions.append(f"len({_string_literal(rng)})")
            elif kind == "sum":
                expressions.append(f"{rng.randint(1, 9)} + {rng.randint(1, 9)}")
            elif kind == "type":
                expressions.append(f"type({rng.choice([str(rng.randint(1, 9)), repr('text'), 'True', '3.5'])}).__name__")
            else:
                expressions.append(repr(rng.choice(["A\nB", "A\tB", 'say "hi"'])))
        kwargs: list[str] = []
        if len(expressions) > 1 and rng.random() < 0.65:
            kwargs.append(f"sep={rng.choice(['-', '|', '/', '::', ''])!r}")
            notes.append("`sep` 决定同一次 print 中多个值之间的分隔符")
        if line_index < 3 and rng.random() < 0.45:
            kwargs.append(f"end={rng.choice(['', ' ', '->', '|'])!r}")
            notes.append("`end` 决定本次 print 结束时追加的内容")
        statements.append(f"print({', '.join([*expressions, *kwargs])})")
    return Draft("\n".join(statements), "；".join(dict.fromkeys(notes)) or "print 会先求值再显示结果")


def _stage_2(attempt: int) -> Draft:
    rng = Random(202_000_003 + attempt)
    pattern, a, b = rng.randrange(6), rng.randint(2, 30), rng.randint(1, 9)
    notes: list[str] = []
    if pattern == 0:
        lines = [f"value = {a}"]
        for _ in range(rng.randint(1, 6)):
            op = rng.choice(["+=", "-=", "*=", "//="])
            lines.append(f"value {op} {rng.randint(1, 3)}")
            notes.append(f"`{op}` 是增强赋值")
        lines.append("print(value, type(value).__name__)")
    elif pattern == 1:
        lines = [f"text = {str(a)!r}"]
        for step in rng.sample(["integer", "floating", "boolean", "text"], rng.randint(2, 4)):
            name, conversion = {"integer": ("integer", "int"), "floating": ("decimal", "float"), "boolean": ("flag", "bool"), "text": ("copy", "str")}[step]
            lines.append(f"{name} = {conversion}(text)")
        names = [name for name in ["integer", "decimal", "flag", "copy"] if any(line.startswith(name) for line in lines)]
        lines.append(f"print({', '.join(names)})")
        notes.append("类型转换函数返回对应类型的新值")
    elif pattern == 2:
        x, y = rng.sample(["x", "y", "left", "right"], 2)
        lines = [f"{x}, {y} = {a}, {b}"]
        for _ in range(rng.randint(1, 3)):
            lines.append(f"{x}, {y} = {y}, {x}" if rng.random() < 0.5 else f"{x} = {x} + {y}")
        lines.append(f"print({x}, {y})")
        notes.append("多重赋值先计算右侧，再一次性绑定左侧变量")
    elif pattern == 3:
        literal = rng.choice(["0", str(a), "''", repr("python"), "[]", f"[{a}]", "None"])
        lines = [f"value = {literal}"]
        checks = rng.sample(["bool(value)", "type(value).__name__", "value is None", "isinstance(value, int)"], rng.randint(2, 4))
        lines.append(f"print({', '.join(checks)})")
        notes.append("真假值、类型名称、身份和类型判断各有不同含义")
    elif pattern == 4:
        lines = [f"first = second = {a}", f"second = second + {b}"]
        if rng.random() < 0.5:
            lines += ["third = float(first)", "print(first, second, third)"]
        else:
            lines += ["third = str(second)", "print(first, second, type(third).__name__)"]
        notes.append("整数不可变，重新绑定 second 不会改动 first")
    else:
        values = [rng.randint(1, 9) for _ in range(rng.randint(2, 4))]
        names = ["a", "b", "c", "d"][: len(values)]
        lines = [f"{', '.join(names)} = {', '.join(map(str, values))}"]
        for name in rng.sample(names, rng.randint(1, len(names))):
            lines.append(f"{name} = {rng.choice(['str', 'float', 'bool'])}({name})")
        lines.append(f"print({', '.join(f'type({name}).__name__' for name in names)})")
        notes.append("变量可以重新绑定到不同类型的对象")
    return Draft("\n".join(lines), "；".join(notes))


def _stage_3(attempt: int) -> Draft:
    rng = Random(303_000_007 + attempt)
    pattern = rng.randrange(5)
    if pattern == 0:
        code = f"result = {_numeric_expr(rng, rng.randint(2, 5))}\nprint(result)"
        analysis = "括号和运算符优先级决定求值顺序；`//` 是整除，`%` 取余"
    elif pattern == 1:
        parts = [_comparison(rng, rng.randint(1, 3)) for _ in range(rng.randint(2, 4))]
        expression = parts[0]
        for connector, part in zip([rng.choice(["and", "or"]) for _ in parts[1:]], parts[1:]):
            expression = f"({expression}) {connector} ({part})"
        if rng.random() < 0.5:
            expression = f"not ({expression})"
        code, analysis = f"print({expression})", "比较先得到布尔值，再由逻辑运算符组合"
    elif pattern == 2:
        code = f"number = {rng.randint(10, 99)}\nprint(divmod(number, {rng.randint(2, 9)}), pow({rng.randint(2, 5)}, {rng.randint(2, 4)}))"
        analysis = "`divmod` 同时返回商和余数，`pow` 执行幂运算"
    elif pattern == 3:
        a, b, c = [rng.randint(1, 15) for _ in range(3)]
        first, second = rng.sample(["<", "<=", ">", ">=", "!=", "=="], 2)
        code = f"a, b, c = {a}, {b}, {c}\nprint(a {first} b {second} c)"
        analysis = "链式比较等价于相邻比较用 `and` 连接"
    else:
        code = f"left = {_numeric_expr(rng, 2)}\nright = {_numeric_expr(rng, 2)}\nprint(abs(left - right), min(left, right), max(left, right))"
        analysis = "先求左右表达式，再计算差的绝对值、较小值和较大值"
    return Draft(code, analysis)


def _stage_4(attempt: int) -> Draft:
    if attempt == 0:
        return Draft(
            's = "Python is fun"\nresult = s.replace("fun", "powerful")\nprint(result)',
            "`str.replace(old, new)` 返回替换后的新字符串，原字符串不会被原地修改",
        )
    rng = Random(404_000_009 + attempt)
    pattern = rng.randrange(6)
    base = rng.choice(["  PyThon Lab  ", "banana split", "Code-Review", "hello_world", "学习 Python", "red,green,blue"])
    lines = [f"text = {base!r}"]
    notes: list[str] = []
    if pattern in {0, 1}:
        expression = "text"
        for _ in range(rng.randint(2, 5)):
            method = rng.choice(["strip", "lower", "upper", "title", "capitalize", "swapcase"])
            expression = f"{expression}.{method}()"
            notes.append(f"`{method}()` 返回转换后的新字符串")
        if pattern == 1:
            old, new = rng.choice([("a", "@"), ("o", "0"), (" ", "-")])
            expression = f"{expression}.replace({old!r}, {new!r}, {rng.randint(1, 3)})"
            notes.append("`replace` 的第三个参数限制最多替换次数")
        lines.append(f"print({expression})")
    elif pattern == 2:
        start, stop, step = rng.choice([0, 1, 2, -5]), rng.choice([None, 4, 7, -1]), rng.choice([1, 2, -1])
        lines.append(f"piece = text[{start}:{'' if stop is None else stop}:{step}]")
        lines.append(f"print({rng.choice(['piece', 'piece.upper()', 'len(piece)', 'piece[::-1]'])})")
        notes.append("切片包含起点、不包含终点，第三个位置是步长")
    elif pattern == 3:
        text, separator = rng.choice([("red,green,blue", ","), ("a-b-c-d", "-"), ("one_two_three", "_"), ("learn python now", " ")])
        lines = [f"text = {text!r}", f"parts = text.split({separator!r}, {rng.randint(1, 3)})"]
        lines.append(f"print({rng.choice(['|', '/', '', '::'])!r}.join(parts))")
        notes.append("`split` 按分隔符拆分，`join` 再用新连接符组合")
    elif pattern == 4:
        target = rng.choice(["a", "o", "Py", " "])
        checks = rng.sample([f"text.count({target!r})", f"text.find({target!r})", f"text.startswith({target!r})", f"text.endswith({target!r})", "len(text)"], rng.randint(2, 4))
        lines.append(f"print({', '.join(checks)})")
        notes.append("`count` 计数，`find` 找位置，首尾判断返回布尔值")
    else:
        method, width, fill = rng.choice(["center", "ljust", "rjust"]), rng.randint(15, 24), rng.choice(["-", "*", "."])
        expression = f"text.strip().{method}({width}, {fill!r})"
        if rng.random() < 0.6:
            expression = f"{expression}.replace(' ', '_')"
        lines.append(f"print({expression})")
        notes.append("对齐方法按宽度和填充字符补齐文本")
    return Draft("\n".join(lines), "；".join(dict.fromkeys(notes)))


def _stage_5(attempt: int) -> Draft:
    rng = Random(505_000_021 + attempt)
    pattern = rng.randrange(7)
    values = _list_values(rng)
    lines = [f"items = {values!r}"]
    notes: list[str] = []
    if pattern in {0, 1}:
        for _ in range(rng.randint(2, 5)):
            operation = rng.choice(["append", "extend", "insert", "reverse", "sort", "pop"])
            if operation == "append":
                lines.append(f"items.append({rng.randint(1, 15)})")
            elif operation == "extend":
                lines.append(f"items.extend({_list_values(rng, 2)!r})")
            elif operation == "insert":
                lines.append(f"items.insert({rng.randint(0, 2)}, {rng.randint(1, 15)})")
            elif operation == "reverse":
                lines.append("items.reverse()")
            elif operation == "sort":
                lines.append(f"items.sort(reverse={rng.choice([True, False])})")
            else:
                lines.append(f"items.pop({rng.choice([0, -1])})")
            notes.append(f"`{operation}` 按其规则原地处理列表")
        lines.append(rng.choice(["print(items)", "print(len(items), items[0], items[-1])", "print(sum(items))"]))
    elif pattern == 2:
        lines.append(f"part = items[{rng.randint(0, 2)}:{rng.randint(3, 7)}:{rng.choice([1, 2, -1])}]")
        lines.append(rng.choice(["print(part)", "print(part[::-1])", "print(len(part), sum(part))"]))
        notes.append("列表切片创建新列表，并遵循起点、终点和步长规则")
    elif pattern == 3:
        lines.append("copied = items.copy()")
        for _ in range(rng.randint(1, 3)):
            lines.append(f"{rng.choice(['items', 'copied'])}.append({rng.randint(13, 20)})")
        lines.append("print(items, copied, items == copied)")
        notes.append("`copy()` 创建浅拷贝，两个列表之后可以分别修改")
    elif pattern == 4:
        lines = [f"point = {tuple(values)!r}", "first, *middle, last = point", "print(first, middle, last)"]
        notes.append("带星号的解包把中间剩余元素收集到列表")
    elif pattern == 5:
        nested = [values[:2], values[2:4], values[4:] or [rng.randint(1, 9)]]
        lines = [f"matrix = {nested!r}"]
        accessors = rng.sample(["matrix[0][-1]", "matrix[1][0]", "len(matrix[-1])", "sum(matrix[0])"], rng.randint(2, 4))
        lines.append(f"print({', '.join(accessors)})")
        notes.append("嵌套索引先选择外层元素，再选择内层元素")
    else:
        lines.append(f"target = {rng.choice(values)}")
        checks = rng.sample(["target in items", "items.count(target)", "items.index(target)", "min(items)", "max(items)"], rng.randint(2, 4))
        lines.append(f"print({', '.join(checks)})")
        notes.append("成员判断、计数和索引方法从不同角度查询列表")
    return Draft("\n".join(lines), "；".join(dict.fromkeys(notes)))


def _stage_6(attempt: int) -> Draft:
    rng = Random(606_000_023 + attempt)
    pattern = rng.randrange(7)
    notes: list[str] = []
    if pattern in {0, 1, 2, 3}:
        data = {"red": rng.randint(1, 9), "blue": rng.randint(1, 9), "green": rng.randint(1, 9)}
        lines = [f"data = {data!r}"]
        if pattern == 0:
            for _ in range(rng.randint(2, 5)):
                operation, key, value = rng.choice(["assign", "update", "setdefault", "pop"]), rng.choice(["red", "blue", "green", "white"]), rng.randint(1, 15)
                if operation == "assign":
                    lines.append(f"data[{key!r}] = {value}")
                elif operation == "update":
                    lines.append(f"data.update({{{key!r}: {value}}})")
                elif operation == "setdefault":
                    lines.append(f"data.setdefault({key!r}, {value})")
                else:
                    lines.append(f"data.pop({key!r}, {value})")
                notes.append(f"字典 `{operation}` 操作按键处理数据")
            lines.append(rng.choice(["print(sorted(data.items()))", "print(len(data), sum(data.values()))", "print(sorted(data))"]))
        elif pattern == 1:
            getters = rng.sample(["data.get('red')", "data.get('white', 0)", "'blue' in data", "len(data)", "sum(data.values())"], rng.randint(2, 5))
            lines.append(f"print({', '.join(getters)})")
            notes.append("`get` 可提供默认值，`in` 默认检查字典的键")
        elif pattern == 2:
            lines += ["swapped = {value: key for key, value in data.items()}", rng.choice(["print(sorted(swapped.items()))", "print(len(swapped))", "print(sorted(swapped.values()))"])]
            notes.append("字典推导式可以交换键和值；相同新键会覆盖")
        else:
            lines += ["keys = list(data.keys())", "values = list(data.values())"]
            if rng.random() < 0.5:
                lines += ["pairs = list(zip(keys, values))", "print(pairs[-1], len(pairs))"]
            else:
                lines += ["rebuilt = dict(zip(keys, values))", "print(rebuilt == data, len(rebuilt))"]
            notes.append("`keys`、`values` 与 `items` 提供字典的不同视图")
    else:
        left, right = set(_list_values(rng, 4)), set(_list_values(rng, 4))
        lines = [f"left = {left!r}", f"right = {right!r}"]
        if pattern == 4:
            operations = rng.sample(["left | right", "left & right", "left - right", "left ^ right"], rng.randint(2, 4))
            lines.append(f"print({', '.join(f'sorted({op})' for op in operations)})")
            notes.append("集合支持并集、交集、差集和对称差集")
        elif pattern == 5:
            for _ in range(rng.randint(2, 5)):
                operation = rng.choice(["add", "discard", "update", "intersection_update"])
                argument = str(rng.randint(1, 12)) if operation in {"add", "discard"} else repr(set(_list_values(rng, 2)))
                lines.append(f"left.{operation}({argument})")
                notes.append(f"`{operation}` 原地修改集合")
            lines.append("print(sorted(left), len(left))")
        else:
            checks = rng.sample(["left <= right", "left < right", "left.isdisjoint(right)", "left == right", "len(left | right)"], rng.randint(2, 5))
            lines.append(f"print({', '.join(checks)})")
            notes.append("集合比较可判断子集、相等和互不相交关系")
    return Draft("\n".join(lines), "；".join(dict.fromkeys(notes)))


def _condition(rng: Random, depth: int) -> str:
    if depth <= 0 or rng.random() < 0.45:
        left = rng.choice(["x", "y", "x + y", "x - y", "x % 2", "y % 3"])
        right = rng.choice(["0", "2", "5", "x", "y"])
        return f"{left} {rng.choice(['<', '<=', '>', '>=', '==', '!='])} {right}"
    left, right = _condition(rng, depth - 1), _condition(rng, depth - 1)
    combined = f"({left}) {rng.choice(['and', 'or'])} ({right})"
    return f"not ({combined})" if rng.random() < 0.3 else combined


def _stage_7(attempt: int) -> Draft:
    rng = Random(707_000_033 + attempt)
    x, y = rng.randint(-5, 15), rng.randint(-5, 15)
    first, second, pattern = _condition(rng, rng.randint(1, 3)), _condition(rng, rng.randint(1, 3)), rng.randrange(6)
    lines = [f"x, y = {x}, {y}"]
    if pattern == 0:
        lines += [f"if {first}:", "    print('A')", "else:", "    print('B')"]
        analysis = "`if` 只执行条件为真对应的分支，否则执行 `else`"
    elif pattern == 1:
        lines += [f"if {first}:", "    print('A')", f"elif {second}:", "    print('B')", "else:", "    print('C')"]
        analysis = "`if/elif/else` 从上到下检查，只执行第一个满足的分支"
    elif pattern == 2:
        lines += [f"if {first}:", f"    if {second}:", "        print('AB')", "    else:", "        print('A')", "else:", "    print('N')"]
        analysis = "外层分支进入后才会继续判断嵌套的内层条件"
    elif pattern == 3:
        lines += [f"label = 'yes' if {first} else 'no'", "print(label)"]
        analysis = "条件表达式为真时取 `if` 前的值，否则取 `else` 后的值"
    elif pattern == 4:
        allowed = rng.sample(range(-3, 12), rng.randint(3, 6))
        lines += [f"allowed = {allowed!r}", "if x in allowed and y not in allowed:", "    print('only x')", "elif y in allowed:", "    print('has y')", "else:", "    print('neither')"]
        analysis = "`in` 与 `not in` 先做成员判断，再由分支决定输出"
    else:
        lines += ["result = ''", f"if {first}:", "    result += 'X'", f"if {second}:", "    result += 'Y'", "if not result:", "    result = 'none'", "print(result)"]
        analysis = "连续多个 `if` 分别判断，因此可能有不止一个分支执行"
    return Draft("\n".join(lines), analysis)


def _stage_8(attempt: int) -> Draft:
    rng = Random(808_000_039 + attempt)
    pattern, limit = rng.randrange(8), rng.randint(4, 10)
    if pattern == 0:
        operations = [
            rng.choice([
                "total += number", "total += number * number", "total -= number",
                "total = total * 2 + number", "total += number % 3",
                "total = max(total, number)",
            ])
            for _ in range(rng.randint(1, 5))
        ]
        body = "\n".join(f"    {operation}" for operation in operations)
        code = f"total = 0\nfor number in range({rng.randint(0, 3)}, {limit}, {rng.randint(1, 3)}):\n{body}\nprint(total)"
        analysis = "`range` 不包含终点，循环依次用每个数更新累计值"
    elif pattern == 1:
        update = rng.choice(["value += step", "value *= 2", "value += value % 3 + 1"])
        start = rng.randint(1, 3) if update == "value *= 2" else rng.randint(0, 3)
        observations = [
            rng.choice([
                "total += value", "total += value * value", "total -= value",
                "total += value % 2", "total = max(total, value)",
            ])
            for _ in range(rng.randint(1, 4))
        ]
        observed_body = "\n".join(f"    {operation}" for operation in observations)
        code = f"value = {start}\ncount = 0\ntotal = 0\nwhile value < {limit}:\n    step = {rng.randint(1, 3)}\n{observed_body}\n    {update}\n    count += 1\nprint(value, count, total)"
        analysis = "`while` 每轮开始前检查条件，直到条件变为假"
    elif pattern == 2:
        code = f"result = []\nfor number in range({limit + 4}):\n    if number % {rng.randint(2, 4)} == 0:\n        continue\n    if number >= {rng.randint(5, limit + 3)}:\n        break\n    result.append(number)\nprint(result)"
        analysis = "`continue` 跳过本轮，`break` 立即结束整个循环"
    elif pattern == 3:
        body = rng.choice(["total += row + col", "total += row * col", "total += 1", "total += (row == col)"])
        code = f"total = 0\nfor row in range({rng.randint(2, 4)}):\n    for col in range({rng.randint(2, 5)}):\n        {body}\nprint(total)"
        analysis = "内层循环会针对外层的每个值完整执行"
    elif pattern == 4:
        operation = rng.choice(["index + value", "index * value", "(index, value)"])
        code = f"items = {_list_values(rng, rng.randint(3, 6))!r}\nresult = []\nfor index, value in enumerate(items):\n    result.append({operation})\nprint(result)"
        analysis = "`enumerate` 在遍历值的同时提供从 0 开始的索引"
    elif pattern == 5:
        operation = rng.choice(["a + b", "a - b", "max(a, b)"])
        code = f"left = {_list_values(rng, 4)!r}\nright = {_list_values(rng, 4)!r}\nresult = []\nfor a, b in zip(left, right):\n    result.append({operation})\nprint(result)"
        analysis = "`zip` 把多个序列相同位置的元素配成一组"
    elif pattern == 6:
        code = f"for number in range(1, {limit + 1}):\n    if number == {rng.randint(2, limit)}:\n        print('found', number)\n        break\nelse:\n    print('missing')"
        analysis = "循环由 `break` 退出时，不执行循环的 `else`"
    else:
        code = f"text = {rng.choice(['python', 'banana', 'code', 'loop'])!r}\ncounts = {{}}\nfor char in text:\n    counts[char] = counts.get(char, 0) + 1\nprint(sorted(counts.items()))"
        analysis = "循环逐个读取字符，用 `get` 默认值累计出现次数"
    return Draft(code, analysis)


def _function_expression(rng: Random, names: list[str], depth: int) -> str:
    if depth <= 0 or rng.random() < 0.3:
        return rng.choice([*names, str(rng.randint(1, 6))])
    left = _function_expression(rng, names, depth - 1)
    op = rng.choice(["+", "-", "*", "//", "%"])
    right = str(rng.randint(1, 5)) if op in {"//", "%"} else _function_expression(rng, names, max(0, depth - 2))
    return f"({left} {op} {right})"


def _stage_9(attempt: int) -> Draft:
    rng = Random(909_000_041 + attempt)
    pattern = rng.randrange(8)
    a, b, c = [rng.randint(2, 9) for _ in range(3)]
    if pattern == 0:
        params = ["x", "y", "z"][: rng.randint(1, 3)]
        expr = _function_expression(rng, params, rng.randint(1, 4))
        args = [str(value) for value in [a, b, c][: len(params)]]
        code, analysis = f"def calculate({', '.join(params)}):\n    return {expr}\n\nprint(calculate({', '.join(args)}))", "实参按位置绑定到形参，`return` 把结果交回调用处"
    elif pattern == 1:
        expr = _function_expression(rng, ["value", "step"], rng.randint(1, 3))
        code, analysis = f"def change(value, step={b}):\n    return {expr}\n\nprint(change({a}), change({a}, {c}))", "省略第二个实参时用默认值，显式提供时覆盖默认值"
    elif pattern == 2:
        code, analysis = f"def combine(x, y):\n    return {rng.choice(['x - y', 'x + y * 2', 'x * y', 'x // y'])}\n\nprint(combine(y={b}, x={a}))", "关键字参数按名称绑定，与书写顺序无关"
    elif pattern == 3:
        args = ", ".join(map(str, [a, b, c, rng.randint(1, 9)][: rng.randint(2, 4)]))
        code, analysis = f"def summarize(*numbers):\n    return {rng.choice(['sum(numbers)', 'max(numbers)', 'min(numbers)', 'sum(numbers) / len(numbers)'])}\n\nprint(summarize({args}))", "带星号的形参把位置参数收集成元组"
    elif pattern == 4:
        code, analysis = f"base = {a}\ndef outer(value):\n    offset = {b}\n    def inner(step):\n        return value + offset + step\n    return inner\n\nfunction = outer(base)\nprint(function({c}))", "内部函数会记住定义时外层作用域的变量"
    elif pattern == 5:
        code, analysis = f"transform = lambda x: {rng.choice(['x * 2 + 1', 'x % 3', '-x', 'x * x'])}\nvalues = {_list_values(rng, 4)!r}\nprint(list(map(transform, values)))", "lambda 创建匿名函数，`map` 依次应用它"
    elif pattern == 6:
        operator = rng.choice(["+", "*"])
        base = "0" if operator == "+" else "1"
        code, analysis = f"def fold(n):\n    if n == 0:\n        return {base}\n    return n {operator} fold(n - 1)\n\nprint(fold({rng.randint(3, 7)}))", "递归把问题缩小到基线条件，再逐层返回"
    else:
        code, analysis = f"def update(items, value):\n    items.append(value)\n    return len(items)\n\nvalues = {_list_values(rng, 3)!r}\nsize = update(values, {rng.randint(10, 20)})\nprint(size, values[-1])", "列表可变，函数内的 `append` 会影响传入的原列表"
    return Draft(code, analysis)


def _x_condition(rng: Random, depth: int) -> str:
    if depth <= 0 or rng.random() < 0.4:
        return rng.choice([
            f"x % {rng.randint(2, 4)} == 0",
            f"x > {rng.randint(1, 6)}",
            f"x < {rng.randint(4, 10)}",
            f"x != {rng.randint(1, 6)}",
            f"x in {tuple(rng.sample(range(8), 3))!r}",
        ])
    left, right = _x_condition(rng, depth - 1), _x_condition(rng, depth - 1)
    return f"({left}) {rng.choice(['and', 'or'])} ({right})"


def _stage_10(attempt: int) -> Draft:
    rng = Random(1_010_000_081 + attempt)
    pattern, number = rng.randrange(10), rng.randint(2, 20)
    if pattern == 0:
        else_steps = [rng.choice(["value += 1", "value *= 2", "value -= 3", "value = abs(value)"]) for _ in range(rng.randint(1, 4))]
        else_body = "\n".join(f"    {step}" for step in else_steps)
        code, analysis = f"try:\n    value = {number} // {rng.choice([0, rng.randint(1, 5)])}\nexcept ZeroDivisionError:\n    value = 'zero'\nelse:\n{else_body}\nfinally:\n    print(value)", "`except` 处理异常，`else` 仅在无异常时运行，`finally` 总会运行"
    elif pattern == 1:
        code, analysis = f"raw = {rng.choice([repr(str(number)), repr('python'), repr('3.5')])}\ntry:\n    result = int(raw)\nexcept ValueError:\n    result = len(raw)\nprint(result)", "无法转换为整数时触发 `ValueError` 并进入处理分支"
    elif pattern == 2:
        root, angle = rng.randint(2, 12), rng.choice([0, 30, 90])
        code, analysis = f"import math\nprint(math.isqrt({root * root + number}), round(math.sin(math.radians({angle})), 1))", "`isqrt` 取整数平方根，角度转弧度后计算正弦"
    elif pattern == 3:
        code, analysis = f"import statistics\nvalues = {_list_values(rng, 5)!r}\nprint(statistics.median(values), round(statistics.mean(values), 1))", "`median` 计算中位数，`mean` 计算平均数"
    elif pattern == 4:
        expression = _function_expression(rng, ["x"], rng.randint(1, 4))
        condition = _x_condition(rng, rng.randint(1, 3))
        code, analysis = f"values = {_list_values(rng, 5)!r}\nresult = [{expression} for x in values if {condition}]\nprint(result)", "列表推导式先筛选元素，再计算结果表达式"
    elif pattern == 5:
        changes = [rng.choice(["value += self.step", "value *= 2", "value -= 1", "value //= 2"]) for _ in range(rng.randint(1, 4))]
        change_body = "\n".join(f"        {change}" for change in changes)
        code, analysis = f"class Counter:\n    total = 0\n    def __init__(self, step):\n        self.step = step\n    def add(self, value):\n        Counter.total += self.step\n{change_body}\n        return value\n\nfirst = Counter({rng.randint(1, 4)})\nsecond = Counter({rng.randint(1, 4)})\nprint(first.add({number}), second.add({number}), Counter.total)", "实例属性属于各对象，类属性由所有实例共享"
    elif pattern == 6:
        expression = _function_expression(rng, ["self.value"], rng.randint(1, 4))
        code, analysis = f"class Box:\n    def __init__(self, value):\n        self.value = value\n    def calculate(self):\n        return {expression}\n\nbox = Box({number})\nbox.value += {rng.randint(1, 5)}\nprint(box.calculate())", "构造方法保存实例属性，实例方法通过 `self` 读取它"
    elif pattern == 7:
        operations = [rng.choice(["result += 1", "result *= 2", "result -= 3", "result //= 2"]) for _ in range(rng.randint(1, 4))]
        operation_body = "\n".join(f"        {operation}" for operation in operations)
        code, analysis = f"class Parent:\n    def value(self):\n        return {number}\n\nclass Child(Parent):\n    def value(self):\n        result = super().value()\n{operation_body}\n        return result\n\nprint(Child().value())", "子类重写方法，并用 `super()` 调用父类实现"
    elif pattern == 8:
        expression = _function_expression(rng, ["x"], rng.randint(1, 4))
        condition = _x_condition(rng, rng.randint(1, 2))
        code, analysis = f"generator = ({expression} for x in range(1, {rng.randint(5, 9)}) if {condition})\nvalues = list(generator)\nprint(values, sum(values))", "生成器按需产生满足条件的值，转为列表后可重复使用结果"
    else:
        code, analysis = f"import json\ndata = {{'name': 'python', 'level': {rng.randint(1, 5)}}}\ntext = json.dumps(data, sort_keys=True)\nrestored = json.loads(text)\nprint(restored['name'], restored['level'])", "`dumps` 序列化，`loads` 把 JSON 文本还原为 Python 数据"
    return Draft(code, analysis)


_PROBES: dict[int, tuple[str, ...]] = {
    1: (
        "print('Py')", "print(2 + 3)", "print('A', 'B')", "print('A', 'B', sep='-')",
        "print('go' * 2)", "print(len('code'))", "print(type(3).__name__)",
        "print('x', end='!')", "print('a\\nb')", "print(True)", "print(7, 8, 9)",
        "print('left', 'right', sep='|', end='.')", "print(3 * 4)", "print('')",
    ),
    2: (
        "print(int('12'))", "print(float(5))", "print(str(8) + 'x')", "print(bool(0))",
        "print(bool(''))", "print(type(2.0).__name__)", "print(isinstance(True, int))",
        "print(int(4.9))", "print(float('3.5'))", "print(type(None).__name__)",
        "print(str(False).lower())", "print(bool([0]))", "print(int(True))", "print(type([]).__name__)",
    ),
    3: (
        "print(17 // 5)", "print(17 % 5)", "print(2 ** 4)", "print(abs(-7))",
        "print(min(4, 9))", "print(max(4, 9))", "print(round(3.6))", "print(2 < 5 < 8)",
        "print(True and False)", "print(True or False)", "print(not 3 == 4)",
        "print(divmod(19, 4))", "print((2 + 3) * 4)", "print(10 - 3 * 2)",
    ),
    4: (
        "print('python'.upper())", "print('PY'.lower())", "print(' banana '.strip())",
        "print('banana'.count('a'))", "print('code'.replace('c', 'n'))", "print('abc'[::-1])",
        "print('-'.join(['a', 'b']))", "print('a,b,c'.split(','))", "print('python'.startswith('py'))",
        "print('python'.endswith('on'))", "print('banana'.find('na'))", "print('hello'.capitalize())",
        "print('two words'.title())", "print('AbC'.swapcase())",
    ),
    5: (
        "print([1, 2] + [3])", "print([1, 2] * 2)", "print(len((1, 2, 3)))",
        "print([3, 1, 2][::-1])", "print(sorted([3, 1, 2]))", "print(2 in [1, 2, 3])",
        "print([1, 2, 1].count(1))", "print((4, 5)[-1])", "print(list((1, 2)))",
        "print(tuple([3, 4]))", "print(sum([1, 2, 3]))", "print(min([4, 2, 7]))",
        "print(max((4, 2, 7)))", "print([[1], [2]][1][0])",
    ),
    6: (
        "print({'a': 1}.get('b', 0))", "print('a' in {'a': 1})", "print(len({'a': 1, 'b': 2}))",
        "print(sorted({3, 1, 2}))", "print(sorted({1, 2} | {2, 3}))", "print(sorted({1, 2} & {2, 3}))",
        "print(sorted({1, 2} - {2, 3}))", "print({1, 2} <= {1, 2, 3})", "print(set([1, 1, 2]))",
        "print(dict([('a', 1)]))", "print(sorted({'b': 2, 'a': 1}))", "print(sum({'a': 2}.values()))",
        "print({1, 2}.isdisjoint({3}))", "print(len({1, 1, 2}))",
    ),
    7: (
        "print('yes' if 3 > 2 else 'no')", "print(bool([]))", "print(bool([0]))",
        "print(2 in [1, 2, 3])", "print(4 not in {1, 2})", "print(3 > 1 and 2 < 5)",
        "print(3 < 1 or 2 < 5)", "print(not '')", "print(0 < 3 <= 5)", "print(None is None)",
        "print('x' if 0 else 'y')", "print(all([True, True]))", "print(any([False, True]))",
        "print(5 % 2 == 0)",
    ),
    8: (
        "print(sum(range(4)))", "print(list(range(1, 6, 2)))", "print(len(range(5)))",
        "print(list(enumerate(['a', 'b'])))", "print(list(zip([1, 2], ['a', 'b'])))",
        "print([x * 2 for x in range(3)])", "print([x for x in range(5) if x % 2])",
        "print(sum(x * x for x in range(3)))", "print(list(reversed(range(4))))",
        "print(max(range(2, 7)))", "print(min(range(-2, 3)))", "print(any(x > 3 for x in range(5)))",
        "print(all(x < 5 for x in range(5)))", "print(dict(enumerate('ab')))",
    ),
    9: (
        "print((lambda x: x + 1)(4))", "print((lambda x, y: x * y)(3, 4))",
        "print(list(map(str, [1, 2])))", "print(list(filter(bool, [0, 1, 2])))",
        "print(sum([1, 2, 3]))", "print(max(2, 8, 5))", "print(min(2, 8, 5))",
        "print(callable(lambda: None))", "print(list(map(lambda x: x * 2, [1, 2])))",
        "print(any(map(bool, [0, 2])))", "print(all(map(bool, [1, 2])))",
        "print((lambda x: x if x > 0 else -x)(-3))", "print(sorted([3, 1], key=lambda x: -x))",
        "print(tuple(map(len, ['a', 'bb'])))",
    ),
    10: (
        "print([x * x for x in range(3)])", "print({x: x + 1 for x in range(2)})",
        "print({x % 2 for x in range(4)})", "print(sum(x for x in range(4)))",
        "print(next(iter([5, 6])))", "print(isinstance(3, int))", "print(hasattr('a', 'upper'))",
        "print(callable(str.upper))", "print(type(ValueError()).__name__)",
        "print(list(map(lambda x: x + 1, [1, 2])))", "print(list(filter(lambda x: x > 1, [1, 2, 3])))",
        "print(any(x == 2 for x in range(4)))", "print(all(x < 4 for x in range(4)))",
        "print(tuple(reversed([1, 2, 3])))",
    ),
}


def _add_learning_probes(stage: int, draft: Draft, attempt: int) -> Draft:
    """加入同阶段的第二个微任务，使整道题的知识组合也保持独立。"""
    rng = Random(stage * 90_000_019 + attempt)
    probes = [rng.choice(_PROBES[stage]) for _ in range(rng.randint(1, 3))]
    return Draft(
        code=f"{draft.code}\n{chr(10).join(probes)}",
        analysis=f"{draft.analysis}；随后按顺序计算同阶段的复习表达式",
        prompt=draft.prompt,
        distractors=draft.distractors,
    )


BUILDERS: dict[int, Callable[[int], Draft]] = {
    1: _stage_1, 2: _stage_2, 3: _stage_3, 4: _stage_4, 5: _stage_5,
    6: _stage_6, 7: _stage_7, 8: _stage_8, 9: _stage_9, 10: _stage_10,
}


def generate_question_bank_with_metadata() -> list[GeneratedQuestion]:
    """生成 10,000 道题，并拒绝仅常量或变量名不同的重复结构。"""
    generated: list[GeneratedQuestion] = []
    titles: set[str] = set()
    all_fingerprints: set[str] = set()
    for stage, builder in BUILDERS.items():
        accepted = attempt = 0
        max_attempts = QUESTIONS_PER_STAGE * 30
        while accepted < QUESTIONS_PER_STAGE and attempt < max_attempts:
            try:
                draft = builder(attempt)
                fingerprint = structure_fingerprint(draft.code)
                if fingerprint in all_fingerprints:
                    attempt += 1
                    continue
                data = _make_question(stage, draft, fingerprint, _question_type(accepted))
                if data["title"] in titles:
                    attempt += 1
                    continue
            except (ArithmeticError, IndexError, KeyError, TypeError, ValueError):
                attempt += 1
                continue
            all_fingerprints.add(fingerprint)
            titles.add(data["title"])
            generated.append(GeneratedQuestion(data, stage, fingerprint))
            accepted += 1
            attempt += 1
        if accepted != QUESTIONS_PER_STAGE:
            raise RuntimeError(f"阶段 {stage} 只生成 {accepted} 道结构独立题，已尝试 {attempt} 个候选")
    if len(generated) != TOTAL_QUESTIONS:
        raise RuntimeError("生成题数不符合预期")
    return generated


def generate_question_bank() -> list[dict[str, str | None]]:
    questions = [item.data for item in generate_question_bank_with_metadata()]
    if any(question["answer"] not in LETTERS for question in questions):
        raise RuntimeError("题库中存在非法答案")
    return questions
