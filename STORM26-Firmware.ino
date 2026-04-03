
#define SDA 2
#define SCL 3
#define NW_DRV 4 // NW is Front Left
#define NE_DRV 5 // NE is Front Right
#define SW_DRV 6 // SW is Rear Left
#define SE_DRV 7 // SE is Rear Right
#define INTAKE 8
#define SLIDE 9
#define CLIMBER 10
#define CHARGE 11
#define EXTRA_1 12
#define EXTRA_2 13
#define CLAW_1 14
#define CLAW_2 15
#define CLAW_3_LARGE 16
#define JUMPSTART 26
#define SWITCH_1 18
#define SWITCH_2 19

const char MOTOR_FREQ = 50;
char data[14];



void setup() {
  pinMode(SWITCH_1, INPUT);
  pinMode(SWITCH_2, INPUT);
  analogWriteFreq(MOTOR_FREQ);
  analogWriteResolution(8);
  Serial.begin();
  // put your setup code here, to run once:

}

void loop() {
  // put your main code here, to run repeatedly:
  if (Serial.available() >= 14) {
    Serial.readBytes(data, 14);
  }
  if((data[0] == '$') && (data[13] == '!')) {
    analogWrite(NW_DRV,data[1]);
    analogWrite(SW_DRV, data[2]);
    analogWrite(NE_DRV, data[3]);
    analogWrite(SE_DRV, data[4]);
    analogWrite(SLIDE, data[5]);
    analogWrite(INTAKE, data[6]);
    analogWrite(CLAW_3_LARGE, data[7]);
    analogWrite(CLAW_2, data[8]);
    analogWrite(CLAW_1, data[9]);
    analogWrite(CLIMBER, data[10]);
    analogWrite(CHARGE, data[11]);
    // JUMPSTART
  }
}
