from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans


def cluster_feedback(feedback_list, num_clusters=5):
    """
    Cluster feedback using TF-IDF + KMeans
    """
    if len(feedback_list) < num_clusters:
        num_clusters = max(1, len(feedback_list))

    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(feedback_list)

    model = KMeans(n_clusters=num_clusters, random_state=42)
    labels = model.fit_predict(X)

    clusters = {}
    for label, text in zip(labels, feedback_list):
        clusters.setdefault(label, []).append(text)

    return clusters
