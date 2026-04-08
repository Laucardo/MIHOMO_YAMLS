import os
import yaml
from urllib.parse import quote
from datetime import datetime

# ================= 配置常量 =================
SOURCE_BASE = "THEYAMLS"
OUTPUT_BASE = "Overwrite/THENEWOPENCLASH"
REPO_RAW = f"https://raw.githubusercontent.com/{os.getenv('GITHUB_REPOSITORY')}/main"

# 处理 YAML 中的 ! 标签
yaml.add_multi_constructor("!", lambda loader, suffix, node: None, Loader=yaml.SafeLoader)


def get_current_date():
    return datetime.now().strftime("%Y-%m-%d")


def to_commented_yaml(obj) -> str:
    """
    将 Python dict/list/scalar 序列化为 YAML 格式字符串，
    每行前面加 '# ' 前缀，使整块内容成为注释。
    用于把源 YAML 的 proxy-providers 内容原样注释进覆写文件。
    """
    raw = yaml.dump(obj, allow_unicode=True, default_flow_style=False, indent=2)
    lines = []
    for line in raw.splitlines():
        lines.append(("# " + line) if line.strip() else "#")
    return "\n".join(lines)


# ==============================================================
# [YAML] 块操作符参考说明（全部注释，仅供用户查阅）
# ==============================================================
YAML_OPERATOR_REFERENCE = """\
# ==========================================================
# 【YAML 块覆写操作符速查表】
# ----------------------------------------------------------
# 操作符    作用
# ----------------------------------------------------------
#  key      默认合并：Hash 类型递归合并（子键不存在则新增），
#           其他类型（字符串、数字等）直接覆盖原值。
#
#  key!     强制覆盖：不管原来是什么，整个值全部替换。
#           常用于替换整个数组或整个子配置块。
#
#  key+     数组后置追加：把新元素加到数组末尾。
#           原数组不变，只在结尾增加内容。
#
#  +key     数组前置插入：把新元素加到数组开头。
#           常用于让自定义规则优先于原有规则生效。
#
#  key-     数组差集删除：从数组中移除指定元素。
#           若目标不是数组，则直接删除该键。
#
#  key*     批量条件更新：配合 where/set 子句，
#           在数组/Hash 中找到匹配的元素后批量修改。
#
#  <key>后缀   同上所有操作符，用于键名本身含有特殊字符（如 . - /）时。
#  +<key>      数组前置插入的 <> 写法。
# =========================================================="""

