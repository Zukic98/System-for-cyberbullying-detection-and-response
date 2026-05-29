# backend/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
import re
import numpy as np
import os
import csv
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from topic_analyzer import TopicAnalyzer

# =====================================================================
# INITIALIZATION
# =====================================================================
app = FastAPI(title="Cyberbullying Detection API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
MODELS_PATH = os.path.join(os.path.dirname(__file__), 'models')
TOKENIZER = AutoTokenizer.from_pretrained('distilbert-base-uncased')

print(f"⚡ Device: {DEVICE}")
print(f"📂 Models path: {MODELS_PATH}")

# =====================================================================
# LOAD MODELS
# =====================================================================
print("\n📥 Loading models...")

models = {}

# Model 1: Jigsaw
print("   Loading Model 1 (Jigsaw)...")
models['jigsaw'] = AutoModelForSequenceClassification.from_pretrained(
    os.path.join(MODELS_PATH, 'model_1_jigsaw'), local_files_only=True
).to(DEVICE).eval()

# Model 2: Cyberbullying Type
print("   Loading Model 2 (Cyberbullying Type)...")
models['cyberbullying'] = AutoModelForSequenceClassification.from_pretrained(
    os.path.join(MODELS_PATH, 'model_2_cyberbullying'), local_files_only=True
).to(DEVICE).eval()
mapping_2 = np.load(os.path.join(MODELS_PATH, 'model_2_mapping.npy'), allow_pickle=True).item()
inv_mapping_2 = {v: k for k, v in mapping_2.items()}

# Model 3: Davidson Hate Speech
print("   Loading Model 3 (Davidson)...")
models['hate_speech'] = AutoModelForSequenceClassification.from_pretrained(
    os.path.join(MODELS_PATH, 'model_3_davidson'), local_files_only=True
).to(DEVICE).eval()

# Model 4: Formspring
print("   Loading Model 4 (Formspring)...")
models['implicit'] = AutoModelForSequenceClassification.from_pretrained(
    os.path.join(MODELS_PATH, 'model_4_formspring'), local_files_only=True
).to(DEVICE).eval()

# Model 5: OffensEval
print("   Loading Model 5 (OffensEval)...")
models['target'] = AutoModelForSequenceClassification.from_pretrained(
    os.path.join(MODELS_PATH, 'model_5_offenseval'), local_files_only=True
).to(DEVICE).eval()
mapping_5 = np.load(os.path.join(MODELS_PATH, 'model_5_mapping.npy'), allow_pickle=True).item()
inv_mapping_5 = {v: k for k, v in mapping_5.items()}

# Model Topic Analyzer
print("\n📥 Loading Topic Analyzer...")
topic_analyzer = TopicAnalyzer("./models/topic_model")

print("✅ All models loaded successfully!")

# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'http\S+|www\S+', '[URL]', text)
    text = re.sub(r'@\w+', '@USER', text)
    text = re.sub(r'[^a-zA-Z\s!?.,\']', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text):
    enc = TOKENIZER(text, max_length=128, padding='max_length', truncation=True, return_tensors='pt')
    return {k: v.to(DEVICE) for k, v in enc.items()}

# =====================================================================
# API MODELS
# =====================================================================
class TextInput(BaseModel):
    text: str

class AdminFeedbackRequest(BaseModel):
    original_text: str
    model_decision: str
    model_score: float
    user_verdict: str  # 'BULLYING_DETECTED' or 'SAFE'
    topic_category: str = None
    model_predictions: dict = None

# =====================================================================
# FEEDBACK SYSTEM
# =====================================================================
FEEDBACK_FILE = "./data/admin_feedback.csv"

# Create folder and file if they don't exist
os.makedirs("./data", exist_ok=True)
if not os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'original_text', 'model_decision', 'model_score', 'user_verdict', 'topic_category', 'model_predictions'])

