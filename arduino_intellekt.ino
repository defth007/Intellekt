//include the servo library
#include <Servo.h>

#include <Wire.h>
#include "rgb_lcd.h"

rgb_lcd lcd;

const int colorR = 255;
const int colorG = 0;
const int colorB = 0;

//initializing the Servo objects
Servo right;
Servo left;

//initializing the variable that will hold certain points of time
int time;

//arm fully straight
const int straight = 90;
//arm fully down
const int down = 175;

//int gradient = 0;

void setup() {
  Serial.begin(9600);
  
  delay(100);

  //right arm attached to pin 10
  right.attach(10, 500, 2500);
  //left arm attached to pin 11
  left.attach(11, 500, 2500);

//telling lcd screen how many characters and lines it will be working with
//and clearing the screen
  lcd.setRGB(colorR, colorG, colorB);
  lcd.begin(16, 2);
  lcd.clear();
//time set to 0
  time = 0;

}

void loop() {

      char Byte = 0;

 if (Serial.available()) 
    {
      
      Byte = Serial.read();    
       
      switch(Byte)
      {
        case 'A':  
        
        angry();
        time = millis();

        case 'B': //your code
            int gradient = (millis() - time)/100;
            right.write(down);
            left.write(down);
                      
        default:
                      sit();
        }//end of switch()
      }//endof if serial.available()


    }

/***
ANGRY FUNCTION
*/
void angry(){

  //face
  lcd.setRGB(255, 40, 40);
 lcd.setCursor(0, 1);
 lcd.print("     ÒwÓ       ");
 delay(5);

 left.write(straight);
 right.write(straight);
 delay(200);

 left.write(down);
 right.write(down);
 delay(200);

}

/**
DEFAULT POSITION
*/
void defaultPos(){
        //backRight.write(backlegDown);
      //backLeft.write(backlegDown);

      right.write(straight);
      left.write(straight);

  lcd.setCursor(0, 1);
  lcd.print("     0wo       ");
}


/***
LAYDOWN FUNCTION
*/
void layDown(){
     // backRight.write(backlegDown);
     // backLeft.write(backlegDown);

      right.write(down);
      left.write(down);

      lcd.setCursor(0, 1);
      lcd.print("     -w-       ");

      delay(5);
}