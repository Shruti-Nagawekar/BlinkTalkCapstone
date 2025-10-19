# ServerBT.py
from SharedFrame import FrameInstance
from fastapi import FastAPI
from pydantic import BaseModel
import base64
import cv2
import numpy as np

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from BlinkTalk backend!"}

# store selected calibration setting
calibration_choice = {"selected": None}

class CalibrationChoice(BaseModel):
     # expects "slow" or "medium"
    option: str

@app.post("/set_calibration")
async def set_calibration(choice: CalibrationChoice):
    if choice.option.lower() not in ["slow", "medium"]:
        return {"status": "error", "message": "Invalid option"}

    calibration_choice["selected"] = choice.option.lower()
    print(f"Calibration setting received from Swift: {calibration_choice['selected']}")
    return {"status": "success", "selected": calibration_choice["selected"]}


# define expected POST payload
class FrameData(BaseModel):
    frame_data: str
    user: str

@app.post("/send_frame")
async def receive_frame(data: FrameData):
    try:
        image_bytes = base64.b64decode(data.frame_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is not None:
            FrameInstance.update(frame)
        else:
            print("Frame decoding failed (frame is None)")

        return {"status": "success", "message": "Frame received"}
    except Exception as e:
        print(f"Error decoding frame: {e}")
        return {"status": "error", "message": str(e)}

SharedOutput = {"result": ""}
@app.get("/get_translation")
async def get_translation():
    return {"output": SharedOutput["result"]}