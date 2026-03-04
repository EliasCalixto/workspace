import pandas as pd


folder = '/Users/darkesthj/dev/family_search/metadata_DRR_tool/updated'
file_name = 'std_metadata_Tacna_fromDB.csv'
df_path = f'{folder}/{file_name}'

df = pd.read_csv(df_path, sep="|")
df = df.dropna(axis=1, how='all') # delete columns with all NaN values

df_copy = df.copy()

def remove_quotes():
    for i in df:
        for j in df[i]:
            if '"' in j:
                new_text = j.replace('"','')
                df.loc[j,i] = new_text
        
def csv_creation():
    destination_folder = '/Users/darkesthj/dev/family_search/metadata_DRR_tool/updated'
    new_file_name = f'{file_name}'
    
    df.to_csv(f'{destination_folder}/{new_file_name}', sep='|', index=False)

if __name__ == "__main__":
    remove_quotes()
    csv_creation()