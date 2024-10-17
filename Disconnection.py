import os
import sys
import pandas as pd
from tools.caseInitializer import init_case


EQCexportPath = 'EXPORT 4 EQC template.xlsx'
dataEQCexport = {
    'Hotel ID': ['']
}
EPCexportPath = 'EXPORT 3 EPC template.xlsx'
dataEPCexport = {
    'Hotel ID': ['']
}
PSandNSexportPath = 'EXPORT 2 PS&NS template.xlsx'
dataPSNSexport = {
    'Hotel ID': [''],
    'EC Agency': [''],
    'Ignore EC Agency': [''],
    'Partner Code': [''],
    'Responder ID': [''],
    'Chain Code': [''],
    'Brand Code': [''],
    'Hotel Code': [''],
    'Property Name': [''],
    'Address': [''],
    'City Name': [''],
    'Country Code': [''],
    'Stop Sell Property': [''],
    'Stop Sell Reason': [''],
    'Projected Stop Sell End Date': [''],
    'Hotel Business Model': [''],
    'Preferred Business Model': [''],
    'Pricing Model': [''],
    'Rate Acquisition Type': [''],
    'Rates Inclusive of Taxes': [''],
    'Rates Inclusive of Fees': [''],
    'Currency Code': [''],
    'Market Manager Email': [''],
    'LOS Extension Enabled': [''],
    'OBP Child Pricing Logic': [''],
    'Vendor ID': [''],
    'Expedia Service Fees': [''],
    'HC Commissions Charged for Taxes': [''],
    'HC Commissions Charged for Fees': [''],
    'HC Commissions Charged for Cancellations': [''],
    'EC Commissions Charged for Taxes': [''],
    'EC Commissions Charged for Fees': [''],
    'EFR Settings': [''],
    'Group Recon Enabled': [''],
    'Maximum Product Count': [''],
    'EVC Enabled': [''],
    'Exclude From Package': [''],
    'Package Multiple Property Allowed': [''],
    'Package Upgrade Allower': [''],
    'TIDS Code': [''],
    'Distributor ID': [''],
    'Segment': [''],
    'SegmentPotential': [''],
    'Inventory Auto-Renewal': [''],
    'Hotel ARI Enabled': [''],
    'Hotel EQC Enabled': [''],
    'Rate Plan Linkage': [''],
    'Default Min LOS': [''],
    'Default Max LOS': [''],
    'Default Cut Off Days': [''],
    'LOS Restriction Type': [''],
    'Rate Plan Inventory Cap': [''],
    'Allowed Age Categories': [''],
    'Check In Age': [''],
    'Cancellation Time': [''],
    'Cut Off Time': [''],
    'Cut Off Day': [''],
    'Time Zone': [''],
    'Property Out of Sync': [''],
    'Eligible for EVC@TOB': [''],
    'Sync Booking Enabled': [''],
    'Primary Notification Method': [''],
    'Secondary Notification Method': [''],
    'Include Guest Contact Info': [''],
    'Rooming List Option': [''],
    'Report Net Rates': [''],
    'Email Address': [''],
    'Fax Country Code': [''],
    'Fax Area Code': [''],
    'Fax Number': [''],
    'Additional Notification Email Address': [''],
    'Additional Notification Fax Country Code': [''],
    'Additional Notification Fax Area Code': [''],
    'Additional Notification Fax Number': [''],
    'Opt In HC SCA': [''], 
    'Same Day Bookings Without Credit Card': [''],
    'Inventory Threshold Same Day Bookings Without Credit Card': [''],
    'Next Day Bookings Without Credit Card': [''],
    'Inventory Threshold Next Day Bookings Without Credit Card': [''],
    'Member Only Deal Stack Enabled': [''],
    'Member Only Deal Stack Percentage': [''],
    'Member Only Deal Stack Negotiated': [''],
    'Support Stack Promotions': ['']
}
RTandRPexportPath = 'EXPORT 1 RoomType&RatePlan template.xlsx'
dataRTRPexport = {
    'Hotel ID': [''],
    'Partner Code': [''],
    'Responder ID': [''],
    'Chain Code': [''], 
    'Brand Code': [''],
    'Hotel Code': [''],
    'City Name': [''],
    'Country Code': [''],
    'Rate Acquisition Type': [''],
    'Pricing Model': [''],
    'Hotel Business Model': [''],
    'Currency Code': [''],
    'Hotel ARI Enabled': [''],
    'Hotel EQC Enabled': [''],
    'Check In Age': [''],
    'Property Cancellation Time': [''],
    'Property Name': [''],
    'Property Status': [''],
    'Room Type ID': [''],
    'Room Type Code': [''],
    'Room Type Status': [''],
    'ARI Room Type': [''],
    'Smoking': [''],
    'Number of Bedrooms - Individual Rooms': [''],
    'Number of Living Rooms - Individual Rooms': [''],
    'Number of Bathrooms - Individual Rooms': [''],
    'Room Out Of Sync': [''],
    'Room Attributes': [''],
    'Recommended Occupancy Total': [''],
    'Recommended Occupancy Adults': [''],
    'Recommended Occupancy Children': [''],
    'Max Occupancy': [''],
    'Max Adults': [''],
    'Max Children': [''],
    'OverrideReason': [''],
    'Room Type Name': [''],
    'RNS Room Type': [''],
    'RNS Quality': [''],
    'RNS Smoking Pref': [''],
    'RNS Accessibility': [''],
    'RNS View': [''],
    'RNS Feature Amenity': [''],
    'RNS Area': [''],
    'RNS Bedroom': [''],
    'RNS Bed Type': [''],
    'RNS Custom Label': [''],
    'RNS Brand Attribute': [''],
    'RNS Other Room Info': [''],
    'RNS Flag': [''],
    'Min Age Adults': [''],
    'Min Age Children': [''],
    'Min Age Infants': [''],
    'Room Tax Start Date': [''],
    'Room Tax End Date': [''],
    'Room Tax Amount': [''],
    'BeddingOption1': [''],
    'BeddingOption2': [''],
    'ExtraBedding': [''],
    'Rate Plan ID': [''],
    'Rate Plan Name': [''],
    'Rate Plan Type': [''],
    'Business Model': [''],
    'Rate Plan Status': [''],
    'Rate Plan Pricing Model': [''],
    'People Included In Base Rate': [''],
    'Expedia Collect Rate Plan Code': [''],
    'Hotel Collect Rate Plan Code': [''],
    'Special Discount Percent': [''],
    'Deposit Required': [''],
    'ARI Rate Plan': [''],
    'Change to Email Notification': [''],
    'Show Rate Plan Name': [''],
    'Rate Plan Includes Significant Value': [''],
    'Waive Taxes Enabled': [''],
    'LOS': [''],
    'DOA': [''],
    'RatePlan Out Of Sync': [''],
    'Value Add 1': [''],
    'Value Add 2': [''],
    'Value Add 3': [''],
    'Value Add 4': [''],
    'Value Add 5': [''],
    'Value Add 6': [''],
    'All Value Adds	Cancellation Policy Name': [''],
    'Non Refundable': [''],
    'Tier 1 Penalty': [''],
    'Tier 2 Ending Hours': [''],
    'Tier 2 Penalty': [''],
    'Tier 3 Ending Hours': [''],
    'Tier 3 Penalty': [''],
    'NRF Stay-Through Restrictions': [''],
    'FeeSet Name': [''],
    'Extra Adult Cost Index 1': [''],
    'Extra Adult Cost Index 2': [''],
    'Extra Adult Cost Index 3': [''],
    'Extra Adult Cost Index 4': [''],
    'Extra Child Cost Index 1': [''],
    'Extra Child Cost Index 2': [''],
    'Extra Infant Cost Index 1': [''],
    'Extra Adult Price Index 1': [''],
    'Extra Adult Price Index 2': [''],
    'Extra Adult Price Index 3': [''],
    'Extra Adult Price Index 4': [''],
    'Extra Child Price Index 1': [''],
    'Extra Child Price Index 2': [''],
    'Extra Infant Price Index 1': [''],
    'Additional Extra Person Fees': [''],
    'Service Charges': [''],
    'Expedia Collect Compensation Name': [''],
    'Expedia Collect Compensation Percent': [''],
    'EC Compensation DOW Start Date': [''],
    'EC Compensation DOW End Date': [''],
    'EC Compensation DOW Pattern': [''],
    'EC Compensation DOW Percent': [''],
    'Hotel Collect Compensation Name': [''],
    'Hotel Collect Compensation Percent': [''],
    'HC Compensation DOW Start Date': [''],
    'HC Compensation DOW End Date': [''],
    'HC Compensation DOW Pattern': [''],
    'HC Compensation DOW Percent': [''],
    'Min EC Compensation Amount': [''],
    'Min Advance Booking Days': [''],
    'Max Advance Booking Days': [''],
    'Min Length Of Stay': [''],
    'Max Length Of Stay': [''],
    'Booking Start Date': [''],
    'Booking End Date': [''],
    'Travel Start Date': [''],
    'Travel End Date': [''],
    'Channels': [''],
    'Channel Restrictions': [''],
    'Referring Channels': [''],
    'Referring Channel Restrictions': [''],
    'Demand Channel Switch': [''],
    'Demand Channels': [''],
    'Mobile Users Only': [''],
    'Parent Rate Plan ID': [''],
    'Rates Linked': [''],
    'Restrictions Linked': [''],
    'Mapping for Avail Rate': [''],
    'Mapping for EC Booking': [''],
    'Mapping for HC Booking': ['']
}


