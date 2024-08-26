import requests
from bs4 import BeautifulSoup
from urllib.request import urlretrieve
import os


def download_kml():
    KML_url = 'https://sentinel.esa.int/web/sentinel/copernicus/sentinel-2/acquisition-plans'
    base_url = 'https://sentinel.esa.int'

    response = requests.get(KML_url)
    sentinel_types = ['sentinel-2a', 'sentinel-2b']

    for sentinel_type in sentinel_types:

        if response.status_code == 200:
            print('Responce ok! for', sentinel_type)

            html_content = BeautifulSoup(response.content, 'html.parser')
            elements = html_content.find_all(class_=sentinel_type)

            if elements:
                for element in elements:
                    link = element.find_all('a')  # find all links in sentinel 2a (or sentinel 2b) aquisition plans

                    for i in range(len(link)):
                        if link and 'href' in link[i].attrs:
                            file_url = link[i]['href']
                            link_text = link[i].get_text(strip=True)
                            print(link_text)
                            print('Link Found!', base_url + link[i]['href'], '\n')
                            file_name = os.path.basename(file_url) + '.kml'
                            file_url = base_url + file_url
                            urlretrieve(file_url, file_name)
                        else:
                            print('Link not Found!')
        else:
            print('Responce not ok for', sentinel_type)

    return 0

if __name__ == "__main__":

    download_kml()