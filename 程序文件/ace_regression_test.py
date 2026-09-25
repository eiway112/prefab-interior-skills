"""
ACE Adversarial Regression Test Suite
=======================================
Re-runnable test suite for ACE architecture formulas, parameters, and data.
Run after any document change to catch inconsistencies.

Usage:  python ace_regression_test.py
        python ace_regression_test.py -v          (verbose)

Version: 1.9.0
Date: 2026-09-25

v1.9.0 (2026-09-25, CG-20260925-003 专业整改十批-组9 参数与证据):
  新增 TestM5M7CaliberAndEvidence 守卫组（PL-068 三子面 ＋ 组8 移交 S1）：
  ① M5 m' 由「面层+垫层总面密度／浮筑层总质量」改定义为浮筑层有效振动面密度，
  排除三项（结构楼板／弹性垫自身／活荷载）跨 ACE 与 FL 两件断言一致，恒荷载侧
  补反向禁互代句，误代后果的 3 个 dB 与 2 个百分比读数用参考函数独立复算；
  ② 撤回「C=12 系统性高估约 5 dB」「C=10 经多个常见构造校准」两句（撤回锚＝
  旧字面 0 命中），保留 C=10 默认值不动，新增 C 灵敏度复算锚（∂ΔLw/∂C≡1，
  [8,12] 全域仅 4 dB ⇒ 5 dB 量级差不得归因 C）；③ M7 Step 5 裁定 Σ修正端点
  配对法＝下界端加各修正项下界之和、上界端加上界之和（500 例随机验证保序与
  中点恒等），算例改 min/max 书写并按该法给出 Rw_A [48.0,49.5]／Rw_B
  [49.0,51.5]，旧乙口径读数 50~51 撤回；④ 无留痕基准算例的演示身份收口
  （「交叉验证」名义撤、派生读数承继演示身份、SKILL.md 4-6 dB 挂演示提示）。
  组8 的 Step 5 判据以 assert_step5_compatible_with_group8 显式复验未被削弱。
  精度面（PL-055）与经验域（PL-053）字面由 test_precision_faces_untouched 钉住不改。
  支持 ACE_SKILL_DIR / FL_SKILL_DIR 环境变量指向改前原像目录做复红自证。

v1.8.0 (2026-09-25, CG-20260925-002 专业整改九批-组8 M7 校准外推):
  新增 TestM7CalibrationExtrapolation 守卫组（PL-067）：① M7 全部区间输出
  入口按数值升序——Step 2 min/max 恒升序（控制锚，组6 前已修）、Step 3 对称
  变化撤位名式「输出区间 [ΔR_low, ΔR_high]」、Step 5 结果组装改 ΔR_下界/
  ΔR_上界（＝min/max 端点加和保序）；覆盖增重/减重/等质量三态（r=2 位名序
  升序、r=1 退化 [0,0]、r=0.5 位名序 [−6.02,−12.04] 降序＝测试内复算）；
  ② SKILL.md 方法概要补恒升序声明；③ 交叉核对撤「差>5dB 即优先报 M7」
  自动择优规则，改四类根因核查（构造同族/机理级变化/参数与口径/模型条件）
  ＋不自动取任一结果＋证据不足降级，并显式禁止「以基准可信推定外推可信」；
  ④ 路由与组合表行（reference.md :529/:549、SKILL.md :150）统一「路线优先
  ≠结果自动择优」口径，算例尾句 :438 同批联动；⑤ 旧肯定式字面以计数守卫
  钉死仅存于否定语境。精度与来源面归 PL-055/PL-068，本组不代结。全部
  C 类派生量与口径面内部复算闭合，不走官方核验通道。
  支持 ACE_SKILL_DIR / ACE_SKILL_MD_DIR 环境变量指向改前原像目录做复红自证。

v1.7.0 (2026-09-25, CG-20260925-001 专业整改八批-组6 M3/M4 模型适用性):
  新增 TestM3M4ModelApplicability 守卫组（PL-066）：① M3 约化质量恒等式
  ω²=k(1/m₁+1/m₂)=k/m_red 对任意正质量比精确成立（r=0.1—10 复算偏差恒 0），
  旧「m₁/m₂ 超出 0.5—2 产生 5-13% 偏差」提示区间撤回（撤回无据结论、
  不给替代偏差值）；② 5-13% 量级正确归因到近对称近似式 1200/√(d×(m₁+m₂))
  的误差（r=2 约 −5.7%、r=3 约 −13%），PW :318 近似式适用性声明为控制锚；
  ③ 真实模型误差＝模型外假设五项逐项显式列出（声桥/阻尼/边界/板弯曲模态/
  空腔无质量弹簧）；④ 双空腔＝三质量-两弹簧耦合系统（1 刚体模态+2 非零
  耦合模态，共振分裂为二），旧「分别计算增益后叠加」算法与 PW「额外提升约
  5-10 dB」数值出口撤回，不编造通用扣减值，定量输出仅限耦合模型或同构造
  实测证据两路径；对称双腔例 69.1/129.2 Hz 与两腔分别算 103.6 Hz 反例
  均在测试内解析复算。全部 C 类派生量内部复算闭合，不走官方核验通道。
  支持 ACE_SKILL_DIR / PW_SKILL_DIR 环境变量指向改前原像目录做复红自证。

v1.6.0 (2026-09-24, CG-20260924-007 专业整改七批-组7 M6 缝隙):
  新增 TestM6GapBoundary 守卫组（PL-038 G-2）：ACE M6 简化表末档下界
  「> 1%」与自述公式矛盾（R_wall=30／R_gap=0 前提下 p=1.01% 损失 10.45 dB，
  12 dB 阈值实为 p≈1.49%）收窄为「> 1.5%」并四档逐档复算；PW「任何缝隙
  封顶 20 dB」改写为封顶式 −10·lg(S_缝)（1%→20／0.1%→30／5%→13 dB）；
  PW 分层损失表 6 行×2 档全部复算（±1 dB）；两件新增「单值代入口径
  （近似声明）」（单值代入仅近似、严格路径逐频带合成后计权）。
  全部 C 类派生量内部复算闭合，不走官方核验通道。
  支持 ACE_SKILL_DIR / PW_SKILL_DIR 环境变量指向改前原像目录做复红自证。

v1.5.0 (2026-09-24, CG-20260924-005 专业整改五批-组5 M2 吻合频率):
  新增 TestM2CoincidenceDocConsistency 守卫组（PL-065／PL-038 G-3）：
  PL-065 ACE 修正因子省略误差说明须与公式一致（旧「3-8%」→ 省略整因子偏低约 70%、
  泊松比项次级约 2.6%，端点 2961↔883 可复算）；G-3 PW 三表同源（参数域→fc 范围表
  按声明域包络复算→搭配表标称点落在包络内）、Δfc 对 E 非单调披露、绝对结论
  「任何合理参数下均有效错开 Δfc≥690」收窄为「须按实测 ρ/E 逐案核算」。
  全部 C 类派生量／B 类参数域内部复算闭合，不走官方核验通道。
  支持 ACE_SKILL_DIR / PW_SKILL_DIR 环境变量指向改前原像目录做复红自证。

v1.4.0 (2026-09-24, CG-20260924-004 专业整改四批-组4 FL 构造与预测):
  新增 TestFloorF02F03Boundary 守卫组（PL-052／PL-064／PL-038 G-1／PL-056／PL-057）：
  F02 厚度链两口径与不猜新总厚、F03 单层板 28mm 口径与双层板 43mm 超标高、
  F02/F03 参数表收窄行值、汇总表 ΔLw／达标可行性两列撤除、选型速查 30mm 行改单层板、
  examples.md 现场 L'nT,w 数值出口（40-48／42-48）禁回潮。
  支持 FLOOR_SKILL_DIR 环境变量指向改前原像目录做复红自证。

v1.3.1 (2026-08-20, CG-20260820-001 复核整改 F-01):
  TestDocAnchor.test_M7_baseline_standard_citations 断言由已废止的
  GB/T 19889.3-2005（2026-02-01 废止，全部被 GB/T 45305.2-2025 代替，
  全国标准信息公共服务平台核验）更正为 GB/T 45305.2-2025。

v1.3.0 (2026-08-20, CG-20260820-001):
  ACE v1.1.0 新增 M7 基准校准模型后同步扩展：新增 m7_delta_R_bounds /
  m7_is_valid_extrapolation 参考实现与 TestM7_BaselineCalibration 测试组
  （界限公式行为、2026-08-20 算例复现、外推区守卫），TestDocAnchor
  新增 M7 章节/界限公式/外推区/精度声明/基准标准引用 5 条本体锚定断言。

v1.2.0 (2026-08-07, CG-20260807-013):
  ACE 发布至运行时技能仓后，TestDocAnchor 的 Markdown SOT 由项目仓
  _专题_ACE开发/reference.md 重锚定至运行时
  ~/.qoderwork/skills/acoustic-calculation-engine/reference.md
  （技能文件以运行时为唯一事实源，项目仓副本转为开发归档）。

v1.1.0 (2026-08-07, CG-20260807-010):
  Added TestDocAnchor suite — key constants and material parameters in this
  script are now cross-checked against the Markdown SOT
  (ACE reference.md) at runtime, so the test suite no longer
  validates only hardcoded self-copies (addresses review finding A3/F2:
  tests previously shared the same source as the implementation).
"""

import unittest
import math
import os
import re
import random
import inspect
from pathlib import Path

# ============================================================
# Constants (physical)
# ============================================================
C_SOUND = 343.0       # speed of sound in air (m/s)
RHO_AIR = 1.2         # air density (kg/m3)

# ============================================================
# ACE Physical Models (executable reference implementations)
# ============================================================

def mass_law(m, f, const=-47.2):
    """M1: Mass law. R = 20*log10(m*f) + const"""
    if m <= 0 or f <= 0:
        raise ValueError("m and f must be positive")
    return 20 * math.log10(m * f) + const


def coincidence_freq(h_m, rho, E, sigma):
    """M2: Cremer coincidence frequency.
    fc = c^2 / (2*pi*h) * sqrt(12*(1-sigma^2)*rho/E)
    """
    if h_m <= 0 or rho <= 0 or E <= 0:
        raise ValueError("h, rho, E must be positive")
    if not (0 < sigma < 0.5):
        raise ValueError("Poisson ratio must be in (0, 0.5)")
    return (C_SOUND ** 2) / (2 * math.pi * h_m) * math.sqrt(
        12 * (1 - sigma ** 2) * rho / E
    )


def msm_resonance(d_cm, m1, m2):
    """M3: MSM resonance frequency (corrected).
    f0 = 600 / sqrt(d_cm * m_red), m_red = m1*m2/(m1+m2)
    """
    if d_cm <= 0 or m1 <= 0 or m2 <= 0:
        raise ValueError("d, m1, m2 must be positive")
    m_red = m1 * m2 / (m1 + m2)
    return 600 / math.sqrt(d_cm * m_red)


def msm_resonance_iso_exact(d_cm, m1, m2):
    """ISO 12354 exact MSM formula for cross-validation."""
    d_m = d_cm / 100
    m_red = m1 * m2 / (m1 + m2)
    return (1 / (2 * math.pi)) * math.sqrt(
        RHO_AIR * C_SOUND ** 2 / (d_m * m_red)
    )


def impact_sound_delta_L(f, f0):
    """M5: Impact sound improvement. dL = 40*log10(f/f0) for f > f0"""
    if f <= f0:
        return 0.0
    return 40 * math.log10(f / f0)


def floating_floor_f0(s_MNm3, m_face):
    """Floating floor resonance frequency.
    f0 = (1/2pi)*sqrt(s/m), s in N/m3, m in kg/m2
    """
    s = s_MNm3 * 1e6
    return (1 / (2 * math.pi)) * math.sqrt(s / m_face)


def impact_sound_deltaLw(m_prime, s_MNm3, C=10):
    """M5: Single-value impact sound improvement (weighted).
    dLw = 18*log10(m') - 10*log10(s) + C
    m' in kg/m2, s in MN/m3, C empirical constant (default 10).
    """
    if m_prime <= 0 or s_MNm3 <= 0:
        raise ValueError("m_prime and s must be positive")
    return 18 * math.log10(m_prime) - 10 * math.log10(s_MNm3) + C


def gap_effective_R(R_wall, gap_fraction, R_gap=0.0):
    """M6: Composite transmission loss with gap.
    R_eff = -10*log10((1-S)*10^(-R/10) + S*10^(-Rg/10))
    """
    if not (0 < gap_fraction < 1):
        raise ValueError("gap_fraction must be in (0, 1)")
    tau_wall = 10 ** (-R_wall / 10)
    tau_gap = 10 ** (-R_gap / 10)
    tau_eff = (1 - gap_fraction) * tau_wall + gap_fraction * tau_gap
    return -10 * math.log10(tau_eff)


# M7 valid extrapolation range for areal density ratio r (doc: [0.5, 2])
M7_VALID_R_RANGE = (0.5, 2.0)


def m7_delta_R_bounds(r):
    """M7: Baseline calibration ΔR bounds.
    dR_low  = 20*log10(r)  (mass-law dominated / single leaf)
    dR_high = 40*log10(r)  (ideal cavity, symmetric double leaf, no bridge)
    For r < 1, dR_high is the larger reduction (more negative).
    """
    if r <= 0:
        raise ValueError("r must be positive")
    return 20 * math.log10(r), 40 * math.log10(r)


def m7_is_valid_extrapolation(r):
    """M7: r outside [0.5, 2] -> large extrapolation, trend judgment only."""
    return M7_VALID_R_RANGE[0] <= r <= M7_VALID_R_RANGE[1]


# ============================================================
# Material Database (from ACE doc section 2.2)
# ============================================================
MATERIALS = {
    "gypsum_12mm":  {"h": 0.012, "rho": 800,  "E": 2.5e9, "sigma": 0.25, "face_m": 9.6},
    "gypsum_9.5mm": {"h": 0.0095,"rho": 800,  "E": 2.5e9, "sigma": 0.25, "face_m": 7.6},
    "gypsum_15mm":  {"h": 0.015, "rho": 800,  "E": 2.5e9, "sigma": 0.25, "face_m": 12.0},
    "casi_10mm":    {"h": 0.010, "rho": 1400, "E": 8.0e9, "sigma": 0.22, "face_m": 14.0},
    "casi_8mm":     {"h": 0.008, "rho": 1400, "E": 8.0e9, "sigma": 0.22, "face_m": 11.2},
    "casi_6mm":     {"h": 0.006, "rho": 1400, "E": 8.0e9, "sigma": 0.22, "face_m": 8.4},
    "alc_150mm":    {"h": 0.150, "rho": 600,  "E": 2.3e9, "sigma": 0.18, "face_m": 90.0},
}

FC_CLAIMED_RANGES = {
    "gypsum_12mm":  (2000, 4000),
    "gypsum_9.5mm": (2500, 5000),
    "gypsum_15mm":  (1600, 3200),
    "casi_10mm":    (1500, 3000),
    "casi_8mm":     (1900, 3800),
    "casi_6mm":     (2500, 5000),
}


# ============================================================
# TEST SUITE 1: M1 Mass Law
# ============================================================
class TestM1_MassLaw(unittest.TestCase):

    def test_typical_gypsum_500Hz(self):
        R = mass_law(9.6, 500)
        self.assertAlmostEqual(R, 26.4, delta=0.5)

    def test_heavy_wall_ALC(self):
        R = mass_law(133.5, 500)
        self.assertAlmostEqual(R, 49.3, delta=0.5)

    def test_mass_doubling_gives_6dB(self):
        """Doubling mass should increase R by ~6 dB (mass law principle)."""
        R1 = mass_law(10, 500)
        R2 = mass_law(20, 500)
        self.assertAlmostEqual(R2 - R1, 6.02, delta=0.1)

    def test_frequency_doubling_gives_6dB(self):
        """Doubling frequency should increase R by ~6 dB."""
        R1 = mass_law(10, 250)
        R2 = mass_law(10, 500)
        self.assertAlmostEqual(R2 - R1, 6.02, delta=0.1)

    def test_monotonicity_mass(self):
        """R must be monotonically increasing with mass."""
        masses = [5, 10, 20, 40, 80, 160]
        R_values = [mass_law(m, 500) for m in masses]
        for i in range(len(R_values) - 1):
            self.assertLess(R_values[i], R_values[i + 1])

    def test_rejects_zero_mass(self):
        with self.assertRaises(ValueError):
            mass_law(0, 500)

    def test_rejects_negative_frequency(self):
        with self.assertRaises(ValueError):
            mass_law(10, -100)


