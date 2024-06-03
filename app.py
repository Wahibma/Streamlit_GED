import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import plotly.express as px
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
            Exploration des GED KAIRNIAL : Cartographie interactive des données
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
    return pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';', dtype=spec_types, low_memory=False)

# Fonction pour mettre à jour le diagramme Sankey
def mise_a_jour_sankey(chemin_fichier_selectionne):
    donnees = charger_donnees(chemin_fichier_selectionne)
    total_par_indice = donnees['INDICE'].value_counts(normalize=True) * 100
    total_par_indice = total_par_indice.reset_index()
    total_par_indice.columns = ['INDICE', 'Percentage']

    etiquettes_indices_avec_pourcentage = total_par_indice.apply(lambda row: f"{row['INDICE']} ({row['Percentage']:.2f}%)", axis=1)
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
    fig.add_annotation(x=0.35, y=1.1, text="Émet", showarrow=False, font=dict(size=12, color="blue"))
    fig.add_annotation(x=0.6, y=1.1, text="Type de Document", showarrow=False, font=dict(size=12, color="blue"))
    fig.add_annotation(x=0.9, y=1.1, text="Indice", showarrow=False, font=dict(size=12, color="blue"))

    fig.update_layout(title_text="Flux de Documents par Projet avec Pourcentages d'Indice", font_size=10, margin=dict(l=0, r=0, t=40, b=0))
    return fig

# Menu latéral pour les onglets
with st.sidebar:
    selectionne = option_menu(
        menu_title="Menu",
        options=["Évolution des Types de Documents", "Flux des Documents", "Visualisation des Documents par Lot et Indice", "Repérer les acteurs majeurs de la GED", "Comparaison de la productivité entre chantiers"],
        icons=["line-chart", "exchange", "bar-chart", "users", "chart-bar"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

# Synchroniser les filtres entre les onglets
if 'projet_selectionne' not in st.session_state:
    st.session_state['projet_selectionne'] = list(projets.keys())[0]

projet_selectionne = st.selectbox('Sélectionnez un projet', list(projets.keys()), key='projet_global', index=list(projets.keys()).index(st.session_state['projet_selectionne']))
st.session_state['projet_selectionne'] = projet_selectionne

# Onglet 1: Évolution des Types de Documents
if selectionne == "Évolution des Types de Documents":
    st.header("Évolution des Types de Documents")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y')
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
        height=500  # Ajuster la hauteur du graphique
    )
    st.plotly_chart(fig, use_container_width=True)  # Ajuster la largeur du graphique

# Onglet 2: Flux des Documents
elif selectionne == "Flux des Documents":
    st.header("Flux des Documents")
    fig = mise_a_jour_sankey(projets[projet_selectionne])
    fig.update_layout(height=600)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig, use_container_width=True)

