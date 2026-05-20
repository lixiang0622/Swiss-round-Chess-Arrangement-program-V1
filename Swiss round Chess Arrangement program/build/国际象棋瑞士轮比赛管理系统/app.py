import streamlit as st
import pandas as pd
import random
import json
import io
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.table import Table

# --- 配置 Matplotlib 中文字体 ---
try:
    plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS', 'PingFang SC', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# ==========================================
# 0. 国际化字典 (i18n)
# ==========================================
TRANS = {
    "CN": {
        "title": "♟️ 国际象棋瑞士轮赛事管理系统 Pro",
        "sidebar_title": "设置 & 菜单",
        "lang_select": "语言 / Language",
        "tab1": "1. 选手报名",
        "tab2": "2. 比赛对阵",
        "tab3": "3. 排名与裁判",
        "match_name": "比赛名称",
        "rounds": "总轮数",
        "team_mode": "启用团体计分",
        "add_player": "添加选手",
        "import_excel": "从 Excel 导入",
        "download_tpl": "下载 Excel 模板",
        "start_btn": "🚀 锁定名单并开始比赛",
        "reset_btn": "⚠️ 重置比赛",
        "status_wait": "等待开始",
        "status_round": "第 {} / {} 轮",
        "pairings_header": "当前对阵表",
        "quick_input": "比分录入控制台",
        "select_match": "选择台次进行录入",
        "btn_w_win": "白胜 (1-0)",
        "btn_b_win": "黑胜 (0-1)",
        "btn_draw": "和棋 (½-½)",
        "btn_w_abs": "白弃权 (0-1F)",
        "btn_b_abs": "黑弃权 (1F-0)",
        "btn_db_abs": "双弃权 (0-0)",
        "commit_round": "✅ 结算本轮 -> 下一轮",
        "rank_header": "实时排名",
        "referee_action": "裁判操作",
        "referee_target": "选择选手",
        "penalty_score": "扣分/加分 (负数为扣分)",
        "penalty_reason": "原因",
        "apply_penalty": "执行判罚",
        "dq_check": "彻底删除/退赛 (DQ)",
        "dq_btn": "执行退赛",
        "requalify_btn": "恢复资格",
        "download_report": "📥 下载本轮报表 (PDF/Img)",
        "game_over": "🎉 比赛结束！",
        "final_report": "下载最终汇总报告 (PDF)",
        "name": "姓名", "sid": "学号", "team": "队伍", "gender": "性别",
        "score": "积分", "sb": "对手分", "wins": "胜", "rank": "排名",
        "status": "状态", "table": "台次", "white": "白方", "black": "黑方",
        "result": "结果"
    },
    "EN": {
        "title": "♟️ Swiss Chess Tournament Manager Pro",
        "sidebar_title": "Settings & Menu",
        "lang_select": "Language / 语言",
        "tab1": "1. Registration",
        "tab2": "2. Pairings",
        "tab3": "3. Standings & Referee",
        "match_name": "Tournament Name",
        "rounds": "Rounds",
        "team_mode": "Enable Team Scoring",
        "add_player": "Add Player",
        "import_excel": "Import from Excel",
        "download_tpl": "Download Template",
        "start_btn": "🚀 Lock & Start",
        "reset_btn": "⚠️ Reset Tournament",
        "status_wait": "Waiting to Start",
        "status_round": "Round {} / {}",
        "pairings_header": "Current Pairings",
        "quick_input": "Score Input Console",
        "select_match": "Select Match to Score",
        "btn_w_win": "White Win (1-0)",
        "btn_b_win": "Black Win (0-1)",
        "btn_draw": "Draw (½-½)",
        "btn_w_abs": "W Forfeit (0-1F)",
        "btn_b_abs": "B Forfeit (1F-0)",
        "btn_db_abs": "Both Forfeit (0-0)",
        "commit_round": "✅ Commit Round -> Next",
        "rank_header": "Live Standings",
        "referee_action": "Referee Actions",
        "referee_target": "Select Player",
        "penalty_score": "Penalty/Bonus Points",
        "penalty_reason": "Reason",
        "apply_penalty": "Apply Penalty",
        "dq_check": "Disqualify/Remove (DQ)",
        "dq_btn": "Disqualify",
        "requalify_btn": "Re-qualify",
        "download_report": "📥 Download Round Report",
        "game_over": "🎉 Tournament Finished!",
        "final_report": "Download Final Report (PDF)",
        "name": "Name", "sid": "ID", "team": "Team", "gender": "Gender",
        "score": "Pts", "sb": "SB", "wins": "W", "rank": "Rank",
        "status": "Status", "table": "Table", "white": "White", "black": "Black",
        "result": "Result"
    }
}

