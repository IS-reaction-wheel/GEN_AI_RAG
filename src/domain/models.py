"""ドメインモデルおよび LLM 構造化出力用モデル"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# ドメインモデル（データ保持）
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    """チャットメッセージの役割"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """チャットメッセージ"""

    model_config = {"frozen": True}

    role: MessageRole
    content: str


class DocumentChunk(BaseModel):
    """ベクトル DB に格納するドキュメントチャンク"""

    model_config = {"frozen": True}

    chunk_id: str
    text: str
    source: str = Field(description="元ファイル名")
    page: Optional[int] = Field(default=None, description="ページ番号（PDF の場合）")
    metadata: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    """検索結果"""

    model_config = {"frozen": True}

    chunk: DocumentChunk
    score: float = Field(description="類似度 or Reranker スコア")


# ---------------------------------------------------------------------------
# LLM 構造化出力用モデル（with_structured_output 用）
# ---------------------------------------------------------------------------


class Subtask(BaseModel):
    """タスク分割ノードが生成するサブタスク"""

    purpose: str = Field(
        description="このサブタスクで明らかにしたいこと（日本語で記述）",
    )
    queries: list[str] = Field(
        description="検索クエリのリスト（日本語で記述）",
    )


class TaskPlanningResult(BaseModel):
    """タスク分割ノードの出力"""

    subtasks: list[Subtask] = Field(
        description="サブタスクのリスト（最大3個）",
    )


class JudgeResult(BaseModel):
    """十分性判定ノードの出力"""

    sufficient: bool = Field(description="情報が十分かどうか")
    reason: str = Field(description="判断理由（必ず日本語で記述すること）")
    additional_subtasks: list[Subtask] | None = Field(
        default=None,
        description="不足時の追加サブタスク（日本語で記述）",
    )

    @model_validator(mode="after")
    def force_consistency(self) -> "JudgeResult":
        """LLM 出力の論理矛盾を自動補正する。

        - sufficient=True の場合: additional_subtasks を None に強制
        - sufficient=False かつ additional_subtasks が空の場合:
          追加調査を具体化できなかったため sufficient=True に補正
        """
        if self.sufficient:
            self.additional_subtasks = None
        if not self.sufficient and not self.additional_subtasks:
            self.sufficient = True
            self.reason += (
                " (※追加調査事項が具体化できなかったため、現状の情報で回答します)"
            )
            self.additional_subtasks = None
        return self
