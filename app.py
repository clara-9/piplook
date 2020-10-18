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

@app.route("/bird_capture")
def bird_capture():
    png_data=request.args.get("png_data")
    img_id=data_to_file(png_data)
    image_url=upload_to_bucket(img_id, img_id, "picture_store")
    labels=visio_call(image_url)
    species_labels=label_species_checker(labels)
    return species_labels


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
    for label in labels:
        if float(label["score"])>score:
            score=float(label["score"])
            best_label=label["species"]
    return best_label

@app.route("/health")
def health():
    return "healthy"


@app.route("/test")
def test():
    png_url=request.args.get("png_url")
    lat=request.args.get("lat")
    lon=request.args.get("long")
    img_id=id_generator()
    image_url=upload_to_bucket(img_id, png_url, "picture_store")
    print(lat)
    print(lon)
    return

@app.route("/test2", methods=['POST'])
def test2():
    file=request.files['file']
    print(file)
    path=os.path.join("/tmp/", file.name)
    file.save(path)
    img_id=id_generator()+".jpeg"
    image_url=upload_to_bucket(img_id, path, "picture_store")
    labels=visio_call(image_url)
    labels=label_parser(labels)
    print(sort_labels(labels))
    return labels

if __name__ == '__main__':
    app.run()