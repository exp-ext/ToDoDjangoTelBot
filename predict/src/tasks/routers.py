from fastapi import APIRouter, HTTPException, status

from .model_utils import predict
from .schemas import Task

router = APIRouter()


@router.post("/check/", status_code=status.HTTP_200_OK)
async def get_task_predict(task: Task):
    try:
        prediction = await predict(task.text)
        return {"predicted_class": prediction}
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
