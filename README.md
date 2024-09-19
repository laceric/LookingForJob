# LookingForJob
Automatisation de recherche d'emploie (scraping des offres, suivi sur Notion, Synthèse LLM et Analyse datas).

Le principe de ce projet est de simplifié la recherche d'emploie en automatisant les tâches les plus répétitives, longues et peu valorisantes.
Pour cela on passe par des programme d'automatisation en python et des bases de données sur Notion.
Et pour le llm on utilise l'api gratuite de Groq (https://console.groq.com/playground).

=========================================================================================================================================================================

Fonctionnement :
1) On définie les paramètres de scraping sur la base de données Notion dédié.
2) On lance le programme de scrapping.
3) On parcours les offres scrapper à partir de leur lien URL, on copie/colle le contenu puis on les passe à l'étape "A compléter" si on souhaite une analyse du LLM.
4) La suite reste manuel.
_____________

Axes de travail : 
- L'ajout du scraping du contenu des offres directement sous forme Json pour simplifier l'étape 3).
- L'ajout d'une base de données pour stoker et normaliser l'ensemble des données des offres afin de mener une analyse pertinante du marché dans le temps.
- L'ajout d'un outils de filtrage pour mieux filtrer et trier les offres selon leur libellé et/ou contenu.
- Une adaptation de l'utilisation du LLM selon les points précédents afin de cibler des questions plus pertinantes sur l'analyse des offres.

=========================================================================================================================================================================

Architechture : 

Bases de données Notion:
- Table des offres => Rassemble les offres d'emploie récupérer avec un grand nombre de caractéristiques qui permettent un bon suivi de la démarche pour postuler.
    lien : https://mighty-neptune-71c.notion.site/106ac98e2bd38072a2c0cc0d7629bd79?v=fffac98e2bd38191adac000c0fad312d&pvs=4
  
- Table de paramétrages => Rassemble les paramètres de webscraping pour chaque poste sur chaque site d'offres d'emploies.
    lien : https://mighty-neptune-71c.notion.site/673eb9e2ba064e6cacb0633b569025d0?v=fffac98e2bd3816191de000cf6103302&pvs=4
__________________________

Programme python :
- Partie Scraping :
  - scrapers_offre.py => programme qui lance le scraping.
  - scrapers_offre_utils.py => Rassembles les fonctions utiles à l'ensembles des procédures de scraping des différents site web.
  - scrapers_offre_wttj.py => Scaper du site Welcome To The Jungle.
  - scrapers_offre_likd.py => Scraper du site LinkedIn.
  - scrapers_offre_indd.py => Scraper du site Indeed.
  - secrets_scraper.py => Rassembles les constantes "Secrètes" nécessaires aux programmes de scraping (A faire évoluer en Secret).

- Partie Analyse LLM :
  - analyst_llm.py => Programme qui lance l'analyse LLM des offres scraper.
  - analyst_llm_utils.py => Rassembles les fonctions utiles pour l'analyse LLM.
  - secrets_analyst_llm.py => Rassemble les constantes "Secrètes" nécessaires aux programmes de scraping. (A faire évoluer en Secret.)
  - cv_model.py => Contient la variable correspondant au contenu d'un modèle de cv sous forme de chaîne de caractères pour l'analyse LLM.
__________________________

 =========================================================================================================================================================================

