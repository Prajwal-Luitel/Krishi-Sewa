import os
from django.shortcuts import render
from ultralytics import YOLO
from PIL import Image
import io
import base64

# Load YOLO model - path relative to this file's location
model_path = os.path.join(os.path.dirname(__file__), 'model', 'best.pt')
model = YOLO(model_path)

# Use GPU if available 
try:
    model.to('cuda')
except Exception:
    pass  # Continue with CPU if CUDA is not available   

def detect(request):
    context = {}
    
    if request.method == "POST":
        # Get the uploaded image
        if 'imageInput' not in request.FILES:
            context['error'] = 'No image provided'
            return render(request, "detect.html", context)
        
        image_file = request.FILES['imageInput']
        
        # Open the image
        img = Image.open(image_file)
        img_array = img.convert('RGB')  # Ensure RGB format
        
        # Convert original image to base64
        buffer_orig = io.BytesIO()
        img.save(buffer_orig, format='PNG')
        orig_img_str = base64.b64encode(buffer_orig.getvalue()).decode()
        context['original_image'] = f'data:image/png;base64,{orig_img_str}'
        
        # Run YOLO inference
        results = model.predict(img_array, conf=0.25)
        
        # Get the result image with bounding boxes
        result_image = results[0].plot()
        
        # Convert to PIL Image
        result_pil = Image.fromarray(result_image)
        
        # Convert to base64 for passing to template
        buffer = io.BytesIO()
        result_pil.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Extract detection info
        detections = []
        if results[0].boxes is not None:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = results[0].names[cls_id]
                detections.append({
                    'class': class_name,
                    'confidence': f"{confidence*100:.2f}%"
                })
        
        # Pass result to template
        context['result_image'] = f'data:image/png;base64,{img_str}'
        context['detections'] = detections
    
    return render(request, "detect.html", context)