# =====================================================================
# ENDPOINT: Complete Analysis
# =====================================================================
@app.post("/api/analyze")
async def analyze_text(input: TextInput):
    text = input.text
    clean = clean_text(text)
    tokens = tokenize(clean)
    
    results = {}
    
    with torch.no_grad():
        # Model 1: Jigsaw
        out1 = torch.sigmoid(models['jigsaw'](**tokens).logits).cpu().numpy()[0]
        jigsaw_labels = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate']
        jigsaw = {l: round(float(out1[i]), 4) for i, l in enumerate(jigsaw_labels)}
        results['jigsaw'] = jigsaw
        
        # Model 2: Cyberbullying Type
        out2 = torch.softmax(models['cyberbullying'](**tokens).logits, dim=1).cpu().numpy()[0]
        pred2 = int(np.argmax(out2))
        results['cyberbullying'] = {
            'type': inv_mapping_2[pred2],
            'is_bullying': inv_mapping_2[pred2] != 'not_cyberbullying',
            'confidence': round(float(out2[pred2]), 4)
        }
        
        # Model 3: Hate Speech
        out3 = torch.softmax(models['hate_speech'](**tokens).logits, dim=1).cpu().numpy()[0]
        results['hate_speech'] = {
            'hate': round(float(out3[0]), 4),
            'offensive': round(float(out3[1]), 4),
            'neutral': round(float(out3[2]), 4)
        }
        
        # Model 4: Implicit Bullying
        out4 = torch.softmax(models['implicit'](**tokens).logits, dim=1).cpu().numpy()[0]
        results['implicit'] = {
            'bullying_prob': round(float(out4[1]), 4),
            'neutral_prob': round(float(out4[0]), 4)
        }
        
        # Model 5: Target
        out5 = torch.softmax(models['target'](**tokens).logits, dim=1).cpu().numpy()[0]
        pred5 = int(np.argmax(out5))
        ind_idx = mapping_5.get('IND', None)
        grp_idx = mapping_5.get('GRP', None)
        results['target'] = {
            'type': inv_mapping_5[pred5],
            'individual_prob': round(float(out5[ind_idx]), 4) if ind_idx is not None else 0,
            'group_prob': round(float(out5[grp_idx]), 4) if grp_idx is not None else 0
        }

    topic_analysis = None
    # Only if bullying is detected
    if results['cyberbullying']['is_bullying'] or results['hate_speech']['hate'] > 0.3 or results['jigsaw']['toxic'] > 0.5:
        topic_analysis = topic_analyzer.analyze_text(clean)    
    
    # Rule Engine Score
    score = (
        jigsaw['toxic'] * 0.10 + jigsaw['severe_toxic'] * 0.25 + 
        jigsaw['threat'] * 0.25 + jigsaw['identity_hate'] * 0.20 +
        jigsaw['obscene'] * 0.10 + jigsaw['insult'] * 0.10
    )
    
    if results['hate_speech']['hate'] > 0.5: score += 0.20
    elif results['hate_speech']['offensive'] > 0.5: score += 0.10
    if results['cyberbullying']['is_bullying']: score += 0.10
    if results['implicit']['bullying_prob'] > 0.6: score += 0.10
    if results['target']['type'] in ['IND', 'GRP']: score += 0.10
    
    # Expert rules
    text_lower = text.lower()
    threat_patterns = [
        r'\b(i|i\'ll)\s+(kill|murder|hurt|destroy)\s+(you|u)\b',
        r'\b(kill|hang)\s+(yourself|urself)\b',
    ]
    direct_threat = any(re.search(p, text_lower) for p in threat_patterns)
    if direct_threat: score += 0.25
    
    score = min(score, 1.0)
    
    # Decision
    if direct_threat: decision = 'BULLYING_DETECTED'
    elif score >= 0.30: decision = 'BULLYING_DETECTED'
    elif score >= 0.12: decision = 'ADMIN_REVIEW'
    else: decision = 'SAFE'
    
    return {
        'decision': decision,
        'score': round(score, 4),
        'direct_threat': direct_threat,
        'models': results,
        'topic_analysis': topic_analysis,
        'original_text': text,
        'cleaned_text': clean
    }

# =====================================================================
# ENDPOINT: Sentiment
# =====================================================================
@app.post("/api/sentiment")
async def analyze_sentiment(input: TextInput):
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        vader = SentimentIntensityAnalyzer()
        scores = vader.polarity_scores(input.text)
        
        return {
            'compound': scores['compound'],
            'sentiment': 'positive' if scores['compound'] > 0.05 else ('negative' if scores['compound'] < -0.05 else 'neutral'),
            'positive': scores['pos'],
            'negative': scores['neg'],
            'neutral': scores['neu'],
        }
    except ImportError:
        return {
            'compound': 0, 'sentiment': 'neutral',
            'positive': 0, 'negative': 0, 'neutral': 1,
            'error': 'vaderSentiment not installed'
        }

# =====================================================================
# ENDPOINT: NER
# =====================================================================
@app.post("/api/ner")
async def extract_entities(input: TextInput):
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(input.text)
        
        entities = {'PER': [], 'LOC': [], 'ORG': [], 'MISC': []}
        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append({'text': ent.text, 'label': ent.label_})
            elif ent.label_ == 'GPE':
                entities['LOC'].append({'text': ent.text, 'label': 'GPE'})
        
        return {'entities': entities, 'total': sum(len(v) for v in entities.values())}
    except:
        return {'entities': {'PER': [], 'LOC': [], 'ORG': [], 'MISC': []}, 'total': 0, 'error': 'spaCy not installed'}

