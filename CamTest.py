
import cv2

capture = cv2.VideoCapture(0)
cv2.namedWindow("CV2 Image")
ret, frame = capture.read()
cv2.imshow("CV2 Image", frame)
cv2.waitKey()
cv2.destroyAllWindows()

while True:
    passpica