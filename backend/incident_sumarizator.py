import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class IncidentSumarizator:
    def __init__(self, model_name_or_path="facebook/bart-large-cnn", cache_dir=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache_dir = cache_dir
        self.model_name_or_path = model_name_or_path

        if cache_dir is not None and os.path.isdir(cache_dir):
            print(f"Loading summarizer from local cache: {cache_dir}")
            self.model_name_or_path = cache_dir
            self.local_files_only = True
        else:
            self.local_files_only = os.path.isdir(model_name_or_path)

        if not self.local_files_only and cache_dir is not None:
            self._download_local_model(model_name_or_path, cache_dir)
            self.model_name_or_path = cache_dir
            self.local_files_only = True

        print(f"Učitavam model i tokenizer ({self.model_name_or_path})...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name_or_path, local_files_only=self.local_files_only)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name_or_path, local_files_only=self.local_files_only).to(self.device)
        print("Model za sumarizaciju je uspješno učitan!")

    def _download_local_model(self, repo_id: str, local_dir: str):
        os.makedirs(local_dir, exist_ok=True)
        print(f"Downloading summarization model {repo_id} to {local_dir}...")
        tokenizer = AutoTokenizer.from_pretrained(repo_id)
        tokenizer.save_pretrained(local_dir)
        model = AutoModelForSeq2SeqLM.from_pretrained(repo_id)
        model.save_pretrained(local_dir)
        print(f"Saved summarization model to {local_dir}")

    def generisi_izvjestaj(self, cijeli_razgovor, max_duzina=80, min_duzina=30):
        if not cijeli_razgovor or not isinstance(cijeli_razgovor, str):
            return "Nema dostupnog sadržaja za sumarizaciju."

        inputs = self.tokenizer(
            cijeli_razgovor,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        summary_ids = self.model.generate(
            inputs["input_ids"],
            max_length=max_duzina,
            min_length=min_duzina,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True
        )

        summary_text = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        return summary_text


if __name__ == "__main__":
    modul_pet = IncidentSumarizator()

    simulacija_konverzacije = """
    INCIDENT LOG REPORT:
    Target / Victim: Identified as [PER] (Zijad).
    Platform / Location: Incident occurred on Instagram and near [LOC] (Sarajevo).
    Rule Engine Status: Cyberbullying detected with high confidence (94%).
    Victim Emotion State: High level of fear, anxiety, and distress.

    FULL TRANSCRIPT:
    Victim: "Someone is constantly sending me threatening messages on Instagram. They know where I live in Sarajevo and they said they will wait for me after school. I am very scared to go outside."
    Chatbot Support Response: "I am very sorry you are going through this, Zijad. Please know that you are not alone and this is not your fault. Your safety is the priority. Do not reply to the bully. Take screenshots of all messages immediately as evidence. Talk to a trusted adult, parent, or school counselor right away. If you feel you are in immediate danger, please call the local police. We are here to support you."
    """

    print("\n" + "="*60)
    print("GENERISANJE IZVJEŠTAJA ZA ADMINA / PSIHOLOGA (FAZA 5)")
    print("="*60)

    kratki_izvjestaj = modul_pet.generisi_izvjestaj(simulacija_konverzacije)

    print("--- ORIGINALNI PODACI IZ KONVERZACIJE ---")
    print(simulacija_konverzacije.strip())
    print("-" * 60)
    print("--- AUTOMATSKI GENERISAN SAŽETAK ZA BAZU ---")
    print(kratki_izvjestaj)
    print("="*60)
