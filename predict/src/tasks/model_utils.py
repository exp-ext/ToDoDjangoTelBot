import torch
from src.config import settings
from transformers import (DistilBertForSequenceClassification,
                          DistilBertTokenizer)

model_path = f"{settings.base_dir}/tasks/distil_bert/"
model = DistilBertForSequenceClassification.from_pretrained(model_path)
tokenizer = DistilBertTokenizer.from_pretrained(model_path)


async def predict(text: str):
    encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**encoded_input)

    predictions = torch.softmax(outputs.logits, dim=1)
    predicted_class = torch.argmax(predictions, dim=1).item()
    predict = {
        0: 'chat_gpt',
        1: 'task'
    }
    return predict[predicted_class]
