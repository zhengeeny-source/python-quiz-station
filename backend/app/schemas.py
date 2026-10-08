"""API 请求和响应的数据结构。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


Answer = Literal["A", "B", "C", "D"]
QuestionType = Literal["single_choice", "true_false", "fill_blank"]


class QuestionBase(BaseModel):
    title: str = Field(min_length=1, max_length=10_000)
    option_a: str = Field(default="", max_length=2_000)
    option_b: str = Field(default="", max_length=2_000)
    option_c: str = Field(default="", max_length=2_000)
    option_d: str = Field(default="", max_length=2_000)
    answer: Answer = "A"
    analysis: str = Field(min_length=1, max_length=10_000)
    question_type: QuestionType = "single_choice"
    accepted_answers: list[str] | None = Field(default=None, max_length=20)

    @field_validator("answer", mode="before")
    @classmethod
    def normalize_answer(cls, value: object) -> object:
        """允许管理页面传入小写答案，但入库前统一转为大写。"""
        return value.upper() if isinstance(value, str) else value

    @field_validator("title", "analysis")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value

    @field_validator("option_a", "option_b", "option_c", "option_d")
    @classmethod
    def strip_option(cls, value: str) -> str:
        return value.strip()

    @field_validator("accepted_answers")
    @classmethod
    def normalize_accepted_answers(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        normalized = list(dict.fromkeys(answer.strip() for answer in value if answer.strip()))
        return normalized or None

    @model_validator(mode="after")
    def validate_question_type(self):
        if self.question_type == "single_choice":
            if not all([self.option_a, self.option_b, self.option_c, self.option_d]):
                raise ValueError("选择题必须填写 A、B、C、D 四个选项")
        elif self.question_type == "true_false":
            if self.answer not in {"A", "B"}:
                raise ValueError("判断题答案只能是 A（正确）或 B（错误）")
            self.option_a, self.option_b = "正确", "错误"
            self.option_c = self.option_d = ""
        elif not self.accepted_answers:
            raise ValueError("填空题至少需要一个可接受答案")
        return self


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
    question_type: QuestionType


class AnswerCheckRequest(BaseModel):
    question_id: int = Field(gt=0)
    selected_answer: str = Field(min_length=1, max_length=2_000)

    @field_validator("selected_answer", mode="before")
    @classmethod
    def normalize_selected_answer(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        value = value.strip()
        return value.upper() if len(value) == 1 else value


class AnswerCheckResponse(BaseModel):
    is_correct: bool
    selected_answer: str
    correct_answer: str
    analysis: str
    question_type: QuestionType


class AccountCredentials(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_\u4e00-\u9fff]+$",
        description="3-32 位中文、字母、数字或下划线",
    )
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip()


class RegisterRequest(AccountCredentials):
    """注册请求。"""


class LoginRequest(AccountCredentials):
    """登录请求。"""


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserPublic


class ProgressSummary(BaseModel):
    total_answered: int
    correct_count: int
    wrong_count: int
    accuracy: int
    unique_questions: int


class AnswerHistoryItem(BaseModel):
    id: int
    question_id: int
    title: str
    question_type: QuestionType
    selected_answer: str
    is_correct: bool
    answered_at: datetime
