"""在不启动 Web 服务的情况下审计生成题库。"""

from collections import Counter

from app.question_bank import LETTERS, STAGES, TOTAL_QUESTIONS, generate_question_bank


def main() -> None:
    questions = generate_question_bank()
    stage_counts = Counter(
        int(question["title"].split("阶段 ", 1)[1].split("：", 1)[0])
        for question in questions
    )
    answer_counts = Counter(question["answer"] for question in questions)

    assert len(questions) == TOTAL_QUESTIONS
    assert set(answer_counts) == set(LETTERS)
    assert set(stage_counts) == set(STAGES)
    assert all(count == 1_000 for count in stage_counts.values())
    assert any("s.replace" in question["title"] for question in questions)

    print(f"题库总数：{len(questions)}")
    print(f"阶段分布：{dict(sorted(stage_counts.items()))}")
    print(f"答案分布：{dict(sorted(answer_counts.items()))}")
    print("审计通过：题量、阶段、答案与 s.replace 样例均符合要求。")


if __name__ == "__main__":
    main()

