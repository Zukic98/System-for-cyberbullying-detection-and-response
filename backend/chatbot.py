import uuid
import re


# =========================================================
# RESPONSE TEMPLATES (odvojene od logike, lako proširiti)
# =========================================================

TOPIC_DESCRIPTIONS = {
    "appearance":     "how you look or your body image",
    "threats":        "threats or intimidation",
    "isolation":      "feeling left out or excluded",
    "intelligence":   "people attacking your intelligence",
    "identity_hate":  "discrimination or hate speech",
    "work":           "bullying at work",
    "school":         "bullying at school",
    "online":         "online or cyberbullying",
    "age":            "bullying about your age",
    "gender":         "bullying about your gender",
    "religion":       "bullying about your religion",
    "general":        "what you're going through",
}

EMOTION_FIRST_MESSAGES = {
    "fear": (
        "{severity}{entity} It sounds like you might be feeling scared or anxious about {topic_msg}. "
        "That's completely normal — threats and bullying are scary. Your safety is the most important thing right now. "
        "Would you like to tell me what happened? I'm here to listen without judgment. 🤝"
    ),
    "sadness": (
        "{severity}{entity} 🧡 I can hear that you're feeling really down about {topic_msg}. "
        "That weight must be heavy to carry alone. Please know that what you're feeling is valid, and you don't deserve any of this. "
        "Do you want to talk about how you're feeling? I'm here for you."
    ),
    "anger": (
        "{severity}{entity} 💪 Your anger about {topic_msg} is completely valid and justified. "
        "What you're experiencing isn't right, and you have every right to be upset. "
        "Would you like to share what happened? I'm here to listen and help you figure out what to do next."
    ),
    "grief": (
        "{severity}{entity} 💔 I'm so sorry you're going through this pain. {topic_msg_cap} can be deeply hurtful, "
        "and it's okay to grieve what's been taken from you. Would you like to talk about what's on your mind?"
    ),
    "nervousness": (
        "{severity}{entity} It's completely okay to feel nervous right now. 🤝 "
        "What you're dealing with regarding {topic_msg} sounds really difficult. "
        "Take your time — there's no rush. I'm here whenever you're ready to share."
    ),
    "disappointment": (
        "{severity}{entity} I hear the disappointment in your voice. 💙 "
        "{topic_msg_cap} can be really discouraging, especially when you expected better from people. "
        "But please know — this situation doesn't define you or your worth. Would you like to tell me more about what's happening?"
    ),
    "default": (
        "{severity}{entity} 👋 I'm your AI support assistant, and I'm here to help you through this. "
        "It sounds like you're dealing with {topic_msg}. You're not alone — many people face this, and there are ways to get through it. "
        "Would you like to share more about what's been happening? I'll listen carefully."
    ),
}

SEVERITY_OPENINGS = {
    "high":   "🚨 I can see this is a serious situation you're dealing with. Thank you for having the courage to reach out — that's a big first step.",
    "medium": "💙 I understand you're going through something difficult. Thank you for trusting me enough to talk about it.",
    "low":    "💙 I'm here to support you. Thank you for reaching out.",
}

GOODBYE_RESPONSES = {
    "fear":        "I hope you feel a little less alone after our chat. 💙 Remember: you're braver than you believe, and stronger than you feel right now. Please reach out to someone in real life too — you deserve support. Take care of yourself. 🤝",
    "sadness":     "I'm glad you reached out today. 🧡 You've taken a step — that takes real courage. You matter more than you know. Please be gentle with yourself. 💙",
    "anger":       "Goodbye for now. 💪 Remember that your anger is valid, but don't let it consume you. Channel it into action that protects you. You deserve peace and safety. 🤝",
    "default":     "Thank you for trusting me today. 💙 Remember: you're not alone, you matter, and this situation doesn't define your worth. Take care of yourself — you deserve it. 🤝💙",
}

ENGAGEMENT_RESPONSES = {
    "fear":        "I know this is really hard to talk about. 💙 What's one small thing that would make you feel even a little better right now? A plan? A distraction? Just someone to listen? 🤝",
    "sadness":     "You don't have to say much. 🧡 Even just telling me how you're feeling — tired, angry, numb — that's enough. I'm listening without judgment. What's on your heart right now?",
    "anger":       "Your feelings matter so much. 💪 Would you like to talk more about what happened, or would practical strategies be more helpful right now? 🚨",
    "default":     "Take your time. 💙 What would help most right now — advice, resources, or just someone to listen? You don't have to go through this alone. 🤝",
}

CRISIS_PHRASES = [
    "kill myself", "want to die", "end my life", "can't go on", "no reason to live",
    "suicide", "self harm", "hurt myself", "better off dead", "want to disappear forever",
    "nothing matters", "what's the point", "don't want to live",
]

STAGE_TRANSITIONS = {
    "initial":          ["venting", "ready_for_advice"],
    "venting":          ["venting", "ready_for_advice"],
    "ready_for_advice": ["action_planning", "venting"],
    "action_planning":  ["action_planning", "closing"],
    "closing":          ["closing"],
}


# =========================================================
# SESSION MANAGEMENT
# =========================================================

