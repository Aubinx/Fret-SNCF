import re
import datetime
import pandas as pd
import horaires
from lecture_donnees import INSTANCE, DATA_DICT, get_first_day
from model import VARIABLES
from util import InstanceSheetNames, TachesColumnNames, OutputColumnNames

EXCEL_FILEPATH = "Outputs/Output_" + INSTANCE + ".xlsx"

re_train = re.compile("Train")

output_df = pd.DataFrame(columns=[OutputColumnNames.OUT_TASK_ID,
                                 OutputColumnNames.OUT_TASK_TYPE,
                                 OutputColumnNames.OUT_DATE,
                                 OutputColumnNames.OUT_START_TIME,
                                 OutputColumnNames.OUT_DURATION,
                                 OutputColumnNames.OUT_TRAIN])
rows = []
for var_name in VARIABLES.keys():
    if not re_train.search(var_name):
        continue
    # Id, Type et Sillon de la tache
    elements = var_name.split("_")
    task_type = elements[-1]
    task_train_nb = elements[-2]
    task_train_date = elements[-3]
    task_id = f"{task_type}_{task_train_date}_{task_train_nb}"
    # Jour et heure de la tache
    opt_value = int(VARIABLES[var_name].X)
    opt_jour, opt_heure, opt_minute = horaires.entier_vers_triplet(opt_value)

    out_date = get_first_day(DATA_DICT) + datetime.timedelta(days=(opt_jour-1))
    out_start_time = datetime.time(hour=opt_heure, minute=opt_minute)

    # Durée de la tache
    df_tasks = DATA_DICT[InstanceSheetNames.SHEET_TACHES]
    task_duration = int(df_tasks[df_tasks[TachesColumnNames.TASK_LINK]==f"{task_type}="][TachesColumnNames.TASK_DURATION])

    rows.append({OutputColumnNames.OUT_TASK_ID: task_id,
           OutputColumnNames.OUT_TASK_TYPE: task_type,
           OutputColumnNames.OUT_DATE: out_date,
           OutputColumnNames.OUT_START_TIME: out_start_time,
           OutputColumnNames.OUT_DURATION: task_duration,
           OutputColumnNames.OUT_TRAIN: task_train_nb
          })
    
output_df = pd.DataFrame(rows)


output_df.to_excel(EXCEL_FILEPATH, sheet_name="Taches machine", index=False)
