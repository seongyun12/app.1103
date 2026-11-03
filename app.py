import io
import os
import qrcode
import streamlit as st
from datetime import datetime

st.set_page_config(
    page_title="장보기 알림메모",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------- Compact mobile-friendly styling ----------
st.markdown("""
<style>
    .block-container {padding-top: .65rem; padding-bottom: .6rem; max-width: 1100px;}
    h1 {font-size: 1.55rem !important; margin-bottom: .1rem !important;}
    h2, h3 {font-size: 1.05rem !important; margin-top: .35rem !important; margin-bottom: .25rem !important;}
    [data-testid="stMetric"] {padding: .35rem .55rem; border-radius: 10px; background: rgba(128,128,128,.08);}
    [data-testid="stMetricValue"] {font-size: 1.25rem !important;}
    div[data-testid="stVerticalBlock"] > div {gap: .45rem;}
    div.stButton > button {min-height: 2.25rem; padding: .35rem .55rem;}
    div[data-testid="stForm"] {border: 1px solid rgba(128,128,128,.25); padding: .65rem; border-radius: 12px;}
    .small-note {font-size: .82rem; opacity: .8;}
</style>
""", unsafe_allow_html=True)

CATEGORIES = ["채소", "과일", "육류·생선", "유제품", "곡류·빵", "간식·음료", "생활용품", "기타"]
PRIORITY_LABELS = {1: "1 · 꼭 필요", 2: "2 · 필요하면", 3: "3 · 여유 있으면"}
PRIORITY_HELP = {
    1: "꼭 필요한 물건이에요.",
    2: "가격을 확인하고 예산에 맞을 때 구매해요.",
    3: "비싸다면 이번에는 사지 않아도 괜찮아요.",
}

if "shopping_items" not in st.session_state:
    st.session_state.shopping_items = []
if "purchases" not in st.session_state:
    st.session_state.purchases = []
if "next_item_id" not in st.session_state:
    st.session_state.next_item_id = 1

items = st.session_state.shopping_items
purchases = st.session_state.purchases

def money(value):
    return f"{value:,.0f}원"

def make_qr(url):
    image = qrcode.make(url)
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()

st.title("🛒 장보기 알림메모")
st.caption("살 물건을 적고, 카트에 담을 때 가격·수량을 기록하세요.")

# Summary stays visible at the top
total_spent = sum(p["price"] * p["qty"] for p in purchases)
a, b, c = st.columns(3)
a.metric("현재 카트 합계", money(total_spent))
b.metric("살 물건", f"{len(items)}개")
c.metric("구매 완료", f"{len(purchases)}종")

left, right = st.columns([1, 1.25], gap="medium")

with left:
    st.subheader("➕ 메모 추가")
    with st.form("add_item_form", clear_on_submit=True):
        product_name = st.text_input("상품명", placeholder="예: 애호박 2개, 사과 작은 것")
        cat = st.selectbox("카테고리", CATEGORIES)
        priority = st.select_slider(
            "중요도",
            options=[1, 2, 3],
            value=2,
            format_func=lambda x: PRIORITY_LABELS[x],
        )
        note = st.text_input("가격 기준·메모 (선택)", placeholder="예: 3,000원 이하면 구매")
        submitted = st.form_submit_button("＋ 목록에 추가", use_container_width=True)
        if submitted:
            if not product_name.strip():
                st.warning("상품명을 입력해 주세요.")
            else:
                st.session_state.shopping_items.append({
                    "id": st.session_state.next_item_id,
                    "name": product_name.strip(),
                    "category": cat,
                    "priority": int(priority),
                    "note": note.strip(),
                })
                st.session_state.next_item_id += 1
                st.rerun()

    st.markdown("**중요도 안내**")
    st.markdown(
        '<div class="small-note">🔴 1 꼭 필요　🟡 2 가격 확인　🟢 3 여유 있으면<br>'
        '중요도 2·3은 비싸면 구매하지 않고 목록에 남겨둘 수 있어요.</div>',
        unsafe_allow_html=True,
    )

    with st.expander("📱 앱 QR 코드 만들기", expanded=False):
        st.caption("GitHub에 배포한 Streamlit 앱 주소를 입력하면 휴대폰으로 열 QR 코드를 만들 수 있어요.")
        app_url = st.text_input("배포된 앱 주소", placeholder="https://your-app.streamlit.app")
        if app_url.strip().startswith(("https://", "http://")):
            st.image(make_qr(app_url.strip()), caption="휴대폰 카메라로 스캔", width=180)
            st.download_button(
                "QR 이미지 저장",
                data=make_qr(app_url.strip()),
                file_name="shopping_memo_qr.png",
                mime="image/png",
                use_container_width=True,
            )
        elif app_url.strip():
            st.info("주소는 https:// 또는 http://로 시작해야 해요.")

with right:
    st.subheader("🧺 장보기 목록")
    if items:
        filter_cat = st.selectbox("카테고리 필터", ["전체"] + CATEGORIES, key="filter_cat")
        visible_items = [x for x in items if filter_cat == "전체" or x["category"] == filter_cat]
        if not visible_items:
            st.caption("이 카테고리에 등록된 물건이 없어요.")
        for item in visible_items:
            p = item["priority"]
            label = {1: "🔴", 2: "🟡", 3: "🟢"}[p]
            with st.container(border=True):
                title_col, delete_col = st.columns([5, 1])
                title_col.markdown(f"**{label} {item['name']}**")
                title_col.caption(f"{item['category']} · 중요도 {p}" + (f" · {item['note']}" if item["note"] else ""))
                if delete_col.button("✕", key=f"delete_{item['id']}", help="목록에서 삭제"):
                    st.session_state.shopping_items = [x for x in items if x["id"] != item["id"]]
                    st.rerun()

                with st.form(f"purchase_{item['id']}"):
                    x, y, z = st.columns([1, 1, 1.15])
                    price = x.number_input("개당 가격(원)", min_value=0, value=0, step=100, key=f"price_{item['id']}")
                    qty = y.number_input("수량", min_value=1, value=1, step=1, key=f"qty_{item['id']}")
                    z.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
                    buy = z.form_submit_button("담았어요 ✓", use_container_width=True)
                    if buy:
                        if price <= 0:
                            st.warning("구매한 상품의 개당 가격을 입력해 주세요.")
                        else:
                            st.session_state.purchases.append({
                                "name": item["name"],
                                "category": item["category"],
                                "price": int(price),
                                "qty": int(qty),
                                "subtotal": int(price) * int(qty),
                                "priority": p,
                                "purchased_at": datetime.now().strftime("%H:%M"),
                            })
                            st.session_state.shopping_items = [x for x in items if x["id"] != item["id"]]
                            st.rerun()
    else:
        st.info("아직 목록이 비어 있어요. 왼쪽에서 살 물건을 추가해 보세요.")

    st.subheader("🛒 카트에 담은 물건")
    if purchases:
        for idx, purchase in enumerate(purchases):
            row1, row2 = st.columns([5, 1])
            row1.markdown(
                f"**{purchase['name']}** · {purchase['qty']}개 × {money(purchase['price'])}"
                f" = **{money(purchase['subtotal'])}**"
            )
            row1.caption(f"{purchase['purchased_at']} 담음 · {purchase['category']}")
            if row2.button("되돌림", key=f"undo_{idx}", help="목록으로 되돌리기"):
                st.session_state.shopping_items.append({
                    "id": st.session_state.next_item_id,
                    "name": purchase["name"],
                    "category": purchase["category"],
                    "priority": purchase["priority"],
                    "note": "",
                })
                st.session_state.next_item_id += 1
                st.session_state.purchases.pop(idx)
                st.rerun()
        st.caption(f"카트 합계: **{money(total_spent)}**")
        if st.button("구매 기록 전체 비우기", use_container_width=True):
            st.session_state.purchases = []
            st.rerun()
    else:
        st.caption("아직 카트에 담은 물건이 없어요.")

st.divider()
st.caption("참고: 현재 데이터는 이 앱 세션 동안 유지됩니다. 새로고침·세션 종료 후에도 저장하려면 데이터베이스 연동이 필요해요.")