class ChatSession:
    def __init__(self):
        self.sessions = {}

    def create_session(self, analysis_result):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "history":          [],
            "analysis":         analysis_result,
            "last_bot_response": None,
            "user_name":        None,
            "user_concern":     None,
            "advice_given":     False,
            "action_taken":     False,
            "emotion_detected": analysis_result.get("emotion", "unknown"),
            "topic_detected":   analysis_result.get("topic", "general"),
            "entities_detected": [],
            # Novo: stage praćenje i skup tema koje su se pojavile
            "stage":            "initial",
            "mentioned_topics": set(),
            "recent_responses": [],   # zadnjih 5 bot odgovora (hash prvih 60 znakova)
        }
        return session_id

    def add_exchange(self, session_id, user_message, bot_message):
        s = self.sessions.get(session_id)
        if not s:
            return
        s["history"].append({"user": user_message, "bot": bot_message})
        s["last_bot_response"] = bot_message
        # Čuvaj hash zadnjih 5 odgovora za deduplikaciju
        key = bot_message[:60]
        s["recent_responses"].append(key)
        if len(s["recent_responses"]) > 5:
            s["recent_responses"].pop(0)
        # Ažuriraj mentioned_topics iz korisnikove poruke
        self._update_mentioned_topics(session_id, user_message)

    def _update_mentioned_topics(self, session_id, text):
        s = self.sessions.get(session_id)
        if not s:
            return
        t = text.lower()
        topic_keywords_map = {
            "work":       ["work", "job", "boss", "coworker", "manager", "hr", "office", "colleague", "workplace"],
            "school":     ["school", "teacher", "class", "student", "counselor", "principal", "professor", "college", "classmate"],
            "online":     ["online", "instagram", "facebook", "tiktok", "twitter", "snapchat", "discord", "reddit", "youtube", "whatsapp"],
            "appearance": ["fat", "ugly", "look", "appearance", "body", "weight", "skin", "face", "hair"],
            "threats":    ["threat", "threaten", "hurt me", "kill me", "beat me", "scared they"],
            "isolation":  ["alone", "lonely", "nobody likes", "no friends", "isolated", "left out", "rejected"],
        }
        for topic, keywords in topic_keywords_map.items():
            if any(kw in t for kw in keywords):
                s["mentioned_topics"].add(topic)

    def get_history(self, session_id):
        return self.sessions.get(session_id, {}).get("history", [])

    def get_analysis(self, session_id):
        return self.sessions.get(session_id, {}).get("analysis")

    def get_last_bot_response(self, session_id):
        return self.sessions.get(session_id, {}).get("last_bot_response")

    def get_stage(self, session_id):
        return self.sessions.get(session_id, {}).get("stage", "initial")

    def set_stage(self, session_id, stage):
        s = self.sessions.get(session_id)
        if s and stage in STAGE_TRANSITIONS:
            s["stage"] = stage

    def set_user_name(self, session_id, name):
        s = self.sessions.get(session_id)
        if s:
            s["user_name"] = name

    def set_user_concern(self, session_id, concern):
        s = self.sessions.get(session_id)
        if s:
            s["user_concern"] = concern

    def mark_advice_given(self, session_id):
        s = self.sessions.get(session_id)
        if s:
            s["advice_given"] = True

    def set_entities(self, session_id, entities):
        s = self.sessions.get(session_id)
        if s:
            s["entities_detected"] = entities

    def is_repeat_response(self, session_id, response):
        s = self.sessions.get(session_id)
        if not s:
            return False
        return response[:60] in s.get("recent_responses", [])

    def get_session_summary(self, session_id):
        s = self.sessions.get(session_id)
        if not s:
            return None
        return {
            "user_name":       s.get("user_name"),
            "user_concern":    s.get("user_concern"),
            "advice_given":    s.get("advice_given"),
            "message_count":   len(s["history"]) * 2,
            "emotion":         s.get("emotion_detected"),
            "topic":           s.get("topic_detected"),
            "entities":        s.get("entities_detected"),
            "stage":           s.get("stage"),
            "mentioned_topics": s.get("mentioned_topics", set()),
        }


# =========================================================
# MAIN CHATBOT
# =========================================================

