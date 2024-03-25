"""Module permettant de générer les fichiers `excel` décrivant les résultats de modélisation"""
import re
import os
import datetime
import pandas as pd
import horaires
from main import DATA_DICT
from util import InstanceSheetNames, TachesColumnNames, OutputColumnNames

RE_TRAIN = re.compile("Train")

def create_output_xls_file(filepath):
    """Crée le fichier `excel` associé à la solution du fichier `filepath`"""
    file_name = filepath.split("/")[-1].replace(".sol", "")
    excel_filepath = "Outputs/Output_" + file_name + ".xlsx"
    output_df = pd.DataFrame(columns=[OutputColumnNames.OUT_TASK_ID,
                                 OutputColumnNames.OUT_TASK_TYPE,
                                 OutputColumnNames.OUT_DATE,
                                 OutputColumnNames.OUT_START_TIME,
                                 OutputColumnNames.OUT_DURATION,
                                 OutputColumnNames.OUT_TRAIN])
    output_rows = []
    with open(filepath, encoding="UTF-8") as cursor:
        first_day = get_first_day_manual(cursor)
        cursor.seek(0)
        for row in cursor:
            data = extract_data_from_row(row, first_day)
            if data is not None:
                output_rows.append(data)
        output_df = pd.DataFrame(output_rows)
        output_df.to_excel(excel_filepath, sheet_name="Taches machine", index=False)

def extract_data_from_row(row: str, first_day: datetime.date) -> dict:
    """Extrait toutes les informations nécessaires de `row`"""
    split_row = row.split(sep=" ")
    var_name, value = split_row[0], split_row[1]
    if RE_TRAIN.search(var_name) is None:
        return None
    # Id, Type et Sillon de la tache
    elements = var_name.split("_")
    # task_type = elements[-1]
    # task_train_nb = elements[-2]
    # task_train_date = elements[-3]
    task_id = f"{elements[-1]}_{elements[-3]}_{elements[-2]}"

    # Jour et heure de la tache
    value = int(value)
    opt_jour, opt_heure, opt_minute = horaires.entier_vers_triplet(value)
    out_date = first_day + datetime.timedelta(days=opt_jour-1)
    out_date = datetime.datetime.strftime(out_date, '%d/%m/%Y')
    out_start_time = datetime.time(hour=opt_heure, minute=opt_minute)

    # Durée de la tache
    df_tasks = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
    task_duration = int(df_tasks.loc[df_tasks[TachesColumnNames.TASK_LINK]==f"{elements[-1]}=",
                                     TachesColumnNames.TASK_DURATION])

    return {OutputColumnNames.OUT_TASK_ID: task_id,
        OutputColumnNames.OUT_TASK_TYPE: elements[-1],
        OutputColumnNames.OUT_DATE: out_date,
        OutputColumnNames.OUT_START_TIME: out_start_time,
        OutputColumnNames.OUT_DURATION: task_duration,
        OutputColumnNames.OUT_TRAIN: elements[-2]
        }

def get_first_day_manual(data :list) -> datetime.date:
    """Recherche et renvoie le premier jour apparaissant dans `data`"""
    first = datetime.date.max
    for row in data:
        if RE_TRAIN.search(row) is None:
            continue
        new_date_str = row.split(sep="_")[2]
        new_date = datetime.datetime.strptime(new_date_str, '%d/%m/%Y').date()
        if new_date < first:
            first = new_date
    return first

if __name__ == "__main__":
    for file in os.listdir("./Outputs"):
        if file.endswith(".sol"):
            create_output_xls_file(f"Outputs/{file}")
