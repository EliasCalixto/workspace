import os
import sys
import pandas as pd
from tools.case_initializer import init_case

export_comp_path = "Expedia Templates/BMC/BMC1/EXPORT Compensation Cloud Export.xlsx"
export_cxl_path = "Expedia Templates/BMC/BMC1/EXPORT CXL Cloud Export.xlsx"
export_EQC_path = "Expedia Templates/BMC/BMC1/EXPORT EQC Cloud Export.xlsx"
export_FeeSet_path = "Expedia Templates/BMC/BMC1/EXPORT FeeSet Cloud Export.xlsx"
export_Promotion_path = "Expedia Templates/BMC/BMC1/EXPORT Promotion Export.xlsx"
export_PSNS_path = "Expedia Templates/BMC/BMC1/EXPORT PS&NS Export_Full.xlsx"
export_RPL_path = "Expedia Templates/BMC/BMC1/EXPORT RPL Cloud Export.xlsx"
export_RTRP_path1 = "Expedia Templates/BMC/BMC1/EXPORT RT&RP Cloud Export_Full.xlsx"
export_RTRP_path2 = "Expedia Templates/BMC/BMC1/EXPORT RT&RP Cloud Export_RP Info Only.xlsx"
export_ids_path = "Expedia Templates/BMC/BMC1/EXPORT VOID Export.xlsx"
import_BMC_path = "Expedia Templates/BMC/BMC1/IMPORT 1 BMC Cloud Property.xlsx"
import_compensation_path = "Expedia Templates/BMC/BMC1/IMPORT 2 Compensation Update.xlsx"


def data_to_json(path):
    df = pd.read_excel(path)
    data_as_dict = df.to_dict(orient="records")
    
    return data_as_dict


data_comp_export = data_to_json(export_comp_path)
new_comp_path = "EXPORT Compensation Cloud Export.xlsx"

data_cxl_export = data_to_json(export_cxl_path)
new_cxl_path = "EXPORT CXL Cloud Export.xlsx"

data_EQC_export = data_to_json(export_EQC_path)
new_EQC_path = "EXPORT EQC Cloud Export.xlsx"

data_FeeSet_export = data_to_json(export_FeeSet_path)
new_FeeSet_path = "EXPORT FeeSet Cloud Export.xlsx"

data_Promotion_export = data_to_json(export_Promotion_path)
new_Promotion_path = "EXPORT Promotion Export.xlsx"

data_PSNS_export = data_to_json(export_PSNS_path)
new_PSNS_path = "EXPORT PS&NS Export_Full.xlsx"

data_RPL_export = data_to_json(export_RPL_path)
new_RPL_path = "EXPORT RPL Cloud Export.xlsx"

data_RTRP1_export = data_to_json(export_RTRP_path1)
new_RTRP1_path = "EXPORT RT&RP Cloud Export_Full.xlsx"

data_RTRP2_export = data_to_json(export_RTRP_path2)
new_RTRP2_path = "EXPORT RT&RP Cloud Export_RP Info Only.xlsx"

data_ids_export = data_to_json(export_ids_path)
new_ids_path = "EXPORT VOID Export.xlsx"

data_BMC_import = data_to_json(import_BMC_path)
new_BMC_path = "IMPORT 1 BMC Cloud Property.xlsx"

data_compensation_import = data_to_json(import_compensation_path)
new_compensationImport_path = "IMPORT 2 Compensation Update.xlsx"


if __name__ == "__main__":
    args = []
    for i,arg in enumerate(sys.argv):
        args.append(arg)
    
    try:
        init_case(args[1], data_ids_export, new_ids_path)
        init_case(args[1], data_comp_export, new_comp_path)
        init_case(args[1], data_cxl_export, new_cxl_path)
        init_case(args[1], data_EQC_export, new_EQC_path)
        init_case(args[1], data_FeeSet_export, new_FeeSet_path)
        init_case(args[1], data_Promotion_export, new_Promotion_path)
        init_case(args[1], data_PSNS_export, new_PSNS_path)
        init_case(args[1], data_RPL_export, new_RPL_path)
        init_case(args[1], data_RTRP1_export, new_RTRP1_path)
        init_case(args[1], data_RTRP2_export, new_RTRP2_path)
        init_case(args[1], data_BMC_import, new_BMC_path)
        init_case(args[1], data_compensation_import, new_compensationImport_path)
        os.mkdir(f'APM files/{args[1]}/Exports Results')
        os.mkdir(f'APM files/{args[1]}/Imports Results')
    except:
        print('Does not met arguments requirements, directory not created.')
