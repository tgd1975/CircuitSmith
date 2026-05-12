"""
Day-one I2C sensor / display library.

Two profiles: BME280 environmental sensor and SSD1306 128×64 OLED display.
Both ride on `category: i2c-sensor` — the SSD1306 is a display, not a
sensor, but its layout shape (4-pin I2C peripheral: VCC, GND, SDA, SCL) is
identical to a sensor and `category` keys layout, not semantics
(`idea-001.components.md` footnote ³). If the category is renamed to
`i2c-peripheral` later, both profiles move with it.

Data-line pins use `type: I2C` and declare `func: ["I2C_SDA"]` /
`["I2C_SCL"]` — both halves are required by the schema's i2c-sensor rule
so ERC E7 (I2C pull-up check) activates.
"""

bme280 = {
    "category": "i2c-sensor",
    "metadata": {
        "label": "BME280",
        "manufacturer": "Bosch",
        "datasheet": "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf",
        # Default address on the Adafruit / SparkFun breakouts (SDO tied
        # to VDDIO). The 0x77 variant ships on some boards with SDO=VDDIO.
        "i2c_address": 0x76,
        "keywords": ["i2c", "sensor", "temperature", "humidity", "pressure", "3.3v"],
    },
    "pins": {
        "VCC": {"side": "top",    "type": "POWER",  "direction": "in"},
        "GND": {"side": "bottom", "type": "GROUND", "direction": "in"},
        "SDA": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SDA"]},
        "SCL": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SCL"]},
    },
}

ssd1306 = {
    "category": "i2c-sensor",
    "metadata": {
        "label": "SSD1306 128x64 OLED",
        "manufacturer": "Solomon Systech",
        "datasheet": "https://www.solomon-systech.com/wp-content/uploads/2024/03/SSD1306-Rev-1.5.pdf",
        # 0x3C is the default for the 7-bit address with D/C tied low; the
        # 128x32 variant uses the same address. 0x3D ships when D/C is
        # tied high — non-standard for the I2C-only breakouts we target.
        "i2c_address": 0x3C,
        "keywords": ["i2c", "display", "oled", "3.3v"],
    },
    "pins": {
        "VCC": {"side": "top",    "type": "POWER",  "direction": "in"},
        "GND": {"side": "bottom", "type": "GROUND", "direction": "in"},
        "SDA": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SDA"]},
        "SCL": {"side": "left",   "type": "I2C",    "direction": "bidir",
                "func": ["I2C_SCL"]},
    },
}
