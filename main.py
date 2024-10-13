from typing import List
import pandas as pd
import streamlit as st

st.write("Hello World")

###########################
# Pour nettoyer une page
# Enlever lignes 1, 3, 4, 5, 6, 7
# Enlever les lignes sans TOTAL dans la colonne 3
# Enlever Colonne 2 à 13
# Renommer colonne 1 en ID
# Les Colonnes n à n+5 sont pour la meme comp si elle est en n
# La premiere comp est en Col2
# Renommer les colonnes selon la ligne 0
# Supprimer la ligne 0
###########################
def clean_df_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop([0, 2, 3, 4, 5, 6, 7])
    row0 = df.iloc[0:1]
    df = pd.concat([row0, df[df.iloc[:, 2] == 'TOTAL']])
    column_index = df.columns[(df == "Compétence").any()].tolist()
    column_index = df.columns.get_loc(column_index[0])
    df = df.drop(df.columns[1:column_index+1], axis=1)
    df.rename(columns={df.columns[0]: 'ID'}, inplace=True)
    for i in range(1, len(df.columns)-1, 6):
        for j in range(i, i+6):
            df.rename(columns={df.columns[j]: df.iloc[0, i]}, inplace=True)
    df = df.iloc[1:]
    return df

def clean_data(data:dict[str, pd.DataFrame]) -> dict:
    res = {}
    for sheet in data:
        if sheet == 'Aide à la lecture':
            continue
        elif sheet == 'CPM':
            res['CPMA'] = clean_df_data(data[sheet])
        elif sheet == 'CPF':
            res['CPFR'] = clean_df_data(data[sheet])
        else:
            res[sheet] = clean_df_data(data[sheet])
    return res

def filter_level(data:dict[pd.DataFrame], niveaux:List[str]) -> dict:
    res = {}
    if len(niveaux) == 1 and niveaux[0] != "Tous":
        for sheet in data:
            if niveaux[0] in sheet:
                res[sheet] = data[sheet]
        return res
    
    elif len(niveaux) == 1 and niveaux[0] == "Tous":
        return data

    else:
        for niveau in niveaux:
            for sheet in data:
                if niveau in sheet:
                    res[sheet] = data[sheet]
            
    return res

def filter_subject(data:dict[pd.DataFrame], matiere:str) -> dict:
    res = {}
    if matiere != "Toutes":
        for sheet in data:
            if matiere in sheet:
                res[sheet] = data[sheet]
        return res
    
    elif matiere == "Toutes":
        return data
            
    return res

def filter_school(data:dict[pd.DataFrame], ecole:str) -> dict:
    res = {}
    secteurs = {}
    if ecole in secteurs:
        for sheet in data:
            res[sheet] = pd.concat([data[sheet][data[sheet].iloc[:, 0] == school] for school in secteurs[ecole]])
    else:
        for sheet in data:
            res[sheet] = data[sheet][data[sheet].iloc[:, 0] == ecole]
    return res

def filter_comp(data:dict[pd.DataFrame], comp:str) -> dict:
    res = {}
    if comp != "Toutes":
        for sheet in data:
            df = data[sheet]
            # Get the columns that are not 'comp' in the first row, except for the first column
            columns_to_drop = [col for col in df.columns if col != comp]
            # Drop those columns
            res[sheet] = df.drop(columns=columns_to_drop[1:])
        return res
    
    elif comp == "Toutes":
        return data
            
    return res

def calc_sheet_avg(sheet:pd.DataFrame) -> float:
    avg = 0
    col = len(sheet.columns)
    total = (col-1)//6
    for i in range(2, col, 2):
        temp = 0
        if (i-2)%6 == 0:
            temp = 1
        elif (i-2)%6 == 2:
            temp = 3
        elif (i-2)%6 == 4:
            temp = 5
        avg += sheet.iloc[0, i]*temp
    return avg/total

def calc_avg(data:dict) -> tuple[float, float]:
    avg_ma = 0.0
    ma_counter = 0
    avg_fr = 0.0
    fr_counter = 0
    for sheet in data:
        if 'MA' in sheet:
            ma_counter += 1
            avg_ma += calc_sheet_avg(data[sheet])
        elif 'FR' in sheet:
            fr_counter += 1
            avg_fr += calc_sheet_avg(data[sheet])
    if ma_counter == 0:
        ma_counter = 1
    if fr_counter == 0:
        fr_counter = 1
    avg_ma /= ma_counter
    avg_fr /= fr_counter

    return avg_ma, avg_fr

def requete(data:dict, schoolID:str, niveau:List[str], matiere:str, comp:str) -> tuple[float]:

    data = clean_data(data)
    data = filter_level(data, niveau)
    data = filter_subject(data, matiere)
    data = filter_school(data, schoolID)
    data = filter_comp(data, comp)

    avg_ma, avg_fr = calc_avg(data)

    return data, avg_ma, avg_fr


# Load the updated Excel file
file = st.file_uploader("Importer un tableau .xlsx", type=["xlsx"])
if file:
    data = pd.read_excel(file, sheet_name=None)


subject = st.selectbox(
    "Quelle(s) matière(s) voulez-vous analyser?",
    ("Toutes", "MA", "FR"),
)

level = st.multiselect(
    "Quel(s) niveau(x) voulez-vous analyser?",
    ["Tous", "CP", "CE1", "CE2", "CM1", "CM2"]
)

list_comp = ['Toutes']

if subject == "MA":
    list_comp += ['Résoudre des problèmes', 'Calculer', 'Géométrie', 'Grandeurs et mesures', 'Organisation et gestion de données']
elif subject == "FR":
    list_comp += ['Lire', 'Écrire', 'Étude de la langue']
else:
    list_comp += ['Résoudre des problèmes', 'Calculer', 'Géométrie', 'Grandeurs et mesures', 'Organisation et gestion de données', 'Lire', 'Écrire', 'Étude de la langue']

comp = st.text_input(
    "Quelle compétence voulez-vous analyser?"
)
if comp == "":
    comp = "Toutes"

schoolID = st.text_input("Entrez le code de l'école")

if st.button("Valider"):
    data, avg_ma, avg_fr = requete(data, schoolID, level, subject, comp)

    if subject == "MA":
        st.write(f"La moyenne de la compétence {comp} pour l'école {schoolID} est de {avg_ma} en MA")
    elif subject == "FR":
        st.write(f"La moyenne de la compétence {comp} pour l'école {schoolID} est de {avg_fr} en FR")
    else:
        st.write(f"La moyenne de la compétence {comp} pour l'école {schoolID} est de {avg_ma} en MA et {avg_fr} en FR")

