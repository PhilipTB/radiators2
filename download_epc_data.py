# doesn't work in Excel because of "URLError: <urlopen error Tunnel connection failed: 400 Bad Request>"
# error - presumed a security feature in the Excel cloud?
import urllib.request
from urllib.parse import urlencode
import pprint
import csv
import pandas as pd
import ast

def clean_value(value):
    # Remove leading and trailing whitespace and single quotes
    value = value.strip().strip("'")
    return value

def convert_to_data_frame(data_string):
    lines = data_string.strip().split('\n')
    header = [clean_value(value) for value in lines[0].split(',')]

    delim = '"'


    # Parse the data rows into a list of lists
    # its awkward as some values contains 'commas'
    # which are delimited by " around the whole value
    data = []
    for line in lines[1:]:
        print(line)
        row = []
        in_quotes = False
        current_value = []
        for char in line:
            if char == delim and not in_quotes:
                in_quotes = True
            elif char == delim and in_quotes:
                in_quotes = False
            elif char == ',' and not in_quotes:
                # End of value, add to row
                row.append(clean_value(''.join(current_value)))
                current_value = []
            else:
                current_value.append(char)

        row.append(clean_value(''.join(current_value)))
        data.append(row)

    return pd.DataFrame(data, columns=header)

def download_data(postcode):
    postcode = postcode.replace(" ", "")

    urghh = "TopSecretcGhpbGlwLmhhaWxlQHRyYW5zaXRpb25iYXRoLm9yZzo4MmExMzAxNzkyMDExZDcwZTAzYTcwZDQxN2QzYTE4MzM1YzM0MWI1"

    headers = {
        'Accept': 'text/csv',
        'Authorization': f'Basic {urghh}'
    }

    # Define base URL and query parameters separately
    base_url = 'https://epc.opendatacommunities.org/api/v1/domestic/search'
    query_params = {'postcode':postcode}

    # Encode query parameters
    encoded_params = urlencode(query_params)

    # Append parameters to the base URL
    full_url = f"{base_url}?{encoded_params}"


    # Now make request
    with urllib.request.urlopen(urllib.request.Request(full_url, headers=headers)) as response:
        response_body = response.read()
        data_string = response_body.decode()
        print("="*100)
    
        epcs = convert_to_data_frame(data_string)

    return epcs

pprint.pp(download_data('BA2 7UW'))
