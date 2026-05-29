# backend/fine_tune.py
"""
Fine-tuning script for cyberbullying detection model using human feedback.
Run this script after collecting 50-100 feedback entries.
"""

import pandas as pd
import torch
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification, 
    TrainingArguments, 
    Trainer
)
from datasets import Dataset
import os
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

# =====================================================================
# CONFIGURATION
# =====================================================================

FEEDBACK_FILE = "./data/admin_feedback.csv"
MODEL_TO_FINE_TUNE = "./models/model_2_cyberbullying"  # Cyberbullying type model
OUTPUT_DIR = "./fine_tuned_model"
MIN_FEEDBACK_REQUIRED = 20  # Minimum feedback entries to start fine-tuning

# =====================================================================
# LOAD FEEDBACK DATA
# =====================================================================

def load_feedback_data():
    """Load and prepare feedback data for fine-tuning"""
    
    if not os.path.exists(FEEDBACK_FILE):
        print(f"❌ Feedback file not found: {FEEDBACK_FILE}")
        return None
    
    df = pd.read_csv(FEEDBACK_FILE)
    print(f"📊 Loaded {len(df)} feedback entries")
    
    if len(df) < MIN_FEEDBACK_REQUIRED:
        print(f"⚠️ Need at least {MIN_FEEDBACK_REQUIRED} feedback entries. Currently: {len(df)}")
        return None
    
    # Filter only ADMIN_REVIEW cases (where model was uncertain)
    df_admin = df[df['model_decision'] == 'ADMIN_REVIEW']
    print(f"📊 Admin review cases: {len(df_admin)}")
    
    if len(df_admin) < 10:
        print(f"⚠️ Need at least 10 admin review cases. Currently: {len(df_admin)}")
        return None
    
    # Prepare training data
    texts = df_admin['original_text'].tolist()
    # Convert user_verdict to labels: BULLYING_DETECTED -> 1, SAFE -> 0
    labels = [1 if verdict == 'BULLYING_DETECTED' else 0 for verdict in df_admin['user_verdict']]
    
    print(f"\n📊 Training data prepared:")
    print(f"   - Bullying labeled: {sum(labels)}")
    print(f"   - Safe labeled: {len(labels) - sum(labels)}")
    
    return texts, labels

# =====================================================================
# PREPARE DATASET
# =====================================================================

def prepare_dataset(texts, labels, tokenizer, max_length=128):
    """Tokenize texts and create HuggingFace Dataset"""
    
    encodings = tokenizer(
        texts, 
        truncation=True, 
        padding=True, 
        max_length=max_length,
        return_tensors=None
    )
    
    dataset = Dataset.from_dict({
        'input_ids': encodings['input_ids'],
        'attention_mask': encodings['attention_mask'],
        'labels': labels
    })
    
    return dataset

# =====================================================================
# COMPUTE METRICS
# =====================================================================

def compute_metrics(eval_pred):
    """Calculate accuracy and F1 score for evaluation"""
    predictions, labels = eval_pred
    predictions = np.argmax(predictions, axis=1)
    accuracy = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average='weighted')
    return {
        'accuracy': accuracy,
        'f1_score': f1
    }

# =====================================================================
# MAIN FINE-TUNING FUNCTION
# =====================================================================

def fine_tune_model():
    """Main fine-tuning function"""
    
    print("\n" + "="*60)
    print("🚀 FINE-TUNING CYBERBULLYING DETECTION MODEL")
    print("="*60)
    
    # 1. Load feedback data
    print("\n📥 Step 1: Loading feedback data...")
    data = load_feedback_data()
    if data is None:
        return False
    
    texts, labels = data
    
    # 2. Load tokenizer and model
    print("\n📥 Step 2: Loading tokenizer and model...")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"   Using device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_TO_FINE_TUNE)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_TO_FINE_TUNE, 
        num_labels=2
    ).to(device)
    
    # 3. Prepare dataset
    print("\n📥 Step 3: Preparing dataset...")
    dataset = prepare_dataset(texts, labels, tokenizer)
    
    # Split into train and validation (80/20)
    split_dataset = dataset.train_test_split(test_size=0.2, seed=42)
    train_dataset = split_dataset['train']
    eval_dataset = split_dataset['test']
    
    print(f"   Train samples: {len(train_dataset)}")
    print(f"   Validation samples: {len(eval_dataset)}")
    
    # 4. Training arguments
    print("\n📥 Step 4: Configuring training...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=5,
        per_device_train_batch_size=4,
        per_device_eval_batch_size=4,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        learning_rate=2e-5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        push_to_hub=False,
    )
    
    # 5. Create trainer
    print("\n📥 Step 5: Initializing trainer...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    
    # 6. Train
    print("\n🚀 Step 6: Starting fine-tuning...")
    print("-"*40)
    trainer.train()
    
    # 7. Evaluate
    print("\n📊 Step 7: Evaluating model...")
    eval_results = trainer.evaluate()
    print(f"   Evaluation results: {eval_results}")
    
    # 8. Save fine-tuned model
    print("\n💾 Step 8: Saving fine-tuned model...")
    model.save_pretrained(MODEL_TO_FINE_TUNE)
    tokenizer.save_pretrained(MODEL_TO_FINE_TUNE)
    print(f"✅ Model saved to: {MODEL_TO_FINE_TUNE}")
    
    # 9. Save training report
    report = {
        'feedback_entries_used': len(texts),
        'training_samples': len(train_dataset),
        'validation_samples': len(eval_dataset),
        'eval_accuracy': eval_results.get('eval_accuracy', 0),
        'eval_f1_score': eval_results.get('eval_f1_score', 0),
        'model_path': MODEL_TO_FINE_TUNE
    }
    
    report_df = pd.DataFrame([report])
    report_df.to_csv("./fine_tuning_report.csv", index=False)
    print("\n📄 Fine-tuning report saved to: fine_tuning_report.csv")
    
    print("\n" + "="*60)
    print("✅ FINE-TUNING COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    return True

# =====================================================================
# TEST THE FINE-TUNED MODEL
# =====================================================================

def test_model():
    """Quick test of the fine-tuned model"""
    
    print("\n🧪 Testing fine-tuned model...")
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_TO_FINE_TUNE)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_TO_FINE_TUNE).to(device)
    model.eval()
    
    test_texts = [
        "You are so ugly and stupid",
        "Thank you for your help",
        "I will kill you",
        "Great job on the presentation"
    ]
    
    for text in test_texts:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(probabilities, dim=-1).item()
            confidence = probabilities[0][predicted_class].item()
        
        label = "BULLYING_DETECTED" if predicted_class == 1 else "SAFE"
        print(f"\n📝 '{text}'")
        print(f"   → Prediction: {label}")
        print(f"   → Confidence: {confidence:.3f}")

# =====================================================================
# RUN
# =====================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fine-tune cyberbullying model with human feedback')
    parser.add_argument('--test', action='store_true', help='Test the model after fine-tuning')
    parser.add_argument('--min-feedback', type=int, default=20, help='Minimum feedback entries required')
    
    args = parser.parse_args()
    
    if args.min_feedback:
        MIN_FEEDBACK_REQUIRED = args.min_feedback
    
    success = fine_tune_model()
    
    if success and args.test:
        test_model()