import streamlit as st
import numpy as np
import plotly.graph_objects as go

# ─────────────────────────────────────────────
# إعداد الصفحة
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="نموذج IS-LM-BP التفاعلي | الاقتصاد الكلي",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS مخصص – واجهة عربية RTL
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');

    html, body, [class*="css"], .stMarkdown, .stText, p, span, div, h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        text-align: right;
        direction: rtl;
    }

    .stNumberInput, .stTextInput, .stSlider {
        direction: ltr;
    }

    .stMetric {
        text-align: center;
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }

    .stMetric label {
        justify-content: center;
        font-weight: 600;
        color: #495057;
    }

    .stMetric [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab"] {
        font-weight: bold;
        font-size: 1.05rem;
    }

    .badge-surplus {
        background-color: #d4edda;
        color: #155724;
        padding: 6px 12px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-deficit {
        background-color: #f8d7da;
        color: #721c24;
        padding: 6px 12px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
    }
    .badge-eq {
        background-color: #cce5ff;
        color: #004085;
        padding: 6px 12px;
        border-radius: 8px;
        font-weight: bold;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# الشريط الجانبي – المدخلات
# ─────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=80)
    st.title("إعدادات ومعطيات النموذج")
    st.caption("قم بتعديل المعاملات الهيكلية للاقتصاد لملاحظة التغير الفوري في التوازن والمنحنيات.")

    # ── IS ──────────────────────────────────
    st.subheader("📦 سوق السلع والخدمات (منحنى IS)")
    C0 = st.number_input("الاستهلاك التلقائي (C₀)", value=200.0, step=10.0)
    c  = st.number_input("الميل الحدي للاستهلاك (c)", value=0.75, min_value=0.01, max_value=0.99, step=0.01, format="%.2f")
    T  = st.number_input("الضرائب الثابتة (T)", value=100.0, step=10.0)
    I0 = st.number_input("الاستثمار التلقائي (I₀)", value=150.0, step=10.0)
    b  = st.number_input("حساسية الاستثمار للفائدة (b)", value=20.0, step=5.0)
    G  = st.number_input("الإنفاق الحكومي (G)", value=200.0, step=10.0)
    X  = st.number_input("الصادرات المستقلة (X)", value=100.0, step=10.0)
    M0 = st.number_input("الواردات التلقائية (M₀)", value=50.0, step=10.0)
    m  = st.number_input("الميل الحدي للاستيراد (m)", value=0.1, min_value=0.01, max_value=0.5, step=0.01, format="%.2f")

    # ── LM ──────────────────────────────────
    st.subheader("💰 سوق النقد (منحنى LM)")
    Ms = st.number_input("المعروض النقدي الحقيقي (Mˢ/P)", value=500.0, step=20.0)
    k  = st.number_input("حساسية الطلب للمعاملات (k)", value=0.5, min_value=0.01, step=0.01, format="%.2f")
    h  = st.number_input("حساسية الطلب للمضاربة (h)", value=10.0, step=1.0)

    # ── BP ──────────────────────────────────
    st.subheader("🌐 ميزان المدفوعات (منحنى BP)")
    st.write("درجة حركية رؤوس الأموال:")
    capital_mobility = st.radio(
        label="capital_mobility",
        options=["حركية غير تامة (معتدلة/مرتفعة)", "حركية تامة (Perfect Mobility)", "حركية معدومة (Zero Mobility)"],
        label_visibility="collapsed"
    )

    if capital_mobility == "حركية غير تامة (معتدلة/مرتفعة)":
        CF0 = st.number_input("تدفقات رأس المال التلقائية (CF₀)", value=0.0, step=10.0)
        f   = st.number_input("حساسية الفائدة لحركة الرأسمال (f)", value=15.0, step=1.0)
    elif capital_mobility == "حركية تامة (Perfect Mobility)":
        r_star = st.number_input("سعر الفائدة العالمي (r*)", value=5.0, step=0.5, format="%.1f")
        CF0, f = 0.0, 1e9  # f → ∞ تقريبياً
    else:  # Zero Mobility
        CF0, f = 0.0, 0.0


# ─────────────────────────────────────────────
# الحسابات الاقتصادية
# ─────────────────────────────────────────────

# معاملات IS:  Y = A_IS - slope_IS * r
#   Y = [C0 - c*T + I0 + G + X - M0] / (1 - c + m) - b/(1-c+m) * r
denom_IS = 1 - c + m
A_IS     = (C0 - c * T + I0 + G + X - M0) / denom_IS
slope_IS = b / denom_IS          # dr/dY < 0  →  r = (A_IS - Y) / slope_IS ... نعكس

# معاملات LM:  r = (k*Y - Ms) / h
slope_LM = k / h                 # dr/dY > 0
intercept_LM = -Ms / h           # r-intercept

# نقطة التوازن IS-LM:
# من IS:  r = (A_IS - Y) / slope_IS
# من LM:  r = slope_LM * Y + intercept_LM
# ⇒  (A_IS - Y) / slope_IS = slope_LM * Y + intercept_LM
# ⇒  A_IS - Y = slope_IS * slope_LM * Y + slope_IS * intercept_LM
# ⇒  Y_star = (A_IS - slope_IS * intercept_LM) / (1 + slope_IS * slope_LM)

Y_star = (A_IS - slope_IS * intercept_LM) / (1 + slope_IS * slope_LM)
r_star_eq = slope_LM * Y_star + intercept_LM

NX = X - M0 - m * Y_star

# ميزان المدفوعات عند التوازن الداخلي
if capital_mobility == "حركية تامة (Perfect Mobility)":
    BP_balance = NX + CF0 + f * (r_star_eq - r_star)
elif capital_mobility == "حركية معدومة (Zero Mobility)":
    BP_balance = NX   # لا يوجد تدفق رأس مال
else:
    BP_balance = NX + CF0 + f * r_star_eq


# ─────────────────────────────────────────────
# واجهة المستخدم الرئيسية
# ─────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; margin-bottom:8px;'>
  <img src='https://img.icons8.com/fluency/64/combo-chart.png' width='50'/>
  <h1 style='display:inline; margin-right:10px;'>📈 محاكي نموذج IS - LM - BP للتوازن الاقتصادي الكلي</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("""
تطبيق أكاديمي تفاعلي مخصص للأساتذة وطلبة الاقتصاد لتحليل التوازن الداخلي والخارجي،
ودراسة فاعلية السياسات الاقتصادية (المالية والنقدية) في ظل أنظمة الصرف المختلفة.
""")

st.divider()

# ── مقاييس التوازن ─────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("الدخل التوازني (Y*)", f"{Y_star:,.2f}")
with col2:
    st.metric("سعر الفائدة التوازني (r*)", f"{r_star_eq:.2f}%")
with col3:
    nx_label = "فائض تجاري" if NX > 0 else ("عجز تجاري" if NX < 0 else "توازن تجاري")
    st.metric(f"صافي الصادرات (NX) – {nx_label}", f"{NX:,.2f}")
with col4:
    if abs(BP_balance) < 0.5:
        bp_html = '<span class="badge-eq">توازن تام (BP = 0)</span>'
    elif BP_balance > 0:
        bp_html = f'<span class="badge-surplus">فائض (+{BP_balance:,.1f})</span>'
    else:
        bp_html = f'<span class="badge-deficit">عجز ({BP_balance:,.1f})</span>'
    st.markdown("**وضعية ميزان المدفوعات (BP)**")
    st.markdown(bp_html, unsafe_allow_html=True)

st.divider()

# ── علامات التبويب ──────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 الرسم البياني",
    "🔍 التشخيص الاقتصادي",
    "📐 الاشتقاق الرياضي",
    "⚗️ محاكي السياسات"
])


