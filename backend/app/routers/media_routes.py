from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from app.services.media_service import MediaService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_media(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Simple Image Upload. Returns URL.
    """
    service = MediaService()
    url = await service.save_image(file)
    return {"url": url}

@router.post("/upload/batch", response_model=List[dict])
async def upload_media_batch(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    service = MediaService()
    urls = []
    for file in files:
        url = await service.save_image(file)
        urls.append({"url": url})
    return urls
