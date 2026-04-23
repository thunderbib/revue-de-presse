#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent de revue de presse quotidienne automatisée avec traduction en français.
Récupère 15 articles de sources diversifiées et crédibles.
Catégories prioritaires : Ville de Québec, Province de Québec, Canada, 
Politique États-Unis, Enjeux Internationaux, Géopolitique.
"""

import os
import requests
import urllib.parse
from datetime import datetime, timedelta
from html import escape
import re
import time

# Mois en français
MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
]

def obtenir_date_francaise(date_obj=None):
    """Retourne la date au format français."""
    if date_obj is None:
        date_obj = datetime.now()
    jour = date_obj.day
    mois = MOIS_FR[date_obj.month - 1]
    annee = date_obj.year
    return f"{jour} {mois} {annee}"

def obtenir_horodatage():
    """Retourne l'horodatage complet d'exécution."""
    maintenant = datetime.now()
    jour = maintenant.day
    mois = MOIS_FR[maintenant.month - 1]
    annee = maintenant.year
    heure = maintenant.strftime("%H:%M:%S")
    return f"{jour} {mois} {annee} à {heure}"

def traduire_google(texte):
    """Traduit du texte en français via Google Translate."""
    if not texte or len(texte) < 2:
        return texte
    
    try:
        texte_encode = urllib.parse.quote(texte[:500])
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=fr&dt=t&q={texte_encode}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            try:
                data = response.json()
                if data and len(data) > 0 and len(data[0]) > 0 and len(data[0][0]) > 0:
                    return data[0][0][0]
            except:
                return texte
        
        return texte
    except:
        return texte

def filtrer_articles(articles, mots_cles_exclure=None):
    """
    Filtre les articles pour exclure le contenu non pertinent.
    Exclut notamment les articles sportifs et le contenu faible.
    """
    if mots_cles_exclure is None:
        mots_cles_exclure = [
            'sport', 'football', 'hockey', 'baseball', 'basketball', 'nfl', 'nba', 'nhl',
            'mma', 'boxing', 'wrestling', 'tennis', 'golf', 'soccer', 'rugby',
            'transfert', 'match', 'équipe', 'joueur', 'entraîneur', 'coach',
            'victoire', 'défaite', 'score', 'but', 'panier', 'essai',
            'ligue', 'coupe', 'championnat', 'tournoi', 'olympique',
            'célébrity gossip', 'entertainment', 'showbiz', 'actor', 'movie',
            'award', 'festival', 'concert', 'singer', 'album'
        ]
    
    articles_filtres = []
    for article in articles:
        titre = article.get("title", "").lower()
        description = article.get("description", "").lower()
        
        # Vérifier si c'est du contenu à exclure
        est_exclu = any(mot in titre or mot in description for mot in mots_cles_exclure)
        
        # Vérifier la qualité minimale
        a_contenu_suffisant = (
            article.get("description") and 
            len(article.get("description", "")) > 80 and
            article.get("title") and
            len(article.get("title", "")) > 15
        )
        
        if not est_exclu and a_contenu_suffisant:
            articles_filtres.append(article)
    
    return articles_filtres

def recuperer_articles():
    """
    Récupère les articles avec les priorités suivantes :
    1. Ville de Québec (3 articles)
    2. Province de Québec (3 articles)
    3. Canada (2 articles)
    4. Politique États-Unis (2 articles)
    5. Enjeux Internationaux majeurs (3 articles)
    6. Géopolitique (2 articles)
    """
    api_key = os.getenv("NEWSAPI_KEY", "")
    
    if not api_key:
        print("❌ Erreur : NEWSAPI_KEY non configurée.")
        exit(1)
    
    # Configuration des requêtes par priorité
    categories = {
        "quebec_ville": {
            "queries": [
                "Quebec City government",
                "Ville de Quebec policy",
                "Quebec City municipal",
                "Montreal downtown development",
                "City of Montreal council"
            ],
            "count": 3,
            "label": "VILLE DE QUÉBEC"
        },
        "quebec_province": {
            "queries": [
                "Quebec government policy",
                "Province of Quebec legislation",
                "Quebec National Assembly",
                "Assemblée nationale Quebec",
                "Quebec provincial budget"
            ],
            "count": 3,
            "label": "PROVINCE DE QUÉBEC"
        },
        "canada": {
            "queries": [
                "Canadian parliament",
                "Canada federal government",
                "Ottawa parliament",
                "Prime Minister Canada",
                "Canadian economy policy"
            ],
            "count": 2,
            "label": "CANADA"
        },
        "usa_politics": {
            "queries": [
                "US politics",
                "White House",
                "Congress",
                "Senate",
                "Trump Biden presidency"
            ],
            "count": 2,
            "label": "ÉTATS-UNIS"
        },
        "international": {
            "queries": [
                "Middle East conflict",
                "Ukraine Russia war",
                "China Taiwan",
                "Europe politics",
                "International crisis"
            ],
            "count": 3,
            "label": "INTERNATIONAL"
        },
        "geopolitique": {
            "queries": [
                "geopolitics",
                "UN UN security council",
                "International relations",
                "NATO",
                "Trump Putin"
            ],
            "count": 2,
            "label": "GÉOPOLITIQUE"
        }
    }
    
    articles_par_categorie = {}
    date_hier = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    
    try:
        for categorie, config in categories.items():
            print(f"  📡 Récupération {config['label']}...")
            articles_par_categorie[categorie] = []
            
            for query in config["queries"]:
                params = {
                    "q": query,
                    "apiKey": api_key,
                    "from": date_hier,
                    "sortBy": "relevancy",
                    "language": "en",
                    "pageSize": 50
                }
                
                try:
                    response = requests.get(
                        "https://newsapi.org/v2/everything",
                        params=params,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        articles_par_categorie[categorie].extend(
                            data.get("articles", [])
                        )
                except requests.exceptions.RequestException:
                    continue
            
            # Filtrer et dédupliquer
            articles_par_categorie[categorie] = filtrer_articles(
                articles_par_categorie[categorie]
            )
            
            # Dédupliquer par titre
            titres_vus = set()
            articles_uniques = []
            for article in articles_par_categorie[categorie]:
                titre = article.get("title", "").lower()
                if titre not in titres_vus:
                    articles_uniques.append(article)
                    titres_vus.add(titre)
            
            articles_par_categorie[categorie] = articles_uniques[:config["count"] * 2]
        
        return articles_par_categorie
    
    except Exception as e:
        print(f"❌ Erreur : {e}")
        exit(1)

def generer_html(articles_par_categorie):
    """Génère le HTML avec articles traduits en français."""
    date_aujourd_hui = obtenir_date_francaise()
    horodatage = obtenir_horodatage()
    html_articles = ""
    numero = 1
    
    # Configuration des catégories avec labels
    categories_ordre = [
        ("quebec_ville", "VILLE DE QUÉBEC", 3),
        ("quebec_province", "PROVINCE DE QUÉBEC", 3),
        ("canada", "CANADA", 2),
        ("usa_politics", "ÉTATS-UNIS", 2),
        ("international", "INTERNATIONAL", 3),
        ("geopolitique", "GÉOPOLITIQUE", 2)
    ]
    
    articles_selectionnes = []
    
    # Sélectionner les articles par catégorie
    for cat_key, label, count in categories_ordre:
        for article in articles_par_categorie.get(cat_key, [])[:count]:
            articles_selectionnes.append((label, article))
    
    print(f"\n🌐 Traduction des {len(articles_selectionnes[:15])} articles...")
    
    # Générer les articles
    for idx, (label, article) in enumerate(articles_selectionnes[:15]):
        titre_en = article.get("title", "Sans titre")
        desc_en = article.get("description", "")
        
        print(f"  [{idx+1}/15] {label}: {titre_en[:50]}...")
        
        titre_fr = traduire_google(titre_en)
        time.sleep(0.3)
        desc_fr = traduire_google(desc_en)
        
        source = escape(article.get("source", {}).get("name", "Unknown"))
        date_article = article.get("publishedAt", "")[:10]
        
        html_articles += f"""
                    <article>
                        <div class="article-image"></div>
                        <div class="article-header">
                            <span class="category-badge">{label}</span>
                            <h3>{escape(titre_fr)}</h3>
                            <div class="article-meta">Date de la nouvelle : {date_article}</div>
                            <p class="article-excerpt">{escape(desc_fr[:250])}...</p>
                            <div class="article-footer">
                                <span class="read-time">Source : {source}</span>
                            </div>
                        </div>
                    </article>
