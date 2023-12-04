import pickle
import re
from random import randint
import bs4


def parse_stations():
    with open("stations.html", 'r', encoding='utf-8') as f:
        stations_html = f.read()

    stations_soup = bs4.BeautifulSoup(stations_html, 'html.parser')

    stations = set()

    for circle in stations_soup.find_all('circle'):
        stations.add((int(circle['x']), int(circle['y'])))

    with open('stations.pickle', 'wb') as f:
        pickle.dump(stations, f)


def parse_labels():
    with open("labels.html", 'r', encoding='utf-8') as f:
        labels_html = f.read()

    labels_soup = bs4.BeautifulSoup(labels_html, 'html.parser')

    stations_labeled = dict()

    for label in labels_soup.find_all('g'):
        station_data = dict()
        names = set()
        for tspan in label.find_all('tspan'):
            if tspan.text not in names:
                names.add((tspan.text + ("" if tspan.text[-1] == '-' else " ")).strip())
        station_data['name'] = "".join(names)
        station_data['svg'] = str(label)
        station_data['to'] = set()
        station_data['ways'] = dict()
        crd = (0, 0)
        for circle in label.find_all('circle'):
            crd = (int(circle['x']), int(circle['y']))
            if circle['fill'] == '#ffffff' or circle['fill'] == '#fff':
                continue
            station_data['col'] = circle['fill']
        stations_labeled[crd] = station_data

    with open('stationsLabeled.pickle', 'wb') as f:
        pickle.dump(stations_labeled, f)

def guess_point(point, stations, r = 10):
    res, d = None, None
    for i in range(-r, r+1):
        for j in range(-r,r+1):
            if stations.get((point[0] + i, point[1] + j)) is not None:
                if res is None or i**2 + j**2 < d:
                    res, d = tuple((point[0] + i, point[1] + j)), i**2 + j**2
    return res

def parse_lines():
    with open("lines.html", 'r', encoding='utf-8') as f:
        lines_html = f.read()

    with open("transfers.html", 'r', encoding='utf-8') as f:
        transfers_html = f.read()

    with open('stationsLabeled.pickle', 'rb') as f:
        stations_labeled = pickle.load(f)

    lines_soup = bs4.BeautifulSoup(lines_html, 'html.parser')

    for line in lines_soup.find_all('line'):
        if line['stroke'] == "#ffffff":
            continue
        p1 = guess_point(tuple((int(line['x1']), int(line['y1']))), stations_labeled)
        p2 = guess_point(tuple((int(line['x2']), int(line['y2']))), stations_labeled)
        if stations_labeled.get(p1) is not None and stations_labeled.get(p2) is not None and p2 != p1:
            if p2 not in stations_labeled[p1]['to']:
                stations_labeled[p1]['to'].add(p2)
                stations_labeled[p1]['ways'][p2] = {'svg': str(line), 'w': randint(3, 3)}
            if p1 not in stations_labeled[p2]['to']:
                stations_labeled[p2]['ways'][p1] = {'svg': str(line), 'w': randint(3, 3)}
                stations_labeled[p2]['to'].add(p1)

    pattern = r"[\d\.]+, [\d\.]+"

    for path in lines_soup.find_all('path'):
        if path['stroke'] == "#ffffff":
            continue
        points = [tuple(map(int, map(float, p.split(', ')))) for p in re.findall(pattern, path['d'])]
        p1 = guess_point(points[0], stations_labeled)
        p2 = guess_point(points[-1], stations_labeled)
        if stations_labeled.get(p1) is not None and stations_labeled.get(p2) is not None and p2 != p1:
            if p2 not in stations_labeled[p1]['to']:
                stations_labeled[p1]['to'].add(p2)
                stations_labeled[p1]['ways'][p2] = {'svg': str(path), 'w': randint(3,3)}
            if p1 not in stations_labeled[p2]['to']:
                stations_labeled[p2]['ways'][p1] = {'svg': str(path), 'w': randint(3,3)}
                stations_labeled[p2]['to'].add(p1)


    transfers_soup = bs4.BeautifulSoup(transfers_html, 'html.parser')

    for path in transfers_soup.find_all('path'):
        if path['stroke'] == "#ffffff":
            continue
        points = [tuple(map(int, map(float, p.split(', ')))) for p in re.findall(pattern, path['d'])]
        for i in range(len(points)):
            for j in range(i+1, len(points)):
                p1 = guess_point(points[i], stations_labeled)
                p2 = guess_point(points[j], stations_labeled)
                if stations_labeled.get(p1) is not None and stations_labeled.get(p2) is not None and p2 != p1:
                    if p2 not in stations_labeled[p1]['to']:
                        stations_labeled[p1]['to'].add(p2)
                        stations_labeled[p1]['ways'][p2] = {'svg': str(path), 'w': randint(3, 3)}
                    if p1 not in stations_labeled[p2]['to']:
                        stations_labeled[p2]['ways'][p1] = {'svg': str(path), 'w': randint(3, 3)}
                        stations_labeled[p2]['to'].add(p1)

    with open('stations_complete.pickle', 'wb') as f:
        pickle.dump(stations_labeled, f)

    for i, (crd, st) in enumerate(stations_labeled.items()):
        if st.get('col') is None:
            print(i, st.get('name'), st.get('col'))

if __name__ == '__main__':
    parse_labels()
    parse_lines()
