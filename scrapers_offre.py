# Récupère les différents modules
from scraper_offre_utils import *  # Fonctions globales
from scraper_offre_wttj import *   # Welcome To The Jungle
from scraper_offre_likd import *   # LinkedIn
from scraper_offre_indd import *   # Indeed
###############################################################################################################################################################################
# Récuperation des paramètres de scraping dans Notion
param_scrap = data_scrap_param_from_notion()

# Filtre sur le mode à 'ON' et regroupement par site à scraper
data_group = {}
for param in param_scrap:
    if param['mode'] == 'ON':
        if param['hebergeur'] not in data_group:
            data_group[param['hebergeur']] = [(param['page_id'], param['poste'], param['date_limite'])]
        else:
            data_group[param['hebergeur']].append((param['page_id'], param['poste'], param['date_limite']))


# Scraping selon le paramétrage
for hebergeur in data_group:      
    if hebergeur == 'WelcomeToTheJungle':
        try:
            scraper_wttj(data_group[hebergeur])
        except Exception as e:
            print(f"Erreur scraper_wttj: {e}")

    elif hebergeur == 'LinkedIn':
        try:
            scraper_likd(data_group[hebergeur])
        except Exception as e:
            print(f"Erreur scraper_likd: {e}")

    elif hebergeur == 'Indeed':
        try:
            scraper_indd(data_group[hebergeur])
        except Exception as e:
            print(f"Erreur scraper_indd: {e}")

    else:
        print(f"ERREUR : hebergeur non reconnu ==> f{hebergeur}")
        print(data_group[hebergeur])