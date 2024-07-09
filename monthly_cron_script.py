#imports 
import requests
import json
import pandas as pd
import numpy as np 
import time
from datetime import datetime, timedelta, date

import sys
import os
import warnings
# Suppress FutureWarning messages
warnings.simplefilter(action='ignore', category=FutureWarning)

from dotenv import load_dotenv
import base64

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


# Exit if not 1st of the month
today = datetime.today()
if today.day != 9:
    sys.exit()


#get secrets from .env
load_dotenv()

api_key = os.getenv('API_UPLISTING')

sender_email = os.getenv('gmail')
receiver_email = os.getenv('emailss')
password = os.getenv('app_pass')

# Encode the API key using Base64
encoded_api_key = base64.b64encode(api_key.encode()).decode()

#functions
#make api call
def get_API_JSON(url):
    try:
        payload={}
        headers = {
            "Authorization": f"Basic {encoded_api_key}",
            "Content-Type": "application/json"
        }

        response = requests.request("GET", url, headers=headers, data=payload)
        JSONRes = response.json()
        return JSONRes
    except Exception as err:
        print(response)
        print(f"An unexpected error occurred: {err}")  # Any other unexpected errors
    return None


#get booking details for one id
def process_bookings_to_dataframe(bookings_data) -> pd.DataFrame:
    data_list = []
    for data in bookings_data['bookings']:
        booking = {
            "property_id": data['property_id'],
            "property_name": data['property_name'],
            "multi_unit_name": data['multi_unit_name'],
            "booked_at": data['booked_at'],
            "booking_id": data['id'],
            "check_in": data['check_in'],
            "arrival_time": data['arrival_time'],
            "check_out": data['check_out'],
            "departure_time": data['departure_time'],
            "number_of_nights": data['number_of_nights'],
            "channel_name": data['channel'],
            "booking_source": data['source'],
            "guest_name": data['guest_name'],
            "guest_email": data['guest_email'],
            "guest_phone": data['guest_phone'],
            "currency": data['currency'],
            "confirmation_code": data['external_reservation_id'],
            "number_of_guests": data['number_of_guests'],
            "accommodation_total": data['accomodation_total'],
            "cleaning_fee": data['cleaning_fee'],
            "extra_guest_charges": data['extra_guest_charges'],
            "extra_charges": data['extra_charges'],
            "discounts": data['discounts'],
            "booking_taxes": data['booking_taxes'],
            "payment_processing_fee": data['payment_processing_fee'],
            "commission": data['commission'],
            "commission_tax": data['commission_vat'],
            "total_payout": data['total_payout'],
            "cancellation_fee": data['cancellation_fee'],
            "accommodation_management_fee": data['accommodation_management_fee'],
            "cleaning_management_fee": data['cleaning_management_fee'],
            "total_management_fee": data['total_management_fee'],
            "note": data['note'],
            "status": data['status']
        }
        data_list.append(booking)
        #get pages number
    pages = bookings_data['meta']['total_pages']
    
    df = pd.DataFrame(data_list)
    return df, pages

def get_prev_month_dates():
    #get previous months start and end date
    last_day = datetime.today().replace(day=1) - timedelta(days=1)
    first_day = datetime.today().replace(day=1) - timedelta(days=last_day.day)
    # Format dates to '%Y-%m-%d'
    first_day = first_day.strftime('%Y-%m-%d')
    last_day = last_day.strftime('%Y-%m-%d')
    
    return first_day, last_day

def get_mulitpage(id, pages):
   
    bookings_list = []
    for x in range(1,pages):
        #between each API call
        time.sleep(1)
        url = f'https://connect.uplisting.io/bookings/{id}?from={date_from}&to={date_to}&page={x}'
        JSONRes = get_API_JSON(url)

        if JSONRes:
            data, _ = process_bookings_to_dataframe(JSONRes)
            bookings_list.append(data)
            #print(bookings_list)
            print("adding multipage")
        

    return bookings_list

def fetch_and_process_bookings(id_list):
    bookings_list = []
    for idx, id in enumerate(id_list):
        url = f'https://connect.uplisting.io/bookings/{id}?from={date_from}&to={date_to}&page=0'
        JSONRes = get_API_JSON(url)
        if JSONRes:
            data, pages = process_bookings_to_dataframe(JSONRes)
            bookings_list.append(data)
            print('adding')

            #mulitpage to search through
            if pages > 1:
                multipage_bookings = get_mulitpage(id, pages)
                for df in multipage_bookings:
                    bookings_list.append(df)
                    
        
        time.sleep(2)
            
    return pd.concat(bookings_list, ignore_index=True)



#Get booking information

date_from, date_to = get_prev_month_dates()

# Define the house groups and their IDs
house_groups = {
    'Whitchurch_Road': ['57536', '82576', '80553']
#    'Penarth_Road': ['78176', '91786', '78178', '78202'],
 #   'Corporation_Flat': ['78957', '78961', '78963', '78966', '82544'],
#    'Ninian_Road': ['80654', '84592', '84593', '82559'],
 #   'Fishguard': ['83909'],
#    'Najmi': ['98704']
}

# DataFrame to hold all bookings
all_bookings_df = pd.DataFrame()
#list of all csvs created to email
files_to_email = []

# Process and save bookings for each house group
for house_name, ids in house_groups.items():
    time.sleep(1)
    bookings_df = fetch_and_process_bookings(ids)

    #filter check in date for only dates in last month
    filtered_bookings_df = bookings_df[(bookings_df['check_in'] >= date_from) & (bookings_df['check_in'] <= date_to)]
    
    # Save to CSV
    csv_filename = f'{house_name}_monthlyBookings.csv'
    files_to_email.append(csv_filename)
    filtered_bookings_df.to_csv(csv_filename, index=False)
    
    print(f'Saved bookings for {house_name} to {csv_filename}')
    # Append to all_bookings_df
    all_bookings_df = pd.concat([all_bookings_df, bookings_df], ignore_index=True)



# Email

# Create a MIME multipart message
msg = MIMEMultipart()

# Attach each CSV file
if files_to_email:
    for csv_file in files_to_email:
        with open(csv_file, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={csv_file}",
            )
            msg.attach(part)


# Set up SMTP server connection
smtp_server = 'smtp.gmail.com'
smtp_port = 465  


# Compose the email message
msg['From'] = sender_email
msg['To'] = receiver_email
msg['Subject'] = f'Monthly Bookings Report ({date_from} - {date_to})'

# Send the email via SMTP server
try:
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(sender_email, password)
        server.send_message(msg)
        print("Email sent successfully.")
except Exception as e:
    print(f"Failed to send email. Error: {str(e)}")

