//ph variables
float calibration = 22.094; //change this value to calibrate
const int analogInPinpH = A0; 
int sensorValue = 0; 
unsigned long int avgValue; 
float b;
int buf[10],temp;
static char outstr3[25];
String phvalueeol = "ph\n";

//Waterlevel sensor variables
int val = 0;
const int waterlevelpin = A5;
float percentage; 
static char outstr[25];
String waterleveleol;

void setup(){
  Serial.begin(19200);
}

void loop(){
  //Water level scode
  val = analogRead(waterlevelpin);
  //100% - 20% capacity, val = 500 - 300
  //20% - 10% capacity, val = 299 - 100
  //10% - 0& capacity, val = 99 - 0
  if (val > 299){
    //Serial.print("high\t");
    percentage = (((float(val)-300.00)/200.00) * 80.00) + 20.00;
  }
  else if (val > 99){
    //Serial.print("Medium\t");
    percentage = (((float(val)-100.00)/199.00) * 10.00) + 10.00;
  }
  else if (val >= 0){
    //Serial.print("Low\t");
    percentage = (((float(val)-0.00)/99.00) * 10.00) + 0.00;
  }

  dtostrf(percentage,4,2,outstr);
    waterleveleol = "waterlevel\n";
    
  //send water level over
  strcat(outstr, waterleveleol.c_str());
  Serial.write(outstr);
  
  //pH sensor code

    //check pH value
    for(int i=0;i<10;i++) 
    { 
      buf[i]=analogRead(analogInPinpH);
      delay(20);
    }
    for(int i=0;i<9;i++)
    {
      for(int j=i+1;j<10;j++)
      {
        if(buf[i]>buf[j])
        {
          temp=buf[i];
          buf[i]=buf[j];
          buf[j]=temp;
        }
      }
    }
    avgValue=0;
    for(int i=2;i<8;i++)
      avgValue+=buf[i];
    float pHVol=(float)avgValue*5.0/1024/6;
    float phValue = -6.0753 * pHVol + calibration;
    dtostrf(phValue,4,2,outstr3);
    
    strcat(outstr3, phvalueeol.c_str());
    //send values over
    Serial.write(outstr3);
  delay(1000);

}