# ==========================================
# 1. 核心逻辑层 (Model) - 保持与之前一致
# ==========================================

class Player:
    def __init__(self, name, student_id="", team="", gender="", category=""):
        self.name = name
        self.student_id = student_id
        self.team = team
        self.gender = gender
        self.category = category
        self.number = 0
        self.score = 0.0
        self.opponents = set()
        self.matches = [] # [{'round':1, 'opponent':'Name', 'color':'W', 'result':1, 'note':''}]
        self.wins = 0
        self.draws = 0
        self.losses = 0
        self.sonneborn_berger = 0.0
        self.bye = False
        self.color_history = []
        self.absent_streak = 0
        self.disqualified = False
        self.adjustments = []
        self.rank = 0

    def add_result(self, opponent_name, score, color, round_no, note=""):
        self.matches.append({'round': round_no, 'opponent': opponent_name, 'color': color, 'result': score, 'note': note})
        if opponent_name != "BYE": self.opponents.add(opponent_name)
        if color: self.color_history.append(color)
        self.score += score
        if score == 1: self.wins += 1
        elif score == 0.5: self.draws += 1
        else: self.losses += 1
        if "缺席" in note or "Forfeit" in note: self.absent_streak += 1
        else: self.absent_streak = 0

    def calculate_sb(self, all_players_dict):
        sb = 0.0
        for m in self.matches:
            opp = m['opponent']
            if opp == "BYE" or opp not in all_players_dict: continue
            opp_obj = all_players_dict[opp]
            if m['result'] == 1: sb += opp_obj.score
            elif m['result'] == 0.5: sb += 0.5 * opp_obj.score
        self.sonneborn_berger = sb

    def get_color_balance(self):
        return self.color_history.count('W') - self.color_history.count('B')

