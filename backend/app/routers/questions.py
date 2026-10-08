"""题目相关 RESTful API。"""

import json
import unicodedata
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AnswerRecord, Question, User
from app.schemas import (
    AnswerCheckRequest,
    AnswerCheckResponse,
    QuestionCreate,
    QuestionPublic,
)
from app.security import get_optional_current_user

router = APIRouter(prefix="/api/question", tags=["question"])
DbSession = Annotated[Session, Depends(get_db)]
OptionalUser = Annotated[User | None, Depends(get_optional_current_user)]


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


def _normalize_fill_answer(value: str) -> str:
    """统一全半角、换行写法和首尾空白，但保留 Python 输出的大小写。"""
    return unicodedata.normalize("NFKC", value).replace("\\n", "\n").replace("\r\n", "\n").strip()


@router.get("/random", response_model=QuestionPublic)
def get_random_question(
    db: DbSession,
    current_user: OptionalUser,
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
    if current_user is not None:
        answered_questions = select(AnswerRecord.question_id).where(
            AnswerRecord.user_id == current_user.id
        )
        statement = statement.where(Question.id.not_in(answered_questions))
    if stage is not None:
        statement = statement.where(Question.title.like(f"【阶段 {stage}：%"))
    question = db.scalar(statement.order_by(func.random()).limit(1))
    if question is None:
        raise HTTPException(status_code=404, detail="没有可用题目")
    return question


@router.post("/check", response_model=AnswerCheckResponse)
def check_answer(
    payload: AnswerCheckRequest,
    db: DbSession,
    current_user: OptionalUser,
) -> AnswerCheckResponse:
    """判题，并在提交后返回正确答案与解析。"""
    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")

    if question.question_type == "fill_blank":
        accepted = json.loads(question.accepted_answers or "[]")
        selected = _normalize_fill_answer(payload.selected_answer)
        is_correct = any(selected == _normalize_fill_answer(answer) for answer in accepted)
        correct_answer = accepted[0] if accepted else ""
    else:
        selected = payload.selected_answer.upper()
        is_correct = selected == question.answer
        correct_answer = question.answer

    if current_user is not None:
        db.add(
            AnswerRecord(
                user_id=current_user.id,
                question_id=question.id,
                selected_answer=payload.selected_answer,
                is_correct=is_correct,
            )
        )
        try:
            db.commit()
        except SQLAlchemyError as exc:
            db.rollback()
            raise HTTPException(status_code=500, detail="答题记录保存失败") from exc

    return AnswerCheckResponse(
        is_correct=is_correct,
        selected_answer=payload.selected_answer,
        correct_answer=correct_answer,
        analysis=question.analysis,
        question_type=question.question_type,
    )


@router.post(
    "/add", response_model=QuestionPublic, status_code=status.HTTP_201_CREATED
)
def add_question(payload: QuestionCreate, db: DbSession) -> Question:
    """新增一道题目。"""
    data = payload.model_dump()
    accepted_answers = data.pop("accepted_answers")
    data["accepted_answers"] = (
        json.dumps(accepted_answers, ensure_ascii=False) if accepted_answers else None
    )
    question = Question(**data)
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
