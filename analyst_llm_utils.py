# Bibliotheques utilisés
# # BLOC 1 => API Notion
#########################################################
from notion_client import Client

# BLOC 2 => Fonctions avec le llm
#########################################################
from groq import Groq
import json

# BLOC 3 => Log
#########################################################
import sys
import pytz
from datetime import datetime

# Secrets 
#########################################################
from secrets_analyst_llm import NOTION_API_KEY, DATABASE_OFFRES_ID, GROQ_API_KEY

# CV 
#########################################################
from cv_model import CV_MODEL
###############################################################################################################################################################################
# BLOC 1 => API NOTION
#####################################################################################################
# BLOC 1.1 => Acces au tableau Gestion des candidatures
def recup_offre_a_analyser_from_notion():
    notion = Client(auth=NOTION_API_KEY)
    results = notion.databases.query(database_id=DATABASE_OFFRES_ID)

    pages_id = []
    contenus = []
    for page in results['results'][:]:
        contenu = list(page['properties']['Contenu offre formule']['formula'].values())[1]
        etat = page['properties']["État d'avancement"]['select']['name']
        
        if (contenu != 'Not Found') and (etat == 'À compléter'):
            page_id = page['id']
            pages_id.append(page_id)
            contenus.append(contenu)
    
    return pages_id, contenus

##################################################################################################
# BLOC 1.2 => Maj tableau Gestion des candidatures (synthese et analyse)
def maj_table_candidature_synthese_analyse(page_id, synthese_json, synthese_format, analyse):
    # on decoupe par lot de 2000 characteres et on stocke dans des colonnes non visibles (3 colonnes par variable) qui seront rassemble par formule
    notion = Client(auth=NOTION_API_KEY)
    # Synthese format => sur 3 lots
    if len(synthese_format)%2000 != 0:
        nb = len(synthese_format)//2000
        nb+=1
    synthese_parts = []
    for i in range(nb):
        synthese_parts.append(synthese_format[0+i*2000:2000+i*2000]) 
    for i in range(3-nb):
        synthese_parts.append('')
    
    # Synthese JSON => sur 2 lots
    synthese_json_text = str(synthese_json)
    if len(synthese_json_text)%2000 != 0:
        nb = len(synthese_json_text)//2000
        nb+=1
    synthese_json_parts = []
    for i in range(nb):
        synthese_json_parts.append(synthese_json_text[0+i*2000:2000+i*2000]) 
    for i in range(2-nb):
        synthese_json_parts.append('')

    # Analyse => sur 3 lots
    if len(analyse)%2000 != 0:
        nb = len(analyse)//2000
        nb+=1
    analyse_parts = []
    for i in range(nb):
        analyse_parts.append(analyse[0+i*2000:2000+i*2000]) 
    for i in range(3-nb):
        analyse_parts.append('')

    updated_properties = {
        'synthese json part 1': {
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': synthese_json_parts[0],
                            'link': None
                        }
                    }
                ]
        },
        'synthese json part 2': {
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': synthese_json_parts[1],
                            'link': None
                        }
                    }
                ]
        },
        'synthese part 1': {
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': synthese_parts[0],
                            'link': None
                        }
                    }
                ]
        },
        'synthese part 2': { 
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': synthese_parts[1],
                            'link': None
                        }
                    }
                ]
        },
        'synthese part 3': { 
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': synthese_parts[2],
                            'link': None
                        }
                    }
                ]
        },
        'analyse part 1': { 
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': analyse_parts[0],
                            'link': None
                        }
                    }
                ]
        },
        'analyse part 2': { 
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': analyse_parts[1],
                            'link': None
                        }
                    }
                ]
        },
        'analyse part 3': { 
                'type': 'rich_text',
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {
                            'content': analyse_parts[2],
                            'link': None
                        }
                    }
                ]
        },
        'État d\'avancement': {
            "select": {
                "name": "À rédiger"
                }
        }
    }

    try:
        notion.pages.update(page_id=page_id, properties=updated_properties)
    except Exception as e:
        log(e)

