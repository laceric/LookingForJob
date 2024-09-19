
# Bibliothèques utilisées
# BLOC 1 => API Notion
#########################################################
from notion_client import Client

# BLOC 2 => Session Selenium
#########################################################
from selenium import webdriver
from selenium.webdriver.common.by import By 

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# BLOC 3 => Heure actuelle de paris
#########################################################
import pytz
from datetime import datetime

# Secrets 
#########################################################
from secrets_scraper import NOTION_API_KEY, DATABASE_OFFRES_ID,  DATABASE_PARAM_SCRAP_OFFRES_ID, CHROME_PROFILE_PATH, EXECUTABLE_PATH_CHROME_SERVICE
###############################################################################################################################################################################

# BLOC 1 => API NOTION
#####################################################################################################
# BLOC 1.1 => Fonction pour Récuperation du paramétrage dans Notion
def data_scrap_param_from_notion():
    # Accès au tableau Paramètres_scraping
    notion = Client(auth=NOTION_API_KEY)
    results = notion.databases.query(database_id=DATABASE_PARAM_SCRAP_OFFRES_ID)
    
    return recup_data_scrap_param_from_notion(results)

def recup_data_scrap_param_from_notion(results):
    # Accès au tableau Paramètres_scraping 
    data = []
    for page in results['results']:
        data_page = {}
        try:
            data_page['page_id'] = page['id']
        except:
            data_page['page_id'] = None

        try:
            data_page['mode'] = page['properties']['Mode']['select']['name']
        except:
            data_page['mode'] = None

        try:
            data_page['hebergeur'] = page['properties']['Hébergeur']['select']['name']
        except:
            data_page['hebergeur'] = None

        try:
            data_page['date_limite'] = page['properties']['Date Limite']['formula']['date']['start']
        except:
            data_page['date_limite'] = None

        try:
            data_page['poste'] = page['properties']['Poste']['select']['name']
        except:
            data_page['poste'] = None

        data.append(data_page)

    return data


##################################################################################################
# BLOC 1.2 => Accès au tableau Gestion des candidatures
def recup_cle_existantes_from_notion(hebergeur_ref):
    notion = Client(auth=NOTION_API_KEY)
    results = notion.databases.query(database_id=DATABASE_OFFRES_ID)
    
    cles = []
    for page in results['results']:
        try:
            hebergeur = page['properties']['Site Hébergeur']['select']['name']
        except:
            hebergeur = None
        if hebergeur == hebergeur_ref:
            if hebergeur == 'Welcome To The Jungle':
                try:
                    # clé (entreprise + date_crea + intitule_poste)
                    entreprise = page['properties']['Entreprise']['title'][0]['plain_text']
                    date_crea = page['properties']['Date de création']['date']['start']
                    intitule_poste = page['properties']['intitulé de poste']['rich_text'][0]['plain_text']

                    cles.append(entreprise+date_crea+intitule_poste)

                except Exception as e:
                    print(f"Erreur de récupération de la clé Welcome To The Jungle : {e}")
                    continue

            elif hebergeur == 'LinkedIn':
                try:
                    # clé (url de l'offre [-10:])
                    id_offre = page['properties']["URL de l'offre"]['url'][-10:]
                    cles.append(id_offre)
                    
                except Exception as e:
                    print(f"Erreur de récupération de la clé LinkedIn : {e}")
                    continue

            elif hebergeur == 'Indeed':
                try:
                    # clé (url de l'offre split('=')[1])
                    id_offre = page['properties']["URL de l'offre"]['url'].split('=')[1]
                    cles.append(id_offre)
                    
                except Exception as e:
                    print(f"Erreur de récupération de la clé Indeed : {e}")
                    continue
        
    return cles


#####################################################################################################
# BLOC 1.3 => Mise à jour de la base de données scrap param post batch
def maj_table_scrap_param_post_batch(new_date, page_id, top_ajout):
    # Accès au tableau Paramètres_scraping pour mettre à jour date de dernier batch et délais
    notion = Client(auth=NOTION_API_KEY)

    # Avec ajout d'offre
    if top_ajout:
        updated_properties = {
            "Date dernier ajout": {
                "date": {
                    "start": new_date,
                    "end": None
                }
            },
            "Date dernier batch": {
                "date": {
                    "start": new_date,
                    "end": None
                }
            },
            "Délais": {
                "number": None
            }
        }
        
    # Sans ajout d'offre
    else:
        updated_properties = {
            "Date dernier batch": {
                "date": {
                    "start": new_date,
                    "end": None
                }
            },
            "Délais": {
                "number": None
            }
        }
        
    notion.pages.update(page_id=page_id, properties=updated_properties)

