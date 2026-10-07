"""API 请求和响应的数据结构。"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Answer = Literal["A", "B", "C", "D"]


class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=10_000)
    option_a: str = Field(min_length=1, max_length=2_000)
    option_b: str = Field(min_length=1, max_length=2_000)
    option_c: str = Field(min_length=1, max_length=2_000)
    option_d: str = Field(min_length=1, max_length=2_000)
    answer: Answer
    analysis: str = Field(min_length=1, max_length=10_000)

    @field_validator("answer", mode="before")
    @classmethod
    def normalize_answer(cls, value: object) -> object:
        """允许管理页面传入小写答案，但入库前统一转为大写。"""
        return value.upper() if isinstance(value, str) else value

    @field_validator(
        "title", "option_a", "option_b", "option_c", "option_d", "analysis"
    )
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class QuestionCreate(QuestionBase):
    """新增题目请求。"""


class QuestionPublic(BaseModel):
    """公开题目，不返回正确答案，避免前端提前看到答案。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class AnswerCheckRequest(BaseModel):
    question_id: int = Field(gt=0)
    selected_answer: Answer

    @field_validator("selected_answer", mode="before")
    @classmethod
    def normalize_selected_answer(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


class AnswerCheckResponse(BaseModel):
    is_correct: bool
    selected_answer: Answer
    correct_answer: Answer
    analysis: str

