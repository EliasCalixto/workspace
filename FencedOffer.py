import os
from tools.caseInitializer import initCase
from BusinessModelConversion import data_to_json

export_comp_path = "Expedia Templates/BMC/BMC2/EXPORT Compensation Cloud Export.xlsx"
export_promo_path = "Expedia Templates/BMC/BMC2/EXPORT Promotion Export.xlsx"
export_PSNS_path = "Expedia Templates/BMC/BMC2/EXPORT PS&NS Export_Full.xlsx"
export_RPL_path = "Expedia Templates/BMC/BMC2/EXPORT RPL Cloud Export.xlsx"
export_RTRPClone_path = "Expedia Templates/BMC/BMC2/EXPORT RT&RP Cloud Export_Clone.xlsx"
import_compensation_path = "Expedia Templates/BMC/BMC2/IMPORT 1 Compensation Update.xlsx"
import_promo_path = "Expedia Templates/BMC/BMC2/IMPORT 2 Promotion Basic MOD Evergreen.xlsx"
import_RPL_path = "Expedia Templates/BMC/BMC2/IMPORT 4 RPL Cloud Create10%.xlsx"
import_rmv_stopsell = "Expedia Templates/BMC/BMC2/IMPORT 5 remove Stop-Sell.xlsx"
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

data_compensation_import = data_to_json(import_compensation_path)
new_compensationImport_path = "IMPORT 1 Compensation Update.xlsx"

data_promo_import = data_to_json(import_promo_path)
new_promoImport_path = "IMPORT 2 Promotion Basic MOD Evergreen.xlsx"

data_RPL_import = data_to_json(import_RPL_path)
new_RPLImport_path = "IMPORT 4 RPL Cloud Create10%.xlsx"

data_rmv_stopsell = data_to_json(import_rmv_stopsell)
new_rmv_stopsell_path = "IMPORT 5 remove Stop-Sell.xlsx"

data_remove_old_pkg = data_to_json(import_remove_old_pkg)
new_remove_old_pkg_path = "IMPORT remove old Packages.xlsx"

data_remove_old_promo = data_to_json(import_remove_old_promo)
new_remove_old_promo_path = "IMPORT remove old Promotions.xlsx"



if __name__ == "__main__":
    print('')
    caseNumber = input('Case: ')
   
    initCase(caseNumber, data_comp_export, new_comp_path)
    initCase(caseNumber, data_promo_export, new_promo_path)
    initCase(caseNumber, data_PSNS_export, new_PSNS_path)
    initCase(caseNumber, data_RPL_export, new_RPL_path)
    initCase(caseNumber, data_RTRPClone_export, new_RTRPClone_path)
    initCase(caseNumber, data_compensation_import, new_compensationImport_path)
    initCase(caseNumber, data_promo_import, new_promoImport_path)
    initCase(caseNumber, data_RPL_import, new_RPLImport_path)
    initCase(caseNumber, data_rmv_stopsell, new_rmv_stopsell_path)
    initCase(caseNumber, data_remove_old_pkg, new_remove_old_pkg_path)
    initCase(caseNumber, data_remove_old_promo, new_remove_old_promo_path)
    os.mkdir(f'APM files/{caseNumber}/Exports Results')
    os.mkdir(f'APM files/{caseNumber}/Imports Results')
        
    
    print('')
    print('Ready to work on case.')
    print('')   

