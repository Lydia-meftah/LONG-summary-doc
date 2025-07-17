import os
import tempfile
from flask import Flask, render_template, request, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

import PyPDF2
import docx
from transformers import pipeline

# ---- INITIALISATION ET CONFIG ----
load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret")
auth = HTTPBasicAuth()

users = {
    os.environ.get("ADMIN_USER", "admin"): generate_password_hash(os.environ.get("ADMIN_PASS", "password"))
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# ---- PIPELINE TRANSFORMERS ----
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# ---- CHUNKING LONG TEXT ----
def chunk_text(text, max_chunk=3500):
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) < max_chunk:
            current_chunk += p + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = p + "\n"
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

def summarize_long(text):
    """Résume un texte long en utilisant la méthode map-reduce."""
    chunks = chunk_text(text)
    partial_summaries = []
    for chunk in chunks:
        if chunk.strip():
            s = summarizer(chunk, max_length=200, min_length=40, do_sample=False)[0]['summary_text']
            partial_summaries.append(s)
    # Résumer le résumé des chunks (reduce)
    if partial_summaries:
        final_summary = summarizer(" ".join(partial_summaries), max_length=250, min_length=60, do_sample=False)[0]['summary_text']
        return final_summary
    else:
        return "Aucun texte à résumer"

# ---- EXTRACTION TEXTE FICHIERS ----
def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# ---- ROUTES WEB ----
@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def index():
    if request.method == 'POST':
        files = request.files.getlist('files')
        if not files or not files[0].filename:
            flash("Ajoutez au moins un fichier !", "warning")
            return render_template('index.html')
        
        docs_text = []
        for file in files:
            suffix = None
            if file.filename.endswith('.pdf'):
                suffix = ".pdf"
            elif file.filename.endswith('.docx'):
                suffix = ".docx"
            else:
                continue
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
                file.save(tmp.name)
                if suffix == ".pdf":
                    text = extract_text_from_pdf(tmp.name)
                elif suffix == ".docx":
                    text = extract_text_from_docx(tmp.name)
                else:
                    text = ""
            if text:
                docs_text.append((file.filename, text))

        if not docs_text:
            flash("Aucun texte extrait des fichiers.", "danger")
            return render_template('index.html')

        # Résumer chaque document (long ou court)
        docs_summary = []
        for fname, txt in docs_text:
            summary = summarize_long(txt)
            docs_summary.append((fname, summary))

        # Résumé global : sur l’ensemble des résumés individuels
        all_summaries = " ".join([summ for _, summ in docs_summary])
        global_summary = summarize_long(all_summaries)

        return render_template('results.html', docs_summary=docs_summary, global_summary=global_summary)

    return render_template('index.html')

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
