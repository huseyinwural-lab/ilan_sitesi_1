import os
import uuid
import shutil
from fastapi import UploadFile, HTTPException
from pathlib import Path

class MediaService:
    def __init__(self, upload_dir: str = "static/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_types = ["image/jpeg", "image/png", "image/webp"]

    async def save_image(self, file: UploadFile) -> str:
        # 1. Validate Type
        if file.content_type not in self.allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, WebP allowed.")
            
        # 2. Validate Size (Naive check, real check needs reading stream or header)
        # Assuming Nginx/Reverse Proxy handles max body size
        
        # 3. Generate Filename
        ext = file.filename.split(".")[-1].lower()
        if ext not in ["jpg", "jpeg", "png", "webp"]:
            ext = "jpg" # Default
            
        filename = f"{uuid.uuid4()}.{ext}"
        file_path = self.upload_dir / filename
        
        # 4. Save File
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        finally:
            file.file.close()
            
        # 5. Return URL (Relative)
        return f"/static/uploads/{filename}"
