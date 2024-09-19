# Bibliothèques utilisées
import time
import pytz
from datetime import datetime, timedelta
import re

from bs4 import BeautifulSoup

# Récupère les différents modules
from scraper_offre_utils import *  # Fonctions globales
###############################################################################################################################################################################
##################################################################################################
def scraper_indd(params):
    # Accès au tableau Gestion des candidatures pour stocker les clés des offres deja récupérer
    cles_existantes = recup_cle_existantes_from_notion('Indeed')

    # Initialisation du navigateur
    driver = lancement_session_selenium()

    # Pour vérifier qu'on est bien connecté
    URL_SITE = "https://fr.indeed.com/"
    driver.get(URL_SITE)
    time.sleep(3)

    # Contrôle si le compte est bien connecté 
    try:
        driver.find_element(By.ID, "AccountMenu")
    except:
        print("Compte déconecté")
        print("On quitte")
        driver.quit()
        return
    
    # URL de base pour CDI en île-de-France dans le poste recherché
    URL_START = "https://fr.indeed.com/emplois?q=%22"
    URL_END = "%22&l=%C3%8Ele-de-France&sc=0kf%3Ajt%28permanent%29%3B"

    for page_id, poste, date_limite in params:
        url = URL_START + poste.replace(" ", "%20") + URL_END
        
        scrap_page_poste_indd(driver, url, date_limite)
        
        # Définition du top si ajout offre à la base de données
        top_ajout = False

        # Vérifier qu'il y a des offres
        try:
            driver.find_element(By.ID, "mosaic-provider-jobcards").find_element(By.TAG_NAME, 'ul')
            
            page_actuelle = 1

            # Définition d'un top pour dire qu'on a fini de parcourir les offres ou pas
            top_out = False
            while not top_out:
                top_ajout = traitement_liste_offre_indd(driver, top_ajout, cles_existantes, poste, date_limite)
                top_out = lecture_liste_page_indd(driver, page_actuelle)
            
        except:
            next
    
        # Obtenir l'heure actuelle a Paris aux format ISO
        now_paris_iso = heure_now_in_paris(1)

        maj_table_scrap_param_post_batch(now_paris_iso, page_id, top_ajout)
    
    driver.quit()


##################################################################################################
def scrap_page_poste_indd(driver, url, date_limite):
    # Ouvrir un nouvel onglet avec une URL spécifique
    driver.get(url)
    time.sleep(2) 

    # Choix de l'option dateposted
    # calcul nombre de jour d'ecart
    ecart_jours = nb_jour(date_limite)
    
    if ecart_jours < 14:
        # Choix délais inferieur à 14 jours sinon c'est dans le mois (30 jours)
        driver.find_element(By.ID, "filter-dateposted").click()
        time.sleep(1)

        if ecart_jours < 1:
            # last 24h
            driver.find_element(By.ID, "filter-dateposted-menu").find_elements(By.TAG_NAME, 'li')[0].click()
            time.sleep(3)
        
        elif ecart_jours < 3:
            # last 3 jours
            driver.find_element(By.ID, "filter-dateposted-menu").find_elements(By.TAG_NAME, 'li')[1].click()
            time.sleep(3)
        
        elif ecart_jours < 7:
            # last 7 jours
            driver.find_element(By.ID, "filter-dateposted-menu").find_elements(By.TAG_NAME, 'li')[2].click()
            time.sleep(3)
            
        else:
            # last 14 jours
            driver.find_element(By.ID, "filter-dateposted-menu").find_elements(By.TAG_NAME, 'li')[3].click()

##################################################################################################
def traitement_liste_offre_indd(driver, top_ajout, cles_existantes, poste, date_limite):
    # Trouver tous les éléments <li> a l'interieur du <ul>
    liste_offres = driver.find_elements(By.CLASS_NAME, "job_seen_beacon")

    for offre in liste_offres:
        # Afficher l'id
        id_value = None
        try :
            id_value = offre.find_elements(By.TAG_NAME, "a")[0].get_attribute('id').split('_')[1]
            
            chaine = None
            try:
                for i, elem in enumerate(offre.find_elements(By.TAG_NAME, "span")):
                    if elem.text[:7] == 'Posted\n':
                        chaine = elem.text[7:]

            except Exception as e:
                print(f"Erreur chaine : {e}")
                
            # click sur l'offre
            offre.click()
            time.sleep(1)
        
            # Recuperer l'ensemble du code HTML
            html_code = driver.page_source
            time.sleep(1)

            ajout = recup_offres_data_indd(html_code, id_value, chaine, cles_existantes, poste, date_limite)

            if ajout:
                top_ajout = True
                
        except Exception as e:
            print(f"Erreur offre ({id_value}) : {e}")
            continue

    return top_ajout