#####################################################################################################
# BLOC 1.4 => Mise à jour de la base de données offre pour ajouter une offre
def ajout_candidature_to_notion(data):
    # Accès au tableau Gestion des candidatures
    notion = Client(auth=NOTION_API_KEY)
    try:
        notion.pages.create(
            parent={"database_id": DATABASE_OFFRES_ID},
            properties={
                'Entreprise': {
                    'title': [
                        {
                            'type': 'text',
                            'text': {
                                'content': data['entreprise'],
                                'link': None
                            }
                        }
                    ]
                },
                'URL Logo': {
                    'type': 'url',
                    'url': data['logo_url']
                },
                'URL de l\'offre': {
                    'type': 'url',
                    'url': data['url_offre']
                },
                'Poste': {
                    "select": {
                        "name": data['poste']
                        }
                },
                'Site Hébergeur': {
                    "select": {
                        "name": data['hebergeur']
                        }
                },
                'État d\'avancement': {
                    "select": {
                        "name": "À lire"
                        }
                },
                'Statut': {
                    "select": {
                        "name": "A faire"
                        }
                },
                'Priorité': {
                    "select": { 
                        "name": 'À définir'
                        }
                },
                'intitulé de poste': {
                    'type': 'rich_text',
                    'rich_text': [
                        {
                            'type': 'text',
                            'text': {
                                'content': data['intitule_poste'],
                                'link': None
                            }
                        }
                    ]
                },
                'Date de création': {
                    'type': 'date',
                    'date': {
                        'start': data['date_crea_iso'],
                        'end': None
                    }
                },
                'Date de récupération': {
                    'type': 'date',
                    'date': {
                        'start': data['now'],
                        'end': None
                    }
                },
                'URL page entreprise': {
                    'type': 'url',
                    'url': data['page_entreprise']
                },
                'Contenu offre': {
                    'type': 'rich_text',
                    'rich_text': [
                        {
                            'type': 'text',
                            'text': {
                                'content': data['contenu'],
                                'link': None
                            }
                        }
                    ]
                }
            }
        )

    except Exception as e:
        print(f"Erreur maj to notion : {e}")
###############################################################################################################################################################################
# BLOC 2 => Session Selenium
def lancement_session_selenium():
    # Configuration des options Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-search-engine-choice-screen")
    chrome_options.add_argument(f"user-data-dir={CHROME_PROFILE_PATH}")

    # Initialisation du service ChromeDriver
    service = Service(executable_path = EXECUTABLE_PATH_CHROME_SERVICE)


    # Initialisation du navigateur
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    return driver


###############################################################################################################################################################################
# BLOC 3 => Opération redontantes sur date et heure
##################################################################################################
# BLOC 3.1 => Heure actuelle de paris
def heure_now_in_paris(format_now = None):
    # Fuseau horaire de Paris
    paris_tz = pytz.timezone('Europe/Paris')
    
    if format_now == 0:
        # Obtenir l'heure actuelle à Paris en datetime
        return datetime.now(paris_tz) 
    
    elif format_now == 1:
        # Obtenir l'heure actuelle à Paris au format ISO
        return datetime.now(paris_tz).isoformat()
    
    else :
        # Obtenir l'heure actuelle à Paris au format datetime et ISO
        return datetime.now(paris_tz), datetime.now(paris_tz).isoformat()
    



##################################################################################################
# BLOC 3.2 => Ecart en jour entre une date iso et l'heure actuelle de paris
def nb_jour(date_limite):
    # Obtenir l'heure actuelle à Paris aux format datetime
    now_paris_dt = heure_now_in_paris(0)

    # Conversion du format de la date limite from iso to datetime
    date_limite = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))

    time_limite = now_paris_dt - date_limite

    # Extraire le nombre de jours
    days_difference = time_limite.days
    return days_difference