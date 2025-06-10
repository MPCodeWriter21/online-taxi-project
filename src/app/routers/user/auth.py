# yapf: disable

from fastapi import APIRouter

# yapf: enable

router = APIRouter(tags=["user-auth"], include_in_schema=False)
