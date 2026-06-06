"""
EVALUACIJA LLM CHATBOTA
Mjeri koliko često LLM uspješno generiše odgovor
"""

from chatbot_llm import LLMChatbotV2
import time

# =========================================================
# INICIJALIZACIJA
# =========================================================
print("=" * 60)
print("EVALUACIJA: LLM CHATBOT")
print("=" * 60)

# Pokreni chatbot sa LLM-om
chatbot = LLMChatbotV2(model_name="llama3.2:3b", use_llm=True)

# Testne poruke (različiti scenariji)
test_messages = [
    "What should I do?",
    "Give me some advice",
    "I'm scared of what they'll do to me",
    "How do I block someone on Instagram?",
    "Yes",
    "No",
    "You are so ugly",
    "Help me please",
    "What now?",
    "I don't know what to do",
    "They keep sending me mean messages",
    "Should I tell my parents?",
    "I feel so alone",
]

# =========================================================
# TESTIRANJE LLM-a DIREKTNO (preko generate_response)
# =========================================================
print("\n📝 Testiram {} poruka...\n".format(len(test_messages)))

results = {
    'llm_success': 0,      # LLM je vratio OK odgovor (ne None)
    'llm_failed': 0,       # LLM je vratio None
    'responses': []        # Spremi odgovore za kasniju analizu
}

for i, msg in enumerate(test_messages):
    print(f"{i+1}. '{msg[:40]}'")
    
    analysis = {'emotion': 'neutral', 'topic': 'general'}
    session_id = chatbot.sessions.create_session(analysis)
    
    try:
        # Direktno pozivamo _llm_generate da zaobiđemo fallback logiku
        llm_response = chatbot._llm_generate(
            session_id=session_id,
            user_message=msg,
            analysis=analysis,
            history=[],
            session_info={}
        )
        
        if llm_response is None:
            results['llm_failed'] += 1
            results['responses'].append(('FAIL', msg, None))
            print(f"   ❌ LLM FAILED → vratio None")
        else:
            results['llm_success'] += 1
            results['responses'].append(('SUCCESS', msg, llm_response[:100]))
            print(f"   ✅ LLM SUCCESS → '{llm_response[:70]}...'")
            
    except Exception as e:
        results['llm_failed'] += 1
        results['responses'].append(('ERROR', msg, str(e)))
        print(f"   ❌ EXCEPTION: {e}")
    
    time.sleep(0.5)  # mali delay da ne preopteretimo Ollamu

# =========================================================
# REZULTATI
# =========================================================
total = len(test_messages)
print("\n" + "=" * 60)
print("REZULTATI")
print("=" * 60)
print(f"📊 LLM uspješno generisao odgovor: {results['llm_success']}/{total} ({results['llm_success']/total*100:.1f}%)")
print(f"📊 LLM nije uspio (fallback aktiviran): {results['llm_failed']}/{total} ({results['llm_failed']/total*100:.1f}%)")

# =========================================================
# ANALIZA KVALITETA ODOGOVORA (jednostavna heuristika)
# =========================================================
print("\n" + "=" * 60)
print("ANALIZA KVALITETA ODOGOVORA")
print("=" * 60)

quality_checks = {
    'has_emoji': 0,
    'too_short': 0,  # manje od 20 karaktera
    'has_question': 0,  # sadrži "would you like"
}

for status, msg, resp in results['responses']:
    if status != 'SUCCESS' or resp is None:
        continue
    
    if '💙' in resp or '🧡' in resp or '💪' in resp or '🤝' in resp:
        quality_checks['has_emoji'] += 1
    
    if len(resp) < 20:
        quality_checks['too_short'] += 1
        print(f"  ⚠️ Prekratak odgovor za: '{msg}' -> '{resp}'")
    
    if 'would you like' in resp.lower():
        quality_checks['has_question'] += 1
        print(f"  ⚠️ Sadrži 'would you like' za: '{msg}'")

print(f"\n📊 Kvalitet uspješnih LLM odgovora ({results['llm_success']} odgovora):")
print(f"   - Sadrži emoji: {quality_checks['has_emoji']}/{results['llm_success']} ({quality_checks['has_emoji']/results['llm_success']*100:.1f}%)")
print(f"   - Prekratki (<20 char): {quality_checks['too_short']}/{results['llm_success']}")
print(f"   - Sadrži 'would you like': {quality_checks['has_question']}/{results['llm_success']}")

