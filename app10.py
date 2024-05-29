import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu
from datetime import timedelta

# Les noms des projets et le chemin des fichiers.
projects = {
    '40_LAFFITE': '40_LAFFITE.csv',
    'LIGTHWELL': 'LIGTHWELL.csv',
    'MDLF': 'MDLF.csv',
    'GOODLIFE': 'GOODLIFE.csv',
    'AXA_MAT': 'AXA_MAT.csv',
    'LEDGER': 'LEDGER.csv',
    'PECM': 'PECM.csv'
}

# Styles personnalisés pour l'application.
def style_header():
    st.markdown("""
        <style>
        .header {
            background-color: #7FDBFF;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 20px;
            font-size: 24px;
        }
        .sidebar .css-1d391kg {
            background-color: #f8f9fa;
        }
        .sidebar .css-1v3fvcr {
            background-color: #f8f9fa;
        }
        .main .block-container {
            padding-top: 1rem;
        }
        </style>
        """, unsafe_allow_html=True)

style_header()
st.markdown('<div class="header">Exploration des GED KAIRNIAL : Cartographie interactive des données</div>', unsafe_allow_html=True)

# Spécification des types de données pour chaque colonne (mettre à jour selon votre fichier CSV)
dtype_spec = {
    'Date dépôt GED': str,
    'TYPE DE DOCUMENT': str,
    'PROJET': str,
    'EMET': str,
    'LOT': str,
    'INDICE': str,
}

# Fonction pour charger les données avec gestion des types
def load_data(filepath):
    return pd.read_csv(filepath, encoding='iso-8859-1', sep=';', dtype=dtype_spec, low_memory=False)

# Fonction pour mettre à jour le diagramme Sankey
def update_sankey(selected_file_path):
    data = load_data(selected_file_path)
    total_by_index = data['INDICE'].value_counts(normalize=True) * 100
    total_by_index = total_by_index.reset_index()
    total_by_index.columns = ['INDICE', 'Percentage']

    label_indices_with_percentage = total_by_index.apply(lambda row: f"{row['INDICE']} ({row['Percentage']:.2f}%)", axis=1)
    index_percentage_map = dict(zip(total_by_index['INDICE'], label_indices_with_percentage))
    data['INDICE'] = data['INDICE'].map(index_percentage_map)

    all_nodes = pd.concat([data['PROJET'], data['EMET'], data['TYPE DE DOCUMENT'], data['INDICE']]).unique()
    all_nodes = pd.Series(index=all_nodes, data=range(len(all_nodes)))

    source = all_nodes[data['PROJET']].tolist() + all_nodes[data['EMET']].tolist() + all_nodes[data['TYPE DE DOCUMENT']].tolist()
    target = all_nodes[data['EMET']].tolist() + all_nodes[data['TYPE DE DOCUMENT']].tolist() + all_nodes[data['INDICE']].tolist()
    value = [1]*len(data['PROJET']) + [1]*len(data['EMET']) + [1]*len(data['TYPE DE DOCUMENT'])

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color='black', width=0.5),
            label=all_nodes.index.tolist()
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])
    fig.update_layout(title_text="Flux de Documents par Projet avec Pourcentages d'Indice", font_size=10)
    return fig

# Menu latéral pour les onglets
with st.sidebar:
    selected = option_menu(
        menu_title="Menu",
        options=["Évolution des Types de Documents", "Flux des Documents", "Visualisation des Documents par Lot et Indice", "Repérer les acteurs majeurs de la GED", "Comparaison de la productivité entre chantiers"],
        icons=["line-chart", "exchange", "bar-chart", "users", "chart-bar"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical"
    )

# Onglet 1: Évolution des Types de Documents
if selected == "Évolution des Types de Documents":
    st.header("Évolution des Types de Documents")
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='tab1_project')
    data = load_data(projects[selected_project])
    data['Date dépôt GED'] = pd.to_datetime(data['Date dépôt GED'], format='%d/%m/%Y')
    type_document_options = data['TYPE DE DOCUMENT'].unique()
    selected_types = st.multiselect('Sélectionnez les types de document', type_document_options, default=type_document_options[0], key='tab1_types')
    
    data_grouped = data.groupby([data['Date dépôt GED'].dt.to_period("M"), 'TYPE DE DOCUMENT']).size().reset_index(name='Nombre de documents')
    data_grouped['Date dépôt GED'] = data_grouped['Date dépôt GED'].dt.to_timestamp()
    
    fig = go.Figure()
    for t in selected_types:
        filtered_data = data_grouped[data_grouped['TYPE DE DOCUMENT'] == t]
        fig.add_trace(go.Scatter(x=filtered_data['Date dépôt GED'], y=filtered_data['Nombre de documents'].cumsum(), mode='lines+markers', name=f'Cumulé - {t}'))
        fig.add_trace(go.Scatter(x=filtered_data['Date dépôt GED'], y=filtered_data['Nombre de documents'], mode='lines+markers', name=t, visible='legendonly'))

    fig.update_layout(
        title=f'Évolution du nombre de documents pour {selected_project}',
        xaxis_title='Date de Dépôt',
        yaxis_title='Nombre de Documents',
        legend_title='Type de Documents',
        height=500  # Ajuster la hauteur du graphique
    )
    st.plotly_chart(fig, use_container_width=True)  # Ajuster la largeur du graphique

