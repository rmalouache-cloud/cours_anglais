import streamlit as st
import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Plateforme Cours d'Anglais",
    page_icon="📚",
    layout="wide"
)

# Création des dossiers nécessaires
BASE_DIR = Path(__file__).parent
PPT_DIR = BASE_DIR / "ppts_uploades"
DATA_FILE = BASE_DIR / "data" / "cours_metadata.json"

# Créer les dossiers s'ils n'existent pas
PPT_DIR.mkdir(exist_ok=True)
(DATA_FILE.parent).mkdir(exist_ok=True)

# Créer la structure des niveaux (chaque niveau a 3 sous-niveaux)
STRUCTURE_NIVEAUX = {
    "A": ["A1", "A2", "A3"],
    "B": ["B1", "B2", "B3"],
    "C": ["C1", "C2", "C3"]
}

for niveau in STRUCTURE_NIVEAUX.keys():
    for sous_niveau in STRUCTURE_NIVEAUX[niveau]:
        (PPT_DIR / niveau / sous_niveau).mkdir(parents=True, exist_ok=True)

# Fonction pour charger les métadonnées des cours
def load_metadata():
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

# Fonction pour sauvegarder les métadonnées
def save_metadata(metadata):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

# Initialisation
if 'cours_metadata' not in st.session_state:
    st.session_state.cours_metadata = load_metadata()

# Titre
st.title("📚 Plateforme de Cours d'Anglais")
st.markdown("---")

# Sidebar pour la navigation
with st.sidebar:
    st.header("🎯 Navigation par niveau")
    
    # Sélection du niveau principal (A, B ou C)
    niveau_principal = st.radio(
        "Choisissez le niveau",
        ["A (Débutant)", "B (Intermédiaire)", "C (Avancé)"],
        index=0,
        horizontal=True
    )
    
    # Extraire la lettre (A, B ou C)
    lettre = niveau_principal[0]
    
    # Sélection du sous-niveau (toujours 3 choix)
    sous_niveaux = STRUCTURE_NIVEAUX[lettre]
    sous_niveau = st.selectbox(
        f"Sous-niveau {lettre}",
        sous_niveaux,
        format_func=lambda x: f"{x} - {get_niveau_description(lettre, x)}"
    )
    
    # Afficher un petit indicateur de progression
    st.markdown("---")
    niveau_index = sous_niveaux.index(sous_niveau) + 1
    st.progress(niveau_index / len(sous_niveaux))
    st.caption(f"Progression dans le niveau {lettre} : {niveau_index}/3")
    
    st.markdown("---")
    st.info("👩‍🏫 **Mode Enseignant** : Uploader des cours PPT\n\n📖 **Mode Cours** : Visualiser et partager")

# Fonction pour la description des niveaux
def get_niveau_description(lettre, sous_niveau):
    descriptions = {
        "A": {"A1": "🔰 Débutant complet", "A2": "📖 Débutant avancé", "A3": "🗣️ Pré-intermédiaire"},
        "B": {"B1": "💬 Intermédiaire seuil", "B2": "📝 Intermédiaire supérieur", "B3": "🎯 Intermédiaire avancé"},
        "C": {"C1": "⚡ Autonome", "C2": "🎓 Avancé", "C3": "🏆 Maîtrise"}
    }
    return descriptions.get(lettre, {}).get(sous_niveau, "")

# Zone principale divisée en 2 colonnes
col1, col2 = st.columns([1, 2])

