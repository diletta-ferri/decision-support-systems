# =======================================
# IMPORT LIBRARIES
# =======================================

import csv
import json
import reverse_geocode as rg
import pycountry_convert as pc
from pycountry_convert import country_alpha2_to_continent_code
import xml.etree.ElementTree as ET
from datetime import datetime

# =======================================
# # DEFINITION OF FUNCTIONS
# =======================================

# Functions for handling GEOGRAPHY INFORMATION:

# Function to read the coordinates from a file 
def extract_coordinates(input_file):
    coordinates_set = set() # Store the coordinates in a set 
    
    with open(input_file, 'r', newline='') as file:
        csv_reader = csv.DictReader(file)
        
        # Scanning the columns of interest in the Csv (lat and lon), add them in the set
        for row in csv_reader:
            latitude = row['latitude']
            longitude = row['longitude']
            coordinates_set.add((latitude, longitude))
    
    return coordinates_set

# Function to retrieve geographic information(city, country etc.) based on coordinates using the reverse geocoding library
def get_geography_info(coordinates): 
    return rg.search(coordinates) 

# Function to retrieve continent information based on the country code (contained in the geographic information)
def map_country_to_continent(geography_info):
    for info in geography_info:
        country_code = info['country_code']
        continent_code = country_alpha2_to_continent_code(country_code) # Get continent code
        continent_name = pc.convert_continent_code_to_continent_name(continent_code) # Convert continent code to continent name

        # Assign continent code and name to the dictionary
        info['continent_code'] = continent_code
        info['continent_name'] = continent_name
    
    return geography_info  # returns the updated list (with added continent information)

def create_geography_csv(output_file, coordinate_set, geography_info):
    # Initialize a counter for geo_id
    geo_id_counter = 1

    with open(output_file, 'w', newline='') as output_csv:
        # Set the fieldnames for the CSV
        fieldnames = ['geo_id', 'latitude', 'longitude', 'city', 'country', 'country_code', 'continent_code', 'continent']

        csv_writer = csv.DictWriter(output_csv, fieldnames=fieldnames)
        csv_writer.writeheader()

        for coordinates, info in zip(coordinate_set, geography_info):
            row = {'geo_id': geo_id_counter,
                   'latitude': coordinates[0], 'longitude': coordinates[1],
                   'city': info.get('city', ''),
                   'country': info.get('country', ''),
                   'country_code': info.get('country_code', ''),
                   'continent_code': info.get('continent_code', ''),
                   'continent': info.get('continent_name', '')}
            csv_writer.writerow(row)
            geo_id_counter += 1 # Update the incremental geo_id

# GENERAL FUNCTIONS for other tables:

# Function to check if an ID exists and generate a new one if needed
def control_or_generate_id(dict_table, row_list):
    id = None # Initialize the ID to None
    # Loop through the dictionary items to check if the given row_list already exists
    for k,v in dict_table.items(): 
        if row_list == v:
            id = k
    # If the row_list is not present, add it and generate the new ID incrementally based on the current length of the dictionary
    if id == None: 
        new_key = len(dict_table) + 1 
        dict_table[new_key] = row_list 
        id = new_key
    return(id) # returns ID

# Function to create a dictionary mapping geo_id and latitude and longitude
def create_geo_mapping():
    geo_mapping = {}
    with open('geography.csv', 'r', newline='') as geo_csv:
        geo_reader = csv.DictReader(geo_csv)
        for row in geo_reader:
            latitude = row['latitude']
            longitude = row['longitude']
            geo_id = row['geo_id']
            geo_mapping[(latitude, longitude)] = geo_id
    return(geo_mapping)

# Function to create the .csv file from a dictionary
def create_csv(outputfile, header, data_dict):
    with open(outputfile, 'w', newline='') as fileoutput:
        writer = csv.writer(fileoutput)
        writer.writerow(header)
        for key in data_dict.keys():
            writer.writerow([key] + data_dict[key])

# =======================================
# DATE INFORMATION:
# =======================================

# Parse the XML date file
with open('dates.xml', 'r') as xml_file:
    tree = ET.parse(xml_file)
    root = tree.getroot()

# Initialize a list to store data rows
data_rows = []

