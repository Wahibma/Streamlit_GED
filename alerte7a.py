import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Les noms des projets
projets = {
    'LIGTHWELL': 'LIGTHWELL.csv',
    '40_LAFFITE': '40_LAFFITE.csv',
    'MDLF': 'MDLF.csv',
    'AXA_MAT': 'AXA_MAT.csv',
    'LEDGER': 'LEDGER.csv',
    'GOODLIFE': 'GOODLIFE.csv',
    'PECM': 'PECM.csv'
}

# Styles CSS personnalisés
styles = """
    <style>
        .header {
            background-color: #007BFF;
            color: white;
            font-weight: bold;
            text-align: center;
            padding: 10px;
            font-size: 24px;
            border-radius: 10px;
        }
        .subheader {
            font-size: 20px;
            font-weight: bold;
            margin-top: 20px;
        }
        .section {
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .table-header {
            background-color: #f8f9fa;
            color: black;
            font-weight: bold;
            text-align: center;
            padding: 10px;
        }
        .lightgreen {
            background-color: lightgreen;
            color: black;
        }
        .yellow {
            background-color: yellow;
            color: black;
        }
        .red {
            background-color: red;
            color: white;
        }
        .orange {
            background-color: orange;
            color: black;
        }
    </style>
"""
st.markdown(styles, unsafe_allow_html=True)

# Fonction pour déterminer le niveau d'alerte en fonction du nombre d'indices
def determiner_niveau_alerte(compte):
    if compte < 3:
        return "Tout va bien"
    elif 3 <= compte <= 6:
        return "Attention ! Des indices à surveiller"
    else:
        return "Alerte !!! Trop d’indice à haut risque !!!"

# Fonction pour créer un graphique circulaire à partir des données
def create_pie_chart(data, column, title):
    labels = data[column].value_counts().index.tolist()
    values = data[column].value_counts().values.tolist()

    color_map = {
        "Tout va bien": "lightgreen",
        "Attention ! Des indices à surveiller": "yellow",
        "Alerte !!! Trop d’indice à haut risque !!!": "red",
        "Tout va bien !": "lightgreen",
        "Attention ! Des indices à surveiller !": "orange"
    }

    colors = [color_map[label] for label in labels]

    trace = go.Pie(labels=labels, values=values, hole=0.3,
                   marker=dict(colors=colors),
                   textinfo='percent',
                   insidetextorientation='horizontal')
    layout = go.Layout(
        title=title,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation='h', xanchor='center', x=0.5, y=-0.1),
        annotations=[dict(text=title, x=0.5, y=0.5, font_size=20, showarrow=False)]
    )
    return go.Figure(data=[trace], layout=layout)

st.markdown("<div class='header'>Indicateur de Récapitulatif d'Alerte</div>", unsafe_allow_html=True)

# Disposition des filtres en ligne
st.markdown("<div class='subheader section'>Sélections</div>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 1])
with col1:
    onglet = st.selectbox("Catégorie", ["Par LOT", "Par TYPE DE DOCUMENT"])
with col2:
    selected_file_path = st.selectbox("Projet", list(projets.values()))

st.markdown("<div class='subheader section'>Recherche</div>", unsafe_allow_html=True)
col3, col4, col5 = st.columns([1, 1, 1])
with col3:
    search_value = st.text_input(f"Rechercher par {onglet.split()[-1]}...")
with col4:
    search_value_alert = st.text_input("Rechercher par Alerte 1...")
with col5:
    search_value_alert2 = st.text_input("Rechercher par Alerte 2...")

def display_table(dataframe):
    if search_value_alert:
        dataframe = dataframe[dataframe['Alerte 1'].str.contains(search_value_alert, case=False)]
    if search_value_alert2:
        dataframe = dataframe[dataframe['Alerte 2'].str.contains(search_value_alert2, case=False)]

    styled_dataframe = dataframe.style.applymap(color_alerte, subset=['Alerte 1']).applymap(color_alerte2, subset=['Alerte 2'])
    st.dataframe(styled_dataframe, height=600)

    col6, col7 = st.columns(2)
    with col6:
        st.plotly_chart(create_pie_chart(dataframe, 'Alerte 1', 'Alerte 1'), use_container_width=True)
    with col7:
        st.plotly_chart(create_pie_chart(dataframe, 'Alerte 2', 'Alerte 2'), use_container_width=True)

def color_alerte(val):
    if val == "Tout va bien":
        color = 'lightgreen'
    elif val == "Attention ! Des indices à surveiller":
        color = 'yellow'
    else:
        color = 'red'
    return f'background-color: {color}'

def color_alerte2(val):
    if val == "Tout va bien !":
        color = 'lightgreen'
    else:
        color = 'orange'
    return f'background-color: {color}'

df = pd.read_csv(selected_file_path, encoding='iso-8859-1', sep=';', low_memory=False)

if onglet == "Par LOT":
    df['LOT'] = df['LOT'].astype(str)
    if search_value:
        df = df[df['LOT'].str.contains(search_value, case=False)]
    group_column = 'LOT'
elif onglet == "Par TYPE DE DOCUMENT":
    df['TYPE DE DOCUMENT'] = df['TYPE DE DOCUMENT'].astype(str)
    if search_value:
        df = df[df['TYPE DE DOCUMENT'].str.contains(search_value, case=False)]
    group_column = 'TYPE DE DOCUMENT'

total_indices = df.groupby(group_column).size().rename(f"Total Indices par {group_column}")
indices_groupes = df.groupby([group_column, 'INDICE']).size().reset_index(name="Nombre de documents")
indices_groupes = indices_groupes.merge(total_indices, on=group_column)
indices_groupes['Proportion'] = (indices_groupes['Nombre de documents'] / indices_groupes[f"Total Indices par {group_column}"] * 100).round(2)

top_deux_indices = indices_groupes.sort_values(by=[group_column, 'Proportion'], ascending=[True, False]).groupby(group_column).head(2)
somme_proportions_top_deux = top_deux_indices.groupby(group_column)['Proportion'].sum().reset_index(name='Somme des deux principales proportions')
somme_proportions_top_deux['Somme des deux principales proportions'] = somme_proportions_top_deux['Somme des deux principales proportions'].round(0).astype(int).astype(str) + '%'

indices_uniques = df.groupby(group_column)['INDICE'].nunique().reset_index(name='Compteur Indice')
dernier_indice = df.sort_values(by=[group_column, 'INDICE'], ascending=[True, False]).drop_duplicates(subset=group_column, keep='first')[[group_column, 'INDICE']].rename(columns={'INDICE': 'Dernier Indice'})

donnees_finales = somme_proportions_top_deux.merge(indices_uniques, on=group_column)
donnees_finales = donnees_finales.merge(dernier_indice, on=group_column)
donnees_finales['Alerte 1'] = donnees_finales['Compteur Indice'].apply(determiner_niveau_alerte)
donnees_finales['Alerte 2'] = donnees_finales['Somme des deux principales proportions'].apply(lambda x: "Tout va bien !" if x[:-1].isdigit() and int(x[:-1]) >= 80 else "Attention ! Des indices à surveiller")

# Abréger ou faire un saut de ligne pour les longues chaînes
donnees_finales['Somme des deux principales proportions'] = donnees_finales['Somme des deux principales proportions'].apply(lambda x: x.replace(' ', '\n'))

colonnes_ordonnees = [group_column, 'Compteur Indice', 'Dernier Indice', 'Alerte 1', 'Somme des deux principales proportions', 'Alerte 2']
donnees_finales = donnees_finales[colonnes_ordonnees]

display_table(donnees_finales)
