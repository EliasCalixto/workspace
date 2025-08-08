import os
import sys
import pandas as pd
from tools.case_initializer import init_case

remove_stop_selling_file_path = 'IMPORT Stop Sell Removal.xlsx'


def onboarding() -> None:
    args = sys.argv

    if len(args) == 3:
        case_id, account_id, hotel_id = args[1], args[2], ""
    elif len(args) == 4:
        case_id, account_id, hotel_id = args[1], args[2], args[3]
    else:
        print('Does not met arguments requirements, directory not created.')
        return

    data_frame = {
        'Hotel ID': [hotel_id],
        'SF ID': [case_id],
        'Stop Sell Property': ['No'],
        'Action Type': ['Update']
    }
    init_case(case_id, data_frame, remove_stop_selling_file_path)  # type: ignore
    os.mkdir(f'APM files/{case_id}/Imports Results')

    data_csv = [
        {'Account ID': hotel_id, 'Managed by': account_id}
    ]
    df_csv = pd.DataFrame(data_csv)
    file_path_csv = f'APM files/{case_id}/{case_id} UpdateManagedBy.csv'
    df_csv.to_csv(file_path_csv, index=False)


if __name__ == "__main__":
    onboarding()
