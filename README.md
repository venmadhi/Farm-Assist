# Farm-Assist
> **An Explainable Multi-Agent AI Framework for Personalized and Profit-Oriented Agricultural Decision Support for Kerala Farmers**
> *Domain: Artificial Intelligence + Machine Learning + Computer Vision + NLP + Precision Agriculture*

---

AgriGenie AI is an advanced agricultural decision intelligence platform designed to replace generic, lookup-table farming suggestions with personalized, climate-resilient, explainable, and profitable actions.

It establishes a **Farmer Digital Twin** to track land history, soil health, and past yields, and orchestrates 5 specialized AI agents to generate unified farming decisions.

---

## 1. Core Innovations (SIH & B.Tech Showcase)

*   **Farmer Digital Twin (FDT):** A virtual profile logging soil quality metrics, regional climate data, and yields. The database acts as a memory buffer allowing the model to adapt and learn dynamically from farmer ratings and comments.
*   **Explainable AI (XAI) via SHAP:** Rather than presenting "black box" recommendations, AgriGenie calculates Shapley values for Nitrogen (N), Phosphorus (P), Potassium (K), and climate variables, showing farmers exactly how each parameter contributed to a crop recommendation.
*   **Bilingual RAG Advisory Chatbot:** Integrates Kerala Agricultural University (KAU) Package of Practices into a vector context search. Supports bilingual queries (English & Malayalam) with built-in Web Speech API voice dictation.
*   **HSV Crop Disease Severity Analysis:** Couples MobileNetV2 image classification with an OpenCV color-segmentation algorithm that measures the percentage of leaves affected by necrosis to calculate low/medium/severe damage levels.
*   **Market Profit Regression Forecast:** Combines seasonal trends (such as Onam banana price spikes) and cultivation budgets to forecast profit margins per acre.

---

## 2. Multi-Agent System Architecture

```
                  +----------------------------------------------+
                  |                 Farmer User                  |
                  +----------------------+-----------------------+
                                         |
                                         v
                  +----------------------+-----------------------+
                  |         React.js + Tailwind Frontend         |
                  +----------------------+-----------------------+
                                         | (REST APIs / JWT)
                                         v
                  +----------------------+-----------------------+
                  |          FastAPI Backend API Layer           |
                  +----------------------+-----------------------+
                                         |
                                         v
                  +----------------------+-----------------------+
                  |        Multi-Agent Orchestrator Layer        |
                  +-----------+----------+-----------+-----------+
                              |          |           |
       +----------------------+          |           +-----------------------+
       |                                 v                                   |
+------v-----------------+     +---------v------------+     +----------------v-------+
|  Crop Intelligence     |     |  Disease Detection   |     |    Smart Fertilizer    |
|  Agent (RF/XGBoost)    |     |  Agent (MobileNetV2) |     |    Agent (Rule + ML)   |
+------+-----------------+     +---------+------------+     +----------------+-------+
       |                                 |                                   |
       |                                 v                                   |
       |                       +---------v------------+                      |
       |                       | Market Intelligence  |                      |
       |                       |   Agent (Regression) |                      |
       |                       +---------+------------+                      |
       |                                 |                                   |
       +---------------------------------+-----------------------------------+
                                         |
                                         v
                  +----------------------+-----------------------+
                  |       Explainable Decision Fusion Engine     |
                  |          (SHAP + Recommendation Logic)       |
                  +----------------------+-----------------------+
                                         |
                                         v
                  +----------------------+-----------------------+
                  |            SQLite / PostgreSQL               |
                  |  (Digital Twin, Crop History, Feedback Loops) |
                  +----------------------------------------------+
```

---

## 3. Project File Structure

