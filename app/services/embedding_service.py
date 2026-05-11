from app.services.embedding_model import get_embedding_model
def generate_embedding(text: str):
    model = get_embedding_model()
    embedding = model.encode(text)

    return embedding.tolist()