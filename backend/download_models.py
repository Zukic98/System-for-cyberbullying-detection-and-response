import os
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSeq2SeqLM

BASE_DIR = os.path.dirname(__file__)
MODELS_DIR = os.path.join(BASE_DIR, 'models')


def download_and_save(repo_id: str, target_name: str, model_class, local_only: bool = False):
    target_dir = os.path.join(MODELS_DIR, target_name)
    os.makedirs(target_dir, exist_ok=True)
    print(f"Downloading {repo_id} to {target_dir}...")

    tokenizer = AutoTokenizer.from_pretrained(repo_id, local_files_only=local_only)
    tokenizer.save_pretrained(target_dir)

    model = model_class.from_pretrained(repo_id, local_files_only=local_only)
    model.save_pretrained(target_dir)

    print(f"Saved {repo_id} to {target_dir}")
    return target_dir


if __name__ == '__main__':
    print('This script downloads model files into backend/models/')
    print('Make sure you have an internet connection for the first run.')
    print()

    download_and_save(
        repo_id='Davlan/bert-base-multilingual-cased-ner-hrl',
        target_name='ner_davlan_bert_base_multilingual_cased_ner_hrl',
        model_class=AutoModelForTokenClassification
    )

    download_and_save(
        repo_id='facebook/bart-large-cnn',
        target_name='bart_large_cnn',
        model_class=AutoModelForSeq2SeqLM
    )

    print('\nDownload complete.')
