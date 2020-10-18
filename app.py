from flask import Flask, render_template
from google.cloud import vision
from google.cloud.vision import ImageAnnotatorClient
from google.cloud import storage
import uuid 
app = Flask(__name__)

@app.route("/save_img", methods = ['POST'])
def data_to_file(png_data):
    png_id=id_generator()
    filename="tmp/{id}png".format(png_id)
    with open(filename, "wb") as fh:
        fh.write(base64.decodebytes(png_data))
    return filename

@app.route("/visio_call", methods = ['POST'])
def visio_call(image_url):
    client = vision.ImageAnnotatorClient()
    response = client.label_detection({
        'source': {'image_uri': 'https://i.imgur.com/PN40fUh.jpeg'}})
    return visio_response

@app.route("/label_parser")
def label_parser(visio_response):
    label_list=[]
    for label in visio_response.label_annotations:
        label_dict={"species":label.description, "score":label.score}
        label_list.append(label_dict)
    labels_json={"labels":label_list}
    print(labels_json)
    return labels_json

@app.route("/label_species_checker")
def label_species_checker():
    return

@app.route("/img_id_creator")
def id_generator():
    img_id=str(uuid.uuid1())
    return img_id

@app.route("/bucket_upload", methods = ['POST'])
def upload_to_bucket(img_name, path_to_file, bucket_name):
    """ Upload data to a bucket"""

    # Explicitly use service account credentials by specifying the private key
    # file.
    storage_client = storage.Client.from_service_account_json(
        'MyFirstProject-65893a830d6d.json')

    #print(buckets = list(storage_client.list_buckets())

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
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
    species_labels=label_species_checker()
    return species_labels


@app.route("/species_response")
def species_human_response():
    human_response=request.args.get("labels_json")
    if human_response=="idk":
        post_to_mongo()
    else:
        post_to_sql()
    return


@app.route("/health")
def health():
    return "healthy"

if __name__ == '__main__':
    app.run()