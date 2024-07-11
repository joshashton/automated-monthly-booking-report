# Automated Monthly Booking Report
Collect and email a monthly property booking report to a client 


## Description

At the start of each month, collect the booking information from the previous month for all the client's properties then email the information back to the client

### Steps
- A script accesses the booking information from API of vacation rental software the user is using 
- The data is saved to a CSV for each property and then attached to an email and sent to the client
- A web server is set up on PythonAnywhere which allows cron-job.org to request a URL that runs the correct script. 

### Built with

- Python (3.10)
- Bottle: Python Web Framework (0.12)
- cron-job.org
