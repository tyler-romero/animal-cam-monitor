import time
import cv2
import numpy as np
from typing import Callable
import asyncio


class ImageCaptureException(Exception):
    pass


def capture_image(source: int | str = 0, swap_rb=True) -> np.ndarray:
    vid = cv2.VideoCapture(source)
    time.sleep(1)  # Allow cam to initialize
    result, image = vid.read()
    vid.release()
    if not result:
        raise ImageCaptureException
    if swap_rb:
        image = image[:, :, ::-1]
    return image


def confidence_to_prob(result) -> float:
    if result is None or result.label is None or result.confidence is None:
        return 0.0
    if result.label == "PASS":
        return result.confidence
    else:
        return 1 - result.confidence


# https://stackoverflow.com/questions/9786102/how-do-i-parallelize-a-simple-python-loop
def background(f) -> Callable:
    def wrapped(*args, **kwargs):
        return asyncio.get_event_loop().run_in_executor(None, f, *args, **kwargs)
    return wrapped
