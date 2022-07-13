#define NUM_OF_ACTUATORS 2
#define NONE_ACTION -1
#define ACTUATOR_OPEN 0
#define ACTUATOR_CLOSE 1
#define ACTION_TIME 30000

#define INA 7   
#define INB 8 
#define EN 4
#define PWM 5

#define MOTOR_SPEED 100 //0 - 255

char ACTUATOR_ACTION_MAP[] = {NONE_ACTION, NONE_ACTION};
int ACTUATOR_TIMEOUT_MAP[NUM_OF_ACTUATORS] = {0,0};



void setup() {
  Serial.begin(9600);
  pinMode(INA, OUTPUT);   
  pinMode(INB, OUTPUT);  
  pinMode(EN, OUTPUT);   
  digitalWrite(EN, LOW);
}

void loop() {
if (Serial.available()) {
    String buff = Serial.readStringUntil('\n');
    int delimPos = buff.indexOf(':');
    int actuatorN = atoi(buff.substring(0, delimPos).c_str());
    String command = buff.substring(delimPos + 1);
    if(actuatorN > NUM_OF_ACTUATORS-1){
      Serial.println("Unknown actuator:" + String(actuatorN));
    }
    else if (ACTUATOR_ACTION_MAP[actuatorN] != NONE_ACTION){
      if (ACTUATOR_ACTION_MAP[actuatorN] == ACTUATOR_OPEN){
        Serial.println(String(actuatorN) + ":opening");
        }
      else if (ACTUATOR_ACTION_MAP[actuatorN] == ACTUATOR_CLOSE){
       Serial.println(String(actuatorN) + ":closing");
       }
    }
    else {
      if ((command != "open")&&(command != "close")){
      Serial.println("Unknown command:" + command);
    } else {
      ActuatorAction(actuatorN,command);
    }
    }

 }
 for (int n=0; n<NUM_OF_ACTUATORS; n++){
  check_states(n);
 }
}

void ActuatorAction(int actuator_id, String command){
   if(command == "open"){
    ACTUATOR_ACTION_MAP[actuator_id] = ACTUATOR_OPEN;
    digitalWrite(EN, HIGH);
    digitalWrite(INA, HIGH);
    digitalWrite(INB, LOW);    
    analogWrite(PWM,MOTOR_SPEED);  
    Serial.println(String(actuator_id) + ":opening");
   }
   else{
    ACTUATOR_ACTION_MAP[actuator_id] = ACTUATOR_CLOSE;
    digitalWrite(EN, HIGH);
    digitalWrite(INA, LOW);
    digitalWrite(INB, HIGH);    
    analogWrite(PWM,MOTOR_SPEED); 
    Serial.println(String(actuator_id) + ":closing");
   }
}

void check_states(int actuator_id){
  String command;
  if(ACTUATOR_ACTION_MAP[actuator_id] == ACTUATOR_OPEN){
    command = "open";
    } else {command = "close";}
  if (ACTUATOR_ACTION_MAP[actuator_id] == NONE_ACTION){
    return;
  }
  if (ACTUATOR_TIMEOUT_MAP[actuator_id] > ACTION_TIME){
    Serial.println(String(actuator_id) + ":" + command);
    ACTUATOR_ACTION_MAP[actuator_id] = NONE_ACTION;
    ACTUATOR_TIMEOUT_MAP[actuator_id] = 0;
    digitalWrite(EN, LOW);
    return;
    }
  int timout = ACTUATOR_TIMEOUT_MAP[actuator_id];
  ACTUATOR_TIMEOUT_MAP[actuator_id] = timout+1;
}