# ==============================================================
# 各操作符使用示例（全部注释，供用户复制取用）
# ==============================================================
YAML_EXAMPLES = """\
# ==========================================================
# 【proxy-providers 订阅 URL 替换】
# ----------------------------------------------------------
# 作用：把配置文件里某个 proxy-provider 的订阅链接换成你自己的。
#
# 步骤：
#   1. 在下方找到对应 provider 的名称（name: xxx）
#   2. 把下面示例里的 name: 改成那个名称
#   3. 把 url: 后面的地址换成你的订阅链接
#   4. 删除这几行前面的 # 号，保存即可生效
#
# 示例（把名为"机场A"的 provider 订阅链接替换为新链接）：
#
# proxy-providers*:
#   where:
#     name: '机场A'
#   set:
#     url: 'https://你的订阅链接'
#
# 如果有多个 provider 需要替换，复制多段即可：
#
# proxy-providers*:
#   where:
#     name: '机场B'
#   set:
#     url: 'https://你的第二个订阅链接'
#
# ⚠️  注意：proxy-providers 原始内容已在本文件末尾完整复制并注释，
#       可直接对照查看各 provider 的名称和原有配置内容。
# ==========================================================

# ==========================================================
# 【1. 默认合并】key: value
# ----------------------------------------------------------
# 作用：修改或新增配置中的某个字段。
#       Hash 类型时递归合并（只改指定字段，其余字段保留）。
#       非 Hash 类型时直接覆盖原值。
# ----------------------------------------------------------
# 示例：开启 allow-lan 并修改混合端口
# allow-lan: true
# mixed-port: 7893
#
# 示例：只修改 dns 中的两个字段，其余 dns 字段保持不变
# dns:
#   enable: true
#   cache-algorithm: lru
#
# 示例：合并修改 tun 配置（只改指定字段，其余保留）
# tun:
#   enable: true
#   stack: gvisor
# ==========================================================

# ==========================================================
# 【2. 强制覆盖】key!: value
# ----------------------------------------------------------
# 作用：整个替换，不做任何合并。
#       常用于替换整个规则列表、整个 dns 块等。
# ----------------------------------------------------------
# 示例：强制替换整个 rules 数组（原有规则全部丢弃）
# rules!:
#   - DOMAIN-SUFFIX,example.com,DIRECT
#   - MATCH,PROXY
#
# 示例：强制替换 dns 里的 fake-ip-filter 数组
# dns:
#   fake-ip-filter!:
#     - '*.lan'
#     - 'my.custom.domain'
#
# 示例：强制替换整个 dns 块（完全自定义 DNS 配置）
# dns!:
#   enable: true
#   nameserver:
#     - '223.5.5.5'
#     - '119.29.29.29'
# ==========================================================

# ==========================================================
# 【3. 数组后置追加】key+: [...]
# ----------------------------------------------------------
# 作用：在已有数组末尾追加新元素，原有内容不变。
#       常用于在规则末尾追加自定义规则。
# ----------------------------------------------------------
# 示例：向 rules 末尾追加两条规则
# rules+:
#   - DOMAIN-SUFFIX,example.com,DIRECT
#   - IP-CIDR,192.168.0.0/16,DIRECT
#
# 示例：向 dns.nameserver 末尾追加 DNS 服务器
# dns:
#   nameserver+:
#     - '1.1.1.1'
#     - '8.8.8.8'
# ==========================================================

# ==========================================================
# 【4. 数组前置插入】+key: [...]
# ----------------------------------------------------------
# 作用：在已有数组开头插入新元素（规则越靠前越先生效）。
#       常用于让自定义规则优先于原有规则匹配。
# ----------------------------------------------------------
# 示例：向 rules 开头插入高优先级规则
# +rules:
#   - DOMAIN-SUFFIX,priority.com,DIRECT
#   - DOMAIN,my.local,DIRECT
#
# 示例：向 dns.nameserver 开头插入首选 DNS
# dns:
#   +nameserver:
#     - '223.5.5.5'
# ==========================================================

# ==========================================================
# 【5. 数组差集删除】key-: [...]
# ----------------------------------------------------------
# 作用：从数组中移除指定元素；若目标不是数组，则删除整个键。
# ----------------------------------------------------------
# 示例：从 dns.nameserver 中移除不需要的 DNS
# dns:
#   nameserver-:
#     - '8.8.8.8'
#     - '8.8.4.4'
#
# 示例：从 rules 中删除某条规则
# rules-:
#   - DOMAIN-SUFFIX,old.com,REJECT
#
# 示例：删除整个键（值留空）
# dns:
#   cache-algorithm-:
# ==========================================================

# ==========================================================
# 【6. 批量条件更新】key*: where/set
# ----------------------------------------------------------
# 作用：在数组或 Hash 中，按条件找到匹配项后批量修改。
#       where 写匹配条件，set 写要修改的内容（支持上述所有操作符）。
# ----------------------------------------------------------
# where 支持的条件类型：
#   name: 'xxx'        精确匹配 name 字段等于 xxx
#   name: '/^HK/'      用正则表达式匹配（以 /.../ 包裹）
#   type: url-test     匹配 type 字段
#   proxies: ['x']     匹配 proxies 数组中包含指定元素的项
#   key: 'xxx'         用于 Hash 集合，匹配键名
#   value: 'xxx'       用于字符串数组，匹配字符串值
# ----------------------------------------------------------
# 示例：给所有 url-test 类型策略组的 proxies 末尾追加节点
# proxy-groups*:
#   where:
#     type: url-test
#   set:
#     proxies+:
#       - '我的自定义节点'
#
# 示例：用正则匹配名称含 HK 的策略组，在 proxies 开头插入节点
# proxy-groups*:
#   where:
#     name: '/^HK/'
#   set:
#     +proxies:
#       - '香港专线'
#
# 示例：给名为"手动选择"的策略组追加节点
# proxy-groups*:
#   where:
#     name: '手动选择'
#   set:
#     proxies+:
#       - '我的节点名'
#
# 示例：修改所有 socks5 类型节点的端口
# proxies*:
#   where:
#     type: socks5
#   set:
#     port: 1080
#
# 示例：删除规则列表中所有以 REJECT 结尾的规则
# rules*:
#   where:
#     value: '/,REJECT$/'
#   set:
#     value: ~
# ==========================================================

# ==========================================================
# 【7. <key> 语法（键名含特殊字符时使用）】
# ----------------------------------------------------------
# 当键名包含 . - / 等特殊字符时，用 <key> 包裹键名。
# 后缀支持：+ - ! *
# 前置插入写法：+<key>
# ----------------------------------------------------------
# 示例：强制覆盖键名含特殊字符的字段
# <dns>!:
#   enable: false
#
# 示例：后置追加
# dns:
#   <nameserver>+:
#     - '8.8.8.8'
#
# 示例：前置插入
# dns:
#   +<nameserver>:
#     - '119.29.29.29'
#
# 示例：批量条件更新
# <proxy-groups>*:
#   where:
#     type: url-test
#   set:
#     interval: 300
# ==========================================================

# ==========================================================
# 【8. 组合操作】同一个块内可同时写多个操作符
# ----------------------------------------------------------
# 示例：同时删除旧 DNS 并前置插入新 DNS
# dns:
#   nameserver-:
#     - '8.8.8.8'
#   +nameserver:
#     - '223.5.5.5'
#
# 示例：同时前置和后置追加
# dns:
#   +nameserver:
#     - '119.29.29.29'
#   nameserver+:
#     - '1.0.0.1'
# ==========================================================\"\""""


