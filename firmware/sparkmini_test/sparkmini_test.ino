#define MOTOR_PIN 6
//#define MOTOR_FREQ 300
// #define MOTOR_FREQ 250000000000
#define MOTOR_FREQ 667
#define LED_PIN 25

int speed = 0;

void setup() {
  // put your setup code here, to run once:
  pinMode(MOTOR_PIN, OUTPUT);
  analogWriteResolution(8);

  pinMode(LED_PIN, OUTPUT);
  analogWriteFreq(MOTOR_FREQ); // idk if this is an actual function
  digitalWrite(LED_PIN, HIGH);
}

void loop() {
  // digitalWrite(LED_PIN, HIGH);
  // delay(200);
  // digitalWrite(LED_PIN, LOW);
  // delay(200);
  // put your main code here, to run repeatedly:
  speed++;

  if (speed >= 255) {
    speed = 0;
  }

  analogWrite(MOTOR_PIN, speed);

  delay(50);

  // delay(200);
}