###############################################################################################################################################################################
# BLOC 2 => Fonctions avec le llm
###############################################################################################################################################################################
# Definition variables
# BLOC 2.1 => Format de la synthese de l'offre
format_resultat = """{
    "secteur": "secteur",
    "salaire": "salaire",
    "tele_travail": "tele_travail",
    "lieux": [
    "lieux1",
    "lieux2",
    "lieux3"
    ],
    "resume": "str",
    "competences": [
    "competence 1",
    "competence 2",
    "competence 3"
    ],
    "missions": [
    "mission 1",
    "mission 2",
    "mission 3",
    ],
    "mots cles": [
    "mot cles 1",
    "mot cles 2",
    "mot cles 3",
    ]
}
}"""
##################################################################################################
# BLOC 2.1 => Generation de la synthese de l'offre
def get_synthese(groq, offre: str) -> dict:
    try:
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un professionnel Français du recrutement et tu donne une synthèse de l'offre (en français) en format JSON.\n"
                    f" Le JSON object doit suivre le schema: {format_resultat}.\n"
                    "La valeur pour resume doit être assez étoffé.\n"
                    "Les valeurs possibles pour tele-travail sont 'no-remote', 'mixte' ou 'full-remote'.\n"
                    "Les valeurs pour salaire est 'non renseigné' si pas précisé.\n"
                    "La valeur secteur doit faire référence au domaine d'activité lié à l'entreprise.\n"
                    "Les valeurs compétences doivent être les compétences nécessaire pour l'offre.\n"
                    "Les valeurs missions doivent être les missions présentées dans l'offre.\n"
                    "Les valeurs mots clés doivent être limité à un seul mot ou verbe d'action important."
                    
                },
                {
                    "role": "user",
                    "content": f"Fait moi une synthèse en français de cette offre: {offre}",
                },
            ],
            model="llama3-8b-8192",
            max_tokens = 1900,
            seed = 42,
            temperature = 0.8,
            top_p = 0.8,
            stream=False,
            response_format={"type": "json_object"}
        )
    
        # Conversion de la chaîne en dictionnaire Python
        synthese_json = json.loads(chat_completion.choices[0].message.content)
    
    except groq.APIConnectionError as e:
        erreur = "The server could not be reached.\n" + e.__cause__
        log(erreur)

    except groq.RateLimitError as e:
        erreur = "A 429 status code was received; we should back off a bit."
        log(erreur)

    except groq.APIStatusError as e:
        erreur = "Another non-200-range status code was received.\n" + e.status_code + '\n' + e.response
        log(erreur)


    return synthese_json


def formatage_synthese(synthese_json):
    new_synthese = f"Synthèse:\n{synthese_json['resume']}"
    new_synthese += f"\n\nSecteur: {synthese_json['secteur']}"
    new_synthese += f"\n\nSalaire: {synthese_json['salaire']}"
    new_synthese += f"\n\nTele travail: {synthese_json['tele_travail']}"
    new_synthese += f"\n\nLieux: {synthese_json['lieux']}"
    new_synthese += "\n\nCompétences:"
    
    for competence in synthese_json['competences']:
        new_synthese += f"\n- {competence or ''}"
        
    new_synthese += "\n\nMissions:"
    
    for mission in synthese_json['missions']:
        new_synthese += f"\n- {mission or ''}"
        
    new_synthese += "\n\nMots clés:"
    for mot_cle in synthese_json['mots cles']:
        new_synthese += f"\n- {mot_cle or ''}"
        
    return new_synthese

##################################################################################################
# Bloc 2.2 => Analyse cv pour offre
def get_analyse_cv(groq, offre: str) -> dict:
    messages=[
            {
                "role": "system",
                "content": "Tu es un professionnel Français du recrutement et tu analyse un cv à l'offre en français.\n"
                "Tu veux mettre en avant les points positif et identifier les points négatif ou inutiles.\n"
                "Si tu vois des aspect à mettre plus en avant donne des conseil sur comment faire."
                "Pour la section profil n'hésite pas à adapter une trame."
                "Tu donnera tes remarques en reprenant la structure du cv."
                "Pas de phrase d'introduction ou de conclusion dans ton retour."
                "Si une partie ne nécessite aucun changement ne donne pas de retour dessus."
                f"Le cv à adapter est le suivant : {CV_MODEL}"
            },
            {
                "role": "user",
                "content": f"Analyse moi le cv pour cette offre: {offre}",
            }
    ]
    
    try:
        chat_completion = groq.chat.completions.create(
            messages = messages,
            model="llama3-8b-8192",
            max_tokens = 1500,
            seed = 42,
            temperature = 0.8,
            top_p = 0.8,
            stream=False
        )
    
    except groq.APIConnectionError as e:
        erreur = "The server could not be reached.\n" + e.__cause__
        log(erreur)

    except groq.RateLimitError as e:
        erreur = "A 429 status code was received; we should back off a bit."
        log(erreur)

    except groq.APIStatusError as e:
        erreur = "Another non-200-range status code was received.\n" + e.status_code + '\n' + e.response
        log(erreur)

    return chat_completion.choices[0].message.content

###############################################################################################################################################################################
# BLOC 3 => LOG
def log(erreur):
    # Sauvegarder la valeur actuelle de sys.stdout
    original_stdout = sys.stdout

    # Recuperation de la date d'execution du pgm
    now = datetime.now(pytz.timezone('Europe/Paris')).isoformat()
    date = str(now[:13]) + '-' + str(now[14:16]) + '-' + str(now[17:19])

    # Rediriger stdout vers un fichier
    with open(f'log_analyst_llm_{date}.txt', 'a') as f:
        sys.stdout = f  # Redirige toutes les sorties vers le fichier
        print(erreur)   
        
    # Restaurer stdout pour que le reste des sorties revienne dans la cellule du notebook
    sys.stdout = original_stdout