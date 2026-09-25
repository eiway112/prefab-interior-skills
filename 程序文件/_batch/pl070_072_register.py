#!/usr/bin/env python3
"""PL-070 + PL-072 取源补登批：更新数据分类复核清单

移除 23 条旧条目（21 STALE_REVIEW + 2 STALE_BASELINE），
添加 23 条新条目（含补来源列后的新单元指纹）。
"""
import sys, json
from pathlib import Path

REGISTRY = Path(r'D:\Qoder-Files\装配式装修技能开发\_专题_技能合集策划\数据分类复核清单.json')

# ── 移除：23 条旧条目 ──────────────────────────────────────
STALE_IDS = [
    # STALE_REVIEW — BK examples.md (1)
    'prefab-bathroom-kitchen-system/examples.md#a2c90f7e025ae9081edc7ad3d452bf89e32ea3b71a31fb37aa6cb4b3d7eae15f:1',
    # STALE_REVIEW — BK reference.md (5)
    'prefab-bathroom-kitchen-system/reference.md#5d4d2a4c4df1793228dcc8d82a8ab9ceab529bc72c164b8d6993c239d3e9420e:1',
    'prefab-bathroom-kitchen-system/reference.md#cf907fb44abf19744ddfd65c23f69f218c930c2d71ce59e97579255e8049c38c:1',
    'prefab-bathroom-kitchen-system/reference.md#d99885f6c24760627cf30c229b49f44ec61678fff060fd13cc4d86279cf137cd:1',
    'prefab-bathroom-kitchen-system/reference.md#dcaaac7426c47cbf093cf5b9e1f8031ec732747e9bc04182c65d67ee6f42fa84:1',
    'prefab-bathroom-kitchen-system/reference.md#fed8c664f768c7fc4d115a3e84849423277566ec1cdfe5f1f2a1f48b7f74bcde:1',
    # STALE_REVIEW — PW reference.md (15)
    'prefab-partition-wall-solution/reference.md#0a50dbd7443cfde35bc51c5d9861896aa29a9232c01a35ef7bfe54d1b89956eb:1',
    'prefab-partition-wall-solution/reference.md#17d767e7c0bb5545fa5a268f51af772615bcad124e86704c629ec4ab0068cc42:1',
    'prefab-partition-wall-solution/reference.md#292cfb2d84b64a967bdbdcf2da8397f9091b271a4cd34aa0a5a033601eddbab8:1',
    'prefab-partition-wall-solution/reference.md#39514a1736632ba93153cad226f0a0ca303f3974f0b2924033380664232fbf40:1',
    'prefab-partition-wall-solution/reference.md#3d28bafa7fa0f110ffb57b872f11447721fe9a942e76122191e237fb50f261a8:1',
    'prefab-partition-wall-solution/reference.md#48269154e6f70fb48a97443e46783494166be538152b4cf7aece9fa63b788a4e:1',
    'prefab-partition-wall-solution/reference.md#5cc0a992a936fc0c91219ca9d2d8dc318713b57258f78af5be3786cb94f2bbc4:1',
    'prefab-partition-wall-solution/reference.md#a0c638b687c4d22e1860a5463ec3b9be312f715a58c89aad9a61fb321952064a:1',
    'prefab-partition-wall-solution/reference.md#be9f76bcd4b2c9d5775ef62e264a30cc91d0075e1527e77c92c81aa2f51b6072:1',
    'prefab-partition-wall-solution/reference.md#bed8de8c5ae57adbc51142849907434f98dfd88f848796886c4cc3da35d3a9cf:1',
    'prefab-partition-wall-solution/reference.md#c809757ec1a557feec4d2ce4a766c854d2da3a0c401ddd7eab5286f7d52e40bd:1',
    'prefab-partition-wall-solution/reference.md#d2f1f4d54a63c8cef232c90728a1f2d752e8e6579eb6cddbd651cb2d6deb99f9:1',
    'prefab-partition-wall-solution/reference.md#d6e3dcf7db1cd0da5f961a0535b8e923a4ee58d1e948d27061ddf624af9b64a1:1',
    'prefab-partition-wall-solution/reference.md#dd15aaddb2980aa4eaf9b09a9f1d6e6e7f0f34f9054e18c3af0151c86bb6ff99:1',
    'prefab-partition-wall-solution/reference.md#fee541bdd861290d64d3a6364b21462f5d88a486d4c1e9750136b16d3a74a482:1',
    # STALE_BASELINE — BK reference.md (1)
    'prefab-bathroom-kitchen-system/reference.md#4aeb478d4bbec402c37b5de3f1dccfbd3cebe17776b7a895a3e946777309f636:1',
    # STALE_BASELINE — PW reference.md (1)
    'prefab-partition-wall-solution/reference.md#5e953f2edc64c777d7d4899a7e3b2adcdffa10531a01d9119da21bf8da70b11b:1',
]

