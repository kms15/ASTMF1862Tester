#include <SPI.h>

#define ABP_PIN 2
#define VALVE_PIN 7

void setup() {
    // our debugging output
    Serial.begin(115200);

    // initialize SPI for the ABP pressure sensor
    SPI.begin();
    pinMode(ABP_PIN, OUTPUT);
    digitalWrite(ABP_PIN, HIGH);

    pinMode(VALVE_PIN, OUTPUT);
    digitalWrite(VALVE_PIN, LOW);
}

void loop() {
    delay(50);

    // read the pressure and temperature
    digitalWrite(ABP_PIN, LOW);
    unsigned pressure = (unsigned(SPI.transfer(0)) << 8);
    pressure |= SPI.transfer(0);
    unsigned temperature = (unsigned(SPI.transfer(0)) << 8);
    temperature |= SPI.transfer(0);
    digitalWrite(ABP_PIN, HIGH);

    Serial.print(pressure);
    Serial.print(",");
    Serial.print(temperature);
    Serial.println("");

    if (Serial.available()) {
        const int maxlen = 5;
        char buffer[maxlen+1];
        const int count = Serial.readBytesUntil('\n', buffer, maxlen);
        buffer[count] = 0;
        int valvetime_ms = atoi(buffer);
        if (valvetime_ms > 0) {
            digitalWrite(VALVE_PIN, HIGH);
            delay(valvetime_ms);
            digitalWrite(VALVE_PIN, LOW);
        }
    }
}

