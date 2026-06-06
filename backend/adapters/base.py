from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel

class GenerateRequest(BaseModel):
    prompt: str
    model: str
    size: str
    n: int
    extra_params: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = "url"
    watermark: Optional[bool] = True
    stream: Optional[bool] = False

class VideoGenerateRequest(BaseModel):
    prompt: str
    model: str
    duration: int
    resolution: str
    source_image: Optional[str] = None
    negative_prompt: Optional[str] = None

class ImageEditRequest(BaseModel):
    image: str
    instruction: str
    edit_type: str
    mask: Optional[str] = None

class BaseAdapter:
    def __init__(self, api_key: str, endpoint: str):
        self.api_key = api_key
        self.endpoint = endpoint

    async def generate_image(self, request: GenerateRequest) -> Tuple[bool, Any, Optional[str]]:
        raise NotImplementedError

    async def generate_video(self, request: VideoGenerateRequest) -> Tuple[bool, Any, Optional[str], Optional[str]]:
        raise NotImplementedError

    async def edit_image(self, request: ImageEditRequest) -> Tuple[bool, Any, Optional[str]]:
        raise NotImplementedError