# COLONNE 1 : Gestion des cours (upload + liste)
with col1:
    st.subheader(f"📤 {sous_niveau} - Gestion des cours")
    st.caption(get_niveau_description(lettre, sous_niveau))
    
    # Formulaire d'upload
    with st.expander("➕ Ajouter un nouveau cours", expanded=True):
        titre_cours = st.text_input("Titre du cours", placeholder="Ex: Leçon 1 - Présent simple")
        
        # Upload du fichier PPT
        fichier_ppt = st.file_uploader(
            "Choisir un fichier PowerPoint (.ppt ou .pptx)",
            type=['ppt', 'pptx'],
            help="Uploader votre présentation PowerPoint - elle sera sauvegardée automatiquement"
        )
        
        # Description optionnelle
        description = st.text_area("Description du cours", placeholder="Décrivez brièvement le contenu du cours...", height=100)
        
        # Tags
        tags = st.text_input("Tags (séparés par des virgules)", placeholder="grammaire, vocabulaire, exercices, dialogue")
        
        # Durée estimée
        duree = st.number_input("Durée estimée (minutes)", min_value=5, max_value=180, value=30, step=5)
        
        if st.button("💾 Sauvegarder le cours", type="primary", use_container_width=True):
            if titre_cours and fichier_ppt:
                # Créer le chemin de sauvegarde
                dossier_cible = PPT_DIR / lettre / sous_niveau
                
                # Générer un nom de fichier unique
                extension = fichier_ppt.name.split('.')[-1]
                nom_fichier = f"{titre_cours.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
                chemin_ppt = dossier_cible / nom_fichier
                
                # Sauvegarder le fichier
                with open(chemin_ppt, "wb") as f:
                    f.write(fichier_ppt.getbuffer())
                
                # Créer les métadonnées
                cours_info = {
                    "id": f"{lettre}_{sous_niveau}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "titre": titre_cours,
                    "fichier": str(chemin_ppt.relative_to(BASE_DIR)),
                    "description": description,
                    "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
                    "duree": duree,
                    "date_ajout": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "presentation",
                    "niveau": f"{lettre}{sous_niveau[1:]}"
                }
                
                # Sauvegarder dans les métadonnées
                key = f"{lettre}/{sous_niveau}"
                if key not in st.session_state.cours_metadata:
                    st.session_state.cours_metadata[key] = []
                
                st.session_state.cours_metadata[key].append(cours_info)
                save_metadata(st.session_state.cours_metadata)
                
                st.success(f"✅ Cours '{titre_cours}' sauvegardé avec succès!")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Veuillez remplir le titre et sélectionner un fichier PPT")
    
    # Liste des cours existants
    st.subheader("📋 Cours disponibles")
    
    key = f"{lettre}/{sous_niveau}"
    cours_liste = st.session_state.cours_metadata.get(key, [])
    
    if cours_liste:
        st.caption(f"📊 {len(cours_liste)} cours disponible(s)")
        
        for i, cours in enumerate(cours_liste):
            with st.container():
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**📌 {cours['titre']}**")
                    st.caption(f"⏱️ {cours['duree']} min | 📅 {cours['date_ajout'].split()[0]}")
                    if cours.get('tags'):
                        st.caption(f"🏷️ {', '.join(cours['tags'][:3])}")
                with col_b:
                    if st.button("🗑️", key=f"del_{lettre}_{sous_niveau}_{i}", help="Supprimer ce cours"):
                        # Supprimer le fichier physique
                        chemin_fichier = BASE_DIR / cours['fichier']
                        if chemin_fichier.exists():
                            chemin_fichier.unlink()
                        
                        # Supprimer des métadonnées
                        st.session_state.cours_metadata[key].pop(i)
                        save_metadata(st.session_state.cours_metadata)
                        st.rerun()
                st.divider()
    else:
        st.info("📭 Aucun cours pour ce niveau")
        st.caption("👆 Cliquez sur 'Ajouter un nouveau cours' pour commencer")

