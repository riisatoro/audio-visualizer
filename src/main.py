import os
import shutil
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, Request, UploadFile, Cookie, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np

app = FastAPI(
    title="Audio visualizer",
    description="Displays audio plots",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def root(
        request: Request,
        session_id: Annotated[str, Cookie()] = None,
):
    response = templates.TemplateResponse("upload_form.html", {"request": request})
    if not session_id:
        response.set_cookie(key="session_id", value=uuid4())
    return response


@app.post("/upload")
def create_upload_file(
        request: Request,
        files: list[UploadFile],
        session_id: Annotated[str, Cookie()] = None,
):
    if not session_id:
        raise HTTPException(status_code=404, detail="No session_id cookie")

    file_upload_path = os.path.join("/app/static/media", session_id)
    if not os.path.exists(file_upload_path):
        os.makedirs(file_upload_path)
    else:
        shutil.rmtree(file_upload_path)
        os.makedirs(file_upload_path)

    for file in files:
        with open(os.path.join(file_upload_path, file.filename), "wb") as f:
            f.write(file.file.read())

    return {"redirect_url": "/media/wait"}


@app.get("/media/wait", response_class=RedirectResponse)
def wait_for_media(
        request: Request,
        session_id: Annotated[str, Cookie()] = None,
):
    base_path = os.path.join("/app/static/media", session_id)
    result_path = os.path.join(base_path, "result/")
    if not os.path.exists(result_path):
        os.mkdir(result_path)

    for file in os.scandir(base_path):
        plt.clf()

        if not file.is_file():
            continue

        y, sr = librosa.load(file.path)
        wave = librosa.amplitude_to_db(librosa.stft(y), ref=np.max)

        plt.figure(figsize=(12, 6))
        librosa.display.specshow(wave, sr=sr, x_axis='time', y_axis='log')
        plt.colorbar(format='%+2.0f dB')
        plt.title('Spectrogram')

        plt.savefig(os.path.join(result_path, file.name + '.png'), format='png')

    return RedirectResponse(url="/media/results")


@app.get("/media/results")
def get_results(
        request: Request,
        session_id: Annotated[str, Cookie()] = None,
):
    if not session_id:
        raise HTTPException(status_code=404, detail="No session_id cookie")

    result_images_path = os.path.join("/app/static/media", session_id, 'result/')
    if not os.path.exists(result_images_path):
        raise HTTPException(status_code=404, detail="No media found")

    plot_files = [
        {
            "name": filename,
            "original": os.path.join("/static/media", session_id, filename).replace('.png', ''),
            "url": os.path.join(result_images_path, filename).replace('/app', '')
        }
        for filename in os.listdir(result_images_path)
    ]

    return templates.TemplateResponse("results.html", {"request": request, "zip_files": plot_files})