class TournamentEngine:
    def __init__(self):
        self.players = []
        self.rounds_total = 5
        self.current_round = 0
        self.pairings = [] # [(p1, p2, color)]
        self.results = {} # {index: (s1, s2, note)}
        self.history = []
        self.use_teams = False
        self.is_started = False
        self.meta = {"name": "Tournament"}

    def add_player(self, name, student_id="", team="", gender="", category=""):
        name_check = name
        cnt = 1
        existing = [p.name for p in self.players]
        while name_check in existing:
            cnt += 1
            name_check = f"{name} ({cnt})"
        p = Player(name_check, student_id, team, gender, category)
        p.number = len(self.players) + 1
        self.players.append(p)

    def remove_player_by_name(self, name):
        self.players = [p for p in self.players if p.name != name]
        for i, p in enumerate(self.players): p.number = i + 1

    def rank_players(self):
        pmap = {p.name: p for p in self.players}
        for p in self.players: p.calculate_sb(pmap)
        self.players.sort(key=lambda x: (x.score, x.sonneborn_berger, x.wins), reverse=True)
        for i, p in enumerate(self.players): p.rank = i + 1
        return self.players

    def generate_pairings(self):
        active = [p for p in self.players if not p.disqualified]
        bye_p = None
        if len(active) % 2 != 0:
            if self.current_round == 0:
                random.shuffle(active)
                bye_p = active.pop()
            else:
                active.sort(key=lambda x: (x.bye, x.score))
                bye_p = active.pop(0)

        # 第一轮随机，之后瑞士轮
        if self.current_round == 0:
            random.shuffle(active)
        else:
            active.sort(key=lambda x: x.score, reverse=True)

        memo = {}
        def solve(rem):
            k = tuple(p.name for p in rem)
            if k in memo: return memo[k]
            if not rem: return []
            p1 = rem[0]
            for i in range(1, len(rem)):
                p2 = rem[i]
                if p2.name in p1.opponents: continue
                if self.use_teams and p1.team and p2.team and p1.team == p2.team: continue
                res = solve(rem[1:i] + rem[i+1:])
                if res is not None:
                    bal1, bal2 = p1.get_color_balance(), p2.get_color_balance()
                    c = 'B' if bal1 > bal2 else ('W' if bal1 < bal2 else ('B' if p1.color_history and p1.color_history[-1]=='W' else 'W'))
                    return [(p1, p2, c)] + res
            memo[k] = None
            return None

        pairs = solve(active)
        if pairs is None and self.use_teams: # Retry weak
            memo = {}
            def solve_loose(rem):
                k = tuple(p.name for p in rem)
                if k in memo: return memo[k]
                if not rem: return []
                p1 = rem[0]
                for i in range(1, len(rem)):
                    p2 = rem[i]
                    if p2.name in p1.opponents: continue
                    res = solve_loose(rem[1:i] + rem[i+1:])
                    if res is not None: return [(p1, p2, 'W')] + res
                memo[k] = None
                return None
            pairs = solve_loose(active)

        if pairs is None:
             # Last resort random for round 1
             if self.current_round == 0:
                 random.shuffle(active)
                 pairs = []
                 while len(active) >= 2:
                     pairs.append((active.pop(), active.pop(), 'W'))
             else:
                 raise Exception("Pairing Failed. Adjust rounds or players.")

        self.pairings = [(p1, p2, c) for p1, p2, c in pairs]
        if bye_p:
            self.pairings.append((bye_p, "BYE", None))
            bye_p.bye = True
            
        self.current_round += 1
        self.results = {}
        return self.pairings

    def commit_round(self):
        if len(self.results) < len(self.pairings): return False
        rh = {"round": self.current_round, "matches": []}
        for i, (p1, p2_obj, color) in enumerate(self.pairings):
            s1, s2, note = self.results.get(i, (0,0,""))
            c1 = color
            c2 = 'B' if color=='W' else 'W'
            if not color: c1, c2 = None, None
            p2_name = p2_obj.name if isinstance(p2_obj, Player) else "BYE"
            p1.add_result(p2_name, s1, c1, self.current_round, note)
            if isinstance(p2_obj, Player):
                p2_obj.add_result(p1.name, s2, c2, self.current_round, note)
                if p1.absent_streak >= 2: p1.disqualified = True
                if p2_obj.absent_streak >= 2: p2_obj.disqualified = True
            rh["matches"].append({"white": p1.name if c1=='W' else p2_name, "black": p2_name if c1=='W' else p1.name, "result": f"{s1}-{s2}"})
        self.history.append(rh)
        return True

# ==========================================
# 2. UI 逻辑 (Streamlit)
# ==========================================

st.set_page_config(page_title="Swiss Chess Manager", page_icon="♟️", layout="wide")