# Loop through each 'row' element in the XML and extract 'date' and 'date_pk' elements
for row in root.findall('.//row'):
    date = row.find('date')
    date_pk = row.find('date_pk')
    
    # Check if both 'date' and 'date_pk' elements are present
    if date is not None and date_pk is not None:
        # Extract the date text and date_pk value
        date_text = date.text.split()[0]  # Take only the date part, ignoring the time
        date_pk = date_pk.text

        # Convert date_text to a datetime object to further manipulate it
        date = datetime.strptime(date_text, '%Y-%m-%d')
        #Extract various information about date
        extended_date = date.strftime("%d %B of %Y")
        year = date.year
        month = date.month
        day = date.day
        day_of_week = date.strftime('%A')
        quarter_of_year = ((month - 1) // 3 + 1)  

        # Create a dictionary representing the row and append it to the list
        data_rows.append({
            'date': date_text, 
            'date_id': date_pk, 
            'year': year, 
            'month': month, 
            'day': day, 
            'day_of_week': day_of_week, 
            'quarter': quarter_of_year, 
            'extended_date': extended_date
            })
    else: 
        # Print an error message if 'date' or 'date_pk' is missing in a row
        print("Elementi mancanti in una riga")
        break

# Write the extracted data to the date.csv file
with open('date.csv', 'w', newline='') as csvfile:
    fieldnames = ['date_id', 'date', 'day', 'month', 'year', 'day_of_week', 'quarter', 'extended_date']
    csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    csv_writer.writeheader()
    csv_writer.writerows(data_rows)

# =======================================
# APPLICATION OF THE FUNCTIONS TO THE DATA
# =======================================

# GEOGRAPHY INFORMATION:

coordinates = extract_coordinates('police.csv')
coordinates_list = list(coordinates) 
geography_info = get_geography_info(coordinates_list)
geography_info = map_country_to_continent(geography_info)

create_geography_csv('geography.csv', coordinates, geography_info)

geo_id_mapping=create_geo_mapping()

# OTHER TABLES:

# Open the JSON files and load them into dictionaries
F1 = json.load(open("dict_partecipant_age.json"))
F2 = json.load(open("dict_partecipant_type.json"))
F3 = json.load(open("dict_partecipant_status.json"))

# Create dictionaries for participants, guns, and custody
participants = {} 
guns = {}
custody = {}

# Create a set to store unique incident IDs
incidents = set()

# Open and read the 'Police.csv' file and create participant, guns, incidents, calculate grime_gravity e create custody
with open("Police.csv", mode='r', encoding='utf-8-sig', newline="") as filecsv:
    police_csv = csv.DictReader(filecsv,delimiter=",")

    for row in police_csv:
        # Generate/retrieve participant_id
        age_and_group = row['participant_age_group'].split()
        row_list_participants = [age_and_group[0], age_and_group[1],row['participant_gender'],row['participant_type'], row['participant_status']]
        participant_id = control_or_generate_id(participants,row_list_participants)
        
        # Generate/retrieve gun_id
        row_list_guns = [row['gun_stolen'],row['gun_type']]
        gun_id=control_or_generate_id(guns,row_list_guns)
        
        # Add incident_id to the set
        incidents.add(row["incident_id"])
        
        # Calculate crime_gravity index
        crime_gravity = int(F1[row["participant_age_group"]]) * int(F2[row["participant_type"]] * int(F3[row["participant_status"]]))
        
        # Retrieve geo_id from the mapping
        latitude = row['latitude']
        longitude = row['longitude']
        coordinates = (latitude, longitude)
        if coordinates in geo_id_mapping:
            geo_id = geo_id_mapping[coordinates]
        else:
            geo_id = 'N/A' 

        # Create the corresponding row in custody
        custody[row['custody_id']] = [participant_id, gun_id, geo_id, row['date_fk'], crime_gravity, row["incident_id"]]


# Definition of the headers and creation of the csv files for the tables gun, participant, custody 
header_participant = ['participant_id','age_group','age','gender','type','status']
header_gun = ['gun_id','is_stolen','gun_type']
header_custody = ['custody_id','participant_id','gun_id','geo_id','date_id','crime_gravity','incident_id']
create_csv('participant.csv',header_participant,participants)
create_csv('gun.csv',header_gun,guns)
create_csv('custody.csv',header_custody,custody)

# Create 'incidents.csv'
with open('incident.csv','w',newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['incident_id']) 
    for i in incidents:
        writer.writerow([i])

