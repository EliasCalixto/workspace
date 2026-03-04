import pandas as pd
import re

folder = '/Users/darkesthj/dev/family_search/metadata_DRR_tool'
file_name = 'metadata_Tacna.csv'
df_path = f'{folder}/{file_name}'

df = pd.read_csv(df_path, sep="|")
df = df.dropna(axis=1, how='all') # delete columns with all NaN values

df_copy = df.copy()

def std_archive_reference():
    for j,i in enumerate(df['archive_reference']):
        if '_' in i:
            new_text = i.replace('_',' ')
            df.loc[j,'archive_reference'] = new_text
        
    for j,i in enumerate(df['archive_reference']):
        if '- -' in i:
            new_text = i.replace('- -',' -')
            df.loc[j,'archive_reference'] = new_text
    
    for j,i in enumerate(df['archive_reference']):
        if 'Libro 1' in i:
            new_text = i.replace('Libro 1','')
            df.loc[j,'archive_reference'] = new_text
            
    for j,i in enumerate(df['archive_reference']):
        if 'Libro 2' in i:
            new_text = i.replace('Libro 2','')
            df.loc[j,'archive_reference'] = new_text
            
    for j,i in enumerate(df['archive_reference']):
        if 'Libro 3' in i:
            new_text = i.replace('Libro 3','')
            df.loc[j,'archive_reference'] = new_text
    
    for j,i in enumerate(df['archive_reference']):
        if 'Libro 4' in i:
            new_text = i.replace('Libro 4','')
            df.loc[j,'archive_reference'] = new_text

    for j,i in enumerate(df['archive_reference']):
        if 'Libro 5' in i:
            new_text = i.replace('Libro 5','')
            df.loc[j,'archive_reference'] = new_text

    for j,i in enumerate(df['archive_reference']):
        if 'Libro 36' in i:
            new_text = i.replace('Libro 36','')
            df.loc[j,'archive_reference'] = new_text

    for j,i in enumerate(df['archive_reference']):
        if 'Vol 1' in i:
            new_text = i.replace('Vol 1','')
            df.loc[j,'archive_reference'] = new_text

    for j,i in enumerate(df['archive_reference']):
        if 'Vol 2' in i:
            new_text = i.replace('Vol 2','')
            df.loc[j,'archive_reference'] = new_text
    
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 3' in i:
            new_text = i.replace('Vol 3','')
            df.loc[j,'archive_reference'] = new_text
            
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 4' in i:
            new_text = i.replace('Vol 4','')
            df.loc[j,'archive_reference'] = new_text
            
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 5' in i:
            new_text = i.replace('Vol 5','')
            df.loc[j,'archive_reference'] = new_text
      
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 6' in i:
            new_text = i.replace('Vol 6','')
            df.loc[j,'archive_reference'] = new_text     
     
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 7' in i:
            new_text = i.replace('Vol 7','')
            df.loc[j,'archive_reference'] = new_text
     
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 8' in i:
            new_text = i.replace('Vol 8','')
            df.loc[j,'archive_reference'] = new_text
     
    for j,i in enumerate(df['archive_reference']):
        if 'Vol 9' in i:
            new_text = i.replace('Vol 9','')
            df.loc[j,'archive_reference'] = new_text
              
    for j,i in enumerate(df['archive_reference']):
        if 'Libro 36' in i:
            new_text = i.replace('Libro 36','')
            df.loc[j,'archive_reference'] = new_text
            
    for j, i in enumerate(df['archive_reference']):
        if ',' in i:
            new_text = re.sub(r',(.*?)(?= - DGS)','', i)
            df.loc[j,'archive_reference'] = new_text

def std_record_title():
    for j,i in enumerate(df['record_title']):
        df.loc[j,'record_title'] = df.loc[j,'archive_reference']

def std_dates():
    df['dates'] = df['dates'].astype(str) # change the datatype for this column to str
    
    # wrong format dates (1234 - 5678)
    for j,i in enumerate(df['dates']):
        if len(str(i)) > 9:
            if i[0:4].isdigit() and i[-4:].isdigit():
                df.loc[j,'dates'] = f'{i[0:4]}/{i[-4:]}'
    
    # for less than 4 digit dates (123)
    for j,i in enumerate(df['dates']):
        if len(str(i)) < 4:
            df.loc[j,'dates'] = f''
    
    # for 4 digit dates (1985)
    for j,i in enumerate(df['dates']):
        if i.isdigit() and int(i) > 2025:
            df.loc[j,'dates'] = f''
        elif i.isdigit() and int(i) < 1200:
            df.loc[j,'dates'] = f''
        elif len(str(i)) == 4:
            df.loc[j,'dates'] = f'{str(i)}/{str(i)}'
    
    # for right format dates but wrong years (1985-2025)
    for j,i in enumerate(df['dates']):
        if i[0:4].isdigit() and int(i[0:4]) < 1500:
            df.loc[j,'dates'] = f''
        elif i[5:].isdigit() and int(i[5:]) > 2025:
            df.loc[j,'dates'] = f''
            
    # for bigger number first (1990-1985)
    for j,i in enumerate(df['dates']):
        if i[0:4].isdigit() and i[-4:].isdigit():
            if int(i[0:4]) > int(i[5:]):
                df.loc[j,'dates'] = f''
  
