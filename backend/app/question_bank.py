"""按 Python 新手学习路线生成 10,000 道原创四选一练习题。

题目由确定性模板生成：同一版本每次生成的题干、选项、答案都一致，
便于测试、审计和部署。每个阶段包含多种题型与大量参数变体。
"""

from collections.abc import Callable
from random import Random
from typing import Any


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
LETTERS = "ABCD"


def _code(source: str) -> str:
    return f"```python\n{source}\n```"


def _display(value: Any) -> str:
    """得到与 print 输出一致的简洁文本。"""
    if value is None:
        return "None"
    return str(value)


def _question(
    stage: int,
    index: int,
    stem: str,
    correct: Any,
    distractors: list[Any],
    analysis: str,
) -> dict[str, str]:
    """创建题目并稳定地打乱选项位置。"""
    correct_text = _display(correct)
    choices = [correct_text]
    for item in distractors:
        text = _display(item)
        if text not in choices:
            choices.append(text)

    fallbacks = ["程序报错", "None", "True", "False", "0", "空字符串"]
    for item in fallbacks:
        if len(choices) == 4:
            break
        if item not in choices:
            choices.append(item)

    if len(choices) != 4:
        raise ValueError(f"题目选项无法补足四项：stage={stage}, index={index}")

    rng = Random(stage * 100_000 + index)
    rng.shuffle(choices)
    answer = LETTERS[choices.index(correct_text)]
    prefix = f"【阶段 {stage}：{STAGES[stage]}】练习 {index + 1:04d}"
    return {
        "title": f"{prefix}\n\n{stem}",
        "option_a": choices[0],
        "option_b": choices[1],
        "option_c": choices[2],
        "option_d": choices[3],
        "answer": answer,
        "analysis": analysis,
    }


def _stage_1(i: int) -> dict[str, str]:
    """阶段 1：print、注释、基础字面量与简单输出。"""
    kind = i % 6
    a, b = i + 2, (i * 3) % 17 + 1
    if kind == 0:
        return _question(1, i, f"下面代码输出什么？\n\n{_code(f'print({a} + {b})')}", a + b, [a, b, a - b], f"`+` 对两个整数执行加法，{a} + {b} = {a + b}。")
    if kind == 1:
        return _question(1, i, f"下面代码输出什么？\n\n{_code(f'print({a}, {b}, sep=\"-\")')}", f"{a}-{b}", [f"{a} {b}", f"{a}{b}", f"{a}, {b}"], "`sep` 指定 print 输出多个值时使用的分隔符，这里分隔符是连字符。")
    if kind == 2:
        source = f"print({a})\n# print({b})"
        return _question(1, i, f"下面代码输出什么？\n\n{_code(source)}", a, [b, f"{a}\n{b}", a + b], "以 `#` 开头的是注释，不会被 Python 执行，所以只有第一行产生输出。")
    if kind == 3:
        source = f"value = {a}\nprint(type(value).__name__)"
        return _question(1, i, f"下面代码输出什么？\n\n{_code(source)}", "int", ["float", "str", "number"], "没有小数点的整数字面量属于 `int` 类型，`__name__` 得到类型名称。")
    if kind == 4:
        return _question(1, i, f"下面代码输出什么？\n\n{_code('print(\"Py\", end=\"\")\nprint(\"thon\")')}", "Python", ["Py thon", "Py\nthon", "thonPy"], "第一条 print 的 `end` 被设为空字符串，因此第二次输出会紧接在 `Py` 后面。")
    times = i % 4 + 2
    return _question(1, i, f"下面代码输出什么？\n\n{_code(f'print(\"Hi\" * {times})')}", "Hi" * times, [f"Hi{times}", "Hi", "Hi " * times], "字符串乘以正整数会把字符串重复指定次数。")


