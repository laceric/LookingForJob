# Bibliothèques utilisées
import time
import pytz
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup

# Récupere les différents modules
from scraper_offre_utils import *  # Fonctions globales
###############################################################################################################################################################################
##################################################################################################
def scraper_likd(params):
    # Accès au tableau Gestion des candidatures pour stocker les clés des offres déja récupérer
    cle_existantes = recup_cle_existantes_from_notion('LinkedIn')

    # Initialisation du navigateur
    driver = lancement_session_selenium()

    # On vérifie qu'on est connecté au compte
    try:
        URL_SITE = "https://www.linkedin.com/feed"
        driver.get(URL_SITE)
        time.sleep(3)

    except:
        print("Erreur de connexion au compte LinkedIn")
        return
    
    
    URL_START = "window.open('https://www.linkedin.com/jobs/search/?&f_E=2&geoId=104246759&keywords=%22"
    URL_END = "%22', '_blank');"

    for page_id, poste, date_limite in params:
        url = URL_START + poste.replace(" ", "%20") + URL_END
        
        scrap_page_poste_likd(driver, url, date_limite)
        
        
        # Définition du top si ajout offre à la base de données
        top_ajout = False

        # Vérifier qu'il y a des offres
        try:
            driver.find_element(By.CLASS_NAME, "jobs-search-no-results-banner__image")

        except:
            page_actuelle = 1

            # Définition d'un top pour dire qu'on a fini de parcourir les offres ou pas
            top_out = False
            while not top_out:
                top_ajout = traitement_liste_offre_likd(driver, top_ajout, cle_existantes, poste, date_limite)
                        
                top_out = lecture_liste_page_likd(driver, page_actuelle)
    
        # Obtenir l'heure actuelle à Paris aux format iso
        now_paris_iso = heure_now_in_paris(1)

        maj_table_scrap_param_post_batch(now_paris_iso, page_id, top_ajout)

    driver.quit()


##################################################################################################
def scrap_page_poste_likd(driver, url, date_limite):
    # Ouvrir un nouvel onglet avec une URL spécifique
    driver.execute_script(url)

    # Attendre un moment pour etre sur que le nouvel onglet est ouvert
    time.sleep(2) 

    # Obtenir les handles de tous les onglets
    handles = driver.window_handles

    # Basculer vers le dernier onglet
    driver.switch_to.window(handles[-1])
    time.sleep(3)

    # calcul nombre de jour d'ecart
    ecart_jours = nb_jour(date_limite)
    
    if ecart_jours <=31:
        # Choix filtre
        driver.find_element(By.CSS_SELECTOR, 'button[aria-label="Afficher tous les filtres. En cliquant sur ce bouton, toutes les options de filtres disponibles apparaîtront."]').click()
        time.sleep(3)

        if ecart_jours < 1:
            # last 24h
            driver.find_element(By.CSS_SELECTOR, "label[for='advanced-filter-timePostedRange-r86400']").click()
            time.sleep(3)
        
        elif ecart_jours < 7:
            # last semaine
            driver.find_element(By.CSS_SELECTOR, "label[for='advanced-filter-timePostedRange-r604800']").click()
            time.sleep(3)
            
        else:
            # last mois
            driver.find_element(By.CSS_SELECTOR, "label[for='advanced-filter-timePostedRange-r2592000']").click()
            time.sleep(3)

        # valider choix
        driver.find_element(By.CLASS_NAME, "artdeco-button--primary").click()
        time.sleep(3)


##################################################################################################
def traitement_liste_offre_likd(driver, top_ajout, cle_existantes, poste, date_limite):
    ul_element = driver.find_element(By.CLASS_NAME, "scaffold-layout__list-container")

    # Trouver tous les éléments <li> à l'interieur du <ul>
    li_elements = ul_element.find_elements(By.TAG_NAME, "li")

    # Parcourir chaque <li> et cliquer dessus
    for li in li_elements:
        # Afficher l'id
        id_value = None

        try :
            id_value = li.get_attribute('id')
            if id_value[:5] == 'ember':
            # Cliquer sur l'element <li>
                li.click()
                time.sleep(1)

                # Recuperer l'ensemble du code HTML
                html_code = driver.page_source
                time.sleep(1)

                ajout = recup_offres_data_likd(html_code, cle_existantes, poste, date_limite)

                if ajout:
                    top_ajout = True

        except Exception as e:
            print(f"Erreur offre ({id_value}) : {e}")
            continue

    return top_ajout


