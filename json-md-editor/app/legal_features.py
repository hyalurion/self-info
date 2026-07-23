"""Legal features: templates, auto-numbering, directory extraction, word count."""

import re

# Common legal document Markdown templates
LEGAL_TEMPLATES = {
    "Confidentiality Agreement (NDA)": """# Confidentiality Agreement (NDA)

**This agreement is signed by the following parties on {date}.**

Party A: ________________________
Party B: ________________________

## One: Confidentiality of Information
"Confidentiality of Information" means any information disclosed by one party to the other party in writing, orally, or otherwise, marked or otherwise reasonably considered to be of confidential nature.

## Two: Confidentiality Obligations
Party B shall keep Party A's confidential information confidential, and shall not disclose it to any third party without Party A's prior written consent.

## Three: Exceptions
Exceptional circumstances
The following information is not considered confidential:
(1) Information that is already known to the public at the time of disclosure;
(2) Information that enters the public domain not due to the receiving party's breach;
(3) Information that the receiving party lawfully knew prior to disclosure.

## Four: Liability for Breach
Any party that violates this agreement shall bear corresponding liability for breach and compensate the non-breaching party for losses suffered thereby.

## Five: Dispute Resolution
Any disputes arising from this agreement shall be resolved through friendly negotiation between the parties; if negotiation fails, the dispute shall be submitted to the competent People's Court for litigation.

**Party A (Seal): ____________    Party B (Seal): ____________**
""",
    "Terms of Service": """# Terms of Service

## One: General Provisions
These terms constitute an agreement for providing services to users. Use of this service constitutes acceptance of these terms.

## Two: Account and Registration
Users shall ensure that registration information is true, accurate, and complete, and shall be responsible for all activities under their account.

## Three: Service Usage Standards
Users shall not use this service to engage in any activities that violate laws and regulations or infringe upon the legitimate rights and interests of others.

## Four: Intellectual Property
Intellectual property rights related to this service, including software, content, and trademarks, belong to the service provider.

## Five: Limitation of Liability
To the maximum extent permitted by law, the service provider shall not be liable for indirect, incidental, or consequential damages.

## Six: Amendment of Terms
The service provider reserves the right to modify these terms at any time. Modified terms shall take effect after being published on the platform.
""",
    "Privacy Policy": """# Privacy Policy

## One: Information Collection
We may collect information you voluntarily provide and logs, device information generated during your use of the service.

## Two: Information Use
We use collected information only for providing services, improving experience, and purposes required by laws and regulations.

## Three: Information Sharing
Except as required by laws and regulations or with your consent, we will not share your personal information with third parties.

## Four: Information Storage and Security
We adopt reasonable technical and management measures to protect the security of your personal information.

## Five: Your Rights
You have the right to query, correct, and delete your personal information, and may withdraw authorization consent previously given.

## Six: Contact Us
If you have any questions about this policy, please contact us at: ________________.
""",
    "Power of Attorney": """# Power of Attorney

Principal: ________________________
Attorney-in-Fact: ________________________

The Principal hereby appoints the Attorney-in-Fact as agent for the following matters: ________________________, with the following authority:

## One: Scope of Authority
(1) To submit and receive relevant materials on behalf of the Principal;
(2) To sign documents related to this matter on behalf of the Principal;
(3) To handle other necessary procedures related to this matter.

## Two: Term of Authority
This appointment shall take effect from the date of signing and terminate upon completion of the above matters.

## Three: Liability
The Principal acknowledges and assumes legal consequences for legal acts performed by the Attorney-in-Fact within the scope of authority above.

**Principal (Signature): ____________    Date: ____ Year __ Month __ Day**
""",
}


def extract_headings(text):
    """Extract headings, returns [(line_number, level, heading_text), ...]."""
    headings = []
    for i, line in enumerate(text.splitlines()):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            headings.append((i, len(m.group(1)), m.group(2).strip()))
    return headings


_CN_NUM = [
    "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
    "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen", "Twenty",
    "Twenty-One", "Twenty-Two", "Twenty-Three", "Twenty-Four", "Twenty-Five", "Twenty-Six", "Twenty-Seven", "Twenty-Eight", "Twenty-Nine", "Thirty",
]


def _cn_upper(n):
    if n <= len(_CN_NUM) - 1:
        return _CN_NUM[n]
    return str(n)


_CN_SMALL = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten"]


