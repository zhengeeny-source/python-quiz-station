"""严格审计 10,000 道题的结构、答案和解析。"""

import json
from collections import Counter

from app.question_bank import (
    CODE_PATTERN,
    LETTERS,
    STAGES,
    TOTAL_QUESTIONS,
    _choice_text,
    _run,
    generate_question_bank_with_metadata,
)


def _correct_option(question: dict[str, str | None]) -> str:
    letter = str(question["answer"])
    return str(question[f"option_{letter.lower()}"])


def main() -> None:
    generated = generate_question_bank_with_metadata()
    questions = [item.data for item in generated]
    stage_counts = Counter(item.stage for item in generated)
    type_counts = Counter(str(question["question_type"]) for question in questions)
    answer_counts = Counter(str(question["answer"]) for question in questions)

    assert len(questions) == TOTAL_QUESTIONS
    assert len({question["title"] for question in questions}) == TOTAL_QUESTIONS
    # 即使去掉数字、文本和变量名，10,000 个程序结构仍必须全部不同。
    assert len({item.structure_fingerprint for item in generated}) == TOTAL_QUESTIONS
    assert stage_counts == Counter({stage: 1_000 for stage in STAGES})
    assert type_counts == Counter(single_choice=6_000, true_false=2_000, fill_blank=2_000)
    assert set(answer_counts) == set(LETTERS)

    for index, question in enumerate(questions, start=1):
        title = str(question["title"])
        match = CODE_PATTERN.search(title)
        assert match, f"第 {index} 题缺少 Python 代码块"
        actual_output = _run(match.group(1))
        expected_answer = _choice_text(actual_output)
        question_type = question["question_type"]

        if question_type == "single_choice":
            assert _correct_option(question) == expected_answer, f"第 {index} 题选择答案错误"
        elif question_type == "fill_blank":
            accepted = json.loads(str(question["accepted_answers"]))
            assert expected_answer in accepted, f"第 {index} 题填空答案错误"
        else:
            marker = "判断题：下面代码的输出是 `"
            claimed = title.split(marker, 1)[1].split("`。", 1)[0].replace("\\n", "\n")
            expected = "A" if claimed == expected_answer else "B"
            assert question["answer"] == expected, f"第 {index} 题判断结论错误"

        shown = expected_answer.replace("\n", "\\n")
        assert f"`{shown}`" in str(question["analysis"]), f"第 {index} 题解析未给出实际输出"

    assert any("s.replace" in str(question["title"]) for question in questions)
    print(f"题库总数：{len(questions)}")
    print(f"阶段分布：{dict(sorted(stage_counts.items()))}")
    print(f"题型分布：{dict(sorted(type_counts.items()))}")
    print(f"答案位置：{dict(sorted(answer_counts.items()))}")
    print("审计通过：10,000 个结构指纹全部不同，且代码、答案与解析逐题一致。")


if __name__ == "__main__":
    main()
