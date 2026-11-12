"""Build the 1000+ word general frequency pack.

Sources:
- 1000mostcommonwords.com Vietnamese list (frequency seed)
- A curated list of extra everyday words
- dict.minhqnd.com open dictionary API for Hanoi IPA / POS / examples
- Microsoft Edge keyless translation endpoint for Chinese glosses

The textbook words in data/words.textbook.json are preserved; general words are
appended and clearly labelled as a general frequency list.
"""
from __future__ import annotations

import argparse
import bz2
import html
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import zhconv

ROOT = Path(__file__).resolve().parents[1]
GENERAL_DIR = ROOT / "data" / "general"
HTML_SOURCE = GENERAL_DIR / "common1000.html"
EXTRA_SOURCE = GENERAL_DIR / "extra_words.txt"
TEXTBOOK_SOURCE = ROOT / "data" / "words.textbook.json"
OUTPUT = ROOT / "data" / "words.json"
LOOKUP_CACHE = GENERAL_DIR / "lookup_cache.json"
TRANSLATION_CACHE = GENERAL_DIR / "translation_cache.json"
DEFINITION_CACHE = GENERAL_DIR / "definition_translation_cache.json"
ENGLISH_SENSE_CACHE = GENERAL_DIR / "english_sense_cache.json"
SIMPLE_GLOSS_CACHE = GENERAL_DIR / "simple_gloss_cache.json"
MYMEMORY_CACHE = GENERAL_DIR / "mymemory_cache.json"
TATOEBA_SOURCE = ROOT / "data" / "tatoeba" / "vie_sentences.tsv.bz2"
TATOEBA_EXAMPLE_CACHE = GENERAL_DIR / "tatoeba_examples.json"
TATOEBA_TRANSLATION_CACHE = GENERAL_DIR / "tatoeba_translation_cache.json"
SEED_OUTPUT = GENERAL_DIR / "frequency_words.json"

DICT_URL = "https://dict.minhqnd.com/api/v1/lookup"
TRANSLATE_URL = "https://edge.microsoft.com/translate/translatetext"

POS_MAP = {
    "Danh từ": "名词",
    "Động từ": "动词",
    "Tính từ": "形容词",
    "Phó từ": "副词",
    "Đại từ": "代词",
    "Giới từ": "介词",
    "Liên từ": "连词",
    "Trợ từ": "助词",
    "Số từ": "数词",
    "Lượng từ": "量词",
    "Thán từ": "叹词",
    "Thành ngữ": "短语",
    "Quán ngữ": "短语",
}

FUNCTION_WORDS = {
    "là", "của", "và", "như", "mà", "cho", "trên", "với", "từ", "tại", "bởi",
    "được", "có", "này", "những", "các", "một", "không", "nhưng", "hoặc", "để",
    "trong", "ngoài", "dưới", "sau", "trước", "khi", "nếu", "thì", "vì", "nên",
    "rất", "quá", "lắm", "cũng", "đã", "đang", "sẽ", "vẫn", "còn", "chỉ", "mới",
    "tôi", "mình", "bạn", "anh", "chị", "em", "ông", "bà", "cô", "chú", "họ",
    "nó", "chúng", "ai", "gì", "nào", "đâu", "sao", "thế", "vậy", "ạ", "nhé",
    "đây", "đó", "kia", "ấy", "mỗi", "mọi", "cả", "tất cả", "một số", "các",
    "muốn", "cần", "thích", "yêu", "biết", "hiểu", "phải", "nên", "ở", "đi",
}

SPECIAL_TEMPLATE_WORDS = FUNCTION_WORDS | {
    "muốn", "cần", "thích", "yêu", "biết", "hiểu", "phải", "nên", "có", "là",
    "được", "ở", "cho",
}

MANUAL_ZH = {
    "như": "如；像", "tôi": "我", "mình": "自己；我", "mà": "而；但是",
    "ông": "先生；祖父", "là": "是", "cho": "给；让", "trên": "上面；在……上",
    "với": "和；与", "họ": "他们", "được": "可以；得到", "tại": "在；因为",
    "một": "一", "có": "有", "này": "这", "từ": "从；词", "bởi": "因为",
    "nóng": "热", "nhưng": "但是", "những gì": "什么", "một số": "一些",
    "nó": "它", "anh": "你；哥哥", "hoặc": "或者", "các": "各；复数前缀",
    "của": "的", "để": "为了；让", "và": "和", "trong": "在……里",
    "chúng tôi": "我们", "bạn": "你；朋友", "đó": "那", "đây": "这",
    "nhiều": "多", "ít": "少", "không": "不；没有", "cũng": "也",
    "rất": "很", "quá": "太", "lắm": "很", "đã": "已经", "đang": "正在",
    "sẽ": "将", "vẫn": "仍然", "còn": "还", "chỉ": "只", "mới": "新；刚",
    "nào": "哪", "ai": "谁", "gì": "什么", "đâu": "哪里", "sao": "怎么；星星",
    "thế": "这样", "vậy": "那样", "ạ": "语气词", "nhé": "语气词",
    "phải": "必须；对", "nên": "应该；所以", "muốn": "想", "cần": "需要",
    "thích": "喜欢", "yêu": "爱", "biết": "知道", "hiểu": "明白",
    "ở": "在", "đi": "去", "đến": "到", "về": "回；关于",
    "gửi": "寄；发送", "nhận": "收到", "mở": "打开", "đóng": "关闭",
    "mua": "买", "bán": "卖", "ăn": "吃", "uống": "喝", "ngủ": "睡觉",
    "nói": "说", "nghe": "听", "nhìn": "看", "thấy": "看见",
    "học": "学习", "dạy": "教", "làm": "做", "chơi": "玩", "xem": "看",
    "giúp": "帮助", "thử": "试", "chọn": "选择", "mặc": "穿", "cởi": "脱",
    "giặt": "洗（衣）", "nấu": "煮", "rửa": "洗", "đợi": "等",
    "bắt đầu": "开始", "kết thúc": "结束", "làm việc": "工作",
    "nghỉ ngơi": "休息", "ngắn": "短", "di chuyển": "移动", "tài liệu": "文档",
    "thay đổi": "改变", "kéo": "拉；剪刀", "cũ": "旧", "dì": "阿姨",
    "trung": "中间", "một số": "一些", "có thể": "可以", "nếu": "如果",
    "thậm chí": "甚至", "như vậy": "这样", "sau khi": "之后", "mỗi": "每个",
    "dưới": "下面", "lần lượt": "依次", "trước": "之前", "cô": "她；老师",
    "tất cả": "全部", "khi": "当", "sau đó": "然后", "nhất": "最",
    "bây giờ": "现在", "không bao giờ": "从不", "trong khi": "当……时",
    "dường như": "似乎", "luôn luôn": "总是", "những": "那些",
    "bao giờ": "什么时候", "mặc dù": "虽然", "toàn bộ": "全部",
    "nhất định": "一定", "sau": "后面", "trăm": "百", "mười": "十",
    "có lẽ": "也许", "triệu": "百万", "sạch": "干净", "lên cao": "升高",
    "hai mươi": "二十", "do đó": "因此", "ngay lập tức": "立刻",
    "ngược lại": "相反", "nghìn": "千", "chú": "叔叔",
    "tài xế": "司机", "ga": "车站", "bài": "课；文章", "bản sao": "副本",
    "khối": "块；街区", "nghi": "怀疑", "riêng biệt": "单独的",
    "ngày mai": "明天", "ho": "咳嗽", "da": "皮肤", "gỗ": "木头",
    "bụng": "肚子", "ngựa": "马", "ớt": "辣椒", "biểu tượng": "标志",
    "chia sẻ": "分享", "phát triển": "发展",
    "lực": "力量", "cà vạt": "领带", "văn phòng": "办公室", "lần": "次",
    "quả": "水果；个", "cuối": "末尾；最后", "lông": "毛",
    "hình dạng": "形状", "ngón tay": "手指", "váy": "裙子",
    "trang trại": "农场", "cầu": "桥", "thẻ": "卡", "tối": "晚上；暗",
    "hoạt động": "活动", "môi": "嘴唇", "cao": "高", "lưỡi": "舌头",
    "như nhau": "一样", "tắt": "关掉", "bỏ lỡ": "错过", "cửa": "门",
    "vàng": "黄色；金子", "súng": "枪", "ngăn chặn": "阻止",
    "dấu hiệu": "迹象", "thể": "身体；形式", "nhà ga": "火车站",
    "ống": "管子", "thứ nhất": "第一", "mắt": "眼睛", "mang lại": "带来",
    "bộ": "套；部", "hướng": "方向",
}

