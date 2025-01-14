#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Oct 31 21:37:40 2023

@author: alyafaraht
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import imutils
import cv2
import pandas as pd
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from fractions import Fraction
import osmnx as ox

# Define the folder containing the images
#image_folder_L = "/Users/alyafaraht/Downloads/yes/"

# Function to extract GPS data from an image
def fraction_to_decimal(fraction):
    return float(fraction.numerator) / float(fraction.denominator)

def extract_gps(image_loc):
    img = Image.open(image_loc)
    exif_data = img._getexif()
    if exif_data is not None:
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'GPSInfo':
                gps_info = {}
                for subtag, subvalue in value.items():
                    subtag_name = GPSTAGS.get(subtag, subtag)
                    gps_info[subtag_name] = subvalue
                longitude = gps_info.get('GPSLongitude', None)
                latitude = gps_info.get('GPSLatitude', None)
                if latitude and longitude:
                    lon_deg = fraction_to_decimal(longitude[0])
                    lon_min = fraction_to_decimal(longitude[1])
                    lon_sec = fraction_to_decimal(longitude[2])
                    lon_dir = gps_info.get('GPSLongitudeRef', 'E')
                    lat_deg = fraction_to_decimal(latitude[0])
                    lat_min = fraction_to_decimal(latitude[1])
                    lat_sec = fraction_to_decimal(latitude[2])
                    lat_dir = gps_info.get('GPSLatitudeRef', 'N')
                    longitude_decimal = lon_deg + lon_min / 60 + lon_sec / 3600
                    if lon_dir == 'W':
                        longitude_decimal = -longitude_decimal
                    latitude_decimal = lat_deg + lat_min / 60 + lat_sec / 3600
                    if lat_dir == 'S':
                        latitude_decimal = -latitude_decimal
    data_gps = {'Longitude': [longitude_decimal], 'Latitude': [latitude_decimal]}
    df_gps = pd.DataFrame(data_gps)
    return df_gps

# Function to extract distance data from an image
def extract_distance(image_loc):
    image = cv2.imread(image_loc)
    scale = 0.02  # Adjust this value according to the height of the drones
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (15, 15), 0)
    thresh = cv2.threshold(blur, 80, 255, cv2.THRESH_BINARY)[1]
    thresh1 = cv2.erode(thresh, None, iterations=2)
    thresh2 = cv2.dilate(thresh1, None, iterations=2)
    inverted_thresh = cv2.bitwise_not(thresh2)
    cnts = cv2.findContours(inverted_thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key=cv2.contourArea)
    extRight = tuple(c[c[:, :, 0].argmax()][0])
    extLeft = tuple(c[c[:, :, 0].argmin()][0])
    left_distance = extLeft[0] * scale
    right_distance = ((image.shape[1] - extRight[0]) * scale)
    if left_distance == 0:
        distance = right_distance
    elif right_distance == 0:
        distance = left_distance
    else:
        distance = max(left_distance, right_distance)
    data_distance = {'Distance': [distance]}
    df_distance = pd.DataFrame(data_distance)
    return df_distance



def call_ael(image_folder_L):
    # Create a list to store DataFrames for each image
    df_list = []

    # Loop through the images in the folder
    for filename in os.listdir(image_folder_L):
        if filename.endswith((".jpg", ".jpeg")):
            image_loc = os.path.join(image_folder_L, filename)
            # Extract GPS coordinates
            df_gps = extract_gps(image_loc)
            # Extract distance information
            df_distance = extract_distance(image_loc)
            # Combine the data into a single DataFrame row
            df_row = pd.concat([df_gps, df_distance], axis=1)
            # Append the row to the list
            df_list.append(df_row)

    # Concatenate all the DataFrames in the list
    df_all = pd.concat(df_list, ignore_index=True)

    return df_all

