import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
from datetime import timedelta

# Les noms des projets et le chemin des fichiers.
projets = {
    '40_LAFFITE': '40_LAFFITE.csv',
    'LIGTHWELL': 'LIGTHWELL.csv',
    'MDLF': 'MDLF.csv',
    'GOODLIFE': 'GOODLIFE.csv',
    'AXA_MAT': 'AXA_MAT.csv',
    'LEDGER': 'LEDGER.csv',
    'PECM': 'PECM.csv'
}

# Styles personnalisés pour l'application.
def style_entete():
    st.markdown(f"""
        <style>
        .entete {{
            background-color: #7FDBFF;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            font-size: 24px;
        }}
        .sidebar .css-1d391kg {{
            background-color: #f8f9fa;
        }}
        .sidebar .css-1v3fvcr {{
            background-color: #f8f9fa;
        }}
        .main .block-container {{
            padding-top: 1rem;
        }}
        </style>
        <div class="entete">
            Suivi et Analyse des Documents GED
        </div>
        """, unsafe_allow_html=True)

style_entete()

# Spécification des types de données pour chaque colonne.
spec_types = {
    'Date dépôt GED': str,
    'TYPE DE DOCUMENT': str,
    'PROJET': str,
    'EMET': str,
    'LOT': str,
    'INDICE': str,
}

# Fonction pour charger les données avec gestion des types
def charger_donnees(chemin_fichier):
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';', dtype=spec_types, low_memory=False)
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y', errors='coerce')
    return donnees

# Fonction pour ajouter les colonnes nécessaires au dataframe
def pretraiter_donnees(donnees):
    donnees = donnees.sort_values(by=['TYPE DE DOCUMENT', 'Date dépôt GED'])
    donnees['Différence en jours'] = donnees.groupby('TYPE DE DOCUMENT')['Date dépôt GED'].diff().dt.days
    donnees['Nombre d\'indices'] = donnees.groupby('TYPE DE DOCUMENT')['INDICE'].transform('count')
    return donnees

# Fonction pour afficher les résultats selon le type (moyenne ou maximum) et la représentation (tableau ou boxplot)
def afficher_resultats(donnees, type_calcul, representation, y_column, title_suffix):
    if type_calcul == 'mean':
        calcul = donnees.groupby('TYPE DE DOCUMENT')[y_column].mean().reset_index()
        title = f"Moyenne {title_suffix}"
    elif type_calcul == 'max':
        calcul = donnees.groupby('TYPE DE DOCUMENT')[y_column].max().reset_index()
        title = f"Maximum {title_suffix}"

    if representation == "Tableau":
        st.dataframe(calcul)
    elif representation == "Boxplot":
        fig = px.box(donnees, x='TYPE DE DOCUMENT', y=y_column, title=title)
        st.plotly_chart(fig, use_container_width=True)