PSandNSimportPath = 'IMPORT 1 PS&NS - deactivation.xlsx'
dataPSNSimport = {
    'Action Type': ['Update'],
    'SF ID': [''],
    'Hotel ID': [''],
    'Stop Sell Property': ['Yes'],
    'Stop Sell Reason': ['Direct Contract to be deactivated'],
    'Projected Stop Sell End Date': ['06/06/2079'],
}
EPCimportPath = 'IMPORT 2 EPC - deactivation.xlsx'
dataEPCimport = {
    'SF ID': [''],
    'Hotel ID': [''],
    'Account User Name': [''],
    'Account Email Address': [''],
    'Account Security Level': [''],
    'Account TUID': [''],
    'Action Type': ['detach']
}
RTandRPimportPath = 'IMPORT 3 Room Type Rate Plan - deactivation.xlsx'
dataRTRPimport = {
    'Action Type': ['Update'],
    'SF ID': [''],
    'Hotel ID': [''],
    'Room Type ID': [''],
    'Room Type Code': [''],
    'Rate Plan ID': [''],
    'Rate Plan Name': [''],
    'Expedia Collect Rate Plan Code': [''],
    'Hotel Collect Rate Plan Code': [''],
    'Rate Plan Status': ['Inactive']
}
EQCimportPath = 'IMPORT 4 EQC - deactivation.xlsx'
dataEQCimport = {
    'Action Type': ['delete'],
    'SF ID': [''],
    'Hotel ID': [''],
    'Rollout Type': [''],
    'Partner System ID': [''],
    'Partner System Name': [''],
    'Send Email Notifications': ['Yes'],
    'Email AddrLst': ['']
}

