import pydantic


class OpenIDConfiguration(pydantic.BaseModel):
    token_endpoint: str
