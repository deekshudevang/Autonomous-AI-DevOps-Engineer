try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import LinearSVC
except ImportError:
    TfidfVectorizer = None
    LinearSVC = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

class NLPLogClassifier:
    """
    Log Pattern Analysis: NLP-based log classification.
    Parses logs and identifies patterns of failure using TF-IDF or HuggingFace Transformers.
    """
    def __init__(self, use_transformers=False):
        self.use_transformers = use_transformers
        if use_transformers and pipeline:
            # Example using a zero-shot or sequence classifier for root cause
            self.model = pipeline("text-classification", model="distilbert-base-uncased")
        elif TfidfVectorizer and LinearSVC:
            self.vectorizer = TfidfVectorizer(max_features=5000)
            self.classifier = LinearSVC()
            self.is_trained = False
        else:
            self.model = None

    def train_classifier(self, log_corpus, labels):
        """
        Train the TF-IDF / SVM classifier on historical log data
        """
        if not self.use_transformers and TfidfVectorizer:
            X = self.vectorizer.fit_transform(log_corpus)
            self.classifier.fit(X, labels)
            self.is_trained = True

    def analyze_log_pattern(self, log_line: str) -> str:
        """
        Root Cause Detection: Automatically identify which service or 
        component caused the problem based on the log pattern.
        """
        # Fallback if no ML available
        if "MemoryError" in log_line or "OOM" in log_line:
            return "Application Layer: Memory Exhaustion"
        elif "Timeout" in log_line or "ConnectionRefused" in log_line:
            return "Network Layer: Connectivity Dropped"
        elif "Deadlock" in log_line:
            return "Database Layer: Row Lock Contention"

        if self.use_transformers and pipeline:
            result = self.model(log_line)
            return result[0]['label']
            
        elif not self.use_transformers and getattr(self, "is_trained", False):
            X = self.vectorizer.transform([log_line])
            prediction = self.classifier.predict(X)
            return prediction[0]
            
        return "Unknown Root Cause Pattern"