class LLMChatbot:
    def __init__(self):
        print("🤖 Initializing improved rule-based chatbot...")
        self.sessions = ChatSession()
        print("✅ Chatbot ready! (stage-aware, context-rich, deduplicated)")

    # ----------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------

    def generate_first_message(self, analysis):
        emotion         = analysis.get("emotion", "unknown")
        topic_category  = analysis.get("topic_category", analysis.get("topic", "general"))
        score           = analysis.get("score", 0)
        topic_severity  = analysis.get("topic_severity", 2)
        entities        = analysis.get("entities", {})
        topic_keywords  = analysis.get("topic_keywords", [])

        topic_msg     = TOPIC_DESCRIPTIONS.get(topic_category.lower(), TOPIC_DESCRIPTIONS["general"])
        topic_msg_cap = topic_msg.capitalize()
        severity_key  = "high" if (score > 0.7 or topic_severity >= 4) else ("medium" if (score > 0.3 or topic_severity >= 3) else "low")
        severity      = SEVERITY_OPENINGS[severity_key]

        person_entities = self._extract_persons(entities)
        entity_str = f" {self._context_string(person_entities, [], [], topic_keywords)}" if person_entities else ""

        template = EMOTION_FIRST_MESSAGES.get(emotion, EMOTION_FIRST_MESSAGES["default"])
        return template.format(
            severity=severity,
            entity=entity_str,
            topic_msg=topic_msg,
            topic_msg_cap=topic_msg_cap,
        )

    def generate_response(self, user_message, history, analysis, session_id):
        # Izvuci sve kontekstualne informacije
        emotion        = analysis.get("emotion", "unknown")
        score          = analysis.get("score", 0)
        topic_severity = analysis.get("topic_severity", 2)
        entities       = analysis.get("entities", {})

        user_lower     = user_message.lower().strip()
        word_count     = len(user_message.split())
        last_bot       = self.sessions.get_last_bot_response(session_id) or ""
        session_info   = self.sessions.get_session_summary(session_id) or {}
        stage          = session_info.get("stage", "initial")
        mentioned      = session_info.get("mentioned_topics", set())
        msg_count      = session_info.get("message_count", 0)

        # Efektivni topic = topic iz analize + sve što je korisnik dosad spomenuo
        base_topic     = analysis.get("topic_category", analysis.get("topic", "general")).lower()
        effective_topic = self._resolve_effective_topic(base_topic, mentioned, user_lower)

        person_entities = self._extract_persons(entities)

        # =====================================================
        # 1. CRISIS (uvijek prvo)
        # =====================================================
        if any(phrase in user_lower for phrase in CRISIS_PHRASES):
            return self._crisis_response()

        # =====================================================
        # 2. TOPIC DETEKCIJA (odmah iza crisis — ne na dnu!)
        # =====================================================
        detected_topic = self._detect_topic_from_message(user_lower, effective_topic)

        # =====================================================
        # 3. IME / POZDRAV
        # =====================================================
        name_match = re.search(
            r"(?:my name is|i'm|i am|call me|name'?s)\s+([a-zA-Z]+)", user_lower
        )
        if name_match:
            name = name_match.group(1).capitalize()
            self.sessions.set_user_name(session_id, name)
            return (
                f"Nice to meet you, {name}! 💙 That takes courage to share your name. "
                "Thank you for trusting me. How can I support you today? I'm here to listen and help."
            )

        # =====================================================
        # 4. DJELJENJE ISKUSTVA (kad je bot postavio pitanje)
        # =====================================================
        sharing_triggers = [
            "Would you like to share", "What happened", "tell me what happened",
            "share what happened", "tell me more", "what's been happening",
            "talk about what's been going on",
        ]
        is_yes_no = user_lower in {"yes", "yeah", "yep", "sure", "ok", "okay", "no", "nope", "nah", "yup", "nop", "yea"}
        if word_count > 3 and not is_yes_no and any(t in last_bot for t in sharing_triggers):
            self.sessions.set_user_concern(session_id, user_message[:200])
            self.sessions.set_stage(session_id, "venting")
            return self._handle_experience_sharing(
                user_lower, emotion, detected_topic, score, topic_severity, person_entities
            )

        # =====================================================
        # 5. SPECIFIČNE AKCIJE
        # =====================================================
        if any(p in user_lower for p in [
                "talk to someone", "tell someone", "talk to a teacher",
                "talk to a parent", "talk to a counselor", "talk to hr",
                "tell a teacher", "tell my parents",
                "what do i say", "what should i say",  # ← dodaj ovo
                "how do i tell", "how do i talk"        # ← i ovo
            ]):
            return self._talking_response(detected_topic, person_entities, user_lower)

        if any(p in user_lower for p in ["evidence", "screenshot", "document", "save proof",
                                          "collect evidence", "take screenshot"]):
            return self._evidence_response()

        if any(p in user_lower for p in ["report", "file a report", "report to platform",
                                          "how to report", "report them", "report the content"]):
            return self._reporting_response(detected_topic, user_lower)

        if any(p in user_lower for p in ["block", "block them", "how to block"]):
            return self._blocking_response(user_lower)

        if any(p in user_lower for p in ["privacy", "private account", "make my account private",
                                          "who can see", "privacy settings"]):
            return self._privacy_response()

        # =====================================================
        # 6. ZAHTJEV ZA SAVJETOM
        # =====================================================
        advice_triggers = [
            "what do i do", "what should i do", "help me", "advice", "how do i",
            "i need help", "what can i do", "any advice", "give me advice",
            "tell me what to do", "what's the best way", "can you help me",
            "i don't know what to do",
        ]
        if any(p in user_lower for p in advice_triggers):
            self.sessions.mark_advice_given(session_id)
            self.sessions.set_stage(session_id, "ready_for_advice")
            return self._advice_response(detected_topic, emotion, user_lower, score, topic_severity)

        # =====================================================
        # 7. TOPIC-SPECIFIČNI ODGOVORI
        # =====================================================
        if detected_topic == "work":
            return self._work_response(user_lower, emotion, person_entities)
        if detected_topic == "school":
            return self._school_response(user_lower, emotion, person_entities)
        if detected_topic == "online":
            return self._online_response(user_lower, emotion)
        if detected_topic == "appearance":
            return self._appearance_response(emotion)
        if detected_topic == "threats":
            return self._threats_response(score, topic_severity)
        if detected_topic == "isolation":
            return self._isolation_response(emotion)

        # =====================================================
        # 8. YES / NO (kontekst-svjesno)
        # =====================================================
        if user_lower in {"yes", "yeah", "yep", "sure", "ok", "okay", "yup", "yea"}:
            return self._yes_response(last_bot, session_info, emotion, detected_topic, stage)

        if user_lower in {"no", "nope", "nah", "not really", "not yet", "no thanks"}:
            return self._no_response(last_bot, stage)

        # =====================================================
        # 9. ZAHVALNOST / POZDRAV
        # =====================================================
        if any(w in user_lower for w in ["thank", "thanks", "appreciate", "helpful", "you're great", "awesome"]):
            return self._thank_you_response(msg_count, emotion)

        if any(p in user_lower for p in ["goodbye", "bye", "that's all", "end chat",
                                          "good bye", "bye bye", "see you", "thanks bye"]):
            self.sessions.set_stage(session_id, "closing")
            return self._goodbye_response(emotion, session_info)

        # =====================================================
        # 10. KRATKE PORUKE (zadržaj konverzaciju)
        # =====================================================
        if word_count < 4 and msg_count >= 2:
            return self._engagement_response(emotion, detected_topic, session_info)

        # =====================================================
        # 11. FALLBACK (koristi historiju i stage)
        # =====================================================
        return self._fallback_response(
            emotion, last_bot, session_info, detected_topic, score, topic_severity, stage
        )

    def get_session_summary(self, session_id):
        return self.sessions.get_session_summary(session_id)

    # ----------------------------------------------------------
    # INTERNE POMOĆNE METODE
    # ----------------------------------------------------------

    def _extract_persons(self, entities):
        result = []
        if entities:
            for etype, elist in entities.items():
                if etype == "PER" and elist:
                    result.extend(e["text"] for e in elist[:2])
        return result

    def _context_string(self, persons, locations, orgs, keywords):
        parts = []
        if persons:
            parts.append(f"I notice you mentioned someone named {persons[0]}")
        if locations:
            parts.append(f"regarding {locations[0]}")
        if keywords:
            parts.append(f"Keywords like '{', '.join(keywords[:3])}' came up")
        return ". ".join(parts) + "." if parts else ""

    def _resolve_effective_topic(self, base_topic, mentioned_topics, user_lower):
        """Kombinira base topic s temama koje su se pojavile u razgovoru."""
        priority_order = ["threats", "work", "school", "online", "appearance", "isolation",
                          "identity_hate", "gender", "religion", "age", "general"]
        # Spoji sve poznate teme
        all_topics = {base_topic} | mentioned_topics
        # Vrati prvu po prioritetu
        for t in priority_order:
            if t in all_topics:
                return t
        return base_topic

    def _detect_topic_from_message(self, user_lower, fallback_topic):
        """Detektuje topic direktno iz teksta poruke (premješteno na vrh)."""
        if any(w in user_lower for w in ["threat", "kill me", "hurt me", "beat me", "scared they"]):
            return "threats"
        if any(w in user_lower for w in ["work", "job", "boss", "coworker", "manager", "hr", "office", "colleague"]):
            return "work"
        if any(w in user_lower for w in ["school", "teacher", "class", "student", "counselor", "principal", "professor", "classmate"]):
            return "school"
        if any(w in user_lower for w in ["online", "instagram", "facebook", "tiktok", "twitter", "snapchat", "discord", "reddit", "youtube"]):
            return "online"
        if any(w in user_lower for w in ["fat", "ugly", "look", "appearance", "body", "weight", "skin", "face", "hair"]):
            return "appearance"
        if any(w in user_lower for w in ["alone", "lonely", "nobody likes", "no friends", "isolated", "left out", "rejected"]):
            return "isolation"
        return fallback_topic

    def _safe_response(self, session_id, response, fallback):
        """Vrati fallback ako je response duplikat."""
        if self.sessions.is_repeat_response(session_id, response):
            return fallback
        return response

    # ----------------------------------------------------------
    # RESPONSE METODE
    # ----------------------------------------------------------

    def _crisis_response(self):
        return (
            "🚨 **I'm really glad you reached out. What you're feeling is serious, "
            "and you deserve immediate support from people who are trained to help.**\n\n"
            "📞 **Call or text 988** (Suicide & Crisis Lifeline) — available 24/7, free, confidential\n"
            "📞 **Text HOME to 741741** (Crisis Text Line)\n"
            "📞 **Call 911** if you're in immediate danger\n\n"
            "These people care and want to help you. You're not alone, and what you're feeling matters. 💙\n\n"
            "Would you like me to stay with you while you contact them? I can wait right here."
        )

    def _handle_experience_sharing(self, user_lower, emotion, topic, score, severity, persons):
        person_str = f" about {persons[0]}" if persons else ""

        if score > 0.7 or severity >= 4:
            return (
                f"I'm really sorry that happened to you{person_str}. 🚨 This sounds serious, "
                "and your safety is the priority. Thank you for having the courage to share this with me. "
                "Would you like to talk about immediate steps you can take to protect yourself? "
                "Or would you prefer to talk to someone who can help right now? I can help you figure out what to say. 💙"
            )

        emotion_reactions = {
            "fear":         f"I'm really sorry that happened to you{person_str}. 💙 It's completely normal to feel scared. Would you like to talk about what might help you feel safer right now? 🤝",
            "anger":        f"Thank you for sharing that{person_str}. 💪 Your anger makes complete sense. Would you like to talk about what you can do next? I'm here to help you figure out a plan. 💙",
            "sadness":      f"I hear how much this hurt you{person_str}. 🧡 You didn't deserve any of that. Would you like to talk about how to move forward, or would you prefer some comfort right now? 💙",
            "embarrassed":  f"Please don't feel embarrassed{person_str}. 💙 What happened is not your fault — not even a little bit. Would you like to talk more and work through those feelings? 🤝",
        }

        for key, resp in emotion_reactions.items():
            if key in user_lower or key == emotion:
                return resp

        topic_reactions = {
            "work":       f"Workplace bullying is really tough and often underreported. 💙 Thank you for sharing. Would you like specific advice on how to document what's happening, talk to HR, or understand your legal rights? 🏢",
            "school":     f"School can be so hard when you're being bullied. 🏫 Thank you for telling me. Would you like to talk about how to approach a teacher or counselor? I can help you figure out what to say. 💙",
            "online":     f"Online bullying can feel inescapable. 💙 Would you like advice on screenshots, blocking, reporting, or privacy settings? I can walk you through all of it. 📱",
            "appearance": f"I'm sorry someone attacked your appearance{person_str}. 💙 That says everything about their insecurities and nothing about you. Would you like to talk about how to respond or build confidence? ✨",
        }
        if topic in topic_reactions:
            return topic_reactions[topic]

        return (
            f"Thank you for sharing that with me{person_str}. 💙 That sounds really difficult. "
            "What would help you most right now — talking more about what happened, getting practical advice, "
            "or just having someone listen without judgment? You're in control here. 🤝"
        )

    def _talking_response(self, topic, persons, user_lower):
        person_str = f" like {persons[0]}" if persons else ""

        if "teacher" in user_lower or topic == "school":
            return (
                f"🏫 Talking to a teacher is a great idea{person_str}. Most schools have anti-bullying policies. "
                "Pick a teacher you trust and say: 'I need help with a situation. Some students have been bullying me "
                "and I don't feel safe. Can we talk privately?' Would you like to practice what to say? 💙"
            )
        if any(w in user_lower for w in ["parent", "mom", "dad", "family"]):
            context = "school" if topic == "school" else "online"
            return (
                f"👨‍👩‍👧 Telling your parents is brave{person_str}. They love you and want to help. "
                f"You could say: 'Mom/Dad, I've been having some problems at {context} and I really need your help. "
                "Can we talk?' Would that feel okay? I can help you think through what to say. 💙"
            )
        if "counselor" in user_lower:
            return (
                f"🎓 School counselors are perfect for this{person_str}! They're trained to handle bullying "
                "and can talk to teachers or parents for you if that's easier. "
                "You can say: 'I need help with a situation involving bullying. Can we talk privately?' "
                "Would you like me to help you prepare for that visit? 🤝"
            )
        if "hr" in user_lower or topic == "work":
            return (
                f"🏢 HR is there for exactly this situation{person_str}. "
                "Say: 'I need to report ongoing harassment in my workplace. Can we schedule a private meeting?' "
                "Would you like to practice what to say? 💪"
            )

        return (
            f"Great choice! Talking to someone is a brave and important step. 💙\n\n"
            f"Here's who you can talk to (based on **{topic}** context):\n"
            "• A parent or family member\n• A teacher you trust\n• A school counselor\n"
            "• HR at work\n• A close friend\n• A coach or mentor\n\n"
            "How to start: \"I need help with a situation. Can we talk privately? "
            "I've been experiencing bullying and I don't know what to do.\"\n\n"
            "Would you like to practice what to say? I can help you get comfortable with the words. 🤝"
        )

    def _evidence_response(self):
        return (
            "📸 **Great! Here's how to document evidence properly:**\n\n"
            "📱 **On phone (iOS/Android)**: Press volume down + power button at the same time\n"
            "💻 **On computer (Windows)**: Use Snipping Tool (search in Start menu)\n"
            "🍎 **On computer (Mac)**: Press Shift + Command + 4\n\n"
            "**What to save:**\n"
            "✅ Screenshots of ALL messages, comments, posts\n"
            "✅ Date and time of each incident\n"
            "✅ What was said (copy text if possible)\n"
            "✅ Names of anyone who witnessed it\n\n"
            "Save everything in a folder called \"Evidence — [Date]\". "
            "This evidence is crucial if you decide to report.\n\n"
            "Would you like to know how to report the bullying? 💙"
        )

    def _reporting_response(self, topic, user_lower):
        if topic == "school" or "teacher" in user_lower:
            return (
                "🏫 **How to report at school:**\n\n"
                "1️⃣ Talk to a teacher or counselor you trust\n"
                "2️⃣ Ask about the school's anti-bullying policy (they have one by law!)\n"
                "3️⃣ You can often report anonymously through a form or website\n"
                "4️⃣ Request a follow-up to make sure something was done\n\n"
                "**What to say:** \"I need to report bullying. Here's what's been happening...\"\n\n"
                "Would you like help with what to say to a teacher? 💙"
            )
        if topic == "work" or "hr" in user_lower:
            return (
                "🏢 **How to report at work:**\n\n"
                "1️⃣ Document EVERYTHING first (dates, times, witnesses)\n"
                "2️⃣ Check your employee handbook — there's usually a procedure\n"
                "3️⃣ Request a private meeting with HR\n"
                "4️⃣ Say: \"I need to report ongoing harassment. Here's my documentation.\"\n\n"
                "**Important:** You have legal protections! It's illegal for employers to retaliate "
                "against you for reporting harassment.\n\n"
                "Would you like to practice what to say to HR? 💪"
            )
        return (
            "🚨 **How to report bullying:**\n\n"
            "**On social media:**\n"
            "• Look for the 'Report' button (usually under ... or ⚙️)\n"
            "• Follow the instructions — be specific about what happened\n"
            "• Save the report confirmation number\n\n"
            "**At school:** Tell a teacher, counselor, or principal\n"
            "**At work:** Go to HR or your manager with documentation\n\n"
            "Would you like specific instructions for a particular platform? Just tell me which one! 💙"
        )

    def _blocking_response(self, user_lower):
        return (
            "🔒 **Blocking is a powerful first step!**\n\n"
            "📱 **Instagram/Facebook**: Go to their profile → three dots (...) → Block\n"
            "📱 **TikTok**: Go to their profile → ... → Block\n"
            "📱 **Twitter/X**: Go to their profile → ... → Block\n"
            "📱 **Snapchat**: Tap on their name → More → Block\n"
            "📱 **Discord**: Right-click their name → Block\n\n"
            "Blocking stops them from seeing your posts, sending you messages, and tagging you.\n\n"
            "**Important:** Screenshot BEFORE you block — once blocked, you lose access to their content!\n\n"
            "Would you also like to know about privacy settings? 💙"
        )

    def _privacy_response(self):
        return (
            "🔐 **Privacy settings protect you!**\n\n"
            "✅ Make your account **private** — only approved followers can see your posts\n"
            "✅ Turn off **comments** on posts that might attract bullies\n"
            "✅ Limit who can **message you** to 'friends only'\n"
            "✅ Remove unknown followers regularly\n"
            "✅ Turn off location sharing in posts\n\n"
            "**How to make account private:**\n"
            "• Instagram: Settings → Privacy → Private Account\n"
            "• Facebook: Settings → Privacy → Who can see your future posts? → Friends\n"
            "• TikTok: Settings → Privacy → Private Account\n\n"
            "Would you like detailed instructions for a specific platform? 💙"
        )

    def _advice_response(self, topic, emotion, user_lower, score, severity):
        if score > 0.7 or severity >= 4:
            return (
                "🚨 This sounds serious. Your safety comes first. Here's what I strongly recommend:\n\n"
                "1️⃣ **Tell someone TODAY** — a parent, teacher, counselor, or call 988 (helpline)\n"
                "2️⃣ **Save all evidence** — screenshots, messages, dates\n"
                "3️⃣ **Don't respond to the bully** — they want a reaction\n"
                "4️⃣ **Report the content** to the platform\n\n"
                "You don't have to deal with this alone. Would you like me to help you plan what to say to someone? 💙"
            )

        advice_map = {
            "work": (
                "🏢 **Workplace bullying plan:**\n\n"
                "1️⃣ **Document everything** — dates, times, witnesses, exactly what was said\n"
                "2️⃣ **Check your employee handbook** — look for anti-harassment policies\n"
                "3️⃣ **Talk to HR** — request a private meeting\n"
                "4️⃣ **Know your rights** — you have legal protections under employment law\n\n"
                "**What to say to HR:** \"I need to report ongoing harassment. I have documentation. Can we meet privately?\"\n\n"
                "Would you like to practice that conversation? 💪"
            ),
            "school": (
                "🏫 **School bullying plan:**\n\n"
                "1️⃣ **Write down what happened** — be specific about dates, times, what was said\n"
                "2️⃣ **Talk to a teacher you trust** — they can help connect you with the counselor\n"
                "3️⃣ **Ask about the school's anti-bullying policy** — every school has one by law\n"
                "4️⃣ **Request a follow-up** — make sure something is done\n\n"
                "**What to say:** \"I need help with a bullying situation. Some students have been targeting me and I don't feel safe.\"\n\n"
                "Would you like help with what to say? 🏫"
            ),
            "online": (
                "📱 **Online bullying plan:**\n\n"
                "1️⃣ **SCREENSHOT EVERYTHING** — before you block or delete anything\n"
                "2️⃣ **Block the bully** — stop them from contacting you\n"
                "3️⃣ **Report to the platform** — find the 'Report' button\n"
                "4️⃣ **Make your account private** — control who sees your content\n"
                "5️⃣ **Take a break** — step away from social media if you need to\n\n"
                "Would you like detailed instructions for a specific platform? 💙"
            ),
            "appearance": (
                "💙 **Dealing with appearance-based bullying:**\n\n"
                "1️⃣ **Remember: their words say everything about THEM, nothing about YOU**\n"
                "2️⃣ **Don't engage** — bullies want a reaction\n"
                "3️⃣ **Save evidence** — screenshot everything\n"
                "4️⃣ **Block and report** them\n"
                "5️⃣ **Talk to someone who makes you feel good about yourself**\n\n"
                "Your worth has nothing to do with how you look. Would you like to talk more about building confidence? ✨"
            ),
            "threats": (
                "🚨 **Threats are serious — here's what to do:**\n\n"
                "1️⃣ **Take screenshots immediately**\n"
                "2️⃣ **Save them in multiple places**\n"
                "3️⃣ **Tell a trusted adult TODAY**\n"
                "4️⃣ **Consider contacting authorities** — threats can be illegal\n"
                "5️⃣ **Call 988 if you feel unsafe** — helpline available 24/7\n\n"
                "Would you like to talk about how to tell someone about these threats? 💙"
            ),
        }
        if topic in advice_map:
            return advice_map[topic]

        return (
            "📋 **Here's what helps in most bullying situations:**\n\n"
            "1️⃣ **📸 Save evidence** — screenshots, messages, dates, times\n"
            "2️⃣ **🔒 Block the bully** — stop them from contacting you\n"
            "3️⃣ **🗣️ Tell someone you trust** — parent, teacher, counselor, HR\n"
            "4️⃣ **🚨 Report to the platform** — most have reporting tools\n\n"
            "Would you like me to explain any of these steps in more detail? Just tell me which one! 💙"
        )

    def _work_response(self, user_lower, emotion, persons):
        person_str = f" like {persons[0]}" if persons else ""
        if "hr" in user_lower:
            return (
                f"🏢 HR is your best resource{person_str}. They're trained to handle this confidentially. "
                "Say: 'I need to report ongoing harassment in my workplace. I have documentation and I'd like to meet privately.' "
                "Would you like to practice that conversation? 💪"
            )
        if "scared" in user_lower or "afraid" in user_lower or emotion == "fear":
            return (
                f"Being scared of retaliation is completely normal{person_str}. 💙 "
                "But anti-retaliation laws protect you — it's illegal for employers to fire or punish someone for reporting harassment. "
                "Start by documenting everything secretly. Would that feel like a safe first step? 📝"
            )
        return (
            f"🏢 Workplace bullying is tough but you have rights{person_str}. "
            "Start a log — dates, times, witnesses, exactly what was said. Then consider talking to HR. "
            "You deserve a safe workplace. Would you like more detailed steps? 💪"
        )

    def _school_response(self, user_lower, emotion, persons):
        person_str = f" like {persons[0]}" if persons else ""
        if "teacher" in user_lower:
            return (
                f"🏫 Pick one teacher you trust{person_str}. "
                "Say: 'I need help with a situation. Some students have been bullying me and I don't feel safe. "
                "Can we talk privately?' Would you like to practice that conversation? 💙"
            )
        if "counselor" in user_lower:
            return (
                f"🎓 School counselors are perfect for this{person_str}! "
                "They're trained to handle bullying and can talk to teachers or parents for you if that's easier. "
                "Would you like help preparing for that visit? We can practice what to say. 🤝"
            )
        if "scared" in user_lower or "afraid" in user_lower or emotion == "fear":
            return (
                f"Being scared is completely normal{person_str}. 💙 "
                "Many students worry that telling someone will make things worse. "
                "But most schools have confidential reporting options and trained staff. "
                "Start by writing down what's happening — having it on paper makes it easier to share. Would that help? 📝"
            )
        return (
            f"🏫 School bullying is hard, but you don't have to face it alone{person_str}. "
            "Talk to a teacher or counselor you trust — they have policies and procedures to protect you. "
            "Would you like help planning what to say? 💙"
        )

    def _online_response(self, user_lower, emotion):
        platform_map = {
            "instagram": "Instagram", "facebook": "Facebook", "tiktok": "TikTok",
            "twitter": "Twitter/X", "snapchat": "Snapchat", "discord": "Discord", "reddit": "Reddit",
        }
        platform = next((v for k, v in platform_map.items() if k in user_lower), None)

        if platform:
            return (
                f"📱 **On {platform}:**\n\n"
                f"1️⃣ Screenshot everything BEFORE you block\n"
                f"2️⃣ Go to their profile → Block\n"
                f"3️⃣ Report the content (look for ... or ⚙️)\n"
                f"4️⃣ Make your account private\n\n"
                f"Would you like more detailed steps for {platform}? I can walk you through it. 💙"
            )
        if emotion == "fear":
            return (
                "Online bullying can feel scary because it's always there, following you everywhere. 📱 "
                "But you have power too! Remember: you can take screenshots, block, report, and take a break. "
                "You don't have to engage. Would you like step-by-step help with any of these? 💙"
            )
        return (
            "📱 **Online bullying action plan:**\n\n"
            "1️⃣ **📸 Screenshot EVERYTHING** — do this BEFORE you block or delete anything\n"
            "2️⃣ **🔒 Block the person** — go to their profile → ... → Block\n"
            "3️⃣ **🚨 Report to the platform** — find the 'Report' button\n"
            "4️⃣ **🔐 Make your account private** — control who sees your content\n"
            "5️⃣ **🧘 Take a break** — step away from social media if you need to\n\n"
            "Would you like details for a specific platform? Just tell me which one! 💙"
        )

    def _appearance_response(self, emotion):
        if emotion == "sadness":
            return (
                "I'm really sorry someone made you feel bad about how you look. 💙 "
                "Your appearance has nothing to do with your worth as a person. "
                "Bullies often attack others' looks because they feel insecure about themselves — "
                "it's a reflection of THEIR issues, not YOUR value. "
                "Would you like to talk about how to respond to these comments or build up your confidence? ✨"
            )
        if emotion == "anger":
            return (
                "Your anger is completely justified. 💪 "
                "Attacking someone's appearance is a cowardly move that says everything about the bully's insecurities "
                "and nothing about you. Would you like some strategies for dealing with this kind of bullying? 🤝"
            )
        return (
            "💙 Attacks on your appearance are hurtful, but remember: beauty standards are completely made up, "
            "and everyone is unique. The bully's words reflect their own issues, not your value. "
            "Would you like to talk about building confidence to handle this? ✨"
        )

    def _threats_response(self, score, severity):
        if score > 0.7 or severity >= 4:
            return (
                "🚨 **These are serious threats. Please take immediate action:**\n\n"
                "1️⃣ **Take screenshots immediately** — this is evidence\n"
                "2️⃣ **Save them securely** — in multiple places\n"
                "3️⃣ **Tell a trusted adult TODAY** — parent, teacher, counselor\n"
                "4️⃣ **Consider contacting authorities** — threats can be illegal\n"
                "5️⃣ **Call 988 if you feel unsafe** — helpline available 24/7\n\n"
                "Your safety is the priority. Would you like to talk about how to tell someone about these threats? 💙"
            )
        return (
            "🚨 Threats are serious and often illegal. Please:\n\n"
            "1️⃣ **Take screenshots immediately**\n"
            "2️⃣ **Save them securely**\n"
            "3️⃣ **Consider telling a trusted adult**\n"
            "4️⃣ **If you feel unsafe, contact authorities**\n\n"
            "Your safety is the most important thing. Would you like to talk more or get help planning what to say to someone? 💙"
        )

    def _isolation_response(self, emotion):
        if emotion == "sadness":
            return (
                "Feeling alone is one of the hardest parts of bullying. 🧡 "
                "But please know — you're not alone right now. I'm here, "
                "and the bullies don't speak for everyone. "
                "Would you like to talk about how to connect with people who will appreciate you? 💙"
            )
        return (
            "I hear that you're feeling isolated and alone. 💙 That's a heavy feeling to carry. "
            "But please know — the bullies' words don't define your worth, and they don't speak for everyone. "
            "Would you like to talk about finding better connections or building your support network? 🤝"
        )

    def _yes_response(self, last_bot, session_info, emotion, topic, stage):
        if "practice" in last_bot or "what to say" in last_bot:
            return (
                "🎯 **Great! Let's practice:**\n\n"
                "**You can say:** \"I've been having problems with someone. They've been saying mean things "
                "and it's really hurting me. I don't feel safe. Can you help me?\"\n\n"
                "**Tips:**\n"
                "• Take a deep breath first\n"
                "• You can show them your screenshots if that's easier\n"
                "• It's okay to cry or be emotional\n"
                "• You don't have to say everything at once\n\n"
                "Now you try! What would you say? (Just type it out — I'll help you make it even better!) 💙"
            )
        if "more detailed" in last_bot or "explain any" in last_bot:
            return (
                "📝 **Let me explain in detail:**\n\n"
                "**📸 Screenshots:** On phone: press volume down + power button. "
                "On computer: use Snipping Tool (Windows) or Shift+Cmd+4 (Mac). Save in a folder called 'Evidence'.\n\n"
                "**🔒 Blocking:** Go to their profile → three dots (...) → Block. "
                "They won't see your posts or contact you.\n\n"
                "**🗣️ Telling someone:** \"I need help with a situation. I've been experiencing bullying.\"\n\n"
                "**🚨 Reporting:** Look for the 'Report' button on the platform and be specific about what happened.\n\n"
                "Would you like to focus on any specific step? 💙"
            )
        # Stage-svjesni yes odgovor
        if stage in ("initial", "venting"):
            return (
                "I'm glad you're ready to open up. 💙 Take your time — you can start with whatever feels easiest. "
                "What happened? Even just a sentence or two is a great start. 🤝"
            )
        if stage == "ready_for_advice":
            return (
                f"Great! Based on the **{topic}** situation, here's what I recommend focusing on first:\n\n"
                "1️⃣ **Save evidence** — this is crucial before anything else\n"
                "2️⃣ **Tell one person** — you don't have to tell everyone\n\n"
                "Which feels more urgent to you? I can walk you through either one. 💙"
            )
        if stage == "action_planning":
            return (
                "Great! Here's your **action plan:**\n\n"
                "1️⃣ **Document everything** — screenshots, dates, times, witnesses\n"
                "2️⃣ **Tell ONE trusted person** — you don't have to tell everyone\n"
                "3️⃣ **Block the bully** — on all platforms\n"
                "4️⃣ **Report the content** — use the platform's reporting tool\n"
                "5️⃣ **Take care of yourself** — this isn't your fault\n\n"
                "Which step feels hardest? I can walk you through it. 💙"
            )
        if emotion == "fear":
            return (
                "I'm glad you're ready to take action. 💙 That takes courage when you're feeling scared. "
                "What would you like to focus on first — documenting evidence, telling someone you trust, or reporting? "
                "I can guide you through any of these step by step. 🤝"
            )
        return (
            "Great! What would you like to focus on first?\n\n"
            "📸 **Documenting evidence** (screenshots, dates, times)\n"
            "🔒 **Blocking the bully**\n"
            "🗣️ **Talking to someone** (parent, teacher, HR)\n"
            "🚨 **Reporting** to the platform\n\n"
            "Just tell me what you need! 💙"
        )

    def _no_response(self, last_bot, stage):
        if stage == "venting":
            return (
                "That's completely okay — you don't have to do anything you're not ready for. 💙 "
                "Sometimes it helps just to talk about how you're feeling, without any pressure to act. "
                "What's on your mind right now? 🤝"
            )
        return (
            "That's completely okay! 💙 There's no pressure at all. "
            "What would be more helpful for you right now — just talking about how you feel, "
            "or would you like me to share some resources you can look at when you're ready? "
            "You're in control of this conversation. 🤝"
        )

    def _thank_you_response(self, msg_count, emotion):
        if msg_count >= 4:
            return (
                "You're so welcome! 💙 I'm really glad I could help. "
                "Remember — you're never alone in this. What you're going through is real, and your feelings are valid. "
                "Please reach out to someone you trust in real life too. You deserve support and kindness. 🤝💙"
            )
        return (
            "You're so welcome! 💙 That's what I'm here for. "
            "Would you like to continue talking, or is there something specific I can help with? "
            "I'm here for whatever you need. 🤝"
        )

    def _goodbye_response(self, emotion, session_info):
        if session_info and session_info.get("advice_given"):
            return (
                "I'm glad we could talk today. 💙 Remember the steps we discussed — you have a plan now. "
                "You're stronger than you know, and this situation doesn't define you. "
                "Please reach out to someone you trust in real life too. You're not alone. 🤝💙"
            )
        return GOODBYE_RESPONSES.get(emotion, GOODBYE_RESPONSES["default"])

    def _engagement_response(self, emotion, topic, session_info):
        if session_info and session_info.get("advice_given"):
            return (
                f"How are you feeling about everything we've discussed regarding **{topic}**? "
                "Is there anything specific you'd like more help with? I'm here for whatever you need. 💙"
            )
        if session_info and session_info.get("user_name"):
            name = session_info["user_name"]
            return (
                f"I know this is hard to talk about, {name}. 💙 "
                "We don't have to solve everything at once. "
                "What's one small thing that would make you feel even a little better right now? "
                "A plan? A distraction? Just someone to listen? You're in control here. 🤝"
            )
        return ENGAGEMENT_RESPONSES.get(emotion, ENGAGEMENT_RESPONSES["default"])

    def _fallback_response(self, emotion, last_bot, session_info, topic, score, severity, stage):
        # Visoka ozbiljnost
        if score > 0.7 or severity >= 4:
            return (
                "I'm really concerned about what you're going through. 🚨 This sounds serious. "
                "Would you like to talk about immediate steps to protect yourself? "
                "Or would you prefer I help you plan what to say to a trusted adult? "
                "Your safety is the priority. I'm here to help either way. 💙"
            )

        # Stage-svjesni fallback
        stage_fallbacks = {
            "initial": (
                "💙 I'm here and I'm listening. Would you like to tell me a bit more about what's been happening? "
                "You don't have to share everything at once — even just a little helps me understand how I can support you. 🤝"
            ),
            "venting": (
                "Thank you for sharing that with me. 🧡 I hear you. "
                "How are you feeling about everything right now? You can take all the time you need. 💙"
            ),
            "ready_for_advice": (
                f"I want to make sure I give you the most helpful advice for your **{topic}** situation. "
                "What feels most important to you right now — taking action, talking to someone, or just understanding your options? 💙"
            ),
            "action_planning": (
                "You're doing really well by thinking through this. 💪 "
                "Which step feels hardest or most unclear? I can dig deeper into any part of the plan with you. 🤝"
            ),
        }
        if stage in stage_fallbacks:
            candidate = stage_fallbacks[stage]
            # Deduplikacija
            if not self.sessions.is_repeat_response(None, candidate):
                return candidate

        # Personalizacija imenom
        if session_info and session_info.get("user_name"):
            name = session_info["user_name"]
            return (
                f"I'm here for you, {name}. 🤝 What's on your mind right now? "
                f"How are you feeling about the **{topic}** situation? You can tell me anything — no judgment, just support. 💙"
            )

        # Emotion-based fallback s deduplikacijom
        fallbacks = {
            "fear":    "It's okay to be scared. 💙 Your safety comes first. Would you like to talk about feeling safer, or would you prefer some practical advice on what to do next?",
            "sadness": "I hear your pain. 🧡 You don't deserve any of this. Would you like to talk more about how you're feeling, or would some resources for support be helpful?",
            "anger":   "Your anger is completely valid. 💪 Would you like to channel that energy into action steps to protect yourself? I can help you make a plan.",
            "default": "Thank you for sharing. 💙 What would be most helpful for you right now — talking more about what happened, getting specific advice, or just having someone listen without judgment?",
        }
        response = fallbacks.get(emotion, fallbacks["default"])
        if response == last_bot:
            return (
                "I'm here with you. 💙 What's one thing that would help you feel even a tiny bit better right now? "
                "Let's start there, one small step at a time. 🤝"
            )
        return response