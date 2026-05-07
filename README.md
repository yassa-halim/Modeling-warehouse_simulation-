# 📦 Warehouse Inventory Flow Simulation System

> نظام محاكاة إدارة المخزون المستودعي — مبني بالكامل على Python الخالص بدون NumPy أو SimPy أو MongoDB.

---

## 📋 جدول المحتويات

1. [نظرة عامة](#نظرة-عامة)
2. [هيكل المشروع](#هيكل-المشروع)
3. [الداتاسيت](#الداتاسيت)
4. [المكونات التفصيلية](#المكونات-التفصيلية)
5. [محرك المحاكاة DES](#محرك-المحاكاة-des)
6. [سياسات الطلب الثلاث](#سياسات-الطلب-الثلاث)
7. [الداشبورد](#الداشبورد)
8. [تشغيل المشروع](#تشغيل-المشروع)
9. [المعادلات والخوارزميات](#المعادلات-والخوارزميات)
10. [الـ KPIs المحسوبة](#الـ-kpis-المحسوبة)

---

## نظرة عامة

نظام **Discrete-Event Simulation (DES)** متكامل لمحاكاة إدارة المخزون في مستودعات حقيقية. يقرأ بيانات حركة المخزون مباشرة من ملف CSV، يجمّعها، يشغّل ثلاث سياسات طلب مختلفة بالتوازي، ثم يعرض النتائج على داشبورد تفاعلي بـ 7 تابات.

### الأهداف الرئيسية
- **تحليل حركة المخزون** (Inbound / Outbound / Transfer / Adjustment)
- **مقارنة 3 سياسات**: FOQ (ثابتة) vs EOQ (اقتصادية) vs JIT (وقت التسليم)
- **تصنيف ABC** للمنتجات بناءً على حجم الطلب
- **توصيات إعادة الطلب** بشكل تلقائي مع مستوى الإلحاحية
- **محاكاة متعددة المستودعات** لكل منتج على حدة

---

## هيكل المشروع

```
warehouse_simulation/
│
├── run_app.py                          # نقطة الدخول الرئيسية
├── config.py                           # الإعدادات المركزية
├── requirements.txt                    # المكتبات المطلوبة
├── warehouse-inventory-flow-dataset.csv # الداتاسيت
│
├── data/
│   └── csv_handler.py                  # قراءة وتجميع CSV
│
├── simulation/
│   ├── engine.py                       # محرك DES الرئيسي
│   ├── event_queue.py                  # Min-Heap Priority Queue
│   ├── math_utils.py                   # توزيعات إحصائية مخصصة
│   └── warehouse_sim.py                # محاكاة متعددة المستودعات
│
├── analysis/
│   ├── abc_classifier.py               # تصنيف ABC + Pareto
│   └── report_generator.py             # تقارير + توصيات + CSV export
│
└── dashboard/
    └── app.py                          # داشبورد Streamlit (7 Tabs)
```

---

## الداتاسيت

**الملف:** `warehouse-inventory-flow-dataset.csv`

### الأعمدة الـ 23

| العمود | النوع | الوصف |
|---|---|---|
| `inventory_flow_id` | string | معرف فريد لكل حركة |
| `warehouse_id` | string | معرف المستودع |
| `warehouse_name` | string | اسم المستودع |
| `warehouse_city` | string | مدينة المستودع |
| `warehouse_state` | string | ولاية/منطقة المستودع |
| `warehouse_postal_code` | string | الرمز البريدي |
| `warehouse_country` | string | الدولة |
| `product_id` | string | معرف المنتج |
| `product_name` | string | اسم المنتج |
| `sku` | string | Stock Keeping Unit |
| `movement_type` | string | **inbound / outbound / transfer / adjustment** |
| `quantity` | float | الكمية المحركة |
| `unit_of_measure` | string | وحدة القياس (kg, units, etc.) |
| `movement_datetime` | datetime | وقت وتاريخ الحركة |
| `source_location_type` | string | نوع المصدر |
| `source_location_id` | string | معرف المصدر |
| `destination_location_type` | string | نوع الوجهة |
| `destination_location_id` | string | معرف الوجهة |
| `reference_document_number` | string | رقم المرجع |
| `movement_reason` | string | سبب الحركة |
| `handled_by_user_id` | string | معرف المستخدم المسؤول |
| `comments` | string | ملاحظات |

### منطق التجميع

```
inbound   → مخزون وارد (تعبئة المستودع)
outbound  → مخزون صادر (الطلب / الطلبات)  ← المصدر الرئيسي للـ demand
transfer  → نقل بين مستودعات
adjustment→ تسوية / تلف / تدقيق (shrinkage)
```

**net_qty = total_inbound − total_outbound − total_adjustment**

---

## المكونات التفصيلية

---

### `config.py` — الإعدادات المركزية

```python
CSV_FILE_PATH           = "warehouse-inventory-flow-dataset.csv"
SIMULATION_HORIZON_DAYS = 90       # أفق المحاكاة (أيام)
INITIAL_STOCK_MULTIPLIER= 15       # مضاعف الـ stock الأولي عند غياب inbound
FOQ_ORDER_SIZE          = 200      # حجم الطلب الثابت (FOQ)
FOQ_REORDER_POINT_DAYS  = 7       # إعادة الطلب عند: stock < 7 أيام طلب
JIT_SAFETY_DAYS         = 2        # JIT: إعادة الطلب عند: stock < يومين
LEAD_TIME_MEAN          = 3.0      # متوسط وقت التسليم (أيام)
LEAD_TIME_STD           = 0.8      # انحراف معياري لوقت التسليم
DEFAULT_HOLDING_COST    = 5.0      # تكلفة تخزين ($/وحدة/سنة)
DEFAULT_ORDERING_COST   = 50.0     # تكلفة طلب ($/طلبية)
SERVICE_LEVEL_Z         = 1.65     # Z-score لمستوى خدمة 95%
```

---

### `data/csv_handler.py` — قارئ ومجمّع CSV

**المهمة:** يقرأ الداتاسيت سطراً بسطر (Single-Pass) دون تحميل الملف كاملاً في الذاكرة.

**المخرجات:** قائمة من `dict` لكل منتج تحتوي على:

| المجموعة | المفاتيح |
|---|---|
| الهوية | `product_id`, `product_name`, `sku`, `unit_of_measure` |
| المستودع الرئيسي | `primary_warehouse_id/name/city/state/country` |
| إجماليات الحركة | `total_inbound_qty`, `total_outbound_qty`, `total_transfer_qty`, `total_adjustment_qty` |
| إحصاءات الطلب | `avg_outbound_qty`, `std_outbound_qty`, `outbound_events` |
| الموقع الزمني | `first_movement_dt`, `last_movement_dt`, `active_days` |
| التتبع | `movement_reasons`, `warehouses_used` |
| Aliases للمحاكاة | `avg_retail_sales`, `std_retail_sales`, `total_retail_sales` |

**تحديد المستودع الرئيسي:** يُحدَّد بخريطة تردد — المستودع الذي يحتوي على أكبر عدد من الحركات.

**الـ std الافتراضي:** إذا كان عدد الأحداث = 1، يُستخدم `std = max(avg × 0.15, 0.1)`

---

### `simulation/event_queue.py` — طابور الأولوية

تطبيق يدوي لـ **Binary Min-Heap** بدون مكتبات خارجية.

```
الهيكل: قائمة Python عادية تمثل شجرة ثنائية
  parent(i) = (i-1) // 2
  left(i)   = 2*i + 1
  right(i)  = 2*i + 2

العمليات:
  push(event) → O(log n)   — إدراج + sift-up
  pop()       → O(log n)   — استخراج الأصغر + sift-down
  peek()      → O(1)       — قراءة الأصغر بدون حذف
```

**الـ Event Class:**
```python
Event(time=5.3, event_type="CUSTOMER_ORDER", data={"qty": 12})
```

أنواع الأحداث:
- `CUSTOMER_ORDER` — طلب عميل يصل (Poisson distributed)
- `INVENTORY_REVIEW` — مراجعة نهاية اليوم + trigger الطلبية
- `SHIPMENT_ARRIVAL` — وصول شحنة بعد Lead Time
- `ADJUSTMENT` — خصم يومي للـ shrinkage

---

### `simulation/math_utils.py` — الرياضيات الإحصائية

كل التوزيعات مكتوبة يدوياً بـ `random` و `math` فقط.

#### التوزيعات

| الدالة | الخوارزمية | الاستخدام |
|---|---|---|
| `exponential_variate(λ)` | Inverse Transform: `X = -ln(1-U)/λ` | لم يُستخدم مباشرة |
| `normal_variate(μ, σ)` | Box-Muller Transform | Lead Time + Poisson بديل |
| `poisson_variate(λ)` | Knuth Algorithm (دقيق لـ λ≤30) | حجم الطلب اليومي |

> **ملاحظة Poisson:** لـ `λ > 30` تُستخدم Normal تقريباً لأسباب أداء.

#### معادلات المخزون

```
EOQ  = √(2 × D × S / H)
       D = الطلب السنوي  |  S = تكلفة الطلبية  |  H = تكلفة التخزين/وحدة/سنة

Safety Stock (SS) = Z × σ_d × √(LT)
       Z = Z-score (1.65 لـ 95%)  |  σ_d = انحراف معياري يومي  |  LT = Lead Time

ROP = (avg_daily_demand × LT) + SS
```

---

### `simulation/engine.py` — محرك DES الرئيسي

#### تهيئة المخزون

```python
# الأولوية: استخدام البيانات الفعلية من الداتاسيت
if total_inbound_qty > 0:
    inventory = total_inbound_qty        # مخزون حقيقي
else:
    inventory = avg_daily_demand × 15   # تقدير

# Shrinkage يومي
daily_shrinkage = total_adjustment_qty / horizon
```

#### دورة اليوم الواحد

```
يوم D:
  │
  ├─ 🛒 CUSTOMER_ORDER (عشوائي) → طلب Poisson → خصم من المخزون
  │     إذا inventory < qty: stockout + partial fulfillment
  │
  ├─ ⚖️  ADJUSTMENT (D + 0.5) → خصم daily_shrinkage (shrinkage)
  │
  └─ 📋 INVENTORY_REVIEW (D + 0.99) → راجع المخزون
        إذا inventory ≤ reorder_point AND pending_orders == 0:
          → أرسل طلب SHIPMENT_ARRIVAL بعد Lead Time عشوائي
```

---

## سياسات الطلب الثلاث

### Policy A — FOQ (Fixed Order Quantity)

```
Reorder Point = avg_daily_demand × 7
Order Qty     = 200 وحدة (ثابت)

ميزة: بسيط، متوقع
عيب:  لا يتكيف مع التقلبات
```

### Policy B — EOQ (Economic Order Quantity)

```
Reorder Point = (avg_daily_demand × LEAD_TIME_MEAN) + Safety_Stock
Order Qty     = √(2 × annual_demand × ordering_cost / holding_cost)

ميزة: يوازن بين تكلفة التخزين والطلب
عيب:  يحتاج بيانات دقيقة للتكاليف
```

### Policy C — JIT (Just-In-Time)

```
Reorder Point = avg_daily_demand × 2   (يومان فقط)
Order Qty     = avg_daily_demand × (LT + 2)

ميزة: أدنى تكلفة تخزين
عيب:  حساس جداً لأي تأخير في التسليم
```

---

### `simulation/warehouse_sim.py` — محاكاة متعددة المستودعات

يُقسّم الطلب بالتساوي على عدد المستودعات التي مر بها المنتج:

```python
wh_demand = avg_outbound_qty / len(warehouses_used)
```

يُشغّل EOQ لكل مستودع منفصلاً ويُعيد KPIs لكل موقع.

---

### `analysis/abc_classifier.py` — تصنيف ABC

#### منطق التصنيف (Pareto Analysis)

```
الترتيب: منتجات مرتبة تنازلياً بـ total_outbound_qty

Class A → النسبة التراكمية ≤ 80%  (عادةً 20% من المنتجات)
Class B → النسبة التراكمية ≤ 95%  (عادةً 30% من المنتجات)
Class C → النسبة التراكمية > 95%  (عادةً 50% من المنتجات)
```

#### الاستراتيجية المقترحة لكل فئة

| الفئة | الوصف | استراتيجية المراجعة |
|---|---|---|
| A (Critical) | 80% من حجم الطلب | مراجعة يومية، stock levels عالية |
| B (Important) | 15% إضافية | مراجعة أسبوعية |
| C (Low-volume) | آخر 5% | مراجعة شهرية، حد أدنى |

---

### `analysis/report_generator.py` — التقارير

#### `compute_aggregate_kpis(policy_results)` 
يحسب متوسطات الأسطول (fleet-level averages) من نتائج المنتجات.

#### `get_reorder_recommendations(products)` 
يحسب توصية لكل منتج:

```python
days_coverage = net_qty / avg_outbound_qty

days < 7   → 🔴 HIGH   (اطلب 30 يوم طلب)
days < 14  → 🟡 MEDIUM (اطلب 21 يوم)
else       → 🟢 LOW    (اطلب 14 يوم)
```

#### `generate_text_report(products, sim_results)` 
تقرير Markdown كامل يشمل:
- ملخص الداتاسيت
- تصنيف ABC
- Top 10 منتجات
- جدول مقارنة FOQ vs EOQ vs JIT
- توصيات إعادة الطلب

#### `export_simulation_csv(sim_results)` 
يُصدّر نتائج الـ 3 سياسات في CSV واحد.

---

## الداشبورد

**الملف:** `dashboard/app.py`  
**المكتبات:** Streamlit + Plotly

### الـ Sidebar — تحكم في المحاكاة

| العنصر | النطاق | الافتراضي |
|---|---|---|
| Products to simulate | 10 → 100 | 50 |
| Horizon (days) | 30 → 180 | 90 |
| Holding cost ($/unit/yr) | 1 → 20 | 5 |
| Ordering cost ($/order) | 10 → 200 | 50 |

> **أي تغيير في الـ Sidebar يعيد تشغيل المحاكاة تلقائياً.**

### الـ 7 Tabs

#### Tab 1 — 📊 Overview
- بطاقات KPIs (منتجات، مستودعات، inbound، outbound، adjustments)
- بطاقات تصنيف ABC (A/B/C مع عدد المنتجات ونسبة الحجم)
- Pareto Chart تفاعلي: Bars ملونة بـ ABC + Cumulative % Line

#### Tab 2 — 🔄 Flow Analysis
- Donut Chart: توزيع أنواع الحركة (Inbound/Outbound/Transfer/Adjustment)
- Scatter Plot: Inbound vs Outbound لأعلى 30 منتج
- Bar Chart: النشاط بالولايات (State-level)
- جدول كامل: كل المنتجات مع كل الأعمدة

#### Tab 3 — ⚙️ Simulation
- 3 بطاقات (FOQ / EOQ / JIT) مع: Fill Rate, Service Level, Stockout Rate, Cost
- توصية تلقائية: أفضل سياسة بأقل تكلفة
- Radar Chart: مقارنة الـ 3 سياسات على 4 محاور
- جدول: نتائج تفصيلية لكل منتج

#### Tab 4 — 🏭 Warehouses
- جدول: KPIs لكل مستودع (EOQ per warehouse)
- Bar Chart: إجمالي تكلفة المحاكاة لكل مستودع

#### Tab 5 — 📝 Recommendations
- جدول توصيات إعادة الطلب (30 منتج) مع urgency
- Bar Chart: Net Inventory Position (أخضر = فائض، أحمر = عجز)

#### Tab 6 — 📈 Charts
- Grouped Bar: Fill Rate لكل منتج (FOQ vs EOQ vs JIT)
- Stacked Bar: Cost Breakdown (Holding + Ordering)
- Line Chart: مستوى المخزون عبر الزمن (90 يوم) للمنتج الأول

#### Tab 7 — 💾 Export
- زر: تحميل التقرير `.md`
- زر: تحميل نتائج المحاكاة `.csv`
- معاينة التقرير مباشرة في الصفحة

---

## تشغيل المشروع

### المتطلبات

```bash
pip install streamlit>=1.32.0 plotly>=5.18.0
```

> **لا يوجد**: pandas, numpy, pymongo, simpy أو أي مكتبة ثقيلة.

### التشغيل

```bash
streamlit run run_app.py
```

سيفتح المتصفح تلقائياً على `http://localhost:8501`

### ترتيب التحميل التلقائي

```
1. قراءة CSV وتجميع البيانات (csv_handler)
2. تصنيف ABC للمنتجات
3. تشغيل المحاكاة (FOQ + EOQ + JIT)
4. تشغيل محاكاة المستودعات
5. فتح الداشبورد بالبيانات جاهزة
```

### الـ Caching

- نتائج قراءة CSV: محفوظة بـ `@st.cache_data` حسب مسار الملف
- نتائج المحاكاة: محفوظة بـ SHA-256 hash لـ product IDs + معاملات المحاكاة
- أي تغيير في الـ sidebar يعيد الحساب تلقائياً

---

## المعادلات والخوارزميات

### Poisson Demand (Knuth Algorithm)

```python
L = e^(-λ)
k = 0, p = 1
repeat:
  k += 1
  p *= U(0,1)
until p < L
return k - 1
```

### Box-Muller (Normal Distribution)

```python
Z = √(-2·ln(U₁)) × cos(2π·U₂)
X = μ + σ·Z
```

### EOQ Formula

```
Q* = √(2·D·S / H)
     D = طلب سنوي  |  S = تكلفة طلبية  |  H = تكلفة تخزين سنوية/وحدة
```

### Safety Stock

```
SS = Z × σ_d × √(LT)
     Z = 1.65 (95% service level)
     σ_d = std يومي للطلب
     LT = متوسط Lead Time
```

### ABC Pareto

```python
cumulative_pct = Σ(outbound_i) / Σ(outbound_all) × 100
A if cumulative_pct ≤ 80
B if cumulative_pct ≤ 95
C otherwise
```

---

## الـ KPIs المحسوبة

| KPI | المعادلة | الوصف |
|---|---|---|
| **Fill Rate** | `total_sold / total_demand` | نسبة الطلب المُنفَّذ |
| **Service Level** | `fulfilled_orders / total_orders` | نسبة الطلبيات الكاملة |
| **Stockout Rate** | `stockout_orders / total_orders` | نسبة الطلبيات الجزئية |
| **Holding Cost** | `avg_inventory × (H/365) × horizon` | تكلفة الاحتفاظ بالمخزون |
| **Ordering Cost** | `replenishments × ordering_cost` | تكلفة إصدار الطلبيات |
| **Total Cost** | `holding_cost + ordering_cost` | إجمالي تكلفة المخزون |
| **Net Qty** | `inbound - outbound - adjustment` | صافي وضع المخزون |
| **Days Coverage** | `net_qty / avg_daily_outbound` | كم يوم يكفي المخزون الحالي |

---

## الفروق بين السياسات الثلاث

| المعيار | FOQ | EOQ | JIT |
|---|---|---|---|
| حجم الطلبية | ثابت (200) | ديناميكي (√formula) | ديناميكي (صغير) |
| نقطة إعادة الطلب | 7 أيام طلب | LT + Safety Stock | 2 أيام فقط |
| تكلفة التخزين | عالية | متوسطة | منخفضة |
| خطر النفاد | منخفض | منخفض-متوسط | عالي |
| التعقيد | بسيط | متوسط | بسيط |
| الأفضل لـ | A-class (حجم كبير) | B-class (متوازن) | C-class (طلب منتظم) |

---

## قرارات التصميم الرئيسية

1. **لا pandas / numpy**: لأن المشروع يجب أن يعمل في بيئات محدودة. كل الرياضيات مكتوبة يدوياً.

2. **Single-Pass CSV**: الملف يُقرأ مرة واحدة فقط لتوفير الذاكرة والوقت.

3. **Primary Warehouse بالتردد**: نختار المستودع الذي تمر به أكثر حركات للمنتج — أكثر دقة من الاختيار العشوائي.

4. **Inbound كـ Initial Inventory**: نبدأ المحاكاة من المخزون الفعلي (total_inbound) بدلاً من قيمة مُقدَّرة — دقة أعلى.

5. **Adjustment كـ Shrinkage Events**: تُجدوَل كأحداث يومية في الـ DES بدلاً من الطرح مرة واحدة — أكثر واقعية.

6. **Caching بـ SHA-256**: نتجنب إعادة حساب المحاكاة عند كل re-render، لكن نُعيد الحساب عند تغيير الـ parameters.

---

*📅 آخر تحديث: مايو 2026 | 🐍 Python 3.9+ | 📊 Streamlit + Plotly*
#   M o d e l i n g - w a r e h o u s e _ s i m u l a t i o n -  
 