def build_yaml_block(providers: dict) -> str:
    """
    生成完整的 [YAML] 覆写块：
    - [YAML] 标记行（新版 OpenClash 的块识别标记，唯一不注释的行）
    - 操作符参考 + 使用示例（全注释）
    - proxy-providers 原始内容逐字复制并注释（对照修改后取消注释即可用）
    """
    lines = []

    lines.append("")
    lines.append("# ==========================================================")
    lines.append("# 【YAML 块覆写区域】")
    lines.append("# [YAML] 是新版 OpenClash 的识别标记，这一行本身不可注释。")
    lines.append("# 所有覆写内容写在 [YAML] 之后，注释状态不生效，取消注释才生效。")
    lines.append("# ==========================================================")
    lines.append("[YAML]")
    lines.append("")
    lines.append(YAML_OPERATOR_REFERENCE)
    lines.append("")
    lines.append(YAML_EXAMPLES)
    lines.append("")

    # proxy-providers 原始内容
    lines.append("# ==========================================================")
    lines.append("# 【proxy-providers 原始配置（从源文件直接复制，全部注释）】")
    lines.append("# ----------------------------------------------------------")
    lines.append("# 以下内容原样复制自源 YAML 的 proxy-providers 块，")
    lines.append("# 全部注释，不会对你的配置产生任何影响。")
    lines.append("#")
    lines.append("# 使用方法：")
    lines.append("#   在上方【proxy-providers 订阅 URL 替换】示例中，")
    lines.append("#   对照下方的 provider 名称（name: xxx），")
    lines.append("#   填写对应名称和你的订阅链接，取消注释后即可生效。")
    lines.append("# ==========================================================")
    lines.append("")

    for name, config in providers.items():
        lines.append(f"# --- provider: {name} ---")
        provider_block = {name: config}
        lines.append(to_commented_yaml(provider_block))
        lines.append("")

    return "\n".join(lines)


