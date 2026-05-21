from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yaml
import os

# 加载配置
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
if config.get('cors', {}).get('enabled', True):
    CORS(app)

# 端口配置
PORT = config['server']['port']
DEBUG = config['server'].get('debug', False)

# 简化的城市坐标数据库
CITIES = {
    # 中国城市
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "深圳": (22.5431, 114.0579),
    "广州": (23.1291, 113.2644),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "重庆": (29.4316, 106.9123),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "南京": (32.0603, 118.7969),
    "天津": (39.3434, 117.3616),
    "苏州": (31.2989, 120.5853),
    "郑州": (34.7466, 113.6253),
    "长沙": (28.2282, 112.9388),
    "沈阳": (41.8057, 123.4328),
    "青岛": (36.0671, 120.3826),
    "济南": (36.6512, 117.1205),
    "大连": (38.9140, 121.6147),
    "福州": (26.0745, 119.2965),
    "厦门": (24.4798, 118.0894),
    "昆明": (25.0406, 102.7129),
    "贵阳": (26.6470, 106.6302),
    "南宁": (22.8170, 108.3665),
    "海口": (20.0444, 110.1999),
    "太原": (37.8706, 112.5489),
    "石家庄": (38.0428, 114.5149),
    "长春": (43.8171, 125.3235),
    "哈尔滨": (45.8038, 126.5340),
    "兰州": (36.0611, 103.8343),
    "乌鲁木齐": (43.8256, 87.6168),
    "拉萨": (29.6500, 91.1000),
    "呼和浩特": (40.8424, 111.7492),
    "银川": (38.4872, 106.2309),
    "西宁": (36.6171, 101.7782),
    "香港": (22.3193, 114.1694),
    "澳门": (22.1987, 113.5439),
    "台北": (25.0330, 121.5654),

    # 国际城市
    "纽约": (40.7128, -74.0060),
    "洛杉矶": (34.0522, -118.2437),
    "旧金山": (37.7749, -122.4194),
    "芝加哥": (41.8781, -87.6298),
    "东京": (35.6762, 139.6503),
    "伦敦": (51.5074, -0.1278),
    "巴黎": (48.8566, 2.3522),
    "柏林": (52.5200, 13.4050),
    "悉尼": (-33.8688, 151.2093),
    "新加坡": (1.3521, 103.8198),
    "首尔": (37.5665, 126.9780),
    "曼谷": (13.7563, 100.5018),
    "迪拜": (25.2048, 55.2708),
    "莫斯科": (55.7558, 37.6173),
    "孟买": (19.0760, 72.8777),
    "开罗": (30.0444, 31.2357),
    "里约热内卢": (-22.9068, -43.1729),
    "开普敦": (-33.9249, 18.4241),
    "多伦多": (43.6532, -79.3832),
    "温哥华": (49.2827, -123.1207),
    "墨西哥城": (19.4326, -99.1332),
    "圣保罗": (-23.5505, -46.6333),
    "Buenos Aires": (-34.6037, -58.3816),
    "罗马": (41.9028, 12.4964),
    "米兰": (45.4642, 9.1900),
    "马德里": (40.4168, -3.7038),
    "巴塞罗那": (41.3851, 2.1734),
    "阿姆斯特丹": (52.3676, 4.9041),
    "维也纳": (48.2082, 16.3738),
    "布拉格": (50.0755, 14.4378),
    "伊斯坦布尔": (41.0082, 28.9784),
    "特拉维夫": (32.0853, 34.7818),
    "吉隆坡": (3.1390, 101.6869),
    "雅加达": (-6.2088, 106.8456),
    "马尼拉": (14.5995, 120.9842),
    "河内": (21.0285, 105.8542),
    "胡志明市": (10.8231, 106.6297),
    "奥克兰": (-36.8485, 174.7633),
    "墨尔本": (-37.8136, 144.9631),
    "珀斯": (-31.9505, 115.8605),
}


def search_city(query):
    """模糊搜索城市"""
    query = query.lower().strip()
    results = []

    # 精确匹配优先
    for name, coords in CITIES.items():
        if query == name.lower():
            results.insert(0, {"name": name, "lat": coords[0], "lng": coords[1], "exact": True})
        elif query in name.lower() or name.lower() in query:
            results.append({"name": name, "lat": coords[0], "lng": coords[1], "exact": False})

    # 去重并保持顺序
    seen = set()
    unique_results = []
    for r in results:
        if r["name"] not in seen:
            seen.add(r["name"])
            unique_results.append(r)

    return unique_results


@app.route('/')
def index():
    """首页 - 地球可视化页面"""
    return send_file(os.path.join(os.path.dirname(__file__), '..', 'index.html'))


@app.route('/api/geocode', methods=['GET'])
def geocode():
    """将地名转换为坐标"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "请提供地点名称"}), 400

    results = search_city(query)
    if not results:
        return jsonify({"error": "未找到该地点", "query": query}), 404

    return jsonify({
        "results": results,
        "count": len(results)
    })


@app.route('/api/cities', methods=['GET'])
def list_cities():
    """获取所有支持的城市列表"""
    cities = [{"name": name, "lat": coords[0], "lng": coords[1]} for name, coords in CITIES.items()]
    return jsonify({"cities": cities, "count": len(cities)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)