# backend/chatbot_llm.py
import uuid
import re
import random
import time
import ollama
from chatbot import ChatSession, LLMChatbot, TOPIC_DESCRIPTIONS, CRISIS_PHRASES

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """You are SafeBot, a kind support assistant for people facing cyberbullying.

CRITICAL RULES:
- Use EXACTLY ONE emoji per message: 💙, 🤝, 💪, or 🧡
- Keep responses SHORT: 2-3 sentences max
- Give CONCRETE steps when someone asks for advice - do NOT ask "would you like suggestions?"
- If they say "yes", "ok", "sure" - immediately give advice, don't ask again
- Never say "Would you like some suggestions?" - just give the suggestions
- Match their energy: if they're solution-focused, be practical
- Never blame the victim or say "just ignore it"
- Only introduce yourself in the FIRST message"""

# =========================================================
# THREAT & CRISIS PATTERNS
# =========================================================

DIRECT_THREAT_PATTERNS = [
    r"(?:i|i\'ll|i will|they|they\'ll|they will|he|he\'ll|he will|she|she\'ll|she will)\s+(?:find|kill|hurt|murder|destroy|hunt)\s+you",
    r"(?:gonna|going to)\s+(?:kill|hurt|find)\s+you",
    r"you(?:\'re| are) (?:dead|gone)",
    r"watch your back",
    r"i know where you live",
    r"(?:will|gonna|going to)\s+kill\s+(?:you|u)",
    r"kill\s+(?:you|u|yourself)",
    r"told\s+me\s+(?:that\s+)?(?:they|he|she|i)\s+(?:will|would|gonna)\s+kill",
]

EXTRA_CRISIS_PHRASES = [
    "suicidal", "want to die", "end it all", "no point in living",
    "take my life", "not worth living", "better off dead",
    "thinking about suicide", "feel like dying", "wish i was dead",
    "wish i were dead", "kill myself", "end my life",
]