def gen_openclash_new():
    print("🚀 开始生成新版 OpenClash 覆写配置（纯 YAML 块格式）...")
    os.makedirs(OUTPUT_BASE, exist_ok=True)

    total_count = 0
    categories = {}

    for root, dirs, files in os.walk(SOURCE_BASE):
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if not file.endswith(('.yaml', '.yml')):
                continue

            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                providers = data.get('proxy-providers', {}) if isinstance(data, dict) else {}
                if not providers:
                    continue

                rel_dir = os.path.relpath(root, SOURCE_BASE)
                out_dir = os.path.join(OUTPUT_BASE, rel_dir)
                os.makedirs(out_dir, exist_ok=True)

                raw_url = f"{REPO_RAW}/{quote(f'{SOURCE_BASE}/{rel_dir}/{file}'.replace(os.sep, '/'))}"
                out_name = os.path.splitext(file)[0] + ".yaml"
                out_file = os.path.join(out_dir, out_name)
                provider_keys = list(providers.keys())

                content_lines = []
                content_lines.append(f"# OpenClash 覆写模块 - {file}")
                content_lines.append(f"# 生成日期：{get_current_date()}")
                content_lines.append(f"# 源文件地址：{raw_url}")
                content_lines.append(f"# 格式：新版 OpenClash 覆写模块（[YAML] 块覆写）")
                content_lines.append("#")
                content_lines.append("# 本文件只包含 [YAML] 块覆写内容。")
                content_lines.append("# 所有覆写内容默认全部注释，加载后不影响你的任何现有配置。")
                content_lines.append("# 按需找到对应内容，取消注释即可启用。")
                content_lines.append(build_yaml_block(providers))

                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(content_lines))

                if rel_dir not in categories:
                    categories[rel_dir] = []
                categories[rel_dir].append({
                    'name': out_name,
                    'source': file,
                    'providers': provider_keys,
                    'raw_url': f"{REPO_RAW}/{quote(f'{OUTPUT_BASE}/{rel_dir}/{out_name}'.replace(os.sep, '/'))}"
                })

                total_count += 1
                print(f"  ✅ 生成: {out_file}  ({len(provider_keys)} 个 provider)")

            except Exception as e:
                print(f"  ⚠️ 处理出错 {file}: {e}")

    # ==== 分类 README ====
    for cat, items in categories.items():
        cat_path = os.path.join(OUTPUT_BASE, cat)
        readme_lines = [
            f"# 📁 {cat}",
            "",
            "此目录为新版 OpenClash 覆写模块（YAML 格式）。",
            "文件内容全部注释，不会影响原始配置，按需取消注释启用。",
            "",
            "| 文件名 | 包含的 proxy-providers | Raw 链接 |",
            "| :--- | :--- | :--- |"
        ]
        for item in sorted(items, key=lambda x: x['name']):
            prov_str = "、".join(item['providers'])
            readme_lines.append(
                f"| **{item['name']}** | {prov_str} | [查看/下载]({item['raw_url']}) |"
            )
        readme_lines.extend(["", "---", "[🔙 返回总览](../README.md)"])
        with open(os.path.join(cat_path, "README.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(readme_lines))

    # ==== 主 README ====
    main_readme = [
        "# 📦 OpenClash 新版覆写模块",
        "",
        "基于新版 OpenClash `[YAML]` 块覆写格式自动生成。",
        "",
        "**设计原则：**",
        "- 文件内所有覆写内容**默认全部注释**，加载后对你的现有配置零影响",
        "- `proxy-providers` 原始内容完整复制进文件，对照修改 `url` 后取消注释即可替换订阅链接",
        "- 提供完整操作符参考和逐类示例，按需取消注释即可实现规则追加、节点插入、批量更新等",
        "",
        "**与旧版 `.conf` 的区别：**",
        "",
        "| | 旧版 `.conf` | 新版 `.yaml` |",
        "| :--- | :--- | :--- |",
        "| url 替换 | `ruby_map_edit` + `$EN_KEY` 环境变量 | 直接写订阅链接，或用 `proxy-providers*` 条件更新 |",
        "| 修改能力 | 仅能替换指定路径的值 | 合并/强制覆盖/追加/删除/批量条件更新 |",
        "| 默认行为 | 启用后立即覆写 | 全部注释，零影响，按需解注释 |",
        "",
        "## 📂 目录",
        "",
        "| 分类 | 文件数 |",
        "| :--- | :--- |"
    ]
    for cat in sorted(categories.keys()):
        count = len(categories[cat])
        main_readme.append(f"| 📁 **[{cat}](./{cat}/README.md)** | {count} 个 |")

    main_readme.extend([
        "",
        "## 🚀 使用方法",
        "",
        "1. 找到对应分类目录，复制 `.yaml` 文件的 Raw URL",
        "2. OpenClash → 覆写设置 → 覆写模块 → 添加该 URL",
        "3. 打开文件，找到文件末尾的 `proxy-providers` 原始内容",
        "4. 对照 `name:` 确认 provider 名称，参考文件内【订阅 URL 替换】示例写好替换内容",
        "5. 取消注释对应内容保存，重启插件生效",
        "",
        "[🏠 返回主页](../../README.md)"
    ])

    with open(os.path.join(OUTPUT_BASE, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(main_readme))

    print(f"✅ 完成！共生成 {total_count} 个覆写文件。")


if __name__ == "__main__":
    gen_openclash_new()
