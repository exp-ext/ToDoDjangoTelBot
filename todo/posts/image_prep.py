from PIL import Image


def resize_and_crop_image(image: Image, desired_width: int, desired_height: int) -> Image:
    """Изменяет размер и обрезает изображение с сохранением пропорций.

    ## Parameters:
    - image (`Image`): Файл изображения для обработки.
    - desired_width (`int`): Желаемая ширина обработанного изображения.
    - desired_height (`int`): Желаемая высота обработанного изображения.

    ## Returns:
    - img (`Image`) Обработанное изображение с желаемыми размерами и обрезанными лишними частями.

    Функция открывает переданное изображение, вычисляет его соотношение сторон и
    обрезает или изменяет размер так, чтобы соответствовать желаемым размерам,
    сохраняя при этом пропорции изображения. Результат возвращается как объект
    изображения Pillow.

    ## Note:
    - Если исходное изображение уже имеет желаемые размеры, оно не будет изменено.
    - Функция работает с форматом изображения JPEG, измените формат по необходимости.
    """

    with Image.open(image) as img:
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        desired_aspect_ratio = desired_width / desired_height

        if aspect_ratio > desired_aspect_ratio:
            new_width = int(original_height * desired_aspect_ratio)
            left = (original_width - new_width) / 2
            right = (original_width + new_width) / 2
            top = 0
            bottom = original_height
        else:
            new_height = int(original_width / desired_aspect_ratio)
            left = 0
            right = original_width
            top = (original_height - new_height) / 2
            bottom = (original_height + new_height) / 2

        img = img.crop((left, top, right, bottom))
        img.thumbnail((desired_width, desired_height))

    return img