##################################################################################################
def recup_offres_data_indd(html_code, id_value, chaine, cles_existantes, poste, date_limite):
    # Définition du top si ajout offre à la base de données
    top_ajout = False    
    # Obtenir l'heure actuelle à Paris aux format datetime et iso
    now_paris_dt, now_paris_iso = heure_now_in_paris()

    # Conversion du format de la date limite from iso to datetime
    date_limite = datetime.fromisoformat(date_limite.replace('Z', '+00:00'))

    time_limite = now_paris_dt - date_limite

    soup = BeautifulSoup(html_code, 'html.parser')

    # Approximation de la date de création
    ###########################################################
    try:
        # Définition du pattern qu'on recherche
        pattern = r'(\d+)\s*(jour)'

        # Recherche de la correspondance
        match = re.search(pattern, chaine)

        if match:
            value = int(match.group(1))  # Récupere le nombre

            unit = match.group(2)  # Récupere l'unité (jours)
            
            # Calcul du timedelta en fonction de l'unité
            if unit in ['jour']:
                delta = timedelta(days=value)

            # Soustrait le delta de la date actuelle
            result_datetime = now_paris_dt - delta
            
            date_crea = str(result_datetime)
            
            date_crea_dt = datetime.strptime(date_crea, '%Y-%m-%d %H:%M:%S.%f').replace(second=0, microsecond=0).replace(tzinfo=pytz.timezone('Europe/Paris'))

        else:
            date_crea_dt = now_paris_dt

    except:
        date_crea_dt = now_paris_dt
    ###########################################################

    # Calculer l'écart entre les deux dates
    time_difference = now_paris_dt - date_crea_dt
    
    if time_difference <= time_limite:
        top_ajout = maj_indd_to_notion(soup, id_value, date_crea_dt, now_paris_iso, poste, cles_existantes, top_ajout)

    return top_ajout

##################################################################################################
def maj_indd_to_notion(soup, id_value, date_crea_dt, now_paris_iso, poste, cles_existantes, top_ajout):
    data = {}

    try:
        ###########################################
        data['entreprise'] = soup.find(attrs={"data-testid":"inlineHeader-companyName"}).find('a').text
        
        ###########################################
        data['logo_url'] = None
        
        ###########################################
        data['intitule_poste'] = soup.find(attrs={"data-testid":"jobsearch-JobInfoHeader-title"}).text
        
        ###########################################
        data['url_offre'] = "https://fr.indeed.com/viewjob?jk=" + id_value
        
        ###########################################
        data['date_crea_iso'] = date_crea_dt.strftime('%Y-%m-%dT%H:%M:%S.000+00:00')
        
        ###########################################
        data['hebergeur'] = "Indeed"
        
        ###########################################
        data['now'] = now_paris_iso
        
        ###########################################
        data['poste'] = poste
        
        ###########################################
        data['page_entreprise'] = soup.find(attrs={"data-testid":"inlineHeader-companyName"}).find('a')['href'].split('?')[0]
        
        ###########################################
        # Scrap de la page de l'offre
        data['contenu'] = scrap_page_offre_indd(soup)

        cle = str(data['url_offre'].split('=')[1])
        if cle not in cles_existantes:
            # Ajout a Notion via api
            ajout_candidature_to_notion(data)
            top_ajout = True

    except Exception as e:
        print(f"Erreur récup data : {e}")
        
    return top_ajout

##################################################################################################
def scrap_page_offre_indd(soup):    
    # Extraire le contenu de l'offre  => Pour l'instant cette partie n'est pas traitée
    try:
        contenu = "Not Found"
    except:
        contenu = "Not Found"
    
    return contenu

##################################################################################################
def lecture_liste_page_indd(driver, page_actuelle):
    top_out = False
    try:
        # Localiser le conteneur <ul> contenant les <li> qui se trouve dans un nav
        navs = driver.find_elements(By.TAG_NAME, 'nav')

        for nav in navs:
            if nav.get_attribute('aria-label') == 'pagination':
                # première ligne vérifie l'existance de li qui indique d'autres pages
                nav.find_element(By.TAG_NAME, 'ul').find_element(By.TAG_NAME, 'li')

                # si d'autres pages on regarde le dernier qui est censé être soit next soit le num de la dernière page
                li_elems = nav.find_element(By.TAG_NAME, 'ul').find_elements(By.TAG_NAME, 'li')
                if li_elems[-1].text == '':
                    li_elems[-1].click()

                    page_actuelle += 1

                else:
                    top_out = True
        return top_out
    
    except:
        top_out = True
        return top_out

##################################################################################################