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
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification, pipeline
from topic_analyzer import TopicAnalyzer
from chatbot_llm import LLMChatbotV2 as LLMChatbot
from incident_sumarizator import IncidentSumarizator

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
os.makedirs(MODELS_PATH, exist_ok=True)

if not os.path.isdir(MODELS_PATH):
    raise RuntimeError(
        f"Missing backend models folder: {MODELS_PATH}.\n"
        "Create the folder and place the downloaded model directories there."
    )

TOKENIZER = AutoTokenizer.from_pretrained('distilbert-base-uncased')

print(f"⚡ Device: {DEVICE}")
print(f"📂 Models path: {MODELS_PATH}")


def local_model_path(model_name):
    model_path = os.path.join(MODELS_PATH, model_name)
    if not os.path.isdir(model_path):
        raise FileNotFoundError(
            f"Local model directory not found: {model_path}.\n"
            "Download the model and place it under backend/models/."
        )
    return model_path

# =====================================================================
# LOAD MODELS
# =====================================================================
print("\n📥 Loading models...")

models = {}

# Model 1: Jigsaw
print("   Loading Model 1 (Jigsaw)...")
models['jigsaw'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_1_jigsaw'), local_files_only=True
).to(DEVICE).eval()

# Model 2: Cyberbullying Type
print("   Loading Model 2 (Cyberbullying Type)...")
models['cyberbullying'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_2_cyberbullying'), local_files_only=True
).to(DEVICE).eval()
mapping_2 = np.load(os.path.join(MODELS_PATH, 'model_2_mapping.npy'), allow_pickle=True).item()
inv_mapping_2 = {v: k for k, v in mapping_2.items()}

# Model 3: Davidson Hate Speech
print("   Loading Model 3 (Davidson)...")
models['hate_speech'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_3_davidson'), local_files_only=True
).to(DEVICE).eval()

# Model 4: Formspring
print("   Loading Model 4 (Formspring)...")
models['implicit'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_4_formspring'), local_files_only=True
).to(DEVICE).eval()

# Model 5: OffensEval
print("   Loading Model 5 (OffensEval)...")
models['target'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_5_offenseval'), local_files_only=True
).to(DEVICE).eval()
mapping_5 = np.load(os.path.join(MODELS_PATH, 'model_5_mapping.npy'), allow_pickle=True).item()
inv_mapping_5 = {v: k for k, v in mapping_5.items()}

# Model GoEmotions 
print("   Loading Model 6 (GoEmotions)...")
models['goemotions'] = AutoModelForSequenceClassification.from_pretrained(
    local_model_path('model_goemotions'), local_files_only=True
).to(DEVICE).eval()

# Lista svih 28 emocija tačno onim redoslijedom kako ih GoEmotions dataset ima registrirane
GO_EMOTIONS_LABELS = [
    "admiration", "amusement", "anger", "annoyance", "approval", "caring",
    "confusion", "curiosity", "desire", "disappointment", "disapproval",
    "disgust", "embarrassment", "excitement", "fear", "gratitude", "grief",
    "joy", "love", "nervousness", "optimism", "pride", "realization",
    "relief", "remorse", "sadness", "surprise", "neutral"
]

# Model Topic Analyzer
print("\n📥 Loading Topic Analyzer...")
topic_analyzer = TopicAnalyzer("./models/topic_model")

