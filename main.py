import json
import os
import random as rd
import sqlite3

from nicegui import ui

current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'sayings.json')

try:
    with open(file_path, "r", encoding="utf-8") as f:
        a = json.load(f)
    if not isinstance(a, list):
        a = []
except Exception:
    a = []

# SQLite DB (store quotes persistently)
db_path = os.path.join(current_dir, 'sayings.db')

def get_conn():
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY,
            text TEXT,
            category TEXT,
            tags TEXT,
            vibe TEXT,
            author TEXT,
            source TEXT,
            attribution_status TEXT
        )
    ''')
    conn.commit()
    c.execute('SELECT COUNT(*) FROM quotes')
    if c.fetchone()[0] == 0:
        # 如果数据库为空，则将现有 JSON 数据导入
        for item in a:  # type: ignore # noqa: F821
            c.execute(
                'INSERT OR IGNORE INTO quotes (id,text,category,tags,vibe,author,source,attribution_status) VALUES (?,?,?,?,?,?,?,?)',
                (
                    item.get('id'),
                    item.get('text'),
                    item.get('category'),
                    json.dumps(item.get('tags') or []),
                    item.get('vibe'),
                    item.get('author'),
                    item.get('source'),
                    item.get('attribution_status'),
                ),
            )
        conn.commit()
    conn.close()

init_db()

# 临时结果容器（多数操作改为局部变量）
b = []

def get_text():
    """返回随机条目，格式与历史代码保持一致：
    (id, text, category, author, source, attribution_status, tags)
    当数据为空时返回占位信息。
    """
    # 优先从数据库随机选取一条
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1')
        row = c.fetchone()
        conn.close()
        if not row:
            return None, '暂无名言，点击“随机浏览”添加或加载数据。', '', '', '', ''
        return row['id'], row['text'], row['category'], row['author'], row['source'], row['attribution_status']
    except Exception:  # noqa: BLE001
        # 回退：如果 DB 出问题，使用内存中的 JSON 列表
        if not a:
            return None, '暂无名言，点击“随机浏览”添加或加载数据。', '', '', '', ''
        pos = rd.choice(a)
        return pos.get('id'), pos.get('text', ''), pos.get('category', ''), pos.get('author', ''), pos.get('source', ''), pos.get('attribution_status', '')


def show_random():
    _id, text, category, author, source, attribution_status = get_text()
    if _id is None and text:
        ui.notify(text, color='warning')
    label_text.set_text(text)
    label_author.set_text(f"作者：{author}（{attribution_status}）" if author or attribution_status else '')
    label_source.set_text(f"来源：{source}" if source else '')
    label_category.set_text(f"类别：{category}" if category else '')

with ui.header().classes(replace='row items-center justify-between px-6 py-3 bg-white shadow-sm') as header, ui.tabs().classes('gap-2 bg-slate-100 p-1 rounded-full') as tabs:
    ui.label('AsaSaying').classes('text-2xl font-bold text-slate-900')
    ui.tab('随机浏览').classes('px-4 py-2 rounded-full text-sm text-slate-700 hover:text-slate-900 hover:bg-white transition-colors')
    ui.tab('上传分享').classes('px-4 py-2 rounded-full text-sm text-slate-700 hover:text-slate-900 hover:bg-white transition-colors')
    ui.tab('索引查找').classes('px-4 py-2 rounded-full text-sm text-slate-700 hover:text-slate-900 hover:bg-white transition-colors')
    ui.tab('支持作者').classes('px-4 py-2 rounded-full text-sm text-slate-700 hover:text-slate-900 hover:bg-white transition-colors')

with ui.footer(value=True) as footer:
    ui.label()

with ui.page_sticky(position='bottom-right', x_offset=20, y_offset=20):
    ui.button(on_click=footer.toggle, icon='contact_support').props('fab')

with ui.tab_panels(tabs, value='随机浏览').classes('w-full min-h-screen bg-slate-50 py-8') as weblist:
    with ui.tab_panel('随机浏览'):  # noqa: SIM117
        with ui.column().classes('w-full max-w-4xl mx-auto p-8 md:p-12 rounded-3xl border border-slate-200 bg-white shadow-lg hover:shadow-2xl transition-all duration-300 items-center'):
            ui.label('随机浏览').classes('text-2xl font-semibold text-slate-900')
            ui.separator().classes('my-3 w-full')
            label_text = ui.label('点击按钮以显示随机名言').classes('text-xl font-semibold text-slate-800 text-center leading-relaxed tracking-wide')
            ui.separator().classes('my-3 w-full')
            label_author = ui.label('').classes('text-center leading-relaxed')
            label_source = ui.label('').classes('text-center leading-relaxed')
            label_category = ui.label('').classes('text-center leading-relaxed')
            ui.separator().classes('my-3 w-full')
            btn = ui.button('🎲 随缘', on_click=show_random).classes('mt-6 px-6 py-3 text-lg rounded-full shadow-md bg-gradient-to-r from-indigo-500 to-blue-500 text-white hover:scale-105 transition-transform').props('elevated')

    with ui.tab_panel('上传分享'):  # noqa: SIM117
        with ui.column().classes('w-full max-w-4xl mx-auto p-8 md:p-12 rounded-3xl border border-slate-200 bg-white shadow-lg hover:shadow-2xl transition-all duration-300 items-center'):
            # 从数据库读取当前条目数以显示下一个 id（更可靠）
            try:
                conn = get_conn()
                c = conn.cursor()
                c.execute('SELECT COUNT(*) FROM quotes')
                oldui = c.fetchone()[0]
                conn.close()
            except Exception:  # noqa: BLE001
                oldui = len(a) # type: ignore  # noqa: F821
            newui = oldui + 1
            ui.label('ui：'+ str(newui)).classes('text-sm text-slate-500')
            content = ui.textarea(label='正文', placeholder='在此输入要分享的名言或段落（支持多行）', value='').props('autogrow').classes('w-full max-w-xl')
            writer = ui.textarea(label='作者名字', placeholder='在此输入作者名字（默认佚名）', value='').props('autogrow').classes('w-full max-w-xl')
            new_source = ui.textarea(label='来源', placeholder='在此输入语段出处，如《我与地坛》或“自创”，默认“网络流传”', value='').props('autogrow').classes('w-full max-w-xl')
            def upload_handler():
                text = content.value.strip() # type: ignore
                if text == "": # type: ignore
                    ui.notify("正文不能为空！", color="negative")
                    return
                name = writer.value.strip() or '佚名' # type: ignore
                attribution_status = 'confirmed' if writer.value.strip() else 'anonymous' # type: ignore
                category = gender_put.value or ''
                if new_source.value.strip() != "":
                    source_val = new_source.value.strip()
                else:
                    source_val = '网络流传'
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute('INSERT INTO quotes (text,category,tags,vibe,author,source,attribution_status) VALUES (?,?,?,?,?,?,?)', (
                        text,
                        category,
                        json.dumps([]),
                        '',
                        name,
                        source_val,
                        attribution_status,
                    ))
                    conn.commit()
                    last_id = c.lastrowid
                    conn.close()
                    ui.notify(f'已上传（id={last_id}）', color='positive')
                    # 清空输入
                    content.set_value('')
                    writer.set_value('')
                    new_source.set_value('')
                    ui.navigate.reload()
                    return last_id, name, attribution_status, text
                except Exception as e:
                    ui.notify(f'上传失败：{e}', color='negative')
                    return
            ui.separator().classes('my-3 w-full')
            ui.label("类别").classes('text-base font-medium text-slate-700 text-center')
            gender_put = ui.radio(['扎心现实', '豁达解压',"治愈清醒","人间清醒","摆烂哲学","治愈温柔"], value=None)
            ui.button('上传', on_click=upload_handler).classes('mt-6 px-6 py-2 text-base rounded-lg shadow-sm bg-gradient-to-r from-green-500 to-emerald-500 text-white hover:scale-105 transition-transform').props('elevated')
    with ui.tab_panel('索引查找'):
        with ui.column().classes('w-full max-w-4xl mx-auto p-8 md:p-12 rounded-3xl border border-slate-200 bg-white shadow-lg hover:shadow-2xl transition-all duration-300 items-center'):
            ui.label("类别").classes('text-base font-medium text-slate-700 text-center')
            gender_get = ui.radio(['扎心现实', '豁达解压', "治愈清醒", "人间清醒", "摆烂哲学", "治愈温柔"], value=None)
            findbtn = ui.button('刷新').classes('mt-6 px-5 py-2 text-base rounded-lg shadow-sm bg-gradient-to-r from-indigo-500 to-blue-500 text-white hover:scale-105 transition-transform').props('elevated')
            # 正确的用法：为按钮注册点击回调，通知显示 radio 的当前值（使用 .value）
            def on_find_click():
                ui.notify(gender_get.value or '未选择类别', color='positive')
                return gender_get.value

            def find():
                text_type = on_find_click()
                if not text_type:
                    results_label.set_text('未选择类别')
                    return
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute('SELECT text,author,source FROM quotes WHERE category=? ORDER BY id', (text_type,))
                    rows = c.fetchall()
                    conn.close()
                except Exception:
                    rows = []
                if rows:
                    parts = []
                    for r in rows:
                        t = r['text']
                        meta = []
                        if r['author']:
                            meta.append(f"作者：{r['author']}")
                        if r['source']:
                            meta.append(f"来源：{r['source']}")
                        if meta:
                            parts.append(t + '\n' + ' · '.join(meta))
                        else:
                            parts.append(t)
                    results_label.set_text('\n\n'.join(parts))
                else:
                    results_label.set_text('无匹配结果')

            findbtn.on('click', find)
        with ui.column().classes('w-full max-w-4xl mx-auto p-6 md:p-8 rounded-3xl border border-slate-200 bg-white shadow-lg hover:shadow-2xl transition-all duration-300 items-start'):
            ui.label("搜索结果").classes('text-lg font-semibold text-slate-800')
            results_label = ui.label('').classes('whitespace-pre-wrap text-center p-4 max-h-64 overflow-auto bg-slate-50 rounded-lg w-full')

    with ui.tab_panel('支持作者'):
        with ui.column().classes('text-center w-full max-w-4xl mx-auto p-8 md:p-12 rounded-3xl border border-slate-200 bg-white shadow-lg hover:shadow-2xl transition-all duration-300 items-start gap-3'):
            ui.label("如果你觉得这里收集的句子刚好戳中情绪、偶尔能治愈片刻。欢迎随缘投喂！").classes('text-center text-lg text-slate-800')
                
            ui.label("os：电子喵喵也需要投喂的^__^").classes('text-center text-slate-500')

            ui.label("不投喂也完全没关系，照常免费浏览所有内容。").classes('text-center text-lg text-slate-800')
            ui.label("唯一许愿：多来逛逛，常点开「随机浏览」🎲").classes('text-center text-lg text-slate-800')

            ui.separator().classes('my-3 w-full')

            ui.label("禁止大额投喂，量力而行最重要").classes('text-center text-lg text-slate-800')
            ui.label("os：电子喵喵也会吃撑的").classes('text-center text-slate-500')

            ui.label("如果想要投喂，可以私信作者获取通道：jade_cyan@qq.com").classes('text-base text-slate-600 mt-4')

ui.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8080)),
    show=False,
    dark=None
)