def _cn_small(n):
    if 1 <= n <= len(_CN_SMALL):
        return _CN_SMALL[n - 1]
    return str(n)


def _strip_article(title):
    """Strip a leading Article number in either Latin or CJK form."""
    title = re.sub(r"^Article\s+[A-Za-z0-9]+\s*:?\s*", "", title).strip()
    title = re.sub(r"^第[零一二三四五六七八九十百]+\s*条\s*", "", title).strip()
    return title


def _strip_paren(title):
    title = re.sub(r"^\([A-Za-z0-9]+\)\s*", "", title).strip()
    title = re.sub(r"^（[一二三四五六七八九十]+）\s*", "", title).strip()
    return title


def _strip_numeric(title):
    return re.sub(r"^\d+\.\s*", "", title).strip()


# Localized numbering styles keyed by language code.
# CJK locales use 第N条 / （一） / 1. ; Latin locales use Article N / (A) / 1.
_CN_NUM_FULL = [
    "零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
]


def _cn_full(n):
    if 1 <= n <= len(_CN_NUM_FULL) - 1:
        return _CN_NUM_FULL[n]
    return str(n)


_PAREN_CN = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]


def _paren_cn(n):
    if 1 <= n <= len(_PAREN_CN):
        return _PAREN_CN[n - 1]
    return str(n)


def auto_number_articles(text, lang=None, article_level=1):
    """Auto-number article headings.

    ``article_level`` is the heading level that carries article numbers
    (1 = top-level ``#``; the self-info site privacy docs use 2 = ``##``).

    The numbering matches the self-info site convention:
    - CJK (ja / zh-Hans / zh-TW)
        article -> "第N条" (Arabic N)
        sub     -> "A." / "B." (Latin letters, like the site's ``### A.``)
        deeper  -> "1." / "2."
    - Latin (en)
        article -> "Article N: ..."
        sub     -> "(A)" / "(B)"
        deeper  -> "1." / "2."
    - levels below article_level (preamble) are left untouched.
    """
    cjk = lang in ("ja", "zh-Hans", "zh-TW") if lang else False
    lines = text.splitlines()
    counters = {}
    out = []
    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if not m:
            out.append(line)
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        if level < article_level:
            out.append(f"{'#' * level} {title}")
            continue
        rel = level - article_level
        counters[level] = counters.get(level, 0) + 1
        for lv in [k for k in counters if k > level]:
            counters[lv] = 0
        if rel == 0:
            if cjk:
                title = f"第{counters[level]}条 {_strip_article(title)}"
            else:
                title = f"Article {_cn_upper(counters[level])}: {_strip_article(title)}"
        elif rel == 1:
            if cjk:
                letter = chr(ord("A") + counters[level] - 1)
                title = f"{letter}. {_strip_paren(title)}"
            else:
                title = f"({_cn_small(counters[level])}) {_strip_paren(title)}"
        else:
            title = f"{counters[level]}. {_strip_numeric(title)}"
        out.append(f"{'#' * level} {title}")
    return "\n".join(out)


def word_count(text):
    """Count words: characters (excluding whitespace), CJK characters, total lines, estimated pages."""
    chars = len(re.sub(r"\s", "", text))
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    lines = text.count("\n") + 1
    non_cjk = max(0, chars - cjk)
    words = cjk + non_cjk // 5  # Rough English word count estimate
    pages = max(1, round(words / 500))
    return {
        "chars": chars,
        "cjk": cjk,
        "words": words,
        "lines": lines,
        "pages": pages,
    }


# ---------------------------------------------------------------------------
# Per-language privacy-policy templates that mirror the self-info site docs
# (src/data/legal/{ja,en,zh-Hans,zh-TW}.md).
#
# Convention for auto-numbering:
#   - preamble sections use "#"  (level 1, never numbered)
#   - articles use        "##" (level 2 -> 第N条 / Article N)
#   - sub-articles use    "###" (level 3 -> （一） / (A))
# Pass article_level=2 to auto_number_articles() so preamble stays untouched.
# ---------------------------------------------------------------------------

