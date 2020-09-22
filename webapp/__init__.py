from flask import Flask, render_template         # import flask
from pontozobiztos import chatmongo

app = Flask(__name__)             # create an app instance


@app.route("/")                   # at the end point /
def hello():
    user_ids = chatmongo.get_user_ids()
    users = [chatmongo.get_user_info(id_) for id_ in user_ids]
    user_points_and_names = []
    for user in users:
        user_points_and_names.append(
            {'id': user['_id'],
             'fullname': user['fullname'],
             'points': chatmongo.get_points_sum(user['_id'])})
    user_points_and_names.sort(key=lambda x: x['points'], reverse=True)

    return render_template("index.html", content=user_points_and_names)


@app.route("/userdetail/<string:id>")
def userdetail(id):
    user_points = chatmongo.get_points(id)
    points_sum = chatmongo.get_points_sum(id)
    user_name = chatmongo.get_user_info(id)['fullname']
    for point in user_points:
        point['timestamp'] = point['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
    user_points.sort(key=lambda x: x['timestamp'])
    return render_template("userdetail.html",
                           user_points=user_points,
                           name=user_name,
                           points_sum=points_sum)


if __name__ == "__main__":
    app.run(host='192.168.1.100', port=9000, debug=False)