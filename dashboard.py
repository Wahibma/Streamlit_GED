import pandas as pd
from jupyter_dash import JupyterDash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go

# Les noms de projets
projects = {
    '40_LAFFITE': '40_LAFFITE.csv',
    'LIGTHWELL': 'LIGTHWELL.csv',
    'MDLF': 'MDLF.csv',
    'GOODLIFE': 'GOODLIFE.csv',
    'AXA_MAT': 'AXA_MAT.csv',
    'LEDGED': 'LEDGED.csv',
    'PECM': 'PECM.csv'
}

app = JupyterDash(__name__)

# Mise en page de l'application
app.layout = html.Div([
    html.H1("Exploration des GED KAIRNIAL : Cartographie interactive des données", style={'textAlign': 'center', 'color': '#F08080'}),

    # Section 1: Exploration temporelle des types de documents
    html.Div([
        dcc.Markdown('''
        ### 1. Évolution des Types de Documents au Fil du Temps

        Ce graphique montre comment l'utilisation des différents types de documents a évolué au fil du temps.

        **But:**

        - Identifier les tendances.
        - Indiquer des moments de forte activité de projet.
        ''',
        style={'margin': '20px'}),

        html.H2('Évolution du nombre de documents', style={'textAlign': 'center', 'color': '#7FDBFF'}),
        dcc.Dropdown(
            id='project-dropdown',
            options=[{'label': p, 'value': p} for p in projects.keys()],
            value=list(projects.keys())[0],
            clearable=False
        ),
        dcc.Dropdown(
            id='type-document-dropdown',
            clearable=False,
            multi=True
        ),
        dcc.Graph(id='line-graph')
    ], style={'margin': '20px'}),

    # Section 2: Exploration des flux de documents
    html.Div([
        dcc.Markdown('''
        ## 2 : Flux des Documents avec pourcentage d'indice

        Ce diagramme visualise le flux des documents depuis leur origine jusqu'à leur classement par indice.

        - Soulignant les parcours principaux que prennent les documents à travers le projet.
        - En intégrant les pourcentages directement dans les noms des indices, le graphique offre une vue claire sur la répartition des documents selon leur indice, **ce qui aide à comprendre quelles révisions ou versions sont les plus courantes.**
        ''',
        style={'margin': '20px'}),

        html.H2("Flux des Documents avec pourcentage d'indice", style={'textAlign': 'center', 'color': '#7FDBFF'}),
        dcc.Dropdown(
            id='project-dropdown-sankey',
            options=[{'label': name, 'value': path} for name, path in projects.items()],
            value=list(projects.values())[0],
            clearable=False
        ),
        dcc.Graph(id='sankey-diagram')
    ], style={'margin': '20px'}),

    # Section 3: Visualisation des Documents par Projet
    html.Div([
        html.H1("Visualisation des Documents par Projet", style={'textAlign': 'center', 'color': '#7FDBFF'}),

        # Sélection du projet
        dcc.Dropdown(
            id='project-dropdown-documents',
            options=[{'label': name, 'value': name} for name in projects.keys()],
            value='40_LAFFITE',  # Valeur par défaut
            clearable=False
        ),

        # Sélection de l'indice
        dcc.Dropdown(
            id='indice-dropdown',
            options=[],  # Les options seront mises à jour en fonction du projet sélectionné
            clearable=True,
            multi=True,
            placeholder='Sélectionnez un ou plusieurs INDICE(S)'
        ),

        # Section Markdown et Treemap pour la répartition par lot et indice
        dcc.Markdown('''
            ## 3 : Répartition des Documents par Lot et Indice

            Ce graphique aide à comprendre la distribution des documents selon les lots et leur indice, fournissant des aperçus concernant les parties du projet qui génèrent le plus de documentation et la fréquence des mises à jour ou révisions.

            **Focus sur les Lots:** Les lots avec un grand nombre de documents ou de révisions (indices élevés) peuvent nécessiter une attention particulière pour la gestion des risques et le contrôle qualité.

            **Révisions :** Un nombre élevé d'indices pour certains documents peut indiquer des problèmes dans la conception ou la communication au sein de l'équipe.
            ''',
            style={'margin': '20px'}
        ),
        dcc.Graph(id='document-treemap'),

        # Section Markdown et Graphique à barres horizontales pour le nombre de documents par lot
        dcc.Markdown('''
            ## Visualisation du Nombre de Documents par LOT

            Cette visualisation présente le nombre de documents associés à chaque lot sous forme de graphique à barres horizontales, facilitant l'identification des lots les plus documentés et ceux qui nécessitent potentiellement plus d'attention en termes de révision et de gestion de la qualité.
            ''',
            style={'margin': '20px'}
        ),
        dcc.Graph(id='simple-bar-chart'),
    ]),

    # Section 4: Repérer les acteurs majeurs de la GED
    html.Div([
        html.H1("Repérer les acteurs majeurs de la GED",style={'textAlign': 'center', 'color': '#7FDBFF'}),
        dcc.Dropdown(
            id='project-dropdown-actors',
            options=[{'label': name, 'value': name} for name in projects.keys()],
            value='40_LAFFITE',  # Valeur initiale
            clearable=False
        ),
        dcc.Graph(id='document-graph-actors'),
        html.P("Ces visualisations offrent une vue d'ensemble de qui ajoute quels types de documents et comment cela a évolué à travers les années.")
    ]),

    # Section 5: Répartition des Types de Document par Émetteur et par Année
    html.Div([
        html.H1("Répartition des Types de Document par Émetteur et par Année", style={'textAlign': 'center', 'color': '#7FDBFF'}),

        # Sélection du projet
        dcc.Dropdown(
            id='project-dropdown-emitter',
            options=[{'label': name, 'value': name} for name in projects.keys()],
            value='40_LAFFITE',  # Valeur par défaut
            clearable=False
        ),

        # Section Markdown et Graphique pour la répartition par émetteur et année
        dcc.Markdown('''
            Ce graphique affiche la distribution des types de documents émis par chaque contributeur sur plusieurs années.

            Distinguer les responsabilités et les spécialités de chaque émetteur basées sur les types de documents qu'ils produisent.
            ''',
            style={'margin': '20px'}
        ),
        dcc.Graph(id='document-graph-emitter-year'),
    ]),
])
# Callback pour mettre à jour les options du dropdown des types de documents
@app.callback(
    [Output('type-document-dropdown', 'options'),
     Output('type-document-dropdown', 'value')],
    Input('project-dropdown', 'value')
)
def update_document_dropdown(selected_project):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-2', sep=';')
    options = [{'label': t, 'value': t} for t in donnees['TYPE DE DOCUMENT'].unique()]
    return options, [donnees['TYPE DE DOCUMENT'].unique()[0]]