# ══════════════════════════════════════════════
# TAB 1 – الرسم البياني
# ══════════════════════════════════════════════
with tab1:
    st.subheader("التمثيل البياني لتوازن الاقتصاد المفتوح (IS - LM - BP)")

    Y_range = np.linspace(max(10, Y_star * 0.3), Y_star * 1.8, 400)

    # IS: r = (A_IS - Y) / slope_IS
    r_IS = (A_IS - Y_range) / slope_IS

    # LM: r = slope_LM * Y + intercept_LM
    r_LM = slope_LM * Y_range + intercept_LM

    fig = go.Figure()

    # منحنى IS
    fig.add_trace(go.Scatter(
        x=Y_range, y=r_IS,
        name="منحنى IS (سوق السلع)",
        line=dict(color="#1f77b4", width=3),
        hovertemplate="الدخل Y: %{x:.1f}<br>الفائدة r: %{y:.2f}%<extra>IS</extra>"
    ))

    # منحنى LM
    fig.add_trace(go.Scatter(
        x=Y_range, y=r_LM,
        name="منحنى LM (سوق النقد)",
        line=dict(color="#d62728", width=3),
        hovertemplate="الدخل Y: %{x:.1f}<br>الفائدة r: %{y:.2f}%<extra>LM</extra>"
    ))

    # منحنى BP
    if capital_mobility == "حركية تامة (Perfect Mobility)":
        fig.add_hline(
            y=r_star,
            line=dict(color="#2ca02c", width=3, dash="dash"),
            annotation_text=f"منحنى BP (حركية تامة: r* = {r_star}%)",
            annotation_position="top left"
        )
    elif capital_mobility == "حركية معدومة (Zero Mobility)":
        fig.add_vline(
            x=Y_star,
            line=dict(color="#2ca02c", width=3, dash="dash"),
            annotation_text=f"BP عمودي (Y={Y_star:.1f})",
            annotation_position="top left"
        )
    else:
        # BP: NX + CF0 + f*r = 0  ⇒  r = (m*Y - X + M0 - CF0) / f
        if f > 0:
            r_BP = (m * Y_range - X + M0 - CF0) / f
            fig.add_trace(go.Scatter(
                x=Y_range, y=r_BP,
                name="منحنى BP (ميزان المدفوعات)",
                line=dict(color="#2ca02c", width=3, dash="dash"),
                hovertemplate="الدخل Y: %{x:.1f}<br>الفائدة r: %{y:.2f}%<extra>BP</extra>"
            ))

    # نقطة التوازن
    fig.add_trace(go.Scatter(
        x=[Y_star], y=[r_star_eq],
        mode="markers+text",
        name="نقطة التوازن الداخلي E*",
        marker=dict(color="#ff7f0e", size=14, symbol="star"),
        text=["E*"],
        textposition="top center",
        hovertemplate="<b>نقطة التوازن E*</b><br>الدخل Y*: %{x:.2f}<br>الفائدة r*: %{y:.2f}%<extra></extra>"
    ))

    # خطوط الإسقاط
    fig.add_shape(type="line", x0=Y_star, x1=Y_star, y0=min(r_IS.min(), r_LM.min()) * 0.9,
                  y1=r_star_eq, line=dict(color="#ff7f0e", dash="dot", width=1.5))
    fig.add_shape(type="line", x0=Y_range[0], x1=Y_star, y0=r_star_eq, y1=r_star_eq,
                  line=dict(color="#ff7f0e", dash="dot", width=1.5))

    fig.update_layout(
        title=dict(text="<b>التوازن المتزامن للأسواق الثلاثة (السلع، النقد، والميزان الخارجي)</b>", x=0.5),
        xaxis_title="الناتج المحلي الإجمالي / الدخل الوطني (Y)",
        yaxis_title="سعر الفائدة المحلي % (r)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#f0f0f0",
        paper_bgcolor="white",
        height=550,
        font=dict(family="Cairo", size=13),
        hovermode="closest"
    )
    st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════