# Onglet 3: Visualisation des Documents par Lot et Indice
elif selectionne == "Visualisation des Documents par Lot et Indice":
    st.header("Visualisation des Documents par Lot et Indice")
    donnees = charger_donnees(projets[projet_selectionne])
    options_indice = donnees['INDICE'].unique()
    indices_selectionnes = st.multiselect('Sélectionnez un ou plusieurs INDICE(S)', options_indice, key='tab3_indices')

    if indices_selectionnes:
        donnees = donnees[donnees['INDICE'].isin(indices_selectionnes)]

    # Répartition des Document par Lot et Indice (Treemap)
    donnees_groupees_treemap = donnees.groupby(['LOT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_treemap = px.treemap(
        donnees_groupees_treemap,
        path=['LOT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Lot et Indice'
    )
    fig_treemap.update_layout(height=500)  # Ajuster la hauteur du graphique

    # Répartition des Documents par Type de Documents et Indice
    donnees_groupees_type_indice = donnees.groupby(['TYPE DE DOCUMENT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_type_indice = px.treemap(
        donnees_groupees_type_indice,
        path=['TYPE DE DOCUMENT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Type de Documents et Indice'
    )
    fig_type_indice.update_layout(height=500)  # Ajuster la hauteur du graphique

    # Nombre des Documents par lot
    documents_par_lot = donnees.groupby('LOT').size().reset_index(name='Nombre de Documents')
    fig_bar_lot = px.bar(
        documents_par_lot,
        y='LOT',
        x='Nombre de Documents',
        orientation='h',
        title="Nombre de Documents par LOT",
        labels={"LOT": "LOT", "Nombre de Documents": "Nombre de Documents"},
        color='Nombre de Documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_bar_lot.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)  # Ajuster la hauteur du graphique

    # Nombre des Documents par Type de Documents
    documents_par_type = donnees.groupby('TYPE DE DOCUMENT').size().reset_index(name='Nombre de Documents')
    fig_bar_type = px.bar(
        documents_par_type,
        y='TYPE DE DOCUMENT',
        x='Nombre de Documents',
        orientation='h',
        title="Nombre de Documents par Type de Documents",
        labels={"TYPE DE DOCUMENT": "Type de Documents", "Nombre de Documents": "Nombre de Documents"},
        color='Nombre de Documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_bar_type.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500)  # Ajuster la hauteur du graphique

    st.plotly_chart(fig_treemap, use_container_width=True)
    st.plotly_chart(fig_type_indice, use_container_width=True)
    st.plotly_chart(fig_bar_lot, use_container_width=True)
    st.plotly_chart(fig_bar_type, use_container_width=True)

# Onglet 4: Repérer les acteurs majeurs de la GED
elif selectionne == "Repérer les acteurs majeurs de la GED":
    st.header("Repérer les acteurs majeurs de la GED")
    donnees = charger_donnees(projets[projet_selectionne])
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y')
    donnees['Année'] = donnees['Date dépôt GED'].dt.year

    # Répartition des Types de documents par Acteur (Ajouté par)
    fig_ajoute_par = px.treemap(donnees, path=['Ajouté par', 'TYPE DE DOCUMENT'],
                                title='Répartition des Types de Documents par Acteur (Ajouté par)')
    fig_ajoute_par.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=700)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig_ajoute_par, use_container_width=True)

    # Répartition des Types de Documents par Emetteur
    fig_emetteur = px.treemap(donnees, path=['EMET', 'TYPE DE DOCUMENT'],
                              title='Répartition des Types de Document par Émetteur')
    fig_emetteur.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=700)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig_emetteur, use_container_width=True)

# Onglet 5: Comparaison de la productivité entre chantiers
elif selectionne == "Comparaison de la productivité entre chantiers":
    st.header("Comparaison de la productivité entre chantiers")
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

        # Calcul de la moyenne de masse de documents par période
        moyenne_masse = df_barre['Masse de documents'].mean()
        df_barre['Moyenne'] = moyenne_masse

        # Création du graphique à barres
        fig_barre = go.Figure()
        fig_barre.add_trace(go.Bar(
            x=df_barre['Chantier'], y=df_barre['Masse de documents'],
            text=df_barre['Masse de documents'], textposition='auto',
            name='Masse de documents',
            marker_color='indianred'
        ))

        fig_barre.add_trace(go.Scatter(
            x=df_barre['Chantier'], y=df_barre['Moyenne'],
            mode='lines', name='Moyenne',
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
            title='Comparaison de la masse de documents selon la période',
            xaxis_title='Chantier', yaxis_title='Masse de documents',
            font=dict(size=15), width=750,
            yaxis=dict(title='Masse de documents', showgrid=True, zeroline=True, showline=True, showticklabels=True),
            xaxis=dict(title='Chantier', showgrid=True, zeroline=True, showline=True, showticklabels=True)
        )
        return fig_barre

    fig1 = mise_a_jour_comparaison_masse_documents(projets_selectionnes, periode_selectionnee)

    st.plotly_chart(fig1, use_container_width=True)
