#Use Flask to create your routes.
import numpy as np

import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurements = Base.classes.measurement
Stations = Base.classes.station

# Flask Setup
app = Flask(__name__)

#Routes Setup
 # home page
@app.route("/")
def home_page():
    return (
        f"Welcome to the Climate App API!<br/>"
        f"<br/>"
        f"<br/>"         
        f"Available Routes:<br/>"
        f"<br/>"
        f"/api/v1.0/precipitation<br/>"
        f" - precipitation returns a list of dates and recorded precipitation values at all stations for the last year in the database <br/>"
        f"<br/>"      
        f"/api/v1.0/stations<br/>"
        f" - stations returns details of all weather stations <br/>"
        f"<br/>"
        f"/api/v1.0/tobs<br/>"
        f" - tobs returns temperature observations of the most active station for the last year in the database <br/>"       
        f"<br/>"
        f"/api/v1.0/start<br/>"
        f" - start returns the minimum temperature, the average temperature, and the max temperature for all dates greater than and equal to the given start date <br/>"
        f" - to use start pass your start date in the url in yyyy-mm-dd format, like so: /api/v1.0/2017-01-27 <br/>"
        f"<br/>"
        f"/api/v1.0/start/end<br/>"
        f" - start/end returns the minimum temperature, the average temperature, and the max temperature for dates between the given start and end date inclusive <br/>"
                f" - to use start/end pass your start and end dates in the url in yyyy-mm-dd format, like so: /api/v1.0/2017-01-27/2017-02-10 <br/>"
    )

 # precipitation 
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    #   finding the last data point in the database
    latest_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    #   converting it to the datetime object
    latest_date_obj = dt.datetime.strptime(latest_date[0], '%Y-%m-%d').date()
    #   finding a date 1 year ago from last date in the dataset
    year_ago = latest_date_obj - dt.timedelta(days=365)
    
    # Query the dates and precipitation records
    prec_results = session.query(Measurements.date, Measurements.prcp).filter(Measurements.date >= year_ago).all()
    session.close()

    # Convert list of tuples into normal lists
    dates_list = [result[0] for result in prec_results]
    prec_list = [result[1] for result in prec_results]

    # Convert lists into dictionary
    precipitation = dict(zip(dates_list, prec_list))

    return jsonify(precipitation)

 # stations
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
     # Query the stations' details   
    stations_results = session.query(Stations.station, Stations.name, Stations.latitude, Stations.longitude, Stations.elevation).all()
    session.close()

    # Create a list of dictionaries with stations' details
    stations = []
    for station, name, latitude, longitude, elevation in stations_results:
        stations_dict = {}
        stations_dict["ID"] = station
        stations_dict["name"] = name
        stations_dict["latitude"] = latitude
        stations_dict["longitude"] = longitude
        stations_dict["elevation"] = elevation   
        stations.append(stations_dict)

    return jsonify(stations)

 # tobs
@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)
    #   finding the last data point in the database
    latest_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    #   converting it to the datetime object
    latest_date_obj = dt.datetime.strptime(latest_date[0], '%Y-%m-%d').date()
    #   finding a date 1 year ago from last date in the dataset
    year_ago = latest_date_obj - dt.timedelta(days=365)
    
    # Query the dates and temperature observations of the most active station for the last year of data
    last_12_months_tobs = session.query(Measurements.station, Measurements.date, Measurements.tobs).filter(Measurements.station == "USC00519281").filter(Measurements.date >= year_ago).all()
    session.close()

    # Create a list of temperature observations for the previous year
    tobs_list = []

    for record in last_12_months_tobs:
        tobs_list.append(record[2])

    return jsonify(tobs_list)

 # start date
@app.route("/api/v1.0/<start>")
def start_date(start):
    session = Session(engine)
    start_date = start

    # Query all dates to check if selected date is in range
    check_date_test = list(np.ravel(session.query(Measurements.date).all()))

    if start_date not in check_date_test:
        # return error if date not found
        session.close()
        return jsonify({"error": f"Date {start_date} not found. Make sure the date is in yyyy-mm-dd format."}), 404
    else:
        # Query the min, avg and max temperature for all dates greater than and equal to the given start date
        start_date_results = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).filter(Measurements.date >= start_date).all()
        session.close()

        # Create a list containing dictionary with temperature details
        start_date_list = []
        for record in start_date_results:
            start_date_dict = {}
            start_date_dict["selected date"] = start_date
            start_date_dict["tmin"] = record[0]
            start_date_dict["tavg"] = round(record[1],1)
            start_date_dict["tmax"] = record[2]
            start_date_list.append(start_date_dict)

        return jsonify(start_date_list)       

 # start and end date
@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end):
    session = Session(engine)
    
    start_date = start
    end_date = end

    # Query all dates to check if selected date is in range
    check_date_test = list(np.ravel(session.query(Measurements.date).all()))

    if start_date not in check_date_test:
        # return error if date not found
        session.close()
        return jsonify({"error": f"Start date {start_date} not found. Make sure the date is in yyyy-mm-dd format."}), 404
    
    elif end_date not in check_date_test:
        # return error if date not found
        session.close()
        return jsonify({"error": f"End date {end_date} not found. Make sure the date is in yyyy-mm-dd format."}), 404

    else:
        # Query the min, avg and max temperature for dates between the given start and end date
        start_end_date_results = session.query(func.min(Measurements.tobs), func.avg(Measurements.tobs), func.max(Measurements.tobs)).filter(Measurements.date >= start_date).filter(Measurements.date <= end_date).all()
        session.close()

        # Create a list containing dictionary with temperature details
        start_end_date_list = []
        for record in start_end_date_results:
            start_end_date_dict = {}
            start_end_date_dict["selected start date"] = start_date
            start_end_date_dict["selected end date"] = end_date        
            start_end_date_dict["tmin"] = record[0]
            start_end_date_dict["tavg"] = round(record[1],1)
            start_end_date_dict["tmax"] = record[2]
            start_end_date_list.append(start_end_date_dict)

        return jsonify(start_end_date_list)

if __name__ == '__main__':
    app.run(debug=True)