MANUAL_EXAMPLES = {
    "cho": ("Mẹ cho tôi một quyển sách.", "妈妈给了我一本书。"),
    "tôi": ("Tôi là người Việt Nam.", "我是越南人。"),
    "như": ("Cô ấy hát như ca sĩ.", "她唱得像歌手。"),
    "mà": ("Tôi muốn đi mà trời mưa.", "我想去，但是下雨了。"),
    "ông": ("Ông ấy là giáo viên.", "他是老师。"),
    "là": ("Tôi là học sinh.", "我是学生。"),
    "trên": ("Quyển sách ở trên bàn.", "书在桌子上。"),
    "với": ("Tôi đi với bạn.", "我和朋友一起去。"),
    "họ": ("Họ đang học tiếng Việt.", "他们在学越南语。"),
    "được": ("Tôi được nghỉ hôm nay.", "我今天可以休息。"),
    "tại": ("Tôi đang ở tại Hà Nội.", "我现在在河内。"),
    "một": ("Tôi có một quả táo.", "我有一个苹果。"),
    "có": ("Tôi có một câu hỏi.", "我有一个问题。"),
    "này": ("Cái này rất đẹp.", "这个很漂亮。"),
    "từ": ("Tôi đến từ Trung Quốc.", "我来自中国。"),
    "bởi": ("Tôi nghỉ bởi vì tôi bị ốm.", "我因为生病而休息。"),
    "nhưng": ("Tôi muốn đi nhưng trời mưa.", "我想去，但是下雨了。"),
    "nó": ("Nó là con mèo của tôi.", "它是我的猫。"),
    "anh": ("Anh ấy là anh trai tôi.", "他是我哥哥。"),
    "hoặc": ("Bạn uống trà hoặc cà phê?", "你喝茶还是咖啡？"),
    "các": ("Các bạn đang học bài.", "同学们在学课文。"),
    "của": ("Đây là sách của tôi.", "这是我的书。"),
    "để": ("Tôi học để làm việc.", "我学习是为了工作。"),
    "và": ("Tôi thích cà phê và trà.", "我喜欢咖啡和茶。"),
    "trong": ("Sách ở trong cặp.", "书在包里。"),
    "chúng tôi": ("Chúng tôi là học sinh.", "我们是学生。"),
    "bạn": ("Bạn tên là gì?", "你叫什么名字？"),
    "đó": ("Cái đó là của tôi.", "那个是我的。"),
    "đây": ("Đây là nhà của tôi.", "这是我的家。"),
    "nhiều": ("Ở đây có nhiều cây.", "这里有很多树。"),
    "ít": ("Tôi có ít tiền.", "我钱不多。"),
    "không": ("Tôi không hiểu.", "我不明白。"),
    "cũng": ("Tôi cũng thích.", "我也喜欢。"),
    "rất": ("Cô ấy rất đẹp.", "她很漂亮。"),
    "quá": ("Cái này đắt quá.", "这个太贵了。"),
    "lắm": ("Cô ấy đẹp lắm.", "她很漂亮。"),
    "đã": ("Tôi đã ăn rồi.", "我已经吃了。"),
    "đang": ("Tôi đang học.", "我正在学习。"),
    "sẽ": ("Ngày mai tôi sẽ đi.", "我明天会去。"),
    "vẫn": ("Anh ấy vẫn khỏe.", "他仍然健康。"),
    "còn": ("Tôi còn một quả.", "我还剩一个。"),
    "chỉ": ("Tôi chỉ có một cái.", "我只有一个。"),
    "mới": ("Đây là sách mới.", "这是新书。"),
    "nào": ("Bạn thích màu nào?", "你喜欢哪个颜色？"),
    "ai": ("Ai đang gọi?", "谁在打电话？"),
    "gì": ("Bạn đang làm gì?", "你在做什么？"),
    "đâu": ("Nhà bạn ở đâu?", "你家在哪里？"),
    "sao": ("Sao bạn không đến?", "你为什么不来？"),
    "thế": ("Thế là tốt.", "这样很好。"),
    "vậy": ("Vậy chúng ta đi nhé.", "那我们走吧。"),
    "phải": ("Bạn phải học bài.", "你必须学习。"),
    "nên": ("Bạn nên nghỉ ngơi.", "你应该休息。"),
    "muốn": ("Tôi muốn uống nước.", "我想喝水。"),
    "cần": ("Tôi cần giúp đỡ.", "我需要帮助。"),
    "thích": ("Tôi thích học tiếng Việt.", "我喜欢学越南语。"),
    "yêu": ("Tôi yêu gia đình.", "我爱家人。"),
    "biết": ("Tôi biết anh ấy.", "我认识他。"),
    "hiểu": ("Tôi hiểu câu này.", "我明白这句话。"),
    "ở": ("Tôi ở Hà Nội.", "我在河内。"),
    "đi": ("Tôi đi học mỗi ngày.", "我每天去上学。"),
    "đến": ("Tôi đến trường lúc 8 giờ.", "我八点到学校。"),
    "về": ("Tôi về nhà.", "我回家。"),
    "gửi": ("Tôi gửi thư cho mẹ.", "我给妈妈寄信。"),
    "nhận": ("Tôi nhận được quà.", "我收到礼物。"),
    "mở": ("Mở cửa ra.", "打开门。"),
    "đóng": ("Đóng cửa lại.", "关上门。"),
    "mua": ("Tôi mua một quả táo.", "我买一个苹果。"),
    "bán": ("Họ bán phở.", "他们卖河粉。"),
    "ăn": ("Tôi ăn phở.", "我吃河粉。"),
    "uống": ("Tôi uống cà phê.", "我喝咖啡。"),
    "ngủ": ("Tôi ngủ lúc 10 giờ.", "我十点睡觉。"),
    "nói": ("Tôi nói tiếng Việt.", "我说越南语。"),
    "nghe": ("Tôi nghe nhạc.", "我听音乐。"),
    "nhìn": ("Tôi nhìn bức tranh.", "我看这幅画。"),
    "thấy": ("Tôi thấy anh ấy.", "我看见他。"),
    "học": ("Tôi học tiếng Việt.", "我学越南语。"),
    "dạy": ("Cô ấy dạy tiếng Anh.", "她教英语。"),
    "làm": ("Tôi làm việc ở đây.", "我在这里工作。"),
    "chơi": ("Trẻ em chơi trong vườn.", "孩子们在花园里玩。"),
    "xem": ("Tôi xem phim.", "我看电影。"),
    "giúp": ("Bạn giúp tôi nhé.", "请你帮帮我。"),
    "thử": ("Tôi muốn thử món này.", "我想尝尝这道菜。"),
    "chọn": ("Tôi chọn cái này.", "我选这个。"),
    "mặc": ("Cô ấy mặc áo đỏ.", "她穿红衣服。"),
    "cởi": ("Cởi giày ra.", "脱下鞋子。"),
    "giặt": ("Tôi giặt quần áo.", "我洗衣服。"),
    "nấu": ("Mẹ nấu cơm.", "妈妈做饭。"),
    "rửa": ("Tôi rửa tay.", "我洗手。"),
    "đợi": ("Tôi đợi bạn.", "我等你。"),
    "bắt đầu": ("Lớp học bắt đầu.", "开始上课。"),
    "kết thúc": ("Buổi học kết thúc.", "课程结束。"),
    "làm việc": ("Tôi làm việc ở công ty.", "我在公司工作。"),
    "nghỉ ngơi": ("Tôi cần nghỉ ngơi.", "我需要休息。"),
    "nặng": ("Cái túi này rất nặng.", "这个包很重。"),
    "cuối cùng": ("Đây là lần cuối cùng.", "这是最后一次。"),
    "tự nhiên": ("Phong cảnh ở đây rất tự nhiên.", "这里的风景很自然。"),
    "động vật": ("Tôi thích động vật.", "我喜欢动物。"),
    "trò chơi": ("Trò chơi này rất vui.", "这个游戏很好玩。"),
    "đầu bếp": ("Đầu bếp đang nấu ăn.", "厨师在做饭。"),
    "mặt trăng": ("Mặt trăng rất sáng.", "月亮很亮。"),
    "đồng bằng": ("Đồng bằng này rất rộng.", "这个平原很辽阔。"),
    "thay đổi": ("Tôi muốn thay đổi công việc.", "我想换工作。"),
    "di chuyển": ("Tôi di chuyển bằng xe buýt.", "我坐公交车出行。"),
    "tỏa sáng": ("Cô ấy tỏa sáng trên sân khấu.", "她在舞台上闪耀。"),
    "thông qua": ("Tôi đã thông qua kỳ thi.", "我通过了考试。"),
    "tài liệu": ("Tôi đang đọc tài liệu.", "我在看文件。"),
    "ngôn ngữ": ("Tiếng Việt là một ngôn ngữ đẹp.", "越南语是一门美丽的语言。"),
    "lo lắng": ("Mẹ tôi lo lắng về tôi.", "我妈妈担心我。"),
    "cảm thấy": ("Tôi cảm thấy rất vui.", "我感觉很开心。"),
    "kim loại": ("Cái bàn này làm bằng kim loại.", "这张桌子是金属做的。"),
    "kéo": ("Tôi cần một cái kéo.", "我需要一把剪刀。"),
    "rau": ("Tôi mua rau ở chợ.", "我在市场买蔬菜。"),
    "dì": ("Dì tôi sống ở Hà Nội.", "我阿姨住在河内。"),
    "thực": ("Đây là câu chuyện có thật.", "这是一个真实的故事。"),
    "dê": ("Con dê đang ăn cỏ.", "山羊在吃草。"),
    "cũ": ("Đây là một cuốn sách cũ.", "这是一本旧书。"),
    "thuốc": ("Tôi phải uống thuốc.", "我得吃药。"),
    "mình": ("Mình là học sinh.", "我是学生。"),
    "một số": ("Một số bạn đang học.", "一些同学在学习。"),
    "có thể": ("Tôi có thể giúp bạn.", "我可以帮你。"),
    "nếu": ("Nếu trời mưa, tôi ở nhà.", "如果下雨，我就待在家。"),
    "thậm chí": ("Anh ấy thậm chí không biết.", "他甚至不知道。"),
    "như vậy": ("Bạn nên làm như vậy.", "你应该这样做。"),
    "sau khi": ("Sau khi ăn, tôi đi học.", "吃完后我去上学。"),
    "mỗi": ("Mỗi ngày tôi học tiếng Việt.", "我每天学越南语。"),
    "dưới": ("Con mèo ở dưới bàn.", "猫在桌子下面。"),
    "lần lượt": ("Các bạn lần lượt trả lời.", "同学们依次回答。"),
    "trước": ("Tôi ăn trước.", "我先吃。"),
    "cô": ("Cô ấy là giáo viên.", "她是老师。"),
    "tất cả": ("Tất cả học sinh đều đến.", "所有学生都来了。"),
    "khi": ("Khi tôi đến, anh ấy đang học.", "我到的时候，他正在学习。"),
    "sau đó": ("Tôi ăn, sau đó đi học.", "我吃饭，然后去上学。"),
    "nhất": ("Đây là cái đẹp nhất.", "这是最漂亮的。"),
    "bây giờ": ("Bây giờ tôi đang học.", "我现在在学习。"),
    "không bao giờ": ("Tôi không bao giờ đi muộn.", "我从不迟到。"),
    "trong khi": ("Trong khi tôi học, mẹ nấu cơm.", "我学习的时候，妈妈做饭。"),
    "dường như": ("Dường như trời sắp mưa.", "好像快要下雨了。"),
    "luôn luôn": ("Cô ấy luôn luôn vui vẻ.", "她总是很开心。"),
    "những": ("Những quyển sách này rất hay.", "这些书很好看。"),
    "bao giờ": ("Bạn bao giờ đi Hà Nội?", "你什么时候去河内？"),
    "mặc dù": ("Mặc dù mưa, tôi vẫn đi.", "尽管下雨，我还是去了。"),
    "toàn bộ": ("Tôi đã đọc toàn bộ cuốn sách.", "我读完了整本书。"),
    "nhất định": ("Tôi nhất định sẽ đến.", "我一定会来。"),
    "sau": ("Tôi đi sau anh ấy.", "我走在他后面。"),
    "trăm": ("Có một trăm người.", "有一百人。"),
    "mười": ("Tôi có mười quả táo.", "我有十个苹果。"),
    "có lẽ": ("Có lẽ anh ấy đang bận.", "他可能很忙。"),
    "triệu": ("Công ty có một triệu đô.", "公司有一百万美元。"),
    "sạch": ("Phòng này rất sạch.", "这个房间很干净。"),
    "lên cao": ("Máy bay bay lên cao.", "飞机飞得很高。"),
    "hai mươi": ("Tôi có hai mươi cuốn sách.", "我有二十本书。"),
    "do đó": ("Trời mưa, do đó tôi ở nhà.", "下雨了，因此我待在家。"),
    "ngay lập tức": ("Hãy đến ngay lập tức.", "立刻过来。"),
    "ngược lại": ("Anh ấy nói ngược lại.", "他说反了。"),
    "nghìn": ("Có một nghìn người.", "有一千人。"),
    "chú": ("Chú ấy là bác sĩ.", "他是医生。"),
    "tài xế": ("Tài xế đang lái xe.", "司机在开车。"),
    "ga": ("Ga Hà Nội ở đâu?", "河内车站在哪里？"),
    "bài": ("Tôi đang học bài.", "我在学习课文。"),
    "bản sao": ("Đây là bản sao của tài liệu.", "这是文件的副本。"),
    "khối": ("Đây là một khối băng.", "这是一块冰。"),
    "nghi": ("Tôi nghi anh ấy nói dối.", "我怀疑他说谎。"),
    "riêng biệt": ("Đây là một trường hợp riêng biệt.", "这是一个单独的情况。"),
    "ngày mai": ("Ngày mai tôi đi học.", "明天我去上学。"),
    "ho": ("Tôi bị ho.", "我咳嗽。"),
    "da": ("Da của cô ấy rất đẹp.", "她的皮肤很好。"),
    "gỗ": ("Cái bàn này làm bằng gỗ.", "这张桌子是木头做的。"),
    "bụng": ("Tôi bị đau bụng.", "我肚子疼。"),
    "ngựa": ("Con ngựa đang chạy.", "马在跑。"),
    "ớt": ("Món này có ớt.", "这道菜有辣椒。"),
    "biểu tượng": ("Đây là biểu tượng của công ty.", "这是公司的标志。"),
    "chia sẻ": ("Cảm ơn bạn đã chia sẻ.", "谢谢你的分享。"),
    "phát triển": ("Kinh tế đang phát triển.", "经济正在发展。"),
    "công việc": ("Công việc của tôi rất bận.", "我的工作很忙。"),
    "thời gian": ("Tôi không có thời gian.", "我没有时间。"),
    "tiền": ("Tôi cần tiền để mua sách.", "我需要钱买书。"),
    "ngày": ("Hôm nay là một ngày đẹp.", "今天是美好的一天。"),
    "năm": ("Tôi học tiếng Việt được một năm.", "我学越南语一年了。"),
    "nhà": ("Nhà tôi ở gần đây.", "我家在这附近。"),
    "trường": ("Trường tôi ở Hà Nội.", "我的学校在河内。"),
    "thành phố": ("Thành phố này rất đẹp.", "这座城市很美。"),
    "câu hỏi": ("Tôi có một câu hỏi.", "我有一个问题。"),
    "vấn đề": ("Đây là một vấn đề lớn.", "这是一个大问题。"),
    "cách": ("Cách này rất tốt.", "这个方法很好。"),
    "điều": ("Điều này rất quan trọng.", "这一点很重要。"),
    "việc": ("Việc này rất khó.", "这件事很难。"),
    "cuộc sống": ("Cuộc sống ở đây rất yên bình.", "这里的生活很平静。"),
    "gia đình": ("Gia đình tôi có bốn người.", "我家有四口人。"),
    "mẹ": ("Mẹ tôi nấu cơm rất ngon.", "我妈妈做饭很好吃。"),
    "bố": ("Bố tôi là giáo viên.", "我爸爸是老师。"),
    "em": ("Em tôi đang học.", "我弟弟/妹妹在读书。"),
    "chị": ("Chị tôi làm việc ở Hà Nội.", "我姐姐在河内工作。"),
    "bà": ("Bà tôi rất khỏe.", "我奶奶身体很好。"),
    "con": ("Con tôi đang học.", "我的孩子在读书。"),
    "trẻ em": ("Trẻ em rất thích chơi.", "孩子们很喜欢玩。"),
    "học sinh": ("Học sinh đang học bài.", "学生们在学习。"),
    "sinh viên": ("Sinh viên học ở trường đại học.", "大学生在大学学习。"),
    "giáo viên": ("Giáo viên đang giảng bài.", "老师正在讲课。"),
    "bác sĩ": ("Bác sĩ đang khám bệnh.", "医生正在看病。"),
    "công nhân": ("Công nhân làm việc ở nhà máy.", "工人在工厂工作。"),
    "nông dân": ("Nông dân làm việc trên đồng.", "农民在田里工作。"),
    "nhà hàng": ("Nhà hàng này rất ngon.", "这家餐厅很好吃。"),
    "khách sạn": ("Tôi ở khách sạn này.", "我住在这家酒店。"),
    "bệnh viện": ("Bệnh viện ở gần đây.", "医院在这附近。"),
    "ngân hàng": ("Ngân hàng mở lúc 8 giờ.", "银行八点开门。"),
    "chợ": ("Tôi đi chợ mua rau.", "我去市场买菜。"),
    "siêu thị": ("Tôi mua thức ăn ở siêu thị.", "我在超市买食物。"),
    "công ty": ("Tôi làm việc ở công ty.", "我在公司工作。"),
    "trường học": ("Trường học ở gần nhà tôi.", "学校在我家附近。"),
    "thư viện": ("Tôi đọc sách ở thư viện.", "我在图书馆看书。"),
    "công viên": ("Trẻ em chơi ở công viên.", "孩子们在公园玩。"),
    "đường": ("Đường này rất đông.", "这条路很拥挤。"),
    "xe": ("Tôi đi xe buýt.", "我坐公交车。"),
    "xe đạp": ("Tôi đi xe đạp mỗi ngày.", "我每天骑自行车。"),
    "xe máy": ("Anh ấy đi xe máy.", "他骑摩托车。"),
    "ô tô": ("Ô tô này rất đắt.", "这辆车很贵。"),
    "máy bay": ("Máy bay bay lên cao.", "飞机飞得很高。"),
    "cơm": ("Tôi ăn cơm mỗi ngày.", "我每天吃饭。"),
    "phở": ("Tôi ăn phở vào buổi sáng.", "我早上吃河粉。"),
    "bánh mì": ("Tôi ăn bánh mì.", "我吃面包。"),
    "cà phê": ("Tôi uống cà phê.", "我喝咖啡。"),
    "nước": ("Tôi uống nước.", "我喝水。"),
    "sức khỏe": ("Sức khỏe rất quan trọng.", "健康很重要。"),
    "bệnh": ("Tôi bị bệnh.", "我生病了。"),
    "mưa": ("Hôm nay trời mưa.", "今天下雨。"),
    "nắng": ("Hôm nay trời nắng.", "今天晴天。"),
    "gió": ("Hôm nay có gió.", "今天有风。"),
    "mùa hè": ("Mùa hè ở đây rất nóng.", "这里的夏天很热。"),
    "mùa đông": ("Mùa đông ở đây rất lạnh.", "这里的冬天很冷。"),
    "thời tiết": ("Thời tiết hôm nay rất đẹp.", "今天天气很好。"),
    "trời": ("Trời hôm nay rất đẹp.", "今天天气很好。"),
    "hướng": ("Bạn đi về hướng nào?", "你往哪个方向走？"),
    "bộ": ("Bộ phim này rất hay.", "这部电影很好看。"),
    "bốn": ("Tôi có bốn quả táo.", "我有四个苹果。"),
    "bảy": ("Tôi có bảy quyển sách.", "我有七本书。"),
    "lần": ("Tôi đã đến Hà Nội hai lần.", "我去过河内两次。"),
    "cà vạt": ("Anh ấy đeo cà vạt.", "他打着领带。"),
    "văn phòng": ("Văn phòng của tôi ở tầng ba.", "我的办公室在三楼。"),
    "lực": ("Anh ấy có rất nhiều lực.", "他很有力量。"),
    "quả": ("Tôi ăn một quả táo.", "我吃一个苹果。"),
    "cuối": ("Cuối tuần tôi được nghỉ.", "周末我休息。"),
    "lông": ("Con mèo có lông trắng.", "猫有白色的毛。"),
    "hình dạng": ("Hình dạng này rất lạ.", "这个形状很奇怪。"),
    "ngón tay": ("Tôi bị đau ngón tay.", "我手指疼。"),
    "váy": ("Cô ấy mặc váy đẹp.", "她穿着漂亮的裙子。"),
    "tháng bảy": ("Tháng bảy ở Hà Nội rất nóng.", "河内的七月很热。"),
    "tháng ba": ("Tháng ba có hoa đào.", "三月有桃花。"),
    "ngày lễ": ("Ngày lễ tôi được nghỉ.", "假日我休息。"),
    "trang trại": ("Gia đình tôi có một trang trại.", "我家有一个农场。"),
    "cầu": ("Cây cầu này rất dài.", "这座桥很长。"),
    "thẻ": ("Tôi có thẻ ngân hàng.", "我有银行卡。"),
    "tối": ("Buổi tối tôi học tiếng Việt.", "晚上我学越南语。"),
    "hoạt động": ("Hoạt động này rất vui.", "这个活动很好玩。"),
    "môi": ("Môi cô ấy rất đỏ.", "她的嘴唇很红。"),
    "cao": ("Anh ấy cao hơn tôi.", "他比我高。"),
    "lưỡi": ("Tôi bị đau lưỡi.", "我舌头疼。"),
    "như nhau": ("Hai cái này giống như nhau.", "这两个一样。"),
    "tắt": ("Tắt đèn đi.", "把灯关掉。"),
    "bỏ lỡ": ("Tôi không muốn bỏ lỡ cơ hội.", "我不想错过机会。"),
    "cửa": ("Cửa nhà tôi bị hỏng.", "我家的门坏了。"),
    "vàng": ("Tôi thích màu vàng.", "我喜欢黄色。"),
    "súng": ("Cảnh sát có súng.", "警察有枪。"),
    "ngăn chặn": ("Chúng ta phải ngăn chặn anh ấy.", "我们必须阻止他。"),
    "dấu hiệu": ("Không có dấu hiệu gì.", "没有任何迹象。"),
    "thể": ("Tôi thích thể thao.", "我喜欢体育。"),
    "nhà ga": ("Nhà ga ở gần đây.", "车站在附近。"),
    "ống": ("Nước chảy qua ống.", "水流过管子。"),
    "thứ nhất": ("Đây là lần thứ nhất.", "这是第一次。"),
    "mắt": ("Mắt tôi bị đau.", "我眼睛疼。"),
    "mang lại": ("Du lịch mang lại nhiều niềm vui.", "旅行带来很多快乐。"),
}