# Menu latéral pour les onglets
with st.sidebar:
    selectionne = option_menu(
        menu_title="Menu",
        options=["Flux des documents", "Évolution des types de documents", "Analyse des documents par lot et indice", "Identification des acteurs principaux", "Comparaison de la masse de documents", "Nombre moyen de docs par type de document", "Évaluer la durée moyenne par type de documents"],
        icons=["exchange", "line-chart", "bar-chart", "users", "chart-bar", "file-text", "clock"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

# Synchroniser les filtres entre les onglets
if 'projet_selectionne' not in st.session_state:
    st.session_state['projet_selectionne'] = list(projets.keys())[0]

projet_selectionne = st.selectbox('Sélectionnez un projet', list(projets.keys()), key='projet_global', index=list(projets.keys()).index(st.session_state['projet_selectionne']))
st.session_state['projet_selectionne'] = projet_selectionne

# Onglet 1: Flux des documents
if selectionne == "Flux des documents":
    st.header("Flux des documents")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees = pretraiter_donnees(donnees)

    total_par_indice = donnees['INDICE'].value_counts(normalize=True) * 100
    total_par_indice = total_par_indice.reset_index()
    total_par_indice.columns = ['INDICE', 'Pourcentage']

    etiquettes_indices_avec_pourcentage = total_par_indice.apply(lambda row: f"{row['INDICE']} ({row['Pourcentage']:.2f}%)", axis=1)
    map_pourcentage_indice = dict(zip(total_par_indice['INDICE'], etiquettes_indices_avec_pourcentage))
    donnees['INDICE'] = donnees['INDICE'].map(map_pourcentage_indice)

    tous_les_noeuds = pd.concat([donnees['PROJET'], donnees['EMET'], donnees['TYPE DE DOCUMENT'], donnees['INDICE']]).unique()
    tous_les_noeuds = pd.Series(index=tous_les_noeuds, data=range(len(tous_les_noeuds)))

    source = tous_les_noeuds[donnees['PROJET']].tolist() + tous_les_noeuds[donnees['EMET']].tolist() + tous_les_noeuds[donnees['TYPE DE DOCUMENT']].tolist()
    cible = tous_les_noeuds[donnees['EMET']].tolist() + tous_les_noeuds[donnees['TYPE DE DOCUMENT']].tolist() + tous_les_noeuds[donnees['INDICE']].tolist()
    valeur = [1] * len(donnees['PROJET']) + [1] * len(donnees['EMET']) + [1] * len(donnees['TYPE DE DOCUMENT'])

    etiquettes_noeuds = tous_les_noeuds.index.tolist()

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=etiquettes_noeuds
        ),
        link=dict(
            source=source,
            target=cible,
            value=valeur
        )
    )])

    # Ajouter des annotations pour les labels de colonne
    fig.add_annotation(x=0.1, y=1.1, text="Projet", showarrow=False, font=dict(size=12, color="blue"))
    fig.add_annotation(x=0.35, y=1.1, text="Émetteur", showarrow=False, font=dict(size=12, color="blue"))
    fig.add_annotation(x=0.6, y=1.1, text="Type de Document", showarrow=False, font=dict(size=12, color="blue"))
    fig.add_annotation(x=0.9, y=1.1, text="Indice", showarrow=False, font=dict(size=12, color="blue"))

    fig.update_layout(title_text="", font_size=10, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, use_container_width=True)

# Onglet 2: Évolution des types de documents
elif selectionne == "Évolution des types de documents":
    st.header("Évolution des types de documents")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees = pretraiter_donnees(donnees)
    options_type_document = donnees['TYPE DE DOCUMENT'].unique()
    types_selectionnes = st.multiselect('Sélectionnez les types de document', options_type_document, default=options_type_document[0], key='tab1_types')
    
    donnees_groupees = donnees.groupby([donnees['Date dépôt GED'].dt.to_period("M"), 'TYPE DE DOCUMENT']).size().reset_index(name='Nombre de documents')
    donnees_groupees['Date dépôt GED'] = donnees_groupees['Date dépôt GED'].dt.to_timestamp()
    
    fig = go.Figure()
    for t in types_selectionnes:
        donnees_filtrees = donnees_groupees[donnees_groupees['TYPE DE DOCUMENT'] == t]
        fig.add_trace(go.Scatter(x=donnees_filtrees['Date dépôt GED'], y=donnees_filtrees['Nombre de documents'].cumsum(), mode='lines+markers', name=f'Cumulé - {t}'))
        fig.add_trace(go.Scatter(x=donnees_filtrees['Date dépôt GED'], y=donnees_filtrees['Nombre de documents'], mode='lines+markers', name=t, visible='legendonly'))

    fig.update_layout(
        title=f'Évolution du nombre de documents pour {projet_selectionne}',
        xaxis_title='Date de Dépôt',
        yaxis_title='Nombre de Documents',
        legend_title='Type de Documents',
        height=500,  # Ajuster la hauteur du graphique
        width=1200  # Ajuster la largeur du graphique
    )
    st.plotly_chart(fig, use_container_width=True)  # Ajuster la largeur du graphique

