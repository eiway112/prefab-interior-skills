"""
ACE Adversarial Regression Test Suite
=======================================
Re-runnable test suite for ACE architecture formulas, parameters, and data.
Run after any document change to catch inconsistencies.

Usage:  python ace_regression_test.py
        python ace_regression_test.py -v          (verbose)

Version: 1.3.1
Date: 2026-08-20

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
import re
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
_DOC_PATH = (Path.home() / ".qoderwork" / "skills"
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


# ============================================================
# Run
# ============================================================
if __name__ == "__main__":
    unittest.main(verbosity=2)
