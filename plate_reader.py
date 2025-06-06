import cv2
import easyocr
import time
import csv
import os
from ultralytics import YOLO


class ANPRDetector:
    def __init__(self):
        # Initialize YOLO models
        self.car_model = YOLO('yolov8n.pt')  # For car detection
        self.plate_model = YOLO('yolov8n.pt')  # You may want to use a license plate specific model

        # Initialize EasyOCR
        self.reader = easyocr.Reader([])

        # Create directory if it doesn't exist
        os.makedirs('parking_data', exist_ok=True)

        # CSV file path
        self.csv_file = 'parking_data/anpr_detections.csv'

        # Initialize CSV file with headers if it doesn't exist
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['id', 'plate_number', 'confidence', 'detection_time',
                                 'camera_location', 'is_emergency', 'processed'])

        self.detection_id = 1

    def detect_cars(self, frame):
        """Detect cars in the frame"""
        results = self.car_model(frame)
        car_boxes = []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Class 2 is 'car' in COCO dataset
                    if int(box.cls) == 2 and box.conf > 0.5:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        car_boxes.append((x1, y1, x2, y2))

        return car_boxes

    def detect_plates_in_car(self, frame, car_box):
        """Detect license plates within car region"""
        x1, y1, x2, y2 = car_box
        car_region = frame[y1:y2, x1:x2]

        # You might want to use a specialized license plate detection model here
        results = self.plate_model(car_region)
        plate_boxes = []

        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Adjust coordinates relative to original frame
                    px1, py1, px2, py2 = map(int, box.xyxy[0])
                    plate_boxes.append((x1 + px1, y1 + py1, x1 + px2, y1 + py2))

        return plate_boxes

    def read_plate_text(self, frame, plate_box):
        """Extract text from license plate using EasyOCR"""
        x1, y1, x2, y2 = plate_box
        plate_region = frame[y1:y2, x1:x2]

        # Use EasyOCR to read text
        results = self.reader.readtext(plate_region)

        if results:
            # Get the text with highest confidence
            best_result = max(results, key=lambda x: x[2])
            text = best_result[1].replace(' ', '').upper()
            confidence = best_result[2]
            return text, confidence

        return None, 0

    def save_detection(self, plate_text, confidence, camera_location="Camera_1"):
        """Save detection to CSV file"""
        detection_time = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(self.csv_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                self.detection_id,
                plate_text,
                round(confidence, 3),
                detection_time,
                camera_location,
                False,  # is_emergency
                False  # processed
            ])

        self.detection_id += 1

    def process_frame(self, frame, camera_location="Camera_1"):
        """Process a single frame for ANPR"""
        # Detect cars
        car_boxes = self.detect_cars(frame)

        detections = []

        for car_box in car_boxes:
            # Detect plates in car region
            plate_boxes = self.detect_plates_in_car(frame, car_box)

            for plate_box in plate_boxes:
                # Read plate text
                plate_text, confidence = self.read_plate_text(frame, plate_box)

                if plate_text and confidence > 0.5:
                    # Save detection
                    self.save_detection(plate_text, confidence, camera_location)

                    # Draw bounding boxes on frame
                    cv2.rectangle(frame, (car_box[0], car_box[1]), (car_box[2], car_box[3]), (0, 255, 0), 2)
                    cv2.rectangle(frame, (plate_box[0], plate_box[1]), (plate_box[2], plate_box[3]), (0, 0, 255), 2)
                    cv2.putText(frame, f"{plate_text} ({confidence:.2f})",
                                (plate_box[0], plate_box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                    detections.append({
                        'plate_text': plate_text,
                        'confidence': confidence,
                        'car_box': car_box,
                        'plate_box': plate_box
                    })

        return frame, detections

    def run_camera(self, camera_index=0):
        """Run ANPR on camera feed"""
        cap = cv2.VideoCapture(camera_index)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process frame
            processed_frame, detections = self.process_frame(frame)

            # Display frame
            cv2.imshow('ANPR Detection', processed_frame)

            # Print detections
            for detection in detections:
                print(f"Detected: {detection['plate_text']} (Confidence: {detection['confidence']:.3f})")

            # Exit on 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def process_image(self, image_path):
        """Process a single image"""
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Could not load image: {image_path}")
            return

        processed_frame, detections = self.process_frame(frame)

        # Save processed image
        output_path = f"parking_data/processed_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, processed_frame)

        print(f"Processed image saved to: {output_path}")
        for detection in detections:
            print(f"Detected: {detection['plate_text']} (Confidence: {detection['confidence']:.3f})")


# Example usage
if __name__ == "__main__":
    detector = ANPRDetector()

    # for camera
    detector.run_camera(0)

    # path to an image
    # detector.process_image('path_to_your_image.jpg')

    print("ANPR Detector initialized. Use run_camera() or process_image() methods.")