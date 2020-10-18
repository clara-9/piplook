# -*- coding: utf-8 -*-
"""
Created on Sat Oct 17 19:34:18 2020

@author: crull
"""

from flask import Flask, render_template, request
import pandas as pd
from google.cloud import vision
from google.cloud.vision import ImageAnnotatorClient
from google.cloud import storage
import uuid 
import os
import json
from sqlalchemy import create_engine


app = Flask(__name__)


# @app.route("/save_img", methods=['POST'])
# def data_to_file():
#     png_data=request.arguments.get("png_data")
#     png_id=id_generator()
#     filename="tmp/{id}png".format(png_id)
#     with open(filename, "wb") as fh:
#         fh.write(base64.decodebytes(png_data))
#     return filename

@app.route("/visio_call", methods=['POST'])
def visio_call(image_url):
    client = vision.ImageAnnotatorClient()
    visio_response = client.label_detection({
        'source': {'image_uri': image_url}})
    return visio_response

@app.route("/label_parser")
def label_parser(visio_response):
    label_list=[]
    for label in visio_response.label_annotations:
        if label_species_checker(label.description.lower()):
            label_dict={"species":label.description.lower(), "score":label.score}
            label_list.append(label_dict)
    labels_json={"labels":label_list}
    print(labels_json)
    return labels_json

@app.route("/label_species_checker")
def label_species_checker(label):
    df=pd.read_csv("lowercased_species.csv")
    if label in df["PRIMARY_COM_NAME"].unique():
        return True
    else:
        return False

@app.route("/img_id_creator")
def id_generator():
    img_id=str(uuid.uuid1())
    return img_id

@app.route("/bucket_upload", methods=['POST'])
def upload_to_bucket(img_name, path_to_file, bucket_name):
    """ Upload data to a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'MyFirstProject-65893a830d6d.json')

    #print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(img_name)
    blob.upload_from_filename(path_to_file)

    #returns a public url
    print(blob.public_url)
    return blob.public_url

@app.route("/species_response")
def species_human_response():
    human_response=request.args.get("labels_json")
    if human_response=="idk":
        post_to_mongo()
    else:
        post_to_sql()
    return

def sort_labels(labels):
    score=0
    best_label=""
    for label in labels["labels"]:
        if float(label["score"])>score:
            score=float(label["score"])
            best_label=label["species"]
    return best_label

@app.route("/health")
def health():
    return "healthy"


@app.route("/bird_capture", methods=['POST'])
def bird_capture():
    file=request.files['file']
    print(file)
    path=os.path.join("/tmp/", file.name)
    file.save(path)
    img_id=id_generator()+".jpg"
    image_url=upload_to_bucket(img_id, path, "picture_store")
    labels=visio_call(image_url)
    labels=label_parser(labels)
    print(labels)
    best_label=sort_labels(labels)
    labels["best_label"]=best_label
    labels["img_id"]=img_id
    return labels


@app.route("/post_record", methods=['POST'])
def post_record():
    species=request.args.get("species")
    timestamp=request.args.get("timestamp")
    latitude=request.args.get("latitude")
    longitude=request.args.get("longitude")
    image_id=request.args.get("image_id")
    user_id=request.args.get("user_id")
    db_uri="postgres://pmgenzxwfartue:b4378ea35bf3914bd75259b0eac84ed461703371cd34600957766e437c196ff4@ec2-54-247-103-43.eu-west-1.compute.amazonaws.com:5432/d9rts97cekhe28"
    engine = create_engine(db_uri)
    query=f"""INSERT INTO public.sighting (species, timestamp, latitude, longitude, image_id, user_id)
    VALUES ({species}, {timestamp}, {latitude}, {longitude}, {image_id}, {user_id});"""
    pd.read_sql(query, engine)
    return

@app.route("/get_coords", methods=['GET'])
def get_coords():
    species=request.args.get("species")
    db_uri="postgres://pmgenzxwfartue:b4378ea35bf3914bd75259b0eac84ed461703371cd34600957766e437c196ff4@ec2-54-247-103-43.eu-west-1.compute.amazonaws.com:5432/d9rts97cekhe28"
    engine = create_engine(db_uri)
    query=f"""SELECT latitude as lat, longitude as lng FROM public.sighting 
    WHERE species='{species}';"""
    df=pd.read_sql(query, engine)
    coords_collection={"records":df.to_dict('records')}
    return coords_collection


if __name__ == '__main__':
    app.run()