# Callback pour mettre à jour le graphique temporel en fonction des sélections
@app.callback(
    Output('line-graph', 'figure'),
    [Input('type-document-dropdown', 'value'),
     State('project-dropdown', 'value')]
)
def update_line_chart(selected_types, selected_project):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y')
    donnees_groupées = donnees.groupby([donnees['Date dépôt GED'].dt.to_period("M"), 'TYPE DE DOCUMENT']).size().reset_index(name='Nombre de documents')
    donnees_groupées['Date dépôt GED'] = donnees_groupées['Date dépôt GED'].dt.to_timestamp()

    fig = go.Figure()

    if selected_types:
        filtered_data = donnees_groupées[donnees_groupées['TYPE DE DOCUMENT'].isin(selected_types)]
        for t in selected_types:
            data_type = filtered_data[filtered_data['TYPE DE DOCUMENT'] == t]
            data_type = data_type.sort_values('Date dépôt GED')
            fig.add_trace(go.Scatter(x=data_type['Date dépôt GED'], y=data_type['Nombre de documents'].cumsum(), mode='lines+markers', name=f'Cumulé - {t}'))
            fig.add_trace(go.Scatter(x=data_type['Date dépôt GED'], y=data_type['Nombre de documents'], mode='lines+markers', name=t, visible='legendonly'))

    fig.update_layout(
        title=f'Évolution du nombre de documents pour {selected_project}',
        xaxis_title='Date de Dépôt',
        yaxis_title='Nombre de Documents',
        legend_title='Type de Documents'
    )

    return fig

