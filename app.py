from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL

app = Flask(__name__)
CORS(app)

app.config['MYSQL_HOST'] = '150.158.140.253'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'qq523629002***'
app.config['MYSQL_DB'] = 'DATA'

mysql = MySQL(app)


@app.route('/user', methods=['GET'])
def get_data():
    user = request.args.get('user')
    cur = mysql.connection.cursor()
    sql = "SELECT screen_name, followers_count, follow_count, verified_reason, avatar_hd " \
          "FROM weibo.user WHERE screen_name = %s"
    val = [user]
    cur.execute(sql, val)
    data = cur.fetchone()
    profile = {
        'name': data[0],
        'followers': data[1],
        'follow': data[2],
        'verification': data[3],
        'avatar': data[4],
    }
    sql = "SELECT privacy_class, privacy_value " \
          "FROM weibo.privacy WHERE userid IN (SELECT id FROM weibo.user where screen_name=%s);"
    cur.execute(sql, val)
    privacy_list = cur.fetchall()
    sql = "SELECT " \
          "SUM(CASE WHEN screen_name = %s THEN 1 ELSE 0 END) AS blog_count," \
          "SUM(CASE WHEN screen_name = %s AND isValid = 1 THEN 1 ELSE 0 END) AS privacy_count, " \
          "SUM(CASE WHEN screen_name = %s AND isValid = 0 THEN 1 ELSE 0 END) AS non_privacy_count " \
          "FROM weibo.weibo;"
    val = [user, user, user]
    cur.execute(sql, val)
    counts = cur.fetchone()
    cur.close()
    html_content = render_template('user.html', profile=profile, privacy_list=privacy_list, counts=counts)
    return html_content


@app.route('/count', methods=['GET'])
def get_count():
    user = request.args.get('user')
    cur = mysql.connection.cursor()
    sql = "SELECT " \
          "SUM(CASE WHEN screen_name = %s THEN 1 ELSE 0 END) AS blog_count," \
          "SUM(CASE WHEN screen_name = %s AND isValid = 1 THEN 1 ELSE 0 END) AS privacy_count, " \
          "SUM(CASE WHEN screen_name = %s AND isValid = 0 THEN 1 ELSE 0 END) AS non_privacy_count " \
          "FROM weibo.weibo;"
    val = [user, user, user]
    cur.execute(sql, val)
    result = cur.fetchone()
    data = {
        "data": [
            {"value": result[2], "name": "安全博文"},
            {"value": result[1], "name": "风险博文"}
        ]
    }
    return jsonify(data)


@app.route('/text', methods=['GET'])
def get_text():
    user = request.args.get('user')
    cur = mysql.connection.cursor()
    sql = "SELECT screen_name, created_at, text, isValid FROM weibo.weibo where screen_name=%s;"
    val = [user]
    cur.execute(sql, val)
    data = cur.fetchall()
    output_data = []
    for item in data:
        id_, time, text, is_privacy = item
        image = 'images/yushuang/p1.png'
        #改一下，正常需要从item中取
        
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')
        output_item = {
            "id": id_,
            "time": formatted_time,
            "text": text,
            "image": image,
            "is_privacy": is_privacy,
            "information": "information"
        }
        output_data.append(output_item)
    return jsonify(output_data)


if __name__ == '__main__':
    app.run()
