import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import io
from PIL import Image
import json

from app.main import app
from app.database import get_db
from app.models import Farmer, Farm, SoilTest, DiseaseRecord
from app.routers.auth import get_current_farmer

# Create a mock farmer for dependencies
mock_farmer = Farmer(
    id=1,
    full_name="Test Farmer",
    phone_number="1234567890"
)

# Mock DB Session
class MockSession:
    def query(self, *args, **kwargs):
        mock_query = MagicMock()
        mock_farm = Farm(id=1, farmer_id=1, soil_type="Loamy", land_area_acres=2.5)
        mock_soil = SoilTest(id=1, farm_id=1, nitrogen=10, phosphorus=10, potassium=10, ph=6.5)
        
        # Depending on the model queried, return mock data
        def filter_side_effect(*f_args, **f_kwargs):
            m = MagicMock()
            def first_side_effect():
                if args[0] == Farm:
                    return mock_farm
                elif args[0] == SoilTest:
                    return mock_soil
                return None
            m.first = first_side_effect
            m.order_by.return_value = m
            return m
            
        mock_query.filter.side_effect = filter_side_effect
        return mock_query
        
    def add(self, *args, **kwargs):
        pass
        
    def commit(self):
        pass
        
    def refresh(self, obj):
        obj.id = 1
        obj.scanned_at = "2026-01-01T00:00:00Z"

def override_get_current_farmer():
    return mock_farmer

def override_get_db():
    return MockSession()

app.dependency_overrides[get_current_farmer] = override_get_current_farmer
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Helper to create a dummy image file
def create_dummy_image(color=(0, 255, 0), size=(100, 100)):
    image = Image.new('RGB', size, color=color)
    import random
    pixels = image.load()
    for i in range(10):
        for j in range(10):
            pixels[i, j] = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr

@pytest.fixture
def mock_yolo():
    with patch("app.routers.disease.yolo_disease_agent.predict") as mock_predict:
        yield mock_predict

@pytest.fixture
def mock_fertilizer():
    with patch("app.routers.disease.fertilizer_agent.calculate_fertilizer") as mock_fert:
        mock_fert.return_value = {
            "n_status": "Low", "p_status": "Low", "k_status": "Low",
            "fertilizer_schedule": [{"amount_grams_per_sqm": 10, "fertilizer_name": "Urea", "stage": "Vegetative"}]
        }
        yield mock_fert

def test_valid_diseased_leaf(mock_yolo, mock_fertilizer):
    """1. Valid diseased leaf"""
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Apple", "disease": "Apple Scab", "confidence": 0.95, "status": "High-confidence model prediction", "severity": "Moderate"},
        "management": {"available": True, "immediate_actions": []},
        "fertilizer": {"available": False},
        "is_healthy": False,
        "crop_key": "apple",
        "source": "DB"
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")}, data={"crop": "Apple"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["prediction"]["disease"] == "Apple Scab"
    assert data["fertilizer"]["available"] == True # Set to true because mock_fertilizer runs

def test_opencv_fails_but_yolo_classifies(mock_yolo, mock_fertilizer):
    """2. OpenCV fails but YOLO classifies (is_leaf_advisory=False, but YOLO returns boxes)"""
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Tomato", "disease": "Tomato Blight", "confidence": 0.88, "status": "Moderate-confidence model prediction", "severity": "Severe"},
        "management": {"available": True, "immediate_actions": []},
        "is_healthy": False,
        "crop_key": "tomato",
        "source": "DB"
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")}, data={"crop": "Tomato"})
    
    assert response.status_code == 200
    assert response.json()["prediction"]["disease"] == "Tomato Blight"

def test_low_confidence_leaf(mock_yolo):
    """3. Low-confidence leaf (<0.50 confidence)"""
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Not determined", "disease": "Unknown", "confidence": 0.40, "status": "uncertain", "severity": "None"},
        "management": {"available": False},
        "is_healthy": False,
        "crop_key": None,
        "source": None
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")})
    
    assert response.status_code == 200
    assert response.json()["prediction"]["status"] == "uncertain"
    assert response.json()["prediction"]["disease"] == "Unknown"
    assert response.json()["fertilizer"]["available"] == False