##################################################################################################
def lecture_liste_page_likd(driver, page_actuelle):
    try:
        # Localiser le conteneur <ul> contenant les <li>
        ul_page = driver.find_element(By.CSS_SELECTOR, 'ul.artdeco-pagination__pages')
    
    except:
        top_out = True
        return top_out

    # Trouver tous les éléments <li> à l'interieur du <ul>
    li_page = ul_page.find_elements(By.TAG_NAME, 'li')

    next_page = False
    # Itérer sur chaque élément <li> et récupérer des informations
    for li in li_page:
        button = li.find_element(By.TAG_NAME, 'button')  # Trouver le <button> à l'interieur du <li>
        page_number = button.find_element(By.TAG_NAME, 'span').text  # Obtenir le texte du <span>


        if next_page:
            page_actuelle +=1
            button.click()
            time.sleep(2)
            top_out = False
            break

        try: 
            pg_num = int(page_number)
        except: 
            pg_num = 0

        if pg_num == page_actuelle:
            next_page = True

        if li == li_page[-1]:
            top_out = True
    return top_out


##################################################################################################
def recup_offres_data_likd(html_code, cle_existantes, poste, date_limite):
    top_ajout = False
    soup = BeautifulSoup(html_code, 'html.parser')
    
    # Obtenir l'heure actuelle à Paris aux format datetime et iso
    now_paris_dt, now_paris_iso = heure_now_in_paris()

    # Conversion du format de la date limite from iso to datetime
    date_limite = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))

    time_limite = now_paris_dt - date_limite

    soup = BeautifulSoup(html_code, 'html.parser')

    # Approximation de la date de creation
    ###########################################################
    try:
        chaine = soup.find(attrs={"class": "job-view-layout jobs-details"}).find(attrs={"class": "t-black--light mt2"}).find_all("span")[4].text

        # Définition des pattern à chercher
        pattern = r'(\d+)\s*(minute|heure|jour)'

        # Recherche de la correspondance
        match = re.search(pattern, chaine)

        if match:
            value = int(match.group(1))  # Récupere le nombre
            unit = match.group(2)  # Récupere l'unite (heures ou jours)
            
            # Calcul du timedelta en fonction de l'unite
            if unit in ['heure']:
                delta = timedelta(hours=value)
            elif unit in ['jour']:
                delta = timedelta(days=value)
            elif unit in ['minute']:
                delta = timedelta(minutes=value)

            # Soustrait le delta de la date actuelle
            result_datetime = now_paris_dt - delta
            
            date_crea = str(result_datetime)
            
            date_crea_dt = datetime.strptime(date_crea, '%Y-%m-%d %H:%M:%S.%f%z').replace(second=0, microsecond=0).replace(tzinfo=pytz.timezone('Europe/Paris'))

        else:
            date_crea_dt = now_paris_dt

    except:
        # On a pas trouve de date
        date_crea_dt = now_paris_dt
    ###########################################################

    # Calculer l'écart entre les deux dates
    time_difference = now_paris_dt - date_crea_dt
    
    if time_difference <= time_limite:
        top_ajout = maj_likd_to_notion(soup, date_crea_dt, now_paris_iso, poste, cle_existantes, top_ajout)
    
    return top_ajout


##################################################################################################
def maj_likd_to_notion(soup, date_crea_dt, now_paris_iso, poste, cle_existantes, top_ajout):
    data = {}
    try:
        ###########################################
        data['entreprise'] = soup.find(attrs={"class": "job-view-layout jobs-details"}).find_all(attrs={"class": "app-aware-link"})[1].text

        ###########################################
        data['logo_url'] = soup.find(attrs={"class": "job-view-layout jobs-details"}).find(attrs={"class": "app-aware-link"}).find("img")['src']
        
        ###########################################
        data['intitule_poste'] = soup.find(attrs={"class": "job-view-layout jobs-details"}).find("h1").find("a").text
        
        ###########################################
        data['url_offre'] = "https://www.linkedin.com/jobs/view/" + soup.find(attrs={"class": "job-view-layout jobs-details"}).find("h1").find("a")["href"].split("?")[0].split("/")[3]
        
        ###########################################
        data['date_crea_iso'] = date_crea_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
        
        ###########################################
        data['hebergeur'] = "LinkedIn"
        
        ###########################################
        data['now'] = now_paris_iso
        
        ###########################################
        data['poste'] = poste
        
        ###########################################
        # Scrap de la page de l'offre
        data['page_entreprise'], data['contenu'] = scrap_page_offre_likd(soup)

        cle = str(data['url_offre'][-10:])

        if cle not in cle_existantes:
            # Ajout a Notion via api
            ajout_candidature_to_notion(data)
            top_ajout = True
            
    except Exception as e:
        print(f"Erreur récup data : {e}")
        
    return top_ajout


##################################################################################################
def scrap_page_offre_likd(soup):    
    # Recherche du lien de la page de l'entreprise
    try:
        page_entreprise = soup.find(attrs={"class": "job-view-layout jobs-details"}).find(attrs={"class": "app-aware-link"})["href"].split('?')[0]
    except:
        page_entreprise = "Not Found"

    # Extraire le contenu de l'offre => Pour l'instant cette partie n'est pas traitée
    try:
#         contenu = soup.find(attrs={"class": "job-view-layout jobs-details"}).find(attrs={"id" : "job-details"}).text
        contenu = "Not Found"
    except:
        contenu = "Not Found"
    
    return page_entreprise, contenu