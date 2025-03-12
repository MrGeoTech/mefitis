//
const int sample_rate = 100;
const int sample_ports_length = 4;
const int sample_ports[] = { A0, A1, A2, A3 };

void setup() {
    Serial.begin(115200);
    Serial.write("start\n");
}

void loop() {
    for (int i = 0; i < sample_ports_length; i++) {
        const int value = analogRead(sample_ports[i]);
        Serial.write(highByte(value));
        Serial.write(lowByte(value));
    }
    Serial.write('\n');
    delay(1000 / sample_rate);
}