# Onglet 2: Flux des Documents
elif selected == "Flux des Documents":
    st.header("Flux des Documents")
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='tab2_project')
    fig = update_sankey(projects[selected_project])
    fig.update_layout(height=600)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig, use_container_width=True)  # Ajuster la largeur du graphique

# Onglet 3: Visualisation des Documents par Lot et Indice
elif selected == "Visualisation des Documents par Lot et Indice":
    st.header("Visualisation des Documents par Lot et Indice")
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='tab3_project')
    data = load_data(projects[selected_project])
    indice_options = data['INDICE'].unique()
    selected_indices = st.multiselect('Sélectionnez un ou plusieurs INDICE(S)', indice_options, key='tab3_indices')

    if selected_indices:
        data = data[data['INDICE'].isin(selected_indices)]

    # Répartition des Document par Lot et Indice (Treemap)
    grouped_data_treemap = data.groupby(['LOT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_treemap = px.treemap(
        grouped_data_treemap,
        path=['LOT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Lot et Indice'
    )
    fig_treemap.update_layout(height=500)  # Ajuster la hauteur du graphique

    # Répartition des Documents par Type de Documents et Indice
    grouped_data_type_indice = data.groupby(['TYPE DE DOCUMENT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_type_indice = px.treemap(
        grouped_data_type_indice,
        path=['TYPE DE DOCUMENT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Type de Documents et Indice'
    )
    fig_type_indice.update_layout(height=500)  # Ajuster la hauteur du graphique

    # Nombre des Documents par lot
    documents_by_lot = data.groupby('LOT').size().reset_index(name='Nombre de Documents')
    fig_bar_lot = px.bar(
        documents_by_lot,
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
    documents_by_type = data.groupby('TYPE DE DOCUMENT').size().reset_index(name='Nombre de Documents')
    fig_bar_type = px.bar(
        documents_by_type,
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
elif selected == "Repérer les acteurs majeurs de la GED":
    st.header("Repérer les acteurs majeurs de la GED")
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='tab4_project')
    data = load_data(projects[selected_project])
    data['Date dépôt GED'] = pd.to_datetime(data['Date dépôt GED'], format='%d/%m/%Y')
    data['Année'] = data['Date dépôt GED'].dt.year

    # Répartition des Types de documents par Acteur (Ajouté par)
    fig_added_by = px.treemap(data, path=['Ajouté par', 'TYPE DE DOCUMENT'],
                              title='Répartition des Types de Documents par Acteur (Ajouté par)')
    fig_added_by.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=700)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig_added_by, use_container_width=True)

    # Répartition des Types de Documents par Emetteur
    fig_emitter = px.treemap(data, path=['EMET', 'TYPE DE DOCUMENT'],
                             title='Répartition des Types de Document par Émetteur')
    fig_emitter.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=700)  # Ajuster la hauteur du graphique
    st.plotly_chart(fig_emitter, use_container_width=True)

# Onglet 5: Comparaison de la productivité entre chantiers
elif selected == "Comparaison de la productivité entre chantiers":
    st.header("Comparaison de la productivité entre chantiers")
    period_selector = st.radio(
        'Sélectionnez la période',
        options=['6m', '12m', 'all'],
        format_func=lambda x: '6 premiers mois' if x == '6m' else '12 premiers mois' if x == '12m' else 'Toute la période',
        horizontal=True
    )
    selected_projects = st.multiselect('Sélectionnez les projets', list(projects.keys()), default=list(projects.keys()))

    def update_document_mass_comparison(selected_projects, selected_period):
        bar_data = []
        for project in selected_projects:
            df = pd.read_csv(projects[project], encoding='iso-8859-1', sep=';', dtype=str)
            df['Date dépôt GED'] = pd.to_datetime(df['Date dépôt GED'], format='%d/%m/%Y')
            start_date = df['Date dépôt GED'].min()
            if selected_period == '6m':
                end_date = start_date + timedelta(days=180)  # 6 mois
            elif selected_period == '12m':
                end_date = start_date + timedelta(days=365)  # 12 mois
            else:
                end_date = df['Date dépôt GED'].max()  # Toute la période

            filtered_df = df[(df['Date dépôt GED'] >= start_date) & (df['Date dépôt GED'] <= end_date)]
            total_documents = filtered_df.shape[0]
            bar_data.append({
                'Chantier': project,
                'Masse de documents': total_documents,
                'Date début': start_date.strftime('%Y-%m-%d'),
                'Date fin': end_date.strftime('%Y-%m-%d')
            })

        # Tri des données par masse de documents
        bar_df = pd.DataFrame(bar_data)
        bar_df = bar_df.sort_values(by='Masse de documents', ascending=False)

        # Création du graphique à barres
        bar_fig = px.bar(bar_df, x='Chantier', y='Masse de documents', text='Masse de documents',
                         color='Masse de documents', color_continuous_scale='reds',
                         hover_data=['Date début', 'Date fin'])

        bar_fig.update_layout(title='Comparaison de la masse de documents selon la période ',
                              xaxis_title='Chantier', yaxis_title='Masse de documents',
                              font=dict(size=15),width=1200)
        return bar_fig

    fig = update_document_mass_comparison(selected_projects, period_selector)
    st.plotly_chart(fig, use_container_width=True)