# TAB 2 – التشخيص الاقتصادي
# ══════════════════════════════════════════════
with tab2:
    st.markdown("#### 🔍 التشخيص الاقتصادي للوضعية الحالية:")

    bp_state = ("توازناً خارجياً تاماً" if abs(BP_balance) < 0.5
                else ("فائضاً خارجياً" if BP_balance > 0 else "عجزاً خارجياً"))

    st.markdown(f"""
* **حالة التوازن الداخلي:** الاقتصاد يحقق التوازن في سوقي السلع والنقد عند مستوى دخل **{Y_star:,.2f}** وفائدة **{r_star_eq:.2f}%**.
* **حالة ميزان المدفوعات:** رصيد الميزان يسجل **{bp_state}** ({BP_balance:+.2f}).
""")

    if capital_mobility == "حركية تامة (Perfect Mobility)":
        mob_label = "تامة تماماً (BP أفقي تماماً عند مستوى الفائدة العالمي)"
        policy_note = "السياسة المالية بالغة الأثر مع الصرف الثابت ومعدومة الأثر مع الصرف المرن."
    elif capital_mobility == "حركية معدومة (Zero Mobility)":
        mob_label = "معدومة (BP عمودي تماماً)"
        policy_note = "لا يوجد أي تأثير لتدفقات رأس المال."
    else:
        slope_BP = m / f if f > 0 else float("inf")
        if slope_BP < slope_LM:
            mob_label = "مرتفعة نسبياً (منحنى BP أكثر تسطحاً من LM)"
            policy_note = "السياسة المالية فعالة في ظل الصرف الثابت، والسياسة النقدية فعالة في ظل الصرف المرن."
        else:
            mob_label = "ضعيفة نسبياً (منحنى BP أكثر انحداراً من LM)"
            policy_note = "تأثير السياسات يعتمد بدرجة أكبر على حساسية الواردات مقارنة بتدفقات رأس المال."

    st.markdown(f"""
* **درجة حركية رأس المال:** {mob_label}.
* **خلاصة فاعلية السياسات:** {policy_note}
""")


