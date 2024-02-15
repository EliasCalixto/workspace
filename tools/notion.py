import requests
from tools.notion_credentials import NOTION_TOKEN, DATABASE_ID

headers = {
    "Authorization": "Bearer "+NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_pages(num_pages=None):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"

    get_all = num_pages is None
    page_size = 100 if get_all else num_pages

    payload = {"page_size": page_size}
    response = requests.post(url, json = payload, headers = headers)
    
    data = response.json()
    
    """
    
    import json
    
    with open('db.json', 'w', encoding = 'utf8') as f:
        json.dump(data, f, ensure_ascii = False , indent = 4)
        
    """
    
    results = data["results"]
    while data["has_more"] and get_all:
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        results.extend(data["results"])
        
    return results

def get_notion_summary():
    pages = get_pages()

    current_task = []

    for page in pages:
        if page['properties']['Status']['status']['name'] == 'Pending':
            current_task.append(page['properties']['Task']['title'][0]['text']['content'])
    
    return current_task


def get_notion_count():
    pages = get_pages()
    
    count = 0
    
    for page in pages:
        if page['properties']['Status']['status']['name'] == 'Pending':
            count += 1
    
    return count


if __name__ == '__main__':
    print(get_notion_summary())
    print(get_notion_count())