# ── 新增：23 条分类记录 ────────────────────────────────────
NEW_ENTRIES = {
    # ── BK examples.md 代码块（含比较表，整体 N 类）──
    'prefab-bathroom-kitchen-system/examples.md#d0a0acbc82b3f934a826850d388a99d125fda4a13712156e1449c32a4a0d742a:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '代码块（```markdown … ```）：内含选型比较表各列（防水可靠性/装饰效果/工期/成本/适用酒店类型/推荐度）均为文字等级评定（如"最优/良好/一般""最短/较长""较低/中等/较高"），无物理量数值与限值符号，不构成量化数据断言（按基准§一 N 类定义）'}]
    },

    # ── BK reference.md §3.2 关键防水节点表 ──
    # 表头行
    'prefab-bathroom-kitchen-system/reference.md#50ef3544c58759c8aa7165d6866b194c1283ca34b7572eb47b5903a3f997568f:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '表头行：列名定义（节点部位/构造要求/常见失效模式/性质与来源），非数据断言'}]
    },
    # 地漏周围（D 类：含"50mm"量化工艺控制值）
    'prefab-bathroom-kitchen-system/reference.md#ddac622f604c934733dfcd8d70937ce9305acc1f855253eefc053a63e51fa9c1:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'D',
            'reason': 'D类工艺控制值（"周围50mm范围加强"）：经验数据，非标准或检测报告规定值'}]
    },
    # 管根（N 类：纯定性）
    'prefab-bathroom-kitchen-system/reference.md#fa1fe2006bfc8ffec8005137b755f12546ce21361a8fcb55db575ae31d5f3ba9:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '定性工艺要求（"管根周围防水加强层，套管密封"），无物理量数值与限值符号，非量化断言'}]
    },
    # 阴角（N 类：纯定性）
    'prefab-bathroom-kitchen-system/reference.md#30fc8a58fbf70e7ce940dda9b00c6b5b34f0c9a79d28cfd0aace57af9f2e6928:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '定性工艺要求（"圆弧过渡+防水加强层"），无物理量数值与限值符号，非量化断言'}]
    },
    # 门槛/挡水（D 类：含"≥20mm"量化工艺控制值）
    'prefab-bathroom-kitchen-system/reference.md#c3dc1172b89f8a2035930008ff81049bcec5d882c029332c81e5d919a2486785:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'D',
            'reason': 'D类工艺控制值（"挡水高度≥20mm"）：经验数据，非标准或检测报告规定值'}]
    },
    # 底盘与排水管接口（N 类：纯定性）
    'prefab-bathroom-kitchen-system/reference.md#ca07c5c585d0be61f37c637eaf679b02801f59f448b3a6b1746a8fe2d5089f6a:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '定性工艺要求（"专用法兰+橡胶密封垫圈"），无物理量数值与限值符号，非量化断言'}]
    },

    # ── PW reference.md fc 包络表 ──
    # 表头行
    'prefab-partition-wall-solution/reference.md#cfdcbfd573657d21105867927538376402478c6dba451423756d722ec64db042:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '表头行：列名定义（板材/常用厚度/fc范围/与关键频段关系/复算来源），非数据断言'}]
    },
    # 10 个数据行（C 类：派生复算值）
    'prefab-partition-wall-solution/reference.md#e51f2283164969e218dcc093311821c7914814f8ae41d4c299d3d6440e27a8ca:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#a1a99b215d3a672e0f9f2911d7721ecc7f35e51f634919ab20f7897ceaa3af9d:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#ebadf253a30d77efa2df5a0471baed4d83c7cbf1c3733e0df4726d8d4805ba94:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#2af58e767875def1bd3c17af0ce4e0d2479efe46ffc166375c4763e9ea5e067b:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#3f11b28c9f21d01576e7af46be58a5c74d5c79fb4392f5749254f8706166958a:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#40807acf8f44701687f28dd9acf877db056ac05275a5e99507f93bb7128c1d8c:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#87873dff7848ca519d80d6416ab1327a6d431122d6c874588e37764c59f23824:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#354467e7cb06e1a88d69441d0bf6b83e3b0ff687a82b788a3df546b62d3c2460:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#005aa05da042078310d6002287c4b1b3b7ae71e6a7e52d2e40ac1ce91d1522b8:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#e9b06bf5c1de2881134ceef752970837164e2f80b519302c62eccdddd3c8cb10:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表声明参数域（ρ/E/h）代入吻合频率修正公式包络计算得出，非直接引用标准或检测报告'}]
    },

    # ── PW reference.md Δfc 搭配表 ──
    # 表头行
    'prefab-partition-wall-solution/reference.md#b46a6184222e1f40fc5190c9c55e9acf07fb170a39eaee836a36d4a77b55535b:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'N',
            'reason': '表头行：列名定义（组合/fc1/fc2/频率差Δfc/有效性判定/复算来源），非数据断言'}]
    },
    # 4 个数据行（C 类：派生复算值）
    'prefab-partition-wall-solution/reference.md#472b9f3c145271b24e5585bbb5fe41a0bfce4cf22ebfed3072bb2e47f8b1a773:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表标称基准参数代入吻合频率修正公式按统一标称基准复算，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#04f579bf8a8e9037ad4c5a05afd9451bb4144fac4824607e71fd13dc2c1bb44e:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表标称基准参数代入吻合频率修正公式按统一标称基准复算，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#ea6ad161be67cd7ef83c77c152e504db6b4e9e87f5a30b9d47ed0f2f220fb526:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表标称基准参数代入吻合频率修正公式按统一标称基准复算，非直接引用标准或检测报告'}]
    },
    'prefab-partition-wall-solution/reference.md#84916faa5b3ba9b8c466d4471971bd5823c10d34e79ccc7ac0394e1f09e18b0c:1': {
        'segments': [{'start': 0, 'end': 'AUTO', 'class': 'C',
            'reason': '派生复算值：由参数表标称基准参数代入吻合频率修正公式按统一标称基准复算，非直接引用标准或检测报告'}]
    },
}