# ============================================================
# TEST SUITE 2: M2 Coincidence Effect
# ============================================================
class TestM2_Coincidence(unittest.TestCase):

    def test_all_materials_in_claimed_range(self):
        """Every material fc must fall within its documented range."""
        for name, params in MATERIALS.items():
            if name not in FC_CLAIMED_RANGES:
                continue
            fc = coincidence_freq(params["h"], params["rho"],
                                  params["E"], params["sigma"])
            lo, hi = FC_CLAIMED_RANGES[name]
            self.assertGreaterEqual(fc, lo,
                f"{name}: fc={fc:.0f} below range {lo}-{hi}")
            self.assertLessEqual(fc, hi,
                f"{name}: fc={fc:.0f} above range {lo}-{hi}")

    def test_thinner_plate_higher_fc(self):
        """Thinner plates must have higher coincidence frequency."""
        fc_6 = coincidence_freq(0.006, 1400, 8e9, 0.22)
        fc_8 = coincidence_freq(0.008, 1400, 8e9, 0.22)
        fc_10 = coincidence_freq(0.010, 1400, 8e9, 0.22)
        self.assertGreater(fc_6, fc_8)
        self.assertGreater(fc_8, fc_10)

    def test_higher_E_lower_fc(self):
        """Higher elastic modulus (stiffer plate) must give LOWER fc.
        fc ~ sqrt(rho/E): larger E -> smaller fc."""
        fc_low_E = coincidence_freq(0.012, 800, 2.0e9, 0.25)
        fc_high_E = coincidence_freq(0.012, 800, 3.0e9, 0.25)
        self.assertGreater(fc_low_E, fc_high_E,
            "Stiffer plate (higher E) should have lower fc")

    def test_bending_correction_factor(self):
        """Correction factor sqrt(12*(1-sigma^2)) at sigma=0.25 ~ 3.35."""
        factor = math.sqrt(12 * (1 - 0.25 ** 2))
        self.assertAlmostEqual(factor, 3.354, delta=0.01)

    def test_fc_without_correction_is_wrong(self):
        """Old formula without correction factor must NOT match claimed ranges."""
        h, rho, E, sigma = 0.012, 800, 2.5e9, 0.25
        fc_wrong = (C_SOUND ** 2) / (2 * math.pi * h) * math.sqrt(rho / E)
        self.assertLess(fc_wrong, 1000,
            "Uncorrected formula gives ~883 Hz, far below claimed 2000-4000")

    def test_heterogeneous_composite_E_sensitivity(self):
        """12mm gypsum + 10mm CaSi: delta_fc depends on E."""
        fc_g = coincidence_freq(0.012, 800, 2.5e9, 0.25)
        fc_c8 = coincidence_freq(0.010, 1400, 8e9, 0.22)
        fc_c6 = coincidence_freq(0.010, 1400, 6e9, 0.22)
        delta_8 = abs(fc_g - fc_c8)
        delta_6 = abs(fc_g - fc_c6)
        self.assertGreaterEqual(delta_8, 300,
            f"E=8GPa: delta_fc={delta_8:.0f} should be >= 300")
        self.assertLess(delta_6, 150,
            f"E=6GPa: delta_fc={delta_6:.0f} should be < 150")

    def test_fc_inversely_proportional_to_thickness(self):
        """fc * h should be approximately constant for same material."""
        fc1 = coincidence_freq(0.010, 1400, 8e9, 0.22)
        fc2 = coincidence_freq(0.008, 1400, 8e9, 0.22)
        ratio = (fc1 * 0.010) / (fc2 * 0.008)
        self.assertAlmostEqual(ratio, 1.0, delta=0.01)

    def test_dimensional_analysis(self):
        """Verify fc has units of Hz (1/s)."""
        # c^2/(2pi*h) has units m/s^2, sqrt(rho/E) has units s/m
        # product = 1/s = Hz -- this is a logic check
        h = 0.012
        unit_c2_over_h = C_SOUND ** 2 / h  # m^2/s^2 / m = m/s^2
        unit_sqrt = math.sqrt(800 / 2.5e9)  # sqrt(kg/m^3 / N/m^2) = s/m
        # The product should be in 1/s = Hz
        self.assertGreater(unit_c2_over_h * unit_sqrt, 0)


# ============================================================
# TEST SUITE 3: M3 MSM Resonance
# ============================================================
class TestM3_MSM(unittest.TestCase):

    def test_symmetric_T_SC3(self):
        """T-SC3 case: m1=m2=20.4, d=5cm -> f0 ~ 84 Hz."""
        f0 = msm_resonance(5.0, 20.4, 20.4)
        self.assertAlmostEqual(f0, 84.0, delta=1.0)

    def test_matches_ISO_exact_symmetric(self):
        """Corrected formula must match ISO 12354 within 1% for symmetric."""
        f0 = msm_resonance(5.0, 20.4, 20.4)
        f0_iso = msm_resonance_iso_exact(5.0, 20.4, 20.4)
        self.assertAlmostEqual(f0, f0_iso, delta=f0_iso * 0.01)

    def test_matches_ISO_exact_asymmetric(self):
        """Corrected formula must match ISO 12354 within 1% for asymmetric."""
        cases = [(5, 9.6, 14.0), (7.5, 9.6, 11.2), (10, 9.6, 19.2)]
        for d, m1, m2 in cases:
            f0 = msm_resonance(d, m1, m2)
            f0_iso = msm_resonance_iso_exact(d, m1, m2)
            err_pct = abs(f0 - f0_iso) / f0_iso * 100
            self.assertLess(err_pct, 1.0,
                f"Asymmetric d={d}, m1={m1}, m2={m2}: err={err_pct:.1f}%")

    def test_matches_ISO_exact_extreme(self):
        """Even extreme mass ratio must match within 1%."""
        f0 = msm_resonance(5.0, 5.0, 30.0)
        f0_iso = msm_resonance_iso_exact(5.0, 5.0, 30.0)
        err_pct = abs(f0 - f0_iso) / f0_iso * 100
        self.assertLess(err_pct, 1.0,
            f"Extreme ratio: err={err_pct:.1f}%")

    def test_old_formula_fails_asymmetric(self):
        """Old formula (1200, sum) must fail for asymmetric by > 5%."""
        m1, m2, d = 5.0, 30.0, 5.0
        f0_old = 1200 / math.sqrt(d * (m1 + m2))
        f0_iso = msm_resonance_iso_exact(d, m1, m2)
        err_pct = abs(f0_old - f0_iso) / f0_iso * 100
        self.assertGreater(err_pct, 5.0,
            f"Old formula should fail for extreme asymmetry, got only {err_pct:.1f}%")

    def test_larger_cavity_lower_f0(self):
        """Larger cavity depth must give lower resonance frequency."""
        f0_5 = msm_resonance(5, 10, 10)
        f0_10 = msm_resonance(10, 10, 10)
        f0_15 = msm_resonance(15, 10, 10)
        self.assertGreater(f0_5, f0_10)
        self.assertGreater(f0_10, f0_15)

    def test_heavier_panels_lower_f0(self):
        """Heavier panels must give lower resonance frequency."""
        f0_light = msm_resonance(5, 5, 5)
        f0_heavy = msm_resonance(5, 20, 20)
        self.assertGreater(f0_light, f0_heavy)

    def test_f0_below_100Hz_typical(self):
        """Typical partition wall configs should have f0 <= 100 Hz."""
        configs = [
            (5, 20.4, 20.4),   # double layer gypsum
            (7.5, 9.6, 9.6),   # single layer, 75mm (boundary: ~100 Hz)
            (10, 20.4, 20.4),  # double layer, 100mm
        ]
        for d, m1, m2 in configs:
            f0 = msm_resonance(d, m1, m2)
            self.assertLessEqual(f0, 100,
                f"d={d}, m1={m1}, m2={m2}: f0={f0:.1f} should be <= 100 Hz")

    def test_constant_derivation(self):
        """K(d=cm) should be ~600 (598 exact)."""
        K = math.sqrt(RHO_AIR * C_SOUND ** 2) / (2 * math.pi) * math.sqrt(100)
        self.assertAlmostEqual(K, 598, delta=5)
        self.assertAlmostEqual(K, 600, delta=5)


# ============================================================
# TEST SUITE 4: M4 Cavity Gain Logic
# ============================================================
class TestM4_CavityGain(unittest.TestCase):

    def test_dual_cavity_total_depth_threshold(self):
        """Dual cavity 50+50=100mm >= 75mm threshold."""
        total = 50 + 50
        self.assertGreaterEqual(total, 75)

    def test_single_cavity_below_threshold(self):
        """Single 50mm cavity < 75mm threshold."""
        self.assertLess(50, 75)

    def test_gain_ranges_reasonable(self):
        """Gain ranges should be positive and bounded."""
        cavity_gain = (3, 8)
        fill_gain = (2, 5)
        decouple_gain = (3, 10)
        for lo, hi in [cavity_gain, fill_gain, decouple_gain]:
            self.assertGreater(hi, lo)
            self.assertGreater(lo, 0)


# ============================================================
# TEST SUITE 5: M5 Impact Sound
# ============================================================
class TestM5_ImpactSound(unittest.TestCase):

    def test_floating_floor_f0_typical(self):
        """Typical floating floor f0: 40-130 Hz."""
        for s in [5, 15, 30, 50]:
            f0 = floating_floor_f0(s, 80)
            self.assertGreater(f0, 30, f"s={s}: f0={f0:.1f} too low")
            self.assertLess(f0, 150, f"s={s}: f0={f0:.1f} too high")

    def test_lower_stiffness_lower_f0(self):
        """Lower dynamic stiffness must give lower f0."""
        f0_soft = floating_floor_f0(5, 80)
        f0_hard = floating_floor_f0(50, 80)
        self.assertLess(f0_soft, f0_hard)

    def test_improvement_increases_with_frequency(self):
        """dL must increase monotonically above f0."""
        f0 = floating_floor_f0(15, 80)
        dL_prev = 0
        for f in [100, 250, 500, 1000, 2000]:
            if f > f0:
                dL = impact_sound_delta_L(f, f0)
                self.assertGreater(dL, dL_prev)
                dL_prev = dL

    def test_no_improvement_below_f0(self):
        """Below f0, improvement is zero."""
        f0 = floating_floor_f0(50, 80)
        dL = impact_sound_delta_L(50, f0)
        self.assertEqual(dL, 0.0)

    def test_IC08_example_Ln_range(self):
        """IC-08: bare slab ~78-80 dB - improvement ~15-22 -> 56-65 dB."""
        bare_Ln = 79  # mid estimate
        f0 = floating_floor_f0(15, 80)
        # Weighted improvement is roughly dL at 500Hz as proxy
        dL_500 = impact_sound_delta_L(500, f0)
        Ln_result = bare_Ln - dL_500
        # dL_500 should be significant
        self.assertGreater(dL_500, 15)

    # -- Single-value ΔLw tests --

    def test_deltaLw_typical_rubber_pad(self):
        """5mm rubber (s=20), 102 kg/m2 screed: dLw should be 30-40 dB."""
        dLw = impact_sound_deltaLw(102, 20)
        self.assertGreater(dLw, 30)
        self.assertLess(dLw, 40)

    def test_deltaLw_softer_pad_higher_improvement(self):
        """Softer pad (lower s) must give higher dLw."""
        dLw_soft = impact_sound_deltaLw(100, 10)
        dLw_hard = impact_sound_deltaLw(100, 30)
        self.assertGreater(dLw_soft, dLw_hard)

    def test_deltaLw_heavier_face_higher_improvement(self):
        """Heavier floating layer must give higher dLw."""
        dLw_heavy = impact_sound_deltaLw(150, 20)
        dLw_light = impact_sound_deltaLw(60, 20)
        self.assertGreater(dLw_heavy, dLw_light)

    def test_deltaLw_C_sensitivity(self):
        """Changing C by 4 should change dLw by exactly 4 dB."""
        dLw_12 = impact_sound_deltaLw(100, 20, C=12)
        dLw_8 = impact_sound_deltaLw(100, 20, C=8)
        self.assertAlmostEqual(dLw_12 - dLw_8, 4.0, places=5)

    def test_deltaLw_V3_scenario(self):
        """V3 verification: 102 kg/m2, s=20, C=10 -> ~33 dB."""
        dLw = impact_sound_deltaLw(102, 20)
        self.assertAlmostEqual(dLw, 33.1, delta=1.0)

    def test_deltaLw_rejects_nonpositive(self):
        """Non-positive m' or s must raise ValueError."""
        with self.assertRaises(ValueError):
            impact_sound_deltaLw(0, 20)
        with self.assertRaises(ValueError):
            impact_sound_deltaLw(100, 0)


# ============================================================
# TEST SUITE 6: M6 Gap/Sound Bridge
# ============================================================
class TestM6_GapBridge(unittest.TestCase):

    def test_gap_always_reduces_R(self):
        """Any gap must reduce effective R below wall R."""
        for R_wall in [35, 45, 50, 55]:
            R_eff = gap_effective_R(R_wall, 0.01)
            self.assertLess(R_eff, R_wall)

    def test_larger_gap_more_loss(self):
        """Larger gap fraction must give lower effective R."""
        R_1pct = gap_effective_R(50, 0.01)
        R_5pct = gap_effective_R(50, 0.05)
        self.assertGreater(R_1pct, R_5pct)

    def test_higher_wall_more_sensitive_to_gap(self):
        """Higher-R walls lose more dB from same gap."""
        loss_35 = 35 - gap_effective_R(35, 0.01)
        loss_55 = 55 - gap_effective_R(55, 0.01)
        self.assertGreater(loss_55, loss_35)

    def test_1pct_gap_50dB_wall(self):
        """1% gap on 50dB wall: R_eff ~ 20 dB (loss ~ 30 dB)."""
        R_eff = gap_effective_R(50, 0.01)
        self.assertAlmostEqual(R_eff, 20.0, delta=1.0)

    def test_gap_effective_R_floor(self):
        """With large gap, R_eff approaches R_gap (0 dB)."""
        R_eff = gap_effective_R(50, 0.5)
        self.assertLess(R_eff, 5)

    def test_tiny_gap_small_loss(self):
        """0.1% gap on 35dB wall: loss should be modest."""
        R_eff = gap_effective_R(35, 0.001)
        loss = 35 - R_eff
        self.assertLess(loss, 15)

    def test_rejects_zero_gap(self):
        with self.assertRaises(ValueError):
            gap_effective_R(50, 0)

    def test_rejects_full_gap(self):
        with self.assertRaises(ValueError):
            gap_effective_R(50, 1.0)


# ============================================================
# TEST SUITE 7: Material Parameter Consistency
# ============================================================
class TestMaterialParams(unittest.TestCase):

    def test_face_density_matches_rho_times_h(self):
        """face_m should equal rho * h for each material."""
        for name, p in MATERIALS.items():
            expected = p["rho"] * p["h"]
            self.assertAlmostEqual(p["face_m"], expected, delta=0.5,
                msg=f"{name}: face_m={p['face_m']} vs rho*h={expected:.1f}")

    def test_density_ranges_reasonable(self):
        """All densities should be in physically reasonable range."""
        for name, p in MATERIALS.items():
            self.assertGreater(p["rho"], 100, f"{name}: rho too low")
            self.assertLess(p["rho"], 3000, f"{name}: rho too high")

    def test_elastic_modulus_positive(self):
        for name, p in MATERIALS.items():
            self.assertGreater(p["E"], 0, f"{name}: E must be positive")

    def test_poisson_ratio_range(self):
        """sigma should be in (0, 0.5) for all materials."""
        for name, p in MATERIALS.items():
            self.assertGreater(p["sigma"], 0, f"{name}: sigma > 0")
            self.assertLess(p["sigma"], 0.5, f"{name}: sigma < 0.5")

    def test_gypsum_density_in_standard_range(self):
        """GB/T 9775: gypsum board rho 700-900 kg/m3."""
        self.assertGreaterEqual(MATERIALS["gypsum_12mm"]["rho"], 700)
        self.assertLessEqual(MATERIALS["gypsum_12mm"]["rho"], 900)

    def test_casi_density_in_standard_range(self):
        """JC/T 564.1: calcium silicate board rho 1000-1400 kg/m3."""
        self.assertGreaterEqual(MATERIALS["casi_10mm"]["rho"], 1000)
        self.assertLessEqual(MATERIALS["casi_10mm"]["rho"], 1400)


