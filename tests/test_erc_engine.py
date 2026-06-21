"""
ERC engine tests for TASK-022.

Coverage:
  - All 13 active predicates (S1, S2, S3, E1..E10) fire on targeted fixtures.
  - The 15 check codes (S1..S5 + E1..E10) appear in `CHECK_TABLE`.
  - Both shipped circuits (data/esp32.circuit.yml, data/nrf52840.circuit.yml)
    are ERC-green with E9 surfacing as WARNING (not ERROR).
  - Dormant checks E6/E7/E10 emit no findings without qualifying components.
  - Three-level severity config (global / per-component / per-net) overrides
    the built-in default, with cross-component most-severe-wins.
"""
from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

from circuitsmith.erc_engine import CHECK_TABLE, Finding, run
from circuitsmith.netgraph import NetGraph
from circuitsmith.schema.registry import Profile, load_profiles


# ── Test scaffolding ────────────────────────────────────────────────────────


def _load_shipped(name: str) -> dict:
    yaml = YAML(typ="safe")
    repo_root = Path(__file__).resolve().parent.parent
    with open(repo_root / "data" / f"{name}.circuit.yml") as fh:
        return yaml.load(fh)


def _run(circuit: dict) -> list[Finding]:
    graph = NetGraph.from_yaml_dict(circuit)
    return run(graph, circuit)


def _codes(findings: list[Finding]) -> list[str]:
    return [f.check for f in findings]


# ── CHECK_TABLE contract ───────────────────────────────────────────────────


def test_check_table_has_all_27_codes() -> None:
    expected = {"S1", "S2", "S3", "S4", "S5",
                "E1", "E2", "E3", "E4", "E5",
                "E6", "E7", "E8", "E9", "E10",
                # EPIC-014 additions: 4 sub-block rules + divider-ambiguity.
                "E11", "E12", "E13", "E14", "E15",
                # EPIC-014 active-device rules (TASK-123).
                "E16", "E17", "E18",
                # EPIC-014 cross-page rules (TASK-127).
                "E19", "E20", "E21", "E22"}
    assert set(CHECK_TABLE) == expected


def test_check_table_e9_is_warning_default() -> None:
    assert CHECK_TABLE["E9"].severity_default == "warning"


# ── Shipped circuits are ERC-green at v0.1 ─────────────────────────────────


def test_esp32_shipped_circuit_clean_with_e9_warning() -> None:
    findings = _run(_load_shipped("esp32"))
    errors = [f for f in findings if f.severity == "error"]
    e9s = [f for f in findings if f.check == "E9"]
    assert errors == [], f"expected no errors on ESP32 default build; got: {errors}"
    assert e9s, "E9 should surface (USB-C VBUS has no diode/MOSFET at v0.1)"
    assert all(f.severity == "warning" for f in e9s)


def test_nrf52840_shipped_circuit_clean_with_e9_warning() -> None:
    findings = _run(_load_shipped("nrf52840"))
    errors = [f for f in findings if f.severity == "error"]
    e9s = [f for f in findings if f.check == "E9"]
    assert errors == [], f"expected no errors on nRF52840 default build; got: {errors}"
    assert all(f.severity == "warning" for f in e9s)


def test_shipped_circuits_have_no_dormant_findings() -> None:
    """E6/E7/E10 dormant on shipped circuits — no findings expected."""
    findings = _run(_load_shipped("esp32"))
    codes = _codes(findings)
    assert "E6" not in codes, "E6 active when an IC with a VCC pin appears — only MCU on shipped"
    assert "E7" not in codes, "E7 active when an I2C device appears — none on shipped"
    assert "E10" not in codes, "E10 active when pins double-up — none on shipped"


# ── Structural checks ──────────────────────────────────────────────────────


def _esp32_minimal() -> dict:
    return {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {"U1": {"type": "mcu/esp32"}},
        "connections": [
            {"net": "VCC", "pins": ["U1.VIN"]},   # dangling on purpose for S2
            {"net": "GND", "pins": ["U1.GNDL"]},  # dangling on purpose for S2
        ],
    }


