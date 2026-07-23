# -*- coding: utf-8 -*-
"""Draw face detection boxes"""
import cv2
import numpy as np

img = cv2.imread(r"C:\ComfyUI\input\wedding_input.png")
h, w = img.shape[:2]

marked = img.copy()

net = cv2.dnn.readNetFromCaffe(
    r"C:\u-claw\portable\data\.openclaw\workspace\deploy.prototxt",
    r"C:\u-claw\portable\data\.openclaw\workspace\res10_300x300_ssd_iter_140000.caffemodel"
)
blob = cv2.dnn.blobFromImage(cv2.resize(img, (300,300)), 1.0, (300,300), (104,177,123))
net.setInput(blob)
dets = net.forward()

for i in range(dets.shape[2]):
    conf = dets[0,0,i,2]
    print("Detection {}: conf={:.3f}".format(i, conf))
    if conf > 0.5:
        box = dets[0,0,i,3:7] * np.array([w, h, w, h])
        fx, fy, fx2, fy2 = box.astype("int")
        cv2.rectangle(marked, (fx, fy), (fx2, fy2), (0, 255, 0), 4)
        cv2.putText(marked, "Face {:.2f}".format(conf), (fx, fy-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        print("  Box: ({},{})-({},{})".format(fx, fy, fx2, fy2))

marked_small = cv2.resize(marked, (0,0), fx=0.3, fy=0.3)
cv2.imwrite(r"C:\temp\tts\face_detection.jpg", marked_small, [cv2.IMWRITE_JPEG_QUALITY, 85])
print("Saved face detection overlay")