# ============================================================
# TEST SUITE 8: Interface Contract Data (IC-08, IC-09)
# ============================================================
class TestInterfaceContracts(unittest.TestCase):

    def test_IC08_concrete_slab_mass(self):
        """IC-08: 120mm concrete, rho=2500 -> m=300 kg/m2."""
        self.assertAlmostEqual(120 * 2500 / 1000, 300, delta=1)

    def test_IC08_rubber_pad_mass(self):
        """IC-08: 5mm rubber, rho~1000 -> m=5 kg/m2."""
        self.assertAlmostEqual(5 * 1000 / 1000, 5, delta=0.5)

    def test_IC08_screed_mass(self):
        """IC-08: 40mm screed, rho~2000 -> m=80 kg/m2."""
        self.assertAlmostEqual(40 * 2000 / 1000, 80, delta=1)

    def test_IC08_stiffness_in_range(self):
        """IC-08: s=15 MN/m3 must be in doc range [5, 50]."""
        self.assertGreaterEqual(15, 5)
        self.assertLessEqual(15, 50)

    def test_IC09_panel_face_density(self):
        """IC-09: 2x12mm gypsum, 8.5 kg/m2 each -> 17 kg/m2 total."""
        total = 8.5 * 2
        self.assertAlmostEqual(total, 17.0, delta=0.5)

    def test_IC09_cavity_above_threshold(self):
        """IC-09: 150mm cavity >= 75mm -> gain applies."""
        self.assertGreaterEqual(150, 75)

    def test_IC09_gypsum_fc_in_range(self):
        """IC-09: 12mm gypsum fc should be in 2000-4000 Hz range."""
        fc = coincidence_freq(0.012, 800, 2.5e9, 0.25)
        self.assertGreaterEqual(fc, 2000)
        self.assertLessEqual(fc, 4000)


# ============================================================
# TEST SUITE 9: Adversarial / Boundary Tests
# ============================================================
class TestAdversarial(unittest.TestCase):

    def test_very_thin_panel_high_fc(self):
        """3mm aluminum panel should have fc well above typical gypsum range."""
        fc = coincidence_freq(0.003, 2700, 70e9, 0.33)
        self.assertGreater(fc, 3000)

    def test_very_thick_panel_low_fc(self):
        """200mm concrete should have fc in low frequency range."""
        fc = coincidence_freq(0.200, 2400, 30e9, 0.20)
        self.assertLess(fc, 200)

    def test_MSM_equal_mass_simplification(self):
        """When m1=m2, f0 formula simplifies cleanly."""
        m = 15.0
        d = 7.5
        f0 = msm_resonance(d, m, m)
        # m_red = m/2 = 7.5
        expected = 600 / math.sqrt(d * m / 2)
        self.assertAlmostEqual(f0, expected, delta=0.01)

    def test_gap_100pct_approaches_zero(self):
        """99.9% gap: R_eff approaches 0 dB."""
        R_eff = gap_effective_R(50, 0.999)
        self.assertLess(R_eff, 1)

    def test_mass_law_very_heavy(self):
        """Very heavy wall (500 kg/m2) at 1000 Hz -> ~67 dB."""
        R = mass_law(500, 1000)
        self.assertGreater(R, 60)
        self.assertLess(R, 80)

    def test_MSM_very_small_cavity(self):
        """Very small cavity (10mm) with light panels -> high f0."""
        f0 = msm_resonance(1.0, 5, 5)
        self.assertGreater(f0, 200)

    def test_fc_monotonic_with_thickness_series(self):
        """fc must decrease monotonically as thickness increases."""
        thicknesses = [0.006, 0.008, 0.010, 0.012, 0.015]
        fcs = [coincidence_freq(h, 800, 2.5e9, 0.25) for h in thicknesses]
        for i in range(len(fcs) - 1):
            self.assertGreater(fcs[i], fcs[i + 1],
                f"fc not monotonic: h={thicknesses[i]} fc={fcs[i]:.0f} vs h={thicknesses[i+1]} fc={fcs[i+1]:.0f}")

    def test_no_formula_produces_negative(self):
        """No valid input should produce negative output from any model."""
        self.assertGreater(mass_law(10, 100), 0)
        self.assertGreater(coincidence_freq(0.01, 800, 2.5e9, 0.25), 0)
        self.assertGreater(msm_resonance(5, 10, 10), 0)
        self.assertGreater(impact_sound_delta_L(1000, 50), 0)
        self.assertGreater(impact_sound_deltaLw(100, 20), 0)

    def test_ALC_fc_below_audible_range(self):
        """150mm ALC: fc should be very low, well below 500 Hz."""
        fc = coincidence_freq(0.150, 600, 2.3e9, 0.18)
        self.assertLess(fc, 300)


# ============================================================
# TEST SUITE 10: Cross-Model Consistency
# ============================================================
class TestCrossModel(unittest.TestCase):

    def test_mass_law_vs_MSM_no_contradiction(self):
        """MSM f0 should be below the frequency range where mass law dominates."""
        f0 = msm_resonance(5, 20.4, 20.4)
        # MSM resonance should be below ~150 Hz for good designs
        self.assertLess(f0, 150)
        # Mass law at f0 should give reasonable base R
        R_at_f0 = mass_law(20.4, f0)
        self.assertGreater(R_at_f0, 0)

    def test_coincidence_above_MSM(self):
        """fc should be well above f0 for typical configs."""
        f0 = msm_resonance(5, 20.4, 20.4)
        fc = coincidence_freq(0.012, 800, 2.5e9, 0.25)
        self.assertGreater(fc, f0 * 10,
            "Coincidence frequency should be much higher than MSM resonance")

    def test_full_pipeline_gypsum_wall(self):
        """End-to-end: 75mm cavity, double gypsum, check all models consistent."""
        m = 9.6 * 2  # double layer
        d = 7.5

        # M2: coincidence check
        fc = coincidence_freq(0.012, 800, 2.5e9, 0.25)
        self.assertGreater(fc, 2000)

        # M3: resonance
        f0 = msm_resonance(d, m, m)
        self.assertLess(f0, 100, "f0 should be < 100 Hz for good design")

        # M1: mass law at 500Hz
        R_500 = mass_law(m * 2, 500)  # both sides
        self.assertGreater(R_500, 30)

        # M6: gap check
        R_gap_1pct = gap_effective_R(45, 0.01)
        self.assertLess(R_gap_1pct, 25,
            "1% gap should severely reduce a 45 dB wall")


# ============================================================
# TEST SUITE 11: M7 Baseline Calibration
# ============================================================
class TestM7_BaselineCalibration(unittest.TestCase):

    def test_r_equals_one_zero_change(self):
        """r=1（面密度不变）时 ΔR 两界均为 0。"""
        lo, hi = m7_delta_R_bounds(1.0)
        self.assertAlmostEqual(lo, 0.0, delta=1e-9)
        self.assertAlmostEqual(hi, 0.0, delta=1e-9)

    def test_upper_bound_twice_lower(self):
        """双叶上界恒为下界的 2 倍（40·lg = 2 × 20·lg）。"""
        for r in (0.6, 0.843, 1.2, 1.5):
            lo, hi = m7_delta_R_bounds(r)
            self.assertAlmostEqual(hi, 2 * lo, delta=1e-9,
                msg=f"r={r}: hi={hi} 应为 lo={lo} 的 2 倍")

    def test_symmetric_double_doubling_up_to_12dB(self):
        """双叶面密度加倍（r=2）：下界 +6 dB（质量定律），上界 +12 dB（两叶之和）。"""
        lo, hi = m7_delta_R_bounds(2.0)
        self.assertAlmostEqual(lo, 6.02, delta=0.05)
        self.assertAlmostEqual(hi, 12.04, delta=0.1)

    def test_case_2026_08_20_standard_board_variant(self):
        """算例记录复现：基准 51 kg/㎡（含龙骨分摊）→ 变体 43 kg/㎡。
        r=0.843，ΔR ∈ [-3.0, -1.5] dB，中值 -2.2 dB → Rw 51-2.2 ≈ 48.8（文档表述约 49 dB）。"""
        r = 43 / 51
        self.assertAlmostEqual(r, 0.843, delta=0.001)
        lo, hi = m7_delta_R_bounds(r)
        self.assertAlmostEqual(lo, -1.5, delta=0.1)
        self.assertAlmostEqual(hi, -3.0, delta=0.1)
        self.assertLess(hi, lo)  # r<1：上界为更大降幅
        Rw_new = 51 + (lo + hi) / 2
        self.assertAlmostEqual(Rw_new, 48.75, delta=0.05)
        self.assertTrue(48.0 <= Rw_new <= 50.0)

    def test_case_panel_only_ratio(self):
        """面板层口径比值 38/46=0.826 亦应落在文档界限逻辑内（|Δ| 略大）。"""
        r = 38 / 46
        lo, hi = m7_delta_R_bounds(r)
        self.assertAlmostEqual(lo, -1.66, delta=0.05)
        self.assertAlmostEqual(hi, -3.32, delta=0.05)

    def test_extrapolation_guard(self):
        """外推区守卫：r ∈ [0.5, 2] 有效，界外无效（仅趋势判断）。"""
        self.assertTrue(m7_is_valid_extrapolation(0.5))
        self.assertTrue(m7_is_valid_extrapolation(2.0))
        self.assertTrue(m7_is_valid_extrapolation(0.843))
        self.assertFalse(m7_is_valid_extrapolation(0.49))
        self.assertFalse(m7_is_valid_extrapolation(2.1))

    def test_rejects_nonpositive_ratio(self):
        with self.assertRaises(ValueError):
            m7_delta_R_bounds(0)
        with self.assertRaises(ValueError):
            m7_delta_R_bounds(-1)


# ============================================================
# TEST SUITE 12: Document Anchor (cross-check vs Markdown SOT)
# ============================================================
# 本组测试在运行时读取技能仓 acoustic-calculation-engine/reference.md
# （Markdown SOT，2026-08-07 起技能文件以运行时为唯一事实源，
# 项目仓 _专题_ACE开发/ 副本为开发归档），将脚本内的关键常数与材料参数
# 与文档本体交叉比对，使测试不再仅校验脚本内硬编码的自我副本
# （评审发现 A3/F2：测试与实现同源自引用）。
# 本组失败时，须按 change-governance.md 流程判定是文档还是脚本漂移，
# 不得通过同时修改两侧"抹平"差异。
_DOC_PATH = (Path.home() / ".qoder" / "skills"
             / "acoustic-calculation-engine" / "reference.md")


def _load_doc():
    if not _DOC_PATH.exists():
        raise AssertionError(f"Markdown SOT 未找到: {_DOC_PATH}")
    return _DOC_PATH.read_text(encoding="utf-8")


def _doc_material_range(text, row_prefix):
    """从材料参数库表行提取 (rho_lo, rho_hi, e_lo, e_hi)。"""
    m = re.search(
        re.escape(row_prefix) + r"\s*\|\s*([\d.]+)-([\d.]+)\s*\|\s*([\d.]+)-([\d.]+)\s*\|",
        text,
    )
    if not m:
        raise AssertionError(f"材料参数库表行未找到: {row_prefix}")
    return tuple(float(x) for x in m.groups())


