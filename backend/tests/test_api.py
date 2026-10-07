"""题目 API 的核心流程测试。"""

import app.main as main_module
from app.database import Base, get_db
from app.main import app
from sqlalchemy import create_engine
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


def test_unknown_question_returns_404() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/question/check",
            json={"question_id": 999999, "selected_answer": "A"},
        )
        assert response.status_code == 404
