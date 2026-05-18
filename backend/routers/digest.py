from fastapi import APIRouter, Depends, BackgroundTasks

from backend.models.user import User
from backend.services.auth_service import get_current_user
from backend.services.digest_service import send_digest_to_user

router = APIRouter()


@router.post("/send-now")
async def send_digest_now(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(
        send_digest_to_user,
        str(current_user.id),
    )

    return {
        "message": f"Digest is being sent to {current_user.email}"
    }


@router.get("/history")
async def get_digest_history():
    return {
        "history": [],
        "message": "History temporarily disabled"
    }