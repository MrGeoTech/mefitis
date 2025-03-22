const int sample_ports_length = 4;
const int sample_ports[] = { A0, A1, A2, A3 };

void setup() {
    Serial.begin(19200);
}

void loop() {
    if (Serial.read() == 0) {
        for (int i = 0; i < sample_ports_length; i++) {
            const int value = analogRead(sample_ports[i]);
            Serial.write(highByte(value));
            Serial.write(lowByte(value));
        }
        Serial.write('\n');
    }
}
