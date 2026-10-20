import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Find the sample knowledge base in the same folder.
DATA_FILE = Path(__file__).with_name("sample_knowledge.json")


def load_knowledge_base():
    """Read the example canine behavior entries from JSON."""
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def retrieve_knowledge(query, documents, top_k=3):
    """Find knowledge base entries related to the query."""

    # Get the text from each entry.
    texts = [document["text"] for document in documents]

    # Convert the reference text into TF-IDF vectors.
    vectorizer = TfidfVectorizer(stop_words="english")
    document_vectors = vectorizer.fit_transform(texts)

    # Convert the search query using the same vocabulary.
    query_vector = vectorizer.transform([query])

    # Compare the query with every knowledge base entry.
    scores = cosine_similarity(query_vector, document_vectors).flatten()

    # Sort the results from highest similarity to lowest.
    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices:
        score = float(scores[index])

        # Skip entries with no overlapping terms.
        if score <= 0:
            continue

        document = documents[index]

        results.append(
            {
                "id": document["id"],
                "topic": document["topic"],
                "text": document["text"],
                "source": document["source"],
                "score": round(score, 3),
            }
        )

        if len(results) >= top_k:
            break

    return results


def main():
    """Run a simple interactive canine behavior search."""
    documents = load_knowledge_base()

    query = input("Enter a dog behavior observation: ")

    results = retrieve_knowledge(query, documents)

    if not results:
        print("\nNo matching reference information found.")
        return

    print("\nRetrieved information:\n")

    for result in results:
        print(f"Topic: {result['topic']}")
        print(f"Similarity score: {result['score']}")
        print(f"Information: {result['text']}")
        print(f"Source: {result['source']}")
        print("-" * 50)


if __name__ == "__main__":
    main()
