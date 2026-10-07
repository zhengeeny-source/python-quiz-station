"""把完整生成题库导出为 JSON，便于检查或迁移。"""

import json
from pathlib import Path

from app.question_bank import generate_question_bank


def main() -> None:
    destination = Path(__file__).resolve().parents[1] / "generated_question_bank.json"
    destination.write_text(
        json.dumps(generate_question_bank(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"已导出：{destination}")


if __name__ == "__main__":
    main()

