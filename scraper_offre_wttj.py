# Bibliothèques utilisées
import time
import pytz
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# Récupère les différents modules
from scraper_offre_utils import *  # Fonctions globales
###############################################################################################################################################################################
##################################################################################################
def scraper_wttj(params):
    # Accès au tableau Gestion des candidatures pour stocker les clés des offres dejà récupérer
    cle_existantes = recup_cle_existantes_from_notion('Welcome To The Jungle')

    # Initialisation du navigateur
    driver = lancement_session_selenium()

    # URL spécifique pour lieu : île-de-France
    url_base = "https://www.welcometothejungle.com/fr/jobs?refinementList%5Boffices.country_code%5D%5B%5D=FR&refinementList%5Boffices.state%5D%5B%5D=Ile-de-France&refinementList%5Bcontract_type%5D%5B%5D=full_time&page=1&aroundQuery=%C3%8Ele-de-France%2C%20France&query="

    for page_id, poste, date_limite in params:
        url = url_base + poste.replace(" ", "%20")
        driver.get(url)
        time.sleep(3)

        driver.find_element(By.ID, "search-only-title-toggle").click()

        time.sleep(3)

        driver.find_element(By.CSS_SELECTOR, "[data-testid='jobs-search-sortby-dropdown']").click()

        driver.find_element(By.CSS_SELECTOR, "[data-testid='jobs-search-sortby-mostRecent']").click()

        time.sleep(3)

        recup_offres_data_wttj(driver, cle_existantes, poste, date_limite, page_id)
    
    driver.quit()


##################################################################################################
def recup_offres_data_wttj(driver, cle_existantes, poste, date_limite, page_id):
    # Obtenir l'heure actuelle à Paris aux format datetime et iso
    now_paris_dt, now_paris_iso = heure_now_in_paris()

    # Conversion du format de la date limite from iso to datetime
    date_limite = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))

    time_limite = now_paris_dt - date_limite

    # Définition du top si ajout offre à la base de données
    top_ajout = False

    # Récupérer l'ensemble du code HTML
    html_code = driver.page_source
    soup = BeautifulSoup(html_code, 'html.parser')

    # On vérifie qu'il y a des offres
    liste_offres = soup.find_all(attrs={"data-testid": "search-results-list-item-wrapper"})

    if liste_offres:
        # On recherche le nombre de page s'il y a (sinon 1 page)
        try:
            nb_page = int(soup.find(attrs={"aria-label": "Pagination"}).find('ul').find_all('li')[-2].text)

        except Exception as e:
            nb_page = 1

        # Définition d'un top pour dire qu'on a fini de parcourir les offres ou pas
        top_out = False
        page_actuelle = 1

        while not top_out:   
            if page_actuelle == nb_page:
                top_out = True          

            for offre in liste_offres:
                # formatage date_crea
                date_crea = offre.time['datetime']
                date_crea_dt = datetime.strptime(date_crea, '%Y-%m-%dT%H:%M:%SZ').replace(second=0, microsecond=0).replace(tzinfo=pytz.timezone('Europe/Paris'))

                # Calculer l'écart entre les deux dates
                time_difference = now_paris_dt - date_crea_dt

                if time_difference <= time_limite:
                    top_ajout = maj_wttj_to_notion(offre, date_crea_dt, now_paris_iso, poste, cle_existantes, top_ajout)
                else:
                    top_out = True
                    break

            if top_out == False :
                # On passe à la page suivante
                driver.find_element(By.CSS_SELECTOR, '[aria-label="Pagination"]').find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')[-1].click()
                time.sleep(3)

                page_actuelle += 1

                # Recuperer l'ensemble du code HTML
                html_code = driver.page_source
                soup = BeautifulSoup(html_code, 'html.parser')
                liste_offres = soup.find_all(attrs={"data-testid": "search-results-list-item-wrapper"})
    
    maj_table_scrap_param_post_batch(now_paris_iso, page_id, top_ajout)


##################################################################################################
def maj_wttj_to_notion(offre, date_crea_dt, now_paris_iso, poste, cle_existantes, top_ajout):
    data = {}
    try:
        ###########################################
        data['entreprise'] = offre.find('span').text
        ###########################################
        images = offre.find_all('img')
        data['logo_url'] = images[1]['src']
        ###########################################
        links = offre.find_all('a', href=True)
        data['intitule_poste'] = links[1].text
        ###########################################
        data['url_offre'] = "https://www.welcometothejungle.com" + links[1]['href']
        ###########################################
        data['date_crea_iso'] = date_crea_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
        ###########################################
        data['hebergeur'] = "Welcome To The Jungle"
        ###########################################
        data['now'] = now_paris_iso
        ###########################################
        data['poste'] = poste

        ###########################################
        # Scrap de la page de l'offre
        data['page_entreprise'], data['contenu'] = scrap_page_offre_wttj(data['url_offre'])

        cle = str(data['entreprise']+data['date_crea_iso']+data['intitule_poste'])

        if cle not in cle_existantes:
            # Ajout à Notion via api
            ajout_candidature_to_notion(data)
            top_ajout = True

    except Exception as e:
        print(f"Erreur récup data : {e}")
        
    return top_ajout


##################################################################################################
def scrap_page_offre_wttj(url_offre):    
    # Envoyez une requête GET à l'URL
    html_code = requests.get(url_offre)
    soup = BeautifulSoup(html_code.content, 'html.parser')

    # Recherche du lien de la page de l'entreprise
    try:
        a_tag = soup.find(attrs={"data-testid": "job-metadata-block"}).find('a', href=True)
        href_value = a_tag['href']
        page_entreprise = "https://www.welcometothejungle.com" + href_value
    except:
        page_entreprise = "Not Found"

    # Extraire le contenu de l'offre  => Pour l'instant cette partie n'est pas traitée
    try:
#         contenu = str(soup.find_all(id="the-position-section")[0])
        contenu = "Not Found"
    except:
        contenu = "Not Found"
    
    return page_entreprise, contenu