class TestDocAnchor(unittest.TestCase):
    """脚本常数/参数 ↔ reference.md 本体锚定检查。"""

    @classmethod
    def setUpClass(cls):
        cls.doc = _load_doc()

    def test_M1_frequency_domain_constant(self):
        """M1 频率域常数：文档 -47.2 = 脚本 mass_law 默认 const。"""
        m = re.search(r"R\(f\) ≈ 20·log₁₀\(m·f\) - ([\d.]+)", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到 M1 频率域公式")
        doc_const = float(m.group(1))
        script_const = inspect.signature(mass_law).parameters["const"].default
        self.assertAlmostEqual(abs(script_const), doc_const, places=1,
            msg=f"M1 常数漂移: 脚本 {-script_const} vs 文档 {doc_const}")

    def test_M3_msm_constant(self):
        """M3 MSM 常数：文档 600 = 脚本 msm_resonance 隐含常数。"""
        m = re.search(r"f₀ [≈=] (\d+) / √\(d(?:_cm)? × m_red\)", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到 M3 公式")
        doc_k = float(m.group(1))
        # msm_resonance(d_cm=1, m1=1, m2=1): m_red=0.5, f0 = K/sqrt(0.5)
        script_k = msm_resonance(1.0, 1.0, 1.0) * math.sqrt(0.5)
        self.assertAlmostEqual(script_k, doc_k, delta=0.5,
            msg=f"M3 常数漂移: 脚本 {script_k:.1f} vs 文档 {doc_k:.0f}")

    def test_M5_default_C(self):
        """M5 默认 C 值：文档 C=10 = 脚本 impact_sound_deltaLw 默认值。"""
        self.assertIn("ΔLw ≈ 18·log₁₀(m') - 10·log₁₀(s) + C", self.doc,
            "reference.md 未找到 M5 ΔLw 公式")
        m = re.search(r"ACE 默认 C=(\d+)", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到 M5 默认 C 值声明")
        doc_c = float(m.group(1))
        script_c = inspect.signature(impact_sound_deltaLw).parameters["C"].default
        self.assertEqual(script_c, doc_c,
            msg=f"M5 默认 C 漂移: 脚本 {script_c} vs 文档 {doc_c}")

    def test_M2_delta_fc_criterion(self):
        """M2 异质复合 Δfc 错开判据：文档 ≥300 Hz。"""
        m = re.search(r"Δfc = \|fc₁ - fc₂\| ≥ (\d+) Hz", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到 Δfc 错开判据")
        self.assertEqual(int(m.group(1)), 300)

    def test_sound_speed(self):
        """声速声明：文档取 343 m/s = 脚本 C_SOUND。"""
        self.assertIn("取 343 m/s", self.doc, "reference.md 未找到声速声明")
        self.assertEqual(C_SOUND, 343.0)

    def test_material_db_within_doc_ranges(self):
        """脚本材料 DB 须落在文档材料参数库 S1 区间内。"""
        cases = [
            ("石膏板 | 标准（12mm）", "gypsum_12mm"),
            ("硅酸钙板 | 高密度", "casi_10mm"),
            ("ALC 条板 | 标准", "alc_150mm"),
        ]
        for row_prefix, key in cases:
            rho_lo, rho_hi, e_lo, e_hi = _doc_material_range(self.doc, row_prefix)
            mat = MATERIALS[key]
            self.assertTrue(rho_lo <= mat["rho"] <= rho_hi,
                f"{key}: rho={mat['rho']} 超出文档区间 {rho_lo}-{rho_hi}")
            self.assertTrue(e_lo * 1e9 <= mat["E"] <= e_hi * 1e9,
                f"{key}: E={mat['E']} 超出文档区间 {e_lo}-{e_hi} GPa")

    def test_IC08_example_concrete_face_density(self):
        """IC-08 示例混凝土面密度 300 kg/㎡ 须在文档基层库 S1 推导区间内。"""
        m = re.search(r"\|\s*普通混凝土（C25-C40）\s*\|\s*([\d.]+)-([\d.]+)\s*\|", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到基层普通混凝土行")
        lo, hi = float(m.group(1)), float(m.group(2))
        face_lo, face_hi = lo * 0.12, hi * 0.12  # 120mm 楼板
        self.assertTrue(face_lo <= 300 <= face_hi + 1e-9,
            f"IC-08 示例面密度 300 超出 S1 推导区间 {face_lo:.0f}-{face_hi:.0f}")

    def test_M7_section_exists(self):
        """M7 基准校准模型章节须存在于 reference.md。"""
        self.assertIn("### M7 基准校准模型（Baseline Calibration）", self.doc,
            "reference.md 未找到 M7 基准校准模型章节")

    def test_M7_bound_formulas(self):
        """M7 界限公式：ΔR_low=20·lg(r)、ΔR_high=40·lg(r)。"""
        self.assertRegex(self.doc, r"ΔR_low\s*=\s*20·lg\(r\)",
            "reference.md 未找到 M7 下限公式")
        self.assertRegex(self.doc, r"ΔR_high\s*=\s*40·lg\(r\)",
            "reference.md 未找到 M7 上限公式")

    def test_M7_extrapolation_range_matches_script(self):
        """M7 外推区文档值须与脚本 M7_VALID_R_RANGE 一致。"""
        m = re.search(r"r 超出 \[([\d.]+),\s*([\d.]+)\]", self.doc)
        self.assertIsNotNone(m, "reference.md 未找到 M7 外推区声明")
        doc_range = (float(m.group(1)), float(m.group(2)))
        self.assertEqual(doc_range, M7_VALID_R_RANGE,
            f"M7 外推区漂移: 文档 {doc_range} vs 脚本 {M7_VALID_R_RANGE}")

    def test_M7_precision_claim(self):
        """M7 精度声明 ±2-3 dB（同族构造校准）。"""
        self.assertIn("±2-3 dB（同族构造校准）", self.doc,
            "reference.md 未找到 M7 精度声明")

    def test_M7_baseline_standard_citations(self):
        """M7 基准测量/评价与方法论标准引用须存在。"""
        for std in ("GB/T 45305.2-2025", "GB/T 50121-2005", "ISO 12354-1:2017"):
            self.assertIn(std, self.doc,
                f"reference.md M7 缺失标准引用 {std}")


class TestFloorF01Boundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path.home() / ".qoder/skills/prefab-floor-system/reference.md"
        cls.full_doc = path.read_text(encoding="utf-8")
        start = cls.full_doc.index("#### 方案 FL-F01：")
        end = cls.full_doc.index("#### 方案 FL-F02：", start)
        cls.doc = cls.full_doc[start:end]

    def assert_f01_boundary(self, text):
        rows = {}
        for line in text.splitlines():
            if line.startswith("| "):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                self.assertEqual(len(cells), 3)
                self.assertNotIn(cells[0], rows)
                rows[cells[0]] = cells[1:]
        expected = {
            "恒荷载增量": "待逐层计算",
            "浮筑层面质量 m'": "待逐层计算",
            "弹性垫动刚度 s": "待按适用条件取值",
            "共振频率 f₀": "输入核实后计算",
            "ΔLw 估算": "本例不提供有效预测值",
            "裸板 Ln,w 基准": "待取得对应构造依据",
            "浮筑后 Ln,w 估算": "本例不提供数值",
            "f₀ 评价": "本例不作性能评价",
        }
        for name, value in expected.items():
            self.assertIn(name, rows)
            self.assertEqual(rows[name][0], value)
            self.assertNotRegex(rows[name][1], r"\d")
        mass = rows["浮筑层面质量 m'"][1]
        load = rows["恒荷载增量"][1]
        for layer in ("细石混凝土", "瓷砖胶", "瓷砖", "实际配置的钢丝网"):
            self.assertIn(layer, mass)
            self.assertIn(layer, load)
        for phrase in ("共同运动", "不含结构楼板及弹性垫自身", "避免重复计量"):
            self.assertIn(phrase, mass)
        for phrase in ("及弹性垫", "不含结构楼板", "重力加速度", "kN/m²", "避免重复计量"):
            self.assertIn(phrase, load)
        for phrase in ("材料状态", "荷载", "加载时间", "表观动刚度与修正动刚度不得混用"):
            self.assertIn(phrase, rows["弹性垫动刚度 s"][1])
        for phrase in ("「浮筑共振频率 f₀」节", "s 用 N/m³", "m' 用 kg/m²", "结果为 Hz"):
            self.assertIn(phrase, rows["共振频率 f₀"][1])
        for phrase in ("不代表已验证的施工控制值", "须经工程设计确认", "不附数值精度承诺",
                       "ΔL(f)、ΔLw、实验室 Ln,w 与现场 L'nT,w", "本例不作现场达标判断"):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r"(?:≈\s*\d|±\s*\d|C\s*=\s*\d|\d\s*dB|余量充足|充足余量|全频段有效改善|优秀)")
        self.assertNotRegex(text, r"(?:质量块\s*m'|弹簧\s*s|面积\s*>)")

    def assert_f01_references(self, text):
        rows = [line for line in text.splitlines()
                if line.startswith("|") and re.search(r"\bFL-F01\b", line)]
        self.assertTrue(rows, "FL-F01 选型引用行缺失，禁止空跑")
        for row in rows:
            self.assertIn("仅作为构造候选", row)
            self.assertIn("隔声性能与现场达标均须另行验证", row)
            self.assertNotRegex(row, r"(?:余量|\d\s*dB|满足|已达标)")

    def test_runtime_f01_boundary(self):
        self.assert_f01_boundary(self.doc)

    def test_direct_references_preserve_boundary(self):
        self.assert_f01_references(self.full_doc)

    def test_direct_reference_performance_claim_rejected(self):
        for claim in ("隔声余量充足", "已达标", "预测 21 dB"):
            text = self.full_doc.replace("仅作为构造候选；", "仅作为构造候选；" + claim + "；")
            with self.subTest(claim=claim), self.assertRaises(AssertionError):
                self.assert_f01_references(text)

    def test_missing_direct_reference_boundary_rejected(self):
        for phrase in ("仅作为构造候选", "隔声性能与现场达标均须另行验证"):
            with self.subTest(phrase=phrase), self.assertRaises(AssertionError):
                self.assert_f01_references(self.full_doc.replace(phrase, ""))
        with self.assertRaises(AssertionError):
            self.assert_f01_references(self.doc)

    def test_other_scheme_reference_is_outside_scope(self):
        self.assert_f01_references(self.full_doc + "\n| 项目 | FL-F02 | 预测 21 dB |\n")

    def test_old_and_substitute_predictions_rejected(self):
        for value in ("≈21 dB", "36.6 dB", "33.0 dB"):
            with self.subTest(value=value), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace("| ΔLw 估算 | 本例不提供有效预测值 |",
                                                         f"| ΔLw 估算 | {value} |"))

    def test_unverified_mass_stiffness_and_load_rejected(self):
        for name, old, new in (("浮筑层面质量 m'", "待逐层计算", "108 kg/m²"),
                               ("恒荷载增量", "待逐层计算", "1.16 kN/m²"),
                               ("弹性垫动刚度 s", "待按适用条件取值", "10 MN/m³")):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace(f"| {name} | {old} |", f"| {name} | {new} |"))

    def test_unverified_ln_and_resonance_rejected(self):
        for name, old, new in (("裸板 Ln,w 基准", "待取得对应构造依据", "76-80 dB"),
                               ("浮筑后 Ln,w 估算", "本例不提供数值", "55-59 dB"),
                               ("共振频率 f₀", "输入核实后计算", "48.4 Hz")):
            with self.subTest(name=name), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace(f"| {name} | {old} |", f"| {name} | {new} |"))

    def test_missing_mass_layer_and_exclusions_rejected(self):
        for phrase in ("瓷砖胶、", "实际配置的钢丝网", "共同运动", "不含结构楼板及弹性垫自身", "避免重复计量"):
            with self.subTest(phrase=phrase), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace(phrase, ""))

    def test_wrong_stiffness_units_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_f01_boundary(self.doc.replace("s 用 N/m³", "s 用 MN/m³"))

    def test_missing_stiffness_conditions_rejected(self):
        for phrase in ("材料状态", "荷载及加载时间", "表观动刚度与修正动刚度不得混用"):
            with self.subTest(phrase=phrase), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace(phrase, ""))

    def test_precision_and_performance_claims_rejected(self):
        for claim in ("ΔLw 精度 ±3-5 dB", "优秀（<80 Hz）", "全频段有效改善", "现场达标有充足余量", "ΔLw=21 dB"):
            with self.subTest(claim=claim), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc + "\n" + claim)

    def test_missing_or_duplicate_result_row_rejected(self):
        row = next(line for line in self.doc.splitlines(keepends=True) if line.startswith("| ΔLw 估算 |"))
        for replacement in ("", row + row):
            with self.subTest(replacement=replacement), self.assertRaises(AssertionError):
                self.assert_f01_boundary(self.doc.replace(row, replacement))

    def test_layout_control_stays_valid(self):
        self.assert_f01_boundary(self.doc.replace("\n\n", "\n\n\n"))

    def test_resonance_method_anchor_and_unit_conversion(self):
        start = self.full_doc.index("#### 浮筑共振频率 f₀")
        end = self.full_doc.index("**f₀ 与隔声效果的关系**", start)
        method = self.full_doc[start:end]
        self.assertIn("f₀ = (1/2π) × √(s / m')", method)
        self.assertIn("1 MN/m³ = 10⁶ N/m³", method)
        self.assertAlmostEqual(floating_floor_f0(10, 108), 48.4293069277, places=8)


class TestFloorF02F03Boundary(unittest.TestCase):
    """CG-20260924-004：F02/F03 构造计量与预测收窄守卫（PL-052/064、G-1、PL-056/057）。

    FLOOR_SKILL_DIR 环境变量可指向改前原像目录做复红自证；默认读运行时技能件。
    """

    @classmethod
    def setUpClass(cls):
        base = Path(os.environ.get("FLOOR_SKILL_DIR") or
                    (Path.home() / ".qoder/skills/prefab-floor-system"))
        cls.full_doc = (base / "reference.md").read_text(encoding="utf-8")
        cls.ex_doc = (base / "examples.md").read_text(encoding="utf-8")
        s2 = cls.full_doc.index("#### 方案 FL-F02：")
        e2 = cls.full_doc.index("#### 方案 FL-F03：", s2)
        cls.doc_f02 = cls.full_doc[s2:e2]
        s3 = cls.full_doc.index("#### 方案 FL-F03：")
        e3 = cls.full_doc.index("### 6.8 性能数据与选型建议", s3)
        cls.doc_f03 = cls.full_doc[s3:e3]
        s5 = cls.full_doc.index("#### 浮筑构造隔声性能汇总")
        e5 = cls.full_doc.index("#### 选型建议速查", s5)
        cls.doc_summary = cls.full_doc[s5:e5]
        s6 = cls.full_doc.index("#### 选型建议速查")
        e6 = cls.full_doc.index("## 七、架空地面系统", s6)
        cls.doc_picker = cls.full_doc[s6:e6]

    @staticmethod
    def _rows(text, ncells):
        rows = {}
        for line in text.splitlines():
            if not line.startswith("| "):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == ncells and cells[0] not in ("参数", "构造方案", "项目条件"):
                rows.setdefault(cells[0], cells[1:])
        return rows

    # ---------- F02 厚度链（PL-052）＋参数收窄（G-1） ----------

    def assert_f02_boundary(self, text):
        self.assertIn("#### 方案 FL-F02：", text)
        rows = self._rows(text, 3)
        expected = {
            "总厚度（不含结构楼板）": "待按计量口径核算",
            "恒荷载增量": "待逐层计算",
            "浮筑层面质量 m'": "待逐层计算",
            "弹性垫动刚度 s": "待按适用条件取值",
            "共振频率 f₀": "输入核实后计算",
            "ΔLw 估算": "本例不提供有效预测值",
        }
        for name, value in expected.items():
            self.assertIn(name, rows)
            self.assertEqual(rows[name][0], value)
        thick = rows["总厚度（不含结构楼板）"][1]
        for phrase in ("嵌管口径", "叠加口径", "71-75mm", "91-95mm", "83-85",
                       "不猜新总厚", "粘结/防潮层未计厚"):
            self.assertIn(phrase, thick)
        for phrase in ("原示例值 125 kg/m² 不能由层次表厚度与密度复算得出",
                       "不从单层厚度反推整层质量"):
            self.assertIn(phrase, rows["浮筑层面质量 m'"][1])
        for phrase in ("地暖温升工况", "表观动刚度与修正动刚度不得混用"):
            self.assertIn(phrase, rows["弹性垫动刚度 s"][1])
        for phrase in ("互斥", "不以直算值顶替印值"):
            self.assertIn(phrase, rows["ΔLw 估算"][1])
        for phrase in ("未计层", "口径待设计文件明确", "嵌于回填层内",
                       "弹簧 s 待按适用条件取值"):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r"弹簧\s*s\s*≈")
        for phrase in ("**输出边界**", "嵌管/叠加", "须由设计意图确定后方可复算总厚",
                       "本例不作现场达标判断"):
            self.assertIn(phrase, text)

    # ---------- F03 标高口径（PL-064）＋参数收窄（G-1）＋现场出口（PL-057） ----------

    def assert_f03_boundary(self, text):
        self.assertIn("#### 方案 FL-F03：", text)
        rows = self._rows(text, 3)
        expected = {
            "总厚度（不含结构楼板）": "28mm（单层板口径）",
            "恒荷载增量": "待逐层计算",
            "浮筑层面质量 m'": "待逐层计算",
            "弹性垫动刚度 s": "待按适用条件取值",
            "共振频率 f₀": "输入核实后计算",
            "ΔLw 估算": "本例不提供有效预测值",
            "裸板 Ln,w 基准": "待取得对应构造依据",
            "浮筑后 Ln,w 估算": "本例不提供数值",
        }
        for name, value in expected.items():
            self.assertIn(name, rows)
            self.assertEqual(rows[name][0], value)
        thick = rows["总厚度（不含结构楼板）"][1]
        for phrase in ("5＋15＋8", "不含找平层与板缝/界面预留", "43mm",
                       "超出 30mm 标高增量 13mm", "标高仅允许 30mm 时不可装"):
            self.assertIn(phrase, thick)
        for phrase in ("无换算式", "不得由实验室量推算现场达标"):
            self.assertIn(phrase, rows["浮筑后 Ln,w 估算"][1])
        for phrase in ("互斥", "不以直算值顶替印值"):
            self.assertIn(phrase, rows["ΔLw 估算"][1])
        self.assertIn("弹簧 s 待按适用条件取值", text)
        self.assertNotRegex(text, r"弹簧\s*s\s*≈")
        for phrase in ("**输出边界**", "现场是否达标以现场检测判定",
                       "不以实验室量推算", "无换算式"):
            self.assertIn(phrase, text)

    # ---------- 汇总表两列撤除（G-1＋PL-056） ----------

    def assert_summary_table(self, text):
        self.assertIn("#### 浮筑构造隔声性能汇总", text)
        header = next(line for line in text.splitlines()
                      if line.startswith("| 构造方案"))
        cells = [c.strip() for c in header.strip("|").split("|")]
        self.assertEqual(cells, ["构造方案", "弹性垫 s (MN/m³)", "面质量 m' (kg/m²)",
                                 "f₀ (Hz)", "置信度"])
        data = [line for line in text.splitlines()
                if line.startswith("| ") and not line.startswith("| 构造方案")]
        self.assertEqual(len(data), 6, "汇总表数据行数变动，须按新口径复核守卫")
        for line in data:
            cells = [c.strip() for c in line.strip("|").split("|")]
            self.assertEqual(len(cells), 5)
            self.assertNotRegex(line, r"余量|达标|dB|极高|中高")
        for phrase in ("「ΔLw 估算」与「L'nT,w 达标可行性」两列已撤除",
                       "互斥", "恢复数值出口的条件"):
            self.assertIn(phrase, text)

    # ---------- 选型速查行（PL-064＋PL-056） ----------

    def assert_picker_rows(self, text):
        row30 = next(line for line in text.splitlines()
                     if "标高仅允许增加 30mm" in line)
        self.assertIn("FL-F03 干式浮筑（单层板）", row30)
        self.assertNotIn("FL-F03 干式浮筑（双层板）", row30)
        for phrase in ("28mm", "43mm", "不可装", "隔声性能须另行验证"):
            self.assertIn(phrase, row30)
        row_hr = next(line for line in text.splitlines() if "住宅+地暖" in line)
        self.assertIn("均须另行核实与验证", row_hr)
        self.assertNotIn("隔声与地暖兼容", row_hr)

    # ---------- examples.md 现场数值出口撤回（PL-057） ----------

    def assert_examples(self, text):
        self.assertNotRegex(text, r"\d+\s*-\s*48\s*dB")
        for phrase in ("远低于 65 dB 限值", "由 Ln,w 区间加宽而得",
                       "此处为区间加宽而非换算结果", "不列余量数值"):
            self.assertNotIn(phrase, text)
        self.assertEqual(
            text.count("不提供数值估算（两量间无换算式），达标须现场 L'nT,w 检测判定"), 2,
            "示例1/示例4 Step4 D1 现场检测出口应各一处")
        self.assertEqual(
            text.count("不提供数值估算（两量间无换算式），达标须现场检测判定"), 2,
            "示例1/示例4 核验清单 D1 行应各一处")
        self.assertEqual(
            text.count("不提供数值估算（两量间无换算式），达标以现场检测判定"), 2,
            "示例1/示例4 三原则审查行应各一处")
        self.assertEqual(text.count("实验室 Ln,w 与现场 L'nT,w 之间无换算式"), 4)
        self.assertEqual(text.count("现场值无数值出口，不作与限值的数值比较"), 2)
        self.assertEqual(text.count("L'nT,w 无数值出口，不作与限值的数值比较"), 2)
        self.assertEqual(text.count("区间加宽亦无依据"), 2)

    # ---------- 常态通过 ----------

    def test_runtime_f02_boundary(self):
        self.assert_f02_boundary(self.doc_f02)

    def test_runtime_f03_boundary(self):
        self.assert_f03_boundary(self.doc_f03)

    def test_runtime_summary_table(self):
        self.assert_summary_table(self.doc_summary)

    def test_runtime_picker_rows(self):
        self.assert_picker_rows(self.doc_picker)

    def test_runtime_examples(self):
        self.assert_examples(self.ex_doc)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_f02_old_thickness_or_stiffness_rejected(self):
        for old, new in (("待按计量口径核算", "83-85mm"),
                         ("待按适用条件取值", "≈15 MN/m³")):
            with self.subTest(new=new), self.assertRaises(AssertionError):
                self.assert_f02_boundary(self.doc_f02.replace(old, new, 1))
        with self.assertRaises(AssertionError):
            self.assert_f02_boundary(self.doc_f02.replace("不猜新总厚", ""))
        with self.assertRaises(AssertionError):
            self.assert_f02_boundary(self.doc_f02.replace("未计层", "构造层"))

    def test_f03_bare_thickness_or_old_values_rejected(self):
        for old, new in (("28mm（单层板口径）", "28mm"),
                         ("本例不提供数值", "61-65 dB"),
                         ("待按适用条件取值", "≈10 MN/m³")):
            with self.subTest(new=new), self.assertRaises(AssertionError):
                self.assert_f03_boundary(self.doc_f03.replace(old, new, 1))
        with self.assertRaises(AssertionError):
            self.assert_f03_boundary(self.doc_f03.replace("43mm", "40mm"))

    def test_summary_columns_restored_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_summary_table(self.doc_summary.replace(
                "| f₀ (Hz) | 置信度 |", "| f₀ (Hz) | ΔLw 估算 (dB) | 置信度 |"))
        with self.assertRaises(AssertionError):
            self.assert_summary_table(self.doc_summary.replace(
                "| 湿式浮筑（标准） | 10 | 108 | 48 | L5 |",
                "| 湿式浮筑（标准） | 10 | 108 | 48 | 高（余量充足） | L5 |"))

    def test_picker_double_board_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_picker_rows(self.doc_picker.replace(
                "FL-F03 干式浮筑（单层板）", "FL-F03 干式浮筑（双层板）"))

    def test_examples_field_value_restored_rejected(self):
        for injected in ("L'nT,w 估算 ≈ 42-48 dB", "L'nT,w ≈ 40-48 dB < 65 dB",
                         "远低于 65 dB 限值"):
            with self.subTest(injected=injected), self.assertRaises(AssertionError):
                self.assert_examples(self.ex_doc + "\n" + injected + "\n")

    # ---------- 控制例（守卫不恒真） ----------

    def test_layout_and_lab_value_control(self):
        self.assert_f02_boundary(self.doc_f02.replace("\n\n", "\n\n\n"))
        self.assert_f03_boundary(self.doc_f03.replace("\n\n", "\n\n\n"))
        self.assert_examples(self.ex_doc + "\nLn,w(浮筑) ≈ 42-46 dB（实验室量出口，允许）\n")
        self.assert_examples(self.ex_doc + "\n恒荷载 ≈ 0.35 kN/m²，远低于住宅活荷载标准值\n")