TONE_MARKS = {0x300: "低降", 0x301: "高升", 0x309: "问声", 0x303: "紧升", 0x323: "重声"}

ENGLISH_GLOSS_WORDS = {
    "a", "an", "the", "as", "at", "be", "by", "for", "from", "have", "he", "her",
    "his", "i", "in", "it", "of", "on", "or", "she", "that", "they", "this", "to",
    "was", "we", "were", "what", "when", "where", "which", "who", "with", "you",
    "might", "inch", "bat", "word", "number", "some", "all", "not", "no", "yes",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def load_frequency_words() -> list[dict]:
    soup = BeautifulSoup(HTML_SOURCE.read_text(encoding="utf-8", errors="replace"), "lxml")
    table = soup.find("table")
    if not table:
        raise RuntimeError("No table found in common1000.html")
    result = []
    seen = set()
    for order, row in enumerate(table.find_all("tr")[1:], start=1):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) < 3:
            continue
        vietnamese, english = cells[1].strip(), cells[2].strip()
        if not vietnamese:
            continue
        key = normalize_key(vietnamese)
        if key in seen:
            continue
        # Drop obvious English contamination from the scraped table.
        if (
            not any(ord(char) > 127 for char in vietnamese)
            and vietnamese.lower() in ENGLISH_GLOSS_WORDS
            and english.lower() == vietnamese.lower()
        ):
            continue
        seen.add(key)
        result.append({"word": vietnamese, "english": english, "order": order})
    return result