"""
        numero += 1
    
    # Remplir jusqu'à 15
    while numero <= 15:
        html_articles += f"""
                    <article>
                        <div class="article-image"></div>
                        <div class="article-header">
                            <span class="category-badge">ACTUALITÉS</span>
                            <h3>En attente de données...</h3>
                            <div class="article-meta">Date de la nouvelle : {date_aujourd_hui}</div>
                            <p class="article-excerpt">Les données pour cet article se chargeront lors de la prochaine exécution.</p>
                            <div class="article-footer">
                                <span class="read-time">Revue de Presse Automatisée</span>
                            </div>
                        </div>
                    </article>
"""
        numero += 1
    
    # Template HTML complet
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Revue de Presse Quotidienne</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Courier+Prime:wght@400;700&display=swap');

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        html {{
            scroll-behavior: smooth;
        }}

        body {{
            font-family: 'Courier Prime', monospace;
            line-height: 1.6;
            color: #1a1a1a;
            background-color: #e8e4d0;
            padding: 15px;
        }}

        header {{
            background-color: #fff8f0;
            border: 6px solid #1a1a1a;
            border-top: 12px solid #1a1a1a;
            border-bottom: 15px double #1a1a1a;
            padding: 25px 30px;
            text-align: center;
            margin-bottom: 0;
            box-shadow: 5px 5px 0px rgba(0, 0, 0, 0.2);
            position: relative;
        }}

        header::before {{
            content: '';
            position: absolute;
            top: 45px;
            left: 30px;
            right: 30px;
            height: 2px;
            background: #1a1a1a;
            box-shadow: 0 4px 0 #1a1a1a, 0 8px 0 #1a1a1a;
        }}

        header .content {{
            position: relative;
            z-index: 1;
        }}

        header h1 {{
            font-family: 'Playfair Display', serif;
            font-size: 4.5em;
            font-weight: 900;
            margin: 15px 0 10px 0;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: #1a1a1a;
            line-height: 1;
            text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.1);
        }}

        header .subtitle {{
            font-family: 'Courier Prime', monospace;
            font-size: 1.2em;
            margin: 10px 0;
            font-weight: bold;
            color: #333;
            letter-spacing: 3px;
            text-transform: uppercase;
        }}

        header .tagline {{
            font-style: italic;
            font-size: 0.9em;
            color: #555;
            margin: 8px 0 15px 0;
            letter-spacing: 1px;
        }}

        header .date-banner {{
            display: inline-block;
            padding: 8px 20px;
            border: 3px solid #1a1a1a;
            background: #fff8f0;
            font-family: 'Courier Prime', monospace;
            font-size: 1em;
            font-weight: bold;
            margin-top: 15px;
            letter-spacing: 2px;
        }}

        header .date-banner strong {{
            color: #1a1a1a;
            display: inline;
            font-weight: bold;
            margin-left: 8px;
        }}

        header .info-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            margin-top: 15px;
            border-top: 2px solid #1a1a1a;
            border-bottom: 2px solid #1a1a1a;
            font-family: 'Courier Prime', monospace;
            font-size: 0.95em;
            font-weight: bold;
        }}

        header .timestamp {{
            font-size: 0.85em;
            color: #666;
            font-style: italic;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed #1a1a1a;
        }}

        nav {{
            background: #1a1a1a;
            padding: 12px 30px;
            display: flex;
            justify-content: center;
            gap: 40px;
            flex-wrap: wrap;
            border-bottom: 8px solid #333;
        }}

        nav span {{
            color: #fff8f0;
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-family: 'Courier Prime', monospace;
            padding: 4px 8px;
        }}

        .container {{
            max-width: 100%;
            margin: 0;
            background: #fff8f0;
            padding: 30px;
            border-left: 8px solid #1a1a1a;
            border-right: 8px solid #1a1a1a;
        }}

        .articles-section h2 {{
            font-family: 'Playfair Display', serif;
            font-size: 2em;
            color: #1a1a1a;
            margin-bottom: 20px;
            text-align: left;
            padding-bottom: 12px;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 2px;
            border-bottom: 4px double #1a1a1a;
            border-top: 2px solid #1a1a1a;
            padding-top: 12px;
        }}

        .articles-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }}

        article {{
            background: #fff8f0;
            border: 3px solid #1a1a1a;
            overflow: hidden;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            height: 100%;
            box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.12);
        }}

        article:hover {{
            transform: translate(3px, 3px);
            box-shadow: 0 0 0px rgba(0, 0, 0, 0.12);
        }}

        article .article-image {{
            height: 160px;
            background: linear-gradient(45deg, #d4d0c8 25%, transparent 25%, transparent 75%, #d4d0c8 75%, #d4d0c8),
                        linear-gradient(45deg, #d4d0c8 25%, transparent 25%, transparent 75%, #d4d0c8 75%, #d4d0c8);
            background-size: 15px 15px;
            background-position: 0 0, 7.5px 7.5px;
            background-color: #c4c0b8;
            border-bottom: 3px solid #1a1a1a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75em;
            color: #666;
            text-align: center;
            padding: 12px;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }}

        article .article-image::before {{
            content: '[PHOTO]';
            letter-spacing: 1px;
        }}

        article .article-header {{
            padding: 15px;
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            border-bottom: 2px dashed #1a1a1a;
        }}

        article .category-badge {{
            display: inline-block;
            background: #f0f0e8;
            color: #1a1a1a;
            padding: 4px 8px;
            border: 2px solid #1a1a1a;
            font-size: 0.65em;
            font-weight: bold;
            margin-bottom: 8px;
            width: fit-content;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-family: 'Courier Prime', monospace;
        }}

        article h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.2em;
            color: #1a1a1a;
            margin-bottom: 8px;
            line-height: 1.2;
            flex-grow: 1;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        article .article-meta {{
            color: #333;
            font-weight: bold;
            font-size: 0.75em;
            margin-bottom: 8px;
            font-family: 'Courier Prime', monospace;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}

        article .article-excerpt {{
            color: #1a1a1a;
            font-size: 0.9em;
            line-height: 1.6;
            margin-bottom: 10px;
            flex-grow: 1;
            text-align: justify;
            font-family: 'Courier Prime', monospace;
        }}

        article .article-footer {{
            padding: 10px 0;
            font-size: 0.8em;
        }}

        article .read-time {{
            color: #666;
            font-style: italic;
            font-family: 'Courier Prime', monospace;
            font-weight: bold;
        }}

        .sidebar {{
            background: #f0f0e8;
            border: 3px double #1a1a1a;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 3px 3px 0px rgba(0, 0, 0, 0.1);
        }}

        .sidebar h3 {{
            font-family: 'Playfair Display', serif;
            font-size: 1.3em;
            color: #1a1a1a;
            margin-bottom: 10px;
            font-weight: 900;
            text-transform: uppercase;
            border-bottom: 2px solid #1a1a1a;
            padding-bottom: 8px;
            letter-spacing: 1px;
        }}

        .sidebar p {{
            font-family: 'Courier Prime', monospace;
            font-size: 0.9em;
            color: #1a1a1a;
            margin-bottom: 8px;
            line-height: 1.6;
            text-align: justify;
        }}

        .update-timestamp {{
            background: #e8e4d0;
            border: 1px solid #1a1a1a;
            padding: 10px;
            margin-top: 15px;
            text-align: center;
            font-size: 0.85em;
            font-style: italic;
            color: #666;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 3em;
            }}
            .articles-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @keyframes slideInUp {{
            from {{
                opacity: 0;
                transform: translateY(15px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        article {{
            animation: slideInUp 0.6s ease-out;
        }}
    </style>
</head>
<body>
    <header>
        <div class="content">
            <h1>REVUE DE PRESSE</h1>
            <p class="subtitle">ÉDITION QUOTIDIENNE</p>
            <p class="tagline">~ Actualités et tendances du jour ~</p>
            <div class="info-row">
                <span>MONTRÉAL - QUÉBEC</span>
                <div class="date-banner">
                    Édition du <strong>Date du jour : {date_aujourd_hui}</strong>
                </div>
                <span>AUTOMATISÉE</span>
            </div>
            <div class="timestamp">
                🕐 Mise à jour le {horodatage}
            </div>
        </div>
    </header>

    <nav>
        <span>QUÉBEC</span>
        <span>CANADA</span>
        <span>ÉTATS-UNIS</span>
        <span>INTERNATIONAL</span>
        <span>GÉOPOLITIQUE</span>
    </nav>

    <div class="container">
        <section class="articles-section">
            <h2>ACTUALITÉS DU JOUR - 15 POINTS CLÉS</h2>
            <div class="articles-grid">
{html_articles}
            </div>
        </section>

        <aside class="sidebar">
            <h3>À PROPOS DE CETTE REVUE</h3>
            <p><strong>Priorités de couverture :</strong></p>
            <p>1. Ville de Québec • 2. Province de Québec • 3. Canada • 4. Politique États-Unis • 5. Enjeux Internationaux • 6. Géopolitique</p>
            <p><strong>Traduction :</strong> Tous les articles sont traduits en français via Google Translate.</p>
            <p><strong>Mise à jour :</strong> Quotidienne à 07:00 heure de Québec avec sources crédibles.</p>
            <p><strong>Dernière exécution :</strong> {horodatage}</p>
            <div class="update-timestamp">
                ✓ Revue générée le {horodatage}
            </div>
        </aside>
    </div>
</body>
</html>
"""
    
    return html

def main():
    """Fonction principale."""
    print("\n" + "="*60)
    print("🗞️  REVUE DE PRESSE QUOTIDIENNE - ÉDITION PRIORITAIRE")
    print("="*60)
    print(f"🕐 Exécution lancée le {obtenir_horodatage()}")
    print("="*60)
    
    print("\n📰 Récupération des articles prioritaires...")
    articles = recuperer_articles()
    
    print("\n✏️  Génération du HTML...")
    html_content = generer_html(articles)
    
    print("\n💾 Sauvegarde du fichier...")
    try:
        with open("revue-de-presse.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\n✅ Succès! Revue mise à jour : {obtenir_date_francaise()}")
        print(f"🕐 Horodatage : {obtenir_horodatage()}")
        print("="*60)
        exit(0)
    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        exit(1)

if __name__ == "__main__":
    main()