# =====================================================================
# ENDPOINT: Chatbot Support
# =====================================================================
@app.post("/api/support")
async def generate_support(input: TextInput):
    # First analyze
    analysis = await analyze_text(input)
    
    score = analysis['score']
    
    if analysis['decision'] == 'BULLYING_DETECTED':
        if score > 0.7:
            support_message = (
                "🚨 I'm sorry you're experiencing this. "
                "This is a SERIOUS form of cyberbullying. "
                "YOU ARE NOT TO BLAME. "
                "I suggest: 1) Block the person, 2) Save evidence, "
                "3) Report to the platform, 4) Talk to a trusted adult. 💙"
            )
        else:
            support_message = (
                "😟 I'm sorry you experienced this. "
                "Your feeling is valid. "
                "Block the person and report the content. "
                "If you need to talk, I'm here. 💚"
            )
    elif analysis['decision'] == 'ADMIN_REVIEW':
        support_message = (
            "🤔 This content is on the borderline. "
            "If it's bothering you, report it. "
            "Don't ignore your feelings. 💛"
        )
    else:
        support_message = (
            "✅ This text shows no indicators of cyberbullying. "
            "If you're still concerned, share more details. 😊"
        )
    
    resources = [
        {"name": "📞 Helpline", "value": "0800-300-303"},
        {"name": "🔗 Report Violence", "value": "https://www.netprijava.rs/"},
        {"name": "📖 Safety Guide", "value": "https://www.unicef.org/serbia/"},
    ]
    
    safety_tips = [
        "🔒 Block the person harassing you",
        "📸 Take screenshots as evidence",
        "🚨 Report the content to the platform",
        "💬 Talk to a trusted adult",
        "🧠 Don't blame yourself - bullying is the bully's choice",
    ]
    
    return {
        'message': support_message,
        'resources': resources,
        'safety_tips': safety_tips,
        'analysis': analysis
    }

# =====================================================================
# ENDPOINT: Summarization
# =====================================================================
@app.post("/api/summarize")
async def summarize_text(input: TextInput):
    # Simple extractive summarization
    sentences = re.split(r'(?<=[.!?])\s+', input.text)
    sentences = [s for s in sentences if len(s) > 10]
    
    if len(sentences) <= 3:
        summary = input.text
    else:
        # Take first, middle, and last sentence
        mid = len(sentences) // 2
        selected = [sentences[0], sentences[mid], sentences[-1]]
        summary = ' '.join(selected)
    
    return {
        'original_length': len(input.text),
        'summary_length': len(summary),
        'summary': summary,
        'compression_ratio': round(len(summary) / max(len(input.text), 1) * 100, 1)
    }

# =====================================================================
# ENDPOINT: Health Check
# =====================================================================
@app.get("/api/health")
async def health_check():
    return {
        'status': 'healthy',
        'models_loaded': len(models),
        'device': str(DEVICE)
    }

# =====================================================================
# ENDPOINT: Test Topic Model
# =====================================================================
@app.get("/api/test-topic")
async def test_topic():
    """Test endpoint for topic model verification"""
    test_text = "You are so ugly and stupid"
    
    if 'topic_analyzer' in globals() and topic_analyzer.topic_model is not None:
        result = topic_analyzer.analyze_text(test_text)
        return {
            "status": "loaded",
            "test_result": result,
            "model_path": topic_analyzer.model_path
        }
    else:
        return {
            "status": "not_loaded",
            "error": "Topic model not loaded"
        }

# =====================================================================
# FEEDBACK ENDPOINTS
# =====================================================================

@app.post("/api/admin-feedback")
async def submit_admin_feedback(feedback: AdminFeedbackRequest):
    """Store user feedback for ADMIN_REVIEW cases"""
    
    with open(FEEDBACK_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            feedback.original_text,
            feedback.model_decision,
            feedback.model_score,
            feedback.user_verdict,
            feedback.topic_category or '',
            str(feedback.model_predictions) if feedback.model_predictions else ''
        ])
    
    print(f"📝 Admin feedback saved: {feedback.user_verdict} for: {feedback.original_text[:50]}...")
    
    # Count collected feedback
    with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
        count = sum(1 for _ in f) - 1
    
    return {
        "status": "success", 
        "message": "Feedback saved",
        "total_feedback": count,
        "suggestion": "After 50-100 feedback entries, you can run fine-tuning"
    }

@app.get("/api/feedback-stats")
async def get_feedback_stats():
    """Return statistics about collected feedback"""
    if not os.path.exists(FEEDBACK_FILE):
        return {"total": 0, "bullying": 0, "safe": 0, "needs_finetune": False}
    
    import pandas as pd
    df = pd.read_csv(FEEDBACK_FILE)
    total = len(df)
    return {
        "total": total,
        "bullying": len(df[df['user_verdict'] == 'BULLYING_DETECTED']),
        "safe": len(df[df['user_verdict'] == 'SAFE']),
        "needs_finetune": total >= 50
    }

# =====================================================================
# RUN SERVER
# =====================================================================
if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 CYBERBULLYING DETECTION SYSTEM")
    print("="*60)
    print(f"📡 Server: http://localhost:8000")
    print(f"📖 API Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)