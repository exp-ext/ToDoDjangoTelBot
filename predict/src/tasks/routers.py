import torch
from fastapi import APIRouter, status
from src.config import settings
from transformers import (DistilBertForSequenceClassification,
                          DistilBertTokenizer)

from .schemas import Task

router = APIRouter()


@router.post("/check/", status_code=status.HTTP_200_OK)
async def get_task_predict(task: Task):

    model_path = f"{settings.base_dir}/tasks/distil_bert/"
    model = DistilBertForSequenceClassification.from_pretrained(model_path)
    tokenizer = DistilBertTokenizer.from_pretrained(model_path)
    encoded_input = tokenizer(task.text, padding=True, truncation=True, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**encoded_input)

    predictions = torch.softmax(outputs.logits, dim=1)
    predicted_class = torch.argmax(predictions, dim=1).item()
    predict = {
        0: 'chat_gpt',
        1: 'task'
    }
    return {"predicted_class": predict[predicted_class]}