def load_extra_words() -> list[dict]:
    result = []
    for order, line in enumerate(EXTRA_SOURCE.read_text(encoding="utf-8").splitlines(), start=1001):
        word = line.strip()
        if not word or word.startswith("#"):
            continue
        result.append({"word": word, "english": "", "order": order})
    return result


def load_tatoeba() -> list[tuple[str, str]]:
    if not TATOEBA_SOURCE.exists():
        return []
    sentences = []
    for line in bz2.open(TATOEBA_SOURCE, "rt", encoding="utf-8"):
        parts = line.rstrip("\n").split("\t", 2)
        if len(parts) == 3:
            sentences.append((parts[0], parts[2].strip()))
    return sentences


def find_tatoeba_example(word: str, sentences: list[tuple[str, str]]) -> tuple[str, str] | None:
    pattern = re.compile(r"(?<!\w)" + re.escape(word) + r"(?!\w)", re.IGNORECASE)
    best = None
    for sentence_id, text in sentences:
        if not (12 <= len(text) <= 90):
            continue
        if text[-1] not in ".?!":
            continue
        if not pattern.search(text):
            continue
        score = (0 if text.lower().startswith(word.lower()) else 1, len(text))
        if best is None or score < best[0]:
            best = (score, sentence_id, text)
    if not best:
        return None
    return best[1], best[2]


