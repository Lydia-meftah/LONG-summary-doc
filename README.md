# SaaS Résumeur M&A - Ultra Long Docs

Résumé plusieurs PDF ou Word longs (juridique, financier...) via HuggingFace (méthode map-reduce) depuis une simple URL web, protégé par login.

## 🚀 Installation

1. Crée `.env` à partir de `.env.example`  
2. Installe les dépendances :
3. Lance :
4. Ouvre [http://localhost:5000](http://localhost:5000) (login : admin / motdepasseultrasecret par défaut)

## ✨ Fonctionnalités
- Upload multi-fichiers .pdf/.docx
- Extraction automatique, découpage en "chunks"
- Résumés intelligents sur des docs TRES LONGS
- Authentification, prêt à déployer SaaS

## 🔐 Sécurité
- Change les identifiants avant toute mise en ligne !
- Utilise HTTPS en prod (Render/Railway le font automatiquement)

## ☁️ Déploiement Cloud
- Ajoute tes variables d’environnement sur Render, Railway, ou Heroku
- Build : `pip install -r requirements.txt`
- Start : `gunicorn app:app`
