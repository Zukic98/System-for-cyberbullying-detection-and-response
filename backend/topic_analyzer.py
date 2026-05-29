# backend/topic_analyzer.py
import json
import os
import pickle
from typing import Dict, Any, List

class TopicAnalyzer:
    def __init__(self, model_path="./models/topic_model"):
        self.model_path = model_path
        self.topic_model = None
        self.topic_mapping = {}
        
        # Debug prints
        abs_path = os.path.abspath(model_path)
        print(f"🔍 TopicAnalyzer init:")
        print(f"   Model path: {abs_path}")
        print(f"   Folder exists: {os.path.exists(abs_path)}")
        
        if os.path.exists(abs_path):
            print(f"   Contents: {os.listdir(abs_path)}")
        
        # 1. Load BERTopic model from binary pickle file
        model_file = os.path.join(model_path, "bertopic_model")
        
        if os.path.isfile(model_file):
            try:
                with open(model_file, 'rb') as f:
                    self.topic_model = pickle.load(f)
                print(f"✅ BERTopic model loaded from {model_file} (binary file)")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                self.topic_model = None
        elif os.path.isdir(model_file):
            try:
                from bertopic import BERTopic
                self.topic_model = BERTopic.load(model_file)
                print(f"✅ BERTopic model loaded from {model_file} (folder)")
            except Exception as e:
                print(f"❌ Failed to load model: {e}")
                self.topic_model = None
        else:
            print(f"❌ Model not found at {model_file}")
            self.topic_model = None
        
        # 2. Load topic mapping
        mapping_file = os.path.join(model_path, "topic_mapping.json")
        if os.path.exists(mapping_file):
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.topic_mapping = json.load(f)
            print(f"✅ Topic mapping loaded: {len(self.topic_mapping)} categories")
        else:
            print(f"⚠️ Topic mapping not found, using fallback")
            self.topic_mapping = {}
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyzes text and returns topic and category"""
        if self.topic_model is None:
            return self._fallback_with_keywords(text, 0.0)
        
        try:
            # Transform text
            topic_id, probability = self.topic_model.transform([text])
            topic_id = topic_id[0]
            probability = probability[0] if probability is not None else 0.0
            
            print(f"🔍 Transform: topic_id={topic_id}, prob={probability:.3f}")
            
            if topic_id == -1 or probability < 0.3:
                return self._fallback_with_keywords(text, probability)
            
            topic_key = str(topic_id)
            if topic_key in self.topic_mapping:
                topic_data = self.topic_mapping[topic_key]
                return {
                    'topic_id': topic_id,
                    'topic_category': topic_data.get('category', 'Unknown topic'),
                    'severity': topic_data.get('severity', 2),
                    'keywords': topic_data.get('keywords', []),
                    'suggested_response': self._get_response_for_category(topic_data.get('category', 'GENERAL ATTACKS')),
                    'confidence': float(probability),
                    'is_analyzed': True,
                    'text': text[:200]
                }
            else:
                return self._fallback_with_keywords(text, probability)
                
        except Exception as e:
            print(f"❌ Error in analyze_text: {e}")
            return self._fallback_with_keywords(text, 0.0)
    
    def _fallback_with_keywords(self, text: str, probability: float) -> Dict[str, Any]:
        """Fallback analysis based on keywords with calculated confidence"""
        text_lower = text.lower()
        
        # Define keywords by category
        keywords_map = {
            "THREATS OF VIOLENCE": ['kill', 'die', 'death', 'suicide', 'hang', 'murder', 'dead', 'destroy'],
            "ATTACKS ON APPEARANCE": ['ugly', 'fat', 'face', 'looks', 'appearance', 'beautiful', 'pretty', 'butt', 'nose', 'hair', 'gross', 'hideous'],
            "ATTACKS ON INTELLIGENCE": ['stupid', 'dumb', 'idiot', 'dummy', 'brain', 'smart', 'intelligent', 'fool', 'moron', 'retard'],
            "ISOLATION/REJECTION": ['alone', 'nobody', 'likes', 'hate', 'friend', 'everyone', 'love', 'care', 'unwanted', 'abandoned'],
            "ATTACKS ON CHARACTER": ['worthless', 'pathetic', 'weak', 'loser', 'failure', 'piece', 'trash', 'garbage', 'waste', 'scum']
        }
        
        # Find which category has the most matches
        best_category = "GENERAL ATTACKS"
        best_score = 0
        best_keywords_found = []
        
        for category, keywords in keywords_map.items():
            found = [kw for kw in keywords if kw in text_lower]
            if len(found) > best_score:
                best_score = len(found)
                best_category = category
                best_keywords_found = found
        
        # If no matches, use GENERAL ATTACKS
        if best_score == 0:
            best_category = "GENERAL ATTACKS"
            best_score = 0
            best_keywords_found = []
        
        # Severity mapping
        severity_map = {
            "THREATS OF VIOLENCE": 5,
            "ATTACKS ON APPEARANCE": 3,
            "ATTACKS ON INTELLIGENCE": 2,
            "ISOLATION/REJECTION": 4,
            "ATTACKS ON CHARACTER": 3,
            "GENERAL ATTACKS": 2
        }
        
        # Calculate confidence (max 0.95, min 0.15)
        if best_score > 0:
            max_keywords = 5
            confidence = min(0.95, 0.3 + (best_score / max_keywords) * 0.65)
        else:
            confidence = 0.15
        
        # Use original probability if higher
        final_confidence = max(confidence, probability) if probability > 0 else confidence
        
        severity = severity_map.get(best_category, 2)
        
        print(f"🔍 Keyword fallback: category={best_category}, score={best_score}, confidence={final_confidence:.3f}")
        
        return {
            'topic_id': -1,
            'topic_category': best_category,
            'severity': severity,
            'keywords': best_keywords_found,
            'suggested_response': self._get_response_for_category(best_category),
            'confidence': round(final_confidence, 3),
            'is_analyzed': True,
            'text': text[:200]
        }
    
    def _get_response_for_category(self, category: str) -> str:
        """Returns support message based on category"""
        messages = {
            "THREATS OF VIOLENCE": "🚨 THIS IS SERIOUS! Threats of violence are a criminal offense. Save evidence and report to the police immediately. You are not alone, help is available. 📞",
            "ATTACKS ON APPEARANCE": "💔 I'm sorry you experienced this. Attacks on appearance are painful, but your appearance does not determine your worth. Block the person sending this. 💪",
            "ATTACKS ON INTELLIGENCE": "🧠 No one has the right to insult your intelligence. Your abilities are far greater than these insults. Keep learning and growing! 📚",
            "ISOLATION/REJECTION": "🏠 You are not alone. This is an attempt to isolate you, but there are people who care. Reach out to friends or family. 🤝",
            "ATTACKS ON CHARACTER": "⚡ Your worth is not measured by others' words. Bullies often project their own insecurities. You are enough! 🌟",
            "GENERAL ATTACKS": "🛡️ This is a form of cyberbullying. You are not to blame. Block, report, and don't let these words get under your skin.",
            "HATE SPEECH ON RELIGION/RACE": "🌍 Hatred based on religion or race is unacceptable. Report this to the platform. Your culture and faith are your pride! ✊",
        }
        return messages.get(category, "💙 Your safety is important. Block the person harassing you and report the content.")