def clean_ipa(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().strip("[]")).strip()


def choose_example(result: dict, word: str) -> str:
    examples = []
    for meaning in result.get("meanings", []):
        example = (meaning.get("example") or "").strip()
        if example:
            examples.append(example)
    for example in examples:
        lower = example.lower()
        if word.lower() not in lower:
            continue
        if any(marker in example for marker in ("~", "…", "...", "→", "|")):
            continue
        if len(example) < 6 or len(example) > 90:
            continue
        return example
    return ""


def lookup_one(word: str) -> dict:
    session = requests.Session()
    last_error = None
    for attempt in range(1, 4):
        try:
            response = session.get(DICT_URL, params={"word": word, "lang": "vi"}, timeout=20)
            if response.status_code == 404:
                return {"ok": False, "reason": "404"}
            response.raise_for_status()
            data = response.json()
            results = data.get("results") or []
            if not results:
                return {"ok": False, "reason": "no-result"}
            result = results[0]
            pronunciations = result.get("pronunciations") or []
            if not pronunciations:
                return {"ok": False, "reason": "no-ipa"}
            hanoi = [
                item for item in pronunciations
                if "Hà-Nội" in (item.get("region") or "") or "Ha-Noi" in (item.get("region") or "")
            ]
            ipa = clean_ipa((hanoi or pronunciations)[0].get("ipa", ""))
            if not ipa:
                return {"ok": False, "reason": "empty-ipa"}
            meanings = result.get("meanings") or []
            pos = next((meaning.get("pos") for meaning in meanings if meaning.get("pos")), "")
            zh = [
                translation["translation"]
                for translation in result.get("translations", [])
                if translation.get("lang_code") == "zh" and translation.get("translation")
            ]
            en = next(
                (
                    meaning.get("definition")
                    for meaning in meanings
                    if meaning.get("definition_lang") == "en" and meaning.get("definition")
                ),
                "",
            )
            return {
                "ok": True,
                "ipa": ipa,
                "pos": pos,
                "zh": zh,
                "en": en,
                "example": choose_example(result, word),
            }
        except Exception as error:  # noqa: BLE001
            last_error = str(error)
            time.sleep(0.5 * attempt)
    return {"ok": False, "reason": last_error or "error"}