def test_missing_soil_npk(mock_yolo):
    """4. Missing soil NPK (tests fertilizer rec logic in disease.py)"""
    # Overriding DB mock to return NO soil test
    class MockSessionNoSoil(MockSession):
        def query(self, *args, **kwargs):
            mock_query = MagicMock()
            mock_farm = Farm(id=1, farmer_id=1)
            def filter_side_effect(*f_args, **f_kwargs):
                m = MagicMock()
                def first_side_effect():
                    if args[0] == Farm:
                        return mock_farm
                    return None
                m.first = first_side_effect
                m.order_by.return_value = m
                return m
            mock_query.filter.side_effect = filter_side_effect
            return mock_query

    app.dependency_overrides[get_db] = lambda: MockSessionNoSoil()
    
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Apple", "disease": "Apple Scab", "confidence": 0.95, "status": "High", "severity": "Moderate"},
        "management": {"available": True},
        "is_healthy": False,
        "crop_key": "apple",
        "source": "DB"
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")})
    
    assert response.status_code == 200
    assert response.json()["fertilizer"]["available"] == False
    assert response.json()["fertilizer"]["reason"] == "missing_soil"
    
    # Restore DB override
    app.dependency_overrides[get_db] = override_get_db

def test_completely_black_image():
    """5. Completely black image (basic validation fail)"""
    # Test the real YOLO agent directly to see basic validation
    from app.ml.yolo_disease_agent import YOLODiseaseClassifier
    agent = YOLODiseaseClassifier()
    img = Image.new("RGB", (100, 100), color=(0, 0, 0)) # All black
    res = agent.predict(img)
    
    assert res["success"] == False
    assert res["reason"] == "invalid_image"

def test_no_bounding_boxes_but_is_leaf():
    """6. No bounding boxes but is_leaf=True (Healthy)"""
    from app.ml.yolo_disease_agent import YOLODiseaseClassifier
    agent = YOLODiseaseClassifier()
    agent.leaf_validator = MagicMock()
    agent.leaf_validator.validate_leaf.return_value = {"is_leaf": True}
    
    # Mock model to return empty boxes
    agent.model = MagicMock()
    mock_result = MagicMock()
    mock_result.probs = None
    mock_result.boxes = []
    agent.model.return_value = [mock_result]
    
    img = Image.open(create_dummy_image())
    res = agent.predict(img)
    
    assert res["success"] == True
    assert res["prediction"]["disease"] == "Healthy"
    assert res["prediction"]["status"] == "No visible disease detected by the model."

def test_no_bounding_boxes_and_not_leaf():
    """7. No bounding boxes and is_leaf=False (Uncertain)"""
    from app.ml.yolo_disease_agent import YOLODiseaseClassifier
    agent = YOLODiseaseClassifier()
    agent.leaf_validator = MagicMock()
    agent.leaf_validator.validate_leaf.return_value = {"is_leaf": False}
    
    agent.model = MagicMock()
    mock_result = MagicMock()
    mock_result.probs = None
    mock_result.boxes = []
    agent.model.return_value = [mock_result]
    
    img = Image.open(create_dummy_image())
    res = agent.predict(img)
    
    assert res["success"] == True
    assert res["prediction"]["status"] == "uncertain"
    assert res["prediction"]["disease"] == "Unknown"

def test_unsupported_crop(mock_yolo):
    """8. Unsupported crop"""
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Not determined", "disease": "Unknown", "confidence": 0.0, "status": "uncertain", "severity": "None"},
        "management": {"available": False},
        "is_healthy": False,
        "crop_key": None,
        "source": None
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")}, data={"crop": "AlienCrop"})
    
    assert response.status_code == 200
    assert response.json()["prediction"]["status"] == "uncertain"

def test_valid_healthy_leaf(mock_yolo):
    """9. Valid healthy leaf"""
    mock_yolo.return_value = {
        "success": True,
        "prediction": {"crop": "Apple", "disease": "Healthy", "confidence": 0.98, "status": "No visible disease detected by the model.", "severity": "None"},
        "management": {"available": True},
        "is_healthy": True,
        "crop_key": "apple",
        "source": "DB"
    }
    
    file = create_dummy_image()
    response = client.post("/api/v1/disease/scan", files={"file": ("test.jpg", file, "image/jpeg")})
    
    assert response.status_code == 200
    assert response.json()["prediction"]["status"] == "No visible disease detected by the model."
    assert response.json()["prediction"]["severity"] == "None"

def test_missing_leaf_unrelated_object():
    """10. Missing leaf (e.g. unrelated object) with no boxes"""
    from app.ml.yolo_disease_agent import YOLODiseaseClassifier
    agent = YOLODiseaseClassifier()
    agent.leaf_validator = MagicMock()
    agent.leaf_validator.validate_leaf.return_value = {"is_leaf": False}
    
    agent.model = MagicMock()
    mock_result = MagicMock()
    mock_result.probs = None
    mock_result.boxes = []
    agent.model.return_value = [mock_result]
    
    # Image that is an unrelated object, but passes basic non-uniformity check
    img = Image.new("RGB", (100, 100))
    import random
    pixels = img.load()
    for i in range(100):
        for j in range(100):
            pixels[i,j] = (random.randint(0,255), random.randint(0,255), random.randint(0,255))
            
    res = agent.predict(img)
    
    assert res["success"] == True
    assert res["prediction"]["status"] == "uncertain"
