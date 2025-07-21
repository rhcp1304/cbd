import os
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from django.conf import settings
from ..models import GoogleSheetData

FAISS_INDEX_PATH = os.path.join(settings.BASE_DIR, 'rag_index.faiss')
FAISS_TEXT_MAPPING_PATH = os.path.join(settings.BASE_DIR, 'rag_text_mapping.json')
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please set it.")
genai.configure(api_key=GEMINI_API_KEY)

_embedding_model = None
_faiss_index = None
_original_texts = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL_NAME}...")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Embedding model loaded.")
    return _embedding_model


def _generate_embedding(text):
    model = _get_embedding_model()
    return model.encode(text, convert_to_numpy=True).astype('float32')


def _row_to_text_chunk(row_obj):
    field_names = [field.name for field in row_obj._meta.fields if field.name != 'id']
    parts = []
    for field_name in field_names:
        value = getattr(row_obj, field_name, '')
        verbose_name = row_obj._meta.get_field(field_name).verbose_name or field_name.replace('_', ' ').title()
        parts.append(f"{verbose_name}: {value}")

    return "; ".join(parts)


def build_and_save_faiss_index(logger=None):
    log_func = logger if logger else print

    log_func("Starting FAISS index build process...")
    all_sheet_data = GoogleSheetData.objects.all().iterator()

    texts = []
    embeddings = []

    for i, row_obj in enumerate(all_sheet_data):
        text_chunk = _row_to_text_chunk(row_obj)
        texts.append(text_chunk)
        embeddings.append(_generate_embedding(text_chunk))
        if (i + 1) % 100 == 0:
            log_func(f"Processed {i + 1} rows for embedding...")

    if not embeddings:
        log_func("No data found in GoogleSheetData to build index.")
        return False

    embeddings_array = np.array(embeddings).astype('float32')
    dimension = embeddings_array.shape[1]
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(embeddings_array)
    faiss.write_index(faiss_index, FAISS_INDEX_PATH)
    import json
    with open(FAISS_TEXT_MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(texts, f, ensure_ascii=False, indent=2)

    log_func(f"FAISS index built and saved to {FAISS_INDEX_PATH}")
    log_func(f"Text mapping saved to {FAISS_TEXT_MAPPING_PATH}")
    return True


def load_faiss_index_and_texts(logger=None):
    global _faiss_index, _original_texts
    log_func = logger if logger else print

    if _faiss_index is not None and _original_texts is not None:
        log_func("FAISS index and texts already loaded from cache.")
        return _faiss_index, _original_texts

    if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(FAISS_TEXT_MAPPING_PATH):
        log_func("FAISS index or text mapping not found. Please run 'build_rag_index' command first.")
        return None, None

    log_func(f"Loading FAISS index from {FAISS_INDEX_PATH}...")
    _faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    log_func("FAISS index loaded.")

    log_func(f"Loading original texts from {FAISS_TEXT_MAPPING_PATH}...")
    import json
    with open(FAISS_TEXT_MAPPING_PATH, 'r', encoding='utf-8') as f:
        _original_texts = json.load(f)
    log_func("Original texts loaded.")

    return _faiss_index, _original_texts


def retrieve_relevant_data(query_text, k=500, logger=None):
    log_func = logger if logger else print
    faiss_index, original_texts = load_faiss_index_and_texts(logger=log_func)
    if faiss_index is None or original_texts is None:
        log_func("RAG system not initialized. Cannot retrieve data.")
        return []

    query_embedding = _generate_embedding(query_text)
    query_embedding = np.array([query_embedding]).astype('float32')
    distances, indices = faiss_index.search(query_embedding, k)

    relevant_chunks = []
    for i, idx in enumerate(indices[0]):
        if idx < len(original_texts):
            relevant_chunks.append(original_texts[idx])
            log_func(
                f"Retrieved chunk {i + 1} (Distance: {distances[0][i]:.4f}): {original_texts[idx][:100]}...")  # Log first 100 chars
        else:
            log_func(f"WARNING: Retrieved index {idx} out of bounds for original_texts (len={len(original_texts)}).")

    return relevant_chunks


def get_gemini_response(prompt_text, logger=None):
    log_func = logger if logger else print
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-lite-preview-06-17')
        log_func("Sending prompt to Gemini LLM...")
        response = model.generate_content(prompt_text)
        log_func("Received response from Gemini LLM.")
        return response.text
    except Exception as e:
        log_func(f"ERROR: Error calling Gemini LLM: {e}")
        return f"An error occurred while generating a response: {e}"