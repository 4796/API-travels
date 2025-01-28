import googlemaps
from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import datetime


app = Flask(__name__)


# Google Maps API ključ  RAPIDAPI_KEY   su potrebni kako bi radilo
gmaps = googlemaps.Client(key=GMAPS_API_KEY)

# Ruta za prikaz forme
@app.route('/')
def home():
    return render_template('index.html')

# Ruta za obradu podataka iz forme i generisanje itinerera
@app.route('/submit', methods=['POST'])
def submit():
    try:
        start = request.form['start']
        destination = request.form['destination']
        budget = float(request.form['budget'])
        duration = int(request.form['duration'])

        # Validacija podataka
        if not start or not destination:
            flash("Starting location and destination cannot be empty.")
            return redirect(url_for('home'))

        if budget <= 0:
            flash("Budget must be greater than 0.")
            return redirect(url_for('home'))

        if duration <= 0:
            flash("Duration must be greater than 0.")
            return redirect(url_for('home'))

        # Generisanje rute preko Google Maps API-ja
        route_info = get_route_info(start, destination)
        if not route_info:
            flash("Could not retrieve route information. Please try again.")
            return redirect(url_for('home'))

        hotels = get_hotels(destination, str(budget), duration)
        if not hotels:
            flash("No hotels found for the selected destination.")
            hotels = []
        # Prikaz rezultata
        return render_template('itinerary.html',start=start,destination=destination,budget=budget,duration=duration,route_info=route_info,hotels=hotels)
    except ValueError:
        flash("Please enter valid numeric values for budget and duration.")
        return redirect(url_for('home'))

def get_hotels(destination, price, days):
    url1="https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
    url2 = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"

    querystring1 = {
        "query": destination
    }

#querystring = {"dest_id":"-553173","dest_type":"city",,"page_number":"0","include_adjacency":"true","categories_filter_ids":"class::2,class::4,free_cancellation::1"}

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "booking-com15.p.rapidapi.com"
       #
        #booking-com.p.rapidapi.com

    }
    response1 = requests.get(url1, headers=headers, params=querystring1)
    if response1.status_code == 200:
        x = datetime.datetime.now()
        danas=x.strftime("%Y-%m-%d")
        x2 = x + datetime.timedelta(days=int(days))
        kraj=x2.strftime("%Y-%m-%d")
        data = response1.json()
        data=data.get("data")
        #jedna lista sadrzi podatke o id dela grada a drugi o tipu dela grada
        #sada sa ove dve liste moze da se pretrazi za svaki par
        #da dobijem jednu listu hotela iz tog dela grada
        ids=list()
        types=list()
        for d in data:
            ids.append(d.get("dest_id"))
            types.append(d.get("search_type"))
        recnik = dict(zip(ids, types))
        for id in ids:

            querystring2 = {
                "dest_id": id,
                "search_type": recnik[id],
                "arrival_date": danas,
                "departure_date": kraj,
                "adults": "1",
                "units": "metric",
                "room_qty": "1",
                "price_max": price,
                "currency_code": "EUR"
            }
            response2 = requests.get(url2, headers=headers, params=querystring2)
            if response2.status_code == 200:
                data = response2.json()
                data=data.get("data")
                hoteli=data.get("hotels")
                hoteli2=list()
                for h in hoteli:
                    if float(h.get("property").get("priceBreakdown").get("grossPrice").get("value"))<float(price):
                        hoteli2.append(h)
                return hoteli2



            else:
                print(f"Error: {response2.status_code}, {response2.text}")
                return None
    else:
        print(f"Error: {response1.status_code}, {response1.text}")
        return None


# Funkcija za dobijanje informacija o ruti
def get_route_info(start, destination):
    try:
        directions_result = gmaps.directions(start, destination, mode="driving")
        if directions_result:
            route = directions_result[0]['legs'][0]  # Uzimamo prvu rutu
            distance = route['distance']['text']
            duration = route['duration']['text']
            return {"distance": distance, "duration": duration}
    except Exception as e:
        print(f"Error with Google Maps API: {e}")
    return None





if __name__ == '__main__':
    app.run(debug=True, port=8765)
