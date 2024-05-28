import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Les noms des projects.

projects = {
    '40_LAFFITE': '40_LAFFITE.csv',
    'LIGTHWELL': 'LIGTHWELL.csv',
    'MDLF': 'MDLF.csv',
    'GOODLIFE': 'GOODLIFE.csv',
    'AXA_MAT': 'AXA_MAT.csv',
    'LEDGER': 'LEDGER.csv',
    'PECM': 'PECM.csv'
}

# Styles personnalisés

def style_header():
    st.markdown(
        """
        <style>
        .header {
            background-color: #7FDBFF;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 10px;
        }
        .table-header {
            background-color: #f2f2f2;
            color: black;
            font-weight: bold;
            text-align: center;
            padding: 10px;
        }
        .tab-style {
            background-color: #f2f2f2;
            padding: 6px;
        }
        .tab-selected-style {
            background-color: #7FDBFF;
            color: white;
            padding: 6px;
        }
        </style>
        """, unsafe_allow_html=True
    )

# Mise en place application

style_header()

st.markdown('<div class="header">Exploration des GED KAIRNIAL : Cartographie interactive des données</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Évolution des Types de Documents', 'Flux des Documents', 'Visualisation des Documents par Projet', 'Repérer les acteurs majeurs de la GED', 'Répartition des Types de Document par Émetteur'])

with tab1:
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()))
    data = pd.read_csv(projects[selected_project], encoding='iso-8859-1', sep=';')
    type_document_options = data['TYPE DE DOCUMENT'].unique()
    selected_types = st.multiselect('Sélectionnez les types de document', type_document_options, default=type_document_options[0])

    data['Date dépôt GED'] = pd.to_datetime(data['Date dépôt GED'], format='%d/%m/%Y')
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
        legend_title='Type de Documents'
    )
    st.plotly_chart(fig)

with tab2:
    selected_file_path = st.selectbox('Sélectionnez un projet', [path for name, path in projects.items()])
    data = pd.read_csv(selected_file_path, encoding='iso-8859-1', sep=';')
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
    st.plotly_chart(fig)

with tab3:
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='documents')
    data = pd.read_csv(projects[selected_project], encoding='iso-8859-1', sep=';')
    indice_options = data['INDICE'].unique()
    selected_indices = st.multiselect('Sélectionnez un ou plusieurs INDICE(S)', indice_options)

    if selected_indices:
        data = data[data['INDICE'].isin(selected_indices)]

    grouped_data_treemap = data.groupby(['LOT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_treemap = px.treemap(
        grouped_data_treemap,
        path=['LOT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Lot et Indice'
    )

    grouped_data_bar = data.groupby(['LOT']).size().reset_index(name='Nombre de Documents')
    fig_bar = px.bar(
        grouped_data_bar,
        x='LOT',
        y='Nombre de Documents',
        title='Nombre de Documents par LOT',
        labels={'LOT': 'LOT', 'Nombre de Documents': 'Nombre de Documents'}
    )

    documents_by_lot = data.groupby('LOT').size().reset_index(name='Nombre de Documents')
    fig_simple_bar = px.bar(
        documents_by_lot,
        y='LOT',
        x='Nombre de Documents',
        orientation='h',
        title="Nombre de Documents par LOT",
        labels={"LOT": "LOT", "Nombre de Documents": "Nombre de Documents"},
        color='Nombre de Documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_simple_bar.update_layout(yaxis={'categoryorder': 'total ascending'})

    st.plotly_chart(fig_treemap)
    st.plotly_chart(fig_bar)
    st.plotly_chart(fig_simple_bar)

with tab4:
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='actors')
    data = pd.read_csv(projects[selected_project], encoding='iso-8859-1', sep=';')
    data['Date dépôt GED'] = pd.to_datetime(data['Date dépôt GED'], format='%d/%m/%Y')
    data['Année'] = data['Date dépôt GED'].dt.year

    fig = px.treemap(data, path=['Ajouté par', 'TYPE DE DOCUMENT'],
                     title='Répartition des Types de Documents par acteur (Ajouté par)')
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig)

with tab5:
    selected_project = st.selectbox('Sélectionnez un projet', list(projects.keys()), key='emitter_year')
    data = pd.read_csv(projects[selected_project], encoding='iso-8859-1', sep=';')
    data['Date dépôt GED'] = pd.to_datetime(data['Date dépôt GED'], format='%d/%m/%Y')
    data['Année'] = data['Date dépôt GED'].dt.year

    fig = px.treemap(data, path=['EMET', 'TYPE DE DOCUMENT'],
                     title='Répartition des Types de Document par Émetteur')
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig)
