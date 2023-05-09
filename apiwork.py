import requests
import json

url = 'https://www.googleapis.com/books/v1/volumes'
# isbn = '9788131520383'
# isbn = '9780786883561'
# isbn = '9781999579500'
# isbn = '9788131530603'
# isbn = '9780143453673'
def get_book_info(isbn):
  param = {
  
      'q': f'isbn:{isbn}'
  }
  req = requests.get(url, params=param)
  data = req.json()
  try:
    title = data['items'][0]['volumeInfo']['title']
  except:
    title = "NA"
  try: 
    author = data['items'][0]['volumeInfo']['authors'][0]
  except:
    author = 'NA'
  return {'title':title,'author':author}