def _stage_2(i: int) -> dict[str, str]:
    """阶段 2：赋值、类型转换、布尔值与变量行为。"""
    kind = i % 7
    a, b = i + 5, i % 13 + 2
    if kind == 0:
        source = f"x = {a}\nx += {b}\nprint(x)"
        return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", a + b, [a, b, a * b], f"`x += {b}` 等价于 `x = x + {b}`，所以结果是 {a + b}。")
    if kind == 1:
        source = f"x, y = {a}, {b}\nx, y = y, x\nprint(x, y)"
        return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", f"{b} {a}", [f"{a} {b}", f"{a} {a}", f"{b} {b}"], "`x, y = y, x` 利用多重赋值交换两个变量的值。")
    if kind == 2:
        source = f'text = "{a}"\nprint(int(text) + {b})'
        return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", a + b, [f"{a}{b}", a, b], "`int()` 先把只包含数字的字符串转换为整数，然后执行数值加法。")
    if kind == 3:
        source = f"value = float({a})\nprint(type(value).__name__)"
        return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", "float", ["int", "str", "number"], "`float()` 返回浮点数，因此类型名称为 `float`。")
    if kind == 4:
        value = 0 if (i // 7) % 2 == 0 else a
        return _question(2, i, f"表达式 `bool({value})` 的结果是什么？", bool(value), [not bool(value), value, "None"], "数字 0 是假值，非零数字是真值。")
    if kind == 5:
        source = f"a = b = {a}\nb += {b}\nprint(a, b)"
        return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", f"{a} {a + b}", [f"{a + b} {a + b}", f"{a} {b}", f"{b} {a}"], "整数是不可变对象；`b +=` 让 b 指向新整数，不会改变 a 的值。")
    source = f"value = {a / 10}\nprint(int(value))"
    return _question(2, i, f"下面代码输出什么？\n\n{_code(source)}", int(a / 10), [round(a / 10), a / 10, a], "`int()` 把正浮点数转换为整数时会去掉小数部分。")


def _stage_3(i: int) -> dict[str, str]:
    """阶段 3：算术、比较和逻辑运算。"""
    kind = i % 8
    a, b, c = i % 80 + 10, i % 7 + 2, i % 5 + 2
    if kind == 0:
        value = a + b * c
        return _question(3, i, f"表达式 `{a} + {b} * {c}` 的值是？", value, [(a + b) * c, a + b + c, a * b + c], "乘法的优先级高于加法，所以先计算乘法。")
    if kind == 1:
        source = f"print({a} // {b}, {a} % {b})"
        return _question(3, i, f"下面代码输出什么？\n\n{_code(source)}", f"{a // b} {a % b}", [f"{a / b} 0", f"{a % b} {a // b}", f"{a // b} {b}"], "`//` 得到整除商，`%` 得到余数。")
    if kind == 2:
        return _question(3, i, f"表达式 `{b} ** {c}` 的值是？", b**c, [b * c, b + c, c**b], "`**` 是幂运算符，表示底数的指定次方。")
    if kind == 3:
        left, middle, right = b, b + c, b + c + 1
        return _question(3, i, f"表达式 `{left} < {middle} < {right}` 的结果是？", True, [False, middle, "None"], "Python 支持链式比较；这里两个小于关系都成立。")
    if kind == 4:
        x, y = i % 2 == 0, i % 3 == 0
        return _question(3, i, f"表达式 `{x} and {y}` 的结果是？", x and y, [not (x and y), x, "None"], "`and` 只有在两边都为真时才得到 `True`。")
    if kind == 5:
        x, y = i % 2 == 0, i % 5 == 0
        return _question(3, i, f"表达式 `{x} or {y}` 的结果是？", x or y, [not (x or y), x and y, "None"], "`or` 只要任一条件为真就得到 `True`。")
    if kind == 6:
        result = not (a > b)
        return _question(3, i, f"表达式 `not ({a} > {b})` 的结果是？", result, [not result, a - b, "None"], "先计算括号内的比较，再由 `not` 对布尔结果取反。")
    value = (a - b) / c
    return _question(3, i, f"表达式 `({a} - {b}) / {c}` 的值是？", value, [a - b / c, (a - b) // c, a - b - c], "括号先计算，`/` 在 Python 3 中返回浮点数。")


def _stage_4(i: int) -> dict[str, str]:
    """阶段 4：字符串索引、切片和常用方法。"""
    kind = i % 10
    word = f"python{i}"
    if i == 0:
        source = 's = "Python is fun"\nprint(s.replace("fun", "powerful"))'
        return _question(4, i, f"下面这道 `s.replace` 题输出什么？\n\n{_code(source)}", "Python is powerful", ["Python is fun", "fun", "程序报错"], "`str.replace(old, new)` 返回替换后的新字符串，所以输出 `Python is powerful`；原字符串本身不会被修改。")
    if kind == 0:
        old, new = str(i % 10), "X"
        source = f's = "item-{i}"\nprint(s.replace("{old}", "{new}"))'
        correct = f"item-{i}".replace(old, new)
        return _question(4, i, f"下面代码输出什么？\n\n{_code(source)}", correct, [f"item-{i}", new, "None"], "`replace()` 返回把目标子串全部替换后的新字符串。")
    if kind == 1:
        return _question(4, i, f"表达式 `\"{word}\".upper()` 的结果是？", word.upper(), [word, word.capitalize(), word.lower()], "`upper()` 返回所有字母均转为大写的新字符串。")
    if kind == 2:
        text = f"PyThOn{i}"
        return _question(4, i, f"表达式 `\"{text}\".lower()` 的结果是？", text.lower(), [text, text.upper(), text.capitalize()], "`lower()` 返回所有字母均转为小写的新字符串。")
    if kind == 3:
        start = i % 3
        stop = start + 3
        correct = word[start:stop]
        return _question(4, i, f"表达式 `\"{word}\"[{start}:{stop}]` 的结果是？", correct, [word[start : stop + 1], word[start + 1 : stop], word[:stop]], "字符串切片包含起始索引，不包含结束索引。")
    if kind == 4:
        return _question(4, i, f"表达式 `\"{word}\"[-1]` 的结果是？", word[-1], [word[0], word[1], word[-2]], "索引 `-1` 表示字符串的最后一个字符。")
    if kind == 5:
        text = f"  python-{i}  "
        return _question(4, i, f"表达式 `{text!r}.strip()` 的结果是？", f"python-{i}", [text, f" python-{i} ", f"python{i}"], "`strip()` 去掉字符串两端的空白，不改变中间内容。")
    if kind == 6:
        text = f"a,b,c,{i}"
        return _question(4, i, f"表达式 `len(\"{text}\".split(\",\"))` 的结果是？", 4, [3, 5, len(text)], "`split(',')` 按逗号分成 4 个字符串，所以列表长度为 4。")
    if kind == 7:
        sep = "-" if i % 2 else "/"
        parts = ["py", "thon", str(i)]
        correct = sep.join(parts)
        source = f'print("{sep}".join(["py", "thon", "{i}"]))'
        return _question(4, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["".join(parts), " ".join(parts), str(parts)], "`join()` 使用调用它的字符串作为分隔符连接序列中的文本。")
    if kind == 8:
        name, score = f"user{i}", i % 101
        source = f'name = "{name}"\nscore = {score}\nprint(f"{{name}}:{{score}}")'
        return _question(4, i, f"下面代码输出什么？\n\n{_code(source)}", f"{name}:{score}", ["{name}:{score}", f"{name} {score}", f"name:{score}"], "f-string 会把花括号中的变量替换为当前值。")
    text = "banana" + ("a" * (i % 4))
    return _question(4, i, f"表达式 `\"{text}\".count(\"a\")` 的值是？", text.count("a"), [text.count("a") - 1, text.count("a") + 1, len(text)], "`count()` 返回指定子串在字符串中出现的次数。")


def _stage_5(i: int) -> dict[str, str]:
    """阶段 5：列表操作、切片与元组。"""
    kind = i % 10
    a, b, c = i + 1, i + 2, i + 3
    if kind == 0:
        source = f"items = [{a}, {b}]\nitems.append({c})\nprint(items)"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", [a, b, c], [[a, b], [c, a, b], None], "`append()` 把一个元素添加到列表末尾，并原地修改列表。")
    if kind == 1:
        source = f"items = [{a}]\nitems.extend([{b}, {c}])\nprint(len(items))"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", 3, [1, 2, 4], "`extend()` 把可迭代对象中的每个元素追加到列表，因此列表共有 3 个元素。")
    if kind == 2:
        source = f"items = [{a}, {c}]\nitems.insert(1, {b})\nprint(items)"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", [a, b, c], [[b, a, c], [a, c, b], [a, c]], "`insert(1, value)` 会在索引 1 的位置插入元素。")
    if kind == 3:
        source = f"items = [{a}, {b}, {c}]\nvalue = items.pop()\nprint(value, len(items))"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", f"{c} 2", [f"{a} 2", f"{c} 3", str([a, b])], "不传索引时，`pop()` 删除并返回最后一个元素；剩余列表长度为 2。")
    if kind == 4:
        values = [a, b, c, c + 1, c + 2]
        return _question(5, i, f"表达式 `{values}[1:4]` 的结果是？", values[1:4], [values[:4], values[1:], values[2:4]], "列表切片和字符串切片一样，包含开始索引，不包含结束索引。")
    if kind == 5:
        values = [a, b, a, c, a]
        return _question(5, i, f"表达式 `{values}.count({a})` 的值是？", 3, [1, 2, 5], "`list.count()` 统计指定元素出现的次数。")
    if kind == 6:
        values = [c, a, b]
        source = f"items = {values}\nresult = sorted(items)\nprint(result)"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", sorted(values), [values, list(reversed(values)), None], "`sorted()` 返回一个新的升序列表。")
    if kind == 7:
        source = f"point = ({a}, {b})\nx, y = point\nprint(y, x)"
        return _question(5, i, f"下面代码输出什么？\n\n{_code(source)}", f"{b} {a}", [f"{a} {b}", f"{a} {a}", str((a, b))], "元组可以解包给多个变量；这里输出顺序是 y 后 x。")
    if kind == 8:
        values = [a, b, c]
        target = b if i % 2 else c + 5
        return _question(5, i, f"表达式 `{target} in {values}` 的结果是？", target in values, [target not in values, target, "None"], "`in` 用于判断元素是否存在于列表中，结果是布尔值。")
    nested = [[a, b], [c, c + 1]]
    return _question(5, i, f"表达式 `{nested}[1][0]` 的值是？", c, [a, b, c + 1], "先取外层列表索引 1 的子列表，再取该子列表索引 0 的元素。")


def _stage_6(i: int) -> dict[str, str]:
    """阶段 6：字典与集合常用操作。"""
    kind = i % 10
    a, b, c = i % 50 + 1, i % 50 + 2, i % 50 + 3
    if kind == 0:
        source = f'data = {{"score": {a}}}\nprint(data.get("age", {b}))'
        return _question(6, i, f"下面代码输出什么？\n\n{_code(source)}", b, [a, "None", "KeyError"], "键不存在时，`dict.get()` 返回第二个参数给出的默认值。")
    if kind == 1:
        source = f'data = {{"x": {a}}}\ndata["x"] = {b}\nprint(data["x"])'
        return _question(6, i, f"下面代码输出什么？\n\n{_code(source)}", b, [a, c, "KeyError"], "给已有键赋值会更新这个键对应的值。")
    if kind == 2:
        data = {"a": a, "b": b, "c": c}
        return _question(6, i, f"表达式 `len({data})` 的值是？", 3, [2, 4, a + b + c], "`len()` 返回字典中的键值对数量。")
    if kind == 3:
        source = f'data = {{"a": {a}, "b": {b}}}\nvalue = data.pop("a")\nprint(value, len(data))'
        return _question(6, i, f"下面代码输出什么？\n\n{_code(source)}", f"{a} 1", [f"{b} 1", f"{a} 2", "KeyError"], "`pop('a')` 删除键 a 并返回它原来的值，字典随后只剩一个键。")
    if kind == 4:
        values = [a, a, b, c, b]
        return _question(6, i, f"表达式 `len(set({values}))` 的值是？", 3, [2, 4, 5], "集合不保留重复元素，这里只有 3 个不同的值。")
    if kind == 5:
        left, right = {a, b}, {b, c}
        return _question(6, i, f"集合 `{left} | {right}` 的元素个数是？", len(left | right), [1, 2, 4], "`|` 计算并集，合并两边所有不重复的元素。")
    if kind == 6:
        left, right = {a, b}, {b, c}
        return _question(6, i, f"集合 `{left} & {right}` 的结果是？", {b}, [set(), left | right, {a, c}], "`&` 计算交集，只保留两个集合共同拥有的元素。")
    if kind == 7:
        left, right = {a, b, c}, {b, c}
        return _question(6, i, f"集合 `{left} - {right}` 的结果是？", {a}, [{b, c}, set(), left], "集合差集保留左侧集合中存在、右侧集合中不存在的元素。")
    if kind == 8:
        source = f"values = {{{a}, {b}}}\nvalues.add({a})\nprint(len(values))"
        return _question(6, i, f"下面代码输出什么？\n\n{_code(source)}", 2, [1, 3, 4], "向集合加入已经存在的元素不会产生重复项，所以长度不变。")
    source = f'keys = ["a", "b", "c"]\ndata = {{key: len(key) + {i % 5} for key in keys}}\nprint(data["b"])'
    correct = 1 + i % 5
    return _question(6, i, f"下面代码输出什么？\n\n{_code(source)}", correct, [correct - 1, correct + 1, 3], "字典推导式为每个键计算值；单字符键的长度为 1。")


def _stage_7(i: int) -> dict[str, str]:
    """阶段 7：if/elif/else 与条件表达式。"""
    kind = i % 8
    n = i % 101
    if kind == 0:
        source = f"n = {n}\nif n >= 60:\n    print(\"通过\")\nelse:\n    print(\"继续练习\")"
        correct = "通过" if n >= 60 else "继续练习"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["通过" if correct != "通过" else "继续练习", n, "无输出"], "程序根据 `n >= 60` 的布尔结果，只执行 if 或 else 中的一个分支。")
    if kind == 1:
        score = n
        grade = "A" if score >= 90 else "B" if score >= 60 else "C"
        source = f"score = {score}\nif score >= 90:\n    print(\"A\")\nelif score >= 60:\n    print(\"B\")\nelse:\n    print(\"C\")"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", grade, [x for x in ["A", "B", "C", "D"] if x != grade][:3], "if/elif 从上到下判断，并执行第一个成立的分支。")
    if kind == 2:
        source = f'n = {n}\nprint("偶数" if n % 2 == 0 else "奇数")'
        correct = "偶数" if n % 2 == 0 else "奇数"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["奇数" if correct == "偶数" else "偶数", n % 2, "程序报错"], "条件表达式根据除以 2 的余数选择文本；余数为 0 时是偶数。")
    if kind == 3:
        a, b = n + 3, (n * 7) % 103
        source = f"a, b = {a}, {b}\nresult = a if a > b else b\nprint(result)"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", max(a, b), [min(a, b), a + b, abs(a - b)], "条件表达式在 a 大于 b 时取 a，否则取 b，因此得到较大值。")
    if kind == 4:
        age, has_ticket = n % 30, i % 3 == 0
        allowed = age >= 18 and has_ticket
        source = f"age = {age}\nhas_ticket = {has_ticket}\nprint(age >= 18 and has_ticket)"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", allowed, [not allowed, age >= 18, has_ticket], "`and` 要求年龄条件和持票条件同时为真。")
    if kind == 5:
        color = ["red", "green", "blue", "black"][i % 4]
        source = f'color = "{color}"\nif color in ["red", "blue"]:\n    print("命中")\nelse:\n    print("未命中")'
        correct = "命中" if color in ["red", "blue"] else "未命中"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["未命中" if correct == "命中" else "命中", color, "True"], "`in` 判断 color 是否是列表中的成员，然后选择对应分支。")
    if kind == 6:
        x = n - 50
        label = "正数" if x > 0 else "零" if x == 0 else "负数"
        source = f"x = {x}\nif x > 0:\n    print(\"正数\")\nelif x == 0:\n    print(\"零\")\nelse:\n    print(\"负数\")"
        return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", label, [x for x in ["正数", "零", "负数", str(x)] if x != label][:3], "三个分支依次判断正数、零和负数。")
    values = [] if i % 2 else [n]
    correct = "非空" if values else "空"
    source = f"items = {values}\nif items:\n    print(\"非空\")\nelse:\n    print(\"空\")"
    return _question(7, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["空" if correct == "非空" else "非空", str(len(values)), "程序报错"], "空列表是假值，包含元素的列表是真值。")


