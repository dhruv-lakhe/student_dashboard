# courses/recommender_engine.py
import pandas as pd
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

# Load dataset
df = pd.read_csv('udemy_courses.csv')
df = df.dropna(subset=["course_title"]).drop_duplicates(subset=["course_title"]).reset_index(drop=True)

# Load model and send to appropriate device
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('distilbert-base-nli-mean-tokens')
model = model.to(device)

# Generate embeddings once
course_embeddings = model.encode(df["course_title"].tolist(), show_progress_bar=True, convert_to_tensor=True)

# Core recommendation function
def recommend_from_resume(resume_text, top_n=10):
    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    similarities = F.cosine_similarity(resume_embedding, course_embeddings)
    top_indices = torch.topk(similarities, k=top_n).indices.cpu().numpy()
    return df.iloc[top_indices][["course_title", "url", "price"]]