# COLONNE 2 : Affichage des cours (partage d'écran)
with col2:
    st.subheader(f"📖 {sous_niveau} - Affichage des cours")
    st.caption("Mode partage d'écran - Activez le mode présentation ci-dessous")
    
    # Mode présentation
    mode_presentation = st.toggle("🎬 Mode présentation (optimisé pour partage d'écran)", value=False)
    
    if cours_liste:
        # Sélection du cours avec recherche
        titres_cours = [c["titre"] for c in cours_liste]
        
        # Ajouter une recherche si beaucoup de cours
        if len(cours_liste) > 5:
            recherche = st.text_input("🔍 Rechercher un cours", placeholder="Titre ou tag...")
            if recherche:
                titres_cours = [c["titre"] for c in cours_liste 
                              if recherche.lower() in c["titre"].lower() 
                              or any(recherche.lower() in tag.lower() for tag in c.get("tags", []))]
        
        cours_selectionne_titre = st.selectbox("Choisir un cours à afficher", titres_cours)
        
        # Récupérer le cours sélectionné
        cours_actuel = next((c for c in cours_liste if c["titre"] == cours_selectionne_titre), None)
        
        if cours_actuel:
            if mode_presentation:
                # Style pour le mode présentation
                st.markdown("""
                <style>
                .presentation-container {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 15px;
                    color: white;
                }
                .presentation-content {
                    background-color: white;
                    padding: 2rem;
                    border-radius: 10px;
                    color: #333;
                    margin-top: 1rem;
                }
                .cours-titre {
                    color: white;
                    text-align: center;
                    font-size: 2rem;
                    margin-bottom: 0.5rem;
                }
                .info-cours {
                    text-align: center;
                    color: rgba(255,255,255,0.9);
                    margin-bottom: 1rem;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="presentation-container">
                    <h1 class="cours-titre">{cours_actuel['titre']}</h1>
                    <div class="info-cours">
                        {sous_niveau} • {cours_actuel['duree']} min • Ajouté le {cours_actuel['date_ajout'].split()[0]}
                    </div>
                """, unsafe_allow_html=True)
                
                if cours_actuel.get('description'):
                    st.markdown(f"""
                    <div style="background-color: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                        📝 {cours_actuel['description']}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('<div class="presentation-content">', unsafe_allow_html=True)
                
                # Afficher le PPT
                chemin_ppt = BASE_DIR / cours_actuel['fichier']
                if chemin_ppt.exists():
                    try:
                        from pptx import Presentation
                        
                        prs = Presentation(str(chemin_ppt))
                        st.info(f"📊 {len(prs.slides)} diapositives disponibles")
                        
                        # Navigation simple
                        if 'slide_index' not in st.session_state:
                            st.session_state.slide_index = 0
                        
                        # Boutons de navigation
                        col_prev, col_page, col_next = st.columns([1, 2, 1])
                        with col_prev:
                            if st.button("◀ Précédent", use_container_width=True) and st.session_state.slide_index > 0:
                                st.session_state.slide_index -= 1
                                st.rerun()
                        with col_page:
                            st.markdown(f"<p style='text-align: center;'><b>Diapositive {st.session_state.slide_index + 1}/{len(prs.slides)}</b></p>", unsafe_allow_html=True)
                        with col_next:
                            if st.button("Suivant ▶", use_container_width=True) and st.session_state.slide_index < len(prs.slides) - 1:
                                st.session_state.slide_index += 1
                                st.rerun()
                        
                        st.markdown("---")
                        
                        # Afficher la diapositive courante
                        slide = prs.slides[st.session_state.slide_index]
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                # Détecter les titres (texte plus grand ou en gras)
                                if hasattr(shape, "text_frame") and shape.text_frame.paragraphs:
                                    if shape.text_frame.paragraphs[0].font.size and shape.text_frame.paragraphs[0].font.size.pt > 20:
                                        st.markdown(f"## {shape.text}")
                                    else:
                                        st.markdown(f"• {shape.text}")
                                else:
                                    st.markdown(f"• {shape.text}")
                        
                        # Option de téléchargement
                        with open(chemin_ppt, "rb") as f:
                            st.download_button(
                                label="📥 Télécharger la présentation complète",
                                data=f,
                                file_name=chemin_ppt.name,
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                use_container_width=True
                            )
                    
                    except Exception as e:
                        st.error(f"Erreur de lecture: {str(e)}")
                        with open(chemin_ppt, "rb") as f:
                            st.download_button(
                                label="📥 Télécharger le fichier PPT",
                                data=f,
                                file_name=chemin_ppt.name,
                                use_container_width=True
                            )
                else:
                    st.error("Fichier introuvable")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.info("💡 **Astuces pour le partage d'écran :**")
                st.caption("• Appuyez sur **F11** pour le plein écran du navigateur")
                st.caption("• Utilisez les boutons ◀ ▶ pour naviguer entre les diapositives")
                st.caption("• Cachez cette barre latérale en cliquant sur la flèche en haut à gauche")
                
            else:
                # Mode normal (affichage info)
                st.markdown(f"### 📄 {cours_actuel['titre']}")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Niveau", sous_niveau)
                with col_info2:
                    st.metric("Durée", f"{cours_actuel['duree']} min")
                with col_info3:
                    st.metric("Ajouté le", cours_actuel['date_ajout'].split()[0])
                
                if cours_actuel.get('description'):
                    st.markdown("**Description :**")
                    st.info(cours_actuel['description'])
                
                if cours_actuel.get('tags'):
                    st.markdown("**Tags :**")
                    st.markdown(", ".join([f"`{tag}`" for tag in cours_actuel['tags']]))
                
                st.markdown("---")
                
                # Lien pour télécharger le PPT
                chemin_ppt = BASE_DIR / cours_actuel['fichier']
                if chemin_ppt.exists():
                    with open(chemin_ppt, "rb") as f:
                        st.download_button(
                            label="📥 Télécharger la présentation",
                            data=f,
                            file_name=chemin_ppt.name,
                            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                            use_container_width=True
                        )
                    
                    st.success("💡 **Pour partager votre écran :**")
                    st.caption("1. Téléchargez le fichier PPT")
                    st.caption("2. Ouvrez-le avec PowerPoint")
                    st.caption("3. Lancez le diaporama (F5)")
                    st.caption("4. Partagez votre écran dans votre outil de visio")
                else:
                    st.error("Fichier non trouvé")
    else:
        st.info("👆 **Aucun cours disponible**")
        st.caption("Ajoutez votre premier cours en uploadant un fichier PPT dans la colonne de gauche")

# Footer
st.markdown("---")
st.caption(f"✨ Plateforme de cours d'anglais - Niveaux A1→A3, B1→B3, C1→C3 | Cours sauvegardés définitivement")