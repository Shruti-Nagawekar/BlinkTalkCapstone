import threading
import time
from SharedFrame import FrameInstance
from ServerBT import app, calibration_choice, SharedOutput
from FinalBT import BlinkToMorse

print(f"FrameInstance ID in RunBlinkTalk.py: {id(FrameInstance)}")

# function to run FastAPI server
def RunServer():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011, log_level="warning")

# start FastAPI server in background
ServerThread = threading.Thread(target=RunServer, daemon=True)
ServerThread.start()

# wait for server
time.sleep(2)

# Wait for Swift to send the option
while calibration_choice["selected"] is None:
    print("Waiting for calibration selection from Swift...")
    time.sleep(2)

# load calibration once selected
TimingSetting = calibration_choice["selected"]
Instance = BlinkToMorse()
print("Starting BlinkToMorse Session...")
Instance.LoadCalibration(TimingSetting)
# run the main BlinkToMorse session
Instance.CommunicationSession()
SharedOutput["result"] = Instance.GetOutput()
print("Final Output to Send to Swift:", SharedOutput["result"])

# keep server alive so Swift can fetch the result
try:
    print("Keeping server alive for Swift to retrieve result...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Server manually interrupted...")