def translate_batch(texts: list[str], session: requests.Session, source_lang: str = "vi") -> list[str | None]:
    if not texts:
        return []
    last_error = None
    for attempt in range(1, 4):
        try:
            response = session.post(
                TRANSLATE_URL,
                params={"from": source_lang, "to": "zh-Hans", "isEnterpriseClient": "false"},
                json=texts,
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                timeout=60,
            )
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
            data = response.json()
            if len(data) != len(texts):
                raise RuntimeError(f"length mismatch {len(data)} != {len(texts)}")
            return [item["translations"][0]["text"] if item.get("translations") else None for item in data]
        except Exception as error:  # noqa: BLE001
            last_error = str(error)
            time.sleep(1.0 * attempt)
    print(f"  translation batch failed: {last_error}")
    return [None] * len(texts)


def clean_translation(value: str) -> str:
    value = re.sub(r"\s+", " ", (value or "").strip())
    value = value.strip("“”\"' ")
    value = value.rstrip("：:，,；;。.")
    return value


def strip_tones(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(char for char in decomposed if ord(char) not in TONE_MARKS)


def syllable_tone(value: str) -> str:
    for char in unicodedata.normalize("NFD", value):
        if ord(char) in TONE_MARKS:
            return TONE_MARKS[ord(char)]
    return "平"


def pinyin_approx_syllable(syllable: str) -> str:
    tone = syllable_tone(syllable)
    base = unicodedata.normalize("NFC", strip_tones(syllable)).lower()

    final = ""
    for coda in ("ch", "nh", "ng", "c", "t", "p", "m", "n"):
        if base.endswith(coda):
            final = coda
            base = base[: -len(coda)]
            break

    # Map Vietnamese letters to a readable Mandarin-like approximation.
    base = base.replace("ă", "a").replace("â", "e")
    base = base.replace("ê", "e").replace("ô", "o").replace("ơ", "o").replace("ư", "u")
    base = base.replace("d", "z").replace("đ", "d")
    base = base.replace("ngh", "ng").replace("tr", "zh")
    base = base.replace("gi", "z").replace("kh", "k").replace("ph", "f")
    base = base.replace("th", "t").replace("qu", "kw")
    base = base.replace("s", "x").replace("r", "z")

    final_map = {"ch": "k", "nh": "n", "ng": "ng", "c": "k", "t": "t", "p": "p", "m": "m", "n": "n"}
    return f"{base}{final_map.get(final, final)}（{tone}）"


def homophone_approx(word: str) -> str:
    syllables = [part for part in re.split(r"\s+", word.strip()) if part]
    return " · ".join(pinyin_approx_syllable(part) for part in syllables)


def has_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value or "")


