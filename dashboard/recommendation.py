# courses/recommender_engine.py
import pandas as pd

# Load dataset
df = pd.read_csv('udemy_courses.csv')
df = df.dropna(subset=["course_title"]).drop_duplicates(subset=["course_title"]).reset_index(drop=True)

# Try to load heavy ML dependencies
try:
    import torch
    import torch.nn.functional as F
    from sentence_transformers import SentenceTransformer

    # Load model and send to appropriate device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    model = model.to(device)

    # Generate embeddings once
    course_embeddings = model.encode(df["course_title"].tolist(), show_progress_bar=True, convert_to_tensor=True)
    ML_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] ML libraries not available: {e}")
    model = None
    course_embeddings = None
    ML_AVAILABLE = False

# Core recommendation function
def recommend_from_resume(resume_text, top_n=10):
    if not ML_AVAILABLE:
        # Fallback: simple keyword matching
        keywords = resume_text.lower().split()
        scores = []
        for _, row in df.iterrows():
            title = row["course_title"].lower()
            score = sum(1 for kw in keywords if kw in title)
            scores.append(score)
        df['_score'] = scores
        result = df.nlargest(top_n, '_score')[["course_title", "url", "price"]]
        df.drop(columns=['_score'], inplace=True)
        return result

    resume_embedding = model.encode(resume_text, convert_to_tensor=True)
    similarities = F.cosine_similarity(resume_embedding, course_embeddings)
    top_indices = torch.topk(similarities, k=top_n).indices.cpu().numpy()
    return df.iloc[top_indices][["course_title", "url", "price"]]