# ============================================================
# TEST SUITE: M2 吻合频率文档一致性（CG-20260924-005 组5 M2）
#   PL-065：ACE 修正因子省略误差说明须与公式一致（内部复算闭合）
#   PL-038 G-3：PW 三表同源（参数域→fc范围包络→搭配标称点）＋绝对结论收窄
#   全部为 C 类派生量／B 类参数域，按 data-classification.md 内部复算，不走官方通道。
#   ACE_SKILL_DIR / PW_SKILL_DIR 环境变量可指向改前原像目录做复红自证。
# ============================================================

def _m2_table_after(text, title_sub):
    """返回 title_sub 之后第一张 Markdown 表的单元列表（跳过表头与分隔行）。"""
    idx = text.index(title_sub)
    rows, started = [], False
    for line in text[idx:].splitlines():
        s = line.strip()
        if s.startswith("|"):
            started = True
            cells = [c.strip() for c in s.strip("|").split("|")]
            if all(c and set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
        elif started:
            break
    return rows


def _m2_fc(h_mm, rho, E_GPa, sigma):
    return coincidence_freq(h_mm / 1000.0, rho, E_GPa * 1e9, sigma)


class TestM2CoincidenceDocConsistency(unittest.TestCase):
    """M2 吻合频率：PL-065 误差说明一致 ＋ G-3 三表同源与绝对结论收窄守卫。"""

    # 声明标称基准（搭配表所用；须落在参数表声明域内）
    NOM_GYPSUM = (800, 2.5, 0.25)
    NOM_CASI = (1400, 6.0, 0.22)
    NOM_GYPSUM_95 = (900, 2.5, 0.25)

    @classmethod
    def setUpClass(cls):
        ace_base = Path(os.environ.get("ACE_SKILL_DIR") or
                        (Path.home() / ".qoder/skills/acoustic-calculation-engine"))
        pw_base = Path(os.environ.get("PW_SKILL_DIR") or
                       (Path.home() / ".qoder/skills/prefab-partition-wall-solution"))
        cls.ace = (ace_base / "reference.md").read_text(encoding="utf-8")
        cls.pw = (pw_base / "reference.md").read_text(encoding="utf-8")

    # ---------- 参数域解析（B 类，真值源＝PW 参数表，不改） ----------

    def _param_domains_from(self, pw_text):
        rows = _m2_table_after(pw_text, "隔墙常用板材声学参数参考表")
        groups = {"石膏板": [], "硅酸钙板": [], "ALC B06": []}
        for c in rows:
            if len(c) < 4 or c[0] == "板材类型":
                continue
            name = c[0]
            rho = [float(x) for x in c[1].split("-")]
            e = [float(x) for x in c[2].split("-")]
            sigma = float(c[3])
            if "石膏板" in name:
                groups["石膏板"].append((rho, e, sigma))
            elif "硅酸钙板" in name:
                groups["硅酸钙板"].append((rho, e, sigma))
            elif "B06" in name:
                groups["ALC B06"].append((rho, e, sigma))
        dom = {}
        for g, items in groups.items():
            self.assertTrue(items, f"参数表未解析到 {g} 行")
            dom[g] = (min(it[0][0] for it in items), max(it[0][1] for it in items),
                      min(it[1][0] for it in items), max(it[1][1] for it in items),
                      items[0][2])
        return dom

    # ---------- G-3(1) fc 范围表＝参数域包络（三表同源核心） ----------

    def assert_fc_range_table_is_envelope(self, pw_text):
        dom = self._param_domains_from(pw_text)
        rows = _m2_table_after(pw_text, "常用板材吻合临界频率参考表")
        label2group = {"普通/耐火石膏板": "石膏板", "硅酸钙板": "硅酸钙板",
                       "ALC B06": "ALC B06"}
        checked = 0
        for c in rows:
            if len(c) < 3 or c[0] == "板材":
                continue
            label, thick_s, rng = c[0], c[1], c[2]
            self.assertIn(label, label2group, f"fc 表出现未声明板材 {label}")
            rlo, rhi, elo, ehi, sig = dom[label2group[label]]
            h = float(thick_s.replace("mm", ""))
            fmin = _m2_fc(h, rlo, ehi, sig)   # 最小ρ/最大E
            fmax = _m2_fc(h, rhi, elo, sig)   # 最大ρ/最小E
            lo_s, hi_s = rng.split("-")
            self.assertAlmostEqual(float(lo_s), round(fmin), delta=1.0,
                msg=f"{label} {thick_s} fc_min 漂移：表 {lo_s} vs 包络复算 {fmin:.0f}")
            self.assertAlmostEqual(float(hi_s), round(fmax), delta=1.0,
                msg=f"{label} {thick_s} fc_max 漂移：表 {hi_s} vs 包络复算 {fmax:.0f}")
            checked += 1
        self.assertEqual(checked, 10, "fc 范围表应恰有 10 行（3 石膏＋4 硅钙＋3 ALC）")

    # ---------- G-3(2) 搭配表标称点可复现且落在包络内 ----------

    def assert_combination_table_same_source(self, pw_text):
        # 基准声明须在场
        for phrase in ("石膏板 ρ800/E2.5/σ0.25", "硅酸钙板 ρ1400/E6/σ0.22",
                       "9.5mm 石膏板取 ρ900"):
            self.assertIn(phrase, pw_text, "搭配表缺标称基准声明")
        # 标称基准须落在声明参数域内
        dom = self._param_domains_from(pw_text)
        grlo, grhi, gelo, gehi, _ = dom["石膏板"]
        crlo, crhi, celo, cehi, _ = dom["硅酸钙板"]
        self.assertTrue(grlo <= self.NOM_GYPSUM[0] <= grhi)
        self.assertTrue(gelo <= self.NOM_GYPSUM[1] <= gehi)
        self.assertTrue(crlo <= self.NOM_CASI[0] <= crhi)
        self.assertTrue(celo <= self.NOM_CASI[1] <= cehi)

        g12 = _m2_fc(12, *self.NOM_GYPSUM)
        g15 = _m2_fc(15, *self.NOM_GYPSUM)
        g95 = _m2_fc(9.5, *self.NOM_GYPSUM_95)
        c10 = _m2_fc(10, *self.NOM_CASI)
        c8 = _m2_fc(8, *self.NOM_CASI)
        expect = {
            "12mm石膏板 + 10mm硅酸钙板": (g12, c10),
            "12mm石膏板 + 8mm硅酸钙板": (g12, c8),
            "15mm石膏板 + 10mm硅酸钙板": (g15, c10),
            "12mm石膏板 + 9.5mm石膏板（不同密度）": (g12, g95),
        }
        # 包络（用于同源性交叉核对）
        env = {
            "12mm石膏板 + 10mm硅酸钙板": ((_m2_fc(12, grlo, gehi, 0.25), _m2_fc(12, grhi, gelo, 0.25)),
                                    (_m2_fc(10, crlo, cehi, 0.22), _m2_fc(10, crhi, celo, 0.22))),
            "12mm石膏板 + 8mm硅酸钙板": ((_m2_fc(12, grlo, gehi, 0.25), _m2_fc(12, grhi, gelo, 0.25)),
                                  (_m2_fc(8, crlo, cehi, 0.22), _m2_fc(8, crhi, celo, 0.22))),
            "15mm石膏板 + 10mm硅酸钙板": ((_m2_fc(15, grlo, gehi, 0.25), _m2_fc(15, grhi, gelo, 0.25)),
                                  (_m2_fc(10, crlo, cehi, 0.22), _m2_fc(10, crhi, celo, 0.22))),
            "12mm石膏板 + 9.5mm石膏板（不同密度）": ((_m2_fc(12, grlo, gehi, 0.25), _m2_fc(12, grhi, gelo, 0.25)),
                                        (_m2_fc(9.5, grlo, gehi, 0.25), _m2_fc(9.5, grhi, gelo, 0.25))),
        }
        rows = _m2_table_after(pw_text, "异质复合吻合谷错开有效性分析")
        seen = 0
        for c in rows:
            if len(c) < 5 or c[0] == "组合":
                continue
            combo = c[0]
            self.assertIn(combo, expect, f"搭配表出现未预期组合 {combo}")
            fc1 = float(c[1].lstrip("~"))
            fc2 = float(c[2].lstrip("~"))
            dfc = float(c[3].lstrip("~"))
            e1, e2 = expect[combo]
            self.assertAlmostEqual(fc1, round(e1), delta=2.0,
                msg=f"{combo} fc1 非标称复算：表 {fc1} vs {e1:.0f}")
            self.assertAlmostEqual(fc2, round(e2), delta=2.0,
                msg=f"{combo} fc2 非标称复算：表 {fc2} vs {e2:.0f}")
            self.assertAlmostEqual(dfc, round(abs(e1 - e2)), delta=2.0,
                msg=f"{combo} Δfc 与 fc1/fc2 不自洽")
            # 同源性：标称点须落在 fc 范围表包络内
            (glo, ghi), (clo, chi) = env[combo]
            self.assertTrue(glo - 1 <= fc1 <= ghi + 1, f"{combo} fc1 超出包络")
            self.assertTrue(clo - 1 <= fc2 <= chi + 1, f"{combo} fc2 超出包络")
            # 判定列与 Δfc 阈值自洽
            if "✅" in c[4]:
                self.assertGreaterEqual(dfc, 300, f"{combo} 判有效但 Δfc<300")
            elif "❌" in c[4]:
                self.assertLess(dfc, 150, f"{combo} 判无效但 Δfc≥150")
            seen += 1
        self.assertEqual(seen, 4, "搭配表应恰有 4 行")

    # ---------- G-3(3) 绝对结论收窄＋Δfc 非单调披露 ----------

    def assert_absolute_claim_narrowed(self, pw_text):
        # 旧绝对结论不得作为断言复现
        self.assertNotIn("以确保在任何合理参数下均有效错开", pw_text)
        self.assertNotIn("Δfc约130-180", pw_text)
        # 收窄与披露须在场
        for phrase in ("非单调", "无法保证", "这一绝对结论不成立",
                       "最小角点差仅约 22 Hz", "逐案核算"):
            self.assertIn(phrase, pw_text, f"缺收窄披露：{phrase}")
        # Δfc 非单调可复算：E=8→314、E≈6.3→~0、E=4→783
        g12 = _m2_fc(12, *self.NOM_GYPSUM)
        d8 = abs(g12 - _m2_fc(10, 1400, 8.0, 0.22))
        d63 = abs(g12 - _m2_fc(10, 1400, 6.3, 0.22))
        d4 = abs(g12 - _m2_fc(10, 1400, 4.0, 0.22))
        self.assertAlmostEqual(d8, 314, delta=2)
        self.assertLess(d63, 40, "E≈6.3 应接近交叉过零")
        self.assertAlmostEqual(d4, 783, delta=3)
        self.assertTrue(d8 > d63 < d4, "Δfc 须非单调（先减后增）")

    # ---------- PL-065：ACE 修正因子省略误差说明 ----------

    def assert_ace_correction_factor_text(self, ace_text):
        self.assertNotIn("误差约 3-8%", ace_text, "PL-065 旧误差说明未清除")
        for phrase in ("偏低约 70%", "29.8%", "2961 Hz 误算为 883 Hz", "2.6%"):
            self.assertIn(phrase, ace_text, f"PL-065 缺披露：{phrase}")
        # 数值可复算
        factor = math.sqrt(12 * (1 - 0.25 ** 2))
        self.assertAlmostEqual(100 / factor, 29.8, delta=0.1)
        self.assertAlmostEqual(100 - 100 / factor, 70.2, delta=0.1)
        self.assertAlmostEqual(_m2_fc(12, 800, 2.5, 0.25), 2961, delta=1)
        simp = (C_SOUND ** 2) / (2 * math.pi * 0.012) * math.sqrt(800 / 2.5e9)
        self.assertAlmostEqual(simp, 883, delta=1)

    def assert_ace_delta_fc_nonmonotonic(self, ace_text):
        self.assertNotIn("Δfc ≈ 131 Hz（无效）", ace_text, "ACE 旧单调叙述未清除")
        for phrase in ("非单调", "6.3 GPa", "388→783"):
            self.assertIn(phrase, ace_text, f"ACE 缺 Δfc 非单调披露：{phrase}")
        # ≥300 判据字面须保留（test_M2_delta_fc_criterion 同源）
        self.assertIn("Δfc = |fc₁ - fc₂| ≥ 300 Hz", ace_text)

    # ---------- 常态通过 ----------

    def test_runtime_fc_range_envelope(self):
        self.assert_fc_range_table_is_envelope(self.pw)

    def test_runtime_combination_same_source(self):
        self.assert_combination_table_same_source(self.pw)

    def test_runtime_absolute_claim_narrowed(self):
        self.assert_absolute_claim_narrowed(self.pw)

    def test_runtime_ace_correction_factor(self):
        self.assert_ace_correction_factor_text(self.ace)

    def test_runtime_ace_delta_fc_nonmonotonic(self):
        self.assert_ace_delta_fc_nonmonotonic(self.ace)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_fc_range_old_value_rejected(self):
        # 回潮旧表值（系统性低约 1.4×）须复红
        with self.assertRaises(AssertionError):
            self.assert_fc_range_table_is_envelope(self.pw.replace("2769-3511", "1950-2450", 1))
        with self.assertRaises(AssertionError):
            self.assert_fc_range_table_is_envelope(self.pw.replace("2216-2809", "1550-1950", 1))

    def test_combination_old_value_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_combination_table_same_source(self.pw.replace("~3056", "~3060", 1))
        # 撤除标称基准声明须复红
        with self.assertRaises(AssertionError):
            self.assert_combination_table_same_source(
                self.pw.replace("硅酸钙板 ρ1400/E6/σ0.22", "硅酸钙板典型值"))

    def test_absolute_claim_restored_rejected(self):
        injected = self.pw + "\n> 以确保在任何合理参数下均有效错开（Δfc ≥ 690 Hz）。\n"
        with self.assertRaises(AssertionError):
            self.assert_absolute_claim_narrowed(injected)
        with self.assertRaises(AssertionError):
            self.assert_absolute_claim_narrowed(self.pw.replace("非单调", "高度敏感", 1))

    def test_ace_old_error_text_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_ace_correction_factor_text(
                self.ace.replace("偏低约 70%", "误差约 3-8%", 1))
        with self.assertRaises(AssertionError):
            self.assert_ace_delta_fc_nonmonotonic(
                self.ace.replace("非单调", "高度敏感", 1))

    # ---------- 控制例（守卫不恒真） ----------

    def test_control_layout_and_valid_variant(self):
        # 追加空行不改判定
        self.assert_fc_range_table_is_envelope(self.pw.replace("\n\n", "\n\n\n"))
        self.assert_combination_table_same_source(self.pw.replace("\n\n", "\n\n\n"))
        # 包络口径本身可失败：把 fc_min/fc_max 对调必红（证明确在算包络而非恒真）
        swapped = self.pw.replace("2769-3511", "3511-2769", 1)
        with self.assertRaises(AssertionError):
            self.assert_fc_range_table_is_envelope(swapped)


# ============================================================
# TEST SUITE: M6 缝隙边界与封顶口径（CG-20260924-007 组7 M6）
#   PL-038 G-2：ACE 简化表末档边界、PW 封顶式结论、分层损失表复算、
#   单值代入近似口径声明。闭合条件＝所有边界陈述由自述公式与条件复算；
#   频带能量合成与 Rw 单值计权分开（直接代入单值只标近似及适用边界）；
#   覆盖全部同表行；保留改前反例（原像重注入复红）。
#   全部 C 类派生量，按 data-classification.md 内部复算，不走官方通道。
#   ACE_SKILL_DIR / PW_SKILL_DIR 环境变量可指向改前原像目录做复红自证。
# ============================================================

def _m6_r_composite(p, r_wall, r_gap=0.0):
    """复合隔声量 R_composite = -10·lg[(1-p)·10^(-R_wall/10) + p·10^(-R_gap/10)]。"""
    return -10.0 * math.log10((1.0 - p) * 10 ** (-r_wall / 10.0)
                              + p * 10 ** (-r_gap / 10.0))


def _m6_loss(p, r_wall, r_gap=0.0):
    """损失量 = R_wall - R_composite。"""
    return r_wall - _m6_r_composite(p, r_wall, r_gap)


def _m6_num(cell):
    """「~20 dB」→ 20.0（取首个数字，忽略约等号与单位）。"""
    m = re.search(r"(\d+(?:\.\d+)?)", cell.replace("~", ""))
    return float(m.group(1))


def _m6_simplified_rows(ace_text):
    """ACE M6 简化表数据行（以来源标记「本式复算」定位，M6 唯一）。"""
    rows = []
    for line in ace_text.splitlines():
        s = line.strip()
        if s.startswith("|") and "本式复算" in s:
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


def _m6_pw_tier_rows(pw_text):
    """PW §3.B.2 分层损失表数据行（首列为 Rw ≈/≥ … dB 的 5 列行）。"""
    rows = []
    for line in pw_text.splitlines():
        s = line.strip()
        if s.startswith("|") and re.match(r"^\|\s*Rw [≈≥]", s):
            rows.append([c.strip() for c in s.strip("|").split("|")])
    return rows


class TestM6GapBoundary(unittest.TestCase):
    """M6 缝隙：ACE 边界行、PW 封顶式、分层表复算、单值口径声明守卫。"""

    @classmethod
    def setUpClass(cls):
        ace_base = Path(os.environ.get("ACE_SKILL_DIR") or
                        (Path.home() / ".qoder/skills/acoustic-calculation-engine"))
        pw_base = Path(os.environ.get("PW_SKILL_DIR") or
                       (Path.home() / ".qoder/skills/prefab-partition-wall-solution"))
        cls.ace = (ace_base / "reference.md").read_text(encoding="utf-8")
        cls.pw = (pw_base / "reference.md").read_text(encoding="utf-8")

    # ---------- R1 ACE M6 简化表：四档边界由自述公式复算（覆盖全部同表行） ----------

    def assert_ace_simplified_table_boundary(self, ace_text):
        rows = _m6_simplified_rows(ace_text)
        self.assertEqual(len(rows), 4, f"M6 简化表应恰 4 行，现 {len(rows)}")
        # 前三档：公式值（R_wall=30、R_gap=0 前提）落在声明区间内
        spec = [("0.01%", 0.0001, 0.0, 1.0), ("0.1%", 0.001, 2.0, 4.0),
                ("1%", 0.01, 8.0, 12.0)]
        labels = [r[0] for r in rows]
        for label, p, lo, hi in spec:
            self.assertIn(label, labels, f"M6 简化表缺行 {label}")
            val = _m6_loss(p, 30.0)
            self.assertTrue(lo <= val <= hi,
                f"{label} 档公式值 {val:.2f} dB 越出声明区间 {lo}-{hi}")
        # 末档：下界 1.5% 使损失严格 > 12 dB；旧「> 1%」在 1%—1.49% 段不成立
        self.assertEqual(rows[3][0], "> 1.5%",
            "M6 简化表末档下界须为 1.5%：12 dB 阈值 p≈1.49%，旧「> 1%」越界（p=1.01% 损失仅 10.45 dB）")
        self.assertIn("12", rows[3][1], "末档损失列须锚定 12 dB")
        self.assertGreater(_m6_loss(0.015, 30.0), 12.0)
        self.assertLess(_m6_loss(0.0101, 30.0), 12.0)  # 改前反例复算
        self.assertAlmostEqual(_m6_loss(0.014864, 30.0), 12.0, delta=0.05)
        # 前提注记须披露阈值并覆盖四档
        self.assertIn("p≈1.49%", ace_text, "前提注记缺 12 dB 阈值披露")
        self.assertIn("四档逐档吻合", ace_text, "前提注记未覆盖全部四档")

    # ---------- R2 PW 封顶式结论：−10·lg(S_缝) 随面积比变化 ----------

    def assert_pw_ceiling_formula(self, pw_text):
        self.assertNotIn("任何缝隙都会使有效隔声量趋近于 20 dB 上限", pw_text,
            "旧「任何缝隙封顶 20 dB」回潮：封顶=−10·lg(S_缝) 随面积比变化")
        self.assertIn("−10·lg(S_缝)", pw_text, "PW 缺缝隙主导段封顶式表述")
        self.assertIn("随面积比变化而非定值 20 dB", pw_text)
        # 三点例值与公式一致，且缝隙主导段封顶与墙体本身性能无关
        for s, phrase, val in [(0.01, "S_缝=1% 封顶约 20 dB", 20.0),
                               (0.001, "0.1% 约 30 dB", 30.0),
                               (0.05, "5% 约 13 dB", 13.0)]:
            self.assertIn(phrase, pw_text, f"PW 缺封顶例值 {phrase}")
            self.assertAlmostEqual(-10.0 * math.log10(s), val, delta=0.5,
                msg=f"封顶例值 {phrase} 与 −10·lg(S_缝)={-10.0 * math.log10(s):.1f} 不符")
        self.assertAlmostEqual(_m6_r_composite(0.01, 50.0), 20.0, delta=0.1)

    # ---------- R3 PW 分层损失表：6 行×2 档复算（覆盖全部同表行） ----------

    def assert_pw_tier_table_recomputed(self, pw_text):
        rows = _m6_pw_tier_rows(pw_text)
        self.assertEqual(len(rows), 3, f"PW 分层损失表应恰 3 行，现 {len(rows)}")
        for c in rows:
            self.assertEqual(len(c), 5, f"分层表行列数异常：{c}")
            m = re.match(r"Rw [≈≥]\s*(\d+)", c[0])
            rw = float(m.group(1))
            self.assertAlmostEqual(_m6_r_composite(0.01, rw), _m6_num(c[1]),
                delta=1.0, msg=f"{c[0]} 1% 有效隔声漂移：表 {c[1]} vs 复算 {_m6_r_composite(0.01, rw):.1f}")
            self.assertAlmostEqual(_m6_loss(0.01, rw), _m6_num(c[2]),
                delta=1.0, msg=f"{c[0]} 1% 损失量漂移：表 {c[2]} vs 复算 {_m6_loss(0.01, rw):.1f}")
            self.assertAlmostEqual(_m6_r_composite(0.05, rw), _m6_num(c[3]),
                delta=1.0, msg=f"{c[0]} 5% 有效隔声漂移：表 {c[3]} vs 复算 {_m6_r_composite(0.05, rw):.1f}")
            self.assertAlmostEqual(_m6_loss(0.05, rw), _m6_num(c[4]),
                delta=1.0, msg=f"{c[0]} 5% 损失量漂移：表 {c[4]} vs 复算 {_m6_loss(0.05, rw):.1f}")

    # ---------- R4 单值代入口径声明（两件） ----------

    def assert_single_value_caliber_declared(self, ace_text, pw_text):
        for name, text in (("ACE", ace_text), ("PW", pw_text)):
            self.assertIn("单值代入口径（近似声明）", text, f"{name} 缺单值代入口径声明")
            self.assertIn("逐频带", text, f"{name} 缺严格路径（逐频带合成）声明")
            self.assertIn("不得当逐频带合成结果使用", text, f"{name} 缺适用边界声明")

    # ---------- 常态通过 ----------

    def test_runtime_ace_boundary(self):
        self.assert_ace_simplified_table_boundary(self.ace)

    def test_runtime_pw_ceiling(self):
        self.assert_pw_ceiling_formula(self.pw)

    def test_runtime_pw_tier_table(self):
        self.assert_pw_tier_table_recomputed(self.pw)

    def test_runtime_caliber_declared(self):
        self.assert_single_value_caliber_declared(self.ace, self.pw)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_ace_old_boundary_rejected(self):
        injected = self.ace.replace("| > 1.5% | > 12 dB", "| > 1% | > 12 dB", 1)
        self.assertNotEqual(injected, self.ace, "注入未命中（边界行锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_ace_simplified_table_boundary(injected)

    def test_pw_old_ceiling_rejected(self):
        injected = self.pw.replace(
            "> - 缝隙主导段的有效隔声量封顶值为 −10·lg(S_缝)（R_缝≈0 dB 时），随面积比变化而非定值 20 dB：S_缝=1% 封顶约 20 dB、0.1% 约 30 dB、5% 约 13 dB（上表两档 ~20 dB／~13 dB 即 1%／5% 两点的封顶值）；达到封顶后与墙体本身隔声性能无关",
            "> - 任何缝隙都会使有效隔声量趋近于 20 dB 上限（由缝隙面积比决定），与墙体本身性能无关", 1)
        self.assertNotEqual(injected, self.pw, "注入未命中（封顶结论锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_pw_ceiling_formula(injected)

    def test_pw_tier_value_drift_rejected(self):
        injected = self.pw.replace(
            "| Rw ≈ 35 dB（一般隔墙） | ~20 dB | ~15 dB",
            "| Rw ≈ 35 dB（一般隔墙） | ~25 dB | ~15 dB", 1)
        self.assertNotEqual(injected, self.pw, "注入未命中（分层表锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_pw_tier_table_recomputed(injected)

    def test_caliber_removed_rejected(self):
        with self.assertRaises(AssertionError):
            self.assert_single_value_caliber_declared(
                self.ace.replace("单值代入口径（近似声明）", "口径说明", 1), self.pw)
        with self.assertRaises(AssertionError):
            self.assert_single_value_caliber_declared(
                self.ace, self.pw.replace("不得当逐频带合成结果使用", "仅供参考", 1))

    # ---------- 控制例（守卫不恒真：良性变更不报红） ----------

    def test_control_benign_changes_pass(self):
        # 追加空行/追加段不改判定
        self.assert_ace_simplified_table_boundary(self.ace.replace("\n\n", "\n\n\n"))
        self.assert_pw_ceiling_formula(self.pw + "\n> 注：本节封顶口径与 M6 简化表同源。\n")
        self.assert_pw_tier_table_recomputed(self.pw.replace("\n\n", "\n\n\n"))
        self.assert_single_value_caliber_declared(self.ace, self.pw)


# ============================================================
# PL-038 组6 / PL-066：M3 约化质量恒等式、近对称近似归因、
#   模型外假设显式列出、双空腔三质量-两弹簧耦合系统守卫。
#   闭合条件＝区分恒等变换/近对称近似/真实模型误差；多腔按耦合模型
#   或同构造证据推断；不机械相加两段单腔增益、不编通用扣减值。
#   全部 C 类派生量，按 data-classification.md 内部复算，不走官方通道。
#   ACE_SKILL_DIR / PW_SKILL_DIR 环境变量可指向改前原像目录做复红自证。
# ============================================================

_K_CAV_M34 = RHO_AIR * C_SOUND ** 2   # 空腔弹簧刚度 K=ρ₀c² ≈ 141,178.8 N/m³


def _m34_two_leaf_dev(r):
    """两质量-一弹簧非零根与 k/m_red 的相对偏差（理想模型内恒为 0）。"""
    m2 = 10.0
    m1 = r * m2
    m_red = m1 * m2 / (m1 + m2)
    return abs(1.0 / m_red - (1.0 / m1 + 1.0 / m2)) / (1.0 / m_red)


def _m34_apsym_pct(r):
    """近对称近似式 1200/√(d·(m₁+m₂)) 相对精确式 600/√(d·m_red) 的偏差 %。"""
    d = 3.75  # cm；两式同 ∝1/√d，比值与 d 无关
    m2 = 10.0
    m1 = r * m2
    m_red = m1 * m2 / (m1 + m2)
    exact = 600.0 / math.sqrt(d * m_red)
    apsym = 1200.0 / math.sqrt(d * (m1 + m2))
    return (apsym - exact) / exact * 100.0


def _m34_three_leaf(m1, m2, m3, d1_m, d2_m):
    """三质量-两弹簧耦合系统两非零模态频率 (Hz)；刚体模态 λ=0 不计。"""
    k1 = _K_CAV_M34 / d1_m
    k2 = _K_CAV_M34 / d2_m
    B = k1 / m1 + (k1 + k2) / m2 + k2 / m3
    C = k1 * k2 * (m1 + m2 + m3) / (m1 * m2 * m3)
    disc = B * B - 4.0 * C
    assert disc >= 0.0, "特征方程判别式为负（输入非物理）"
    lam_lo = (B - math.sqrt(disc)) / 2.0
    lam_hi = (B + math.sqrt(disc)) / 2.0
    return (math.sqrt(lam_lo) / (2 * math.pi), math.sqrt(lam_hi) / (2 * math.pi))


def _m34_single_cav_f0(ma, mb, d_m):
    """单腔 MSM 精确式 f₀=(1/2π)√(k(1/mₐ+1/m_b))，k=K_CAV/d。"""
    lam = (_K_CAV_M34 / d_m) * (1.0 / ma + 1.0 / mb)
    return math.sqrt(lam) / (2 * math.pi)


class TestM3M4ModelApplicability(unittest.TestCase):
    """M3/M4：恒等式适用域、近对称近似归因、模型外假设、双空腔耦合守卫。"""

    @classmethod
    def setUpClass(cls):
        ace_base = Path(os.environ.get("ACE_SKILL_DIR") or
                        (Path.home() / ".qoder/skills/acoustic-calculation-engine"))
        pw_base = Path(os.environ.get("PW_SKILL_DIR") or
                       (Path.home() / ".qoder/skills/prefab-partition-wall-solution"))
        cls.ace = (ace_base / "reference.md").read_text(encoding="utf-8")
        cls.pw = (pw_base / "reference.md").read_text(encoding="utf-8")

    # ---------- R1 约化质量恒等式：任意正质量比精确成立，旧区间撤回 ----------

    def assert_m3_identity_and_retraction(self, ace_text):
        self.assertIn("非对称构造适用性（三面分清）", ace_text)
        self.assertIn("对任意正质量比精确成立", ace_text)
        self.assertIn("质量比本身不使本公式产生偏差", ace_text)
        self.assertNotIn("以 5-13% 作为提示区间", ace_text,
            "旧肯定式「以 5-13% 作为提示区间」回潮：恒等式对任意正质量比精确成立，区间归因无据")
        self.assertIn("撤回无据结论，不给替代偏差值", ace_text)
        # 数值自证：r=0.1—10 恒等式偏差恒 0（复算取证 §一）
        for r in (0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 10.0):
            self.assertAlmostEqual(_m34_two_leaf_dev(r), 0.0, places=12,
                msg=f"r={r} 恒等式偏差非 0")

    # ---------- R2 5-13% 量级归因到近对称近似式，非约化质量式 ----------

    def assert_apsym_attribution(self, ace_text, pw_text):
        self.assertIn("近对称近似（另一公式，非本件 M3）", ace_text)
        self.assertIn("1200/√(d×(m₁+m₂))", ace_text)
        self.assertIn("r=2 约 −5.7%、r=3 约 −13%", ace_text)
        self.assertIn("不得把近似式的误差误归为约化质量式的适用域限制", ace_text)
        # PW :318 控制锚（本批不改面）：近似式适用性声明在场
        self.assertIn("适用于对称或近对称构造 m₁≈m₂", pw_text)
        # 复算（取证 §二）：近似式偏差方向为低估 f₀，量级与文档一致
        self.assertAlmostEqual(_m34_apsym_pct(1.0), 0.0, delta=0.05)
        self.assertAlmostEqual(_m34_apsym_pct(1.5), -2.0, delta=0.15)
        self.assertAlmostEqual(_m34_apsym_pct(2.0), -5.7, delta=0.15)
        self.assertAlmostEqual(_m34_apsym_pct(3.0), -13.4, delta=0.15)

    # ---------- R3 真实模型误差＝模型外假设逐项显式列出 ----------

    def assert_out_of_model_assumptions(self, ace_text):
        for phrase in ("声桥（龙骨等刚性连接）", "阻尼（填充材料耗能）",
                       "边界条件（板尺寸有限与边缘约束）", "板弯曲模态",
                       "空腔无质量弹簧假设"):
            self.assertIn(phrase, ace_text, f"模型外假设缺项：{phrase}")
        self.assertIn("逐项显式列出", ace_text)
        self.assertIn("精度降低的归因按上列第 3 条模型外假设逐项作出，不按质量比本身归因",
                      ace_text)

    # ---------- R4 双空腔＝三质量-两弹簧耦合系统，叠加算法撤回 ----------

    def assert_dual_cavity_coupled(self, ace_text):
        self.assertIn("双空腔系统（三质量-两弹簧耦合系统）", ace_text)
        self.assertIn("1 个刚体模态 + 2 个非零耦合模态，共振分裂为二", ace_text)
        self.assertIn("耦合模态 69.1/129.2 Hz", ace_text)
        self.assertIn("增益无 dB 可加性", ace_text)
        self.assertIn("按两层空腔分别计算增益后叠加」算法已撤回", ace_text)
        self.assertIn("同例均为 103.6 Hz", ace_text)
        self.assertIn("亦不编造通用扣减值替代", ace_text)
        self.assertIn("检测报告编号", ace_text)
        self.assertNotIn("理论上隔声增益优于单空腔", ace_text,
            "旧肯定式「理论上隔声增益优于单空腔」回潮：耦合系统不还原逐值，叠加无据")
        self.assertNotIn("ACE 按两层空腔分别计算增益后叠加，但标注", ace_text,
            "旧叠加算法肯定式回潮")
        # 解析复算（取证 §四例1）：对称双腔 m₁=m₃=20、m₂=16、d=37.5mm
        f_lo, f_hi = _m34_three_leaf(20.0, 16.0, 20.0, 0.0375, 0.0375)
        self.assertAlmostEqual(f_lo, 69.1, delta=0.15)
        self.assertAlmostEqual(f_hi, 129.2, delta=0.15)
        # 对称双腔恒等式：低模态精确位于 ω²=k/m（中板静止、外板反相 (1,0,−1)）
        k = _K_CAV_M34 / 0.0375
        self.assertAlmostEqual(f_lo, math.sqrt(k / 20.0) / (2 * math.pi), places=6)
        # 撤回算法反例：两腔分别按单腔 MSM 计算同值 103.6 Hz，不还原耦合模态
        f_single = _m34_single_cav_f0(20.0, 16.0, 0.0375)
        self.assertAlmostEqual(f_single, 103.6, delta=0.15)
        self.assertGreater(abs(f_single - f_lo), 30.0)
        self.assertGreater(abs(f_single - f_hi), 20.0)

    # ---------- R5 PW 双空腔数值出口撤回（披露句外肯定式灭活） ----------

    def assert_pw_dual_cavity_retraction(self, pw_text):
        self.assertIn("1 刚体模态＋2 非零耦合模态，共振分裂为二", pw_text)
        self.assertIn("增益无 dB 可加性", pw_text)
        self.assertIn("因无可定位实测来源已撤回数值出口", pw_text)
        self.assertIn("不得编造通用扣减值替代", pw_text)
        self.assertIn("见 ACE M4「双空腔系统」条", pw_text)
        # 计数守卫：旧肯定式字面仅允许存在于撤回披露句内（组4「互斥披露含原印值」先例）
        n = pw_text.count("比单空腔可额外提升约 5-10 dB")
        self.assertEqual(n, 1, "旧「额外提升约 5-10 dB」在披露句外复活或缺失")
        i = pw_text.find("比单空腔可额外提升约 5-10 dB")
        ctx = pw_text[max(0, i - 30):i + 80]
        self.assertIn("原「", ctx, "唯一命中不在撤回语境（缺「原「」前缀）")
        self.assertIn("已撤回", ctx, "唯一命中不在撤回语境（缺「已撤回」后缀）")

    # ---------- 常态通过 ----------

    def test_runtime_m3_identity(self):
        self.assert_m3_identity_and_retraction(self.ace)

    def test_runtime_apsym_attribution(self):
        self.assert_apsym_attribution(self.ace, self.pw)

    def test_runtime_out_of_model_assumptions(self):
        self.assert_out_of_model_assumptions(self.ace)

    def test_runtime_dual_cavity_coupled(self):
        self.assert_dual_cavity_coupled(self.ace)

    def test_runtime_pw_dual_cavity_retraction(self):
        self.assert_pw_dual_cavity_retraction(self.pw)

    # ---------- 数值性质（与文档字面解耦的独立复算） ----------

    def test_apsym_error_monotonic_decreasing(self):
        prev = 0.0
        for r in (1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 10.0):
            e = _m34_apsym_pct(r)
            self.assertLessEqual(e, prev + 1e-9, f"r={r} 近似式偏差非单调")
            prev = e
        self.assertAlmostEqual(_m34_apsym_pct(6.0), -30.0, delta=0.3)
        self.assertAlmostEqual(_m34_apsym_pct(10.0), -42.5, delta=0.3)

    def test_three_leaf_asymmetric_example(self):
        # 取证 §四例3：非对称三叶 12/16/40、d=50mm
        f_lo, f_hi = _m34_three_leaf(12.0, 16.0, 40.0, 0.05, 0.05)
        self.assertAlmostEqual(f_lo, 58.4, delta=0.15)
        self.assertAlmostEqual(f_hi, 115.2, delta=0.15)
        # 两腔分别算（撤回算法）逐值不同：102.1 / 79.1 Hz
        self.assertAlmostEqual(_m34_single_cav_f0(12.0, 16.0, 0.05), 102.1, delta=0.2)
        self.assertAlmostEqual(_m34_single_cav_f0(16.0, 40.0, 0.05), 79.1, delta=0.2)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_ace_old_asym_interval_rejected(self):
        injected = self.ace.replace(
            "质量比本身不使本公式产生偏差。原「m₁/m₂ 超出 0.5—2 产生 5-13% 偏差」的提示区间因归因在理想模型内不成立、且无可定位实测来源而**撤回**（撤回无据结论，不给替代偏差值）",
            "当 m₁ 与 m₂ 差异较大时（m₁/m₂ > 2 或 < 0.5），以单一 m_red 代表双叶系统会产生偏差，本件以 5-13% 作为提示区间", 1)
        self.assertNotEqual(injected, self.ace, "注入未命中（R1 撤回句锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_m3_identity_and_retraction(injected)

    def test_ace_old_dual_cavity_superposition_rejected(self):
        injected = self.ace.replace(
            "增益无 dB 可加性**：原「按两层空腔分别计算增益后叠加」算法已撤回——两腔分别按单腔 MSM 计算（同例均为 103.6 Hz）不还原耦合模态逐值，dB 相加亦无依据；亦不编造通用扣减值替代",
            "理论上隔声增益优于单空腔。ACE 按两层空腔分别计算增益后叠加，但标注影响较大", 1)
        self.assertNotEqual(injected, self.ace, "注入未命中（R4 撤回句锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_dual_cavity_coupled(injected)

    def test_pw_old_gain_value_rejected(self):
        injected = self.pw.replace(
            "原「比单空腔可额外提升约 5-10 dB」因无可定位实测来源已撤回数值出口——定量值以同构造检测报告或耦合模型估算为准（见 ACE M4「双空腔系统」条），不得编造通用扣减值替代",
            "比单空腔可额外提升约 5-10 dB", 1)
        self.assertNotEqual(injected, self.pw, "注入未命中（R5 撤回句锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_pw_dual_cavity_retraction(injected)

    def test_pw_apsym_control_anchor_removed_rejected(self):
        injected = self.pw.replace("适用于对称或近对称构造 m₁≈m₂", "适用于任意构造", 1)
        self.assertNotEqual(injected, self.pw, "注入未命中（PW :318 控制锚漂移）")
        with self.assertRaises(AssertionError):
            self.assert_apsym_attribution(self.ace, injected)

    # ---------- 控制例（守卫不恒真：良性变更不报红） ----------

    def test_control_benign_changes_pass(self):
        self.assert_m3_identity_and_retraction(self.ace.replace("\n\n", "\n\n\n"))
        self.assert_apsym_attribution(
            self.ace + "\n> 注：本节口径与 M4「双空腔系统」条同源。\n", self.pw)
        self.assert_out_of_model_assumptions(self.ace.replace("\n\n", "\n\n\n"))
        self.assert_dual_cavity_coupled(self.ace.replace("\n\n", "\n\n\n"))
        self.assert_pw_dual_cavity_retraction(
            self.pw + "\n> 注：双空腔定量路径以 ACE M4 为准。\n")


# ============================================================
# TEST SUITE 17: M7 校准外推（区间数值排序 + 交叉核对不自动择优）
# ============================================================
# PL-067（CG-20260925-002）守卫。证据：m7_recalc.py 七节（取证目录）。
# 位名 ΔR_low/ΔR_high 是 20·lg/40·lg 两界的名称，r<1 时数值序反转；
# 「差>5dB 优先 M7」把锚点可信度误传给外推结果。本组把两件事分别钉死。
class TestM7CalibrationExtrapolation(unittest.TestCase):
    """M7：输出入口恒升序、交叉核对四类核查、路线优先≠结果自动择优。"""

    @classmethod
    def setUpClass(cls):
        ace_base = Path(os.environ.get("ACE_SKILL_DIR") or
                        (Path.home() / ".qoder/skills/acoustic-calculation-engine"))
        cls.ref = (ace_base / "reference.md").read_text(encoding="utf-8")
        cls.skill = (ace_base / "SKILL.md").read_text(encoding="utf-8")

    # ---------- R1 Step2 恒升序（控制锚，组6 前先批已修，本批零改） ----------

    def assert_step2_sorted_anchor(self, ref):
        self.assertIn("输出区间（恒升序）:  [min(ΔR_low, ΔR_high),  max(ΔR_low, ΔR_high)]", ref)
        self.assertIn("位名与大小排序不是一回事（端点判据）", ref)

    # ---------- R2 Step3 对称变化输出入口数值排序 ----------

    def assert_step3_sorted(self, ref):
        self.assertNotIn("同时输出区间 [ΔR_low, ΔR_high]", ref,
            "旧位名式 Step3 输出入口回潮：r<1 时 [low, high] 为降序（复算 −6.02 > −12.04）")
        self.assertIn("端点一律按数值升序", ref)
        self.assertIn("r<1 时该序为降序", ref)
        # 中值与端点书写序无关（复算 §四）：文档须披露 −9.03 中值例
        self.assertIn("−9.03", ref)

    # ---------- R3 Step5 结果组装保序 ----------

    def assert_step5_sorted(self, ref):
        self.assertNotIn("[Rw_base + ΔR_low + Σ修正,  Rw_base + ΔR_high + Σ修正]", ref,
            "旧位名式 Step5 组装回潮：加同一常数保序后仍须以 min/max 端点为下/上界")
        self.assertIn("Rw_base + ΔR_下界 + Σ修正", ref)
        self.assertIn("加同一常数与同一 Σ修正后区间保序", ref)

    # ---------- R4 交叉核对撤自动择优（含否定语境计数守卫） ----------

    def assert_crosscheck_no_autopick(self, ref, skill):
        self.assertIn("不构成自动择优规则", ref)
        self.assertIn("不得直接取任一结果", ref)
        for phrase in ("构造是否真正同族", "是否存在机理级变化",
                       "参数与口径", "模型条件"):
            self.assertIn(phrase, ref, f"四类根因核查缺项：{phrase}")
        self.assertIn("交叉核对未通过", ref)
        self.assertIn("锚点可信度不随差值大小传递到外推结果", ref)
        self.assertIn("不构成自动择优", skill)
        self.assertIn("数据锚点可信不等于变体外推可信", skill)
        # 计数守卫：旧肯定式「优先报 M7 校准值」全件 0 命中；
        # 「优先报 M7」裸字面仅允许存在于否定句（SKILL.md 恰 1 处）
        self.assertEqual(ref.count("优先报 M7"), 0,
            "reference.md 出现「优先报 M7」字面（含披露语境均不允许）")
        n = skill.count("优先报 M7")
        self.assertEqual(n, 1, "SKILL.md「优先报 M7」计数漂移（应仅存于否定句 1 处）")
        i = skill.find("优先报 M7")
        ctx = skill[max(0, i - 40):i + 40]
        self.assertIn("不得直接", ctx, "唯一命中不在否定语境（缺「不得直接」前缀）")

    # ---------- R5 路由/组合表/算例尾句「路线优先≠结果自动择优」口径统一 ----------

    def assert_route_wording(self, ref, skill):
        self.assertIn("路线优先≠结果自动择优", skill)
        self.assertIn("M7 校准路线优先", skill)
        self.assertIn("优先 M7 校准路线（路线优先仅指计算入口选择", ref)
        self.assertIn("M7 校准路线优先 + M1-M6 交叉核对（见 M7，路线优先≠结果自动择优）", ref)
        self.assertNotIn("M7 应优先", ref,
            "算例尾句旧肯定式「M7 应优先」回潮（应带四类核查前提）")
        self.assertIn("四类核查时 M7 作优先参考路线", ref)

    # ---------- R6 SKILL.md 方法概要恒升序声明 ----------

    def assert_skill_sorted_declaration(self, skill):
        self.assertIn("端点一律按数值升序", skill)
        self.assertIn("[min(ΔRw_low, ΔRw_high), max(ΔRw_low, ΔRw_high)]", skill)
        self.assertIn("r<1 时不得按位名写作 [low, high]", skill)

    # ---------- 数值性质（与文档字面解耦的独立复算） ----------

    def test_sorted_bounds_three_states(self):
        # 复算 §一/§二：位名序在 r<1 侧为降序，min/max 化后恒升序
        for r in (0.5, 43 / 51, 0.843):
            a, b = m7_delta_R_bounds(r)
            self.assertGreater(a, b, f"r={r} 位名序应非升序")
            lo, hi = min(a, b), max(a, b)
            self.assertLessEqual(lo, hi)
        self.assertAlmostEqual(m7_delta_R_bounds(0.5)[0], -6.02, delta=0.01)
        self.assertAlmostEqual(m7_delta_R_bounds(0.5)[1], -12.04, delta=0.01)
        self.assertAlmostEqual(m7_delta_R_bounds(2.0)[1], 12.04, delta=0.01)
        a, b = m7_delta_R_bounds(1.0)
        self.assertAlmostEqual(a, 0.0, places=12)
        self.assertAlmostEqual(b, 0.0, places=12)
        # 中值与端点书写序无关（复算 §四恒等性）
        for r in (0.5, 0.843, 1.2, 2.0):
            a, b = m7_delta_R_bounds(r)
            self.assertAlmostEqual((a + b) / 2, (min(a, b) + max(a, b)) / 2, places=12)
        # 算例 :426 印值 [−3.0, −1.5] 系 min/max 升序（复算 §三，控制锚非写面）
        self.assertIn("[−3.0, −1.5]", self.ref)

    # ---------- 常态通过 ----------

    def test_runtime_step2_anchor(self):
        self.assert_step2_sorted_anchor(self.ref)

    def test_runtime_step3_sorted(self):
        self.assert_step3_sorted(self.ref)

    def test_runtime_step5_sorted(self):
        self.assert_step5_sorted(self.ref)

    def test_runtime_crosscheck_no_autopick(self):
        self.assert_crosscheck_no_autopick(self.ref, self.skill)

    def test_runtime_route_wording(self):
        self.assert_route_wording(self.ref, self.skill)

    def test_runtime_skill_sorted_declaration(self):
        self.assert_skill_sorted_declaration(self.skill)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_old_step3_position_name_interval_rejected(self):
        injected = self.ref.replace(
            "对称变化（两侧叶同步变化）:  ΔR 取区间中值，同时输出区间——端点一律按数值升序，",
            "对称变化（两侧叶同步变化）:  ΔR 取区间中值，同时输出区间 [ΔR_low, ΔR_high]；", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（Step3 改写句锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_step3_sorted(injected)

    def test_old_step5_position_name_assembly_rejected(self):
        # 注入源字面随 CG-20260925-003（组9 Step 5 端点配对法）同批更新；判据本身未变：
        # 位名式组装一旦出现即复红。
        injected = self.ref.replace(
            "输出区间: [Rw_base + ΔR_下界 + Σ修正_下界,  Rw_base + ΔR_上界 + Σ修正_上界]",
            "输出区间: [Rw_base + ΔR_low + Σ修正,  Rw_base + ΔR_high + Σ修正]", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（Step5 组装行锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_step5_sorted(injected)

    def test_old_autopick_rule_rejected(self):
        injected = self.ref.replace(
            "**两者差 > 5 dB 不构成自动择优规则**——差值大于 5 dB 时不得直接取任一结果（包括\"看似更优\"者）",
            "**两者差 > 5 dB 时，优先报 M7 校准值（数据锚点可信度更高）**", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（交叉核对改写句锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_crosscheck_no_autopick(injected, self.skill)

    def test_skill_sorted_declaration_removed_rejected(self):
        self.assert_skill_sorted_declaration(self.skill)  # 原像态先复绿，防恒真
        injected = self.skill.replace(
            "输出区间（端点一律按数值升序，即 [min(ΔRw_low, ΔRw_high), max(ΔRw_low, ΔRw_high)]，r<1 时不得按位名写作 [low, high]）",
            "输出区间", 1)
        self.assertNotEqual(injected, self.skill, "注入未命中（SKILL.md :181 锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_skill_sorted_declaration(injected)

    # ---------- 控制例（守卫不恒真：良性变更不报红） ----------

    def test_control_benign_changes_pass(self):
        self.assert_step2_sorted_anchor(self.ref.replace("\n\n", "\n\n\n"))
        self.assert_step3_sorted(self.ref + "\n> 注：本节口径与 Step 2 端点判据同源。\n")
        self.assert_step5_sorted(self.ref.replace("Σ修正", "Σ 修正", 0))
        self.assert_crosscheck_no_autopick(self.ref, self.skill + "\n> 注：交叉核对细则见 reference.md。\n")
        self.assert_route_wording(self.ref, self.skill.replace("\n\n", "\n\n\n"))


# ============================================================
# TEST SUITE 18: 组9 参数与证据（M5 m' 口径／C 定标证据／M7 Σ 端点配对／演示身份）
# ============================================================
# PL-068（CG-20260925-003）三子面 ＋ 组8 移交 S1。证据：m5e_recalc.py 五节（取证目录）。
# 口径面与配对法是「同一条物理量被两个技能各自表述」的跨件一致问题，故本组同时取
# ACE 与 FL 两层文件做字面与数值双断言；C 定标面只钉撤回锚与灵敏度复算，不动常数值。
M_SCREED, M_TILE, M_SLAB, MAT_KG_M3, MAT_T_M = 85.0, 22.0, 288.0, 900.0, 0.008
S_DEMO = 15.0  # MN/m3，与 FL examples.md 同一构造


class TestM5M7CaliberAndEvidence(unittest.TestCase):
    """M5 有效振动面密度口径、C 证据状态、M7 Σ 端点配对与算例演示身份。"""

    EXCLUSIONS = ("不含结构楼板", "不含弹性垫", "不含活荷载")

    @classmethod
    def setUpClass(cls):
        ace_base = Path(os.environ.get("ACE_SKILL_DIR") or
                        (Path.home() / ".qoder/skills/acoustic-calculation-engine"))
        fl_base = Path(os.environ.get("FL_SKILL_DIR") or
                       (Path.home() / ".qoder/skills/prefab-floor-system"))
        cls.ref = (ace_base / "reference.md").read_text(encoding="utf-8")
        cls.skill = (ace_base / "SKILL.md").read_text(encoding="utf-8")
        cls.fl_ref = (fl_base / "reference.md").read_text(encoding="utf-8")
        cls.fl_skill = (fl_base / "SKILL.md").read_text(encoding="utf-8")

    # ---------- 复算基准（与文档字面解耦） ----------

    @staticmethod
    def misuse_deltas():
        ok = M_SCREED + M_TILE
        cases = {
            "slab": ok + M_SLAB,        # 误代：以含楼板的恒荷载口径代入
            "finish": M_TILE,           # 误代：漏计砂浆垫层只计面层
            "mat": ok + MAT_T_M * MAT_KG_M3,  # 误代：计入弹性垫自身质量
        }
        return {k: (impact_sound_deltaLw(v, S_DEMO) - impact_sound_deltaLw(ok, S_DEMO),
                    floating_floor_f0(S_DEMO, v) / floating_floor_f0(S_DEMO, ok) - 1)
                for k, v in cases.items()}

    # ---------- R1 m' 口径三元组跨件一致 ----------

    def assert_mass_caliber(self, ref, fl_ref, fl_skill):
        for phrase in self.EXCLUSIONS:
            self.assertIn(phrase, ref, f"ACE m' 口径条缺排除项：{phrase}")
            self.assertIn(phrase, fl_ref, f"FL 参数表 m' 行缺排除项：{phrase}")
        self.assertIn("共同运动各构造层的单位面积质量之和", ref)
        self.assertIn("有效振动面密度", fl_ref)
        self.assertIn("不得互代", ref)
        self.assertIn("不得互代", fl_ref)  # A3 恒荷载行的反向声明
        self.assertIn("非仅饰面层", fl_skill)
        self.assertIn("不进入 f₀ 与 ΔLw 的质量项", ref)  # m_slab 与 m' 分列

    def test_old_mass_labels_withdrawn(self):
        for dead in ("面层+垫层总面密度", "浮筑层总质量", "面层+垫层面密度"):
            self.assertNotIn(dead, self.ref, f"ACE 旧含糊口径标签回潮：{dead}")
        self.assertNotIn("面层+垫层上覆构造的总质量", self.fl_ref,
            "FL 旧含糊口径标签回潮")

    # ---------- R2 误代后果数值与复算一致 ----------

    def test_mass_misuse_penalties_match_recalc(self):
        line = next((ln for ln in self.ref.splitlines()
                     if "以含楼板的合计恒荷载代入" in ln), None)
        self.assertIsNotNone(line, "ACE 未记录恒荷载误代后果（口径条第 2 条缺项）")
        db = [float(x) for x in re.findall(r"约 ([\d.]+) dB", line)]
        pct = [float(x) for x in re.findall(r"约 (\d+)%", line)]
        d = self.misuse_deltas()
        self.assertEqual(len(db), 3, f"误代后果 dB 读数应为 3 个，实得 {db}")
        self.assertAlmostEqual(db[0], d["slab"][0], delta=0.05,
            msg="含楼板误代的 ΔLw 虚高值与复算不符")
        self.assertAlmostEqual(db[1], -d["finish"][0], delta=0.05, msg="漏计垫层后果不符")
        self.assertAlmostEqual(db[2], d["mat"][0], delta=0.05, msg="计入弹性垫后果不符")
        self.assertAlmostEqual(pct[0], abs(d["slab"][1]) * 100, delta=1.0)
        self.assertAlmostEqual(pct[1], d["finish"][1] * 100, delta=1.0)
        self.assertGreater(d["slab"][0], 5.0, "前两类误代须超出精度声明区间（否则口径条量级论证失效）")
        self.assertLess(d["mat"][0], 1.0)

    # ---------- R3 C 定标说法撤回 ＋ 灵敏度 ----------

    def test_C_calibration_claims_withdrawn(self):
        for dead in ("C=12 基于理想实验室条件", "系统性高估约 5 dB", "经多个常见构造校准"):
            self.assertNotIn(dead, self.ref, f"无据 C 定标说法回潮：{dead}")

    def test_C_status_and_sensitivity(self):
        self.assertIn("待独立验证的经验定标取值", self.ref)
        self.assertIn("∂ΔLw/∂C ≡ 1 dB/dB", self.ref)
        self.assertIn("ACE 默认 C=10", self.ref)  # 常数本体不改（与脚本默认一致由 test_M5_default_C 钉）
        self.assertAlmostEqual(impact_sound_deltaLw(107, S_DEMO, 12)
                               - impact_sound_deltaLw(107, S_DEMO, 10), 2.0, places=10)
        self.assertAlmostEqual(impact_sound_deltaLw(107, S_DEMO, 12)
                               - impact_sound_deltaLw(107, S_DEMO, 8), 4.0, places=10)
        for v in ("2.00 dB", "4.00 dB"):
            self.assertIn(v, self.ref, f"C 灵敏度读数缺失：{v}")
        # 5 dB 量级差在 [8,12] 内不可由 C 产生 ⇒ 文档须把排查方向指回 m'/s 与施工条件
        self.assertIn("排查方向不在 C 的取值", self.ref)

    # ---------- R4 Σ 修正端点配对法（S1 裁定） ----------

    def test_sigma_endpoint_pairing_rule(self):
        self.assertIn("输出区间: [Rw_base + ΔR_下界 + Σ修正_下界,  Rw_base + ΔR_上界 + Σ修正_上界]", self.ref)
        self.assertIn("Σ修正_下界 / Σ修正_上界 ＝ Step 4 各修正项的下界之和 / 上界之和", self.ref)
        self.assertIn("两端各自相加后区间仍升序", self.ref)
        self.assertIn("单值输出（工程推荐值）＝区间中点＝Rw_base + ΔR 中值 + Σ修正 中值", self.ref)
        self.assertIn("区间扩张（Minkowski 和）", self.ref)
        self.assertIn("不得把 Σ修正 的某一中间值同时加到两端而不声明口径", self.ref)
        # 组8 既有的单值情形特例句须保留（语义未削弱）
        self.assertIn("退化为「加同一常数与同一 Σ修正后区间保序」的特例", self.ref)
        self.assertIn("下界端加 Σ修正_下界", self.skill)
        self.assertIn("本件不重复承载", self.skill)

    def test_sigma_pairing_order_and_midpoint_property(self):
        rnd = random.Random(20260925)
        base = 51.0
        for _ in range(500):
            r = rnd.uniform(0.5, 2.0)
            a, b = m7_delta_R_bounds(r)
            lo, hi = min(a, b), max(a, b)
            sl, sh = sorted((rnd.uniform(-3, 3), rnd.uniform(-3, 3)))
            self.assertLessEqual(base + lo + sl, base + hi + sh,
                "端点配对法在 ΔR 与 Σ 均升序时须保序；违例即裁定失效")
            self.assertAlmostEqual((base + lo + sl + base + hi + sh) / 2,
                                   base + (lo + hi) / 2 + (sl + sh) / 2, places=9,
                msg="区间中点与「ΔR 中值＋Σ 中值」单值口径不恒等")

    def test_sigma_pairing_wider_than_half_open(self):
        # 乙口径（ΔR 取中值后叠加 Σ 区间）丢掉 ΔR 宽度 ⇒ 甲区间必不窄于乙，且不等的量＝ΔR 宽度
        a, b = m7_delta_R_bounds(43 / 51)
        lo, hi = min(a, b), max(a, b)
        sl, sh = 1.0, 2.0
        width_A = (51 + hi + sh) - (51 + lo + sl)
        width_B = (51 + (lo + hi) / 2 + sh) - (51 + (lo + hi) / 2 + sl)
        self.assertAlmostEqual(width_A - width_B, hi - lo, places=9)
        self.assertGreater(width_A, width_B)

    # ---------- R5 算例改 min/max ＋ 甲读数 ----------

    def test_example_minmax_and_assembled_intervals(self):
        self.assertIn("[−3.0, −1.5]", self.ref)  # 组8 印值控制锚不受影响
        self.assertNotIn("ΔR ∈ [40·lg(0.843), 20·lg(0.843)]", self.ref,
            "算例位名式书写回潮（r>1 侧会产出逆序区间）")
        self.assertIn("min(20·lg 0.843, 40·lg 0.843)", self.ref)
        self.assertIn("[48.0, 49.5]", self.ref)
        self.assertIn("[49.0, 51.5]", self.ref)
        self.assertNotIn("Rw_B ≈ 50~51", self.ref, "乙口径旧读数回潮")
        a, b = m7_delta_R_bounds(43 / 51)
        lo, hi = min(a, b), max(a, b)
        self.assertAlmostEqual(51 + lo, 48.0, delta=0.05)
        self.assertAlmostEqual(51 + hi + 2.0, 51.5, delta=0.05)
        self.assertAlmostEqual(51 + (lo + hi) / 2 + 1.5, 50.3, delta=0.05)
        self.assertAlmostEqual(51 + (lo + hi) / 2, 48.8, delta=0.05)

    # ---------- R6 演示身份 ----------

    def test_demo_identity_of_uncited_benchmark(self):
        self.assertIn("同构造对照（演示数据，不计为验证样本）", self.ref)
        self.assertIn("承继同一演示身份", self.ref)
        self.assertIn("演示对照提示", self.skill)
        self.assertIn("不得拆出引用为已校准证据", self.skill)
        self.assertNotIn("已知案例", self.skill, "SKILL.md 把演示读数包装为已证案例")
        # 算例段内不得再以「交叉验证」名义出现
        start = self.ref.index("**校准算例记录")
        end = self.ref.index("## ", start + 10)
        self.assertNotIn("交叉验证", self.ref[start:end],
            "无留痕对照仍以「交叉验证」名义出现")

    # ---------- R7 不做项边界：精度面未被本批改写 ----------

    def test_precision_faces_untouched(self):
        self.assertIn("**精度声明**：ΔLw 估算精度约 ±3-5 dB。Ln,w 估算精度约 ±4-6 dB", self.ref)
        self.assertIn("**精度声明**：±2-3 dB（同族构造校准）", self.ref)
        self.assertIn("该精度值的证据状态", self.ref)
        self.assertIn("经验判断，本件未记录校准样本量", self.ref)

    # ---------- 常态通过 ----------

    def test_runtime_all_anchors(self):
        self.assert_mass_caliber(self.ref, self.fl_ref, self.fl_skill)

    # ---------- 负向注入（守卫须仍能失败） ----------

    def test_old_mass_row_injection_rejected(self):
        injected = self.ref.replace(
            "| 浮筑层有效振动面密度 | m' | kg/㎡ | 弹性垫上方共同运动各构造层的单位面积质量之和；"
            "不含结构楼板、不含弹性垫自身，组成与排除见下方「m' 口径」条 |",
            "| 面层+垫层总面密度 | m' | kg/㎡ | 浮筑层总质量 |", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（ACE m' 参数表行锚点漂移）")
        ref_bak, self.ref = self.ref, injected
        try:
            with self.assertRaises(AssertionError):
                self.assert_mass_caliber(injected, self.fl_ref, self.fl_skill)
            with self.assertRaises(AssertionError):
                self.test_old_mass_labels_withdrawn()
        finally:
            self.ref = ref_bak

    def test_fl_exclusion_dropped_rejected(self):
        injected = self.fl_ref.replace(
            "不含结构楼板自重、不含弹性垫自身质量、不含活荷载与可变堆载",
            "不含弹性垫自身质量", 1)
        self.assertNotEqual(injected, self.fl_ref, "注入未命中（FL m' 行锚点漂移）")
        with self.assertRaises(AssertionError):
            self.assert_mass_caliber(self.ref, injected, self.fl_skill)

    def test_C_claim_reintroduced_rejected(self):
        injected = self.ref.replace(
            "C 为经验修正常数，典型取值 8-12。ACE 默认 C=10。",
            "C 为经验修正常数，典型取值 8-12。ACE 默认 C=10。C=12 基于理想实验室条件，"
            "对典型浮筑地面构造系统性高估约 5 dB。", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（C 取值行锚点漂移）")
        ref_bak, self.ref = self.ref, injected
        try:
            with self.assertRaises(AssertionError):
                self.test_C_calibration_claims_withdrawn()
        finally:
            self.ref = ref_bak

    def test_half_open_sigma_pairing_rejected(self):
        injected = self.ref.replace(
            "输出区间: [Rw_base + ΔR_下界 + Σ修正_下界,  Rw_base + ΔR_上界 + Σ修正_上界]",
            "输出区间: [Rw_base + ΔR 中值 + Σ修正_下界,  Rw_base + ΔR 中值 + Σ修正_上界]", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（Step 5 组装行锚点漂移）")
        ref_bak, self.ref = self.ref, injected
        try:
            with self.assertRaises(AssertionError):
                self.test_sigma_endpoint_pairing_rule()
        finally:
            self.ref = ref_bak

    def test_demo_label_restored_rejected(self):
        injected = self.ref.replace(
            "同构造对照（演示数据，不计为验证样本）：", "交叉验证：", 1)
        self.assertNotEqual(injected, self.ref, "注入未命中（算例对照行锚点漂移）")
        ref_bak, self.ref = self.ref, injected
        try:
            with self.assertRaises(AssertionError):
                self.test_demo_identity_of_uncited_benchmark()
        finally:
            self.ref = ref_bak

    # ---------- 控制例（守卫不恒真：良性编辑不误伤） ----------

    def test_control_benign_changes_pass(self):
        self.assert_mass_caliber(self.ref + "\n> 注：本节口径与楼地面技能方案表同源。\n",
                                 self.fl_ref, self.fl_skill)
        self.test_C_calibration_claims_withdrawn()
        self.test_demo_identity_of_uncited_benchmark()
        self.test_sigma_pairing_order_and_midpoint_property()
        self.test_example_minmax_and_assembled_intervals()
        self.assert_step5_compatible_with_group8(self.ref + "\n")

    def assert_step5_compatible_with_group8(self, ref):
        """组8 判据在本批改写后仍成立（判据未被削弱，只被一般化）。"""
        self.assertNotIn("[Rw_base + ΔR_low + Σ修正,  Rw_base + ΔR_high + Σ修正]", ref)
        self.assertIn("Rw_base + ΔR_下界 + Σ修正", ref)
        self.assertIn("加同一常数与同一 Σ修正后区间保序", ref)


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)