def std_locality():
    df['locality'] = df['locality'].astype(str) # change the datatype for this column to str

    # for localities with +5 levels
    for j,i in enumerate(df['locality']):
        list_locality = i.split(',')
        try:
            list_locality = list_locality[0:2]+list_locality[-3:]
        except:
            list_locality = list_locality
        
        locality_text = ''
        for k in list_locality:
            locality_text += f'{k},'
        locality_text = locality_text.rstrip(',')
        
        df.loc[j,'locality'] = locality_text
        
    for j,i in enumerate(df['locality']):
        if '  ' in i:
            new_text = i.replace('  ',' ')
            df.loc[j,'locality'] = new_text
        
def std_record_type():
    # matrimonio
    # bautizo
    # defuncion
    # nacimiento
    # confirmacion
    
    df['record_type'] = df['record_type'].str.lower()
    
    for j,i in enumerate(df['record_type']):
        # for matrimonio
        if 'matri' in i:
            df.loc[j,'record_type'] = 'matrimonio'
        elif 'marria' in i:
            df.loc[j,'record_type'] = 'matrimonio'
        elif 'weddin' in i:
            df.loc[j,'record_type'] = 'matrimonio'
        # for bautizo
        elif 'bau' in i:
            df.loc[j,'record_type'] = 'bautizo'
        # for defuncion
        elif 'defu' in i:
            df.loc[j,'record_type'] = 'defunción'
        # for nacimiento
        elif 'naci' in i:
            df.loc[j, 'record_type'] = 'nacimiento'
        # for confirmacion
        elif 'confirm' in i:
            df.loc[j, 'record_type'] = 'confirmación'
            
    for j,i in enumerate(df['record_type']):
        df.loc[j,'record_type'] = i.capitalize()
            
def std_volume():
    df['volume'] = df['volume'].astype(str)
    
    for j,i in enumerate(df['volume']):
        if i == 'S/N' or i =='SN' or i == ' -' or i == '- ' or i == '-' or i == ' ' or i == '' or i == 'x' or i == None or i == 'nan' or i == 'N/A' or i == 'N/A ':
            df.loc[j,'volume'] = ''
        elif len(str(i)) > 9:
            df.loc[j,'volume'] = ''
        elif 'libro ' in i:
            i.replace('libro ','')
        elif 'Libro ' in i:
            new_text = i.replace('Libro ','')
            df.loc[j,'volume'] = new_text
        elif 'volumen ' in i:
            new_text = i.replace('volumen ','')
            df.loc[j,'volume'] = new_text
        elif 'vol ' in i:
            new_text = i.replace('vol ','')
            df.loc[j,'volume'] = new_text
        elif 'Vol ' in i:
            new_text = i.replace('Vol ','')
            df.loc[j,'volume'] = new_text
        elif 'Vol' in i:
            new_text = i.replace('Vol','')
            df.loc[j,'volume'] = new_text
        elif 'vol' in i:
            new_text = i.replace('vol','')
            df.loc[j,'volume'] = new_text
        elif 'volumen' in i:
            new_text = i.replace('volumen','')
            df.loc[j,'volume'] = new_text
        elif 'libro' in i:
            new_text = i.replace('libro','')
            df.loc[j,'volume'] = new_text
        elif 'Libro' in i:
            new_text = i.replace('Libro','')
            df.loc[j,'volume'] = new_text
        
    for j,i in enumerate(df['volume']):
        if ' ' in i:
            new_text = i.replace(' ','')
            df.loc[j,'volume'] = new_text
            
    for j,i in enumerate(df['volume']):
        if '-' in i:
            position = i.index('-')
            first_num = i[0:position]
            second_num = i[position+1:]
            try:
                if int(first_num) > int(second_num):
                    df.loc[j,'volume'] = f'{second_num}-{first_num}'
            except:
                pass
            
    for j,i in enumerate(df['volume']):
        try:
            if i.index('0') == 0:
                new_text = i.replace('0','')
                df.loc[j,'volume'] = new_text
        except:
            pass

    for j,i in enumerate(df['volume']):
        if '.' in i:
            new_text = i.replace('.','')
            df.loc[j,'volume'] = new_text

def std_event_type():
    for j,i in enumerate(df['record_type']):
        df.loc[j,'event_type'] = i

# test function
def test(col):
    test_df = pd.concat([df_copy[col],df[col]], axis=1)
    test_df.columns = ['old_values','new_values']
    print(test_df)

# creation of new .csv file
def csv_creation():
    destination_folder = '/Users/darkesthj/dev/family_search/metadata_DRR_tool'
    new_file_name = f'std_{file_name}'
    
    df.to_csv(f'{destination_folder}/{new_file_name}', sep='|', index=False)

if __name__ == '__main__':
    std_archive_reference()
    std_record_title()
    std_dates()
    # std_locality()
    std_record_type()
    std_volume()
    std_event_type()

    test('record_title')
    csv_creation()