def mymemory_lookup(word: str, session: requests.Session) -> tuple[str, str | None]:
    last_error = None
    for attempt in range(1, 4):
        try:
            response = session.get(
                "https://api.mymemory.translated.net/get",
                params={"q": word, "langpair": "vi|zh-CN"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("quotaFinished"):
                return "", "quota"
            value = html.unescape((data.get("responseData") or {}).get("translatedText") or "")
            value = zhconv.convert(value, "zh-cn").strip()
            if value and has_cjk(value) and "MYMEMORY WARNING" not in value.upper():
                return value, None
            return "", None
        except Exception as error:  # noqa: BLE001
            last_error = str(error)
            time.sleep(0.5 * attempt)
    return "", last_error


def clean_meaning(value: str) -> str:
    value = clean_translation(value)
    if not value:
        return value
    # Keep the first compact gloss; avoid an entire definition sentence.
    for separator in ("；", ";", "，", ","):
        if separator in value:
            first = value.split(separator, 1)[0].strip()
            if first:
                value = first
                break
    return value[:28].strip()


def clean_english_sense(value: str) -> str:
    value = re.sub(r"\([^)]*\)", "", value or "")
    value = re.split(r"[;,/]", value)[0].strip()
    value = re.sub(r"^(a|an|the|to)\s+", "", value, flags=re.IGNORECASE)
    return value[:60].strip()


def meaning_for(
    word: str,
    item: dict,
    translation_cache: dict,
    definition_cache: dict,
    english_sense_cache: dict,
    simple_gloss_cache: dict,
    mymemory_cache: dict,
) -> str:
    if word in MANUAL_ZH:
        return MANUAL_ZH[word]
    simple_gloss = clean_english_sense(item.get("english") or "")
    if simple_gloss:
        gloss_zh = clean_meaning(simple_gloss_cache.get(simple_gloss, ""))
        if gloss_zh and has_cjk(gloss_zh):
            return gloss_zh
    edge = clean_meaning(translation_cache.get(word, ""))
    if edge and has_cjk(edge) and not any(
        marker in edge for marker in ("另一种拼写", "的简称", "大写字母", "的缩写")
    ):
        return edge
    api_zh = [clean_meaning(value) for value in item.get("zh", []) if clean_meaning(value)]
    api_zh = [value for value in api_zh if has_cjk(value)]
    if api_zh:
        return api_zh[0]
    memory = clean_meaning(mymemory_cache.get(word, ""))
    if memory and has_cjk(memory):
        return memory
    english_sense = clean_english_sense(item.get("en") or "")
    if english_sense:
        sense_zh = clean_meaning(english_sense_cache.get(english_sense, ""))
        if sense_zh and has_cjk(sense_zh):
            return sense_zh
    english = item.get("en", "")
    if english:
        english_zh = clean_meaning(definition_cache.get(english, ""))
        if english_zh and has_cjk(english_zh):
            return english_zh
    return ""


def example_for(word: str, pos: str, meaning: str, api_example: str, translated_example: str | None) -> tuple[str, str]:
    meaning = meaning.strip("。！？；;，, ")
    if word in MANUAL_EXAMPLES:
        return MANUAL_EXAMPLES[word]

    seed = sum(ord(char) for char in word) % 1000

    noun_frames = [
        ("Đây là {word} của tôi.", "这是我的{meaning}。"),
        ("Tôi cần {word}.", "我需要{meaning}。"),
        ("{word} này rất quan trọng.", "这个{meaning}很重要。"),
        ("Tôi thích {word}.", "我喜欢{meaning}。"),
        ("Tôi đang nói về {word}.", "我在说{meaning}。"),
        ("Bạn có {word} không?", "你有{meaning}吗？"),
    ]
    verb_frames = [
        ("Tôi muốn {word}.", "我想{meaning}。"),
        ("Bạn có thể {word} không?", "你能{meaning}吗？"),
        ("Hôm nay tôi {word}.", "今天我{meaning}。"),
        ("Anh ấy đang {word}.", "他正在{meaning}。"),
        ("Chúng ta hãy {word}.", "我们{meaning}吧。"),
        ("Tôi phải {word}.", "我必须{meaning}。"),
    ]
    adjective_frames = [
        ("Cái này rất {word}.", "这个很{meaning}。"),
        ("Anh ấy trông rất {word}.", "他看起来很{meaning}。"),
        ("Tôi cảm thấy {word}.", "我感觉很{meaning}。"),
        ("Món này rất {word}.", "这道菜很{meaning}。"),
        ("Hôm nay trời rất {word}.", "今天天气很{meaning}。"),
    ]

    frames = None
    if pos == "名词":
        frames = noun_frames
    elif pos == "动词":
        frames = verb_frames
    elif pos == "形容词":
        frames = adjective_frames
    if not frames:
        return f'Từ này là "{word}".', f"这个词是“{meaning}”。"
    vi_template, zh_template = frames[seed % len(frames)]
    return vi_template.format(word=word), zh_template.format(meaning=meaning)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="ignore caches")
    parser.add_argument("--target", type=int, default=1000, help="minimum total entries")
    args = parser.parse_args()

    textbook = json.loads(TEXTBOOK_SOURCE.read_text(encoding="utf-8"))
    existing_keys = {normalize_key(item["word"]) for item in textbook}
    frequency = load_frequency_words()
    extras = load_extra_words()
    candidates = []
    seen = set(existing_keys)
    for item in frequency + extras:
        key = normalize_key(item["word"])
        if key in seen:
            continue
        seen.add(key)
        candidates.append(item)
    save_json(SEED_OUTPUT, {"frequency": frequency, "extra": extras, "candidates": candidates})
    print(f"textbook={len(textbook)} frequency={len(frequency)} extra={len(extras)} candidates={len(candidates)}")

    lookup_cache = {} if args.refresh else load_json(LOOKUP_CACHE, {})
    todo = [item for item in candidates if normalize_key(item["word"]) not in lookup_cache]
    print(f"lookup cache hits: {len(candidates) - len(todo)}, requests: {len(todo)}")
    if todo:
        completed = 0
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(lookup_one, item["word"]): item
                for item in todo
            }
            for future in as_completed(futures):
                item = futures[future]
                try:
                    lookup_cache[normalize_key(item["word"])] = future.result()
                except Exception as error:  # noqa: BLE001
                    lookup_cache[normalize_key(item["word"])] = {"ok": False, "reason": str(error)}
                completed += 1
                if completed % 50 == 0:
                    save_json(LOOKUP_CACHE, lookup_cache)
                    print(f"  dictionary {completed}/{len(todo)}")
        save_json(LOOKUP_CACHE, lookup_cache)

    usable = []
    for item in candidates:
        lookup = lookup_cache.get(normalize_key(item["word"]))
        if not lookup or not lookup.get("ok"):
            continue
        usable.append({**item, **lookup})

    translation_cache = {} if args.refresh else load_json(TRANSLATION_CACHE, {})
    texts = [item["word"] for item in usable]
    texts = list(dict.fromkeys(text for text in texts if text))
    missing_texts = [text for text in texts if text not in translation_cache]
    print(f"translation cache hits: {len(texts) - len(missing_texts)}, requests: {len(missing_texts)}")
    session = requests.Session()
    for start in range(0, len(missing_texts), 40):
        batch = missing_texts[start:start + 40]
        translations = translate_batch(batch, session)
        for text, translation in zip(batch, translations):
            if translation:
                translation_cache[text] = translation
        if start % 200 == 0:
            save_json(TRANSLATION_CACHE, translation_cache)
            print(f"  translation {min(start + 40, len(missing_texts))}/{len(missing_texts)}")
        time.sleep(0.1)
    save_json(TRANSLATION_CACHE, translation_cache)

    definition_cache = {} if args.refresh else load_json(DEFINITION_CACHE, {})
    english_texts = list(dict.fromkeys(item.get("en", "") for item in usable if item.get("en")))
    missing_definitions = [text for text in english_texts if text not in definition_cache]
    print(f"definition cache hits: {len(english_texts) - len(missing_definitions)}, requests: {len(missing_definitions)}")
    for start in range(0, len(missing_definitions), 40):
        batch = missing_definitions[start:start + 40]
        translations = translate_batch(batch, session, source_lang="en")
        for text, translation in zip(batch, translations):
            if translation:
                definition_cache[text] = translation
        if start % 200 == 0:
            save_json(DEFINITION_CACHE, definition_cache)
            print(f"  definitions {min(start + 40, len(missing_definitions))}/{len(missing_definitions)}")
        time.sleep(0.1)
    save_json(DEFINITION_CACHE, definition_cache)

    simple_gloss_cache = {} if args.refresh else load_json(SIMPLE_GLOSS_CACHE, {})
    simple_glosses = list(
        dict.fromkeys(
            clean_english_sense(item.get("english") or "")
            for item in usable
            if clean_english_sense(item.get("english") or "")
        )
    )
    missing_glosses = [text for text in simple_glosses if text not in simple_gloss_cache]
    print(f"simple gloss cache hits: {len(simple_glosses) - len(missing_glosses)}, requests: {len(missing_glosses)}")
    for start in range(0, len(missing_glosses), 40):
        batch = missing_glosses[start:start + 40]
        translations = translate_batch(batch, session, source_lang="en")
        for text, translation in zip(batch, translations):
            if translation:
                simple_gloss_cache[text] = translation
        if start % 200 == 0:
            save_json(SIMPLE_GLOSS_CACHE, simple_gloss_cache)
            print(f"  glosses {min(start + 40, len(missing_glosses))}/{len(missing_glosses)}")
        time.sleep(0.1)
    save_json(SIMPLE_GLOSS_CACHE, simple_gloss_cache)

    english_sense_cache = {} if args.refresh else load_json(ENGLISH_SENSE_CACHE, {})
    english_senses = list(
        dict.fromkeys(
            clean_english_sense(item.get("en") or item.get("english") or "")
            for item in usable
            if clean_english_sense(item.get("en") or item.get("english") or "")
        )
    )
    missing_senses = [text for text in english_senses if text not in english_sense_cache]
    print(f"english sense cache hits: {len(english_senses) - len(missing_senses)}, requests: {len(missing_senses)}")
    for start in range(0, len(missing_senses), 40):
        batch = missing_senses[start:start + 40]
        translations = translate_batch(batch, session, source_lang="en")
        for text, translation in zip(batch, translations):
            if translation:
                english_sense_cache[text] = translation
        if start % 200 == 0:
            save_json(ENGLISH_SENSE_CACHE, english_sense_cache)
            print(f"  senses {min(start + 40, len(missing_senses))}/{len(missing_senses)}")
        time.sleep(0.1)
    save_json(ENGLISH_SENSE_CACHE, english_sense_cache)

    mymemory_cache = {} if args.refresh else load_json(MYMEMORY_CACHE, {})
    mymemory_words = list(dict.fromkeys(item["word"] for item in usable))
    missing_memory = [
        word for word in mymemory_words
        if word not in mymemory_cache and word not in MANUAL_ZH
    ]
    print(f"mymemory cache hits: {len(mymemory_words) - len(missing_memory)}, requests: {len(missing_memory)}")
    memory_session = requests.Session()
    quota_hit = False
    for index, word in enumerate(missing_memory, start=1):
        if quota_hit:
            break
        value, error = mymemory_lookup(word, memory_session)
        if error == "quota":
            quota_hit = True
            print("  MyMemory quota reached; using dictionary/Edge fallbacks for the rest.")
            break
        if value:
            mymemory_cache[word] = value
        if index % 25 == 0:
            save_json(MYMEMORY_CACHE, mymemory_cache)
            print(f"  mymemory {index}/{len(missing_memory)}")
        time.sleep(0.08)
    save_json(MYMEMORY_CACHE, mymemory_cache)

    tatoeba_sentences = load_tatoeba()
    tatoeba_examples = {} if args.refresh else load_json(TATOEBA_EXAMPLE_CACHE, {})
    if tatoeba_sentences:
        missing_examples = [
            item["word"]
            for item in usable
            if item["word"] not in MANUAL_EXAMPLES and item["word"] not in tatoeba_examples
        ]
        print(f"tatoeba example cache hits: {len(usable) - len(missing_examples)}, searches: {len(missing_examples)}")
        for index, word in enumerate(missing_examples, start=1):
            found = find_tatoeba_example(word, tatoeba_sentences)
            if found:
                sentence_id, text = found
                tatoeba_examples[word] = {"id": sentence_id, "text": text}
            if index % 100 == 0:
                save_json(TATOEBA_EXAMPLE_CACHE, tatoeba_examples)
                print(f"  tatoeba {index}/{len(missing_examples)}")
        save_json(TATOEBA_EXAMPLE_CACHE, tatoeba_examples)

    tatoeba_translations = {} if args.refresh else load_json(TATOEBA_TRANSLATION_CACHE, {})
    tatoeba_texts = list(
        dict.fromkeys(
            item["text"]
            for word, item in tatoeba_examples.items()
            if word not in MANUAL_EXAMPLES and item.get("text")
        )
    )
    missing_tatoeba = [text for text in tatoeba_texts if text not in tatoeba_translations]
    print(f"tatoeba translation cache hits: {len(tatoeba_texts) - len(missing_tatoeba)}, requests: {len(missing_tatoeba)}")
    for start in range(0, len(missing_tatoeba), 40):
        batch = missing_tatoeba[start:start + 40]
        translations = translate_batch(batch, session, source_lang="vi")
        for text, translation in zip(batch, translations):
            if translation:
                tatoeba_translations[text] = translation
        if start % 200 == 0:
            save_json(TATOEBA_TRANSLATION_CACHE, tatoeba_translations)
            print(f"  tatoeba translations {min(start + 40, len(missing_tatoeba))}/{len(missing_tatoeba)}")
        time.sleep(0.1)
    save_json(TATOEBA_TRANSLATION_CACHE, tatoeba_translations)

    general_entries = []
    skipped_translation = 0
    skipped_ipa = 0
    for item in usable:
        word = item["word"]
        meaning = meaning_for(
            word,
            item,
            translation_cache,
            definition_cache,
            english_sense_cache,
            simple_gloss_cache,
            mymemory_cache,
        )
        if not meaning:
            skipped_translation += 1
            continue
        ipa = item.get("ipa", "")
        if not ipa:
            skipped_ipa += 1
            continue
        pos = POS_MAP.get(item.get("pos", ""), "词汇")
        example_source = "生成例句"
        if word in MANUAL_EXAMPLES:
            example, example_zh = MANUAL_EXAMPLES[word]
            example_source = "手写例句"
        else:
            tatoeba_item = tatoeba_examples.get(word)
            tatoeba_zh = tatoeba_translations.get(tatoeba_item["text"]) if tatoeba_item else ""
            if tatoeba_item and tatoeba_zh and has_cjk(tatoeba_zh):
                example = tatoeba_item["text"]
                example_zh = zhconv.convert(tatoeba_zh, "zh-cn").strip()
                example_source = f"Tatoeba #{tatoeba_item['id']}"
            else:
                example, example_zh = example_for(word, pos, meaning, "", None)
        general_entries.append(
            {
                "id": f"gen-{len(general_entries) + 1:04d}",
                "word": word,
                "pos": pos,
                "ipa": ipa,
                "homophone": homophone_approx(word),
                "meaning": meaning,
                "example": example,
                "exampleZh": example_zh,
                "exampleSource": example_source,
                "lesson": 100,
                "topic": "通用高频",
                "source": "通用高频词表",
            }
        )
        if len(general_entries) + len(textbook) >= max(args.target, len(textbook) + 1):
            break

    merged = textbook + general_entries
    # Final guard against duplicates.
    final = []
    final_seen = set()
    for item in merged:
        key = normalize_key(item["word"])
        if key in final_seen:
            continue
        final_seen.add(key)
        final.append(item)

    OUTPUT.write_text(json.dumps(final, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"OK: {len(final)} total entries "
        f"({len(textbook)} textbook + {len(final) - len(textbook)} general); "
        f"skipped zh={skipped_translation}, ipa={skipped_ipa}"
    )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