# ══════════════════════════════════════════════
# TAB 3 – الاشتقاق الرياضي
# ══════════════════════════════════════════════
with tab3:
    st.subheader("الاشتقاق الجبري الدقيق لمعادلات النموذج")

    st.markdown("##### 1. اشتقاق منحنى التوازن في سوق السلع والخدمات (IS):")
    st.code("Y = C + I + G + NX", language="")
    st.code(f"Y = ({C0} + {c}(Y - {T})) + ({I0} - {b}r) + {G} + ({X} - ({M0} + {m}Y))", language="")
    st.code(f"Y(1 - {c} + {m}) = ({C0} - {c}×{T} + {I0} + {G} + {X} - {M0}) - {b}r", language="")
    st.latex(fr"\mathbf{{Y = {A_IS:.4f} - {slope_IS:.4f}\,r}} \quad \iff \quad \mathbf{{r = \frac{{{A_IS:.4f} - Y}}{{{slope_IS:.4f}}}}}")
    st.info(f"ميل المنحنى في المستوى (Y, r) هو: -{1/slope_IS:.4f}")

    st.divider()
    st.markdown("##### 2. اشتقاق منحنى التوازن في سوق النقد (LM):")
    st.latex(r"\frac{M^s}{P} = L(Y, r) = kY - hr")
    st.code(f"{Ms} = {k}Y - {h}r", language="")
    st.latex(fr"r = \frac{{{k}}}{ {h} } Y - \frac{{{Ms:.0f}}}{ {h} } = {slope_LM:.4f}\,Y - {abs(intercept_LM):.4f}")
    st.info(f"ميل المنحنى في المستوى (Y, r) هو: +{slope_LM:.4f}")

    st.divider()
    st.markdown("##### 3. اشتقاق منحنى توازن ميزان المدفوعات (BP):")
    st.code("BP = NX + CF = 0", language="")

    if capital_mobility == "حركية تامة (Perfect Mobility)":
        st.latex(fr"\mathbf{{r = r^* = {r_star:.1f}\%}}")
        st.info("منحنى BP أفقي تماماً – سعر الفائدة محدد دولياً.")
    elif capital_mobility == "حركية معدومة (Zero Mobility)":
        st.latex(r"NX = 0 \implies Y = \text{ثابت}")
        st.info("منحنى BP عمودي – لا حركة لرأس المال.")
    else:
        st.code(f"({X} - {M0} - {m}Y) + ({CF0} + {f}r) = 0", language="")
        slope_BP = m / f if f > 0 else 0
        intercept_BP = (M0 - X - CF0) / f if f > 0 else 0
        st.latex(fr"\mathbf{{r = {slope_BP:.4f}\,Y + ({intercept_BP:.4f})}}")
        st.info(f"ميل منحنى BP هو: {slope_BP:.4f}  مقابل ميل LM البالغ: {slope_LM:.4f}")