SITE_PRIVACY_TEMPLATES = {
    "zh-Hans": """# 隐私政策

本隐私政策说明我们通过 Google Analytics 收集的数据类型、使用目的及管理方式。本声明生效日期：{date}。

# 版本更新机制
本声明修订时，我们可能不会在网站上单独通知。但若涉及实质性变更，将通过显著方式告知用户。

# 基本原则
本服务使用 Google Analytics 时，严格遵守相关个人数据保护法规。本声明旨在获取用户的明确同意。

# 定义条款
- **本服务**: 指由我们提供的所有网络服务及功能
- **用户**: 使用本服务的任何个人
- **匿名标识符**: 经不可逆处理、无法识别个人身份的唯一标识

> **重要声明：** 所收集数据仅用于服务优化，绝不用于身份识别。

## 收集的数据类型
### 个人相关数据
- **用户标识符**: 随机生成的匿名ID（经不可逆匿名化处理）
- **设备信息**: 设备类型、操作系统、浏览器版本

### 行为数据
- **使用情况**: 页面浏览量、会话时长、跳出率
- **交互数据**: 点击事件、页面滚动深度

### 位置数据
- **区域数据**: 国家/州级位置（基于匿名化IP推算，非GPS）

## 数据使用目的
（请填写数据使用目的，可按数据类型列表说明）

## 数据跨境传输
（请填写跨境传输安排及保障措施）

## 数据保护措施
- **匿名化**: IP地址仅用于地区级定位后立即丢弃
- **加密**: 传输加密（TLS 1.3+），存储加密（AES-256）
- **保留期限**: 最长14个月（用户可随时要求删除）

## 用户权利
- 访问权、更正权、撤回同意权、删除权（请填写行使方式）

## 儿童数据处理
若用户为13岁以下儿童，我们将要求法定监护人同意。

## 同意管理机制
1. 首次访问时展示本声明并获取同意
2. 用户可通过设置随时撤回同意
3. 撤回同意后立即停止数据收集

## Cookie政策
### Cookie类型及用途
（请填写Cookie类型、名称、用途、保留期）

### Cookie管理
- 浏览器设置拒绝Cookie
""",

    "zh-TW": """# 隱私權政策

本隱私權政策說明我們透過 Google Analytics 收集的資料類型、使用目的及管理方式。本聲明生效日期：{date}。

# 版本更新機制
本聲明修訂時，我們可能不會在網站上單獨通知。但若涉及實質性變更，將透過顯著方式告知使用者。

# 基本原則
本服務使用 Google Analytics 時，嚴格遵守相關個人資料保護法規。本聲明旨在取得使用者的明確同意。

# 定義條款
- **本服務**: 指由我們提供的所有網路服務及功能
- **使用者**: 使用本服務的任何個人
- **匿名識別碼**: 經不可逆處理、無法識別個人身分的唯一識別碼

> **重要聲明：** 所收集資料僅用於服務最佳化，絕不用於身分識別。

## 收集的資料類型
### 個人相關資料
- **使用者識別碼**: 隨機生成的匿名ID（經不可逆匿名化處理）
- **裝置資訊**: 裝置類型、作業系統、瀏覽器版本

### 行為資料
- **使用情況**: 頁面瀏覽量、工作階段時長、跳出率
- **互動資料**: 點擊事件、頁面捲動深度

### 位置資料
- **區域資料**: 國家/州級位置（基於匿名化IP推算，非GPS）

## 資料使用目的
（請填寫資料使用目的，可依資料類型列表說明）

## 資料跨境傳輸
（請填寫跨境傳輸安排及保障措施）

## 資料保護措施
- **匿名化**: IP位址僅用於地區級定位後立即捨棄
- **加密**: 傳輸加密（TLS 1.3+），儲存加密（AES-256）
- **保留期限**: 最長14個月（使用者可隨時要求刪除）

## 使用者權利
- 存取權、更正權、撤回同意權、刪除權（請填寫行使方式）

## 兒童資料處理
若使用者為13歲以下兒童，我們將要求法定監護人同意。

## 同意管理機制
1. 首次造訪時展示本聲明並取得同意
2. 使用者可隨時撤回同意
3. 撤回同意後立即停止資料收集

## Cookie政策
### Cookie類型及用途
（請填寫Cookie類型、名稱、用途、保留期）

### Cookie管理
- 瀏覽器設定拒絕Cookie
""",

    "ja": """# プライバシーポリシー

本プライバシーポリシーは、Google Analytics を通じて収集するデータの種類、利用目的、管理手法を説明します。本声明の発効日：{date}。

# バージョン更新メカニズム
本声明を改訂する際、ウェブサイト上で個別に通知しない場合があります。ただし実質的な変更がある場合は、顕著な方法で利用者に告知します。

# 基本方針
本サービスは Google Analytics を利用する際、関連する個人データ保護法規を厳格に遵守します。本声明は利用者の明確な同意を得ることを目的とします。

# 定義条項
- **本サービス**: 当社が提供するすべてのネットワークサービスおよび機能
- **利用者**: 本サービスを利用するいかなる個人
- **匿名識別子**: 不可逆処理により個人を識別できない一意の識別子

> **重要声明：** 収集されたデータはサービスの最適化のみに使用され、身元識別には一切使用されません。

## 収集するデータの種類
### 個人関連情報
- **利用者識別子**: ランダム生成された匿名ID（不可逆匿名化処理済み）
- **デバイス情報**: デバイス種別、OS、ブラウザバージョン

### 行動データ
- **利用状況**: ページビュー、セッション時間、離脱率
- **インタラクション**: クリックイベント、スクロール深度

### 位置情報
- **地域データ**: 国/州レベルの位置（匿名化IPから算出、GPS非依存）

## データ利用目的
（データ利用目的を記入。データ種別ごとにリスト化可）

## データの第三者提供
（第三者提供の条件および措置を記入）

## データ保護措置
- **匿名化**: IPアドレスは地域レベルのみに使用し即時破棄
- **暗号化**: 通信暗号化（TLS 1.3+）、保存暗号化（AES-256）
- **保存期間**: 最大14か月（利用者はいつでも削除を要求可）

## ユーザーの権利
- アクセス権、訂正権、同意撤回権、削除権（行使方法を記入）

## 児童データ処理
利用者が13歳未満の児童である場合、法定代理人の同意を求めます。

## 同意管理プロセス
1. 初回アクセス時に本声明を表示し同意を取得
2. 利用者は設定からいつでも同意を撤回可能
3. 同意撤回後は直ちにデータ収集を停止

## Cookie政策
### 使用するCookieの種類と目的
（Cookieの種類、名前、目的、保存期間を記入）

### Cookieの管理方法
- ブラウザ設定でCookieを拒否
""",

    "en": """# Privacy Policy

This privacy policy explains the types of data we collect through Google Analytics, the purposes of use, and how it is managed. Effective date: {date}.

# Version Update Mechanism
When this statement is revised, we may not notify users separately on the website. However, for material changes we will inform users through a prominent method.

# Basic Principles
When using Google Analytics, this service strictly complies with relevant personal data protection laws. This statement is intended to obtain the user's explicit consent.

# Definitions
- **This service**: all network services and features provided by us
- **User**: any individual who uses this service
- **Anonymous identifier**: a unique identifier that has been irreversibly processed and cannot identify a person

> **Important notice:** Data collected is used only for service optimization and never for identification.

## Types of Data Collected
### Personal Data
- **User identifier**: a randomly generated anonymous ID (irreversibly anonymized)
- **Device information**: device type, OS, browser version

### Behavioral Data
- **Usage**: page views, session duration, bounce rate
- **Interaction**: click events, scroll depth

### Location Data
- **Regional data**: country/state-level location (derived from anonymized IP, not GPS)

## Purposes of Data Use
(Fill in the purposes of data use, list by data type)

## Cross-Border Data Transfer
(Fill in the transfer arrangements and safeguards)

## Data Protection Measures
- **Anonymization**: IP addresses used only for regional location then discarded
- **Encryption**: transport encryption (TLS 1.3+), storage encryption (AES-256)
- **Retention**: up to 14 months (users may request deletion at any time)

## User Rights
- Right of access, rectification, withdrawal of consent, erasure (fill in how to exercise)

## Children's Data
If the user is a child under 13, we will require parental/guardian consent.

## Consent Management
1. Display this statement and obtain consent on first visit
2. Users may withdraw consent at any time via settings
3. Data collection stops immediately after consent is withdrawn

## Cookie Policy
### Cookie Types and Purposes
(Fill in cookie type, name, purpose, retention)

### Cookie Management
- Reject cookies via browser settings
""",
}


def get_legal_template(lang=None):
    """Return a per-language site privacy-policy template.

    Falls back to Simplified Chinese when ``lang`` is unknown/None.
    """
    if lang in SITE_PRIVACY_TEMPLATES:
        return SITE_PRIVACY_TEMPLATES[lang]
    return SITE_PRIVACY_TEMPLATES["zh-Hans"]
