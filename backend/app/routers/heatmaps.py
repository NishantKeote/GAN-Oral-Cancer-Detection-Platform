"""Router for serving generated XAI heatmaps and overlay images."""

import re
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.config import settings

router = APIRouter()

# Whitelisted filenames corresponding to the four attribution methods
ALLOWED_HEATMAP_FILENAMES = {
    "grad_cam.png",
    "grad_cam_overlay.png",
    "grad_cam_plus_plus.png",
    "grad_cam_plus_plus_overlay.png",
    "layer_cam.png",
    "layer_cam_overlay.png",
    "hires_cam.png",
    "hires_cam_overlay.png",
}

CASE_ID_REGEX = re.compile(r"^CASE-[A-F0-9]{10}$")


@router.get("/heatmaps/{case_id}/{filename}", summary="Stream XAI Heatmap or Overlay PNG")
async def get_heatmap(case_id: str, filename: str):
    """Retrieve and stream a generated XAI heatmap or overlay PNG file.

    Guarded against directory traversal attacks by validating case ID regex
    and whitelisting exact allowable filenames.
    """
    if not CASE_ID_REGEX.match(case_id) or filename not in ALLOWED_HEATMAP_FILENAMES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heatmap not found or invalid identifier format.",
        )

    file_path = settings.ARTIFACT_DIR / case_id / filename
    if not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested heatmap file does not exist on disk.",
        )

    return FileResponse(file_path, media_type="image/png", filename=filename)