class LLMChatbotV2(LLMChatbot):
    
    def __init__(self, model_name="llama3.2:1b", use_llm=True):
        super().__init__()
        self.model_name = model_name
        self.use_llm = use_llm
        self._last_fallback_index = {}
        self._advice_given = {}  # Prati da li je savjet već dat
        
        if use_llm:
            try:
                ollama.list()
                print(f"🤖 LLM mode: {model_name} (Ollama - SafeBot ready)")
            except Exception as e:
                print(f"⚠️ Ollama not available ({e}), falling back to rule-based")
                self.use_llm = False
        else:
            print("🤖 Rule-based mode (LLM disabled)")
    
    def _is_direct_threat(self, text):
        text_lower = text.lower()
        for pattern in DIRECT_THREAT_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _is_asking_question(self, text):
        text_lower = text.lower()
        patterns = [
            r"give me (?:some |any )?(?:advice|tips|help|suggestions)",
            r"i need (?:some |any )?(?:advice|tips|help|suggestions)",
            r"tell me (?:what|how) (?:to|i|you)",
            r"what (?:do|should|can) i do",
            r"(?:do|can) you (?:have|give|offer) (?:any |some )?advice",
            r"how (?:do|should|can) i",
            r"any (?:advice|suggestions|tips|ideas)",
            r"help me",
            r"what now", r"what next",
            r"how (?:do|should|can) i (?:deal|handle|respond|react|stop|fix|make|get|report|block)",
            r"how to (?:deal|handle|respond|react|stop|report|block)",
            r"don'?t know how", r"not sure how",
            r"advice",
            r"\?$",
        ]
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _is_affirmation(self, text):
        """Detektuje kratke potvrdne odgovore"""
        text_lower = text.lower().strip()
        affirmations = [
            "yes", "yeah", "yep", "yup", "sure", "ok", "okay", 
            "alright", "please", "go ahead", "tell me", "i do",
            "i would", "that would be", "yes please",
        ]
        return text_lower in affirmations or any(text_lower == a for a in affirmations)
    
    def _clean_llm_output(self, text):
        if not text:
            return None
        
        
        # Pronađi sve emojije
        emoji_pattern = re.compile("["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        
        emojis = emoji_pattern.findall(text)
        if len(emojis) > 1:
            # Zadrži samo prvi emoji
            first_emoji = emojis[0]
            for emoji in emojis[1:]:
                text = text.replace(emoji, "", 1)
            # Dodaj prvi emoji na kraj ako nije već tamo
            if first_emoji not in text[-5:]:
                text = text.rstrip() + " " + first_emoji
        
        # Ukloni sve neželjene prefixe
        garbage_patterns = [
            r"^(Here(?: is|'s) my (?:response|introduction|message|reply)[:\)]?\s*)",
            r"^(My (?:response|introduction|message|reply)[:\)]?\s*)",
            r"^(Response|Introduction|Message|Reply)[:\)]?\s*",
            r"^(Hello again!?\s*)",
            r"^(Hi again!?\s*)",
            r"^(Hello there!?\s*)",
            r"^(Hey there!?\s*)",
            r"^(Hi there!?\s*)",
            r"^(I(?:\'m| am) SafeBot\s*[🚨🆘⚠️🔴💙🌟✨😊]?\s*)",
            r"^(I(?:\'m| am) SafeBot[^.!?]*[.!?]?\s*)",
            r"^(here to (?:support|help|listen)[^.!?]*[.!?]?\s*)",
            r"^(a supportive chatbot[^.!?]*[.!?]?\s*)",
            r"^(supportive chatbot[^.!?]*[.!?]?\s*)",
            r"^(I can only imagine[^.!?]*[.!?]?\s*)",
            r"^(I can imagine[^.!?]*[.!?]?\s*)",
            r"^👤 USER:.*?(?=\w)",
            r"^🔍 DETECTION:.*?(?=\w)",
            r"^📍 ENTITIES:.*?(?=\w)",
            r"^📊 STATE:.*?(?=\w)",
            r"^CONVERSATION CONTEXT:.*?(?=\w)",
            r"^User message:.*?(?=\w)",
            r"^\d+\.\s*",
        ]
        for pattern in garbage_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Ukloni neželjene fraze o postavljanju pitanja
        question_frases = [
            r"Would you like (?:some |any )?(?:support|tips|suggestions|advice|help)\??",
            r"Would you like me to (?:give|offer|provide|share)\??",
            r"Can I (?:give|offer|provide|share) you (?:some |any )?(?:support|tips|suggestions|advice|help)\??",
            r"Would (?:some |any )?(?:support|tips|suggestions|advice|help) (?:be |sound )?(?:helpful|good|useful)\??",
        ]
        for pattern in question_frases:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        text = text.strip("\"'")
        text = re.sub(r"\s+", " ", text).strip()
        
        # Ukloni trailing period pa emoji pa period
        text = re.sub(r'\.\s*(\S)\s*\.$', r'. \1', text)
        
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        if not text or len(text) < 5:
            return None
        
        # Ako je poruka postala prekratka nakon čišćenja
        if len(text) < 20:
            return None
            
        return text
    
    def _build_llm_context(self, user_message, analysis, history, session_id):
        """Context builder koji je svjestan da li je savjet već dat"""
        
        user_lower = user_message.lower()
        stage = self.sessions.get_stage(session_id) if session_id else "initial"
        
        # Detektuj intent
        if self._is_direct_threat(user_message):
            intent = "User mentioned threats - needs urgent safety advice NOW"
        elif self._is_affirmation(user_message) and self.sessions.was_advice_offered(session_id):
            intent = "User said YES to advice - give CONCRETE steps NOW, do NOT ask again"
        elif self._is_asking_question(user_message):
            intent = "User is asking for advice - give CONCRETE steps, do NOT ask if they want advice"
        elif len(user_message.split()) > 15:
            intent = "User is sharing their experience"
        else:
            intent = "User is reaching out for support"
        
        # Recent history
        recent = ""
        if history:
            for ex in history[-2:]:
                recent += f"User: {ex.get('user', '')}\nBot: {ex.get('bot', '')}\n"
        
        # Special instruction based on intent
        special = ""
        if "give CONCRETE steps" in intent:
            special = "\nIMPORTANT: Give specific, numbered steps. Do NOT ask if they want advice - just give it."
        if "said YES" in intent:
            special = "\nCRITICAL: They already said yes. Give the advice NOW. Do NOT ask again."
        
        prompt = f"""Context: {intent}
Chat stage: {stage}
{special}

Recent conversation:
{recent}
User message: "{user_message}"

Respond as SafeBot (2-3 sentences, EXACTLY ONE emoji, NO questions about whether they want advice):"""
        
        return prompt
    
    def generate_response(self, user_message, history, analysis, session_id):
        print(f"\n🔵 GENERATE RESPONSE for: '{user_message[:50]}...'")
        
        session_info = self.sessions.get_session_summary(session_id) or {}
        user_lower = user_message.lower().strip()
        
        # 1. CRISIS CHECKS
        if any(phrase in user_lower for phrase in CRISIS_PHRASES):
            print("   ⚠️ CRISIS DETECTED!")
            return self._crisis_response()
        
        if any(phrase in user_lower for phrase in EXTRA_CRISIS_PHRASES):
            print("   ⚠️ EXTRA CRISIS DETECTED!")
            return self._crisis_response()
        
        # 2. DIRECT THREAT
        if self._is_direct_threat(user_message):
            print("   ⚠️ DIRECT THREAT DETECTED!")
            self.sessions.set_stage(session_id, "ready_for_advice")
            return self._direct_threat_response()
        
        # 3. AFFIRMATION CHECK - korisnik je rekao "yes" na ponudu za savjet
        if self._is_affirmation(user_message) and self.sessions.was_advice_offered(session_id):
            print("   ✅ User affirmed - giving advice immediately")
            return self._give_concrete_advice(analysis, session_id)
        
        # 4. NAME DETECTION
        name_match = re.search(r"(?:my name is|i'm|i am|call me|name'?s)\s+([a-zA-Z]+)", user_lower)
        if name_match:
            name = name_match.group(1).capitalize()
            print(f"   👤 Name detected: {name}")
            self.sessions.set_user_name(session_id, name)
        
        # 5. LLM GENERATION
        if self.use_llm:
            self._update_stage(session_id, user_lower, session_info)
            
            # Provjeri da li je prethodna poruka nudila savjet
            if history:
                last_bot_msg = history[-1].get('bot', '') if history else ""
                if any(phrase in last_bot_msg.lower() for phrase in ['would you like', 'can i give', 'want some']):
                    self.sessions.mark_advice_offered(session_id)
            
            print("   🤖 Trying LLM generation...")
            response = self._llm_generate(session_id, user_message, analysis, history, session_info)
            
            if response is None:
                print("   ⚠️ LLM returned None, using fallback")
                return self._get_smart_fallback(user_message, analysis, session_id, history)
            
            # Provjeri da li odgovor sadrži "would you like" - to je loše
            if re.search(r'would you like (?:some |any )?(?:support|tips|suggestions|advice|help)', response, re.IGNORECASE):
                print("   ⚠️ Response asks question instead of giving advice - replacing")
                return self._get_smart_fallback(user_message, analysis, session_id, history)
            
            if self.sessions.is_repeat_response(session_id, response):
                print("   ⚠️ Repeated response detected, using fallback")
                return self._get_smart_fallback(user_message, analysis, session_id, history)
            
            print(f"   ✅ LLM response: '{response[:80]}...'")
            return response
        
        print("   📋 Using rule-based fallback")
        return super().generate_response(user_message, history, analysis, session_id)
    
    def _give_concrete_advice(self, analysis, session_id):
        """Daje konkretne savjete bez pitanja"""
        advice = (
            "Here's what to do 💙 "
            "1) Screenshot everything as evidence. "
            "2) Block the person on all platforms. "
            "3) Report them using the platform's report button. "
            "4) Tell a trusted friend or adult. "
            "Which step would you like more detail on?"
        )
        return advice
    
    def _direct_threat_response(self):
        return (
            "A death threat is a CRIMINAL OFFENSE and NOT your fault.\n\n"
            "Please do this NOW:\n"
            "1. Save screenshots of everything\n"
            "2. Tell someone you trust immediately\n"
            "3. Contact the police\n"
            "4. If at work, report to HR today\n\n"
            "Your safety is the priority. 💙\n\n"
            "Would you like help figuring out what to say to HR or the police?"
        )
    
    def _update_stage(self, session_id, user_lower, session_info):
        stage = session_info.get("stage", "initial")
        
        advice_patterns = [
            "give me advice", "give me some advice", "give me tips",
            "give me help", "give me suggestions",
            "i need advice", "i need help", "i need tips",
            "what do i do", "what should i do", "help me", "advice",
            "how do i", "what can i do", "any advice", "what now",
            "how to deal", "how do i deal", "what would you suggest",
            "i don't know what to do", "can you give me", "can u give me",
            "how do i handle", "how do i respond", "how do i stop",
            "how to handle", "how to report", "how do i report",
            "don't know how", "not sure how",
        ]
        if any(p in user_lower for p in advice_patterns):
            self.sessions.set_stage(session_id, "ready_for_advice")
            self.sessions.mark_advice_given(session_id)
            print(f"   📍 Stage updated: ready_for_advice")
            return
        
        action_patterns = [
            "i will", "i'm going to", "i'll try", "ok i'll", "yes i will",
            "i can do that", "that sounds good", "i think i'll",
            "ill block", "i'll block", "ill report", "i'll report",
            "ill do that", "i'll do that", "ill try", "i'll try",
            "sounds good", "good idea", "will do",
        ]
        if any(p in user_lower for p in action_patterns):
            self.sessions.set_stage(session_id, "action_planning")
            print(f"   📍 Stage updated: action_planning")
            return
        
        goodbye_patterns = ["goodbye", "bye", "thank you bye", "thanks bye", "that's all", "end chat"]
        if any(p in user_lower for p in goodbye_patterns):
            self.sessions.set_stage(session_id, "closing")
            print(f"   📍 Stage updated: closing")
            return
        
        emotion_words = ["scared", "afraid", "hurt", "crying", "alone", "hate", "angry", "sad", 
                        "terrified", "worried", "embarrassed", "humiliated", "ashamed"]
        if (len(user_lower.split()) > 10 or any(w in user_lower for w in emotion_words)) and stage in ["initial", "ready_for_advice"]:
            self.sessions.set_stage(session_id, "venting")
            print(f"   📍 Stage updated: venting")
    
    def _llm_generate(self, session_id, user_message, analysis, history, session_info, extra=None):
        
        context = self._build_llm_context(user_message, analysis, history, session_id)  # ← proslijedi session_id
        if extra:
            context += f"\n\n{extra}"
        
        for attempt in range(3):
            try:
                if attempt == 0:
                    current_context = context
                elif attempt == 1:
                    current_context = f"""User says: "{user_message}"

Respond as SafeBot. Give CONCRETE advice if they asked for help. Use EXACTLY ONE emoji. NO questions about whether they want advice. 2-3 sentences."""
                else:
                    current_context = f"User: {user_message}\n\nSupportive response with concrete steps (2-3 sentences, ONE emoji):"
                
                response = ollama.chat(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": current_context}
                    ],
                    options={
                        "temperature": 0.7,
                        "num_predict": 150,
                        "top_p": 0.9,
                        "repeat_penalty": 1.2,
                    }
                )
                
                raw_message = response["message"]["content"].strip()
                
                if not raw_message:
                    print(f"   🐞 Attempt {attempt+1}: Empty response")
                    if attempt < 2:
                        time.sleep(1)
                        continue
                    return None
                
                print(f"   🐞 RAW attempt {attempt+1}: '{raw_message[:100]}...'")
                message = self._clean_llm_output(raw_message)
                
                if message and len(message) >= 20:
                    # Provjeri da li poruka sadrži "would you like"
                    if re.search(r'would you like', message, re.IGNORECASE):
                        print(f"   ⚠️ Contains 'would you like' - removing question")
                        message = re.sub(r'[Ww]ould you like[^.]*\.?', '', message).strip()
                        if len(message) < 20:
                            continue
                    
                    if not message.rstrip().endswith(('.', '!', '?')):
                        message = message.rstrip() + '.'
                    
                    print(f"   🐞 CLEANED: '{message[:100]}'")
                    return message
                
                print(f"   🐞 Attempt {attempt+1}: Too short: '{message}'")
                
            except Exception as e:
                print(f"   ⚠️ Attempt {attempt+1} error: {e}")
                if attempt < 2:
                    time.sleep(1)
                else:
                    return None
        
        return None
    
    def generate_first_message(self, analysis):
        if self.use_llm:
            emotion = analysis.get("emotion", "unknown")
            
            emotion_desc = {
                "fear": "scared and frightened",
                "sadness": "sad and hurting",
                "anger": "angry and frustrated",
                "nervousness": "nervous and anxious",
                "embarrassment": "embarrassed and humiliated",
                "confusion": "confused and unsure",
                "neutral": "reaching out for support",
            }.get(emotion, "going through something difficult")
            
            context = f"""Write a warm first message from SafeBot to someone who feels {emotion_desc}.

Start with: "Hi, I'm SafeBot 💙"
Thank them for reaching out.
Ask ONE simple question about what happened.
Keep it under 50 words. Use ONLY ONE emoji.

Your response:"""

            for attempt in range(3):
                try:
                    response = ollama.chat(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": "You are SafeBot. Start with 'Hi, I'm SafeBot 💙'. Use ONLY ONE emoji. Be warm and brief."},
                            {"role": "user", "content": context}
                        ],
                        options={
                            "temperature": 0.8,
                            "num_predict": 80,
                        }
                    )
                    raw_message = response["message"]["content"].strip()
                    print(f"🐞 RAW first: '{raw_message}'")
                    
                    if not raw_message:
                        if attempt < 2:
                            time.sleep(2)
                            continue
                        return self._get_first_message_fallback(emotion)
                    
                    message = self._clean_llm_output(raw_message)
                    print(f"🐞 CLEANED first: '{message}'")
                    
                    if message and len(message) >= 20:
                        return message
                    
                except Exception as e:
                    print(f"⚠️ First message attempt {attempt+1} error: {e}")
                    if attempt < 2:
                        time.sleep(2)
                    else:
                        return self._get_first_message_fallback(emotion)
        
        return self._get_first_message_fallback("neutral")
    
    def _get_first_message_fallback(self, emotion):
        messages = {
            "fear": "Hi, I'm SafeBot 💙 Thank you for reaching out. Being threatened or scared is really tough, and you're not alone. Can you tell me what's been happening?",
            "sadness": "Hi, I'm SafeBot 💙 I'm really glad you reached out. It sounds like you're hurting right now. What's on your mind?",
            "anger": "Hi, I'm SafeBot 💙 Thank you for sharing. It sounds like something has really upset you, and that's completely valid. What happened?",
            "nervousness": "Hi, I'm SafeBot 💙 I appreciate you reaching out. It's okay to feel nervous - this is a safe space. What's going on?",
            "embarrassment": "Hi, I'm SafeBot 💙 Thank you for being brave enough to talk about this. You didn't deserve to be treated that way. What happened?",
            "confusion": "Hi, I'm SafeBot 💙 I'm here to help you make sense of things. Thank you for reaching out. What's been happening?",
            "neutral": "Hi, I'm SafeBot 💙 Thank you for reaching out - that takes real courage. I'm here to listen. What's been happening?",
        }
        return messages.get(emotion, messages["neutral"])
    
    def _get_smart_fallback(self, user_message, analysis, session_id, history):
        """Pametni fallback koji stvarno odgovara na ono što korisnik pita"""
        user_lower = user_message.lower()
        emotion = analysis.get("emotion", "unknown")
        
        print(f"   🔄 Smart fallback for: '{user_lower[:60]}...'")
        
        # Ako korisnik traži savjet - DAJ GA ODMAH
        if self._is_asking_question(user_message):
            print("   🎯 User asked for advice - giving concrete steps")
            return (
                "Here's what to do 💙 "
                "1) Screenshot everything as evidence. "
                "2) Block the person on all platforms. "
                "3) Report them using the report button. "
                "4) Tell a trusted friend or adult. "
                "Which step would you like more detail on?"
            )
        
        # Ako je korisnik rekao "yes" na prethodnu ponudu
        if self._is_affirmation(user_message):
            last_bot_msg = history[-1].get('bot', '') if history else ""
            if any(p in last_bot_msg.lower() for p in ['would you like', 'want some', 'can i']):
                print("   🎯 User affirmed - giving concrete steps")
                return (
                    "Here's what to do 💙 "
                    "1) Screenshot everything as evidence. "
                    "2) Block the person on all platforms. "
                    "3) Report them using the report button. "
                    "4) Tell a trusted friend or adult. "
                    "Which step would you like more detail on?"
                )
        
        # Hate speech
        if any(w in user_lower for w in ['hate speech', 'hate', 'racist', 'slur']):
            return "Hate speech is never okay 💙 Block the person immediately and report the content. Take screenshots first as evidence. You deserve to be treated with respect."
        
        # Threats
        if any(w in user_lower for w in ['threat', 'threaten', 'kill', 'hurt', 'harm']):
            return "Threats are serious 💙 Screenshot everything, block the person, and report them. If you feel unsafe, contact the police. Your safety comes first."
        
        # Cyberbullying general
        if any(w in user_lower for w in ['bully', 'bullied', 'cyberbully']):
            return "You don't deserve to be bullied 💙 Here's what helps: 1) Don't respond 2) Screenshot evidence 3) Block them 4) Report to the platform 5) Talk to someone you trust. Which step can I help with?"
        
        # Online harassment
        if any(w in user_lower for w in ['messages', 'posts', 'comments', 'social media', 'online']):
            return "Online harassment is exhausting 💙 Protect yourself: make your accounts private, block harassers, and report abusive content. Would you like specific instructions for any platform?"
        
        # Emotion-based fallbacks
        fallbacks = {
            "fear": [
                "I hear that you're scared 💙 It's completely normal to feel this way. What would help you feel safer right now?",
                "Being threatened is frightening 💙 You're not alone in this. Tell me more about what happened.",
            ],
            "sadness": [
                "I'm sorry you're hurting 💙 Your feelings are valid. What's been weighing on your mind?",
                "It sounds really painful 🧡 I'm here to listen. Take your time sharing.",
            ],
            "anger": [
                "Your anger is understandable 💪 What happened to you isn't okay. Want to talk about it?",
                "I get why you'd be angry 💙 Sometimes anger shows us when our boundaries have been crossed.",
            ],
            "embarrassment": [
                "You have nothing to be ashamed of 💙 The bully's behavior reflects on them, not you. What happened?",
                "Embarrassment is painful, but you didn't do anything wrong 💙 Want to talk about it?",
            ],
            "neutral": [
                "I'm here for you 💙 How can I best support you right now?",
                "Thank you for sharing with me 💙 What would be most helpful to talk about?",
            ],
        }
        
        options = fallbacks.get(emotion, ["I'm here for you 💙 How can I best support you right now?"])
        
        if session_id not in self._last_fallback_index:
            self._last_fallback_index[session_id] = 0
        else:
            self._last_fallback_index[session_id] = (self._last_fallback_index[session_id] + 1) % len(options)
        
        return options[self._last_fallback_index[session_id]]