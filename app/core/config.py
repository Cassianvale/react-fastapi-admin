import json
from decimal import Decimal

# 自定义JSON编码器
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)

# 在FastAPI应用初始化时使用这个编码器
def setup_json_encoder(app):
    app.json_encoder = CustomJSONEncoder 