def _stage_8(i: int) -> dict[str, str]:
    """阶段 8：for、while、range、break 和 continue。"""
    kind = i % 10
    n = i % 20 + 3
    if kind == 0:
        source = f"total = 0\nfor x in range(1, {n + 1}):\n    total += x\nprint(total)"
        correct = n * (n + 1) // 2
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", correct, [correct - n, correct + n + 1, n], "循环累加 1 到 n；等差数列和为 `n * (n + 1) // 2`。")
    if kind == 1:
        start, stop, step = i % 5, n + 10, i % 3 + 2
        values = list(range(start, stop, step))
        return _question(8, i, f"表达式 `len(list(range({start}, {stop}, {step})))` 的值是？", len(values), [len(values) - 1, len(values) + 1, stop - start], "`range` 从 start 开始按 step 递增，并且不包含 stop。")
    if kind == 2:
        source = f"count = 0\nfor _ in range({n}):\n    count += 1\nprint(count)"
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", n, [n - 1, n + 1, 0], "`range(n)` 产生 n 个值，因此循环体执行 n 次。")
    if kind == 3:
        source = f"x = 0\nwhile x < {n}:\n    x += 2\nprint(x)"
        correct = n if n % 2 == 0 else n + 1
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", correct, [n - 1, n, n + 2], "x 每次增加 2，循环在 x 第一次不小于目标值时停止。")
    if kind == 4:
        stop = n // 2
        source = f"for x in range({n}):\n    if x == {stop}:\n        break\nprint(x)"
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", stop, [stop - 1, stop + 1, n - 1], "当 x 等于指定值时执行 `break`，立即退出循环；x 保留该值。")
    if kind == 5:
        limit = n
        odd_sum = sum(x for x in range(limit) if x % 2 != 0)
        source = f"total = 0\nfor x in range({limit}):\n    if x % 2 == 0:\n        continue\n    total += x\nprint(total)"
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", odd_sum, [sum(range(limit)), sum(x for x in range(limit) if x % 2 == 0), limit], "`continue` 跳过偶数，因此只累加小于上限的奇数。")
    if kind == 6:
        values = [i % 9, i % 9 + 1, i % 9 + 2]
        source = f"items = {values}\nfor index, value in enumerate(items):\n    if index == 1:\n        print(value)"
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", values[1], [values[0], values[2], 1], "`enumerate()` 同时提供索引和值；索引 1 对应第二个元素。")
    if kind == 7:
        rows, cols = i % 4 + 1, i % 3 + 2
        source = f"count = 0\nfor _ in range({rows}):\n    for _ in range({cols}):\n        count += 1\nprint(count)"
        return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", rows * cols, [rows + cols, rows, cols], "内层循环会针对外层的每一次循环完整执行，因此总次数是两者相乘。")
    if kind == 8:
        start, stop = n, n - (i % 5 + 3)
        values = list(range(start, stop, -1))
        return _question(8, i, f"表达式 `list(range({start}, {stop}, -1))` 的最后一个元素是？", values[-1], [stop, start, values[0] - 1], "步长为 -1 时序列递减，但仍不包含 stop。")
    limit = i % 6 + 3
    factorial = 1
    for value in range(1, limit + 1):
        factorial *= value
    source = f"result = 1\nfor x in range(1, {limit + 1}):\n    result *= x\nprint(result)"
    return _question(8, i, f"下面代码输出什么？\n\n{_code(source)}", factorial, [factorial // limit, factorial * (limit + 1), limit * limit], "循环把 1 到目标值依次相乘，计算的是阶乘。")


def _stage_9(i: int) -> dict[str, str]:
    """阶段 9：函数参数、返回值、作用域与 lambda。"""
    kind = i % 9
    a, b = i % 40 + 2, i % 11 + 1
    if kind == 0:
        source = f"def add(x, y):\n    return x + y\n\nprint(add({a}, {b}))"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", a + b, [a, b, a * b], "函数接收两个实参，并通过 `return` 返回它们的和。")
    if kind == 1:
        source = f"def power(x, exponent=2):\n    return x ** exponent\n\nprint(power({b}))"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", b**2, [b * 2, b, 2**b], "调用时未提供 exponent，因此使用默认值 2。")
    if kind == 2:
        source = f"def check(x):\n    if x > 0:\n        return \"正\"\n    return \"非正\"\n\nprint(check({a - 20}))"
        correct = "正" if a - 20 > 0 else "非正"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", correct, ["非正" if correct == "正" else "正", "None", a - 20], "函数执行到 `return` 就结束；根据参数是否大于 0 返回对应文本。")
    if kind == 3:
        source = f"def subtract(x, y):\n    return x - y\n\nprint(subtract(y={b}, x={a}))"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", a - b, [b - a, a + b, a], "关键字参数按名称匹配，不受调用时书写顺序影响。")
    if kind == 4:
        values = [a, b, i % 7]
        source = f"def total(*numbers):\n    return sum(numbers)\n\nprint(total({', '.join(map(str, values))}))"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", sum(values), [len(values), a + b, max(values)], "`*numbers` 把所有位置参数收集成元组，`sum()` 求它们的和。")
    if kind == 5:
        outer, inner = a, a + b
        source = f"x = {outer}\ndef show():\n    x = {inner}\n    return x\n\nprint(show(), x)"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", f"{inner} {outer}", [f"{inner} {inner}", f"{outer} {outer}", f"{outer} {inner}"], "函数内部赋值创建局部变量 x，不会改动函数外部的 x。")
    if kind == 6:
        source = f"double = lambda x: x * 2\nprint(double({a}))"
        return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", a * 2, [a, a + 2, a**2], "lambda 创建了一个接收 x 并返回 `x * 2` 的匿名函数。")
    if kind == 7:
        n = i % 5 + 2
        factorial = 1
        for value in range(1, n + 1):
            factorial *= value
        source = f"def factorial(n):\n    if n == 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial({n}))"
        return _question(9, i, f"下面递归函数输出什么？\n\n{_code(source)}", factorial, [factorial // n, n * n, n], "递归不断计算 `n * factorial(n-1)`，直到 n 等于 1，结果是 n 的阶乘。")
    values = [a, b]
    source = f"def add_item(items):\n    items.append({i % 9})\n\nvalues = {values}\nadd_item(values)\nprint(len(values))"
    return _question(9, i, f"下面代码输出什么？\n\n{_code(source)}", 3, [2, 1, "None"], "列表是可变对象；函数中的 `append()` 会修改传入的原列表。")


def _stage_10(i: int) -> dict[str, str]:
    """阶段 10：异常、标准库、类和综合入门。"""
    kind = i % 10
    n = i % 50 + 1
    if kind == 0:
        source = "try:\n    print(10 / 0)\nexcept ZeroDivisionError:\n    print(\"不能除以零\")"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", "不能除以零", ["0", "10", "程序直接终止且无输出"], "除以零触发 `ZeroDivisionError`，该异常被对应的 except 捕获。")
    if kind == 1:
        source = 'try:\n    int("python")\nexcept ValueError:\n    print("格式错误")'
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", "格式错误", ["python", "0", "TypeError"], "无法把非数字字符串转换成整数，会触发并捕获 `ValueError`。")
    if kind == 2:
        source = f"try:\n    print({n})\nfinally:\n    print(\"结束\")"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", f"{n}\n结束", [str(n), "结束", f"结束\n{n}"], "`finally` 中的代码无论是否发生异常都会执行。")
    if kind == 3:
        root = i % 20 + 2
        value = root * root
        source = f"import math\nprint(math.isqrt({value}))"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", root, [value, root + 1, float(root)], "`math.isqrt()` 返回非负整数平方根的整数部分；这里输入是完全平方数。")
    if kind == 4:
        value = n + (i % 9 + 1) / 10
        import math

        source = f"import math\nprint(math.ceil({value}))"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", math.ceil(value), [int(value), round(value), math.ceil(value) + 1], "`math.ceil()` 向上取整，返回不小于输入值的最小整数。")
    if kind == 5:
        source = f"class User:\n    def __init__(self, age):\n        self.age = age\n\nu = User({n})\nprint(u.age)"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", n, [n + 1, "age", "None"], "创建对象时 `__init__` 把传入的 age 保存为实例属性。")
    if kind == 6:
        source = f"class Counter:\n    def double(self, value):\n        return value * 2\n\nc = Counter()\nprint(c.double({n}))"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", n * 2, [n, n + 2, n**2], "通过实例调用方法时，实参 n 传给 value，方法返回其两倍。")
    if kind == 7:
        mode = ["r", "w", "a"][i % 3]
        meaning = {"r": "读取文件", "w": "写入并覆盖文件", "a": "追加写入文件"}[mode]
        return _question(10, i, f"在 `open(\"data.txt\", \"{mode}\")` 中，模式 `{mode}` 表示什么？", meaning, [x for x in ["读取文件", "写入并覆盖文件", "追加写入文件", "以二进制方式读取"] if x != meaning][:3], "文件模式 `r` 表示读取，`w` 表示写入并覆盖，`a` 表示在末尾追加。")
    if kind == 8:
        limit = i % 10 + 4
        values = [x * 2 for x in range(limit) if x % 2 == 0]
        source = f"values = [x * 2 for x in range({limit}) if x % 2 == 0]\nprint(values)"
        return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", values, [list(range(0, limit, 2)), [x * 2 for x in range(limit)], values[1:]], "列表推导式先筛选 range 中的偶数，再把每个偶数乘以 2。")
    source = f"class Box:\n    count = 0\n    def __init__(self):\n        Box.count += 1\n\nBox()\nBox()\nprint(Box.count)"
    return _question(10, i, f"下面代码输出什么？\n\n{_code(source)}", 2, [0, 1, n], "`count` 是类属性；每创建一个对象，构造方法都会把它加 1。")


BUILDERS: dict[int, Callable[[int], dict[str, str]]] = {
    1: _stage_1,
    2: _stage_2,
    3: _stage_3,
    4: _stage_4,
    5: _stage_5,
    6: _stage_6,
    7: _stage_7,
    8: _stage_8,
    9: _stage_9,
    10: _stage_10,
}


def generate_question_bank() -> list[dict[str, str]]:
    """生成完整题库，并执行基本完整性检查。"""
    questions = [
        BUILDERS[stage](index)
        for stage in STAGES
        for index in range(QUESTIONS_PER_STAGE)
    ]
    if len(questions) != TOTAL_QUESTIONS:
        raise RuntimeError("生成的题目数量不符合预期")
    if any(question["answer"] not in LETTERS for question in questions):
        raise RuntimeError("题库中存在非法答案")
    if len({question["title"] for question in questions}) != TOTAL_QUESTIONS:
        raise RuntimeError("题库中存在重复题干")
    return questions

