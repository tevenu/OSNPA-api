from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_mysqldb import MySQL
import json

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
    print(data)
    profile = {
        'name': data[0],
        'followers': data[1],
        'follow': data[2],
        'verification': data[3],
        'avatar': data[4],
    }
    sql = "SELECT privacy_class, privacy_value " \
          "FROM weibo.INFO WHERE screen_name=%s;"
    cur.execute(sql, val)
    privacy_list = cur.fetchall()
    sql = "SELECT " \
          "SUM(CASE WHEN screen_name = %s THEN 1 ELSE 0 END) AS blog_count," \
          "SUM(CASE WHEN screen_name = %s AND isPrivacy = 1 THEN 1 ELSE 0 END) AS privacy_count, " \
          "SUM(CASE WHEN screen_name = %s AND isPrivacy = 0 THEN 1 ELSE 0 END) AS non_privacy_count " \
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
          "SUM(CASE WHEN screen_name = %s AND isPrivacy = 1 THEN 1 ELSE 0 END) AS privacy_count, " \
          "SUM(CASE WHEN screen_name = %s AND isPrivacy = 0 THEN 1 ELSE 0 END) AS non_privacy_count " \
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
    search_params = request.args.get('searchParams')
    params = json.loads(search_params)  # 解析 JSON 数据

    is_privacy = params.get('是否隐私')
    publish_time = params.get('发布时间')
    text_content = params.get('文本内容')
    privacy_info = params.get('隐私信息')

    cur = mysql.connection.cursor()

    # 构建基础的 SQL 查询语句
    sql = "SELECT screen_name, created_at, text, pics, isPrivacy, privacy " \
          "FROM weibo.weibo WHERE screen_name=%s"

    # 根据搜索条件添加相应的过滤条件
    conditions = []
    val = [user]
    if publish_time:
        publish_parts = publish_time.split('-')
        if len(publish_parts) == 1:
            conditions.append("YEAR(created_at) = %s")  # 匹配年份
        elif len(publish_parts) == 2:
            conditions.append("YEAR(created_at) = %s")
            conditions.append("MONTH(created_at) = %s")  # 匹配年月
        elif len(publish_parts) == 3:
            conditions.append("YEAR(created_at) = %s")
            conditions.append("MONTH(created_at) = %s")
            conditions.append("DAY(created_at) = %s")  # 匹配年月日
        val.extend(publish_parts)
    if text_content:
        conditions.append("text LIKE %s")
        val.append(f"%{text_content}%")
    if is_privacy:
        conditions.append("isPrivacy = %s")
        is_privacy = 1 if is_privacy == "是" else 0
        val.append(is_privacy)
    if privacy_info:
        conditions.append("privacy LIKE %s")
        val.append(f"%{privacy_info}%")

    if conditions:
        sql += " AND " + " AND ".join(conditions)

    sql += " ORDER BY created_at DESC;"

    cur.execute(sql, val)
    data = cur.fetchall()
    output_data = []

    for item in data:
        id_, time, text, image, is_privacy, privacy = item
        is_privacy = "是" if is_privacy else "否"
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S')
        if image:
            image = "images/%s/%s" % (id_, image)
        else:
            image = ''
        output_item = {
            "id": id_,
            "time": formatted_time,
            "text": text,
            "image": image,
            "is_privacy": is_privacy,
            "information": privacy
        }
        output_data.append(output_item)

    return jsonify(output_data)


users = ['余霜YSCandice', '空中的士马宏', '我是F1兵哥', '拓树成林', '余霜的小老婆', '余霜小粉儿', '余霜_sea']


@app.route('/search')
def search():
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify([])  # 返回空列表表示没有匹配项

    matched_users = [user for user in users if user.startswith(keyword)]
    return jsonify(matched_users)


if __name__ == '__main__':
    app.run(debug=True)
