import os
import sys
from tools.caseInitializer import init_case
from BusinessModelConversion import data_to_json

export_comp_path = "Expedia Templates/BMC/BMC2/EXPORT Compensation Cloud Export.xlsx"
export_promo_path = "Expedia Templates/BMC/BMC2/EXPORT Promotion Export.xlsx"
export_PSNS_path = "Expedia Templates/BMC/BMC2/EXPORT PS&NS Export_Full.xlsx"
export_RPL_path = "Expedia Templates/BMC/BMC2/EXPORT RPL Cloud Export.xlsx"
export_RTRPClone_path = "Expedia Templates/BMC/BMC2/EXPORT RT&RP Cloud Export_Clone.xlsx"
import_promo_path = "Expedia Templates/BMC/BMC2/IMPORT 1 Promotion Basic MOD Evergreen.xlsx"
import_RPL_path = "Expedia Templates/BMC/BMC2/IMPORT 3 RPL Cloud Create10%.xlsx"
import_rmv_stopsell = "Expedia Templates/BMC/BMC2/IMPORT 4 remove Stop-Sell.xlsx"
import_remove_old_pkg = "Expedia Templates/BMC/BMC2/IMPORT remove old Packages.xlsx"
import_remove_old_promo = "Expedia Templates/BMC/BMC2/IMPORT remove old Promotions.xlsx"

data_comp_export = data_to_json(export_comp_path)
new_comp_path = "EXPORT Compensation Cloud Export.xlsx"

data_promo_export = data_to_json(export_promo_path)
new_promo_path = "EXPORT Promotion Export.xlsx"

data_PSNS_export = data_to_json(export_PSNS_path)
new_PSNS_path = "EXPORT PS&NS Export_Full.xlsx"

data_RPL_export = data_to_json(export_RPL_path)
new_RPL_path = "EXPORT RPL Cloud Export.xlsx"

data_RTRPClone_export = data_to_json(export_RTRPClone_path)
new_RTRPClone_path = "EXPORT RT&RP Cloud Export_Clone.xlsx"

data_promo_import = data_to_json(import_promo_path)
new_promoImport_path = "IMPORT 1 Promotion Basic MOD Evergreen.xlsx"

data_RPL_import = data_to_json(import_RPL_path)
new_RPLImport_path = "IMPORT 3 RPL Cloud Create10%.xlsx"

data_rmv_stopsell = data_to_json(import_rmv_stopsell)
new_rmv_stopsell_path = "IMPORT 4 remove Stop-Sell.xlsx"

data_remove_old_pkg = data_to_json(import_remove_old_pkg)
new_remove_old_pkg_path = "IMPORT remove old Packages.xlsx"

data_remove_old_promo = data_to_json(import_remove_old_promo)
new_remove_old_promo_path = "IMPORT remove old Promotions.xlsx"



if __name__ == "__main__":
    args = []
    
    for i,arg in enumerate(sys.argv):
        args.append(arg)
    
    try:
        init_case(args[1], data_comp_export, new_comp_path)
        init_case(args[1], data_promo_export, new_promo_path)
        init_case(args[1], data_PSNS_export, new_PSNS_path)
        init_case(args[1], data_RPL_export, new_RPL_path)
        init_case(args[1], data_RTRPClone_export, new_RTRPClone_path)
        init_case(args[1], data_promo_import, new_promoImport_path)
        init_case(args[1], data_RPL_import, new_RPLImport_path)
        init_case(args[1], data_rmv_stopsell, new_rmv_stopsell_path)
        init_case(args[1], data_remove_old_pkg, new_remove_old_pkg_path)
        init_case(args[1], data_remove_old_promo, new_remove_old_promo_path)
        os.mkdir(f'APM files/{args[1]}/Exports Results')
        os.mkdir(f'APM files/{args[1]}/Imports Results')
    except:
        print('Does not met arguments requirements, directory not created.')