```
c:/Users/venmadhi/FinalYear Project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Security & DB configurations
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models.py            # Database tables
│   │   ├── schemas.py           # Pydantic validation schemas
│   │   ├── routers/
│   │   │   ├── auth.py          # JWT authentication
│   │   │   ├── profile.py       # Farmer Profile & Digital Twin
│   │   │   ├── crop.py          # Crop Agent APIs
│   │   │   ├── disease.py       # Leaf Disease Agent APIs
│   │   │   ├── fertilizer.py    # Fertilizer Agent APIs
│   │   │   ├── chatbot.py       # Chatbot Advisor API
│   │   │   └── market.py        # Price trends API
│   │   ├── ml/
│   │   │   ├── train_crop.py    # RF model training pipeline
│   │   │   ├── crop_agent.py    # Crop Inference & SHAP
│   │   │   ├── disease_agent.py # CV leaf analyzer & HSV thresholding
│   │   │   ├── fertilizer_agent.py # NPK scheduler rules
│   │   │   └── market_agent.py  # Market economics simulator
│   │   └── knowledge_base/
│   │       ├── kerala_agriculture_kb.json # Agricultural practices guidelines
│   │       └── rag_engine.py    # Context matching and LLM prompts
│   ├── requirements.txt         # Backend Python packages
│   └── tests/
│       └── test_agents.py       # Unit tests for ML/Rule agents
├── frontend/
│   ├── tailwind.config.js       # Custom agricultural styles
│   ├── src/
│   │   ├── App.jsx              # Main React routing
│   │   ├── utils/
│   │   │   └── api.js           # Axios REST services
│   │   ├── components/
│   │   │   ├── Sidebar.jsx      # Portal side navigation
│   │   │   ├── Navbar.jsx       # Environmental weather widget header
│   │   │   ├── StatCard.jsx     # Reusable dashboard KPIs
│   │   │   └── SHAPChart.jsx    # Explainable AI bars
│   │   └── pages/
│   │       ├── Dashboard.jsx    # Farmer Digital Twin
│   │       ├── CropRecommendation.jsx # Crop predictor & XAI
│   │       ├── DiseaseScanner.jsx # Plant disease computer vision
│   │       ├── FertilizerOptimizer.jsx # Smart NPK dose scheduler
│   │       ├── MarketAnalysis.jsx # Pricing forecasts & budgets
│   │       └── AICompanion.jsx  # Malayalam voice enabled chat
└── README.md
```

---

## 4. Installation & Setup

Ensure you have **Python 3.10+** and **Node.js 18+** installed.

### A. Backend Setup
1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Install Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Crop model training script to generate the trained classifier binary:
   ```bash
   python app/ml/train_crop.py
   ```
4. Start the FastAPI development server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```
   *The interactive Swagger documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).*

### B. Frontend Setup
1. Open a new terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Launch the Vite local hot-reload server:
   ```bash
   npm run dev
   ```
   *Open your browser and navigate to [http://localhost:5173](http://localhost:5173).*

---

## 5. Walkthrough Guide (Demonstration Steps)

1.  **Register a Land Profile:** Navigate to the registration page. Create a farmer profile (e.g. name, phone, select district "Idukki", soil "Laterite", land size "2.5 Acres").
2.  **Inspect the Digital Twin Dashboard:** View details on soil warnings, NPK trends, and log a previous crop harvest.
3.  **Run Crop Suitability Intelligence:** Open the Crop Intelligence tab. 
    *   Click the **"Kuttanad Clay (Paddy-ready)"** preset button to populate mock soil metrics.
    *   Click **Compute Optimal Crop**. Watch the model suggest Paddy cultivation, show the yield index, display the SHAP graph explaining *why* nitrogen and moisture were positive drivers, and provide a feedback form.
4.  **Scan an Leaf for Plant Diseases:** Go to the Disease Scanner page.
    *   Click any of the **SIH Shortcut buttons** (e.g. *Quick Wilt decay in Pepper*).
    *   A simulated leaf with matching spots is dynamically rendered and uploaded.
    *   Observe the OpenCV-calculated leaf affected area ratio, the MobileNetV2 classification (Quick Wilt), and the detailed chemical/biological treatment plan.
5.  **Calculate Smart NPK fertilizer Schedules:** Open the Smart Fertilizer tab. Select "Banana", input your custom NPK soil test levels, and inspect the split vegetative and yielding schedules, including wood ash and organic alternatives.
6.  **Forecast Market Prices:** Open the Market Price Forecast tab. Change the crop to "Banana" or "Cardamom" and inspect the price fluctuations, cost sheets, and the Recharts historical monthly price graph.
7.  **Consult the AI Advisor:** Go to the AI Companion tab.
    *   Toggle the microphone button to dictate questions verbally (Malayalam supported in Chrome/Edge).
    *   Type or ask: *"How to make Jeevamrutham?"* or *"വാഴയിലെ പിണ്ടിഉണ്ണി തടയാൻ എന്തുചെയ്യണം?"*.
    *   Observe the bilingual retrieved response pulled directly from the local guidelines database.
