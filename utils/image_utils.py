import io
from PIL import Image
from fastapi import UploadFile, HTTPException
from starlette import status


ALLOWED_MIME = {"image/png", "image/jpeg"}


async def validate_image(file: UploadFile) -> bytes:
    contents = await file.read()

    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image type",
        )

    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Invalid Image",
        )

    return contents
