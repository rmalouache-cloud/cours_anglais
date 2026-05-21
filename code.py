import streamlit as st
import json
import os
from pathlib import Path

# Configuration de la page
st.set_page_config(page_title="Plateforme Cours Anglais", layout="wide")

# Initialisation des dossiers
def init_folders():
    niveaux = ["A", "B", "C"]
    sous_niveaux = ["1", "2", "3"]
    for niveau in niveaux:
        for sous in sous_niveaux:
            Path(f"cours/Niveau_{niveau}/{niveau}{sous}").mkdir(parents=True, exist_ok=True)

# Chargement des métadonnées
def load_metadata():
    if os.path.exists("data/cours_metadata.json"):
        with open("data/cours_metadata.json", "r") as f:
            return json.load(f)
    return {}

# Sauvegarde des métadonnées
def save_metadata(metadata):
    Path("data").mkdir(exist_ok=True)
    with open("data/cours_metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)

# Interface principale
def main():
    st.title("📚 Plateforme de Cours d'Anglais")
    
    # Mode : Enseignant ou Étudiant
    mode = st.sidebar.radio("Mode", ["👩‍🏫 Professeur", "👨‍🎓 Étudiant"])
    
    metadata = load_metadata()
    
    if mode == "👩‍🏫 Professeur":
        st.header("📤 Upload de cours (format PPT/PPTX)")
        
        # Sélection du niveau
        col1, col2 = st.columns(2)
        with col1:
            niveau = st.selectbox("Niveau principal", ["A", "B", "C"])
        with col2:
            sous_niveau = st.selectbox("Sous-niveau", ["1", "2", "3"])
        
        niveau_complet = f"Niveau_{niveau}/{niveau}{sous_niveau}"
        
        # Informations du cours
        titre = st.text_input("Titre du cours")
        description = st.text_area("Description (optionnelle)")
        
        # Upload du fichier
        uploaded_file = st.file_uploader("Choisir le fichier PPT/PPTX", 
                                         type=["ppt", "pptx"])
        
        if st.button("💾 Sauvegarder le cours") and titre and uploaded_file:
            # Chemin de sauvegarde
            save_path = Path(f"cours/{niveau_complet}/{uploaded_file.name}")
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarde du fichier
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Sauvegarde des métadonnées
            key = f"{niveau}{sous_niveau}_{uploaded_file.name}"
            metadata[key] = {
                "titre": titre,
                "description": description,
                "niveau": f"{niveau}{sous_niveau}",
                "chemin": str(save_path),
                "fichier": uploaded_file.name
            }
            save_metadata(metadata)
            
            st.success(f"✅ Cours '{titre}' sauvegardé avec succès!")
    
    else:  # Mode étudiant
        st.header("📖 Consultation des cours")
        
        # Sélection du niveau
        col1, col2 = st.columns(2)
        with col1:
            niveau = st.selectbox("Niveau principal", ["A", "B", "C"])
        with col2:
            sous_niveau = st.selectbox("Sous-niveau", ["1", "2", "3"])
        
        niveau_complet = f"{niveau}{sous_niveau}"
        
        # Filtrage des cours
        cours_filtres = {k: v for k, v in metadata.items() 
                        if v["niveau"] == niveau_complet}
        
        if cours_filtres:
            for key, cours in cours_filtres.items():
                with st.expander(f"📘 {cours['titre']}"):
                    st.write(f"**Description:** {cours['description']}")
                    
                    # Option de téléchargement/visualisation
                    with open(cours["chemin"], "rb") as f:
                        st.download_button(
                            label="📥 Télécharger le cours",
                            data=f,
                            file_name=cours["fichier"],
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                        )
        else:
            st.info("Aucun cours disponible pour ce niveau.")

if __name__ == "__main__":
    init_folders()
    main()
