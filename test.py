import time

import fastapi
from fastapi import UploadFile as fastapiUploadFile
from socaity_router import SocaityRouter
from socaity_router import JobProgress
from socaity_router.compatibility import UploadDataType
from socaity_router.settings import EXECUTION_PROVIDER
from socaity_router import UploadFile, ImageFile, AudioFile, VideoFile

#router = SocaityRouter(provider="runpod")
router = SocaityRouter(
    provider=EXECUTION_PROVIDER,
    app=fastapi.FastAPI(
        title="FriesMaker",
        summary="Make fries from potatoes",
        version="0.0.1",
        contact={
            "name": "w4hns1nn",
            "url": "https://github.com/w4hns1nn",
        }),
)

@router.post(path="/make_fries", queue_size=10)
def make_fries(job_progress: JobProgress, fries_name: str, amount: int = 1):
    job_progress.set_status(0.1, f"started new fries creation {fries_name}")
    time.sleep(1)
    job_progress.set_status(0.5, f"I am working on it. Lots of work to do {amount}")
    time.sleep(2)
    job_progress.set_status(0.8, "Still working on it. Almost done")
    time.sleep(2)
    return f"Your fries {fries_name} are ready"


@router.add_route("/make_file_fries")
def make_fries_from_files(
        potato_one: UploadDataType.FILE,
        potato_two: UploadFile,
        potato_three: fastapiUploadFile
    ):
    potato_one_content = potato_one.content
    potato_two_content = potato_two.content
    potato_three_content = potato_three.content

    return "fries"

@router.add_route("/make_image_fries")
def make_image_fries(
        potato_one: UploadDataType.IMAGE,
        potato_two: ImageFile,
    ):
    return "image_fries"

@router.add_route("/make_audio_fries")
def make_audio_fries(
        potato_one: UploadDataType.AUDIO,
        potato_two: AudioFile,
    ):
    potato_one_content = potato_one.content
    potato_two_content = potato_two.content

    return "audio_fries"

@router.add_route("/make_video_fries")
def make_video_fries(
        potato_one: UploadDataType.VIDEO,
        potato_two: VideoFile,
    ):
    potato_one_content = potato_one.content
    potato_two_content = potato_two.content
    return "video_fries"


if __name__ == "__main__":
    # Runpod version
    router.start(port=8000, environment="localhost")
    # router.start(environment="serverless", port=8000)
    # router.start(environment="localhost", port=8000)