def main():
    registry = json.loads(REGISTRY.read_text(encoding='utf-8-sig'))

    # 1. 移除旧条目
    removed_r, removed_b = 0, 0
    for sid in STALE_IDS:
        if sid in registry['records']:
            del registry['records'][sid]
            removed_r += 1
        elif sid in registry.get('baseline', {}):
            del registry['baseline'][sid]
            removed_b += 1
        else:
            print(f'WARNING: not found: {sid[:60]}...')
    print(f'Removed: {removed_r} records + {removed_b} baseline = {removed_r + removed_b}')

    # 2. 扫描文件获取单元文本长度（用于填充 end='AUTO'）
    sys.path.insert(0, str(Path(__file__).parent.parent / '程序文件'))
    from validate_governance import data_content_units

    RUNTIME = Path.home() / '.qoder' / 'skills'
    affected_files = set()
    for uid in NEW_ENTRIES:
        path_part = uid.split('#')[0]
        affected_files.add(path_part)

    unit_text_lens = {}
    for rel in sorted(affected_files):
        raw = (RUNTIME / rel).read_bytes()
        parsed = data_content_units(rel, raw)
        for u in parsed['units']:
            unit_text_lens[u['id']] = len(u['text'])

    # 3. 添加新条目（填充实际 end 值）
    added = 0
    for uid, entry in NEW_ENTRIES.items():
        if uid in registry['records']:
            print(f'SKIP (exists): {uid[:60]}...')
            continue
        text_len = unit_text_lens.get(uid)
        if text_len is None:
            print(f'ERROR: unit not found in scan: {uid[:60]}...')
            sys.exit(1)
        for seg in entry['segments']:
            if seg['end'] == 'AUTO':
                seg['end'] = text_len
        registry['records'][uid] = entry
        added += 1
        cls = entry['segments'][0]['class']
        print(f'  + [{cls}] {uid[:70]}...')

    print(f'Added: {added}')

    # 4. 写回
    REGISTRY.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8'
    )
    print(f'Done. Registry: {REGISTRY}')


if __name__ == '__main__':
    main()