def ensure_local_ner_model(repo_id: str, local_dir: str):
    if os.path.isdir(local_dir):
        return local_dir

    os.makedirs(local_dir, exist_ok=True)
    print(f"Downloading NER model {repo_id} into {local_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    tokenizer.save_pretrained(local_dir)
    model = AutoModelForTokenClassification.from_pretrained(repo_id)
    model.save_pretrained(local_dir)
    print(f"NER model downloaded and saved to {local_dir}")
    return local_dir

# Model 7: NER
print("   Loading NER model...")
NER_LOCAL_MODEL = os.path.join(MODELS_PATH, 'ner_davlan_bert_base_multilingual_cased_ner_hrl')
NER_MODEL_NAME = NER_LOCAL_MODEL
if not os.path.isdir(NER_LOCAL_MODEL):
    try:
        NER_MODEL_NAME = ensure_local_ner_model("Davlan/bert-base-multilingual-cased-ner-hrl", NER_LOCAL_MODEL)
    except Exception as e:
        print(f"Failed to download local NER model: {e}")
        NER_MODEL_NAME = "Davlan/bert-base-multilingual-cased-ner-hrl"

NER_DEVICE = 0 if torch.cuda.is_available() else -1
try:
    ner_pipeline = pipeline(
        "ner",
        model=NER_MODEL_NAME,
        aggregation_strategy="simple",
        device=NER_DEVICE
    )
    print(f"NER model loaded: {NER_MODEL_NAME} on device {NER_DEVICE}")
except Exception as e:
    ner_pipeline = None
    print(f"Failed to load NER model: {e}")

# Initialize abstractive summarizer (optional; may download model)
try:
    SUMMARIZER_LOCAL_MODEL = os.path.join(MODELS_PATH, 'bart_large_cnn')
    summarizer = IncidentSumarizator("facebook/bart-large-cnn", cache_dir=SUMMARIZER_LOCAL_MODEL)
    print("Summarizer loaded")
except Exception as e:
    summarizer = None
    print(f"Summarizer not available: {e}")

print("✅ All models loaded successfully!")

print("🤖 Initializing LLM Chatbot...")
llm_chatbot = LLMChatbot(model_name="llama3.2:3b", use_llm=True)
print("✅ LLM Chatbot initialized!")

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
# ENDPOINT: Sentiment / GoEmotions 
# =====================================================================
@app.post("/api/sentiment")
async def analyze_sentiment(input: TextInput):
    try:
        clean = clean_text(input.text)
        tokens = tokenize(clean)
        
        with torch.no_grad():
            logits = models['goemotions'](**tokens).logits
            probs = torch.sigmoid(logits).cpu().numpy()[0]
            
        emotions_result = {l: round(float(probs[i]), 4) for i, l in enumerate(GO_EMOTIONS_LABELS) if i < len(probs)}
        
        top_emotion = max(emotions_result, key=emotions_result.get)
        top_score = emotions_result[top_emotion]
        
      
        negative_emotions = ["anger", "annoyance", "disappointment", "disapproval", "disgust", "fear", "grief", "nervousness", "sadness", "remorse", "embarrassment"]

        positive_emotions = ["admiration", "amusement", "approval", "caring", "desire", "excitement", "gratitude", "joy", "love", "optimism", "relief", "pride"]

        pos_score = sum(emotions_result.get(e, 0.0) for e in positive_emotions)
        neg_score = sum(emotions_result.get(e, 0.0) for e in negative_emotions)
        neu_score = (
            emotions_result.get("neutral", 0.0) + 
            emotions_result.get("confusion", 0.0) + 
            emotions_result.get("curiosity", 0.0) + 
            emotions_result.get("surprise", 0.0) +
            emotions_result.get("realization", 0.0)
        )
                
        total_score = pos_score + neg_score + neu_score
        if total_score > 0:
            pos_pct = round(pos_score / total_score, 4)
            neg_pct = round(neg_score / total_score, 4)
            neu_pct = round(neu_score / total_score, 4)
        else:
            pos_pct, neg_pct, neu_pct = 0.0, 0.0, 1.0

        if top_emotion in negative_emotions:
            sentiment_category = 'negative'
        elif top_emotion in positive_emotions:
            sentiment_category = 'positive'
        else:
            sentiment_category = 'neutral'
            
        return {
            'compound': float(top_score) if sentiment_category == 'positive' else -float(top_score) if sentiment_category == 'negative' else 0,
            'sentiment': sentiment_category,
            'top_emotion': top_emotion,
            'confidence': float(top_score),
            'all_emotions': emotions_result,
            
            'positive': pos_pct,
            'negative': neg_pct,
            'neutral': neu_pct
        }
        
    except Exception as e:
        return {
            'compound': 0, 'sentiment': 'neutral', 'top_emotion': 'neutral', 'confidence': 0,
            'error': str(e)
        }

# =====================================================================
# ENDPOINT: NER
# =====================================================================
@app.post("/api/ner")
async def extract_entities(input: TextInput):
    if not input.text or ner_pipeline is None:
        return {'entities': {'PER': [], 'LOC': [], 'ORG': [], 'MISC': []}, 'total': 0}

    try:
        ner_output = ner_pipeline(input.text)
        entities = {'PER': [], 'LOC': [], 'ORG': [], 'MISC': []}

        for ent in ner_output:
            label = ent.get('entity_group') or ent.get('entity')
            text = ent.get('word') or ent.get('entity')

            if label in ['PER', 'PERSON']:
                group = 'PER'
            elif label in ['LOC', 'GPE', 'LOCATION']:
                group = 'LOC'
            elif label in ['ORG', 'ORGANIZATION']:
                group = 'ORG'
            else:
                group = 'MISC'

            entities[group].append({
                'text': text,
                'label': label,
                'score': round(float(ent.get('score', 0.0)), 4),
                'start': ent.get('start'),
                'end': ent.get('end')
            })

        return {'entities': entities, 'total': sum(len(v) for v in entities.values())}
    except Exception as e:
        return {'entities': {'PER': [], 'LOC': [], 'ORG': [], 'MISC': []}, 'total': 0, 'error': str(e)}

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
    # Prefer abstractive summarizer when available
    if 'summarizer' in globals() and summarizer is not None:
        try:
            summary = summarizer.generisi_izvjestaj(input.text)
            return {
                'original_length': len(input.text),
                'summary_length': len(summary),
                'summary': summary,
                'method': 'abstractive'
            }
        except Exception as e:
            print(f"Summarizer error: {e}")

    # Fallback: simple extractive summarization
    sentences = re.split(r'(?<=[.!?])\s+', input.text)
    sentences = [s for s in sentences if len(s) > 10]

    if len(sentences) <= 3:
        summary = input.text
    else:
        mid = len(sentences) // 2
        selected = [sentences[0], sentences[mid], sentences[-1]]
        summary = ' '.join(selected)

    return {
        'original_length': len(input.text),
        'summary_length': len(summary),
        'summary': summary,
        'method': 'extractive'
    }


# =====================================================================
# ENDPOINT: Summarize Chat Transcript (on-demand)
# =====================================================================
@app.post("/api/summarize_chat")
async def summarize_chat(payload: dict):
    """Expect payload: {"messages": [{"role": "user"|"bot", "text": "..."}, ...]}"""
    messages = payload.get('messages') if isinstance(payload, dict) else None
    if not messages or not isinstance(messages, list):
        return {
            'error': 'Invalid payload. Expected {"messages": [{"role","text"}, ...]}'
        }

    # Build a single text blob from messages, preserving role context
    parts = []
    for m in messages:
        role = m.get('role', 'user')
        text = m.get('text', '')
        if not text:
            continue
        prefix = 'User: ' if role == 'user' else 'Assistant: '
        parts.append(prefix + text)

    transcript = '\n'.join(parts).strip()
    if not transcript:
        return {'error': 'Empty transcript'}

    # Prefer abstractive summarizer when available
    if 'summarizer' in globals() and summarizer is not None:
        try:
            summary = summarizer.generisi_izvjestaj(transcript)
            return {
                'original_length': len(transcript),
                'summary_length': len(summary),
                'summary': summary,
                'method': 'abstractive'
            }
        except Exception as e:
            print(f"Summarizer error (chat): {e}")

    # Fallback extractive: pick first, middle, last substantive sentences
    sentences = re.split(r'(?<=[.!?])\s+', transcript)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    if len(sentences) <= 3:
        summary = transcript
    else:
        mid = len(sentences) // 2
        selected = [sentences[0], sentences[mid], sentences[-1]]
        summary = ' '.join(selected)

    return {
        'original_length': len(transcript),
        'summary_length': len(summary),
        'summary': summary,
        'method': 'extractive'
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
# ENDPOINT: Start chat after analysis
# =====================================================================
@app.post("/api/chat/start")
async def start_chat(input: TextInput):
    # Prvo analiziraj tekst
    analysis = await analyze_text(input)
    sentiment = await analyze_sentiment(input)
    ner = await extract_entities(input)  # ← DODAJ NER
    
    # Pripremi analysis za chatbot (sa SVE informacije)
    topic_analysis = topic_analyzer.analyze_text(clean_text(input.text)) or {}
    
    EMOTION_MAP = {
    "outrage":        "anger",
    "annoyance":      "anger",
    "disapproval":    "anger",
    "disgust":        "anger",
    "fear":           "fear",
    "nervousness":    "nervousness",
    "grief":          "grief",
    "sadness":        "sadness",
    "disappointment": "disappointment",
    "embarrassment":  "sadness",
    "remorse":        "sadness",
    "embarrassment":  "embarrassment",
}

    chat_analysis = {
        'emotion': EMOTION_MAP.get(sentiment.get('top_emotion', 'unknown'), 'default'),
        'topic': topic_analysis.get('topic_category', 'general'),
        'topic_category': topic_analysis.get('topic_category', 'general'),
        'topic_keywords': topic_analysis.get('keywords', []),
        'topic_severity': topic_analysis.get('severity', 2),
        'decision': analysis['decision'],
        'score': analysis['score'],
        'entities': ner.get('entities', {})  # ← DODAJ ENTITETE
    }

    
    # Create chat session
    session_id = llm_chatbot.sessions.create_session(chat_analysis)
    
    # Generate first message
    first_message = llm_chatbot.generate_first_message(chat_analysis)
    
    return {
        'session_id': session_id,
        'first_message': first_message,
        'analysis': chat_analysis
    }

# =====================================================================
# ENDPOINT: Continue chat
# =====================================================================
@app.post("/api/chat/message")
async def chat_message(request: dict):
    """
    Send a message in an existing chat session
    """
    session_id = request.get('session_id')
    user_message = request.get('message')
    
    if not session_id or not user_message:
        return {"error": "Missing session_id or message"}, 400
    
    # Get session data
    history = llm_chatbot.sessions.get_history(session_id)
    analysis = llm_chatbot.sessions.get_analysis(session_id)
    
    if not analysis:
        return {"error": "Session not found"}, 404
    
    # Generate response (proslijedi session_id)
    bot_response = llm_chatbot.generate_response(
        user_message=user_message,
        history=history,
        analysis=analysis,
        session_id=session_id
    )
    
    # Save to history
    llm_chatbot.sessions.add_exchange(session_id, user_message, bot_response)
    
    return {
        'session_id': session_id,
        'response': bot_response,
        'history_length': len(history) + 1
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