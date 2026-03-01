#include <Servo.h>
#include <Wire.h>
#include "rgb_lcd.h"

rgb_lcd lcd;

const int colorR = 255;
const int colorG = 0;
const int colorB = 0;

Servo right;
Servo left;

const int straight = 90;
const int down = 175;


void printMessage16x2(String msg) {
  if (msg.length() > 32) {
    msg = msg.substring(0, 32);
  }

  lcd.clear();
  lcd.setCursor(0, 0);
  if (msg.length() <= 16) {
    lcd.print(msg);
    return;
  }

  lcd.print(msg.substring(0, 16));
  lcd.setCursor(0, 1);
  lcd.print(msg.substring(16));
}


void angry() {
  lcd.setRGB(255, 40, 40);
  lcd.clear();
  lcd.setCursor(0, 1);
  lcd.print("    >:(    ");
  left.write(straight);
  right.write(straight);
  delay(200);
  left.write(down);
  right.write(down);
  delay(200);
}

void showAlertMessage(String msg) {
  // Grove RGB LCD has fixed character color, so use a high-contrast backlight.
  lcd.setRGB(255, 200, 120);
  printMessage16x2(msg);
}


void defaultPos() {
  right.write(straight);
  left.write(straight);
  lcd.setRGB(colorR, colorG, colorB);
  printMessage16x2("Ready");
}


void layDown() {
  right.write(down);
  left.write(down);
  lcd.setRGB(255, 80, 80);
}


void setup() {
  Serial.begin(9600);
  Serial.setTimeout(30);
  delay(100);

  right.attach(10, 500, 2500);
  left.attach(11, 500, 2500);

  lcd.begin(16, 2);
  lcd.setRGB(colorR, colorG, colorB);
  defaultPos();
}

void processCommand(String input) {
  input.trim();
  if (input.length() == 0) {
    return;
  }

  if (input.startsWith("MSG:")) {
    String msg = input.substring(4);
    angry();
    showAlertMessage(msg);
    return;
  }

  if (input == "CLR") {
    defaultPos();
    return;
  }

  // Backward-compatible single-byte commands.
  if (input == "A") {
    angry();
    lcd.setCursor(0, 1);
    lcd.print("    >:(    ");
    return;
  }

  if (input == "B") {
    layDown();
    printMessage16x2("Focused");
  }
}


void loop() {
  if (!Serial.available()) {
    return;
  }

  String input = Serial.readStringUntil('\n');
  input.trim();
  processCommand(input);
}
