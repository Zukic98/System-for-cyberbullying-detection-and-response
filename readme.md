# System-for-cyberbullying-detection-and-response

A full-stack application designed for detecting and responding to cyberbullying behavior. The project features a responsive React frontend powered by Vite and a high-performance Python backend built with FastAPI that utilizes Machine Learning models for real-time text analysis.

---

## 🚀 How to Run the Application Locally

Follow these steps to successfully set up and run both the backend and frontend environments on your machine.

### Prerequisites
Before you begin, make sure you have the following installed on your system:
* **Node.js** (v18 or higher recommended)
* **Python 3.x**

### 1. Cloning the Repository
Clone the repository and navigate into the project's root folder:
```bash
git clone [https://github.com/Zukic98/System-for-cyberbullying-detection-and-response.git](https://github.com/Zukic98/System-for-cyberbullying-detection-and-response.git)
cd System-for-cyberbullying-detection-and-response

### 2. Set & run backend

cd backend
python -m venv venv
# Activate venv:
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
mkdir models
# Download ML models from Google Drive and place them in backend/models/
python app.py

### 3. Set and run frontend
cd frontend
npm install
npm run dev

Localhosts:

Frontend: http://localhost:5173

Backend API: http://localhost:8000

API Docs: http://localhost:8000/docs