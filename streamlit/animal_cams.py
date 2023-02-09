import streamlit as st
import time
import pandas as pd
from pydantic import BaseModel
from typing import Optional, Any
import asyncio

from groundlight import Groundlight
import utils


st.write("# San Diego Zoo Animal Cam Monitor")
st.write("""Here we monitor five different streams provided by the San Diego Zoo:
Baboon, Tiger, Koala, Polar Bear, and Ape.
Every minute or so we will update you on
which stream is most likely to have an animal present!""")


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
        stream_link="https://zssd-baboon.preview.api.camzonecdn.com/previewimage",
        website_link="https://sdzsafaripark.org/cams/ape-cam",
    ),
}

gl = Groundlight()  # Reads API key from env

for animal, animal_cam in CAMS.items():
    query = f"Is there a {animal} visible in the image?"
    animal_cleaned = animal.lower().replace(" ", "")
    detector_name = f"is_{animal_cleaned}_present"
    animal_cam.detector = gl.get_or_create_detector(name=detector_name, query=query)
print("Detectors initialized")

result_space = st.empty()
result_space.write("Capturing images and submitting queries...")
timer_space = st.empty()

while True:
    start = time.time()

    # Submit queries async
    print("Capturing images and submitting queries...")
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    looper = asyncio.gather(*[capture_frame_and_answer_query(animal_cam) for animal_cam in CAMS.values()])
    event_loop.run_until_complete(looper)

    # Display image w/ highest probability
    most_likely_animal: str = max(CAMS, key=lambda k: (CAMS[k].probability_present, k))
    animal_cam = CAMS[most_likely_animal]
    with result_space.container():
        if animal_cam.probability_present < 0.5:
            st.write("It doesnt seem like any animals are present on any of the streams at the moment :(")
        else:
            st.write(f"[Watch a(n) {most_likely_animal} here!]({animal_cam.website_link})")
            st.image(animal_cam.current_image)  # type: ignore

        # Display bar chart
        chart_data = pd.DataFrame(
            {
                "Animal": CAMS.keys(),
                "Probability": [cam.probability_present for cam in CAMS.values()]
            }
        )
        chart_data = chart_data.sort_values(by="Probability", ascending=False)
        print(chart_data)
        st.bar_chart(chart_data, x="Animal", y="Probability")

        # Display links to other present animals
        if len([1 for animal_cam in CAMS.values() if animal_cam.probability_present > 0.5]) > 1:
            st.write("It seems like other animals may also be present!")
            for animal, animal_cam in CAMS.items():
                if animal_cam.probability_present > 0.5:
                    st.write(f"* [Watch a(n) {animal}]({animal_cam.website_link})")

    while (time.time() - start) < 120:
        timer_space.write(f"Submitting new queries in {int(60 - (time.time() - start))}s")
        time.sleep(1)
    timer_space.write("Submitting new queries...")
