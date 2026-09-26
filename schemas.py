from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Payload for the /generate-comic/json API route."""

    story_prompt: str = Field(..., description="The main idea for the comic")
    character_name: str = Field(..., description="Name of the main character")
    setting: str = Field(..., description="Where the story takes place")
    tone: str = Field(..., description="Mood of the story, e.g. funny, dramatic")
    art_style: str = Field(..., description="Visual style, e.g. anime, comic book")
