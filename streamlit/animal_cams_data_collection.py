import time
from pydantic import BaseModel
from typing import Optional, Any
import asyncio

from groundlight import Groundlight
import utils


class AnimalCam(BaseModel):
    stream_link: str
    website_link: str
    detector: Optional[Any] = None
    current_image: Optional[Any] = None
    current_image_query: Optional[Any] = None
    probability_present: float = 0.0


@utils.background
def capture_frame_and_answer_query(animal_cam):
    print(f"Submitting query for {animal_cam.stream_link}")
    animal_cam.current_image = utils.capture_image(animal_cam.stream_link, swap_rb=True)
    animal_cam.current_image_query = gl.submit_image_query(
        animal_cam.detector, image=animal_cam.current_image, wait=45
    )
    animal_cam.probability_present = utils.confidence_to_prob(animal_cam.current_image_query.result)


CAMS = {
    "Baboon": AnimalCam(
        stream_link="https://zssd-baboon.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/baboon-cam",
    ),
    "Tiger": AnimalCam(
        stream_link="https://zssd-tiger.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/tiger-cam",
    ),
    "Koala": AnimalCam(
        stream_link="https://zssd-koala.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/koala-cam",
    ),
    "Polar Bear": AnimalCam(
        stream_link="https://polarplunge.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/polar-cam",
    ),
    "Ape": AnimalCam(
        stream_link="https://ape.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/ape-cam",
    ),
}

gl = Groundlight()  # Reads API key from env

for animal, animal_cam in CAMS.items():
    query = f"Is there a {animal} visible in the image?"
    animal_cleaned = animal.lower().replace(" ", "")
    detector_name = f"is_{animal_cleaned}_present"
    animal_cam.detector = gl.get_or_create_detector(name=detector_name, query=query)
    print(f"{animal} cam: {animal_cam}")
print("Detectors initialized, collecting 5k images...")


for i in range(1000):  # 5 animal cams * 1000 iterations = 5k images collected
    start = time.time()

    # Submit queries async
    print("Capturing images and submitting queries...")
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    looper = asyncio.gather(*[capture_frame_and_answer_query(animal_cam) for animal_cam in CAMS.values()])
    event_loop.run_until_complete(looper)

    # Display image w/ highest probability
    most_likely_animal: str = max(CAMS, key=lambda k: (CAMS[k].probability_present, k))
    print("Most likely animal:", most_likely_animal)

    time.sleep(60 * 12)
