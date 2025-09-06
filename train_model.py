# Training and prediction utilities for NB, SVM, and BERT (sentence-transformers)
import os, pickle
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression
    HAVE_BERT = True
except Exception:
    HAVE_BERT = False

MODEL_DIR = 'models'

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT text, label FROM emails')
    rows = cur.fetchall()
    conn.close()
    texts = [r[0] for r in rows]
    labels = [r[1] for r in rows]
    return texts, labels

def train_and_save_all(db_path, root_path):
    texts, labels = load_data(db_path)
    if len(texts) < 10:
        print('Not enough data to train')
        return
    os.makedirs(os.path.join(root_path, MODEL_DIR), exist_ok=True)
    vec = TfidfVectorizer(stop_words='english', max_features=15000)
    X = vec.fit_transform(texts)
    nb = MultinomialNB()
    nb.fit(X, labels)
    svm = LinearSVC()
    svm.fit(X, labels)
    with open(os.path.join(root_path, MODEL_DIR, 'tfidf.pkl'), 'wb') as f:
        pickle.dump(vec, f)
    with open(os.path.join(root_path, MODEL_DIR, 'nb.pkl'), 'wb') as f:
        pickle.dump(nb, f)
    with open(os.path.join(root_path, MODEL_DIR, 'svm.pkl'), 'wb') as f:
        pickle.dump(svm, f)
    if HAVE_BERT:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        emb = model.encode(texts, show_progress_bar=True)
        clf = LogisticRegression(max_iter=1000)
        clf.fit(emb, labels)
        with open(os.path.join(root_path, MODEL_DIR, 'bert.pkl'), 'wb') as f:
            pickle.dump({'model_name':'all-MiniLM-L6-v2', 'clf':clf}, f)
    print('Training complete')

def retrain_models_if_missing(db_path, root_path):
    os.makedirs(os.path.join(root_path, MODEL_DIR), exist_ok=True)
    if not os.path.exists(os.path.join(root_path, MODEL_DIR, 'nb.pkl')):
        train_and_save_all(db_path, root_path)

def predict_with_models(text, db_path, root_path):
    import pickle
    res = {'models':{}}
    with open(os.path.join(root_path, MODEL_DIR, 'tfidf.pkl'), 'rb') as f:
        vec = pickle.load(f)
    X = vec.transform([text])
    with open(os.path.join(root_path, MODEL_DIR, 'nb.pkl'), 'rb') as f:
        nb = pickle.load(f)
    nb_label = nb.predict(X)[0]
    nb_prob = None
    if hasattr(nb, 'predict_proba'):
        nb_prob = max(nb.predict_proba(X)[0])
    res['models']['NaiveBayes'] = {'label': nb_label, 'score': nb_prob}
    with open(os.path.join(root_path, MODEL_DIR, 'svm.pkl'), 'rb') as f:
        svm = pickle.load(f)
    svm_label = svm.predict(X)[0]
    res['models']['SVM'] = {'label': svm_label, 'score': None}
    if os.path.exists(os.path.join(root_path, MODEL_DIR, 'bert.pkl')) and HAVE_BERT:
        with open(os.path.join(root_path, MODEL_DIR, 'bert.pkl'), 'rb') as f:
            bobj = pickle.load(f)
        from sentence_transformers import SentenceTransformer
        bert_model = SentenceTransformer(bobj.get('model_name'))
        emb = bert_model.encode([text])
        pred = bobj['clf'].predict(emb)[0]
        res['models']['BERT'] = {'label': pred, 'score': None}
    else:
        res['models']['BERT'] = {'label': 'not_available', 'score': None}
    return res