# ══════════════════════════════════════════════
# TAB 4 – محاكي السياسات
# ══════════════════════════════════════════════
with tab4:
    st.subheader("تجربة السياسات الاقتصادية والتحليل الديناميكي")
    st.write("اختر نوع السياسة لتشاهد كيف تؤثر الصدمات على الاقتصاد في ظل أنظمة أسعار الصرف المختلفة:")

    policy_type = st.radio(
        "نوع السياسة",
        ["صدمة في الإنفاق الحكومي (ΔG):", "صدمة في المعروض النقدي (ΔMˢ):"],
        horizontal=True
    )

    if "ΔG" in policy_type:
        delta = st.slider("مقدار التغير في الإنفاق الحكومي (ΔG)", -200, 200, 50, 10)
        G2    = G + delta
        Ms2   = Ms
    else:
        delta = st.slider("مقدار التغير في المعروض النقدي (ΔMˢ)", -200, 200, 50, 10)
        G2    = G
        Ms2   = Ms + delta

    # الاقتصاد بعد الصدمة
    A_IS2  = (C0 - c * T + I0 + G2 + X - M0) / denom_IS
    intercept_LM2 = -Ms2 / h
    Y2 = (A_IS2 - slope_IS * intercept_LM2) / (1 + slope_IS * slope_LM)
    r2 = slope_LM * Y2 + intercept_LM2
    NX2 = X - M0 - m * Y2

    if capital_mobility == "حركية تامة (Perfect Mobility)":
        BP2 = NX2 + CF0 + f * (r2 - r_star)
    elif capital_mobility == "حركية معدومة (Zero Mobility)":
        BP2 = NX2
    else:
        BP2 = NX2 + CF0 + f * r2

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("الدخل بعد الصدمة الأولي", f"{Y2:,.2f}", f"{Y2 - Y_star:+.2f}")
    with c2:
        st.metric("الفائدة بعد الصدمة الأولي", f"{r2:.2f}%", f"{r2 - r_star_eq:+.2f}%")
    with c3:
        st.metric("رصيد ميزان المدفوعات الأولي", f"{BP2:+.2f}")

    st.markdown("#### مقارنة بين نظامي سعر الصرف بعد هذا التدخل:")

    st.markdown("""
<div style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; border-right: 5px solid #0066cc;">
<h4 style="color: #0066cc; margin-top:0;">1. في ظل نظام سعر الصرف الثابت (Fixed)</h4>
<p><b>الآلية التلقائية للبنك المركزي:</b></p>
<ul>
    <li>إذا أحدثت الصدمة <b>فائضاً</b> (ضغط لرفع العملة): يتدخل البنك بشراء العملة الأجنبية وضخ العملة المحلية، فيزيد المعروض النقدي وينتقل منحنى LM نحو اليمين ليدعم التوسع.</li>
    <li>إذا أحدثت الصدمة <b>عجزاً</b> (ضغط لخفض العملة): يبيع البنك الاحتياطي النقدي لسحب العملة المحلية، فينكمش المعروض النقدي وينتقل LM لليسار.</li>
</ul>
<p><b>النتيجة:</b> السياسة المالية تكون <b>فعالة للغاية</b> إذا كانت حركية رأس المال مرتفعة، بينما تفقد السياسة النقدية استقلاليتها التامة.</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div style="background-color: #fff9f0; padding: 15px; border-radius: 10px; border-right: 5px solid #ff9900; margin-top:12px;">
<h4 style="color: #ff9900; margin-top:0;">2. في ظل نظام سعر الصرف المرن (Flexible)</h4>
<p><b>الآلية التلقائية لقوى السوق:</b></p>
<ul>
    <li>إذا أحدثت الصدمة <b>فائضاً</b>: ترتفع قيمة العملة المحلية (Appreciation)، فتنخفض الصادرات وترتفع الواردات، مما يعيد منحنى IS لليسار (مزاحمة الصادرات).</li>
    <li>إذا أحدثت الصدمة <b>عجزاً</b>: تنخفض قيمة العملة المحلية (Depreciation)، فتتحسن القدرة التنافسية وتزداد الصادرات، وينزاح منحنى IS نحو اليمين.</li>
</ul>
<p><b>النتيجة:</b> السياسة المالية تفقد فاعليتها بسبب مزاحمة سعر الصرف، في حين تصبح السياسة النقدية <b>شديدة الفاعلية</b>.</p>
</div>
""", unsafe_allow_html=True)

    # ── دليل الأستاذ ──
    with st.expander("📖 دليل الأستاذ لاستخدام التطبيق في قاعة المحاضرات"):
        st.markdown("""
### 🎯 الأهداف التعليمية المستفادة للطلاب:
1. **الربط بين الجبر والهندسة:** فهم كيف تؤثر المعاملات السلوكية (كالميل الحدي للاستهلاك $c$ أو حساسية الاستثمار $b$) في انحدار وميل المنحنيات ومواضع تقاطعها.
2. **ثلاثية ماندل وفلمنغ (Mundell-Fleming Trilemma):** تمكين الطالب من معاينة استحالة الجمع بين:
   * حرية حركة رؤوس الأموال.
   * ثبات سعر الصرف.
   * استقلالية السياسة النقدية.
3. **تفسير الفجوات:** بيان كيف أن أي نقطة تقع **فوق** منحنى $BP$ تمثل فائضاً خارجياً، وأي نقطة **تحته** تمثل عجزاً، وكيف تعيد قوى السوق أو تدخلات البنك المركزي الاقتصاد إلى مساره التوازني.
""")

# ─────────────────────────────────────────────
# تذييل الصفحة
# ─────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align: center; color: #6c757d; font-size: 0.9rem;'>"
    "تم تصميم وتطوير هذا النموذج الرقمي لمساعدة الأساتذة وطلبة الجامعات في تيسير تدريس مادة الاقتصاد الكلي."
    "</div>",
    unsafe_allow_html=True
)