# CSS 美化
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    .reportview-container { background: #f0f2f6; }
    h1, h2, h3 { color: #0e1117; font-family: 'Microsoft YaHei', sans-serif; }
    .status-card { padding: 10px; border-radius: 5px; background-color: #e6f3ff; border: 1px solid #4da6ff; text-align: center;}
    div[data-testid="stMetric"] { background-color: #fff; padding: 10px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
</style>
""", unsafe_allow_html=True)

# Session State 初始化
if 'engine' not in st.session_state:
    st.session_state.engine = TournamentEngine()
if 'lang' not in st.session_state:
    st.session_state.lang = "CN"

engine = st.session_state.engine
T = TRANS[st.session_state.lang]

# --- Sidebar ---
st.sidebar.title(T["sidebar_title"])
lang_opt = st.sidebar.selectbox(T["lang_select"], ["CN", "EN"], index=0 if st.session_state.lang=="CN" else 1)
if lang_opt != st.session_state.lang:
    st.session_state.lang = lang_opt
    st.rerun()

st.sidebar.divider()

if not engine.is_started:
    engine.meta["name"] = st.sidebar.text_input(T["match_name"], value=engine.meta["name"])
    engine.rounds_total = st.sidebar.number_input(T["rounds"], min_value=1, max_value=20, value=5)
    engine.use_teams = st.sidebar.checkbox(T["team_mode"], value=False)
else:
    st.sidebar.info(f"🏆 {engine.meta['name']}")
    st.sidebar.markdown(f"<div class='status-card'>{T['status_round'].format(engine.current_round, engine.rounds_total)}</div>", unsafe_allow_html=True)
    if st.sidebar.button(T["reset_btn"]):
        st.session_state.engine = TournamentEngine()
        st.rerun()

# --- Helpers ---
def fmt_p(p):
    if isinstance(p, Player): return f"[#{p.number}] {p.name} ({p.score})"
    return "BYE"

def export_pdf_report():
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        # Page 1: Standings
        fig, ax = plt.subplots(figsize=(11, 8))
        ax.axis('off')
        plt.title(f"Final Standings - {engine.meta['name']}", fontsize=20)
        cols = ["Rank", "No.", "Name", "Team", "Pts", "SB", "W-D-L"]
        data = [[p.rank, p.number, p.name, p.team, p.score, f"{p.sonneborn_berger:.2f}", f"{p.wins}-{p.draws}-{p.losses}"] for p in engine.players]
        tbl = Table(ax, bbox=[0.05, 0.1, 0.9, 0.8])
        for i, c in enumerate(cols): tbl.add_cell(0, i, 0.1, 0.05, text=c, loc='center', facecolor='#ccc')
        for r, row in enumerate(data):
            for c, val in enumerate(row): tbl.add_cell(r+1, c, 0.1, 0.05, text=str(val), loc='center')
        ax.add_table(tbl)
        pdf.savefig(fig)
        plt.close(fig)
        # Page 2+: Details
        pmap = {p.name: p for p in engine.players}
        for p in sorted(engine.players, key=lambda x: x.rank):
            fig, ax = plt.subplots(figsize=(11, 8))
            ax.axis('off')
            plt.text(0.05, 0.95, f"Player: #{p.number} {p.name} (Rank: {p.rank}, Pts: {p.score})", fontsize=14, weight='bold')
            d_cols = ["Round", "Color", "Opponent", "Opp.Rank", "Result"]
            d_data = []
            for m in sorted(p.matches, key=lambda x: x['round']):
                op = pmap.get(m['opponent'])
                orank = op.rank if op else "-"
                d_data.append([m['round'], m['color'] or "-", m['opponent'], orank, m['result']])
            tbl = Table(ax, bbox=[0.05, 0.5, 0.9, 0.4])
            for i, c in enumerate(d_cols): tbl.add_cell(0, i, 0.2, 0.08, text=c, loc='center', facecolor='#eee')
            for r, row in enumerate(d_data):
                for c, val in enumerate(row): tbl.add_cell(r+1, c, 0.2, 0.08, text=str(val), loc='center')
            ax.add_table(tbl)
            pdf.savefig(fig)
            plt.close(fig)
    buffer.seek(0)
    return buffer

# --- Main Layout ---
st.title(T["title"])

tab1, tab2, tab3 = st.tabs([T["tab1"], T["tab2"], T["tab3"]])

# ================= Tab 1: 报名 =================
with tab1:
    if not engine.is_started:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("### " + T["add_player"])
            with st.form("add_p_form", clear_on_submit=True):
                col_a, col_b = st.columns(2)
                p_name = col_a.text_input(T["name"])
                p_sid = col_b.text_input(T["sid"])
                col_c, col_d = st.columns(2)
                p_team = col_c.text_input(T["team"])
                p_gender = col_d.selectbox(T["gender"], ["M", "F"])
                submitted = st.form_submit_button("➕ " + T["add_player"])
                if submitted and p_name:
                    engine.add_player(p_name, p_sid, p_team, p_gender)
                    st.success(f"Added: {p_name}")
                    st.rerun()

        with c2:
            st.markdown("### " + T["import_excel"])
            uploaded_file = st.file_uploader("Excel (.xlsx)", type=['xlsx'])
            if uploaded_file:
                try:
                    df = pd.read_excel(uploaded_file)
                    # 简单映射列
                    name_col = next((c for c in df.columns if "名" in str(c) or "Name" in str(c)), None)
                    if name_col:
                        count = 0
                        for _, row in df.iterrows():
                            nm = str(row[name_col]).strip()
                            if nm and nm != 'nan':
                                sid = str(row.get("学号", row.get("ID", ""))).strip()
                                tm = str(row.get("队伍", row.get("Team", ""))).strip()
                                gd = str(row.get("性别", row.get("Gender", ""))).strip()
                                engine.add_player(nm, sid, tm, gd)
                                count += 1
                        st.success(f"Imported {count} players!")
                except Exception as e:
                    st.error(f"Error: {e}")

        # 列表显示
        if engine.players:
            st.divider()
            p_data = [{"No.": p.number, T["sid"]: p.student_id, T["name"]: p.name, T["team"]: p.team} for p in engine.players]
            df_p = pd.DataFrame(p_data)
            st.dataframe(df_p, use_container_width=True)
            
            # 允许删除
            del_name = st.selectbox("Select to Delete", [p.name for p in engine.players], key="del_sel")
            if st.button("❌ Remove Player"):
                engine.remove_player_by_name(del_name)
                st.rerun()

        st.divider()
        if st.button(T["start_btn"], type="primary", disabled=len(engine.players)<2):
            engine.is_started = True
            engine.run_new_round_flag = True # Helper flag
            st.rerun()
    else:
        st.success("✅ Tournament is running. Go to Pairings tab.")
        st.metric(T["match_name"], engine.meta["name"])
        st.metric("Total Players", len(engine.players))

# ================= Tab 2: 对阵 =================
with tab2:
    if not engine.is_started:
        st.warning(T["status_wait"])
    else:
        # 生成新的一轮逻辑
        if getattr(engine, 'run_new_round_flag', False):
            try:
                engine.generate_pairings()
                engine.run_new_round_flag = False
                # Auto-fill BYE
                for i, (p1, p2, c) in enumerate(engine.pairings):
                    if p2 == "BYE": engine.results[i] = (1, 0, "BYE")
                st.rerun()
            except Exception as e:
                st.error(str(e))
                engine.run_new_round_flag = False

        st.subheader(f"{T['pairings_header']} ({T['status_round'].format(engine.current_round, engine.rounds_total)})")

        # 构造对阵数据展示
        pair_data = []
        match_options = {} # "1: A vs B" -> index
        
        for i, (p1, p2_obj, color) in enumerate(engine.pairings):
            res_val = engine.results.get(i)
            res_str = " - "
            if res_val:
                s1, s2, n = res_val
                # 根据颜色显示结果
                if color == 'W': w_s, b_s = s1, s2
                else: w_s, b_s = s2, s1
                res_str = f"{w_s} - {b_s}"
                if n: res_str += " (F)"
            
            p1_fmt = fmt_p(p1)
            p2_fmt = fmt_p(p2_obj)
            
            if color == 'W':
                w, b = p1_fmt, p2_fmt
            else:
                w, b = p2_fmt, p1_fmt
                
            if p2_obj == "BYE": w, b, res_str = p1_fmt, "BYE", "1 - 0"

            pair_data.append({
                T["table"]: i + 1,
                T["white"]: w,
                T["result"]: res_str,
                T["black"]: b
            })
            if p2_obj != "BYE":
                match_options[f"Table {i+1}: {w} vs {b}"] = i

        st.dataframe(pd.DataFrame(pair_data), hide_index=True, use_container_width=True)

        # 录入区域
        st.divider()
        st.markdown(f"#### 🎮 {T['quick_input']}")
        
        c_sel, c_btns = st.columns([1, 2])
        with c_sel:
            # 找出尚未录入的
            pending = [k for k, v in match_options.items() if v not in engine.results]
            all_opts = list(match_options.keys())
            def_idx = 0
            # 尝试定位到第一个未录入的
            if pending:
                def_idx = all_opts.index(pending[0])
            
            selected_match_str = st.selectbox(T["select_match"], all_opts, index=def_idx if all_opts else 0)
            
        if selected_match_str:
            idx = match_options[selected_match_str]
            p1, p2, color = engine.pairings[idx]
            
            # Buttons Logic
            def set_res(s1, s2, note=""):
                # s1 for Left(White), s2 for Right(Black) displayed in UI
                # map back to p1, p2 in engine list
                if color == 'W':
                    final_p1, final_p2 = s1, s2
                else:
                    final_p1, final_p2 = s2, s1
                engine.results[idx] = (final_p1, final_p2, note)
                st.rerun()

            with c_btns:
                r1, r2, r3 = st.columns(3)
                r1.button(T["btn_w_win"], on_click=set_res, args=(1, 0), type="primary")
                r2.button(T["btn_draw"], on_click=set_res, args=(0.5, 0.5))
                r3.button(T["btn_b_win"], on_click=set_res, args=(0, 1), type="primary")
                
                r4, r5, r6 = st.columns(3)
                r4.button(T["btn_w_abs"], on_click=set_res, args=(0, 1, "W Forfeit"))
                r5.button(T["btn_db_abs"], on_click=set_res, args=(0, 0, "Both Forfeit"))
                r6.button(T["btn_b_abs"], on_click=set_res, args=(1, 0, "B Forfeit"))

        st.divider()
        
        # 结算按钮
        if st.button(T["commit_round"], type="primary", use_container_width=True):
            if engine.commit_round():
                engine.rank_players()
                if engine.current_round < engine.rounds_total:
                    engine.run_new_round_flag = True
                    st.success("Round Finished! Starting next round...")
                    st.rerun()
                else:
                    st.balloons()
                    st.success(T["game_over"])
            else:
                st.error("Please enter all results first.")

        # 下载本轮
        if st.button(T["download_report"]):
            # 这里简单生成CSV代替图片，Web版生成图片较慢
            csv = pd.DataFrame(pair_data).to_csv(index=False).encode('utf-8-sig')
            st.download_button("Download CSV", csv, f"Round_{engine.current_round}_Pairings.csv", "text/csv")


# ================= Tab 3: 排名 & 裁判 =================
with tab3:
    if engine.players:
        engine.rank_players() # Ensure up to date
        st.subheader(T["rank_header"])
        
        # 构造排名数据
        r_data = []
        for p in engine.players:
            st_str = "DQ" if p.disqualified else ("ABS" if p.absent_streak else "OK")
            r_data.append({
                T["rank"]: p.rank,
                T["sid"]: p.student_id,
                T["name"]: p.name,
                T["team"]: p.team,
                T["score"]: p.score,
                T["sb"]: f"{p.sonneborn_berger:.2f}",
                T["wins"]: p.wins,
                T["status"]: st_str
            })
        st.dataframe(pd.DataFrame(r_data), use_container_width=True)
        
        st.divider()
        st.markdown(f"#### ⚖️ {T['referee_action']}")
        
        c_ref1, c_ref2 = st.columns(2)
        
        targets = [p.name for p in engine.players]
        target_p_name = c_ref1.selectbox(T["referee_target"], targets)
        target_p = next((p for p in engine.players if p.name == target_p_name), None)
        
        with c_ref2:
            # 判罚分
            with st.expander(T["penalty_score"]):
                pen_val = st.number_input("Points", value=0.0, step=0.5)
                pen_reason = st.text_input(T["penalty_reason"], value="Referee Adj")
                if st.button(T["apply_penalty"]):
                    if target_p:
                        target_p.apply_penalty(pen_val, pen_reason)
                        st.success(f"Applied {pen_val} to {target_p_name}")
                        st.rerun()
            
            # DQ / 退赛
            with st.expander(T["dq_check"]):
                if target_p.disqualified:
                    st.warning(f"{target_p_name} is already DQ.")
                    if st.button(T["requalify_btn"]):
                        target_p.disqualified = False
                        st.rerun()
                else:
                    if st.button(T["dq_btn"], type="primary"):
                        target_p.disqualified = True
                        st.rerun()

        # 最终报表下载
        if engine.current_round >= engine.rounds_total:
            st.divider()
            pdf_buf = export_pdf_report()
            st.download_button(T["final_report"], pdf_buf, f"{engine.meta['name']}_Report.pdf", "application/pdf")