if __name__ == "__main__":
    args = []

    for i,arg in enumerate(sys.argv):
        args.append(arg)

    if len(args) == 2:
        init_case(args[1], dataEQCexport,EQCexportPath)
        init_case(args[1], dataEPCexport,EPCexportPath)
        init_case(args[1], dataPSNSexport, PSandNSexportPath)
        init_case(args[1], dataRTRPexport, RTandRPexportPath)

        init_case(args[1], dataPSNSimport, PSandNSimportPath)
        init_case(args[1], dataEPCimport, EPCimportPath)
        init_case(args[1], dataRTRPimport, RTandRPimportPath)
        init_case(args[1], dataEQCimport, EQCimportPath)

        os.mkdir(f'APM files/{args[1]}/Exports Results')
        os.mkdir(f'APM files/{args[1]}/Imports Results')

        #Create ManagedBy File
        dataCsv = {
            'Account ID': [],
            'Managed by': []
        }

        # Create a DataFrame from the data
        dfCsv = pd.DataFrame(dataCsv)
        # Specify the file name and path
        file_pathCsv = f'APM files/{args[1]}/{args[1]} UpdateManagedBy.csv'
        # Write the DataFrame to and Excel file
        dfCsv.to_csv(file_pathCsv, index=False)
        #print(f"ManagedBy.csv file has been created.")

    elif len(args) == 3:
        dataEQCexport['Hotel ID'] = [f'{args[2]}']
        dataEPCexport['Hotel ID'] = [f'{args[2]}']
        dataPSNSexport['Hotel ID'] = [f'{args[2]}']
        dataRTRPexport['Hotel ID'] = [f'{args[2]}']
        dataPSNSimport['Hotel ID'] = [f'{args[2]}']
        dataEPCimport['Hotel ID'] = [f'{args[2]}']
        dataRTRPimport['Hotel ID'] = [f'{args[2]}']
        dataEQCimport['Hotel ID'] = [f'{args[2]}']

        init_case(args[1], dataEQCexport,EQCexportPath)
        init_case(args[1], dataEPCexport,EPCexportPath)
        init_case(args[1], dataPSNSexport, PSandNSexportPath)
        init_case(args[1], dataRTRPexport, RTandRPexportPath)

        init_case(args[1], dataPSNSimport, PSandNSimportPath)
        init_case(args[1], dataEPCimport, EPCimportPath)
        init_case(args[1], dataRTRPimport, RTandRPimportPath)
        init_case(args[1], dataEQCimport, EQCimportPath)

        os.mkdir(f'APM files/{args[1]}/Exports Results')
        os.mkdir(f'APM files/{args[1]}/Imports Results')

    else:
        print('Does not met arguments requirements, directory not created.')