# Onglet 3: Analyse des documents par lot et indice
elif selectionne == "Analyse des documents par lot et indice":
    st.header("Analyse des documents par lot et indice")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees = pretraiter_donnees(donnees)
    options_indice = donnees['INDICE'].unique()
    indices_selectionnes = st.multiselect('Sélectionnez un ou plusieurs indices', options_indice, key='tab3_indices')

    if indices_selectionnes:
        donnees = donnees[donnees['INDICE'].isin(indices_selectionnes)]

    # Répartition des documents par lot et indice (Treemap)
    donnees_groupees_treemap = donnees.groupby(['LOT', 'INDICE']).size().reset_index(name='Nombre de documents')
    fig_treemap = px.treemap(
        donnees_groupees_treemap,
        path=['LOT', 'INDICE'],
        values='Nombre de documents',
        title='Répartition des documents par lot et indice'
    )
    fig_treemap.update_layout(height=500, width=1200)  # Ajuster la hauteur et la largeur du graphique

    # Répartition des documents par type de documents et indice
    donnees_groupees_type_indice2 = donnees.groupby(['TYPE DE DOCUMENT', 'INDICE']).size().reset_index(name='Nombre de documents')
    fig_type_indice2 = px.treemap(
        donnees_groupees_type_indice2,
        path=['TYPE DE DOCUMENT', 'INDICE'],
        values='Nombre de documents',
        title='Répartition des documents par type de documents et indice'
    )
    fig_type_indice2.update_layout(height=550, width=1200)  # Ajuster la hauteur et la largeur du graphique

    # Répartition des documents par type de documents, lot et indice (Treemap)
    donnees_groupees_type_indice = donnees.groupby(['LOT', 'TYPE DE DOCUMENT', 'INDICE']).size().reset_index(name='Nombre de documents')
    fig_type_indice = px.treemap(
        donnees_groupees_type_indice,
        path=['LOT', 'TYPE DE DOCUMENT', 'INDICE'],
        values='Nombre de documents',
        title='Répartition des documents par type de documents, lot et indice'
    )
    fig_type_indice.update_layout(height=800, width=1200)  # Ajuster la hauteur et la largeur du graphique

    # Nombre de documents par lot
    documents_par_lot = donnees.groupby('LOT').size().reset_index(name='Nombre de documents')
    fig_bar_lot = px.bar(
        documents_par_lot,
        y='LOT',
        x='Nombre de documents',
        orientation='h',
        title="Nombre de documents par lot",
        labels={"LOT": "Lot", "Nombre de documents": "Nombre de documents"},
        color='Nombre de documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_bar_lot.update_layout(yaxis={'categoryorder': 'total ascending'}, height=850, width=1000)  # Ajuster la hauteur et la largeur du graphique

    # Nombre de documents par type de documents
    documents_par_type = donnees.groupby('TYPE DE DOCUMENT').size().reset_index(name='Nombre de documents')
    fig_bar_type = px.bar(
        documents_par_type,
        y='TYPE DE DOCUMENT',
        x='Nombre de documents',
        orientation='h',
        title="Nombre de documents par type de documents",
        labels={"TYPE DE DOCUMENT": "Type de documents", "Nombre de documents": "Nombre de documents"},
        color='Nombre de documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_bar_type.update_layout(yaxis={'categoryorder': 'total ascending'}, height=850, width=1200)  # Ajuster la hauteur et la largeur du graphique

    st.plotly_chart(fig_treemap, use_container_width=True)
    st.plotly_chart(fig_type_indice2, use_container_width=True)
    st.plotly_chart(fig_type_indice, use_container_width=True)
    st.plotly_chart(fig_bar_lot, use_container_width=True)
    st.plotly_chart(fig_bar_type, use_container_width=True)

# Onglet 4: Identification des acteurs principaux
elif selectionne == "Identification des acteurs principaux":
    st.header("Identification des acteurs principaux")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y')
    donnees['Année'] = donnees['Date dépôt GED'].dt.year

    # Répartition des types de documents par émetteur
    fig_emetteur = px.treemap(donnees, path=['EMET', 'TYPE DE DOCUMENT'],
                              title='Répartition des types de documents par émetteur')
    fig_emetteur.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=480, width=1200)  # Ajuster la hauteur et la largeur du graphique
    st.plotly_chart(fig_emetteur, use_container_width=True)

    # Répartition des types de documents par acteur (Ajouté par)
    fig_ajoute_par = px.treemap(donnees, path=['Ajouté par', 'TYPE DE DOCUMENT'],
                                title='Répartition des types de documents par acteur (Ajouté par)')
    fig_ajoute_par.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=480, width=1200)  # Ajuster la hauteur et la largeur du graphique
    st.plotly_chart(fig_ajoute_par, use_container_width=True)