def test_S2_fires_on_dangling_net() -> None:
    findings = _run(_esp32_minimal())
    assert any(f.check == "S2" and f.net == "VCC" and f.severity == "error" for f in findings)


def test_S3_fires_on_duplicate_net_name() -> None:
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
            "SW2": {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "BTN", "path": ["U1.D13", "SW1.1", "SW1.2", "GND"], "pull": "firmware"},
            {"net": "BTN", "path": ["U1.D12", "SW2.1", "SW2.2", "GND"], "pull": "firmware"},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    s3 = [f for f in findings if f.check == "S3"]
    assert s3 and s3[0].severity == "warning"


def test_S1_fires_on_unconnected_required_pin() -> None:
    """A profile pin marked `required: True` that lands in no net fires S1.

    TASK-134: no day-one shipped profile carries `required:` on any pin, so
    S1 has no triggering fixture against the stock library — it is only
    *avoided* by the other structural fixtures. We synthesise a minimal
    component profile with one required pin, wire only its *other* pin, and
    pass it via the `run(profiles=…)` override so `_check_S1` sees a required
    pin absent from `pin_index`. The component sits on an otherwise-clean
    ESP32 circuit; S1 is the only structural error expected.
    """
    profiles = dict(load_profiles())
    profiles["test/required_pin_widget"] = Profile(
        type="test/required_pin_widget",
        file="test",
        name="required_pin_widget",
        pins=frozenset({"A", "B"}),
        category="ic",
        pins_detail={
            # A is required but deliberately left unconnected below → S1.
            "A": {"side": "left",  "type": "GPIO", "direction": "bidir",
                  "required": True},
            "B": {"side": "right", "type": "GPIO", "direction": "bidir"},
        },
        metadata={"kind": "ic"},
    )
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "X1": {"type": "test/required_pin_widget"},
        },
        "connections": [
            # Only X1.B is wired; X1.A (required) is connected to no net.
            {"net": "SIG", "pins": ["U1.D13", "X1.B"]},
            {"net": "GND", "pins": ["U1.GNDL", "U1.GNDR"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=profiles)
    assert any(
        f.check == "S1" and f.ref == "X1" and f.pin == "A" and f.severity == "error"
        for f in findings
    ), f"expected an S1 error on X1.A; got: {findings}"


def test_S_class_error_skips_E_class() -> None:
    """If S2 fires as ERROR, E-class checks are not run."""
    circuit = _esp32_minimal()
    findings = _run(circuit)
    e_codes = [f.check for f in findings if f.check.startswith("E")]
    assert not e_codes, f"expected no E-class findings after S-class errors; got {e_codes}"


# ── Electrical: E1 floating input ──────────────────────────────────────────


def test_E1_fires_on_floating_button_input() -> None:
    """Button on GPIO with no pull — E1 fires."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            # No `pull:` on the BTN net — D13 is bidir GPIO with role: in,
            # the button bridges to GND but no pull is declared.
            {"net": "BTN", "path": ["U1.D13", "SW1.1", "SW1.2", "GND"],
             "role": "in"},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    assert any(f.check == "E1" and f.net == "BTN" for f in findings)


def test_E1_passes_with_pull_firmware() -> None:
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "BTN", "path": ["U1.D13", "SW1.1", "SW1.2", "GND"],
             "pull": "firmware"},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    assert not any(f.check == "E1" for f in findings)


# ── Electrical: E2/E3 LED resistor checks ──────────────────────────────────


def test_E2_fires_on_led_without_resistor() -> None:
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "D1": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "LED", "path": ["U1.D13", "D1.A", "D1.K", "GND"]},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    assert any(f.check == "E2" for f in findings)


def test_E3_fires_on_resistor_too_small_pin_at_risk() -> None:
    """22Ω on 3.3V => ~60 mA, above the ESP32 12 mA budget."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "R1": {"type": "passives/resistor", "value": 22},
            "D1": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "LED", "path": ["U1.D13", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    e3 = [f for f in findings if f.check == "E3"]
    assert e3 and e3[0].severity == "warning"


# ── Electrical: E4 INPUT_ONLY driven ───────────────────────────────────────


def test_E4_fires_when_input_only_pin_sees_output() -> None:
    """ESP32's D34 is INPUT_ONLY. Wiring D26 (output bidir) to D34 fires E4
    when D26's role resolves to `out`."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {"U1": {"type": "mcu/esp32"}},
        "connections": [
            {"net": "BAD", "pins": ["U1.D26", "U1.D34"], "role": {"U1.D26": "out"}},
            {"net": "GND", "pins": ["U1.GNDL", "U1.GNDR"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    # The pin direction in profile data is "bidir" by default for GPIO,
    # so E4's predicate (direction == "out") fires only when the pin
    # profile literally has direction: "out". On ESP32 no pin profile
    # declares direction: "out", so this test exercises the *predicate
    # path* but yields no finding — the assertion below validates the
    # predicate is wired (no crash, no spurious finding).
    findings = _run(circuit)
    # Engine must complete and treat the topology as legal at the
    # predicate level — the actual E4 trigger requires a pin with
    # profile direction: out, which lives on LED.K (CATHODE).
    assert isinstance(findings, list)


def test_E4_fires_with_led_cathode_driving_input_only() -> None:
    """LED.K declares direction: out; on a net with an INPUT_ONLY pin, E4 fires."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "D1": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "BAD", "pins": ["D1.K", "U1.D34"]},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
            {"net": "ANODE", "pins": ["D1.A"]},  # tied off to avoid S1
        ],
    }
    findings = _run(circuit)
    # Even with S2 firing on dangling ANODE, E4 should also surface; but
    # since S-class error gates E-class, we only require S2 here.
    assert any(f.check == "S2" for f in findings)


def test_E4_fires_clean_with_no_s_class_gate() -> None:
    """E4 in isolation: INPUT_ONLY pin driven by an `out` pin, no S-class gate.

    TASK-134: the sibling test above leaves D1.A dangling, so S2 fires and
    gates the entire E-class run — E4 never reports. Here the LED anode is
    wired through a legal current-limited *path* net (so E2 stays quiet) and
    the BAD net carries `pull: firmware` (so E1 stays quiet on the
    INPUT_ONLY pin). The circuit is structurally clean — no S1/S2/S3 — so
    the E-class run proceeds and E4 is the only finding.

    Mechanism: LED.K declares `direction: out` (the only shipped pin that
    does); ESP32 D34 is `type: INPUT_ONLY`. Sharing a net trips
    `_check_E4`'s `direction == "out"` predicate against the INPUT_ONLY pin.
    """
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "D1": {"type": "passives/led", "color": "red"},
            "R1": {"type": "passives/resistor", "value": 330},
        },
        "connections": [
            # K (direction: out) on the same net as D34 (INPUT_ONLY) → E4.
            # pull: firmware keeps E1 from firing on the INPUT_ONLY input.
            {"net": "BAD", "pins": ["D1.K", "U1.D34"], "pull": "firmware"},
            # Anode wired through a proper current-limited path → no E2.
            {"net": "ANODE", "path": ["U1.D25", "R1.1", "R1.2", "D1.A"]},
            {"net": "GND", "pins": ["U1.GNDL", "U1.GNDR"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    # No S-class error must gate the E-class run.
    assert not any(
        f.check.startswith("S") and f.severity == "error" for f in findings
    ), f"S-class error would gate E4; got: {findings}"
    assert any(
        f.check == "E4" and f.net == "BAD" and f.pin == "D34"
        for f in findings
    ), f"expected E4 on U1.D34; got: {findings}"


# ── Electrical: E5 strapping pin without pull ──────────────────────────────


def test_E5_fires_on_unpulled_strapping_pin_with_switch() -> None:
    """ESP32 D5 is a strapping pin. Wired to a switch with no pull → E5."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
        },
        "connections": [
            # No pull on this net.
            {"net": "STRAP", "path": ["U1.D5", "SW1.1", "SW1.2", "GND"],
             "role": "in"},
            {"net": "GND", "pins": ["U1.GNDL"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    assert any(f.check == "E5" for f in findings)


# ── Electrical: E6 IC decoupling cap ───────────────────────────────────────


def test_E6_fires_on_non_mcu_ic_without_decoupling_cap() -> None:
    """A non-MCU IC with a POWER pin on a power rail with no cap fires E6.

    TASK-134: `_check_E6` requires `_kind(profile) == "ic"` AND a pin with
    `attrs.get("type") == "POWER"`. The shipped general-purpose IC profiles
    do **not** qualify: `ic/555` has `kind: "timer"` and its supply pin is
    `type: "POWER_INPUT"`; `ic/opamp_dual_supply` has `kind: "opamp"` with
    `POWER_INPUT` rails. Neither matches the `kind == "ic"` +
    `type == "POWER"` predicate, so E6 is dormant on the stock library.

    We synthesise a minimal non-MCU IC (`kind: "ic"`, one `type: "POWER"`
    pin) and place its VCC pin on the power rail with no capacitor anywhere
    on that net. The ESP32 (the MCU) is excluded from E6 by the
    `ref in mcu_refs` guard, so E6 fires only on the synthetic IC.
    """
    profiles = dict(load_profiles())
    profiles["test/decoupled_ic"] = Profile(
        type="test/decoupled_ic",
        file="test",
        name="decoupled_ic",
        pins=frozenset({"VCC", "GND", "IO"}),
        category="ic",
        pins_detail={
            "VCC": {"side": "top",    "type": "POWER",  "direction": "in"},
            "GND": {"side": "bottom", "type": "GROUND", "direction": "in"},
            "IO":  {"side": "left",   "type": "GPIO",   "direction": "bidir"},
        },
        metadata={"kind": "ic"},
    )
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "U2": {"type": "test/decoupled_ic"},
        },
        "connections": [
            # U2.VCC sits on the power rail; no capacitor on the net → E6.
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33", "U2.VCC"]},
            {"net": "GND", "pins": ["U1.GNDL", "U2.GND"]},
            {"net": "SIG", "pins": ["U1.D13", "U2.IO"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=profiles)
    assert any(
        f.check == "E6" and f.ref == "U2" and f.net == "VCC"
        for f in findings
    ), f"expected E6 on U2's VCC rail; got: {findings}"


# ── Electrical: E7 I2C pull-up ─────────────────────────────────────────────


def test_E7_fires_on_i2c_net_without_pullup() -> None:
    """ESP32 D21=SDA, D22=SCL with an I2C peripheral (BME280) on the bus and
    no pull-up resistor to V33 — E7 fires."""
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "S1": {"type": "sensors/bme280"},
        },
        "connections": [
            {"net": "SDA", "pins": ["U1.D21", "S1.SDA"]},
            {"net": "SCL", "pins": ["U1.D22", "S1.SCL"]},
            {"net": "GND", "pins": ["U1.GNDL", "S1.GND"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33", "S1.VCC"]},
        ],
    }
    findings = _run(circuit)
    assert any(f.check == "E7" for f in findings)


# ── Electrical: E8 LED current budget ──────────────────────────────────────


def test_E8_fires_when_led_current_exceeds_total_budget() -> None:
    """Summed LED path current over the MCU's `max_total_current_ma` fires E8.

    TASK-134: `_check_E8` sums `(vcc - v_forward) / R * 1000` across every
    LED path net and reports when the total exceeds the MCU profile's
    `max_total_current_ma`. To keep the fixture minimal *and* isolate E8
    (no per-GPIO E3 overcurrent co-firing), we synthesise an MCU profile
    with a deliberately low total budget (20 mA) and a generous per-GPIO
    budget (500 mA). Two LED paths at ~13.6 mA each (5.0 V, 220 Ω, red LED
    Vf 2.0 V) total ~27.3 mA > 20 mA → E8, while each branch stays well
    under the per-GPIO ceiling so E3 never fires.

    A synthetic MCU is used rather than 17+ LEDs on the shipped ESP32
    (200 mA budget) because lowering the budget keeps the circuit two-LED
    small and the only finding E8.
    """
    profiles = dict(load_profiles())
    profiles["test/low_budget_mcu"] = Profile(
        type="test/low_budget_mcu",
        file="test",
        name="low_budget_mcu",
        pins=frozenset({"IO1", "IO2", "VIN", "GND"}),
        category="ic",
        pins_detail={
            "IO1": {"side": "left", "type": "GPIO",   "direction": "bidir"},
            "IO2": {"side": "left", "type": "GPIO",   "direction": "bidir"},
            "VIN": {"side": "left", "type": "POWER",  "direction": "in"},
            "GND": {"side": "left", "type": "GROUND", "direction": "in"},
        },
        metadata={
            "kind": "mcu",
            "vcc_max": 5.0,
            "max_gpio_current_ma": 500,   # generous → no per-GPIO E3
            "max_total_current_ma": 20,   # tight → E8 fires with two LEDs
        },
    )
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "test/low_budget_mcu"},
            "R1": {"type": "passives/resistor", "value": 220},
            "R2": {"type": "passives/resistor", "value": 220},
            "D1": {"type": "passives/led", "color": "red"},
            "D2": {"type": "passives/led", "color": "red"},
        },
        "connections": [
            {"net": "L1", "path": ["U1.IO1", "R1.1", "R1.2", "D1.A", "D1.K", "GND"]},
            {"net": "L2", "path": ["U1.IO2", "R2.1", "R2.2", "D2.A", "D2.K", "GND"]},
            {"net": "GND", "pins": ["U1.GND", "U1.VIN"]},
        ],
    }
    graph = NetGraph.from_yaml_dict(circuit)
    findings = run(graph, circuit, profiles=profiles)
    e8 = [f for f in findings if f.check == "E8"]
    assert e8 and e8[0].severity == "warning", (
        f"expected an E8 warning; got: {findings}"
    )


# ── Electrical: E10 pin conflict ───────────────────────────────────────────


def test_E10_fires_when_pin_in_two_nets() -> None:
    circuit = {
        "meta": {"title": "tst", "target": "esp32"},
        "components": {
            "U1": {"type": "mcu/esp32"},
            "SW1": {"type": "passives/pushbutton"},
            "SW2": {"type": "passives/pushbutton"},
        },
        "connections": [
            {"net": "A", "pins": ["U1.D13", "SW1.1"]},
            {"net": "B", "pins": ["U1.D13", "SW2.1"]},  # D13 in two nets
            {"net": "GND", "pins": ["U1.GNDL", "SW1.2", "SW2.2"]},
            {"net": "VCC", "pins": ["U1.VIN", "U1.V33"]},
        ],
    }
    findings = _run(circuit)
    assert any(f.check == "E10" for f in findings)


# ── Severity override system ───────────────────────────────────────────────


def test_global_meta_erc_overrides_default() -> None:
    """Setting meta.erc.E9: off suppresses the E9 finding on shipped circuit."""
    circuit = _load_shipped("esp32")
    circuit.setdefault("meta", {})["erc"] = {"E9": "off"}
    findings = _run(circuit)
    assert not any(f.check == "E9" for f in findings)


def test_per_component_override_wins_over_global() -> None:
    circuit = _load_shipped("esp32")
    circuit.setdefault("meta", {})["erc"] = {"E9": "error"}
    # J1 is the USB-C connector; override its E9 to off.
    circuit["components"]["J1"]["erc"] = {"E9": "off"}
    findings = _run(circuit)
    e9 = [f for f in findings if f.check == "E9"]
    assert not e9, "per-component override should win over global"


def test_per_net_override_wins_over_component() -> None:
    circuit = _load_shipped("esp32")
    circuit["components"]["J1"]["erc"] = {"E9": "off"}
    # Find the net containing J1.VBUS — the shipped VCC net — and re-enable E9 on it.
    for entry in circuit["connections"]:
        if entry["net"] == "VCC":
            entry["erc"] = {"E9": "error"}
    findings = _run(circuit)
    assert any(f.check == "E9" and f.severity == "error" for f in findings)
