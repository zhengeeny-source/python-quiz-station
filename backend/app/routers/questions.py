"""题目相关 RESTful API。"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Question
from app.schemas import (
    AnswerCheckRequest,
    AnswerCheckResponse,
    QuestionCreate,
    QuestionPublic,
)

router = APIRouter(prefix="/api/question", tags=["question"])
DbSession = Annotated[Session, Depends(get_db)]


def _parse_excluded_ids(value: str | None) -> list[int]:
    """把前端传来的逗号分隔 ID 转成整数列表。非法片段会被忽略。"""
    if not value:
        return []
    result: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if part.isdigit() and int(part) > 0:
            result.append(int(part))
    # 限制长度，避免超长查询参数造成不必要的数据库压力。
    return list(dict.fromkeys(result))[:1000]


@router.get("/random", response_model=QuestionPublic)
def get_random_question(
    db: DbSession,
    exclude_ids: Annotated[
        str | None,
        Query(description="可选，逗号分隔的已做题目 ID，本轮抽题时将排除它们"),
    ] = None,
    stage: Annotated[
        int | None,
        Query(ge=1, le=10, description="可选，新手路线阶段（1 到 10）"),
    ] = None,
) -> Question:
    """随机返回一道未被排除的题目。"""
    statement = select(Question)
    excluded = _parse_excluded_ids(exclude_ids)
    if excluded:
        statement = statement.where(Question.id.not_in(excluded))
    if stage is not None:
        statement = statement.where(Question.title.like(f"【阶段 {stage}：%"))
    question = db.scalar(statement.order_by(func.random()).limit(1))
    if question is None:
        raise HTTPException(status_code=404, detail="没有可用题目")
    return question


@router.post("/check", response_model=AnswerCheckResponse)
def check_answer(payload: AnswerCheckRequest, db: DbSession) -> AnswerCheckResponse:
    """判题，并在提交后返回正确答案与解析。"""
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    return AnswerCheckResponse(
        is_correct=payload.selected_answer == question.answer,
        selected_answer=payload.selected_answer,
        correct_answer=question.answer,
        analysis=question.analysis,
    )


@router.post(
    "/add", response_model=QuestionPublic, status_code=status.HTTP_201_CREATED
)
def add_question(payload: QuestionCreate, db: DbSession) -> Question:
    """新增一道题目。"""
    question = Question(**payload.model_dump())
    db.add(question)
    try:
        db.commit()
        db.refresh(question)
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="题目保存失败") from exc
    return question


@router.get("/list", response_model=list[QuestionPublic])
def list_questions(db: DbSession) -> list[Question]:
    """按 ID 返回全部公开题目信息，供题量统计使用。"""
    return list(db.scalars(select(Question).order_by(Question.id)).all())