# Onglet 5: Comparaison de la masse de documents entre projets
elif selectionne == "Comparaison de la masse de documents":
    st.header("Comparaison de la masse de documents")
    periode_selectionnee = st.radio(
        'Sélectionnez la période',
        options=['6m', '12m', 'all'],
        format_func=lambda x: '6 premiers mois' if x == '6m' else '12 premiers mois' if x == '12m' else 'Toute la période',
        horizontal=True
    )
    projets_selectionnes = st.multiselect('Sélectionnez les projets', list(projets.keys()), default=list(projets.keys()))

    def mise_a_jour_comparaison_masse_documents(projets_selectionnes, periode_selectionnee):
        donnees_barre = []
        for projet in projets_selectionnes:
            df = pd.read_csv(projets[projet], encoding='iso-8859-1', sep=';', dtype=str)
            df['Date dépôt GED'] = pd.to_datetime(df['Date dépôt GED'], format='%d/%m/%Y')
            date_debut = df['Date dépôt GED'].min()
            if periode_selectionnee == '6m':
                date_fin = date_debut + timedelta(days=180)  # 6 mois
            elif periode_selectionnee == '12m':
                date_fin = date_debut + timedelta(days=365)  # 12 mois
            else:
                date_fin = df['Date dépôt GED'].max()  # Toute la période

            df_filtre = df[(df['Date dépôt GED'] >= date_debut) & (df['Date dépôt GED'] <= date_fin)]
            total_documents = df_filtre.shape[0]
            donnees_barre.append({
                'Chantier': projet,
                'Masse de documents': total_documents,
                'Date début': date_debut.strftime('%Y-%m-%d'),
                'Date fin': date_fin.strftime('%Y-%m-%d')
            })

        # Tri des données par masse de documents
        df_barre = pd.DataFrame(donnees_barre)
        df_barre = df_barre.sort_values(by='Masse de documents', ascending=False)

        # Calcul de la médiane de masse de documents par période
        mediane_masse = df_barre['Masse de documents'].median()
        df_barre['mediane'] = mediane_masse

        # Création du graphique à barres pour voir la masse de chaque document
        fig_barre = go.Figure()
        fig_barre.add_trace(go.Bar(
            x=df_barre['Chantier'], y=df_barre['Masse de documents'],
            text=df_barre['Masse de documents'], textposition='auto',
            name='Masse de documents',
            marker_color='indianred'
        ))

        fig_barre.add_trace(go.Scatter(
            x=df_barre['Chantier'], y=df_barre['mediane'],
            mode='lines', name='Médiane',
            line=dict(color='blue', dash='dash')
        ))

        # Ajouter des annotations pour les valeurs importantes
        for index, row in df_barre.iterrows():
            fig_barre.add_annotation(
                x=row['Chantier'], y=row['Masse de documents'],
                text=f"{row['Masse de documents']}",
                showarrow=True, arrowhead=2
            )

        fig_barre.update_layout(
            title='Comparaison de la masse de documents entre les chantiers',
            xaxis_title='Chantier', yaxis_title='Masse de documents',
            font=dict(size=15),
            height=450,  # Ajuster la hauteur du graphique
            width=1200,  # Ajuster la largeur du graphique
            yaxis=dict(title='Masse de documents', showgrid=True, zeroline=True, showline=True, showticklabels=True),
            xaxis=dict(title='Chantier', showgrid=True, zeroline=True, showline=True, showticklabels=True)
        )
        return fig_barre

    fig1 = mise_a_jour_comparaison_masse_documents(projets_selectionnes, periode_selectionnee)
    st.plotly_chart(fig1, use_container_width=True)

# Onglet 6: Nombre moyen de docs par type de document
elif selectionne == "Nombre moyen de docs par type de document":
    st.header("Nombre moyen de documents par type de document")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees = pretraiter_donnees(donnees)

    # Choix du type de calcul
    type_calcul = st.selectbox('Sélectionnez le type de calcul', ['mean', 'max'], key='calcul_type')
    representation = st.selectbox('Sélectionnez le type de représentation', ['Tableau', 'Boxplot'], key='rep_type')
    
    # Afficher les résultats selon le type de calcul et la représentation
    afficher_resultats(donnees, type_calcul, representation, 'Nombre d\'indices', "de documents par type de document")

# Onglet 7: Évaluer la durée moyenne par type de documents
elif selectionne == "Évaluer la durée moyenne par type de documents":
    st.header("Évaluer la durée moyenne par type de documents")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees = pretraiter_donnees(donnees)

    # Choix du type de calcul
    type_calcul = st.selectbox('Sélectionnez le type de calcul', ['mean', 'max'], key='calcul_duree_type')
    representation = st.selectbox('Sélectionnez le type de représentation', ['Tableau', 'Boxplot'], key='rep_duree_type')
    
    # Afficher les résultats selon le type de calcul et la représentation
    afficher_resultats(donnees, type_calcul, representation, 'Différence en jours', "de durée entre versions par type de document")


# FIN Programme