# Callback pour mettre à jour le diagramme Sankey en fonction des sélections
@app.callback(
    Output('sankey-diagram', 'figure'),
    Input('project-dropdown-sankey', 'value')
)
def update_sankey(selected_file_path):
    donnees = pd.read_csv(selected_file_path, encoding='iso-8859-1', sep=';')
    total_par_indice = donnees['INDICE'].value_counts(normalize=True) * 100
    total_par_indice = total_par_indice.reset_index()
    total_par_indice.columns = ['INDICE', 'Pourcentage']

    labels_indices_avec_pourcentages = total_par_indice.apply(lambda row: f"{row['INDICE']} ({row['Pourcentage']:.2f}%)", axis=1)
    map_indice_pourcentage = dict(zip(total_par_indice['INDICE'], labels_indices_avec_pourcentages))
    donnees['INDICE'] = donnees['INDICE'].map(map_indice_pourcentage)

    all_nodes = pd.concat([donnees['PROJET'], donnees['EMET'], donnees['TYPE DE DOCUMENT'], donnees['INDICE']]).unique()
    all_nodes = pd.Series(index=all_nodes, data=range(len(all_nodes)))

    source = all_nodes[donnees['PROJET']].tolist() + all_nodes[donnees['EMET']].tolist() + all_nodes[donnees['TYPE DE DOCUMENT']].tolist()
    target = all_nodes[donnees['EMET']].tolist() + all_nodes[donnees['TYPE DE DOCUMENT']].tolist() + all_nodes[donnees['INDICE']].tolist()
    value = [1]*len(donnees['PROJET']) + [1]*len(donnees['EMET']) + [1]*len(donnees['TYPE DE DOCUMENT'])

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

# Callback pour mettre à jour les options du dropdown des indices en fonction du projet sélectionné
@app.callback(
    Output('indice-dropdown', 'options'),
    Input('project-dropdown-documents', 'value')
)
def update_indice_dropdown(selected_project):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')
    indices = donnees['INDICE'].unique()
    return [{'label': indice, 'value': indice} for indice in indices]

# Callback pour mettre à jour les graphiques en fonction des sélections de projet et d'indices
@app.callback(
    [Output('document-treemap', 'figure'),
     Output('simple-bar-chart', 'figure')],
    [Input('project-dropdown-documents', 'value'), Input('indice-dropdown', 'value')]
)
def update_graphs(selected_project, selected_indices):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')

    # Filtre basé sur la sélection des indices
    if selected_indices:
        donnees = donnees[donnees['INDICE'].isin(selected_indices)]

    # Treemap pour la répartition par lot et indice
    donnees_groupées_treemap = donnees.groupby(['LOT', 'INDICE']).size().reset_index(name='Nombre de Documents')
    fig_treemap = px.treemap(
        donnees_groupées_treemap,
        path=['LOT', 'INDICE'],
        values='Nombre de Documents',
        title='Répartition des Documents par Lot et Indice'
    )

    # Graphique à barres horizontales pour le nombre de documents par lot avec filtrage par indice
    documents_par_lot = donnees.groupby('LOT').size().reset_index(name='Nombre de Documents')
    fig_simple_bar = px.bar(
        documents_par_lot,
        y='LOT',
        x='Nombre de Documents',
        orientation='h',
        title="Nombre de Documents par LOT",
        labels={"LOT": "LOT", "Nombre de Documents": "Nombre de Documents"},
        color='Nombre de Documents',
        color_continuous_scale=px.colors.sequential.Viridis
    )
    fig_simple_bar.update_layout(yaxis={'categoryorder': 'total ascending'})

    return fig_treemap, fig_simple_bar

# Callback pour mettre à jour le graphique des acteurs majeurs
@app.callback(
    Output('document-graph-actors', 'figure'),
    [Input('project-dropdown-actors', 'value')]
)
def update_graph(selected_project):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')
    # Préparation des données pour la visualisation
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'],format='%d/%m/%Y')
    donnees['Année'] = donnees['Date dépôt GED'].dt.year

    # Création de la visualisation avec Plotly Express
    fig = px.treemap(donnees, path=['Année', 'Ajouté par', 'TYPE DE DOCUMENT'],
                     title='Répartition des Types de Documents par acteur (Ajouté par) et par Année')
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig

# Callback pour mettre à jour le graphique de la répartition par émetteur et année
@app.callback(
    Output('document-graph-emitter-year', 'figure'),
    [Input('project-dropdown-emitter', 'value')]
)
def update_graph_emitter_year(selected_project):
    chemin_fichier = projects[selected_project]
    donnees = pd.read_csv(chemin_fichier, encoding='iso-8859-1', sep=';')
    # Préparation des données pour la visualisation
    donnees['Date dépôt GED'] = pd.to_datetime(donnees['Date dépôt GED'], format='%d/%m/%Y')
    donnees['Année'] = donnees['Date dépôt GED'].dt.year

    # Création de la visualisation avec Plotly Express
    fig = px.treemap(donnees, path=['Année', 'EMET', 'TYPE DE DOCUMENT'],
                     title='Répartition des Types de Document par Émetteur et par Année')
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig
# Exécution de l'application :
if __name__ == '__main__':
    app.run_server(debug=True, port=2000)