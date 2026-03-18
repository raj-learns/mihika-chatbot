import requests

def get_meaning(word : str):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return {
            "word": word,
            "meanings": []
        }
    
    data = response.json()
    meanings_list = []
    for item in data:
        for meaning in item["meanings"]:
            for definition in meaning["definitions"]:
                meanings_list.append(definition["definition"])
    meanings_list = meanings_list[:5]
    return {
        "word": word,
        "meanings": meanings_list
    }

