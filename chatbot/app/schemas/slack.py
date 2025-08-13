from pydantic import BaseModel
from typing import Optional


class SlackResponse(BaseModel):
    """Standard Slack response for Socket Mode"""
    response_type: str = "ephemeral"  # "ephemeral" or "in_channel"
    text: str


class SlackMessage(BaseModel):
    """Slack message format for Socket Mode"""
    channel: str
    text: str
    username: Optional[str] = "bobbot"
    icon_emoji: Optional[str] = ":robot_face:"
