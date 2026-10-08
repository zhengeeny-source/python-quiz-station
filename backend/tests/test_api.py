"""题目 API 的核心流程测试。"""

import re

import app.main as main_module
from app.database import Base, get_db
from app.main import app
from app.models import AnswerRecord, AppMetadata, Question
from app.question_bank import QUESTION_BANK_VERSION
from app.seed import seed_questions
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient


test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


def override_get_db():
    with TestingSession() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db
main_module.engine = test_engine
main_module.SessionLocal = TestingSession


def setup_module() -> None:
    Base.metadata.create_all(bind=test_engine)


def teardown_module() -> None:
    Base.metadata.drop_all(bind=test_engine)
    app.dependency_overrides.clear()


def test_quiz_flow() -> None:
    with TestClient(app) as client:
        list_response = client.get("/api/question/list")
        assert list_response.status_code == 200
        assert len(list_response.json()) >= 10_000
        assert "answer" not in list_response.json()[0]

        random_response = client.get("/api/question/random")
        assert random_response.status_code == 200
        question = random_response.json()
        assert "answer" not in question

        staged_response = client.get("/api/question/random?stage=4")
        assert staged_response.status_code == 200
        assert staged_response.json()["title"].startswith("【阶段 4：")

        check_response = client.post(
            "/api/question/check",
            json={"question_id": question["id"], "selected_answer": "A"},
        )
        assert check_response.status_code == 200
        result = check_response.json()
        if question["question_type"] == "fill_blank":
            assert result["correct_answer"].strip()
        else:
            assert result["correct_answer"] in ["A", "B", "C", "D"]
        assert isinstance(result["is_correct"], bool)
        assert result["analysis"]


def test_add_question_and_validation() -> None:
    payload = {
        "title": "`print(1 + 1)` 的输出是什么？",
        "option_a": "1",
        "option_b": "2",
        "option_c": "11",
        "option_d": "报错",
        "answer": "b",
        "analysis": "整数相加得到 2。",
    }
    with TestClient(app) as client:
        response = client.post("/api/question/add", json=payload)
        assert response.status_code == 201
        assert "answer" not in response.json()

        invalid = {**payload, "answer": "E"}
        assert client.post("/api/question/add", json=invalid).status_code == 422

        visually_duplicated = {
            **payload,
            "option_c": "第一行\n第二行",
            "option_d": "第一行 第二行",
        }
        assert client.post("/api/question/add", json=visually_duplicated).status_code == 422


def test_unknown_question_returns_404() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/question/check",
            json={"question_id": 999999, "selected_answer": "A"},
        )
        assert response.status_code == 404


def test_true_false_and_fill_blank_flow() -> None:
    with TestClient(app) as client:
        questions = client.get("/api/question/list").json()
        true_false = next(item for item in questions if item["question_type"] == "true_false")
        fill_blank = next(item for item in questions if item["question_type"] == "fill_blank")

        assert true_false["option_a"] == "正确"
        assert true_false["option_b"] == "错误"
        assert fill_blank["option_a"] == ""

        true_result = client.post(
            "/api/question/check",
            json={"question_id": true_false["id"], "selected_answer": "A"},
        )
        assert true_result.status_code == 200
        assert true_result.json()["question_type"] == "true_false"

        # 错误提交会安全地返回填空题标准答案，再用标准答案复核必须判为正确。
        first_try = client.post(
            "/api/question/check",
            json={"question_id": fill_blank["id"], "selected_answer": "wrong"},
        )
        assert first_try.status_code == 200
        correct = first_try.json()["correct_answer"]
        second_try = client.post(
            "/api/question/check",
            json={"question_id": fill_blank["id"], "selected_answer": correct},
        )
        assert second_try.json()["is_correct"] is True


def test_add_fill_blank_question() -> None:
    payload = {
        "question_type": "fill_blank",
        "title": "`print(1 + 1)` 的输出是什么？",
        "answer": "A",
        "analysis": "整数相加得到 2。",
        "accepted_answers": ["2"],
    }
    with TestClient(app) as client:
        created = client.post("/api/question/add", json=payload)
        assert created.status_code == 201
        question_id = created.json()["id"]
        result = client.post(
            "/api/question/check",
            json={"question_id": question_id, "selected_answer": " 2 "},
        )
        assert result.status_code == 200
        assert result.json()["is_correct"] is True


def test_account_login_and_persistent_progress() -> None:
    credentials = {"username": "learner_01", "password": "safe-password-123"}
    with TestClient(app) as client:
        registered = client.post("/api/auth/register", json=credentials)
        assert registered.status_code == 201
        body = registered.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["username"] == credentials["username"]
        assert "password" not in body["user"]

        assert client.post("/api/auth/register", json=credentials).status_code == 409
        assert client.post(
            "/api/auth/login",
            json={**credentials, "password": "wrong-password"},
        ).status_code == 401

        logged_in = client.post("/api/auth/login", json=credentials)
        assert logged_in.status_code == 200
        headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}
        assert client.get("/api/auth/me", headers=headers).status_code == 200

        first_question = client.get("/api/question/random?stage=1", headers=headers).json()
        checked = client.post(
            "/api/question/check",
            headers=headers,
            json={"question_id": first_question["id"], "selected_answer": "A"},
        )
        assert checked.status_code == 200

        summary = client.get("/api/progress/summary", headers=headers).json()
        assert summary["total_answered"] == 1
        assert summary["unique_questions"] == 1
        history = client.get("/api/progress/history", headers=headers).json()
        assert len(history) == 1
        assert history[0]["question_id"] == first_question["id"]

        # 登录账号抽题时会自动排除已经完成过的题目。
        next_question = client.get("/api/question/random?stage=1", headers=headers).json()
        assert next_question["id"] != first_question["id"]


def test_question_bank_upgrade_preserves_progress() -> None:
    """修正内置题时必须原位更新，不能因重建题库删除用户历史。"""
    with TestingSession() as db:
        record = db.scalar(select(AnswerRecord).limit(1))
        assert record is not None
        question_id = record.question_id
        history_count = db.scalar(select(func.count(AnswerRecord.id)))

        version = db.get(AppMetadata, "question_bank_version")
        assert version is not None
        version.value = "outdated-test-version"
        question = db.get(Question, question_id)
        assert question is not None
        question.option_d = question.option_c
        db.commit()

        seed_questions(db)

        refreshed = db.get(Question, question_id)
        assert refreshed is not None
        options = [refreshed.option_a, refreshed.option_b, refreshed.option_c, refreshed.option_d]
        visible = [re.sub(r"\s+", " ", option).strip() for option in options]
        assert len(set(visible)) == 4
        assert db.scalar(select(func.count(AnswerRecord.id))) == history_count
        assert db.get(AppMetadata, "question_bank_version").value == QUESTION_BANK_VERSION
