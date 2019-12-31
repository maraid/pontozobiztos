import json
import pathlib
from datetime import datetime
import re
import pymongo

root = pathlib.Path(__file__).parent
grouped_images = root / "grouped_images"

client = pymongo.MongoClient()
db = client.chat
user_coll = db.users

cursor = user_coll.find({}, {'id_': 1, 'fullname': 1})
participants = {c['fullname']: c['_id'] for c in cursor}


def fix_text(text):
    return text.encode('latin1').decode('utf8')


def main():
    msg_jsons = [item for item in root.iterdir() if item.suffix == ".json"]
    new_old_pairs = {}
    status_i = 0
    for json_doc in msg_jsons:
        with open(json_doc, "r") as f:
            doc = json.load(f)

        for msg in doc['messages']:
            photos = msg.get('photos')
            if photos is not None:
                timestamp = datetime.fromtimestamp(msg['timestamp_ms'] / 1000)
                timestamp_str = timestamp.strftime('%Y%m%d%H%M%S')
                author_id = participants.get(fix_text(msg.get('sender_name')), '000000')
                i = 0
                for photo in photos:
                    try:
                        old_filename, ext = re.search(
                            r"photos/(.*(\..*))$", photo['uri']).groups()
                    except AttributeError:
                        print(photo)
                        continue
                    new_filename = timestamp_str + "_" + author_id + "_" + "n" + str(i) + ext

                    old_path = pathlib.Path("photos", old_filename)
                    try:
                        old_path.rename("photos/" + new_filename)
                    except FileExistsError:
                        i += 1
                        new_filename = timestamp_str + "_" + author_id + "_" + "n" + str(i) + ext
                        old_path.rename("photos/" + new_filename)
                    except FileNotFoundError:
                        pass
                    new_old_pairs[new_filename] = old_filename
                    status_i += 1
                    print(status_i)


def check_photo_names():
    photos = root / "photos"

    for image in photos.iterdir():
        match = re.search(r"photos\\.*_n\d{1,2}\..*$", str(image))
        if not match:
            print(image)

def distribute_images():
    photos = root / "photos"
    bins = root / "grouped_images"
    bins.mkdir(exist_ok=True)
    n_bins = 24
    for b in range(n_bins):
        (bins / f"group_{b + 1}").mkdir(exist_ok=True)

    i = 0
    for image in photos.iterdir():
        print(f"group_{(i % n_bins) + 1}")
        image.rename(f"grouped_images/group_{(i % n_bins) + 1}/" + image.name)
        i += 1


def zipup():
    import pyminizip

    zips = pathlib.Path("zips")
    zips.mkdir(exist_ok=True)

    for dir_ in grouped_images.iterdir():
        if not dir_.is_dir():
            continue
        filenames = [str(f) for f in dir_.iterdir()]
        path_prefix = ["/" + dir_.name] * len(filenames)
        pyminizip.compress_multiple(filenames, path_prefix, str(zips / (dir_.name + ".zip")), "szarapontozo", 3)
    # pyminizip.compress_multiple(["tmp.txt"], ["/group_1"], "tmp.zip", "asd", 3)
    #pyminizip.compress(str(grouped_images / "group_1"), str(grouped_images / "group_1.zip"), "szarapontozo", 3)


def group_images():
    source_dir = pathlib.Path("grouped_images")
    train_dir = pathlib.Path("classified_data", "train")
    (train_dir / "kakie").mkdir(exist_ok=True)
    (train_dir / "extra").mkdir(exist_ok=True)
    (train_dir / "pisie").mkdir(exist_ok=True)
    (train_dir / "selfie").mkdir(exist_ok=True)
    (train_dir / "other").mkdir(exist_ok=True)
    for item in source_dir.iterdir():
        if not item.is_file() or item.suffix != ".txt":
            continue
        groupname = source_dir / item.name[:-4]
        with open(str(item), "r") as f:
            for line in f:
                filename, class_ = line.strip().split(" ")
                source_file = groupname / filename
                if not source_file.exists():
                    print(source_file)
                    continue
                source_file.rename(str(train_dir / class_ / filename))


def group_15():
    """Márk elbaszta az other-t"""
    source_dir = pathlib.Path("grouped_images")
    train_dir = pathlib.Path("classified_data", "train")
    groupname = "group_15"
    with open(str(source_dir) + "/" + groupname + ".txt", "r") as f:
        for line in f:
            filename, class_ = line.strip().split(" ")
            if class_ == "other":
                continue
            source_file = source_dir / groupname / filename
            if not source_file.exists():
                print(source_file)
                continue
            source_file.rename(str(train_dir / class_ / filename))


if __name__ == "__main__":
    group_15()