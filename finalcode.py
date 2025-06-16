import cv2 as cv
import supervision as sv
from ultralytics import YOLO
import serial
from serial.tools import list_ports
import math
import torch
import time

#user input wala function bnaya hai
def get_user_port():
    ports = serial.tools.list_ports.comports()
    ports_list = []

    for one in ports:
        ports_list.append(str(one))
        print(str(one))

    com = input("Select Com Port for Arduino (#): ")
    return str(com)

def main():
    ser = None 
    try:
        #prakhar wale mein ni hoga abhi aditya wale mein shyd ho
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(device)
        port = get_user_port()
        #baudrate check krna
        ser = serial.Serial(port, 9600, timeout=1)
          #location check
        model = YOLO("./ppe.pt")
        model.to(device)

        cap = cv.VideoCapture(0)
        # Box annotations
        bounding_box_annotator = sv.BoxAnnotator()
        label_annotator = sv.LabelAnnotator()
        target_class = "P"

        #previous data wala concept use kia taki wo bulk mein ek sath message walil dikkt na ae
        previous_data = ""
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Unable to capture Video")
                break

            # Bounding Box processing
            results = model(frame, stream=True)
            for result in results:
                boxes = result.boxes
                X1 = Y1 = X2 = Y2 = 0
                area = 0
                for box in boxes:
                    if math.ceil(box.conf[0]) > 0.5 and model.names[int(box.cls[0])] == target_class:   
                        X1, Y1, X2, Y2 = box.xyxy[0]
                        X1, Y1, X2, Y2 = [int(X1), int(Y1), int(X2), int(Y2)]
                        detections = sv.Detections.from_ultralytics(result)
                        annotated_image = bounding_box_annotator.annotate(scene=frame, detections=detections)
                        annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections)
                        cv.imshow("Video", annotated_image)
                        area = int((X2 - X1) * (Y2 - Y1))

            # Communication with Arduino
            center_xp = (X2 + X1) // 2
            center_yp = (Y2 + Y1) // 2
            # approx_framearea = (frame.shape[1] - 100) * (frame.shape[0] - 100)
            threshold = frame.shape[1] // 5
            data = ""
            print("Threshold: ", threshold)
            #inne zyada data.encode ki zrursat thi last mein define kr dia
            # if area >= approx_framearea:
            #     data = "S"
            # data = "A"
            # ser.write(data.encode())
            if center_xp < threshold:
                data = "A"
            elif center_xp < 2 * threshold:
                data = "B"
            elif center_xp > 4 * threshold:
                data = "D"
            elif center_xp > 3 * threshold:
                data = "C"
            elif ((center_xp > 2 * threshold) and (center_xp < 3 * threshold)):
                data = "f"

            
            else:
                data = "S"
                # if center_yp > 4 * frame.shape[0] // 3:
                #     data = "S"
                # elif center_yp < frame.shape[0] // 3:
                #     data = "F"
                # else:
                #     data = "f"
             #ek sath multople command bhejne ko rokne se
            if data != previous_data:
                ser.write(data.encode())
                serialData = ser.readline().decode("utf-8").strip()
                print("the data is: ",serialData)
                previous_data = data
                # print(data)

            if cv.waitKey(1) == ord('q'):
                break
            # time.sleep(0.3)
        
    #ye sare checks dale if koi error ae to pta chle
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if ser is not None and ser.is_open:
            ser.close()
            print("Serial port closed.")
#whatsapp mein copy krne k bad underscore ki dikkt ati hai MIND IT!!
if __name__ == "__main__":
    main()
#koi ladt ein error ae to btana konsa error
#serial moniotor sbke close kr lena