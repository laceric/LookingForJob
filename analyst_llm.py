# Recupere les différents modules
from analyst_llm_utils import *  # Fonctions globales
###############################################################################################################################################################################

pages_id, contenus = recup_offre_a_analyser_from_notion()
print(f"Nombre de pages à traiter: {len(pages_id)}")


groq = Groq(api_key=GROQ_API_KEY)

i = 0
for page_id, contenu in zip(pages_id, contenus):
    i+=1
    print(f"Page ({i}): {page_id}")
    # Synthese via llm
    try:
        synthese_json = get_synthese(groq, contenu)
        print(f"syntheses_json recupere !")
        synthese_format = formatage_synthese(synthese_json)
        print(f"syntheses_format recupere !")
    except Exception as e:
        log(e)
    
    # Analyse cv via llm
    try:
        analyse = get_analyse_cv(groq, contenu)
        print(f"analyses recupere !")
    except Exception as e:
        log(e)

    # Stockage dans la base de données notion
    try:
        maj_table_candidature_synthese_analyse(page_id, synthese_json, synthese_format, analyse)
        print("Maj table faite")
    except Exception as e:
        log(e)
    
    del(synthese_json)
    del(synthese_format)
    del(analyse)

print("Fin boucle")